# M3 后端B任务布置：教学闭环（作业→批改→学情→练习）

面向：后端B（数据流转与基础服务），用于完成 M3 “Teaching Loop Complete” 的后端闭环交付。

## 背景与目标

M2 已完成：课程资料上传→入库→RAG 检索→QAAgent 答疑。

M3 需要完成：**作业提交 → 批改 → 学情数据更新（掌握度/预警） → 个性化练习生成/评判**，形成“测-评-练”闭环。

### 成功标准（验收口径）

1. 学生提交作业后，`submissions.status` 能从 `pending/grading` 变为 `graded`（失败能进入 `failed`）。
2. 批改完成后：
   - `grading_results` 产生或更新（含 `score/max_score/overall_comment`，可选 `knowledge_point_scores`）。
   - `submission_annotations` 产生或更新（用于前端渲染批注）。
3. 批改完成后能反哺学情：
   - `student_knowledge_mastery` 的 `attempt_count/mastery_score` 对应知识点发生变化。
   - 必要时在 `learning_alerts` 生成“薄弱知识点预警”（避免重复刷同一条未解决预警）。
4. `analytics` 与 `exercises` 现有接口可读到上述变化（不要求 UI 完成，但接口与数据要一致）。

## A/B 边界（避免打架）

- 后端A（你不需要做）：
  - 批改 Prompt/LLM 调用、多模态批改策略
  - 批注 JSON 规范（字段、坐标、严重级别）的定义与调优
- 后端B（你负责落地）：
  - 任务调度、落库、状态流转
  - 批改结果写入 `grading_results/submission_annotations`
  - 批改后掌握度/预警更新（闭环数据层）

## 你负责的文件/模块（建议直接从这里下手）

- 作业接口与任务触发：`backend/api/routes/assignments.py`
- 批改异步任务（核心）：`backend/workers/grading_task.py`
- 学情引擎与接口：`backend/education/analytics_engine.py`、`backend/api/routes/analytics.py`
- 练习引擎与接口：`backend/education/exercise_engine.py`、`backend/api/routes/exercises.py`
- 数据模型：
  - 作业/批改：`backend/models/assignment.py`
  - 学情：`backend/models/learning.py`
  - 知识点：`backend/models/course.py`（`KnowledgeUnit`）

## 任务清单（按优先级）

### P0：批改任务落库 + 闭环数据更新（必须完成）

**目标**：`grading_task.py` 在一次批改任务中完成“四件事”：

1) **写/更新** `grading_results`
- 若已有同一 `submission_id` 的记录，则更新（保证可重跑/幂等）。
- 建议写入字段：
  - `score/max_score/overall_comment/strengths/weaknesses`
  - `knowledge_point_scores`（若可获得；结构建议 `{kp_id: score}`，score 可用 0-100 或 0-1，但要统一）

2) **写/覆盖** `submission_annotations`
- 同一 `submission_id` 批改结果重跑时：先清理旧批注再写新批注，避免叠加。
- 批注字段对齐前端渲染需求：`annotation_type/position/content/severity/knowledge_point_id`

3) **更新** `student_knowledge_mastery`
- 依据批改输出中的 `knowledge_point_scores`（或用整体分数兜底）更新对应知识点的掌握度。
- 注意：
  - 首次出现知识点时应创建默认记录（`mastery_score` 初始建议 0.5）。
  - `attempt_count/correct_count/last_assessed_at` 需要同步更新。

4) **刷新/生成** `learning_alerts`（薄弱知识点预警）
- 规则：当某知识点掌握度低于阈值（建议 `0.4`）生成未解决预警。
- 去重：同一 `student_id/course_id/knowledge_unit_id` 在未解决状态下不重复创建。

**并发/事务建议**
- 将 `submission.status` 从 `pending`→`grading`→`graded/failed` 放在同一任务逻辑中，必要时加防重入判断（例如已 `graded` 可直接返回）。
- 落库操作尽量在同一事务里完成，减少“状态已 graded 但结果/批注没写全”的中间态。

### P1：补齐闭环的“观测面”（便于联调）

1) 作业相关接口补强（如需要）
- 若前端需要轮询状态：考虑加 `GET /assignments/submissions/{submission_id}` 返回 `status`（当前已有 list/submission result，可按需补）。

2) 学情接口可验证
- `GET /analytics/student/{student_id}/mastery?course_id=...`：能看到掌握度变化。
- `GET /analytics/alerts?course_id=...&student_id=...`：能看到预警生成。
- `POST /analytics/course/{course_id}/refresh-alerts`：可重算预警（用于修复历史数据）。

### P2：练习中心与掌握度更新的一致性（建议完成）

**目标**：练习 attempt 的更新口径与作业批改更新口径一致（EMA/阈值/分数比例）。

- 练习 attempt 入口：`POST /exercises/attempt`
- 建议做法：
  - attempt 更新掌握度逻辑与作业批改尽量共用同一套“score_ratio → mastery”策略
  - attempt 之后刷新一次薄弱预警（当前路由已有 refresh 调用，可确认策略一致）

## 联调脚本（最短验收路径）

建议你按以下顺序手动联调（Postman/DBeaver 均可）：

1. 创建课程、创建知识点（KnowledgeUnit），拿到 `knowledge_unit_id` 列表。
2. 创建作业（Assignment），`knowledge_points` 填入上述知识点 ID。
3. 提交作业（Submission），等待 worker 执行批改。
4. 验收数据表：
   - `submissions`：状态为 `graded`
   - `grading_results`：有该 submission 的记录
   - `submission_annotations`：有批注记录
   - `student_knowledge_mastery`：对应知识点的 `attempt_count/mastery_score` 发生变化
   - `learning_alerts`：若 mastery 低于阈值，生成预警且不重复
5. 验收接口：
   - `GET /api/v1/assignments/submissions/{submission_id}/result`
   - `GET /api/v1/assignments/submissions/{submission_id}/annotations`
   - `GET /api/v1/analytics/student/{student_id}/mastery?course_id=...`
   - `GET /api/v1/analytics/alerts?course_id=...&student_id=...`

## 交付物清单（提交 PR 时检查）

- `backend/workers/grading_task.py`：批改任务端到端完成落库+闭环更新
- （如有新增工具函数）放在 `backend/education/`，并确保不引入循环依赖
- （如有 schema 变更）新增 Alembic migration，保证一键迁移可跑通
- 更新 `docs/codex-work-log.md`（可选，但建议记录关键行为变更）

## 接口与表（速查）

### 关键接口（现有）

- 作业
  - `POST /api/v1/assignments` 创建作业（包含 `knowledge_points`）
  - `POST /api/v1/assignments/{assignment_id}/submit` 提交作业（触发异步批改）
  - `GET /api/v1/assignments/submissions/{submission_id}/result` 查看批改结果
  - `GET /api/v1/assignments/submissions/{submission_id}/annotations` 查看批注
- 学情
  - `GET /api/v1/analytics/student/{student_id}/mastery?course_id=...` 学生掌握度概览
  - `GET /api/v1/analytics/alerts?course_id=...&student_id=...` 预警列表
  - `POST /api/v1/analytics/course/{course_id}/refresh-alerts` 刷新预警
- 练习
  - `POST /api/v1/exercises/generate` 按知识点生成练习
  - `POST /api/v1/exercises/attempt` 提交作答并更新掌握度

### 关键表（现有）

- 作业链路
  - `assignments`（含 `knowledge_points`）
  - `submissions`（含 `status`）
  - `grading_results`（含 `knowledge_point_scores`）
  - `submission_annotations`（批注）
- 学情链路
  - `student_knowledge_mastery`（掌握度）
  - `learning_alerts`（预警）

