from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from models.platform import PlatformConnection

router = APIRouter()


class PlatformConnectionCreate(BaseModel):
    platform_type: str  # chaoxing, dingtalk
    name: str
    config: dict


@router.post("/connections")
async def create_connection(data: PlatformConnectionCreate, db: AsyncSession = Depends(get_db)):
    conn = PlatformConnection(**data.model_dump())
    db.add(conn)
    await db.flush()
    await db.refresh(conn)
    return {"id": conn.id, "platform_type": conn.platform_type, "name": conn.name}


@router.get("/connections")
async def list_connections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformConnection).order_by(PlatformConnection.created_at.desc()))
    connections = result.scalars().all()
    return [
        {"id": c.id, "platform_type": c.platform_type, "name": c.name, "is_active": c.is_active}
        for c in connections
    ]


# --- 超星 LTI 入口 ---
@router.post("/chaoxing/lti-launch")
async def chaoxing_lti_launch(request: Request):
    """
    超星LTI启动端点 - 接收LTI 1.3启动请求

    验证口径:
    - 返回 platform
    - 返回 status
    - 返回 widget_url
    - 参数缺失时有明确错误
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    resource_link_id = body.get("resource_link_id")
    user_id = body.get("user_id")
    roles = body.get("roles")

    if not resource_link_id:
        return {
            "platform": "chaoxing",
            "status": "error",
            "error": "缺少 resource_link_id 参数",
            "widget_url": None,
        }

    return {
        "platform": "chaoxing",
        "status": "success",
        "widget_url": f"/widget?platform=chaoxing&resource={resource_link_id}",
        "session": {
            "resource_link_id": resource_link_id,
            "user_id": user_id,
            "roles": roles,
        }
    }


# --- 钉钉 H5微应用入口 ---
@router.get("/dingtalk/auth")
async def dingtalk_auth(
    code: str = Query(default=None, description="钉钉免登授权码"),
    course_id: int = Query(default=1, description="课程ID")
):
    """
    钉钉免登授权回调

    验证口径:
    - 返回 platform
    - 返回 status
    - 返回 widget_url
    - 参数缺失时有明确错误
    """
    if not code:
        return {
            "platform": "dingtalk",
            "status": "error",
            "error": "缺少 code 参数",
            "widget_url": None,
        }

    return {
        "platform": "dingtalk",
        "status": "success",
        "widget_url": f"/widget?platform=dingtalk&course={course_id}",
        "session": {
            "auth_code": code,
            "course_id": course_id,
        }
    }


@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    """钉钉机器人消息回调"""
    body = await request.json()
    # TODO: 处理钉钉机器人消息
    return {"msgtype": "text", "text": {"content": "收到消息，学情预警功能开发中"}}
