# M2 QA Checklist

目标：为 `M2 — Q&A MVP` 建立最小可执行的问答评测记录，区分检索问题和回答问题。

使用方式：

1. 先用 `backend/script/test_rag_retrieval.py` 跑检索。
2. 再用 `/api/v1/chat/send` 跑真实问答。
3. 对每道题填写下表。

判定字段说明：

- `retrieved_chunk_ok`
  - `yes`：top-k 中已经命中正确资料
  - `no`：top-k 没命中正确资料
- `answer_ok`
  - `yes`：回答正确且基本完整
  - `partial`：回答部分正确但不完整
  - `no`：回答错误或明显跑偏
- `error_type`
  - `ok`
  - `retrieval_miss`
  - `answer_incomplete`
  - `answer_hallucination`
  - `source_not_covered`

---

## 当前验证课程

- `course_id`: `1`
- 资料样例：`Excel实验报告-批改.docx`
- 当前验证目标：确认向量检索与问答回答是否已基于课程资料工作

---

## 评测表

| id | question | expected_points | retrieved_chunk_ok | answer_ok | error_type | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Excel 中条件格式怎么设置？ | 应提到：条件格式、语文列大于 60、红色加粗、操作步骤 | pending | pending | pending | 先跑过，当前是检索命中样例题 |
| 2 | 什么是数组公式？ | 应提到：可同时对多个单元格/数据集合运算；旧版需 Ctrl+Shift+Enter，新版可直接 Enter | pending | pending | pending | 看回答是否区分旧版与新版 |
| 3 | Excel 中的绝对引用是什么？ | 应提到：使用 `$` 固定行/列；复制公式后引用不偏移 | pending | pending | pending | 检查是否回答成相对引用 |
| 4 | 高级筛选怎么做？ | 应提到：数据 -> 高级；设置列表区域、条件区域；结果保留在指定工作表 | pending | pending | pending | 看检索是否命中操作步骤 chunk |
| 5 | 数据透视表怎么统计优等生人数？ | 应提到：插入数据透视表；将“优等生”拖到行区域和值区域 | pending | pending | pending | 检查回答是否能提到字段拖拽 |

---

## 检索记录模板

每道题建议先记录一次检索结果：

```text
query:
top_k:
top_1 chunk_id:
top_1 resource_id:
top_1 chunk_index:
top_1 preview:
是否命中预期资料:
```

---

## 问答记录模板

```text
query:
assistant_answer:
expected_points:
缺失点:
是否有幻觉:
最终判断:
```

---

## 下一步

1. 先完成上面 5 道题的检索与问答记录。
2. 明天 D 提供正式题集后，继续往这份表里追加。
3. 后续按统计结果计算：
   - 检索命中率
   - 回答正确率
   - 最终 M2 准确率
