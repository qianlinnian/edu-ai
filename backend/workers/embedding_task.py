from __future__ import annotations

import base64
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import dashscope
from minio import Minio
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker
import pypdfium2 as pdfium

from core.config import get_settings
from models.course import CourseResource, ResourceChunk
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def split_text(content: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    text = content.strip()
    if not text:
        return []

    chunks: list[str] = []
    step = max(chunk_size - overlap, 1)
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step

    return chunks


def parse_resource_content(file_type: str, payload: bytes) -> str:
    suffix = file_type.lower()
    if suffix in {"txt", "md", "py", "json", "csv"}:
        return payload.decode("utf-8", errors="ignore")

    if suffix == "pdf":
        return parse_pdf_content(payload)

    if suffix == "docx":
        document = Document(BytesIO(payload))
        texts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(texts)

    if suffix == "pptx":
        presentation = Presentation(BytesIO(payload))
        texts: list[str] = []
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text = shape.text.strip()
                    if text:
                        texts.append(text)
        return "\n".join(texts)

    if suffix == "xlsx":
        return parse_xlsx_content(payload)

    return payload.decode("utf-8", errors="ignore")


def parse_xlsx_content(payload: bytes) -> str:
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    texts: list[str] = []

    with ZipFile(BytesIO(payload)) as workbook_zip:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            shared_root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", namespace):
                parts = [node.text or "" for node in item.findall(".//main:t", namespace)]
                shared_strings.append("".join(parts).strip())

        sheet_files = sorted(
            name
            for name in workbook_zip.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )

        for sheet_name in sheet_files:
            sheet_root = ET.fromstring(workbook_zip.read(sheet_name))
            rows: list[str] = []
            for row in sheet_root.findall(".//main:sheetData/main:row", namespace):
                values: list[str] = []
                for cell in row.findall("main:c", namespace):
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("main:v", namespace)
                    inline_node = cell.find("main:is", namespace)

                    if cell_type == "s" and value_node is not None and value_node.text is not None:
                        index = int(value_node.text)
                        value = shared_strings[index] if index < len(shared_strings) else ""
                    elif inline_node is not None:
                        parts = [node.text or "" for node in inline_node.findall(".//main:t", namespace)]
                        value = "".join(parts).strip()
                    elif value_node is not None and value_node.text is not None:
                        value = value_node.text.strip()
                    else:
                        value = ""

                    if value:
                        values.append(value)

                if values:
                    rows.append(" | ".join(values))

            if rows:
                texts.append(f"[{sheet_name.split('/')[-1]}]\n" + "\n".join(rows))

    return "\n\n".join(texts)


def parse_pdf_content(payload: bytes) -> str:
    reader = PdfReader(BytesIO(payload))
    texts = [(page.extract_text() or "").strip() for page in reader.pages]
    extracted_text = "\n".join(text for text in texts if text)
    if extracted_text:
        return extracted_text

    return ocr_pdf_content(payload)


def ocr_pdf_content(payload: bytes) -> str:
    if not settings.DASHSCOPE_API_KEY:
        return ""

    dashscope.api_key = settings.DASHSCOPE_API_KEY
    pdf = pdfium.PdfDocument(BytesIO(payload))
    texts: list[str] = []

    try:
        page_count = min(len(pdf), 5)
        for page_index in range(page_count):
            page = pdf[page_index]
            pil_image = page.render(scale=2).to_pil()
            buffer = BytesIO()
            pil_image.save(buffer, format="PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            response = dashscope.MultiModalConversation.call(
                model=settings.QWEN_VL_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/png;base64,{image_base64}"},
                            {"text": "请提取这页中的文字内容，直接返回纯文本，不要解释。"},
                        ],
                    }
                ],
            )

            if response.status_code != 200:
                continue

            content = response.output.choices[0].message.content
            page_text_parts: list[str] = []
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        page_text_parts.append(item["text"].strip())
            elif isinstance(content, str):
                page_text_parts.append(content.strip())

            page_text = "\n".join(part for part in page_text_parts if part)
            if page_text:
                texts.append(page_text)
    finally:
        pdf.close()

    return "\n\n".join(texts)


@celery_app.task(name="workers.embedding_task.process_resource")
def process_resource(resource_id: int):
    """处理课程资料并将其分块写入 resource_chunks。"""
    print(f"[Embedding] 开始处理资料 resource_id={resource_id}")

    with SyncSessionLocal() as db:
        resource = db.execute(
            select(CourseResource).where(CourseResource.id == resource_id)
        ).scalar_one_or_none()
        if not resource:
            return {"resource_id": resource_id, "status": "not_found"}

        client = get_minio_client()
        response = client.get_object(settings.MINIO_BUCKET, resource.file_path)
        try:
            payload = response.read()
        finally:
            response.close()
            response.release_conn()

        content = parse_resource_content(resource.file_type, payload)
        chunks = split_text(content)

        db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id == resource.id))

        for index, chunk in enumerate(chunks):
            db.add(
                ResourceChunk(
                    resource_id=resource.id,
                    course_id=resource.course_id,
                    content=chunk,
                    chunk_index=index,
                    metadata_={
                        "resource_name": resource.name,
                        "file_type": resource.file_type,
                        "object_name": resource.file_path,
                    },
                )
            )

        resource.chunk_count = len(chunks)
        resource.is_processed = True
        db.commit()

    return {"resource_id": resource_id, "status": "processed", "chunk_count": len(chunks)}
