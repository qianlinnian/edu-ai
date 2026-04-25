from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from api.routes import auth, courses, agents, assignments, chat, analytics, exercises, platform

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    print(f"{settings.APP_NAME} 启动中...")
    yield
    # 关闭时清理
    print(f"{settings.APP_NAME} 关闭中...")


app = FastAPI(
    title=settings.APP_NAME,
    description="可嵌入式跨课程AI Agent通用架构平台",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
prefix = settings.API_PREFIX
app.include_router(auth.router, prefix=f"{prefix}/auth", tags=["认证"])
app.include_router(courses.router, prefix=f"{prefix}/courses", tags=["课程管理"])
app.include_router(agents.router, prefix=f"{prefix}/agents", tags=["Agent管理"])
app.include_router(assignments.router, prefix=f"{prefix}/assignments", tags=["作业管理"])
app.include_router(chat.router, prefix=f"{prefix}/chat", tags=["智能答疑"])
app.include_router(analytics.router, prefix=f"{prefix}/analytics", tags=["学情分析"])
app.include_router(exercises.router, prefix=f"{prefix}/exercises", tags=["练习生成"])
app.include_router(platform.router, prefix=f"{prefix}/platform", tags=["平台适配"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
