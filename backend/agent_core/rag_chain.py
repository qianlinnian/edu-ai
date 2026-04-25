"""RAG retrieval helpers for course Q&A."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_core.llm_provider import get_llm_provider
from models.course import ResourceChunk


async def embed_query(query: str) -> list[float]:
    """Generate one embedding vector for the user query."""
    llm_provider = get_llm_provider("dashscope")
    embeddings = await llm_provider.embedding([query])
    if not embeddings:
        raise RuntimeError("query embedding generation returned no vectors")
    return embeddings[0]


async def retrieve_chunks(
    db: AsyncSession,
    course_id: int,
    query: str,
    top_k: int = 5,
) -> list[ResourceChunk]:
    """Retrieve the most relevant chunks for a query within one course."""
    query_embedding = await embed_query(query)

    result = await db.execute(
        select(ResourceChunk)
        .where(ResourceChunk.course_id == course_id)
        .where(ResourceChunk.embedding.is_not(None))
        .order_by(ResourceChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return result.scalars().all()


def build_context(chunks: list[ResourceChunk]) -> str:
    """Format retrieved chunks into one prompt context string."""
    if not chunks:
        return ""

    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"资料{index}:\n{chunk.content}")
    return "\n\n".join(parts)


async def get_context(
    db: AsyncSession,
    course_id: int,
    query: str,
    top_k: int = 5,
) -> str:
    """Public entry point for building QA context."""
    chunks = await retrieve_chunks(db, course_id, query, top_k=top_k)
    return build_context(chunks)
