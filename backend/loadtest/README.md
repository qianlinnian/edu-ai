# EduAI Load Test

这套压测入口基于当前仓库真实 API，而不是外部草稿文档中的旧路径。

## 覆盖范围

默认 `locustfile.py` 只压同步、可重放、不会直接打第三方 LLM 的主链路：

- `POST /api/v1/auth/login`
- `GET /api/v1/courses`
- `GET /api/v1/courses/{id}`
- `GET /api/v1/courses/{id}/resources`
- `GET /api/v1/courses/{id}/resources/{resource_id}/download`
- `GET /api/v1/chat/sessions?course_id=...`
- `GET /api/v1/assignments?course_id=...`
- `GET /api/v1/exercises/pool?course_id=...`

默认不压这些接口：

- `POST /api/v1/chat/send`
- `POST /api/v1/chat/send-stream`
- `POST /api/v1/assignments/{id}/submit`
- `POST /api/v1/exercises/generate`

原因：

- 会打真实 LLM 或走 Celery 异步链路
- 500 并发直接压第三方模型接口不可靠，也容易限流和计费失真

## 测试前准备

先准备最小测试数据：

```bash
cd backend
source ~/miniconda3/etc/profile.d/conda.sh
conda activate edu
python seed.py
```

`seed.py` 默认会创建：

- 教师：`teacher_zhang`
- 学生：`student_01` 到 `student_10`
- 默认密码：`123456`

如果要让 500 并发用户各自独立登录，建议先扩充测试学生数，再把 `EDUAI_USER_COUNT` 调大。

## 安装 Locust

推荐在独立压测机执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install locust==2.31.0
```

## 环境变量

默认脚本读取这些环境变量：

- `EDUAI_USERNAME_PREFIX`
  - 默认：`student_`
- `EDUAI_PASSWORD`
  - 默认：`123456`
- `EDUAI_USER_COUNT`
  - 默认：`10`
- `EDUAI_COURSE_ID`
  - 默认：`0`
  - `0` 代表登录后自动取第一个已选课程

示例：

```bash
export EDUAI_PASSWORD=123456
export EDUAI_USER_COUNT=10
export EDUAI_COURSE_ID=0
```

## 运行方式

### 1. 固定 500 并发，手工指定

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  -u 500 \
  -r 50 \
  --run-time 10m \
  --host http://114.116.207.63
```

### 2. 使用内置 500 压测曲线

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  --class-picker \
  --host http://114.116.207.63
```

在 Web UI 中选择：

- User class: `AuthenticatedStudentUser`
- Shape class: `Baseline500Shape`

### 3. 导出报告

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  -u 500 \
  -r 50 \
  --run-time 10m \
  --host http://114.116.207.63 \
  --csv backend/loadtest/results/loadtest-500 \
  --html backend/loadtest/results/loadtest-500.html
```

## 结果判读建议

第一轮只看主链路基线：

- `courses.list`
- `courses.detail`
- `resources.list`
- `chat.sessions.list`
- `assignments.list`
- `exercises.pool`

重点观察：

- P95 / P99
- 5xx 比例
- 登录失败比例
- 下载接口是否拖慢整体吞吐

## 当前限制

- 仓库当前没有为 `analytics` / `chat send` / `exercise generate` 默认准备好压测前置能力
- 如果要压这些接口，需要先准备：
  - 已发布的课程 Agent / Workflow 能力
  - 独立 mock LLM 或严格限流
  - Celery 队列监控
