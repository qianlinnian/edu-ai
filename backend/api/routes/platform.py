from fastapi import APIRouter, Depends, Request
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
    """超星LTI启动端点 - 接收LTI 1.3启动请求"""
    # TODO: 验证LTI签名，解析用户身份，返回嵌入页面
    return {"message": "超星LTI对接端点", "status": "开发中"}


# --- 钉钉 H5微应用入口 ---
@router.get("/dingtalk/auth")
async def dingtalk_auth(code: str | None = None):
    """钉钉免登授权回调"""
    # TODO: 使用code换取用户信息
    return {"message": "钉钉认证端点", "status": "开发中"}


@router.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    """钉钉机器人消息回调"""
    body = await request.json()
    # TODO: 处理钉钉机器人消息
    return {"msgtype": "text", "text": {"content": "收到消息，学情预警功能开发中"}}
