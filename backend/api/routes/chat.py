from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from agent_core.agent_base import AgentConfig,QAAgent
from core.database import get_db
from core.security import get_current_user
from models.agent import AgentInstance
from models.chat import ChatMessage, ChatSession
from models.user import User

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


async def _build_history_messages(session_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    history = result.scalars().all() 

    return [{"role": item.role, "content": item.content} for item in history]


@router.post("/send")
# api接口 负责接收用户消息 调用agent生成回答 并保存聊天记录
async def send_message(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent_result = await db.execute(
        select(AgentInstance).where(
            AgentInstance.id == data.agent_id,
            AgentInstance.is_active == True,
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if data.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == data.session_id,
                ChatSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(
            user_id=user.id,
            agent_id=data.agent_id,
            course_id=data.course_id,
            title=data.message[:50],
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    await db.flush()

    history = await _build_history_messages(session.id, db)

    agent_config = AgentConfig(
        name=agent.name,
        course_id=data.course_id,
        system_prompt=agent.system_prompt,
        llm_provider=agent.llm_provider,
        llm_model=agent.llm_model,
    )

    qa_agent = QAAgent(agent_config) # 创建 QAAgent实例，传入agent_config配置。
    response = await qa_agent.chat(
        query=data.message,
        history=history[:-1] if history else [],
        context={"db": db},
    )

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response,
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
    course_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(ChatSession).where(ChatSession.user_id == user.id)
    if course_id:
        query = query.where(ChatSession.course_id == course_id)
    result = await db.execute(query.order_by(ChatSession.updated_at.desc()))
    sessions = result.scalars().all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "course_id": item.course_id,
            "created_at": str(item.created_at),
        }
        for item in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    return result.scalars().all()
