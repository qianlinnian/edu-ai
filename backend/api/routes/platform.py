from typing import Any, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import get_settings
from core.security import create_access_token, get_current_user
from models.platform import PlatformConnection
from models.user import User, UserRole

router = APIRouter()
settings = get_settings()

SIMULATED_INTEGRATION_NOTE = (
    "This is a simulated platform integration. The backend issues the embed token and widget_url, "
    "but it does not perform real platform SDK calls or signature validation."
)


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
    course_id: int = Field(ge=1)
    role: Literal["student", "teacher"] = "student"
    launch_ticket: str = Field(min_length=1, max_length=200)


class SimulatedPlatformLaunchResponse(BaseModel):
    platform: Literal["chaoxing", "dingtalk"]
    mode: Literal["simulated"]
    status: Literal["ok"]
    message: str
    widget_url: str
    token: str
    token_source: str
    course_id: int
    course_id_source: str
    role: Literal["student", "teacher"]
    role_source: str
    upstream_reference: str
    upstream_reference_type: str
    integration_boundary: str


def _ensure_platform_manager(user: User) -> None:
    if user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")


def _build_simulated_widget_launch(
    *,
    platform_name: Literal["chaoxing", "dingtalk"],
    user: User,
    course_id: int,
    role: Literal["student", "teacher"],
    upstream_reference: str,
    upstream_reference_type: str,
    request: Request | None = None,
) -> SimulatedPlatformLaunchResponse:
    embed_token = create_access_token(data={"sub": str(user.id), "platform": platform_name, "role": role})
    frontend_base_url = settings.FRONTEND_BASE_URL.rstrip("/")
    if request is not None:
        origin = (request.headers.get("origin") or "").strip().rstrip("/")
        if origin:
            frontend_base_url = origin
        else:
            referer = (request.headers.get("referer") or "").strip()
            if referer:
                parsed = urlsplit(referer)
                if parsed.scheme and parsed.netloc:
                    frontend_base_url = f"{parsed.scheme}://{parsed.netloc}"

    return SimulatedPlatformLaunchResponse(
        platform=platform_name,
        mode="simulated",
        status="ok",
        message=f"Simulated {platform_name} launch prepared",
        widget_url=f"{frontend_base_url}/widget/chat?course={course_id}&token={embed_token}",
        token=embed_token,
        token_source="issued_by_edu_ai_backend",
        course_id=course_id,
        course_id_source="provided_by_upstream_platform_payload",
        role=role,
        role_source="provided_by_upstream_platform_payload",
        upstream_reference=upstream_reference,
        upstream_reference_type=upstream_reference_type,
        integration_boundary=SIMULATED_INTEGRATION_NOTE,
    )


@router.post("/connections", response_model=PlatformConnectionResponse)
async def create_connection(
    data: PlatformConnectionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_platform_manager(user)

    payload = data.model_dump()
    payload["config"] = {
        **payload["config"],
        "integration_mode": "simulated",
        "integration_boundary": SIMULATED_INTEGRATION_NOTE,
    }

    conn = PlatformConnection(**payload)
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


@router.post("/chaoxing/lti-launch", response_model=SimulatedPlatformLaunchResponse)
async def chaoxing_lti_launch(
    data: ChaoxingLaunchRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    return _build_simulated_widget_launch(
        platform_name="chaoxing",
        user=user,
        course_id=data.course_id,
        role=data.role,
        upstream_reference=data.launch_ticket,
        upstream_reference_type="launch_ticket",
        request=request,
    )


@router.get("/dingtalk/auth", response_model=SimulatedPlatformLaunchResponse)
async def dingtalk_auth(
    request: Request,
    code: str = Query(min_length=1),
    course_id: int = Query(ge=1),
    role: Literal["student", "teacher"] = Query(default="student"),
    user: User = Depends(get_current_user),
):
    return _build_simulated_widget_launch(
        platform_name="dingtalk",
        user=user,
        course_id=course_id,
        role=role,
        upstream_reference=code,
        upstream_reference_type="auth_code",
        request=request,
    )


@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    try:
        await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    return {
        "msgtype": "text",
        "text": {
            "content": "Received message. Simulated analytics alert callbacks are not implemented yet.",
        },
    }
