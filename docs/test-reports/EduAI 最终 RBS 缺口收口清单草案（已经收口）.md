# EduAI 最终 RBS 缺口收口清单草案

日期：2026-06-30  
优先级：仅保留完成最终 RBS 测试覆盖闭环所必需的事项

## P0 必须完成项

- [x] 将 [final-rbs-test-coverage-matrix-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-test-coverage-matrix-draft.md) 中的最终覆盖矩阵写入最终测试文档。
- [x] 明确记录后端自动化测试基线：
  - 环境：`conda activate edu`
  - 命令：`pytest backend/tests -q`
  - 历史结果：`74 passed`
- [x] 补充当前自动化测试收口结果：
  - 命令：`pytest backend/tests -q`
  - 当前结果：`100 passed`
- [x] 使用 [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md) 中的服务器真实课程评测关闭 `R7121` 的问答准确率部分。
- [x] 确认批改准确率是否具备可计分评测产物。
  - 结果：已有 [grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md)。
  - 当前计量结果：递归题 `23 / 25 = 0.92`；非递归 stack-vs-queue 题 `11 / 12 = 0.9167`。

## P1 证据整理

- [x] 加入 500 用户读链路监控压测结果：[loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)。
- [x] 加入 15 用户核心业务链路压测结果：[loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)。
- [x] 说明较早噪声压测 [loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv) 已被监控重跑结果替代，不作为主引用结果。

## P1 需求收口

### `R2111`

- [x] 形成 `pdf / docx / pptx` 的正向解析证据。
- [x] 引用实现证据：[embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py)。
- [x] 引用解析测试：[test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py)。

### `R4111`

- [x] 形成文档附件进入评分输入的验证测试。
- [x] 覆盖 `pdf / docx / pptx / xlsx` 当前后端评分输入范围。
- [x] 复用批改链路证据：[docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md) 与 [M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)。

### `R7231`

- [x] 建立异常提示族证据集合。
- [x] 覆盖上传失败、worker 失败、LLM 失败、无资料、无 Agent。
- [x] 引用直接测试：[test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py) 与 [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py)。

### `R2131`

- [x] 将需求表述与当前最终 RBS 对齐。
- [x] 整理检索片段参与 grounding 答案生成的证据。
- [x] 当前证据支持 最终 RBS 中的 `vector retrieval / RAG grounding` 范围，可关闭。

## P1 文档收口项

- [x] 将这些历史 partial 行整理为最终文档可关闭状态：
  - `R1111`
  - `R1211`
  - `R1311`
  - `R2121`
  - `R3111`
  - `R6121`
  - `R6211`
  - `R7111`
  - `R7131`
  - `R7221`
  - `R831`

## 最终提交前禁止事项

不要声明以下内容：

- 形式化代码覆盖率已经达到 100%。
- 500 用户 AI 全链路压测已经完成。
- 500 用户读链路压测为零失败。
- 批改准确率已经对所有课程、所有题型、所有评分标准普遍验证达到 90% 以上。

## 当前收口结论

当前最终 RBS 与当前证据包已经不再触发 完整测试覆盖 提交的硬性阻塞条件。可以提交的口径是：最终 RBS 中每个叶子需求均已有需求级测试证据或文档证据覆盖；但不声明形式化代码覆盖率完整，也不声明超出测试集范围的通用能力。




