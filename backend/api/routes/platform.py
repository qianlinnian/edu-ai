from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import create_access_token, get_current_user
from models.platform import PlatformConnection
from models.user import User, UserRole

router = APIRouter()


class PlatformConnectionCreate(BaseModel):
    platform_type: Literal["chaoxing", "dingtalk"]
    name: str = Field(min_length=1, max_length=200)
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_config(self) -> "PlatformConnectionCreate":
        required_fields = {
            "chaoxing": ("lti_key", "lti_secret", "callback_url"),
            "dingtalk": ("app_key", "app_secret", "agent_id"),
        }
        missing = [key for key in required_fields[self.platform_type] if not self.config.get(key)]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")

        callback_url = self.config.get("callback_url")
        if self.platform_type == "chaoxing" and callback_url is not None:
            HttpUrl(callback_url)

        return self


class PlatformConnectionResponse(BaseModel):
    id: int
    platform_type: Literal["chaoxing", "dingtalk"]
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ChaoxingLaunchRequest(BaseModel):
    course: int = Field(ge=1)
    token: str = Field(min_length=1)
    role: Literal["student", "teacher", "assistant"] = "student"


def _ensure_platform_manager(user: User) -> None:
    if user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")


@router.post("/connections", response_model=PlatformConnectionResponse)
async def create_connection(
    data: PlatformConnectionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_platform_manager(user)

    conn = PlatformConnection(**data.model_dump())
    db.add(conn)
    await db.flush()
    await db.commit()
    await db.refresh(conn)
    return conn


@router.get("/connections", response_model=list[PlatformConnectionResponse])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_platform_manager(user)

    result = await db.execute(select(PlatformConnection).order_by(PlatformConnection.created_at.desc()))
    return result.scalars().all()


@router.post("/chaoxing/lti-launch")
async def chaoxing_lti_launch(
    data: ChaoxingLaunchRequest,
    user: User = Depends(get_current_user),
):
    embed_token = create_access_token(data={"sub": str(user.id)})
    return {
        "platform": "chaoxing",
        "status": "ok",
        "message": "Chaoxing LTI launch ready",
        "widget_url": f"/widget/chat?course={data.course}&token={embed_token}",
        "token": embed_token,
        "course": data.course,
        "role": data.role,
    }


@router.get("/dingtalk/auth")
async def dingtalk_auth(
    code: str = Query(min_length=1),
    course_id: int = Query(ge=1),
    user: User = Depends(get_current_user),
):
    embed_token = create_access_token(data={"sub": str(user.id)})
    return {
        "platform": "dingtalk",
        "status": "ok",
        "message": "DingTalk auth ready",
        "code": code,
        "course_id": course_id,
        "widget_url": f"/widget/chat?course={course_id}&token={embed_token}",
        "token": embed_token,
    }


@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    try:
        await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    return {
        "msgtype": "text",
        "text": {
            "content": "Received message, analytics alert workflow is under development.",
        },
    }
