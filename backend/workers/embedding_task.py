from workers.celery_app import celery_app
import os
import minio
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
import markdown
import requests

@celery_app.task(name="workers.embedding_task.process_resource")
def process_resource(resource_id: int):
    """异步处理课程资料：解析 -> 分块 -> 向量化 -> 存储"""
    print(f"[Embedding] 处理资料 resource_id={resource_id}")

    # 1. 从MinIO下载文件
    minio_client = minio.Minio(
        "minio-server.com",
        access_key="your-access-key",
        secret_key="your-secret-key",
        secure=True
    )

    # Get file info (assuming the file is stored under 'course_resources' bucket)
    file_info = minio_client.stat_object("course_resources", f"{resource_id}.pdf")  # Replace with dynamic file type

    file_path = f"/tmp/{resource_id}.pdf"  # Temporary file storage
    minio_client.fget_object("course_resources", f"{resource_id}.pdf", file_path)

    # 2. 根据文件类型解析 (PDF/Word/PPT/Markdown)
    content = ""

    if file_info.content_type == "application/pdf":
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            content = "\n".join([page.extract_text() for page in reader.pages])

    elif file_info.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])

    elif file_info.content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        presentation = Presentation(file_path)
        content = "\n".join([slide.shapes.title.text for slide in presentation.slides])

    elif file_info.content_type == "text/markdown":
        with open(file_path, "r") as f:
            content = markdown.markdown(f.read())

    # 3. 文本分块 (按段落/固定长度，overlap)
    # Assuming simple paragraph-based chunking with a fixed overlap (e.g., 20 words per chunk, 5 words overlap)
    chunk_size = 20
    overlap = 5
    words = content.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    # 4. 调用Embedding API生成向量 (假设有一个函数或API调用)
    embedding_api_url = "https://your-embedding-api.com/embeddings"
    response = requests.post(embedding_api_url, json={"text": chunks})
    if response.status_code == 200:
        embeddings = response.json()["embeddings"]
    else:
        embeddings = []

    # 5. 存入resource_chunks表 (含向量)
    # Assuming we have a database session to interact with
    from backend.models import ResourceChunk
    from backend.core.database import get_db

    db = get_db()
    for idx, chunk in enumerate(chunks):
        db.add(ResourceChunk(resource_id=resource_id, chunk_index=idx, chunk_text=chunk, embedding=embeddings[idx]))
    db.commit()

    # 6. 更新course_resources.is_processed = True
    from backend.models import CourseResource
    course_resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
    if course_resource:
        course_resource.is_processed = True
        db.commit()

    return {"resource_id": resource_id, "status": "processed"}