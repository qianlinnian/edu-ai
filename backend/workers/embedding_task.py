from __future__ import annotations

from minio import Minio
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

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

    return payload.decode("utf-8", errors="ignore")


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
