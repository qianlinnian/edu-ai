import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_core.agent_base import AgentConfig, QAAgent
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


async def _resolve_chat_session(
    *,
    data: ChatRequest,
    db: AsyncSession,
    user: User,
) -> tuple[AgentInstance, ChatSession]:
    agent_result = await db.execute(
        select(AgentInstance).where(
            AgentInstance.id == data.agent_id,
            AgentInstance.course_id == data.course_id,
            AgentInstance.is_active == True,
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found for this course")

    if data.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == data.session_id,
                ChatSession.user_id == user.id,
                ChatSession.course_id == data.course_id,
                ChatSession.agent_id == data.agent_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found for this course")
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

    return agent, session


@router.post("/send")
async def send_message(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent, session = await _resolve_chat_session(data=data, db=db, user=user)

    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()

    history = await _build_history_messages(session.id, db)

    agent_config = AgentConfig(
        name=agent.name,
        course_id=data.course_id,
        system_prompt=agent.system_prompt,
        llm_provider=agent.llm_provider,
        llm_model=agent.llm_model,
    )

    qa_agent = QAAgent(agent_config)
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


@router.post("/send-stream")
async def send_message_stream(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent, session = await _resolve_chat_session(data=data, db=db, user=user)

    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()

    history = await _build_history_messages(session.id, db)
    agent_config = AgentConfig(
        name=agent.name,
        course_id=data.course_id,
        system_prompt=agent.system_prompt,
        llm_provider=agent.llm_provider,
        llm_model=agent.llm_model,
    )
    qa_agent = QAAgent(agent_config)

    async def event_stream():
        chunks: list[str] = []
        try:
            async for chunk in qa_agent.chat_stream(
                query=data.message,
                history=history[:-1] if history else [],
                context={"db": db},
            ):
                chunks.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_content = "".join(chunks).strip()
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_content,
            )
            db.add(assistant_msg)
            session.updated_at = datetime.now(timezone.utc)
            await db.flush()
            await db.refresh(assistant_msg)
            yield f"data: {json.dumps({'type': 'done', 'session_id': session.id, 'message_id': assistant_msg.id}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
    user: User = Depends(get_current_user),
):
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    return result.scalars().all()


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.delete(session)
    await db.flush()
    return {"ok": True}
