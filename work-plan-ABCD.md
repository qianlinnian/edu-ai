# EduAI Work Plan ABCD

更新时间：2026-06-03

## 1. 先澄清：哪些问题是“代码事实”，哪些是“完成度判断”

### 1.1 可以直接从代码确认的事实

- `exercises/pool` 当前没有鉴权，也没有课程访问校验。
  - 文件：`backend/api/routes/exercises.py`
  - 现状：`list_exercise_pool(course_id: int, db: AsyncSession = Depends(get_db))`
  - 事实：没有 `get_current_user`，没有角色限制，没有选课校验

- 教师端学情页“选中学生”后，预警请求没有带 `student_id`。
  - 文件：`frontend/src/pages/Analytics/index.tsx`
  - 现状：`loadStudentSlice()` 内调用 `analyticsAPI.getAlerts(courseId)`
  - 事实：请求只按课程查，不按学生查

- 平台适配当前是“模拟接入”。
  - 文件：`backend/api/routes/platform.py`
  - 现状：
    - 超星：`POST /platform/chaoxing/lti-launch`
    - 钉钉：`GET /platform/dingtalk/auth`
    - 后端签发 token，返回 `widget_url`
  - 事实：代码和文档都明确写了 `simulated`

- 钉钉 webhook 当前只是占位响应。
  - 文件：`backend/api/routes/platform.py`
  - 现状：接收 JSON 后返回固定文本消息
  - 事实：没有把 webhook 事件真正写回业务链路

- Agent Builder 当前是“配置映射器”。
  - 文件：
    - `frontend/src/pages/AgentBuilder/index.tsx`
    - `backend/models/agent.py`
  - 现状：工作流会被校验并映射成 Agent 运行配置
  - 事实：当前运行时不是通用 DAG 执行引擎

### 1.2 属于“完成度判断”的内容

- “超星/钉钉适配做得不够完善”
  - 这句话不是说“完全没做”
  - 更准确的说法是：
    - 当前已经完成“模拟接入闭环”
    - 但不是“真实平台联调闭环”

- “平台回流没有做好”
  - 更准确的说法是：
    - 当前已有启动/认证入口
    - 但没有把 webhook、成绩/预警回传、真实签名校验做成完整生产链路

- “异常场景与错误提示做得不够”
  - 更准确的说法是：
    - 已经做了第一层
    - 但还没系统化覆盖所有高频边界场景

## 2. 当前阶段目标

当前目标不是再扩新系统，而是：

1. 修掉高优先级代码问题
2. 收口前后端主链路
3. 统一项目口径
4. 进入部署与回归验证阶段

## 3. 统一权限规则

当前建议统一按下面规则执行。

### 3.1 课程访问

- `ADMIN`：可访问任意课程
- `TEACHER`：仅可访问自己任课课程
- `STUDENT`：仅可访问自己已选课程

公共实现：
- `backend/core/permissions.py`
- `ensure_course_access`
- `ensure_course_manager`

### 3.2 学情访问

- `ADMIN`：可看任意课程、任意学生
- `TEACHER`：可看自己课程的班级报表，也可看该课程任一学生
- `STUDENT`：只能看自己

公共实现：
- `backend/core/permissions.py`
- `ensure_student_or_teacher_access`

### 3.3 提交记录访问

- `ADMIN`：可看任意提交
- `TEACHER`：可看自己课程下的提交
- `STUDENT`：只能看自己的提交

公共实现：
- `backend/core/permissions.py`
- `ensure_submission_access`

## 4. A / B / C / D 详细工作方案

## 4.1 A：AI 架构师 / 后端工程师

### 目标

- 统一 AI 主链路口径
- 保证学情、练习、批改、Agent Builder 的解释与实现一致
- 决定哪些能力作为“当前边界”写入文档

### A 需要做什么

#### A1. 复核当前 AI 主链路

覆盖范围：

- `backend/agent_core/agent_base.py`
- `backend/agent_core/rag_chain.py`
- `backend/workers/grading_task.py`
- `backend/education/analytics_engine.py`
- `backend/education/exercise_engine.py`

要确认的点：

- QAAgent 的输入、RAG、LLM 输出链路是否自洽
- 批改结果结构是否稳定
- 学情更新与 alerts 刷新是否闭环
- 练习生成失败时的 fallback 是否符合当前项目口径

验收标准：

- 能用 1 张图解释“问答 / 批改 / 学情 / 练习”主链路
- 能回答“哪里是真实能力，哪里是兜底能力”

#### A2. 统一 Agent Builder 口径

当前代码事实：

- 只支持把工作流映射为 Agent 配置
- 当前发布规则是线性 QA 映射

需要输出的统一说法：

- 当前 Agent Builder 是“可视化 Agent 配置器”
- 当前不宣称“通用 DAG 运行引擎”

涉及文件：

- `frontend/src/pages/AgentBuilder/index.tsx`
- `backend/models/agent.py`
- 相关文档说明

#### A3. 统一批注能力口径

当前代码事实：

- 批改结果里有 `annotations`
- annotation 里有 `position`
- 前端当前展示为批注列表

建议统一说法：

- 当前支持“带位置数据的批注结果”
- 当前前端展示为“批注列表 + 位置信息”
- 当前不宣称“复杂文档原位高亮渲染”

## 4.2 B：后端工程师

### 目标

- 修高优先级后端问题
- 收口权限与接口边界
- 为部署联调清理明显风险

### B 需要做什么

#### B1. 修 `exercises/pool` 权限问题

当前接口：

```http
GET /api/v1/exercises/pool?course_id={id}
```

当前问题：

- 无鉴权依赖
- 无角色限制
- 无课程访问校验

建议改法：

1. 给接口增加：

```python
user: User = Depends(get_current_user)
```

2. 查询课程：

```python
course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
```

3. 没有课程则：

```python
raise HTTPException(status_code=404, detail="Course not found")
```

4. 按统一权限规则校验：

- `ADMIN` 放行
- `TEACHER` 必须是课程教师
- `STUDENT` 必须已选课

建议直接复用：

- `ensure_course_access(db, course=course, user=user)`

涉及文件：

- `backend/api/routes/exercises.py`

验收标准：

- 未登录请求被拒绝
- 非本课程教师被拒绝
- 未选课学生被拒绝
- 合法学生/教师可正常获取题库

#### B2. 配合修复 Analytics 按学生过滤

后端接口已支持：

```http
GET /api/v1/analytics/alerts?course_id={id}&student_id={id}
```

当前事实：

- `backend/api/routes/analytics.py` 已有 `student_id` 参数
- 但前端没有在教师选学生时传进去

B 的任务：

- 确认后端对 `course_id + student_id` 查询逻辑可用
- 如有必要补测试

#### B3. 部署前接口回归

B 需要重点回归这些接口：

- `GET /api/v1/courses`
- `GET /api/v1/courses/{id}/resources`
- `GET /api/v1/courses/{id}/resources/{resource_id}/download`
- `POST /api/v1/assignments/{assignment_id}/submit`
- `GET /api/v1/analytics/alerts`
- `POST /api/v1/exercises/generate`
- `GET /api/v1/exercises/pool`
- `POST /api/v1/platform/chaoxing/lti-launch`
- `GET /api/v1/platform/dingtalk/auth`

## 4.3 C：前端工程师

### 目标

- 完成页面联调收口
- 保证页面文案与系统实际能力一致
- 统一高频异常提示

### C 需要做什么

#### C1. 修复教师端学情页的学生预警问题

当前前端代码：

- `analyticsAPI.getAlerts(courseId)`

应改为支持：

```ts
getAlerts(courseId?: number, studentId?: number)
```

建议修改：

文件：
- `frontend/src/services/api.ts`
- `frontend/src/pages/Analytics/index.tsx`

建议接口封装改成：

```ts
getAlerts: (courseId?: number, studentId?: number) =>
  api.get('/analytics/alerts', { params: { course_id: courseId, student_id: studentId } })
```

然后在教师端单学生视角里：

```ts
analyticsAPI.getAlerts(courseId, studentId)
```

验收标准：

- 不选学生时看班级预警
- 选学生后只看该学生预警

#### C2. 统一页面口径

需要统一这些页面的文案：

- `PlatformConfig`
- `Widget`
- `AgentBuilder`
- `GradingResult`

统一要求：

- 平台接入写“模拟接入”
- Agent Builder 写“可视化配置 / 发布映射”
- 批注页写“批注列表 / 位置信息”

#### C3. 错误提示收口

当前已经有：

- `getErrorMessage`

还要做的：

- 检查高频失败场景是否都走统一提示
- 检查超时、401、worker 未启动、课程为空、资源为空时的页面反馈

建议重点检查页面：

- `CourseManage`
- `Chat`
- `Assignment`
- `Analytics`
- `Exercises`

## 4.4 D：测试与文档工程师

### 目标

- 把“真实完成度”和“当前边界”写清楚
- 整理部署前测试记录
- 确保答辩材料不会说过头

### D 需要做什么

#### D1. 统一文档口径

重点更新：

- `4.10` 写成上传 / 下载 / 删除
- 平台适配写成模拟接入
- Agent Builder 写成配置器
- 批注能力写成“带位置数据的批注 + 列表展示”

建议核对文档：

- `docs/platform-adapter-simulated.md`
- `docs/M4-交付材料清单与追踪矩阵.md`
- `docs/rbs-wbs-schedule+gantt.md`
- `docs/Intro.md`
- `.vscode/codex-problem.md`

#### D2. 测试记录

至少补清楚：

- 主流程可用性测试
- 异常场景测试
- 部署联调测试
- 当前性能测试级别

当前建议写法：

- 不要写“已证明支持 500 并发”
- 可以写“当前已有小规模基线测试，部署后继续补压测”

#### D3. 答辩边界说明

建议在答辩材料中明确写：

- 哪些是完整主链路
- 哪些是模拟接入
- 哪些是当前版本边界

## 5. 当前接口责任划分

### 5.1 B 负责的后端接口

- `GET /api/v1/exercises/pool`
- `GET /api/v1/analytics/alerts`
- 课程资源相关接口

### 5.2 C 负责的前端接口接入

- `analyticsAPI.getAlerts`
- `exerciseAPI.listPool`
- 平台接入相关页面展示接口

### 5.3 A 负责的链路说明接口

- `POST /api/v1/exercises/generate`
- `POST /api/v1/exercises/attempt`
- `POST /api/v1/chat/send-stream`
- Agent Builder 发布链路

## 6. 当前建议执行顺序

1. B 先修 `GET /exercises/pool` 权限问题
2. C 接着修学情页 `alerts` 传 `student_id`
3. A 统一练习 / 学情 / Agent Builder 口径
4. D 同步更新文档和测试材料
5. 四人一起做部署联调回归

## 7. 什么时候可以认为项目“基本完成”

满足以下条件即可认为开发基本完成，进入部署与答辩阶段：

- `exercises/pool` 权限问题修复
- 学情页按学生过滤预警修复
- 平台适配口径统一为模拟接入
- Agent Builder 口径统一为配置器
- 主页面联调通过
- 文档与测试记录同步更新
