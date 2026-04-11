# EduAI - 可嵌入式跨课程AI Agent通用架构平台
# EduAI - 可嵌入式跨课程AI Agent通用架构平台
# EduAI - 可嵌入式跨课程AI Agent通用架构平台

## 环境准备

### 1. 安装必备软件

| 软件 | 版本要求 | 下载地址 |
|------|----------|----------|
| Docker Desktop | 最新版 | https://www.docker.com/products/docker-desktop |
| Python | 3.11+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| Git | 最新版 | https://git-scm.com/ |

### 2. 克隆项目

```bash
git clone <仓库地址>
cd edu-ai
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑 .env，填入你的 API Key
# DASHSCOPE_API_KEY=你的通义千问Key
# DEEPSEEK_API_KEY=你的DeepSeek Key
# ZHIPU_API_KEY=你的智谱Key（可选）
```

### 4. 启动基础服务（PostgreSQL + Redis + MinIO）

```bash
docker compose up postgres redis minio -d
```

验证服务是否启动成功：

```bash
docker compose ps
```

应看到 3 个服务状态为 running。

MinIO 管理界面：http://localhost:9001（账号 minioadmin / minioadmin）

### 5. 后端启动

#### 方式A：使用 Anaconda（推荐）

```bash
# 创建 conda 环境
conda create -n eduai python=3.11 -y

# 激活环境
conda activate eduai

# 进入后端目录
cd backend

# 安装依赖
pip install -e ".[dev]"

# 数据库迁移（建表）
alembic upgrade head

# 启动后端
uvicorn main:app --reload --port 8000
```

#### 方式B：使用 venv

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 数据库迁移（建表）
alembic upgrade head

# 启动后端
uvicorn main:app --reload --port 8000
```

后端 API 文档：http://localhost:8000/docs

### 6. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端页面：http://localhost:5173

### 7. 一键启动（部署/演示时使用）

部署或演示时，可以用 Docker 一次性启动所有服务（包括后端代码）：

```bash
docker compose up -d
```

这会启动 5 个容器：

| 容器 | 说明 |
|------|------|
| postgres | 数据库 |
| redis | 缓存 |
| minio | 文件存储 |
| backend | FastAPI 后端（你的Python代码） |
| celery-worker | 异步任务（批改、Embedding） |

> **注意**：日常开发时不建议用这种方式，因为改代码后需要重新构建镜像。
> 开发时推荐第 4+5 步的方式：Docker 只跑数据库，Python 代码本地跑（支持热更新）。

前端始终需要单独 `npm run dev` 启动。

## 项目结构

```
edu-ai/
├── backend/           # Python 后端（FastAPI）
│   ├── main.py        # 入口
│   ├── core/          # 配置、数据库、认证
│   ├── models/        # 数据库模型
│   ├── api/routes/    # API 路由
│   ├── agent_core/    # Agent SDK + LLM Provider
│   ├── education/     # 批改、学情、练习引擎
│   ├── platform_adapter/  # 超星/钉钉适配
│   └── workers/       # Celery 异步任务
├── frontend/          # React 前端
│   └── src/
│       ├── pages/     # 页面组件
│       ├── components/# 公共组件
│       └── services/  # API 封装
├── docker-compose.yml # 服务编排
└── docs/              # 文档
```

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs backend -f

# 停止所有服务
docker compose down

# 重建后端镜像（依赖变更后）
docker compose build backend

# 数据库迁移（新增模型后）
cd backend && alembic revision --autogenerate -m "描述" && alembic upgrade head

# 前端构建生产版本
cd frontend && npm run build
```

## 团队分工

详见 [docs/plan.md](docs/plan.md)
