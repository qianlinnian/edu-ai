from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.chat import ChatSession, ChatMessage

router = APIRouter()


class ChatRequest(BaseModel):
    agent_id: int
    course_id: int
    session_id: int | None = None
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata_: dict | None = None

    model_config = {"from_attributes": True}


@router.post("/send")
async def send_message(
    data: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    # 获取或创建会话
    if data.session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == data.session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session = ChatSession(user_id=user.id, agent_id=data.agent_id, course_id=data.course_id)
        db.add(session)
        await db.flush()
        await db.refresh(session)

    # 保存用户消息
    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    await db.flush()

    # TODO: 调用Agent进行RAG答疑，生成回复
    # from agent_core.rag_chain import get_rag_response
    # response = await get_rag_response(data.agent_id, data.course_id, data.message, session.id)

    # 临时模拟回复
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=f"[模拟回复] 收到你的问题：{data.message}。RAG答疑模块开发中...",
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "message": ChatMessageResponse.model_validate(assistant_msg),
    }


@router.get("/sessions", response_model=list[dict])
async def list_sessions(
    course_id: int | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    query = select(ChatSession).where(ChatSession.user_id == user.id)
    if course_id:
        query = query.where(ChatSession.course_id == course_id)
    result = await db.execute(query.order_by(ChatSession.updated_at.desc()))
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "course_id": s.course_id, "created_at": str(s.created_at)} for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    return result.scalars().all()
