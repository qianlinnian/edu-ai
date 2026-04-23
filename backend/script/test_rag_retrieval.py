from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from agent_core.rag_chain import retrieve_chunks
from core.database import async_session
from models.course import ResourceChunk


def preview(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact[:limit] + ("..." if len(compact) > limit else "")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test RAG retrieval results for a course query.")
    parser.add_argument("--course-id", type=int, required=True, help="Course id to search within.")
    parser.add_argument("--query", required=True, help="User query to retrieve chunks for.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve.")
    parser.add_argument("--preview", type=int, default=200, help="Preview characters per chunk.")
    args = parser.parse_args()

    async with async_session() as db:
        total_chunks = await db.scalar(
            select(func.count()).select_from(ResourceChunk).where(ResourceChunk.course_id == args.course_id)
        )
        embedded_chunks = await db.scalar(
            select(func.count())
            .select_from(ResourceChunk)
            .where(ResourceChunk.course_id == args.course_id, ResourceChunk.embedding.is_not(None))
        )

        print(f"course_id={args.course_id}")
        print(f"total_chunks={total_chunks or 0}")
        print(f"embedded_chunks={embedded_chunks or 0}")

        if not embedded_chunks:
            print("No embedded chunks found. Reprocess course resources before testing retrieval.")
            return 1

        try:
            chunks = await retrieve_chunks(db, args.course_id, args.query, top_k=args.top_k)
        except Exception as exc:
            print(f"retrieval failed: {exc}")
            return 1

        if not chunks:
            print("No chunks retrieved.")
            return 1

        for rank, chunk in enumerate(chunks, start=1):
            print("=" * 80)
            print(
                f"rank={rank} chunk_id={chunk.id} "
                f"resource_id={chunk.resource_id} chunk_index={chunk.chunk_index}"
            )
            print(preview(chunk.content, args.preview))

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
