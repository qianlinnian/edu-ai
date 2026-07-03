# EduAI 可嵌入式跨课程 AI Agent 通用架构平台

EduAI 是一个面向课程场景的 AI Agent 平台，支持课程知识库问答、作业提交与智能批改、练习生成、学情分析、课程 Agent 配置发布，以及超星/钉钉等平台的模拟接入。

如果需要了解仓库整体能力、模块结构和测试材料，请先阅读：[Intro_pro_readme.md](Intro_pro_readme.md)。

## 当前推荐启动方式

日常开发建议采用“Docker 启动基础设施 + 本地 Conda 启动后端/Worker + 本地启动前端”的方式。

推荐环境名：

```powershell
conda activate edu
```

## 1. 环境要求

| 组件 | 推荐版本 | 说明 |
| --- | --- | --- |
| Docker Desktop | 最新稳定版 | 启动 PostgreSQL、Redis、MinIO |
| Python | 3.11 | 后端 FastAPI / Celery |
| Conda | 任意新版 | 推荐使用 `edu` 环境 |
| Node.js | 18+ | 前端 Vite / React |
| Git | 任意新版 | 代码管理 |

## 2. 克隆项目

```powershell
git clone <repository-url>
cd edu-ai
```

## 3. 配置后端环境变量

```powershell
Copy-Item backend\.env.example backend\.env
```

根据实际情况编辑 `backend/.env`，至少需要确认：

```env
DASHSCOPE_API_KEY=
DEEPSEEK_API_KEY=
ZHIPU_API_KEY=
DEFAULT_LLM_PROVIDER=dashscope
```

本地直接运行后端时，数据库建议连接 `localhost`：

```env
DATABASE_URL=postgresql+asyncpg://eduai:eduai123@localhost:5432/eduai
DATABASE_SYNC_URL=postgresql://eduai:eduai123@localhost:5432/eduai
```

如果 Redis / MinIO 也从本机访问，建议使用：

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
MINIO_ENDPOINT=localhost:9000
```

## 4. 启动基础服务

在仓库根目录执行：

```powershell
docker compose up postgres redis minio -d
docker compose ps
```

服务端口：

| 服务 | 地址 |
| --- | --- |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO API | `localhost:9000` |
| MinIO Console | `http://localhost:9001` |

MinIO 默认账号密码：`minioadmin / minioadmin`。

## 5. 启动后端 API

首次安装依赖：

```powershell
conda activate edu
cd backend
pip install -r requirements.txt
```

执行数据库迁移：

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
alembic upgrade head
```

启动 FastAPI：

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
uvicorn main:app --reload --port 8000
```

也可以使用项目脚本：

```powershell
conda activate edu
backend\script\migrate.cmd
backend\script\dev.cmd
```

后端地址：

```text
http://localhost:8000
http://localhost:8000/docs
```

## 6. 启动 Celery Worker

资源解析、Embedding、异步批改等任务依赖 Worker。另开一个终端执行：

```powershell
conda activate edu
backend\script\worker.cmd
```

等价手动命令：

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
celery -A workers.celery_app worker --loglevel=info -P solo -Q celery,embedding,grading
```

## 7. 启动前端

首次安装依赖：

```powershell
cd frontend
npm install
```

启动开发服务器：

```powershell
cd frontend
npm run dev
```

前端地址：`http://localhost:5173`。

## 8. Docker 部署/演示启动

如果需要一次性启动后端、Worker 和基础服务：

```powershell
docker compose up -d
```

这会启动：

| 容器 | 说明 |
| --- | --- |
| `postgres` | PostgreSQL + pgvector |
| `redis` | 缓存与 Celery Broker |
| `minio` | 对象存储 |
| `backend` | FastAPI 后端 |
| `celery-worker` | 异步任务 Worker |

注意：全 Docker 方式适合部署/演示。日常开发更推荐本地启动后端，因为修改代码后不需要重建镜像。

## 9. 测试命令

后端自动化测试：

```powershell
conda activate edu
pytest backend/tests -q
```

更稳定的截图命令：

```powershell
conda run -n edu pytest backend/tests -q -p no:warnings --basetemp=D:\course\SEME\edu-ai\.pytest_tmp_clean -p no:cacheprovider
```

API 级 E2E 冒烟测试需要后端、数据库、Redis、MinIO、Worker 和 LLM 配置可用：

```powershell
conda activate edu
python backend\script\test_api.py --base-url http://127.0.0.1:8000/api/v1 --poll-timeout 180
```

前端构建检查：

```powershell
cd frontend
npm run build
```

## 10. 常用命令

```powershell
# 查看容器状态
docker compose ps

# 查看后端容器日志
docker compose logs backend -f

# 查看 worker 容器日志
docker compose logs celery-worker -f

# 停止容器
docker compose down

# 重建后端镜像
docker compose build backend

# 生成并执行数据库迁移
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 11. 项目结构

```text
edu-ai/
├── backend/                 # FastAPI 后端
│   ├── api/routes/           # API 路由
│   ├── agent_core/           # Agent、RAG、LLM Provider
│   ├── core/                 # 配置、数据库、认证
│   ├── education/            # 练习、学情、教学逻辑
│   ├── models/               # 数据库模型
│   ├── platform_adapter/     # 平台模拟接入
│   ├── script/               # 启动、检查、测试脚本
│   ├── tests/                # 后端自动化测试
│   └── workers/              # Celery 异步任务
├── frontend/                 # React + Vite 前端
│   └── src/
├── data/                     # 评测数据与样例数据
├── docs/                     # RBS/WBS、测试报告、设计与交付文档
├── docker-compose.yml        # 基础服务与部署编排
├── README.md                 # 启动说明
└── Intro_pro_readme.md       # 项目介绍
```

## 12. 注意事项

- 本地运行后端时，`DATABASE_URL` 应连接 `localhost`。
- Docker 容器内运行后端时，`DATABASE_URL` 应连接 `postgres`。
- 本地运行 Worker 时，`CELERY_BROKER_URL` 建议连接 `localhost`。
- `alembic` 建议在 `backend/` 目录执行，并设置 `PYTHONPATH`。
- 前端默认访问后端 API，请确认后端 `8000` 端口已启动。
- LLM 功能需要配置可用的 API Key，否则问答、批改、练习生成等功能会受限。
