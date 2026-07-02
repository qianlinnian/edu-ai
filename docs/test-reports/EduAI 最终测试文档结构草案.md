# EduAI 最终测试文档结构草案

日期：2026-06-29  
用途：面向课程最终提交的测试文档目录结构说明

## 建议提交文件

- `docs/test-reports/final-test-document.md`

## 建议目录

1. 执行结论
   - 是否可以声明 最终 RBS 需求级测试覆盖完成
   - 哪些结论必须保留测试范围边界

2. 测试范围与需求来源
   - 最终 RBS 来源：[docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md)
   - 本文覆盖范围
   - 证据类型定义：自动化测试证据、功能测试证据、部署/性能证据、文档证据

3. 测试环境与执行基线
   - 后端环境
   - `conda activate edu`
   - `pytest backend/tests -q`
   - 历史结果：`74 passed`
   - 当前补充结果：`100 passed`
   - 部署健康检查证据

4. 最终 RBS 优先覆盖矩阵
   - 每个 最终 RBS 叶子需求一行
   - 建议列：需求编号、需求摘要、自动化测试证据、功能证据、文档证据、状态、缺口、收口动作

5. 重点需求说明
   - `R7121` 准确率目标
   - `R2111` 文档内容提取格式
   - `R4111` 文本与文档附件进入评分链路
   - `R7231` 异常提示族覆盖
   - `R2131` RAG 检索与 grounding 范围说明

6. 自动化测试证据
   - 测试套件列表
   - 高价值测试用例说明
   - 明确说明当前没有形式化 `pytest-cov` 覆盖率产物

7. 功能与 E2E 证据
   - M3 教学闭环
   - M4 主流程验证
   - 当前 UI/浏览器证据边界

8. 部署与性能证据
   - 部署健康检查
   - 500 用户读链路监控压测
   - 15 用户核心业务链路压测
   - 较早噪声压测为什么不作为主结论

9. 准确率证据
   - 问答评测结果
   - 批改评测结果
   - 当前测试集范围边界

10. 缺口收口清单
   - 复用 [final-rbs-gap-closure-checklist-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-gap-closure-checklist-draft.md)

11. 最终声明边界
   - 可安全提交的表述
   - 必须避免的过度表述

## 建议附录

### 附录 A：证据文件索引

- [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md)
- [final-rbs-test-coverage-matrix-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-test-coverage-matrix-draft.md)
- [data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json)
- [2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md)
- [M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md)
- [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv)
- [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv)

### 附录 B：已收口的历史缺口

- `R7121`：问答与批改准确率均已有当前测试集范围内 90% 以上证据。
- `R2131`：最终 RBS 已对齐为 RAG 检索与 grounding 范围，当前证据可关闭。
- `R2111`：已有 `pdf / docx / pptx` 正向解析测试。
- `R4111`：已有文档附件进入评分输入链路证据。
- `R7231`：已有异常提示族自动化测试证据。




