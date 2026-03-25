# EduAI - 可嵌入式跨课程AI Agent通用架构平台

## 一、技术架构

### 1.1 整体架构图

```
┌──────────────────────────────────────────────────────────────┐
│                        用户层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Web管理端 │  │超星嵌入H5│  │钉钉H5小程序│  │ iframe Widget│ │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────┬───────┘ │
└────────┼─────────────┼─────────────┼───────────────┼─────────┘
         │             │             │               │
         └─────────────┴──────┬──────┴───────────────┘
                              │ HTTPS / WebSocket
┌─────────────────────────────┼────────────────────────────────┐
│                        Nginx 反向代理                         │
└─────────────────────────────┼────────────────────────────────┘
                              │
┌─────────────────────────────┼────────────────────────────────┐
│                     FastAPI 应用层                            │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ Auth API │  │ Course API│  │  Chat API │  │ Agent API │   │
│  ├──────────┤  ├───────────┤  ├───────────┤  ├───────────┤   │
│  │Assign API│  │Analytics  │  │Exercise   │  │Platform   │   │
│  │          │  │API        │  │API        │  │Adapter API│   │
│  └──────────┘  └───────────┘  └───────────┘  └───────────┘   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│                    核心引擎层                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ Agent SDK       │  │ 精细化智能引擎   │  │ 知识中间件    │  │
│  │ ├ AgentBase     │  │ ├ 批改引擎       │  │ ├ 文档解析    │ │
│  │ ├ QAAgent       │  │ ├ 学情分析       │  │ ├ 分块索引    │ │
│  │ ├ GradingAgent  │  │ ├ 练习生成       │  │ ├ 向量检索    │ │
│  │ └ ExerciseAgent │  │ └ 教学决策       │  │ └ 知识图谱    │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘  │
└───────────┼────────────────────┼───────────────────┼─────────┘
            │                    │                   │
┌───────────┼────────────────────┼───────────────────┼─────────┐
│           │             LLM 适配层                 │          │
│  ┌────────┴─────┐ ┌──────────┐ ┌──────────┐ ┌────────┴────┐  │
│  │千问 qwen-max │ │qwen-vl   │ │DeepSeek  │ │GLM-4 (备选) │  │
│  └──────────────┘ └──────────┘ └──────────┘ └─────────────┘  │
└──────────────────────────────────────────────────────────────┘
            │                    │                   │
┌───────────┼────────────────────┼───────────────────┼─────────┐
│                         数据层                                │
│  ┌─────────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐   │
│  │PostgreSQL 16│  │  Redis 7 │  │ MinIO  │  │  Celery    │   │
│  │+ pgvector   │  │ 缓存/会话 │  │文件存储 │  │ 异步任务队列│   │
│  └─────────────┘  └──────────┘  └────────┘  └────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈明细

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | React 18 + TypeScript | 主框架 |
| | Vite 5 | 构建工具 |
| | Ant Design 5 + ProComponents | UI组件库 |
| | Zustand | 状态管理（轻量替代Redux） |
| | React Router 6 | 路由 |
| | ECharts | 学情数据可视化 |
| | React Flow | Agent可视化构建器 |
| | react-markdown + react-syntax-highlighter | 答疑Markdown渲染 |
| **后端** | FastAPI (Python 3.11+) | Web框架，原生async |
| | SQLAlchemy 2.0 + asyncpg | 异步ORM |
| | Alembic | 数据库迁移 |
| | Pydantic 2 | 数据校验 |
| | python-jose + passlib | JWT认证 |
| **AI引擎** | LangChain 0.3 | LLM编排框架 |
| | LangGraph | Agent工作流编排 |
| | 通义千问 qwen-max | 主力LLM |
| | 通义千问 qwen-vl-max | 图像理解（作业批改） |
| | text-embedding-v3 | 向量化模型 |
| | DeepSeek deepseek-chat | 代码批改增强（OpenAI兼容接口） |
| | 智谱 GLM-4 | 备选LLM |
| **数据** | PostgreSQL 16 + pgvector | 关系数据 + 向量存储 |
| | Redis 7 | 缓存、会话、Celery Broker |
| | MinIO | 课件/作业文件存储 |
| | Celery | 异步任务（批改、Embedding） |
| **部署** | Docker Compose | 一键编排 |
| | Nginx | 反向代理 + 静态资源 |

### 1.3 核心模块说明

**Agent SDK（`agent_core/`）**
- `AgentBase`：所有Agent基类，定义chat/grade/analyze/generate标准接口
- `LLMProvider`：LLM适配层，支持通义千问/DeepSeek/智谱一键切换
- `QAAgent`：RAG增强答疑（向量检索 + BM25 + Rerank混合策略）
- `GradingAgent`：多模态批改（文本/代码/图像）
- `ExerciseAgent`：个性化练习生成

**知识中间件**
- 文档解析：PDF/Word/PPT/Markdown → 文本提取
- 分块策略：RecursiveCharacterTextSplitter（overlap=200）
- 向量存储：pgvector（余弦相似度，HNSW索引）
- 知识图谱：知识点关联关系存储

**精细化智能引擎（`education/`）**
- 批改引擎：定位错误位置 + 生成批注JSON → 前端渲染为教师批注样式
- 学情分析：基于知识点掌握度矩阵，多维度评估 + 动态预警
- 练习生成：根据薄弱知识点，Prompt模板动态生成 + 难度自适应

---

## 二、项目结构

```
edu-ai/
├── backend/                    # Python后端
│   ├── main.py                 # FastAPI入口
│   ├── core/                   # 基础设施
│   │   ├── config.py           #   环境配置
│   │   ├── database.py         #   数据库连接
│   │   └── auth.py             #   JWT认证
│   ├── models/                 # 数据库模型（8个表）
│   │   ├── user.py             #   用户
│   │   ├── course.py           #   课程 + 知识单元 + 资源
│   │   ├── assignment.py       #   作业 + 提交 + 批改结果
│   │   ├── chat.py             #   对话会话 + 消息
│   │   ├── analytics.py        #   学情 + 预警 + 班级报告
│   │   ├── exercise.py         #   题库 + 做题记录
│   │   ├── agent.py            #   Agent模板 + 实例 + 工作流
│   │   └── resource_chunk.py   #   文档分块 + 向量
│   ├── api/routes/             # API路由（8组）
│   ├── agent_core/             # Agent SDK（核心）
│   │   ├── agent_base.py       #   Agent基类 + QA/Grading/Exercise Agent
│   │   ├── llm_provider.py     #   LLM适配层（千问/智谱）
│   │   └── tools/              #   Agent工具集
│   ├── education/              # 教学智能引擎
│   │   ├── grading_engine.py   #   批改引擎（待实现）
│   │   ├── analytics_engine.py #   学情分析引擎（待实现）
│   │   └── exercise_engine.py  #   练习生成引擎（待实现）
│   ├── platform_adapter/       # 平台适配器
│   │   ├── chaoxing.py         #   超星LTI/iframe（待实现）
│   │   └── dingtalk.py         #   钉钉H5/机器人（待实现）
│   ├── workers/                # Celery异步任务
│   │   ├── celery_app.py       #   Celery配置
│   │   ├── grading_task.py     #   批改任务
│   │   └── embedding_task.py   #   文档向量化任务
│   ├── alembic/                # 数据库迁移
│   ├── Dockerfile
│   └── .env
├── frontend/                   # React前端
│   ├── src/
│   │   ├── App.tsx             #   路由配置（9个页面）
│   │   ├── components/
│   │   │   └── Layout/         #   侧边栏布局
│   │   ├── pages/
│   │   │   ├── Login/          #   登录/注册
│   │   │   ├── Dashboard/      #   仪表盘
│   │   │   ├── CourseManage/   #   课程管理
│   │   │   ├── Chat/           #   智能答疑
│   │   │   ├── Assignment/     #   作业管理
│   │   │   ├── GradingResult/  #   批改结果展示
│   │   │   ├── Analytics/      #   学情分析看板
│   │   │   ├── Exercises/      #   练习中心
│   │   │   ├── AgentBuilder/   #   Agent可视化构建器
│   │   │   └── PlatformConfig/ #   平台对接配置
│   │   ├── services/api.ts     #   全部API封装
│   │   └── hooks/useAuthStore  #   认证状态
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml          # PostgreSQL+Redis+MinIO+后端+Celery
└── docs/                       # 文档
```

---

## 三、27天实施计划（4人团队）

### 角色分配

| 角色 | 代号 | 主要职责 | 核心产出 |
|------|------|----------|----------|
| **后端A** | AI架构师 | Agent SDK、LLM对接、RAG答疑、批改引擎Prompt | `agent_core/`、`education/grading_engine.py` |
| **后端B** | 后端工程师 | 知识中间件、学情分析、练习生成、平台适配、异步任务 | `education/`其余、`platform_adapter/`、`workers/` |
| **前端C** | 前端工程师 | 所有页面开发、Agent构建器、嵌入式Widget | `frontend/` 全部 |
| **综合D** | 数据+文档+QA | 课程数据收集整理、测试、方案文档、PPT、视频 | `docs/`、演示数据、测试报告 |

### 各角色详细任务清单

#### 后端A— AI架构师

**核心定位**：整个项目最核心的AI能力层，决定产品质量上限

| 阶段 | 具体任务 | 产出文件 |
|------|----------|----------|
| Week1 Day1-2 | Docker环境搭建、Alembic迁移跑通、`llm_provider.py`对接通义千问API | `core/`、`llm_provider.py` |
| Week1 Day3-4 | 调通Chat接口端到端、设计Agent SDK接口规范 | `agent_base.py` |
| Week1 Day5-7 | **RAG检索链**（向量+BM25混合+Rerank+多轮记忆） | `agent_core/rag_chain.py` |
| Week2 Day8-10 | **批改引擎**：文本批注Prompt + 代码行级标注Prompt + 批注JSON格式 | `education/grading_engine.py` |
| Week2 Day11-12 | **学情分析Prompt**（与后端B协作，你负责LLM调用部分） | 学情Prompt模板 |
| Week2 Day13-14 | **练习生成Prompt**（题目格式化+答案生成+难度控制） | 练习Prompt模板 |
| Week3 Day15-16 | 图像批改（qwen-vl-max）、实验报告批改 | 多模态批改逻辑 |
| Week3 Day17-19 | LangGraph工作流引擎（Agent节点串联执行） | `agent_core/workflow.py` |
| Week3 Day20-21 | 调优全部Prompt达标（答疑≥95%、批改≥95%） | Prompt模板集 |
| Week4 Day22-27 | Bug修复、性能优化、协助部署 | — |

#### 后端B — 后端工程师

**核心定位**：数据流转与基础服务，确保数据正确流通

| 阶段 | 具体任务 | 产出文件 |
|------|----------|----------|
| Week1 Day1-2 | 完善数据库模型、写种子数据脚本（用户/课程/知识点） | `models/`、`seed.py` |
| Week1 Day3-4 | 文档解析pipeline：PDF/Word→分块→Embedding→存pgvector | `workers/embedding_task.py` |
| Week1 Day5-7 | 知识单元CRUD API、知识点关联关系存储 | `api/routes/courses.py` |
| Week2 Day8-10 | 作业提交/批改API完善、Celery批改任务调度 | `api/routes/assignments.py`、`workers/grading_task.py` |
| Week2 Day11-12 | **学情分析引擎**：掌握度计算、预警规则、班级报告聚合 | `education/analytics_engine.py` |
| Week2 Day13-14 | **练习评判**逻辑 + 掌握度动态更新（测-评-练闭环） | `education/exercise_engine.py` |
| Week3 Day15-16 | **超星LTI适配器** + **钉钉H5适配器**（模拟适配，写技术说明即可） | `platform_adapter/` |
| Week3 Day17-19 | 预置Agent模板数据、Agent实例管理API | `api/routes/agents.py` |
| Week3 Day20-21 | Redis缓存、连接池调优、性能压测 | 缓存层 |
| Week4 Day22-27 | **云服务器部署**（Docker Compose+Nginx+HTTPS）、Bug修复 | 部署脚本 |

#### 前端C — 前端工程师

**核心定位**：用户体验层，页面美观+交互流畅是评分重点

| 阶段 | 具体任务 | 产出文件 |
|------|----------|----------|
| Week1 Day1-2 | `npm install`、跑通前端、完善登录/注册页 | `Login/` |
| Week1 Day3-4 | 课程管理页（课程CRUD、文件上传、知识点树） | `CourseManage/` |
| Week1 Day5-7 | **智能答疑对话界面**（Markdown渲染、代码高亮、来源引用） | `Chat/`、`ChatWindow/` |
| Week2 Day8-10 | **作业管理页** + **批改结果展示**（文本批注、代码行标注） | `Assignment/`、`GradingResult/`、`AnnotationViewer/` |
| Week2 Day11-12 | **学情分析看板**（ECharts雷达图、热力图、预警列表） | `Analytics/` |
| Week2 Day13-14 | **练习中心**（做题界面、提交评判、练习报告） | `Exercises/` |
| Week3 Day15-16 | 嵌入式Widget（可iframe嵌入的轻量答疑/批改窗口） | `Widget/` |
| Week3 Day17-19 | **Agent可视化构建器**（react-flow拖拽画布） | `AgentBuilder/` |
| Week3 Day20-21 | 仪表盘完善、教师决策看板、UI打磨 | `Dashboard/` |
| Week4 Day22-27 | 响应式适配、动画细节、全局UI走查 | — |

#### 综合D — 数据+文档+QA

**核心定位**：保证演示效果和文档质量，这是评审看到的第一印象

| 阶段 | 具体任务 | 产出 |
|------|----------|------|
| Week1 Day1-2 | **购买云服务器**、收集2-3门课程的课件资料（用于RAG知识库演示） | 服务器、课程PDF/PPT |
| Week1 Day3-4 | 整理各课程知识点清单、准备标准问答对50题 | 知识点表、QA测试集 |
| Week1 Day5-7 | 测试答疑效果、记录准确率、反馈给后端A调Prompt | 测试报告 |
| Week2 Day8-10 | 整理企业提供的样例作业数据、标注预期批改结果 | 样例作业集 |
| Week2 Day11-12 | 准备演示用学习记录数据（模拟30+学生的学习轨迹） | 演示数据脚本 |
| Week2 Day13-14 | **端到端测试**全流程、记录Bug、验证指标 | Bug清单 |
| Week3 Day15-16 | 研究超星LTI/钉钉文档、撰写平台对接技术说明 | 技术文档 |
| Week3 Day17-19 | 辅助前端C做简单页面（Dashboard/PlatformConfig） | 页面代码 |
| Week3 Day20-21 | 集成测试、准确率验证（答疑≥95%、批改≥95%） | 验收报告 |
| Week4 Day22-25 | **撰写全部文档**：项目概要、详细方案、PPT | 文档3件套 |
| Week4 Day26-27 | **录制5分钟演示视频** + 最终提交材料打包 | 视频、提交包 |

---

### 第1周（Day 1-7）：基础架构 + 智能答疑MVP

**目标**：环境跑通 + 一门课程能够智能问答

| 天 | 后端A | 后端B | 前端C | 综合D |
|----|------------|-------|-------|-------|
| 1-2 | `docker compose up` 跑通环境，Alembic迁移建表，调通LLM API | 完善数据库模型，写种子数据脚本 | `npm install` 跑通前端，完善登录/注册页 | **购买云服务器**，收集3门课程资料 |
| 3-4 | Chat接口端到端跑通（用户发消息→LLM回复→流式返回） | 文档解析pipeline：PDF/Word→分块→Embedding→pgvector | 课程管理页（CRUD、文件上传、知识点管理） | 整理知识点清单，准备问答对50题 |
| 5-7 | **RAG检索链**（向量+BM25混合+Rerank+多轮对话） | 知识单元API完善、知识点关联 | **答疑对话界面**（Markdown、代码高亮、来源引用） | 测试答疑准确率，反馈调优 |

> **里程碑1**：上传一门课程资料 → 学生提问 → AI基于课程知识回答（准确率≥90%）

---

### 第2周（Day 8-14）：核心教学功能

**目标**：作业→批改→学情→练习 完整闭环

| 天 | 后端A | 后端B | 前端C | 综合D |
|----|------------|-------|-------|-------|
| 8-10 | **批改引擎**：文本批注Prompt + 代码行标注 + 批注JSON设计 | 作业API + Celery批改任务调度 + 图像批改(qwen-vl) | **作业管理页** + **批改结果展示**（批注渲染） | 准备样例作业，标注预期结果 |
| 11-12 | 学情分析LLM部分（生成分析报告、建议文本） | **学情引擎**：掌握度计算、预警规则、班级报告 | **学情看板**（雷达图、热力图、预警列表） | 准备演示数据 |
| 13-14 | **练习生成Prompt**（题目+答案+解析+难度控制） | 练习评判 + 掌握度更新闭环 | **练习中心**（做题、评判、报告） | 端到端测试 |

> **里程碑2**：提交作业 → AI批注式批改 → 学情分析 → 自动生成练习

---

### 第3周（Day 15-21）：平台对接 + 创新功能

**目标**：超星/钉钉嵌入 + Agent可视化构建器

| 天 | 后端A | 后端B | 前端C | 综合D |
|----|------------|-------|-------|-------|
| 15-16 | 图像/实验报告批改（多模态） | **超星LTI** + **钉钉H5**适配器 | 嵌入式Widget组件 | 研究LTI文档，撰写技术说明 |
| 17-19 | **LangGraph工作流引擎** | 预置Agent模板、实例管理API | **Agent可视化构建器**（react-flow） | 测试平台嵌入、辅助前端 |
| 20-21 | 全部Prompt调优冲刺（≥95%） | Redis缓存、性能优化 | 仪表盘完善、教师决策看板 | 集成测试 |

> **里程碑3**：超星/钉钉嵌入 + 教师拖拽构建Agent + 准确率达标

---

### 第4周（Day 22-27）：打磨 + 部署 + 交付

**目标**：上线部署 + 提交全部材料

| 天 | 全员任务 |
|----|----------|
| 22-23 | 全员Bug修复、UI打磨、答疑准确率调到≥95%、批改准确率调到≥95% |
| 24 | **云服务器部署**：Docker Compose部署 + 域名绑定 + HTTPS + Nginx配置 |
| 25 | 充实演示数据（3门课程完整数据），完整流程走通一遍 |
| 26 | 综合D主笔：①项目概要介绍 ②PPT ③项目详细方案 ④全员Review |
| 27 | **录制5分钟演示视频**（覆盖所有基本功能+创新功能）+ 最终提交 |

> **里程碑4**：可运行Demo + 全部提交材料就绪

---

## 四、关键技术指标对照

| 赛题要求 | 实现方案 | 所在模块 |
|----------|----------|----------|
| 支持≥2种教学平台嵌入 | 超星LTI + 钉钉H5（模拟适配+技术说明，赛题不要求真实对接） | `platform_adapter/` |
| 支持多类型课程 | 统一Agent SDK + 课程知识中间件 | `agent_core/` |
| 500用户并发 | FastAPI async + Redis缓存 + Celery异步 | 架构层面 |
| 微服务架构 | Docker Compose独立服务 | `docker-compose.yml` |
| 智能答疑≥95%准确率 | RAG混合检索 + Prompt优化 | `agent_core/QAAgent` |
| 批注式批改≥95%准确率 | LLM精细化批注 + 多模态 | `education/grading_engine` |
| 学情预警 | 掌握度矩阵 + 规则引擎 | `education/analytics_engine` |
| 个性化练习生成 | 知识点关联 + 动态Prompt | `education/exercise_engine` |
| 可视化Agent构建器 | react-flow拖拽编辑器 | 前端 `AgentBuilder/` |
| 教学决策支持 | 班级报告 + LLM建议 | `analytics API` |

---

## 五、风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| LLM API调用速度慢 | 用户体验差 | SSE流式输出 + Redis缓存高频问题 |
| 批改准确率不达标 | 不满足95%指标 | 分题型Prompt模板 + Few-shot示例 + 人工标注校准 |
| 超星/钉钉接口文档不全 | 对接受阻 | 赛题明确不要求真实对接，做模拟适配层+技术说明即可 |
| 时间紧张（27天） | 功能不完整 | 优先保证基本功能（答疑+批改+学情+练习），创新功能次之 |
| 演示数据不充分 | 展示效果差 | 第4人专职准备3门课程完整数据 |
