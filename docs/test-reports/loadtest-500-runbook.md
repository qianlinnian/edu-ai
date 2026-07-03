# 500 并发压测运行手册

## 目标

在服务器部署完成后，对 EduAI 当前可重放的主链路做 500 并发基线压测。

## 当前仓库真实口径

压测脚本位置：

- [backend/loadtest/locustfile.py](/D:/course/SEME/edu-ai/backend/loadtest/locustfile.py)

运行说明：

- [backend/loadtest/README.md](/D:/course/SEME/edu-ai/backend/loadtest/README.md)

## 为什么不直接用现有草稿文档

外部草稿中的多条路径和当前仓库实现不一致，例如：

- 登录不是 JSON，而是表单登录：`POST /api/v1/auth/login`
- 课程列表是：`GET /api/v1/courses`
- 作业列表是：`GET /api/v1/assignments?course_id=...`
- 练习池列表是：`GET /api/v1/exercises/pool?course_id=...`
- 聊天流式接口是：`POST /api/v1/chat/send-stream`

因此要以仓库代码为准，不然压测结果没有意义。

## 推荐执行顺序

1. 在服务端确认：
   - `eduai-backend` 正常
   - `eduai-celery` 正常
   - `postgres / redis / minio` 正常
2. 在服务端准备最小测试数据：
   - `python seed.py`
3. 在独立压测机安装 `locust`
4. 先跑 50 并发 warm-up
5. 再跑 200 并发
6. 最后跑 500 并发

## 第一轮建议命令

### 50 并发

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  -u 50 \
  -r 10 \
  --run-time 3m \
  --host http://114.116.207.63
```

### 200 并发

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  -u 200 \
  -r 20 \
  --run-time 5m \
  --host http://114.116.207.63
```

### 500 并发

```bash
locust -f backend/loadtest/locustfile.py \
  --headless \
  -u 500 \
  -r 50 \
  --run-time 10m \
  --host http://114.116.207.63
```

## 服务端观测建议

压测同时观察：

```bash
sudo systemctl status eduai-backend --no-pager
sudo systemctl status eduai-celery --no-pager
docker compose ps
```

日志：

```bash
journalctl -u eduai-backend -f
journalctl -u eduai-celery -f
docker logs -f eduai-postgres
docker logs -f eduai-redis
```

## 下一阶段

如果 500 并发同步基线稳定，再单独设计：

- SSE 流式压测
- Celery 入队 / 出队吞吐压测
- 真实或 mock LLM 链路压测
