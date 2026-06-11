import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_core.agent_base import AgentConfig, QAAgent
from core.database import get_db
from core.permissions import ensure_course_access
from core.security import get_current_user
from models.agent import AgentInstance
from models.chat import ChatMessage, ChatSession
from models.course import Course
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


def _json_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _agent_config(agent: AgentInstance, *, course_id: int) -> AgentConfig:
    config = agent.config if isinstance(agent.config, dict) else {}
    raw_top_k = config.get("top_k", 5)
    try:
        top_k = int(raw_top_k)
    except (TypeError, ValueError):
        top_k = 5
    if top_k <= 0:
        top_k = 5

    raw_similarity = config.get("similarity_threshold")
    try:
        similarity_threshold = float(raw_similarity) if raw_similarity is not None else None
    except (TypeError, ValueError):
        similarity_threshold = None

    return AgentConfig(
        name=agent.name,
        course_id=course_id,
        system_prompt=agent.system_prompt,
        llm_provider=agent.llm_provider,
        llm_model=agent.llm_model,
        tools=list(agent.tools or []),
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )


async def _build_history_messages(session_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    history = result.scalars().all()
    return [{"role": item.role, "content": item.content} for item in history]


async def _resolve_agent(*, data: ChatRequest, db: AsyncSession) -> AgentInstance:
    result = await db.execute(select(AgentInstance).where(AgentInstance.id == data.agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.course_id != data.course_id:
        raise HTTPException(status_code=400, detail="Agent does not belong to this course")
    if not agent.is_active:
        raise HTTPException(status_code=409, detail="Agent is not active")
    return agent


async def _resolve_course(*, data: ChatRequest, db: AsyncSession) -> Course:
    result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


async def _resolve_chat_session(
    *,
    data: ChatRequest,
    db: AsyncSession,
    user: User,
    agent: AgentInstance,
) -> ChatSession:
    if not data.session_id:
        session = ChatSession(
            user_id=user.id,
            agent_id=agent.id,
            course_id=data.course_id,
            title=data.message[:50],
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == data.session_id,
            ChatSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.course_id != data.course_id:
        raise HTTPException(status_code=400, detail="Session course mismatch")
    if session.agent_id != agent.id:
        raise HTTPException(status_code=400, detail="Session agent mismatch")
    return session


async def _prepare_chat(
    *,
    data: ChatRequest,
    db: AsyncSession,
    user: User,
) -> tuple[AgentInstance, ChatSession, list[dict]]:
    course = await _resolve_course(data=data, db=db)
    await ensure_course_access(db, course=course, user=user)
    agent = await _resolve_agent(data=data, db=db)
    session = await _resolve_chat_session(data=data, db=db, user=user, agent=agent)

    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()

    history = await _build_history_messages(session.id, db)
    return agent, session, history[:-1] if history else []


async def _save_assistant_message(
    *,
    db: AsyncSession,
    session: ChatSession,
    content: str,
) -> ChatMessage:
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=content,
    )
    db.add(assistant_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(assistant_msg)
    return assistant_msg


@router.post("/send")
async def send_message(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent, session, history = await _prepare_chat(data=data, db=db, user=user)

    qa_agent = QAAgent(_agent_config(agent, course_id=data.course_id))
    response = await qa_agent.chat(
        query=data.message,
        history=history,
        context={"db": db},
    )

    assistant_msg = await _save_assistant_message(db=db, session=session, content=response)
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
    agent, session, history = await _prepare_chat(data=data, db=db, user=user)
    await db.commit()
    qa_agent = QAAgent(_agent_config(agent, course_id=data.course_id))

    async def event_stream():
        chunks: list[str] = []
        try:
            async for chunk in qa_agent.chat_stream(
                query=data.message,
                history=history,
                context={"db": db},
            ):
                chunks.append(chunk)
                yield _json_sse({"type": "chunk", "content": chunk})

            assistant_msg = await _save_assistant_message(
                db=db,
                session=session,
                content="".join(chunks).strip(),
            )
            await db.commit()
            yield _json_sse(
                {
                    "type": "done",
                    "session_id": session.id,
                    "message_id": assistant_msg.id,
                }
            )
        except Exception as exc:
            await db.rollback()
            yield _json_sse({"type": "error", "detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
