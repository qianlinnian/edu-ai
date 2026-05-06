from __future__ import annotations

import argparse

from minio import Minio
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models.course import CourseResource, ResourceChunk


def get_minio_client(settings) -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear course resources + chunks (keep course/users/agents).")
    parser.add_argument("--course-id", type=int, required=True)
    parser.add_argument("--delete-minio", action="store_true", help="Best-effort delete objects from MinIO as well.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be deleted without changing anything.")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.DATABASE_SYNC_URL)
    session_local = sessionmaker(bind=engine)

    with session_local() as db:
        resources = db.execute(select(CourseResource).where(CourseResource.course_id == args.course_id)).scalars().all()
        resource_ids = [resource.id for resource in resources]

        print(f"[clear_course_resources] course_id={args.course_id}")
        print(f"[clear_course_resources] resources={len(resources)}")

        if args.dry_run:
            for resource in resources:
                print(f"- resource_id={resource.id} name={resource.name} object={resource.file_path}")
            return 0

        if resource_ids:
            db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id.in_(resource_ids)))
            db.execute(delete(CourseResource).where(CourseResource.id.in_(resource_ids)))

        minio_deleted = 0
        minio_failed = 0
        if args.delete_minio and resources:
            client = get_minio_client(settings)
            for resource in resources:
                try:
                    client.remove_object(settings.MINIO_BUCKET, resource.file_path)
                    minio_deleted += 1
                except Exception:
                    minio_failed += 1

        db.commit()
        print("[clear_course_resources] db_deleted_resources=", len(resources))
        if args.delete_minio:
            print("[clear_course_resources] minio_deleted=", minio_deleted, "minio_failed=", minio_failed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

