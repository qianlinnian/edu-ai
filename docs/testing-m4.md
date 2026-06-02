# M4 测试说明

## 可直接本地运行
- `conda activate edu`
- `cd backend`
- `pytest tests/test_chat_route_contracts.py tests/test_chat_streaming_support.py`
- `pytest tests/test_agent_platform_contracts.py`
- `pytest tests/test_exercise_analytics_loop.py tests/test_m4_acceptance_baselines.py tests/test_exercise_generation_normalization.py`

这些测试不依赖真实外部平台 SDK，也不依赖真实 LLM 网络调用，主要通过假数据和 monkeypatch 验证 M4 核心链路。

## 前端静态验证
- `cd frontend`
- `.\node_modules\.bin\tsc.cmd -b --pretty false`

## 当前仍受环境影响的项
- `npm run build` 在当前沙箱环境里曾触发 `esbuild spawn EPERM`，因此本轮以前端 TypeScript 构建作为最小替代验证。
- 未建立真实数据库种子下的完整端到端自动化测试。
- 未做真实超星/钉钉联调，也未做真实 LLM 调用压测。
