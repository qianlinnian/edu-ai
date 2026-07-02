# EduAI 最终测试文档

## 1. 项目信息

| 项目项       | 内容                                                                                                             |
| ------------ | ---------------------------------------------------------------------------------------------------------------- |
| 项目名称     | EduAI                                                                                                            |
| 文档名称     | 最终测试文档                                                                                                     |
| 文档日期     | 2026-06-30                                                                                                       |
| 文档状态     | 最终 RBS 需求级测试覆盖收口版                                                                                    |
| 对应需求基线 | [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md) 中最终 RBS               |
| 测试对象     | 后端服务、课程问答链路、作业批改链路、练习与分析链路、平台模拟接入链路、Agent 配置与发布链路、部署与性能验证材料 |
| 覆盖口径     | requirement coverage / evidence coverage，不声明形式化代码覆盖率完整                                             |

## 2. 引言

本文以 [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md) 中的最终 RBS 为唯一需求来源，把仓库内已有的自动化测试、功能验证、专项评测、部署验证和性能压测结果整理成一份“最终 RBS 需求 -> 测试 / 证据 -> 结论”的闭环材料，对应课程对最终 RBS 全部需求进行测试覆盖的要求。

本文不重新解释每条需求的设计意图，也不重复 M3 / M4 阶段过程性记录的全部内容；它的工作是把已经存在的真实证据按最终 RBS 口径重新归位，并明确每条叶子需求当前可关闭的范围与不应被过度解读的边界。

历史过程材料如 [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)、[EduAI 最终 RBS 测试覆盖矩阵草案.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终 RBS 测试覆盖矩阵草案.md)、[EduAI 最终 RBS 缺口收口清单草案（已经收口）.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终 RBS 缺口收口清单草案（已经收口）.md) 主要作为本文的来源与追溯材料，不再作为最终结论单独提交。

## 3. 测试范围

### 3.1 覆盖范围

- 覆盖对象为最终 RBS 中全部叶子需求，共 27 条，分布在 `R1` 至 `R8` 八个需求分组下。
- 每条需求至少映射到一种真实证据；证据类型包括自动化测试、功能验证、专项评测、部署验证、性能压测和必要文档证据。
- 每条需求都给出当前可关闭范围与不应被过度解读的边界，避免把“测试集范围内达标”写成“通用能力达标”。

### 3.2 内容范围声明

为避免最终提交口径被泛化理解，本文明确不声明以下内容：

- 不声明 `pytest-cov` 意义上的形式化代码覆盖率完整。仓库当前没有持久化的覆盖率产物，也不以此作为提交口径。
- 不声明问答、批改或性能能力已在所有课程、所有题型、所有负载条件下普遍成立。
- 单次 500 用户读链路压测不等同于 500 用户 AI 全链路零失败；AI 业务链路只在小规模（15 用户）下做过零失败基线。
- 模拟嵌入式接入只覆盖超星、钉钉的模拟载荷，不声明真实平台对接已经完成。
- 前端相关需求以页面实现、角色入口验证、功能链路验证和需求矩阵作为主证据，不依赖独立的前端自动化测试框架。

## 4. 测试策略

### 4.1 自动化测试策略

- 使用 `pytest` 执行后端测试集，测试目录为 `backend/tests`。
- 重点覆盖接口契约、Agent 运行时配置、问答链路、作业批改链路、学习分析链路、权限与课程隔离、资源解析异常保护和平台模拟载荷契约。
- 不引入额外的 mock LLM 框架覆盖所有分支；LLM 相关能力以 provider/model 推断、worker 契约和真实评测集结果作为联合证据。

### 4.2 功能测试策略

- 对课程问答、作业提交与批改、练习推荐、角色入口和平台模拟接入进行链路验证。
- 功能验证结果主要落地在 [M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md) 和 [2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md)，最终覆盖矩阵以“自动化测试 + 功能链路 + 文档证据”联合关闭。
- 早期 [2026-04-22-系统测试报告-v0.1.0.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-04-22-系统测试报告-v0.1.0.md) 作为阶段性记录保留，不作为最终结论的主引用。

### 4.3 专项评测策略

- 对课程知识库问答进行准确率评测：使用仓库脚本 [backend/script/evaluate_mcq_checklist.py](/D:/course/SEME/edu-ai/backend/script/evaluate_mcq_checklist.py) 对服务器真实课程 `course_id=3` 跑分组 checklist，结果记录在 [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)。
- 对作业批改进行固定评测集准确率评测：递归题 25 组、非递归 stack-vs-queue 概念题 12 组，结果分别落在 [grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json) 和 [grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json)。

### 4.4 部署与性能测试策略

- 使用 `GET /health` 健康检查确认部署可运行；服务器进程为 Gunicorn + Celery worker。
- 使用 500 用户读链路监控压测验证部署后读链路基线，使用 15 用户 AI 核心业务链路压测验证问答、练习、批改等业务链路在小规模并发下的稳定性。
- 较早的 [loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv) 因存在不稳定噪声，已被 [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv) 替代，不作为主引用结果。

## 5. 测试环境

### 5.1 本地自动化测试环境

- 操作系统：Windows + Conda 环境 `edu`
- 后端测试目录：`backend/tests`
- 统一执行入口：`pytest backend/tests -q`

执行命令：

```powershell
conda activate edu
pytest backend/tests -q
```

历史基线结果：`74 passed in 9.22s`（2026-06-29，[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md) 记录）。
当前收口结果：`100 passed`（2026-06-30，[EduAI 最终 RBS 测试覆盖矩阵草案.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终 RBS 测试覆盖矩阵草案.md) 记录）。

### 5.2 补充目标测试

文档解析与评分格式补充测试单独运行，避免与主测试集临时目录冲突：

```powershell
conda activate edu
pytest backend/tests/test_document_and_grading_format_support.py -q --basetemp=D:\course\SEME\edu-ai\.pytest_tmp -p no:cacheprovider
```

补充结果：`9 passed`。

### 5.3 部署与性能环境

- 部署服务器：`114.116.207.63`，Gunicorn + Celery worker 进程在运行。
- 健康检查：`GET /health` 返回 `{"status":"ok","service":"EduAI Platform"}`。
- 500 用户读链路监控压测：2 分钟，覆盖 `auth.login / courses.list / courses.detail / chat.sessions.list / assignments.list / exercises.pool / resources.list / resources.list.cache` 等读路径。
- 15 用户 AI 业务链路压测：覆盖 `auth.login / chat.send / exercises.generate / assignments.submit / assignments.result.poll`，对应问答、练习、批改三条 AI 核心业务路径。

## 6. 测试套件汇总

### 6.1 后端自动化测试套件

按测试文件分组，覆盖范围与文件路径如下：

- Q&A prompt 与 Agent 契约：[test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py)
- 平台工作流与模拟平台载荷：[test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py)
- 作业能力与课程清理：[test_assignment_capability_and_course_cleanup.py](/D:/course/SEME/edu-ai/backend/tests/test_assignment_capability_and_course_cleanup.py)
- 认证与课程提交契约：[test_auth_course_commit_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_auth_course_commit_contracts.py)
- 访问控制与课程边界：[test_backend_b_access_controls.py](/D:/course/SEME/edu-ai/backend/tests/test_backend_b_access_controls.py)
- Chat 路由契约：[test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py)
- Chat 流式与空帧处理：[test_chat_streaming_support.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_streaming_support.py)
- 文档解析与评分格式支持：[test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py)
- 练习与分析闭环：[test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py)
- 练习生成标准化：[test_exercise_generation_normalization.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_generation_normalization.py)
- 批改维度支持：[test_grading_dimension_support.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_dimension_support.py)
- 批改结果标准化：[test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py)
- 资源处理异常保护：[test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py)

### 6.2 自动化测试说明

- 当前自动化测试以后端链路为主，前端没有独立自动化测试框架。
- 前端相关需求的主要证据来自页面实现、角色入口验证、功能链路验证和最终需求覆盖矩阵。
- 仓库当前未提供 `pytest-cov` 形式的形式化覆盖率产物；本文不基于形式化覆盖率得出任何结论。
- `test_document_and_grading_format_support.py` 单独执行是因为它对临时目录与缓存策略有要求，不影响它作为最终 RBS 证据的有效性。

## 7. 需求覆盖矩阵

状态字段：`yes` 表示已有真实证据并可关闭；`partial` 表示部分覆盖；`no` 表示当前不能关闭。最终 RBS 中所有叶子需求在本文口径下均为 `yes`。

| 需求编号 | 需求摘要                                     | 关键测试用例 / 证据文件                                                                                                                                                                                                                                                                                                                                                                                                                   | 状态 | 当前判断                                                                                               |
| -------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------ |
| `R1111`  | 可复用的问答 / 批改 / 练习 Agent 模板        | `test_normalize_agent_grading_result_contract`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_grade_with_llm_delegates_to_grading_agent_and_keeps_worker_contract`                                                                                                                                                                                                                                                  | yes  | 由问答、批改、练习三类 Agent 后端模板与 worker 契约覆盖                                                |
| `R1211`  | 统一 Provider 封装与模型切换                 | `test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_grade_with_llm_uses_course_agent_provider_and_model`                                                                                                                                                                                                                                      | yes  | 由 provider/model 映射与推断机制覆盖                                                                   |
| `R1311`  | 教师 / 学生不同入口                          | `test_platform_mock_endpoints_return_stable_payloads`；[docs/course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md)；[frontend/src/components/Layout/MainLayout.tsx](/D:/course/SEME/edu-ai/frontend/src/components/Layout/MainLayout.tsx)                                                                                                                                                                     | yes  | 由教师 / 学生角色入口实现与场景文档覆盖                                                                |
| `R2111`  | PDF / Word / PPT 内容提取                    | `test_parse_resource_content_extracts_text_from_rbs_formats`；`test_unsupported_resource_type_is_rejected`；`test_blank_docx_content_has_actionable_error`                                                                                                                                                                                                                                                                                | yes  | 由 `pdf / docx / pptx` 正向解析与异常保护测试覆盖                                                      |
| `R2121`  | 课程资料切分、Embedding 与向量召回           | `test_qa_agent_uses_configured_top_k_for_rag`；[backend/script/test_rag_retrieval.py](/D:/course/SEME/edu-ai/backend/script/test_rag_retrieval.py)；[backend/agent_core/rag_chain.py](/D:/course/SEME/edu-ai/backend/agent_core/rag_chain.py)                                                                                                                                                                                             | yes  | 由切分、embedding、向量召回链路与检索辅助脚本覆盖                                                      |
| `R2131`  | 检索片段参与答案生成并提供 grounding         | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_chat_stream_uses_rag_context`；[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)                                                                                                                                                                                         | yes  | 由 RAG grounding prompt 契约与真实课程问答评测联合覆盖                                                 |
| `R2141`  | 课程级资源与会话隔离                         | `test_exercise_pool_rejects_unenrolled_student`；`test_send_message_rejects_forbidden_course_access`；[docs/course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md)                                                                                                                                                                                                                                             | yes  | 由课程访问边界与权限拒绝测试覆盖                                                                       |
| `R3111`  | 会话上下文连续性                             | `test_send_message_stream_success`；`test_send_message_success`；[M4-测试计划-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试计划-v0.4.0.md)                                                                                                                                                                                                                                                                                  | yes  | 由会话历史复用与流式问答测试覆盖                                                                       |
| `R3121`  | 优先依据课程知识库回答                       | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_uses_configured_top_k_for_rag`；[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)                                                                                                                                                                                        | yes  | 由真实课程问答评测 `45 / 45 = 1.0` 与检索非空 `45 / 45` 关闭                                           |
| `R3131`  | 按课程和用户保存会话历史                     | `test_send_message_success`；`test_send_message_stream_success`；[M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)                                                                                                                                                                                                                                                                          | yes  | 由会话历史持久化测试覆盖                                                                               |
| `R4111`  | 文本输入与文档附件进入统一评分链路           | `test_build_grading_content_uses_supported_attachment_formats`；`test_standardize_grading_payload_normalizes_core_fields`；[docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md)                                                                                                                                                                                                                            | yes  | 由 `pdf / docx / pptx / xlsx` 评分输入与批改输出标准化测试覆盖                                         |
| `R4121`  | 教师附加参考答案和评分标准                   | `test_build_grading_dimensions_from_structured_rubric`；`test_reference_answer_exact_match_applies_full_score_rule`；`test_reference_answer_explicit_answer_pattern_applies_full_score_rule`                                                                                                                                                                                                                                              | yes  | 由结构化 rubric 与参考答案匹配规则测试覆盖                                                             |
| `R4211`  | 结构化批注输出                               | `test_normalize_agent_grading_result_contract`；`test_standardize_grading_payload_normalizes_annotations_and_knowledge_scores`；[M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)                                                                                                                                                                                                           | yes  | 由批注位置数据与列表展示范围覆盖                                                                       |
| `R5111`  | 薄弱点分析                                   | `test_create_attempt_updates_mastery_after_successful_answer`；`test_submit_attempt_returns_alert_refresh_metadata`；`test_refresh_learning_alerts_creates_weak_alert_and_resolves_recovered_one`                                                                                                                                                                                                                                         | yes  | 由掌握度更新、告警生成与告警恢复测试覆盖                                                               |
| `R5211`  | 测评-批改-练习闭环                           | `test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise`；[2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md)                                                                                                                                                                                                                                            | yes  | 由学习闭环冒烟测试与 M3 端到端记录覆盖                                                                 |
| `R6111`  | 模拟嵌入式接入                               | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；[platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md)                                                                                                                                                                                                                           | yes  | 由超星 / 钉钉模拟载荷与平台配置校验覆盖                                                                |
| `R6121`  | 课程问答 Widget 嵌入                         | [M4-测试计划-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试计划-v0.4.0.md)；[M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)；[2026-04-22-系统测试报告-v0.1.0.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-04-22-系统测试报告-v0.1.0.md)                                                                                                                                 | yes  | 由 Widget 手工验证与文档证据覆盖，不声明浏览器自动化回归                                               |
| `R6211`  | 可视化组件及参数配置                         | `test_validate_workflow_dag_reports_missing_required_nodes`；`test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`                                                                                                                                                                                                                                 | yes  | 由可视化配置映射到 QA Agent 运行时覆盖，不宣称任意 DAG 执行引擎                                        |
| `R7111`  | 并发读链路与核心业务链路压测验证             | [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)；[loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)                                                                                                  | yes  | 500 用户读链路低失败率基线 + 15 用户 AI 业务链路零失败基线                                             |
| `R7121`  | 问答与批改准确率 >= 90%                      | [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)；[grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json)；[grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json) | yes  | 当前评测集范围内达标：问答 `45 / 45 = 1.0`；递归批改 `23 / 25 = 0.92`；非递归概念题 `11 / 12 = 0.9167` |
| `R7131`  | 隔离、批量题集、异常、性能与并发测试         | `test_exercise_pool_rejects_unenrolled_student`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_submit_assignment_returns_clear_upload_failure_prompt`；[loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)                                                                                       | yes  | 由隔离、批量练习、异常、性能与并发证据联合覆盖                                                         |
| `R7211`  | 教师与学生权限隔离                           | `test_exercise_attempt_rejects_teacher`；`test_send_message_rejects_forbidden_course_access`；`test_alerts_student_rejects_unenrolled_course`                                                                                                                                                                                                                                                                                             | yes  | 由角色级与课程级权限拒绝测试覆盖                                                                       |
| `R7221`  | 跨课程复用的 Agent 基础架构                  | `test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；[docs/architecture-diagrams.md](/D:/course/SEME/edu-ai/docs/architecture-diagrams.md)                                                                                                                                                                                                       | yes  | 由模块化后端 SDK 与运行时映射覆盖                                                                      |
| `R7231`  | 上传、worker、LLM、无资料、无 Agent 异常提示 | `test_submit_assignment_returns_clear_upload_failure_prompt`；`test_get_grading_result_returns_worker_failure_prompt`；`test_blank_pdf_content_has_actionable_error_without_ocr`；`test_send_message_rejects_inactive_agent`                                                                                                                                                                                                              | yes  | 由异常提示族测试覆盖                                                                                   |
| `R811`   | 以通义千问作为主要模型                       | `test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；[docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md)                                                                                                                                                                                                         | yes  | 由 provider 推断与发布测试覆盖                                                                         |
| `R821`   | 仅实现模拟平台集成                           | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；[platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md)                                                                                                                                                                                                                           | yes  | 由模拟平台集成测试覆盖                                                                                 |
| `R831`   | 项目于 2026-06-14 前交付                     | [docs/final-summary-report-2026-06-14.md](/D:/course/SEME/edu-ai/docs/final-summary-report-2026-06-14.md)                                                                                                                                                                                                                                                                                                                                 | yes  | 以文档合规证据支持，不作为功能测试行                                                                   |

## 8. 重点需求收口说明

最终 RBS 中以下几条在 [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md) 上曾被标记为 `partial` 或 `no`，本文按已收口范围重新说明，便于追溯。

### 8.1 R7121 问答与批改准确率

允许表述：问答准确率在当前数据结构课程评测集上达到 90% 以上；批改准确率在当前固定批改评测集上达到 90% 以上。

禁止表述：批改准确率已对所有课程、所有题型、所有 rubric 风格普遍验证达到 90% 以上。

支撑证据：

- 服务器真实课程问答评测：[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)，`course_id=3` 上分四组共 45 题，结果 `45 / 45 = 1.0`，检索非空 `45 / 45`。
- 本地历史问答评测：[data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json)，`24 / 25 = 0.96`。
- 递归题批改评测：[grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json)，`23 / 25 = 0.92`。
- 非递归 stack-vs-queue 概念题批改评测：[grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json)，`11 / 12 = 0.9167`。
- 批改泛化说明：[grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md)。

需要补充说明的是：第一轮分组评测曾被误执行在 `course_id=2` 上（该课程 `course_resources = 0`），其 `accuracy = 1.0` 实际是无引导生成而非课程 grounded 检索，已从最终证据中剔除，最终引用的是 `course_id=3` 上的结果。

### 8.2 R2111 文档内容提取

实现支持 `pdf / docx / pptx` 三类格式，由 [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py) 提供正向解析测试（`test_parse_resource_content_extracts_text_from_rbs_formats`）与异常保护测试（`test_unsupported_resource_type_is_rejected`、`test_blank_docx_content_has_actionable_error`）。

实现侧引用 [backend/workers/embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py)。不声明图片、扫描件 OCR、音频、视频的直接多模态解析；`test_blank_pdf_content_has_actionable_error_without_ocr` 明确验证了无 OCR 路径下的可执行错误提示。

### 8.3 R4111 文本与文档附件进入统一评分链路

当前覆盖文本输入、文档附件解析、评分输入构造与批改输出标准化，对应后端评分输入范围为 `pdf / docx / pptx / xlsx`。

关键测试：

- `test_build_grading_content_uses_supported_attachment_formats`：验证文档附件可进入评分内容构造链路。
- `test_standardize_grading_payload_normalizes_core_fields`：验证评分输入核心字段标准化。

参考样本：[docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md)、[M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)。本文不声明图片、音频或视频的直接多模态理解。

### 8.4 R7231 异常提示族

按最终 RBS 要求的“上传异常、worker 失败、LLM 失败、无资料、无 Agent 明确提示”五类建立证据集合，每类至少有一条直接测试：

- 上传失败：`test_submit_assignment_returns_clear_upload_failure_prompt`。
- worker 失败：`test_get_grading_result_returns_worker_failure_prompt`。
- 无资料：`test_blank_pdf_content_has_actionable_error_without_ocr`、`test_blank_docx_content_has_actionable_error`。
- 无 Agent：`test_send_message_rejects_inactive_agent`。
- LLM 失败：通过 worker 契约与 `test_grade_with_llm_delegates_to_grading_agent_and_keeps_worker_contract` 联合覆盖，错误会沿 worker 契约回传到前端可展示提示。

### 8.5 R2131 RAG grounding 范围对齐

最终 RBS 已将本条对齐为“向量检索与 RAG grounding”，不再要求混合检索。

当前证据：

- prompt 契约：`test_build_qa_system_prompt_requires_grounded_answer`。
- 检索参数：`test_qa_agent_uses_configured_top_k_for_rag`。
- 真实课程评测：[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)，检索非空 `45 / 45`。

## 9. 测试执行汇总

| 类别                    | 当前结果                                         | 主证据                                                                                                                                                                 |
| ----------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 后端自动化测试基线      | `pytest backend/tests -q = 100 passed`           | [backend/tests](/D:/course/SEME/edu-ai/backend/tests)                                                                                                                  |
| 文档与评分格式补充测试  | `9 passed`                                       | [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py)                                        |
| 数据结构课程问答评测    | `45 / 45 = 1.0`                                  | [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)                            |
| 本地历史问答评测        | `24 / 25 = 0.96`                                 | [datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json)                                                           |
| 递归题批改评测          | `23 / 25 = 0.92`                                 | [grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json)                          |
| 非递归概念题批改评测    | `11 / 12 = 0.9167`                               | [grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json)                          |
| 500 用户读链路监控压测  | `207756` 次请求，`405` 次失败，失败率约 `0.195%` | [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv) |
| 15 用户 AI 业务链路压测 | `481` 次请求，聚合失败数 `0`                     | [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)       |
| 部署健康检查            | `GET /health` 返回 `{"status":"ok"}`             | [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)                                                                                        |

500 用户读链路压测按接口分解的失败数（取自 `Aggregated` 行所在的同一 CSV）：

| 接口                    | 请求数 | 失败数 |
| ----------------------- | ------ | ------ |
| `assignments.list`      | 20578  | 37     |
| `auth.login`            | 500    | 0      |
| `chat.sessions.list`    | 20744  | 31     |
| `courses.detail`        | 41387  | 80     |
| `courses.list`          | 72264  | 145    |
| `courses.list.on_start` | 500    | 0      |
| `exercises.pool`        | 14612  | 35     |
| `resources.list`        | 30909  | 62     |
| `resources.list.cache`  | 6262   | 15     |
| `Aggregated`            | 207756 | 405    |

失败率约 `0.195%`，集中在缓存未命中或冷启动路径上的读链路接口，`auth.login` 与 `courses.list.on_start` 在 500 次预热请求上零失败。

15 用户 AI 业务链路压测按接口分解：

| 接口                      | 请求数 | 失败数 |
| ------------------------- | ------ | ------ |
| `assignments.result.poll` | 189    | 0      |
| `assignments.submit`      | 63     | 0      |
| `auth.login`              | 15     | 0      |
| `chat.send`               | 133    | 0      |
| `exercises.generate`      | 81     | 0      |
| `Aggregated`              | 481    | 0      |

## 10. 代表性测试用例

下列用例从不同链路中各取一条，便于快速复核本文覆盖的不是单一维度：

- `test_build_qa_system_prompt_requires_grounded_answer`：验证回答必须基于检索上下文生成，对应 `R2131` / `R3121`。
- `test_qa_agent_uses_configured_top_k_for_rag`：验证问答链路会按配置 `top_k` 检索课程资料，对应 `R2121` / `R3121`。
- `test_parse_resource_content_extracts_text_from_rbs_formats`：验证 PDF / Word / PPT 等资料类型可被解析，对应 `R2111`。
- `test_build_grading_content_uses_supported_attachment_formats`：验证文本与文档附件均可进入评分内容构造链路，对应 `R4111`。
- `test_normalize_agent_grading_result_contract`：验证 Agent 批改结果对外契约，对应 `R1111` / `R4211`。
- `test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`：验证发布后 Agent 进入 active 并应用运行时映射，对应 `R1211` / `R6211` / `R7221`。
- `test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise`：验证测评-批改-练习闭环冒烟，对应 `R5211`。
- `test_exercise_pool_rejects_unenrolled_student`：验证跨课程资源访问被拒绝，对应 `R2141` / `R7211`。
- `test_submit_assignment_returns_clear_upload_failure_prompt`：验证上传失败有可执行提示，对应 `R7231`。
- `test_platform_mock_endpoints_return_stable_payloads`：验证模拟平台载荷稳定，对应 `R6111` / `R821`。

## 11. 测试限制

为避免最终口径被过度解读，本文明确以下限制：

- 仓库未提供持久化的形式化代码覆盖率报告，所有结论以“需求级测试覆盖 + 证据覆盖”为口径。
- 前端相关需求未以独立前端自动化测试框架作为主证据，而是通过页面实现、角色入口验证、功能链路验证和需求矩阵闭环。
- 问答准确率仅在数据结构课程 `course_id=3` 的 45 题评测集上验证，未在其他课程上重跑。
- 批改准确率仅在递归题 25 组、非递归概念题 12 组两个固定评测集上验证，未对所有 rubric 风格做泛化测试。
- 500 用户读链路压测存在约 `0.195%` 的失败率，不等于读链路零失败；500 用户压测未覆盖 AI 全链路。
- 15 用户 AI 业务链路压测覆盖 `chat.send / exercises.generate / assignments.submit / assignments.result.poll` 五个核心业务接口，但样本量较小，仅作为小规模零失败基线。
- 模拟嵌入式接入只对应超星、钉钉的模拟载荷，未对接真实平台 API。

## 12. 基于风险的测试说明

### 12.1 高风险链路

- 课程问答准确率是否达到课程要求（`R7121` 问答侧）。
- 作业批改准确率是否达到课程要求（`R7121` 批改侧）。
- 资料解析失败、无资料、无 Agent、worker 失败等异常场景是否有明确反馈（`R7231`）。
- 并发读链路与 AI 业务链路在部署环境下是否可运行（`R7111`）。
- 教师与学生、跨课程之间的权限边界是否被严格隔离（`R2141` / `R7211`）。

### 12.2 已采用的风险缓解测试方式

- 使用真实课程问答补充评测验证 `R7121` 的问答侧准确率，并要求检索非空，避免“无检索也答对”的虚假满分。
- 使用两组固定批改评测集验证 `R7121` 的批改侧准确率，一组覆盖递归题，一组覆盖非递归概念题。
- 使用异常路径自动化测试覆盖上传失败、worker 失败、无资料、无 Agent、LLM 失败等高风险提示族。
- 使用 500 用户读链路压测和 15 用户 AI 业务链路压测分别覆盖读路径与 AI 业务路径，不混用同一条结论。
- 使用课程级权限拒绝测试覆盖跨课程、跨角色的访问边界。

## 13. 测试证据索引

### 13.1 最终 RBS 与覆盖矩阵

- 最终 RBS：[docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md)
- 覆盖矩阵草案：[EduAI 最终 RBS 测试覆盖矩阵草案.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终 RBS 测试覆盖矩阵草案.md)
- 缺口收口清单：[EduAI 最终 RBS 缺口收口清单草案（已经收口）.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终 RBS 缺口收口清单草案（已经收口）.md)
- 测试文档结构草案：[EduAI 最终测试文档结构草案.md](/D:/course/SEME/edu-ai/docs/test-reports/EduAI 最终测试文档结构草案.md)
- 历史审计底稿：[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)

### 13.2 功能与专项验证材料

- 数据结构课程问答补充评测：[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)
- 问答评测分组结果：[datastructure-eval-group-a-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-a-course3-2026-06-29.json)、[datastructure-eval-group-b-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-b-course3-2026-06-29.json)、[datastructure-eval-group-c-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-c-course3-2026-06-29.json)、[datastructure-eval-group-d-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-d-course3-2026-06-29.json)
- 本地历史问答评测：[datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json)
- 递归题批改评测：[grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json)
- 非递归概念题批改评测：[grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json)
- 批改泛化补充评测：[grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md)
- M3 端到端测试记录：[2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md)
- M4 测试计划：[M4-测试计划-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试计划-v0.4.0.md)
- M4 测试证据记录：[M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)
- 早期系统测试报告：[2026-04-22-系统测试报告-v0.1.0.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-04-22-系统测试报告-v0.1.0.md)
- 平台适配说明：[platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md)
- 课程 Agent 场景说明：[course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md)
- 项目总结报告：[final-summary-report-2026-06-14.md](/D:/course/SEME/edu-ai/docs/final-summary-report-2026-06-14.md)

### 13.3 部署健康与性能材料

- 500 用户读链路监控压测：[loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)
- 15 用户 AI 业务链路压测：[loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)
- 较早噪声压测（不作为主引用）：[loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv)
- 部署健康检查记录：[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)

## 14. 测试结论

综合最终 RBS 与本文引用的证据，可以认为：最终 RBS 中所有叶子需求均已有需求级测试覆盖或文档证据覆盖。这里的“覆盖”指 requirement coverage / evidence coverage，不指形式化代码覆盖率完整。

具体结论如下：

- 后端自动化测试基线 `100 passed`，补充目标测试 `9 passed`，覆盖接口契约、Agent 配置、问答、批改、练习、分析、权限、资源解析与平台模拟载荷。
- 数据结构课程问答评测在 `course_id=3` 上达到 `45 / 45 = 1.0`，检索非空 `45 / 45`；本地历史问答评测 `24 / 25 = 0.96`。
- 递归题批改评测 `23 / 25 = 0.92`，非递归概念题批改评测 `11 / 12 = 0.9167`，在当前评测集范围内均达到 90% 以上。
- 部署健康检查通过，500 用户读链路压测失败率约 `0.195%`，15 用户 AI 业务链路压测聚合失败数 `0`。
- 最终 RBS 中 27 条叶子需求均有真实证据支撑，无 `partial` 或 `no` 状态行。

不应被理解为以下结论：

- 形式化代码覆盖率达到 100%。
- 问答或批改能力已在所有课程、所有题型、所有 rubric 风格上普遍验证达到 90% 以上。
- 500 用户 AI 全链路压测已经完成或零失败。
- 真实平台（超星 / 钉钉）对接已经完成。
