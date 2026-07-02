# EduAI 最终 RBS 测试覆盖矩阵草案

日期：2026-06-30  
状态：最终提交前收口草案  
范围：需求 -> 测试 -> 证据 -> 缺口 -> 收口动作

## 优先结论

1. 当前仓库已经具备较完整的真实测试证据，可以在明确证据边界的前提下，支撑“最终 RBS 中所有需求均已有测试覆盖”的提交说法。
2. 当前最强证据包括：后端自动化测试 `100 passed`、部署健康验证、500 用户读链路压测、15 用户核心业务链路压测、数据结构课程问答评测 `45 / 45 = 1.0`。
3. 历史重点缺口已经按当前最终 RBS 口径收口：`R7121` 在当前测试集范围内达到 90% 以上；`R2131` 按“向量检索 / RAG grounding”范围闭环。
4. 本矩阵证明的是“需求级测试覆盖 / 证据覆盖”，不声明形式化代码覆盖率达到 100%。

## 已确认的证据基线

### 后端自动化测试

- 测试环境：本地 Conda 环境 `edu`
- 后端测试目录：`backend/tests`
- 历史审计记录：[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)
- 历史结果：`conda activate edu` 后执行 `pytest backend/tests -q`，结果 `74 passed`
- 当前补充结果：`conda activate edu` 后执行 `pytest backend/tests -q`，结果 `100 passed`
- 目标补充测试：`pytest backend/tests/test_document_and_grading_format_support.py -q --basetemp=D:\course\SEME\edu-ai\.pytest_tmp -p no:cacheprovider`，结果 `9 passed`

### 问答准确率

- 本地历史结果：[data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json)，`24 / 25 = 0.96`
- 服务器真实课程补充评测：[datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md)
- 当前优先引用结果：服务器课程 `course_id = 3`，分组汇总 `45 / 45 = 1.0`，检索非空 `45 / 45`

### 批改准确率

- 批改泛化说明：[grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md)
- 递归题 25 组：[grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json)，`23 / 25 = 0.92`
- 非递归 stack-vs-queue 12 组：[grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json)，`11 / 12 = 0.9167`

### 部署与性能

- 500 用户读链路监控压测：[loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)
- 15 用户业务链路压测：[loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)
- 较早噪声压测：[loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv)
- 审计说明：[tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)

## 最终 RBS 优先覆盖矩阵

状态说明：`yes` 表示已有真实证据并可关闭；`partial` 表示部分覆盖；`no` 表示当前不能关闭。  
类型说明：`证据就绪` 表示可直接引用；`文档收口` 表示主要缺文档整理；`需补测试` 表示需要新增测试；`范围澄清` 表示 RBS 与实现/证据边界需对齐。

| 需求编号 | 需求摘要 | 代表性测试函数 / 证据文件 | 类型 | 状态 | 收口动作 |
| --- | --- | --- | --- | --- | --- |
| `R1111` | 可复用的问答 / 批改 / 练习 Agent 模板 | `test_normalize_agent_grading_result_contract`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_grade_with_llm_delegates_to_grading_agent_and_keeps_worker_contract` | 证据就绪 | yes | 已按问答、批改、练习三条 Agent 后端模板能力关闭 |
| `R1211` | 统一 Provider 封装与模型切换 | `test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_grade_with_llm_uses_course_agent_provider_and_model` | 证据就绪 | yes | 已按后端 provider/model 映射与推断能力关闭 |
| `R1311` | 同一课程知识库下按教师/学生提供不同入口 | `test_platform_mock_endpoints_return_stable_payloads`；`docs/course-agent-scenarios.md`；`frontend/src/components/Layout/MainLayout.tsx` | 证据就绪 | yes | 已按教师/学生角色入口关闭 |
| `R2111` | PDF / Word / PPT 内容提取 | `test_parse_resource_content_extracts_text_from_rbs_formats`；`test_unsupported_resource_type_is_rejected`；`test_blank_docx_content_has_actionable_error` | 证据就绪 | yes | 已由 `pdf / docx / pptx` 解析测试关闭 |
| `R2121` | 课程资料切分、Embedding 与向量召回 | `test_qa_agent_uses_configured_top_k_for_rag`；`backend/script/test_rag_retrieval.py`；`backend/agent_core/rag_chain.py` | 证据就绪 | yes | 已按切分、embedding、向量召回链路关闭 |
| `R2131` | 检索片段参与答案生成并提供 grounding | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_chat_stream_uses_rag_context`；`datastructure-qna-eval-supplement-2026-06-29.md` | 证据就绪 | yes | 已按课程过滤向量检索与 RAG grounding 关闭 |
| `R2141` | 资源、chunk、embedding、Agent、chat session 绑定 course_id | `test_exercise_pool_rejects_unenrolled_student`；`test_send_message_rejects_forbidden_course_access`；`docs/course-agent-scenarios.md` | 证据就绪 | yes | 已按课程级隔离关闭 |
| `R3111` | 基于会话的上下文连续性 | `test_send_message_stream_success`；`test_send_message_success`；`M4-测试计划-v0.4.0.md` | 证据就绪 | yes | 已按会话复用与历史连续性关闭 |
| `R3121` | 优先依据课程知识库内容生成回答 | `test_build_qa_system_prompt_requires_grounded_answer`；`test_qa_agent_uses_configured_top_k_for_rag`；`datastructure-qna-eval-supplement-2026-06-29.md` | 证据就绪 | yes | 已由服务器课程 `45 / 45 = 1.0` 与检索非空 `45 / 45` 关闭 |
| `R3131` | 按课程和用户保存会话历史 | `test_send_message_success`；`test_send_message_stream_success`；`M4-测试证据记录-v0.4.0.md` | 证据就绪 | yes | 已关闭 |
| `R4111` | 支持文本输入与文档附件提交并进入统一评分链路 | `test_build_grading_content_uses_supported_attachment_formats`；`test_standardize_grading_payload_normalizes_core_fields`；`docs/M3-A-grading-samples.md` | 证据就绪 | yes | 已按 `pdf / docx / pptx / xlsx` 后端评分输入范围关闭 |
| `R4121` | 教师可在作业中附加参考答案和评分标准 | `test_build_grading_dimensions_from_structured_rubric`；`test_reference_answer_exact_match_applies_full_score_rule`；`test_reference_answer_explicit_answer_pattern_applies_full_score_rule` | 证据就绪 | yes | 已按参考答案和评分标准进入批改链路关闭 |
| `R4211` | 输出包含位置、类型与内容的结构化批注 | `test_normalize_agent_grading_result_contract`；`test_standardize_grading_payload_normalizes_annotations_and_knowledge_scores`；`M4-测试证据记录-v0.4.0.md` | 证据就绪 | yes | 按位置数据与列表展示范围关闭 |
| `R5111` | 依据练习与批改结果生成薄弱点分析 | `test_create_attempt_updates_mastery_after_successful_answer`；`test_submit_attempt_returns_alert_refresh_metadata`；`test_refresh_learning_alerts_creates_weak_alert_and_resolves_recovered_one` | 证据就绪 | yes | 已关闭 |
| `R5211` | 测评-批改-练习闭环支持 | `test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise`；`2026-05-26-M3-end-to-end-test-record.md` | 证据就绪 | yes | 已关闭 |
| `R6111` | 支持模拟嵌入式接入 | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；`platform-adapter-simulated.md` | 证据就绪 | yes | 已按超星/钉钉载荷的模拟嵌入接入关闭 |
| `R6121` | 课程问答 Widget 嵌入 | `M4-测试计划-v0.4.0.md`；`M4-测试证据记录-v0.4.0.md`；`2026-04-22-系统测试报告-v0.1.0.md` | 证据就绪 | yes | 已按课程问答 Widget 手工验证与文档证据关闭 |
| `R6211` | 可视化组件及参数配置 | `test_validate_workflow_dag_reports_missing_required_nodes`；`test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping` | 证据就绪 | yes | 已按可视化配置映射到 QA Agent 运行时关闭，不宣称任意 DAG 执行 |
| `R7111` | 支持并发读链路与核心业务链路压测验证 | `loadtest-500-monitored2m-final-20260628_stats.csv`；`loadtest-business-clean-15u-20260628_stats.csv` | 证据就绪 | yes | 已按“500 用户读链路低失败率基线 + 小规模 AI 业务链路零失败基线”关闭 |
| `R7121` | 问答与批改准确率 >= 90% | `datastructure-qna-eval-supplement-2026-06-29.md`；`grading-eval-local-rerun-25cases-2026-06-29.json`；`grading-eval-stack-queue-12cases-2026-06-30.json` | 证据就绪 | yes | 当前测试范围内关闭：问答 `45 / 45 = 1.0`；递归批改 `23 / 25 = 0.92`；非递归概念题 `11 / 12 = 0.9167` |
| `R7131` | 课程隔离、批量题集、异常场景、性能与并发测试 | `test_exercise_pool_rejects_unenrolled_student`；`test_generate_targeted_exercises_uses_weak_points_metadata`；`test_submit_assignment_returns_clear_upload_failure_prompt`；`loadtest-500-monitored2m-final-20260628_stats.csv` | 证据就绪 | yes | 已由隔离、批量练习、异常、性能/并发证据联合关闭 |
| `R7211` | 教师与学生权限隔离 | `test_exercise_attempt_rejects_teacher`；`test_send_message_rejects_forbidden_course_access`；`test_alerts_student_rejects_unenrolled_course` | 证据就绪 | yes | 已关闭 |
| `R7221` | 跨课程复用的 Agent 基础架构 | `test_build_agent_runtime_config_from_workflow_maps_supported_nodes`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`docs/architecture-diagrams.md` | 证据就绪 | yes | 已按模块化后端 SDK / 运行时映射范围关闭 |
| `R7231` | 上传异常、worker 失败、LLM 失败、无资料、无 Agent 明确提示 | `test_submit_assignment_returns_clear_upload_failure_prompt`；`test_get_grading_result_returns_worker_failure_prompt`；`test_blank_pdf_content_has_actionable_error_without_ocr`；`test_send_message_rejects_inactive_agent` | 证据就绪 | yes | 已按所有要求的异常提示族关闭 |
| `R811` | 以通义千问作为主要模型 | `test_build_agent_runtime_config_infers_provider_from_llm_model`；`test_publish_workflow_marks_agent_active_and_applies_runtime_mapping`；`docs/rbs-wbs-schedule+gantt.md` | 证据就绪 | yes | 已关闭 |
| `R821` | 仅实现模拟平台集成 | `test_platform_connection_requires_platform_specific_config`；`test_platform_mock_endpoints_return_stable_payloads`；`platform-adapter-simulated.md` | 证据就绪 | yes | 已关闭 |
| `R831` | 项目于 2026-06-14 前交付 | `docs/final-summary-report-2026-06-14.md` | 证据就绪 | yes | 作为文档合规证据关闭，不作为功能测试行 |

## 历史重点缺口收口说明

### R7121 问答与批改准确率

当前可关闭，但必须限定为“当前测试集范围”。允许表述为：问答准确率在当前数据结构课程评测集上达到 90% 以上；批改准确率在当前固定批改评测集上达到 90% 以上。禁止表述为：批改准确率已对所有课程、所有题型、所有 rubric 风格普遍验证达到 90% 以上。

### R2111 文档内容提取

实现支持 `pdf / docx / pptx`，且已有正向解析测试和异常保护测试，当前可标记为 `yes`。

### R4111 文本与文档附件进入统一评分链路

当前证据覆盖文本输入、文档附件解析、评分输入、批改输出标准化。关闭范围是文档类附件进入文本化评分链路，不宣称图片、音频或视频的直接多模态理解。

### R7231 异常提示

上传失败、worker 失败、LLM 失败、无资料、无 Agent 均已有自动化或契约测试证据，当前可标记为 `yes`。

### R2131 RAG grounding

最终 RBS 已对齐到向量检索与 RAG grounding。实现、prompt 契约、检索辅助脚本、真实问答评测共同证明检索片段参与答案生成，当前可标记为 `yes`。

## 当前提交风险说明

当前仓库可以支撑后端自动化测试覆盖、核心教学闭环功能验证、部署验证、性能与并发验证、问答准确率超过 90% 的真实课程评测结果、批改准确率超过 90% 的固定测试集评测结果。

当前不应声称：形式化代码覆盖率达到 100%；500 用户 AI 全链路压测已经完成；批改能力对所有课程和所有题型都已泛化验证。

## 推荐最终提交口径

> 本测试文档采用最终 RBS 优先的需求级覆盖方式，将每一条最终 RBS 叶子需求映射到自动化测试、功能验证、部署验证、性能压测或文档证据。基于当前最终 RBS 表述与已引用证据，EduAI 可以支撑“最终 RBS 中所有需求均已有测试覆盖”的提交说法；但本文不声明形式化代码覆盖率完整，也不声明超出测试集范围的通用性能或通用准确率结论。




