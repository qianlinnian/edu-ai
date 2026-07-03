# EduAI 项目介绍

EduAI 是一个面向课程教学场景的可嵌入式 AI Agent 平台。项目目标是把课程资料、教学任务、学生学习行为和多类 AI Agent 能力组织到统一平台中，使不同课程能够复用问答、作业批改、练习生成和学情分析等能力。

## 项目定位

EduAI 是一个课程级 AI Agent 架构平台。它围绕“课程”组织知识库、Agent 配置、学生权限、作业、练习和分析结果，并提供可嵌入外部教学平台的模拟接入能力。

核心定位：

- 跨课程复用：同一套 Agent 能力可面向不同课程配置。
- 课程知识库优先：问答和批改尽量基于课程资料和教师配置。
- 教师可配置：教师可以配置课程 Agent、模型、知识库、能力开关和工作流。
- 学生侧闭环：学生可以问答、提交作业、生成练习并查看学习反馈。
- 平台可嵌入：通过 Widget 和模拟平台接口支持外部教学平台接入演示。

## 核心功能

### 课程知识库与 RAG 问答

教师可以上传课程资料，系统解析文档内容并构建课程级知识库。学生或教师提问时，系统优先检索课程资料，并把检索上下文传入问答 Agent，减少脱离课程内容的回答。

相关模块：

- `backend/workers/embedding_task.py`
- `backend/agent_core/rag_chain.py`
- `backend/api/routes/chat.py`
- `frontend/src/pages/Chat`

### 作业提交与智能批改

系统支持文本作业和文档附件作业提交。批改链路会结合题目描述、参考答案、评分标准、课程材料上下文和学生提交内容，输出分数、评语和批注。

相关模块：

- `backend/api/routes/assignments.py`
- `backend/workers/grading_task.py`
- `backend/agent_core/agent_base.py`
- `frontend/src/pages/Assignment`

### 练习生成与学习闭环

系统可以根据课程知识点、学生薄弱项和历史作答情况生成练习，并记录学生作答结果，用于后续学情分析和个性化练习推荐。

相关模块：

- `backend/api/routes/exercises.py`
- `backend/education`
- `frontend/src/pages/Exercises`

### 学情分析与预警

系统统计学生练习、作业和知识点掌握情况，支持教师查看班级报告、学生薄弱点和预警信息。

相关模块：

- `backend/api/routes/analytics.py`
- `frontend/src/pages/Analytics`

### Agent Builder 与课程 Agent 发布

教师可以创建课程 Agent，配置模型、Provider、能力、工作流和发布状态。发布后的 Agent 会影响课程问答、练习和批改等运行时行为。

相关模块：

- `backend/api/routes/agents.py`
- `backend/agent_core`
- `frontend/src/pages/AgentBuilder`

### 平台模拟接入与 Widget

项目提供超星、钉钉等平台的模拟接入口径，并支持课程问答 Widget 的嵌入演示。

相关模块：

- `backend/platform_adapter`
- `backend/api/routes/platform.py`
- `frontend/src/pages/Widget`

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | FastAPI、SQLAlchemy、Alembic、Celery |
| 数据库 | PostgreSQL、pgvector |
| 缓存/任务 | Redis |
| 文件存储 | MinIO |
| 前端 | React、Vite、TypeScript、Ant Design |
| AI 能力 | DashScope / DeepSeek / Zhipu 等 Provider 封装 |
| 部署 | Docker Compose |

## 仓库结构

```text
backend/             后端 API、Agent、RAG、Worker、测试
frontend/            React 前端页面
data/                评测数据、课程数据和样例
docs/                RBS/WBS、测试报告、设计和交付文档
docker-compose.yml   PostgreSQL、Redis、MinIO、后端和 Worker 编排
README.md            启动和运行说明
```

## 测试与验证材料

仓库中保留了课程项目最终测试文档所需的主要证据：

- 后端自动化测试：`backend/tests`
- API 级 E2E 冒烟测试：`backend/script/test_api.py`
- RBS 覆盖矩阵和最终测试文档：`docs/test-reports`
- 问答评测数据：`docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md`
- 批改评测结果：`docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json`
- 性能测试结果：`docs/test-reports/autodl-20260628/round2`

项目最终测试口径是 requirement-level coverage：每条 final RBS 叶子需求需要有对应测试或验证证据。它不等同于声明代码覆盖率达到 100%。

## 推荐阅读顺序

1. `README.md`：启动项目。
2. `docs/rbs-wbs-schedule+gantt.md`：查看 final RBS/WBS。
3. `docs/test-reports`：查看最终测试文档、覆盖矩阵和评测结果。
4. `backend/tests`：查看后端自动化测试。
5. `backend/script/test_api.py`：查看 API 级 E2E 冒烟测试。

## 当前项目状态

EduAI 已完成课程项目所需的核心演示能力。系统支持本地开发、服务器部署演示和 API 级核心链路验证。
