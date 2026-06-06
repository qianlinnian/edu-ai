# Agent Builder 工作流说明

## 当前支持的节点语义
- `input_node`: 工作流入口，表示用户问题进入 Agent。
- `rag_node`: 课程知识检索节点。发布后会映射为 QA Agent 的 `top_k`、`similarity_threshold` 和 `tools=["rag"]`。
- `llm_node`: 大模型回答节点。发布后会映射为 Agent 的 `llm_model`。
- `output_node`: 工作流出口，表示最终回答返回给聊天链路。

## 仅 UI 原型节点
- `grading_node`
- `analytics_node`
- `exercise_node`
- `condition_node`

这些节点目前可以出现在 Builder 画布中，用于表达未来能力方向，但当前运行时不会执行它们。
如果工作流包含这些节点，前端会给出提示，后端会拒绝发布。

## 最小可用工作流结构
- 必须且只能有 1 个 `input_node`
- 必须且只能有 1 个 `llm_node`
- 必须且只能有 1 个 `output_node`
- `input_node` 必须是起点
- `output_node` 必须是终点
- 必须存在 `input -> ... -> llm -> ... -> output` 的可达路径
- 如果存在 `rag_node`，当前运行时最多支持 1 个，且必须配置当前课程、`topK`、`similarity`

## 发布后如何生效
当前平台还没有通用工作流执行引擎。

发布动作会把一个通过校验的 QA 工作流映射成 `AgentInstance` 的运行时配置：
- `config.workflow_mode = "mapped_qa_pipeline"`
- `config.top_k`
- `config.similarity_threshold`
- `config.workflow_summary`
- `config.workflow_mapping`
- `tools`
- `llm_model`

也就是说，发布后的实际生效方式是“把 DAG 映射为 QA Agent 配置”，而不是逐节点执行任意流程。
