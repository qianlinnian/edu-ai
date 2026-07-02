# EduAI 最终测试文档（模板版）

## 1. 项目信息

| 项目项 | 内容 |
| --- | --- |
| 项目名称 | EduAI |
| 文档名称 | 最终测试文档 |
| 文档日期 | 2026-06-30 |
| 文档状态 | 模板化底稿 |
| 对应需求基线 | `docs/rbs-wbs-schedule+gantt.md` 中最终 RBS |
| 测试对象 | 后端服务、课程问答链路、作业批改链路、练习与分析链路、平台模拟接入链路、部署与性能验证材料 |
| 覆盖口径 | requirement coverage / evidence coverage |
| 作者 | `{待补}` |
| 审核人 | `{待补}` |

## 2. 引言

本文基于 [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md) 中的最终 RBS，对 EduAI 当前仓库中的自动化测试结果、功能验证记录、专项评测结果、部署验证记录和性能压测结果进行整理，形成面向最终提交的需求级测试覆盖文档。

本文的目标不是声明形式化代码覆盖率，而是建立“最终 RBS 需求 -> 测试/验证 -> 证据 -> 当前结论”的闭环，以支撑课程要求中的 complete test coverage for all requirements specified in the final RBS。

## 3. 测试范围

### 3.1 覆盖范围

- 覆盖对象为最终 RBS 中全部叶子需求。
- 每条需求至少映射到一种真实证据。
- 证据类型包括自动化测试、功能验证、专项评测、部署验证、性能压测和必要文档证据。

### 3.2 不在本文声明范围内的内容

- 本文不声明 `pytest-cov` 意义上的形式化代码覆盖率完整。
- 本文不声明问答、批改或性能能力已在所有课程、所有题型、所有负载条件下普遍验证成立。
- 本文不把单次 500 用户读链路压测解释为 500 用户 AI 全链路零失败证明。

## 4. 测试策略

### 4.1 自动化测试策略

- 使用 `pytest` 执行后端测试集。
- 重点覆盖接口契约、Agent 运行时配置、问答链路、作业批改链路、学习分析链路和异常路径。

### 4.2 功能测试策略

- 对课程问答、作业提交与批改、练习推荐、角色入口和平台模拟接入进行链路验证。
- 功能验证结果主要通过最终覆盖矩阵和专项验证材料体现。

### 4.3 专项评测策略

- 对课程知识库问答进行准确率评测。
- 对作业批改进行固定评测集准确率评测。

### 4.4 部署与性能测试策略

- 使用健康检查确认部署可运行。
- 使用读链路压测和小规模 AI 业务链路压测验证性能基线。

## 5. 测试环境

### 5.1 本地自动化测试环境

- Conda 环境：`edu`
- 后端测试目录：`backend/tests`
- 统一执行入口：`pytest backend/tests -q`

执行命令：

```powershell
conda activate edu
pytest backend/tests -q
```

### 5.2 补充目标测试

```powershell
conda activate edu
pytest backend/tests/test_document_and_grading_format_support.py -q --basetemp=D:\course\SEME\edu-ai\.pytest_tmp -p no:cacheprovider
```

### 5.3 部署与性能环境

- 已有服务器部署健康检查记录，`/health` 可正常响应。
- 已有 500 用户读链路压测结果。
- 已有 15 用户 AI 核心业务链路压测结果。

## 6. 测试套件汇总

### 6.1 后端自动化测试套件

- Q&A prompt 与 Agent 契约：[test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py)
- 平台工作流与模拟平台载荷：[test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py)
- 作业能力与课程清理：[test_assignment_capability_and_course_cleanup.py](/D:/course/SEME/edu-ai/backend/tests/test_assignment_capability_and_course_cleanup.py)
- 认证与课程提交契约：[test_auth_course_commit_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_auth_course_commit_contracts.py)
- 访问控制：[test_backend_b_access_controls.py](/D:/course/SEME/edu-ai/backend/tests/test_backend_b_access_controls.py)
- Chat 路由契约：[test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py)
- Chat 流式支持：[test_chat_streaming_support.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_streaming_support.py)
- 文档解析与评分格式：[test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py)
- 练习与分析闭环：[test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py)
- 练习生成标准化：[test_exercise_generation_normalization.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_generation_normalization.py)
- 批改维度支持：[test_grading_dimension_support.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_dimension_support.py)
- 批改结果标准化：[test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py)
- 学习闭环与流式问答基线：[test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py)、[test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py)
- 资源处理异常保护：[test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py)

### 6.2 自动化测试说明

- 当前自动化测试以后端链路为主。
- 前端相关需求的主要证据来自页面实现、角色入口验证、功能链路验证和最终需求覆盖矩阵，而不是独立前端自动化测试框架。

## 7. 需求覆盖矩阵

| 需求编号 | 需求摘要 | 关键测试用例 / 证据文件 | 状态 | 当前判断 |
| --- | --- | --- | --- | --- |
| `R1111` | 可复用的问答 / 批改 / 练习 Agent 模板 | `test_normalize_agent_grading_result_contract`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_grade_with_llm_delegates_to_grading_agent_and_keeps_worker_contract` | yes | 已按三类 Agent 后端模板能力关闭 |
| `R1211` | 统一 Provider 封装与模型切换 | `test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_grade_with_llm_uses_course_agent_provider_and_model` | yes | 已按 provider/model 映射与推断关闭 |
| `R1311` | 教师/学生不同入口 | `test_platform_mock_endpoints_return_stable_payloads`；`docs/course-agent-scenarios.md`；`frontend/src/components/Layout/MainLayout.tsx` | yes | 已按角色入口关闭 |
| `R2111` | PDF / Word / PPT 内容提取 | `test_parse_resource_content_extracts_text_from_rbs_formats`；`test_unsupported_resource_type_is_rejected`；`test_blank_docx_content_has_actionable_error` | yes | 已由文档解析测试关闭 |
| `R2121` | 课程资料切分、Embedding 与向量召回 | `test_qa_agent_uses_configured_top_k_for_rag`；`backend/script/test_rag_retrieval.py`；`backend/agent_core/rag_chain.py` | yes | 已按 RAG 检索链路关闭 |
| `R2131` | 检索片段参与答案生成并提供 grounding | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_chat_stream_uses_rag_context`；`datastructure-qna-eval-supplement-2026-06-29.md` | yes | 已按 RAG grounding 范围关闭 |
| `R2141` | 课程级资源与会话隔离 | `test_exercise_pool_rejects_unenrolled_student`；`test_send_message_rejects_forbidden_course_access`；`docs/course-agent-scenarios.md` | yes | 已关闭 |
| `R3111` | 会话上下文连续性 | `test_send_message_stream_success`；`test_send_message_success`；`M4-测试计划-v0.4.0.md` | yes | 已关闭 |
| `R3121` | 优先依据课程知识库回答 | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_uses_configured_top_k_for_rag`；`datastructure-qna-eval-supplement-2026-06-29.md` | yes | 已由真实课程问答评测关闭 |
| `R3131` | 按课程和用户保存会话历史 | `test_send_message_success`；`test_send_message_stream_success`；`M4-测试证据记录-v0.4.0.md` | yes | 已关闭 |
| `R4111` | 文本输入与文档附件进入统一评分链路 | `test_build_grading_content_uses_supported_attachment_formats`；`test_standardize_grading_payload_normalizes_core_fields`；`docs/M3-A-grading-samples.md` | yes | 已按文档附件文本化评分链路关闭 |
| `R4121` | 教师附加参考答案和评分标准 | `test_build_grading_dimensions_from_structured_rubric`；`test_reference_answer_exact_match_applies_full_score_rule`；`test_reference_answer_explicit_answer_pattern_applies_full_score_rule` | yes | 已按进入批改链路关闭 |
| `R4211` | 结构化批注输出 | `test_normalize_agent_grading_result_contract`；`test_standardize_grading_payload_normalizes_annotations_and_knowledge_scores`；`M4-测试证据记录-v0.4.0.md` | yes | 已关闭 |
| `R5111` | 薄弱点分析 | `test_create_attempt_updates_mastery_after_successful_answer`；`test_submit_attempt_returns_alert_refresh_metadata`；`test_refresh_learning_alerts_creates_weak_alert_and_resolves_recovered_one` | yes | 已关闭 |
| `R5211` | 测评-批改-练习闭环 | `test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise`；`2026-05-26-M3-end-to-end-test-record.md` | yes | 已关闭 |
| `R6111` | 模拟嵌入式接入 | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；`platform-adapter-simulated.md` | yes | 已按模拟平台集成关闭 |
| `R6121` | 课程问答 Widget 嵌入 | `M4-测试计划-v0.4.0.md`；`M4-测试证据记录-v0.4.0.md`；`2026-04-22-系统测试报告-v0.1.0.md` | yes | 已按手工验证和文档证据关闭 |
| `R6211` | 可视化组件及参数配置 | `test_validate_workflow_dag_reports_missing_required_nodes`；`test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping` | yes | 已按当前可视化配置范围关闭 |
| `R7111` | 并发读链路与核心业务链路压测验证 | `loadtest-500-monitored2m-final-20260628_stats.csv`；`loadtest-business-clean-15u-20260628_stats.csv` | yes | 500 用户读链路低失败率基线 + 小规模 AI 业务链路零失败基线 |
| `R7121` | 问答与批改准确率 >= 90% | `datastructure-qna-eval-supplement-2026-06-29.md`；`grading-eval-local-rerun-25cases-2026-06-29.json`；`grading-eval-stack-queue-12cases-2026-06-30.json` | yes | 当前测试范围内关闭 |
| `R7131` | 隔离、批量题集、异常、性能与并发测试 | `test_exercise_pool_rejects_unenrolled_student`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_submit_assignment_returns_clear_upload_failure_prompt`；`loadtest-500-monitored2m-final-20260628_stats.csv` | yes | 已关闭 |
| `R7211` | 教师与学生权限隔离 | `test_exercise_attempt_rejects_teacher`；`test_send_message_rejects_forbidden_course_access`；`test_alerts_student_rejects_unenrolled_course` | yes | 已关闭 |
| `R7221` | 跨课程复用的 Agent 基础架构 | `test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`docs/architecture-diagrams.md` | yes | 已关闭 |
| `R7231` | 上传、worker、LLM、无资料、无 Agent 异常提示 | `test_submit_assignment_returns_clear_upload_failure_prompt`；`test_get_grading_result_returns_worker_failure_prompt`；`test_blank_pdf_content_has_actionable_error_without_ocr`；`test_send_message_rejects_inactive_agent` | yes | 已关闭 |
| `R811` | 以通义千问作为主要模型 | `test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`docs/rbs-wbs-schedule+gantt.md` | yes | 已关闭 |
| `R821` | 仅实现模拟平台集成 | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；`platform-adapter-simulated.md` | yes | 已关闭 |
| `R831` | 项目于 2026-06-14 前交付 | `docs/final-summary-report-2026-06-14.md` | yes | 作为文档合规证据关闭 |

## 8. 测试执行汇总

| 类别 | 当前结果 | 主证据 |
| --- | --- | --- |
| 后端自动化测试基线 | `pytest backend/tests -q = 100 passed` | `backend/tests` |
| 文档与评分格式补充测试 | `9 passed` | `test_document_and_grading_format_support.py` |
| 数据结构课程问答评测 | `45 / 45 = 1.0` | [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md) |
| 本地历史问答评测 | `24 / 25 = 0.96` | [datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json) |
| 递归题批改评测 | `23 / 25 = 0.92` | [grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json) |
| 非递归概念题批改评测 | `11 / 12 = 0.9167` | [grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json) |
| 500 用户读链路压测 | `207756` 次请求，`405` 次失败，失败率约 `0.195%` | [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv) |
| 15 用户 AI 业务链路压测 | 聚合失败数 `0` | [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv) |

## 9. 代表性测试用例

- `test_build_qa_system_prompt_requires_grounded_answer`：验证回答必须基于检索上下文生成。
- `test_qa_agent_uses_configured_top_k_for_rag`：验证问答链路会按配置检索课程资料。
- `test_parse_resource_content_extracts_text_from_rbs_formats`：验证 PDF、Word、PPT 等资料类型可被解析。
- `test_build_grading_content_uses_supported_attachment_formats`：验证文本与文档附件均可进入评分内容构造链路。
- `test_build_grading_dimensions_from_structured_rubric`：验证评分标准可转为结构化评分维度。
- `test_reference_answer_exact_match_applies_full_score_rule`：验证参考答案精确匹配时的评分规则生效。
- `test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise`：验证测评、分析、推荐的学习闭环。
- `test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`：验证平台模拟接入与课程 Agent 发布链路。

## 10. 缺陷与问题汇总

### 10.1 当前无阻塞提交的未闭合需求缺口

- 按当前最终 RBS 口径，全部叶子需求均已有对应证据并可关闭。

### 10.2 当前文档与测试边界说明

- 当前仓库未提供持久化形式化代码覆盖率报告。
- 前端相关需求未以独立前端自动化测试框架作为主证据，而是通过页面实现、角色入口验证、功能链路验证和需求矩阵闭环。

## 11. 基于风险的测试说明

### 11.1 高风险链路

- 课程问答准确率是否达到课程要求。
- 作业批改准确率是否达到课程要求。
- 资料解析失败、无资料、无 Agent、worker 失败等异常场景是否有明确反馈。
- 并发读链路与 AI 业务链路在部署环境下是否可运行。

### 11.2 已采用的风险缓解测试方式

- 使用真实课程问答补充评测验证 `R7121` 的问答侧准确率。
- 使用两组固定批改评测集验证 `R7121` 的批改侧准确率。
- 使用异常路径自动化测试覆盖上传失败、worker 失败、无资料、无 Agent 等高风险提示。
- 使用 500 用户读链路压测和 15 用户 AI 业务链路压测验证部署后性能基线。

## 12. 测试证据

### 12.1 功能与专项验证材料

- 最终需求覆盖矩阵：[final-rbs-test-coverage-matrix-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-test-coverage-matrix-draft.md)
- 数据结构课程问答补充评测：[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)
- 批改泛化补充评测：[grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md)

### 12.2 部署健康与性能材料

- 读链路监控压测：[loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)
- 核心业务链路压测：[loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)
- 部署健康检查参考：[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)

## 13. 测试结论

基于当前最终 RBS 与已引用证据，EduAI 可以支撑“最终 RBS 中所有需求均已有测试覆盖”的提交说法。该结论的含义是需求级测试覆盖 / 证据覆盖，而不是形式化代码覆盖率完整。

当前最安全的最终表述是：

- EduAI 已具备较完整的后端自动化测试、核心功能验证、部署验证、性能压测证据。
- 数据结构课程问答评测与当前固定批改评测集结果均达到 90% 以上。
- 最终 RBS 中每个叶子需求均已映射到真实证据并可关闭。

## 14. 附录

### 14.1 可继续补写内容

- 文档作者、审核人、版本记录。
- 代表性页面截图或平台侧操作截图。
- 若老师要求，可追加“完整测试用例列表”或“缺陷记录摘要”。
