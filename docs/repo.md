# EduAI 仓库架构说明

## 1. 项目概述

EduAI 是一个面向跨课程 AI Agent 的教学平台，核心目标是把智能答疑、作业批改、学情分析、增量练习和平台嵌入能力统一到一套通用架构中。仓库采用前后端分离设计，后端以 FastAPI 为核心，前端以 React + TypeScript 为核心，配合 PostgreSQL、Redis、MinIO 和 Celery 构成完整的教学智能平台底座。

从业务上看，这个仓库不是单一的问答系统，而是一个覆盖“课程管理 -> Agent 构建 -> 智能答疑 -> 作业提交与批改 -> 学情分析 -> 练习生成 -> 平台对接”的教育应用骨架。当前仓库已经具备完整的目录结构和主要数据模型，但部分智能能力仍处于占位实现阶段。

## 2. 根目录文件作用

### README.md
仓库总说明文档，包含环境准备、启动方式、项目结构、常用命令和团队分工入口。它适合用来快速了解项目怎么启动、依赖什么环境、推荐用什么方式部署。

### docker-compose.yml
容器编排文件，用于启动 PostgreSQL、Redis、MinIO、后端服务和 Celery worker 等基础设施。它是项目本地开发和部署演示的关键入口之一。

### .gitignore
Git 忽略规则文件，用于排除虚拟环境、构建产物、缓存文件和敏感配置文件，避免这些内容被提交到仓库。

## 3. 文档目录作用

### docs/Intro.md
项目命题与需求背景文档，描述了 EduAI 所解决的教育数字化问题、业务挑战、技术要求和评分要点。它更偏向“为什么要做这个系统”和“系统要满足什么指标”。

### docs/frontend-design.md
前端页面设计说明，定义了教师和学生两类角色的页面范围、页面布局、交互方式和功能预期。这个文件是前端页面实现的重要依据。

### docs/gant.md
项目进度或甘特图相关文档，通常用于描述开发计划、阶段安排和任务拆分。它更偏管理视角，不是业务代码的一部分。

### docs/Project Charter-冯俊财.md
项目章程文档，记录项目目标、范围、组织和约束条件，属于项目管理材料。

### docs/repo.md
当前这份仓库架构说明文档，用于系统性解释仓库结构、目录职责和关键文件作用，方便新成员快速上手。

## 4. 数据目录作用

### data/
存放示例数据和批改案例，包括作业、实验报告、题目要求等真实或模拟材料。这个目录主要用于演示批改、文档分析和练习生成等功能的输入样本。

### data/作业、实验报告批改案例/
批改案例主目录，提供作业和实验报告相关样本。

### data/作业、实验报告批改案例/面向对象程序设计（Java）（作业）/
Java 作业批改示例目录，包含题目 PDF 和批改后的文档，适合验证作业批改和批注展示能力。

### data/作业、实验报告批改案例/计算机科学与技术专业导论（实验报告）/
实验报告批改示例目录，包含实验题目、原始素材和批改后的文档，适合验证文档理解、定位批注和成绩反馈能力。

## 5. 后端目录架构

后端采用分层结构，核心分为入口层、配置与基础设施层、API 路由层、领域模型层、Agent 与 LLM 抽象层、异步任务层和迁移层。

### backend/main.py
FastAPI 应用入口。负责创建应用实例、配置 CORS、注册所有 API 路由，并提供健康检查接口。它是后端服务真正启动的入口文件。
> CORS：浏览器的跨域访问安全机制，全称：Cross-Origin Resource Sharing。后端需要配置 CORS 以允许前端应用访问 API。
> 注册API路由：把每个功能模块的接口文件挂到著应用上，让这些接口真正生效。

### backend/pyproject.toml
后端依赖和构建配置文件，声明 Python 版本、运行依赖和开发依赖。它定义了 FastAPI、SQLAlchemy、Celery、LLM SDK、文档解析和 MinIO 等后端所需组件。

### backend/Dockerfile
后端镜像构建文件，用于把后端服务打包到容器中，供 Docker Compose 或部署环境使用。

### backend/alembic.ini
Alembic 迁移配置文件，定义数据库迁移所需的基础设置。
> Alembic 是 Python 生态里面配合 SQLAlchemy 使用的数据库迁移工具。它可以根据数据库模型的变化自动生成迁移脚本，并执行这些脚本来更新数据库结构。
> 配置迁移脚本目录
> 日志规格
> 数据库连接方式

> 即 Alembic 的 启动参数配置文件

### backend/alembic/env.py *配置层*
Alembic 迁移运行环境脚本，负责把数据库模型加载到迁移上下文中，支撑自动生成和执行迁移脚本。
> 导入SQLAlchemy模型和所有模型，了解当前代码的目标表格结构
> 创建迁移上下文
> 把信息可以传递给Alembic

### backend/alembic/script.py.mako *运行层*
Alembic 迁移脚本模板文件，定义新建迁移版本时生成的脚本格式。

### backend/.env.example *模板层*
环境变量示例文件，列出数据库、Redis、MinIO 和 LLM API Key 等配置项，便于复制到本地 .env 并修改。

## 6. backend/core 目录

这个目录存放后端基础设施能力，包括配置、数据库和认证。

### backend/core/config.py
系统配置中心。使用 Pydantic Settings 读取环境变量，管理应用名、API 前缀、数据库连接、Redis、MinIO、LLM Provider、Celery 和 CORS 配置。它是整个后端配置的统一入口。
> 代码程序读取逻辑
### backend/core/database.py
数据库连接与会话管理文件。负责创建异步 SQLAlchemy 引擎、会话工厂和通用数据库依赖 get_db()。它是后端访问 PostgreSQL 的基础。

### backend/core/security.py
认证与安全工具文件。负责密码加密、密码验证、JWT Token 生成以及当前用户解析。它支撑登录、鉴权和受保护接口访问。

### backend/core/__init__.py
Python 包标记文件，表明 core 是一个可导入包。一般不承载业务逻辑。

## 7. backend/api 目录

这个目录是后端 HTTP 接口层，按业务功能拆分路由。

### backend/api/__init__.py
API 包标记文件，用于让 api 目录成为 Python 包。

### backend/api/routes/auth.py
认证接口路由。提供注册、登录和获取当前用户信息的接口，是用户身份体系的入口。

### backend/api/routes/courses.py
课程管理路由。负责课程创建、课程列表、课程详情、选课、知识点管理和课程资料上传，是课程域的核心接口。

### backend/api/routes/agents.py
Agent 管理路由。用于管理课程相关的 Agent 模板、实例和工作流，是通用 Agent 架构的接口层。

### backend/api/routes/assignments.py
作业管理路由。负责作业创建、提交、批改结果查询和批注查询，是作业流程的核心接口。

### backend/api/routes/chat.py
智能答疑路由。负责创建会话、保存聊天消息和查询历史消息，是课程问答的入口。

### backend/api/routes/analytics.py
学情分析路由。用于提供学生掌握度、薄弱点、班级报告和预警信息，是学情看板的后端接口。

### backend/api/routes/exercises.py
练习生成路由。负责根据知识点生成练习、提交练习作答和查询题库，是“测-评-练”闭环的一部分。

### backend/api/routes/platform.py
平台对接路由。用于适配超星、钉钉等外部平台连接、回调和嵌入入口，是外部集成层。

### backend/api/routes/__init__.py
路由包标记文件。

## 8. backend/models 目录

这个目录定义系统的领域模型，是后端业务数据结构的核心。

### backend/models/user.py
用户模型文件。定义用户角色和用户实体，用于区分学生、教师和管理员。

### backend/models/course.py
课程域模型文件。定义课程、选课关系、知识点、知识关系、课程资源和资源切片等实体，是课程知识体系和资源检索的基础。

### backend/models/agent.py
Agent 域模型文件。定义 Agent 模板、Agent 实例和工作流，支撑“按课程快速构建 Agent”的设计目标。

### backend/models/chat.py
聊天域模型文件。定义聊天会话和聊天消息，用于保存答疑历史、消息内容和引用元数据。

### backend/models/assignment.py
作业与批改域模型文件。定义作业、提交、批改结果和批注信息，是作业智能批改的核心数据结构。

### backend/models/exercise.py
练习域模型文件。定义题库题目、生成题目和练习尝试记录，用于练习推荐、生成和作答分析。

### backend/models/learning.py
学情分析域模型文件。定义学生知识掌握度和学情预警，用于记录个体与班级的学习状态。

### backend/models/platform.py
平台对接模型文件。定义外部平台连接配置，用于保存超星、钉钉等平台的接入信息。

### backend/models/__init__.py
模型包标记文件。

## 9. backend/agent_core 目录

这个目录是 AI Agent 能力抽象层，用来统一不同课程 Agent 的开发方式。

### backend/agent_core/agent_base.py
Agent 基类文件。定义统一的 EduAgentBase，以及答疑 Agent、批改 Agent 和练习 Agent 的基类扩展。它是课程 Agent 的开发骨架，负责把对话、批改、分析、生成等能力统一到一个抽象接口里。

### backend/agent_core/llm_provider.py
大模型提供者抽象文件。封装不同 LLM Provider 的调用方式，支持通义千问、智谱和 DeepSeek 等后端模型切换。它的作用是把具体模型 API 与上层 Agent 逻辑解耦。

### backend/agent_core/__init__.py
Agent 核心包标记文件。

### backend/agent_core/tools/__init__.py
Agent 工具包入口文件，预留给工具注册和扩展使用。

## 10. backend/workers 目录

这个目录放异步任务处理逻辑，主要给文档处理和批改任务使用。

### backend/workers/celery_app.py
Celery 应用配置文件。负责初始化 Celery、设置 Redis 作为 broker 和 result backend，以及定义任务路由和队列分配规则。
> Celery 是 Python 生态中常用的分布式任务队列框架，支持异步执行和定时任务。这个文件是 Celery 任务系统的核心配置入口。
### backend/workers/embedding_task.py
资料处理异步任务文件。用于把课程文件解析、切块、向量化并写入数据库，是资料检索和 RAG 的基础任务入口。

### backend/workers/grading_task.py
作业批改异步任务文件。用于把提交作业转入异步批改流程，后续可扩展为自动评分、批注生成和知识点掌握度更新。

### backend/workers/__init__.py
Worker 包标记文件。

## 11. backend/education 目录

### backend/education/__init__.py
教育算法或教学智能模块的包入口。当前更像预留目录，用于未来放置作业批改、学情分析、练习生成等算法实现。

## 12. backend/platform_adapter 目录

### backend/platform_adapter/__init__.py
平台适配层包入口。用于未来封装超星、钉钉等平台的标准化接入逻辑。

## 13. backend/tests 目录

### backend/tests/__init__.py
测试包标记文件。说明测试目录已预留，但当前还没有完整测试用例。

## 14. 前端目录架构

前端采用 React + TypeScript + Vite + Ant Design 的组合，页面按功能拆分，整体通过路由和布局组件拼装成一个统一管理台。

### frontend/package.json
前端依赖与脚本配置文件，定义了开发、构建、预览和 lint 命令，同时声明了 React、Ant Design、ECharts、React Router、Zustand 等依赖。

### frontend/index.html
Vite 的 HTML 入口文件，作为前端应用挂载容器。

### frontend/vite.config.ts
Vite 构建配置文件，定义开发服务器和打包相关设置。

### frontend/tsconfig.json
TypeScript 配置文件，定义前端项目的编译规则和路径约束。

### frontend/src/main.tsx
前端应用入口。负责挂载 React 根组件，并包裹路由容器，是前端真正启动的入口文件。

### frontend/src/App.tsx
前端路由总入口。根据登录状态决定展示登录页还是主应用，并定义所有功能页面的路由关系。

### frontend/src/index.css
全局样式文件，用于定义页面基础样式、布局重置和统一视觉规范。

### frontend/src/vite-env.d.ts
Vite 环境类型声明文件，用于 TypeScript 识别 Vite 的全局类型定义。

### frontend/src/hooks/useAuthStore.ts
认证状态存储文件，通常基于 Zustand 保存 token、用户信息和退出登录逻辑，是前端鉴权状态的核心。

### frontend/src/services/api.ts
前端 API 封装文件，负责与后端接口交互，统一管理请求实例、鉴权头和接口调用方法。

### frontend/src/components/Layout/MainLayout.tsx
主布局组件。提供侧边栏、顶部栏和内容区，是登录后页面的统一壳子。

## 15. frontend/src/pages 目录

这个目录按业务页面拆分。大多数页面目前是功能占位或正在逐步实现的页面壳，和前端设计说明中的目标功能一一对应。

### frontend/src/pages/Login/index.tsx
登录页。负责用户登录入口，通常对应认证流程。

### frontend/src/pages/Dashboard/index.tsx
仪表盘页面。用于展示课程数、学生数、待批改数量、预警数等概览信息。

### frontend/src/pages/CourseManage/index.tsx
课程管理页面。用于管理课程、课件和知识点。

### frontend/src/pages/Chat/index.tsx
智能答疑页面。用于课程问答、历史会话和流式聊天展示。

### frontend/src/pages/Assignment/index.tsx
作业管理页面。用于作业创建、提交、查看提交记录和批改状态。

### frontend/src/pages/GradingResult/index.tsx
批改结果页面。用于展示作业批注、评分、错误位置和详细反馈。

### frontend/src/pages/Analytics/index.tsx
学情分析页面。用于展示学生掌握度、薄弱点、预警和班级分析图表。

### frontend/src/pages/Exercises/index.tsx
练习中心页面。用于生成练习、做题和查看练习报告。

### frontend/src/pages/AgentBuilder/index.tsx
Agent 构建器页面。用于可视化配置课程 Agent、工具和工作流。

### frontend/src/pages/PlatformConfig/index.tsx
平台配置页面。用于管理超星、钉钉等平台连接与嵌入配置。
 