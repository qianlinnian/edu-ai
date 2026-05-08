# Codex Work Log — Backend B (M2 Resource Stability)

Date: 2026-05-06

## Goal (M2 收尾，资源管理稳定性)
- 不改 RAG 主逻辑；在 M2 主链路已通的前提下，补齐资源管理“可回收/可重跑/可观测”能力。

## Changes

### 1) Resource list / delete / retry APIs
- Added resource list API (for frontend rendering fields):
  - `GET /api/v1/courses/{course_id}/resources`
- Added resource delete API (best-effort MinIO cleanup):
  - `DELETE /api/v1/courses/{course_id}/resources/{resource_id}`
  - Deletes `resource_chunks` then `course_resources`; tries MinIO object deletion and returns `minio_deleted`.
- Added resource retry API (re-run processing without re-upload):
  - `POST /api/v1/courses/{course_id}/resources/{resource_id}/retry`
  - Clears old chunks, resets fields:
    - `processing_status=pending`
    - `processing_error=null`
    - `chunk_count=0`
    - `is_processed=false`
  - Re-dispatches Celery task `process_resource`.

Files:
- `backend/api/routes/courses.py`
- `backend/core/storage.py`

### 2) Demo cleanup script
- Added a safe CLI script to clear one course’s resources and chunks (keep course/users/agents):
  - `backend/script/clear_course_resources.py`
  - Supports `--dry-run`; optional best-effort MinIO cleanup via `--delete-minio`.

## How to test (quick)
1. Upload a resource:
   - `POST /api/v1/courses/{course_id}/resources` (multipart file)
2. Observe list fields:
   - `GET /api/v1/courses/{course_id}/resources`
3. Retry a failed resource:
   - `POST /api/v1/courses/{course_id}/resources/{resource_id}/retry`
4. Delete a resource:
   - `DELETE /api/v1/courses/{course_id}/resources/{resource_id}`
5. Script (dry run):
   - `python backend/script/clear_course_resources.py --course-id 1 --dry-run`

