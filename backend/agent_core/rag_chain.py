from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import ResourceChunk

"""RAG增强链 - 负责根据查询进行资料检索和上下文构建"""

# todo: 
# embedding 检索
# 相似度排序
# BM25
# rerank
# 调模型
# 读聊天历史
 

async def retrieve_chunks(db: AsyncSession, course_id: int, query: str, top_k: int = 5) -> list[ResourceChunk]:
    # 第一版先按课程取前几个资料片段，后续再替换成真正检索
    result = await db.execute(
        select(ResourceChunk)
        .where(ResourceChunk.course_id == course_id)
        .order_by(ResourceChunk.chunk_index)
        .limit(top_k)
    )
    return result.scalars().all()


def build_context(chunks: list[ResourceChunk]) -> str:
    # 构建上下文字符串 - 可以根据需要调整格式
    if not chunks:
        return ""

    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"资料{index}:\n{chunk.content}")
    return "\n\n".join(parts)


async def get_context(db: AsyncSession, course_id: int, query: str, top_k: int = 5) -> str:
    # 对外接口 - 根据课程ID和查询内容获取相关资料上下文
    chunks = await retrieve_chunks(db, course_id, query, top_k=top_k)
    return build_context(chunks)
