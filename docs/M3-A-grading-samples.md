# M3-A 批改输出样例

更新时间：26-05-14 22:28  
用途：给后端 B 落库、前端 C 展示和集成 D 验收时对齐批改结果结构。

## 1. 文本提交样例

### 作业信息

- 作业标题：递归函数分析
- 满分：100
- 关联知识点：`[3, 4]`
- rubric：正确性 60%，完整性 25%，表达清晰度 15%

### 学生提交摘要

学生说明了递归会不断调用自身，但没有明确终止条件，也没有说明参数如何向终止条件收敛。

### 标准化批改结果

```json
{
  "score": 72,
  "max_score": 100,
  "overall_comment": "答案覆盖了递归的基本概念，但对终止条件和参数收敛过程说明不足。",
  "strengths": ["能说明递归函数会调用自身", "答案结构较清晰"],
  "weaknesses": ["没有明确说明递归终止条件", "缺少参数变化过程分析"],
  "knowledge_point_scores": {
    "3": 78,
    "4": 55
  },
  "annotations": [
    {
      "annotation_type": "suggestion",
      "position": {
        "type": "text",
        "paragraph": 1,
        "quote": "递归会一直调用直到结束"
      },
      "content": "建议明确说明递归终止条件，否则容易造成无限递归。",
      "severity": "medium",
      "knowledge_point_id": 4
    }
  ],
  "source": "llm"
}
```

## 2. 附件提交样例

### 作业信息

- 作业标题：实验报告批改
- 满分：100
- 关联知识点：`[7, 8]`
- reference answer：实验报告应包含实验目的、实验过程、结果分析和总结。

### 学生提交摘要

学生上传 DOCX 实验报告。报告包含实验目的和过程，但结果分析较简略，总结部分为空。

### 标准化批改结果

```json
{
  "score": 80,
  "max_score": 100,
  "overall_comment": "实验报告结构基本完整，实验目的和过程描述清楚，但结果分析和总结部分仍需补充。",
  "strengths": ["实验目的明确", "实验过程描述较完整"],
  "weaknesses": ["结果分析不够深入", "实验总结缺失"],
  "knowledge_point_scores": {
    "7": 86,
    "8": 62
  },
  "annotations": [
    {
      "annotation_type": "warning",
      "position": {
        "type": "text",
        "paragraph": 4,
        "quote": "实验总结"
      },
      "content": "该部分内容为空，建议补充实验收获、问题和解决过程。",
      "severity": "medium",
      "knowledge_point_id": 8
    }
  ],
  "source": "llm"
}
```

## 3. fallback 样例

LLM 不可用时，仍应保持同一结构。

```json
{
  "score": 65,
  "max_score": 100,
  "overall_comment": "已完成自动批改（规则兜底）。LLM 批改暂不可用，已回退到基础规则。",
  "strengths": ["提交格式完整"],
  "weaknesses": [],
  "knowledge_point_scores": {
    "3": 65
  },
  "annotations": [],
  "source": "fallback"
}
```

## 4. B/C/D 对接说明

- 后端 B：可以把 `knowledge_point_scores` 写入 `grading_results`，把 `annotations` 展开写入 `submission_annotations`。
- 前端 C：可以直接渲染 `score`、`overall_comment`、`strengths`、`weaknesses`，annotations 为空时显示空状态。
- 集成 D：验收时优先检查字段类型是否稳定，而不是只看自然语言评价是否丰富。
