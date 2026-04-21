from __future__ import annotations

from io import BytesIO

from minio import Minio
from minio.error import S3Error

from core.config import get_settings

settings = get_settings()


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_bytes(*, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    ensure_bucket(client, settings.MINIO_BUCKET)
    stream = BytesIO(data)
    try:
        client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            stream,
            length=len(data),
            content_type=content_type,
        )
    except S3Error:
        raise
    return object_name
