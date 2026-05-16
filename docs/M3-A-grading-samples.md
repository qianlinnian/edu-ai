# M3-A 批改输出样例

更新时间：26-05-16 22:39  
用途：给后端 B 落库、前端 C 展示和集成 D 验收时对齐批改结果结构。

## 1. 文本提交样例

### 1.1 真实模型响应：递归基础题

调用方式：
- 工作目录：`D:\course\SEME\edu-ai\backend`
- 命令：使用 `D:\software\Anaconda\envs\edu\python.exe -X utf8 -c "..."` 直接调用 `_grade_with_llm`
- 说明：该结果为真实 LLM 返回后，经 A 的标准化逻辑处理后的结构化结果。

#### 作业信息

- 作业标题：M3 AI批改样例：递归基础题
- 满分：100
- 关联知识点：`[8, 9]`
- rubric：正确性 60%，完整性 25%，表达清晰度 15%
- reference answer：递归函数通常包含递归终止条件和递归调用过程，并且每次调用应逐步接近终止条件。

#### 学生提交内容

```text
递归就是函数自己调用自己。比如 factorial(n) 可以调用 factorial(n-1)。但是我觉得不需要终止条件，只要一直调用就可以得到结果。
```

#### 标准化后的真实模型结果

```json
{
  "score": 20.0,
  "overall_comment": "学生对递归的基本概念有初步了解，但未能正确理解递归函数的核心要素，特别是忽略了递归终止条件的重要性。",
  "strengths": [
    "能够正确理解递归的基本概念，即函数调用自身"
  ],
  "weaknesses": [
    "错误地认为递归不需要终止条件",
    "未能解释递归函数必须包含的组成部分"
  ],
  "annotations": [
    {
      "annotation_type": "error",
      "position": {
        "type": "text",
        "line": 1,
        "paragraph": 1,
        "quote": "但是我觉得不需要终止条件，只要一直调用就可以得到结果"
      },
      "content": "递归函数必须包含终止条件，否则会导致无限递归，最终栈溢出",
      "severity": "critical",
      "knowledge_point_id": 8
    },
    {
      "annotation_type": "warning",
      "position": {
        "type": "text",
        "line": 1,
        "paragraph": 1,
        "quote": "递归就是函数自己调用自己"
      },
      "content": "这个描述过于简单，未能完整解释递归函数的组成部分",
      "severity": "medium",
      "knowledge_point_id": 9
    }
  ],
  "knowledge_point_scores": {
    "8": 30.0,
    "9": 10.0
  },
  "source": "llm"
}
```

验收点：
- `source` 为 `llm`。
- `annotations` 为数组，包含 2 条真实批注。
- `knowledge_point_scores` 为对象，包含知识点 `8` 和 `9` 的分项得分。
- 批注位置使用 `position.type = "text"` 和 `quote` 对齐学生原文片段。

### 1.2 结构示例：递归函数分析

### 2.1 真实模型响应：附件递归答案

调用方式：
- 工作目录：`D:\course\SEME\edu-ai\backend`
- 测试文件：`D:\course\SEME\edu-ai\data\test\recursion_answer.txt`
- MinIO 路径：`m3-a-test/recursion_answer.txt`
- 说明：该结果验证了“附件上传到 MinIO -> 后端读取附件 -> 解析文本 -> 交给真实 LLM -> A 标准化输出”的链路。

#### 作业信息

- 作业标题：M3 附件批改样例：递归函数说明
- 满分：100
- 关联知识点：`[8, 9]`
- rubric：正确性 60%，完整性 25%，表达清晰度 15%
- reference answer：递归函数应包含终止条件和递归调用过程，每次递归应逐步接近终止条件。

#### 附件信息

- 文件名：`recursion_answer.txt`
- MinIO file_path：`m3-a-test/recursion_answer.txt`
- 文件类型：txt
- 解析警告：无

#### 附件解析内容

```text
[附件解析内容]
递归函数就是函数调用自己。
例如 factorial(n) = n * factorial(n-1)。
我写递归时通常不需要终止条件，因为程序会自己停止。
```

#### 标准化后的真实模型结果

```json
{
  "score": 20.0,
  "overall_comment": "学生对递归函数的基本概念有了解，但缺乏对递归函数核心要素的完整理解，特别是忽略了终止条件的重要性。",
  "strengths": [
    "能够正确识别递归函数的基本定义"
  ],
  "weaknesses": [
    "未提及递归函数的终止条件",
    "错误认为递归不需要终止条件",
    "未解释递归调用如何逐步接近终止条件"
  ],
  "annotations": [
    {
      "annotation_type": "error",
      "position": {
        "type": "text",
        "line": 1,
        "paragraph": 1,
        "quote": "递归函数就是函数调用自己。"
      },
      "content": "递归函数的定义不完整，递归函数不仅是函数调用自己，还需要有明确的终止条件。",
      "severity": "medium",
      "knowledge_point_id": 8
    },
    {
      "annotation_type": "error",
      "position": {
        "type": "text",
        "line": 2,
        "paragraph": 1,
        "quote": "例如 factorial(n) = n * factorial(n-1)。"
      },
      "content": "这个例子缺少了终止条件的说明，完整的阶乘递归函数应该包含当n=0或n=1时的返回值。",
      "severity": "high",
      "knowledge_point_id": 8
    },
    {
      "annotation_type": "suggestion",
      "position": {
        "type": "text",
        "line": 3,
        "paragraph": 1,
        "quote": "我写递归时通常不需要终止条件，因为程序会自己停止。"
      },
      "content": "这是完全错误的观点。没有终止条件的递归函数会导致无限递归，最终导致栈溢出错误。终止条件是递归函数的必要组成部分。",
      "severity": "critical",
      "knowledge_point_id": 9
    }
  ],
  "knowledge_point_scores": {
    "8": 30.0,
    "9": 10.0
  },
  "source": "llm"
}
```

验收点：
- `source` 为 `llm`。
- `annotations` 为数组，包含 3 条真实批注。
- `knowledge_point_scores` 为对象，包含知识点 `8` 和 `9` 的分项得分。
- `position.quote` 均能对应附件解析内容中的原文片段。
- 附件解析无 warning，说明 MinIO 读取和 txt 解析链路正常。

### 2.2 结构示例：实验报告批改

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

## 4. A 输出字段契约

A 输出的是标准化后的批改结果。后端 B、前端 C 和集成 D 应以这里的字段为准，不再猜测 LLM 原始文本结构。

### 4.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `score` | number | 是 | 最终得分，范围满足 `0 <= score <= max_score`。 |
| `overall_comment` | string | 是 | 总体评价，标准化后保证非空。 |
| `strengths` | string[] | 是 | 优点列表；没有内容时返回 `[]`。 |
| `weaknesses` | string[] | 是 | 不足列表；没有内容时返回 `[]`。 |
| `annotations` | object[] | 是 | 批注列表；没有批注时返回 `[]`。 |
| `knowledge_point_scores` | object | 是 | 知识点分项得分；没有关联知识点时返回 `{}`。 |
| `source` | string | 是 | `llm` 或 `fallback`，表示批改结果来源。 |

说明：
- `score` 是作业满分制下的实际得分。
- `knowledge_point_scores` 是百分制掌握度分数，不是作业满分制得分。
- `fallback` 场景下也必须保持同一字段集合，方便前端和落库逻辑复用。

### 4.2 annotations 字段

`annotations` 中每一项的结构如下：

```json
{
  "annotation_type": "error",
  "position": {
    "type": "text",
    "line": 1,
    "paragraph": 1,
    "quote": "学生原文片段"
  },
  "content": "批注意见",
  "severity": "medium",
  "knowledge_point_id": 1
}
```

字段约定：
- `annotation_type`: 只使用 `error` / `warning` / `suggestion` / `praise`。
- `severity`: 只使用 `low` / `medium` / `high` / `critical`。
- `position.type`: M3 第一版统一为 `text`。
- `position.quote`: 尽量保存学生原文片段，便于前端定位或展示。
- `knowledge_point_id`: 可以是整数，也可以是 `null`；无法匹配知识点时返回 `null`。

### 4.3 knowledge_point_scores 字段

示例：

```json
{
  "8": 30.0,
  "9": 10.0
}
```

字段约定：
- key 使用字符串形式的知识点 ID。
- value 使用 `0-100` 范围内的数字。
- A 会过滤当前作业未关联的知识点 ID。
- 如果 LLM 没有返回有效知识点得分，A 会根据总分和关联知识点生成 fallback 分项结果；没有关联知识点时返回 `{}`。

## 5. B/C/D 对接说明

- 后端 B：可以把 `knowledge_point_scores` 写入 `grading_results`，把 `annotations` 展开写入 `submission_annotations`。
- 前端 C：可以直接渲染 `score`、`overall_comment`、`strengths`、`weaknesses`，annotations 为空时显示空状态。
- 集成 D：验收时优先检查字段类型是否稳定，而不是只看自然语言评价是否丰富。

### 5.1 后端 B 落库建议

- `grading_results.score` 使用 `score`。
- `grading_results.overall_comment` 使用 `overall_comment`。
- `grading_results.strengths` 使用 `strengths`。
- `grading_results.weaknesses` 使用 `weaknesses`。
- `grading_results.knowledge_point_scores` 使用 `knowledge_point_scores`。
- `submission_annotations` 从 `annotations` 展开写入：
  - `submission_id`: 当前提交 ID。
  - `annotation_type`: `annotation.annotation_type`。
  - `position`: `annotation.position`。
  - `content`: `annotation.content`。
  - `severity`: `annotation.severity`。
  - `knowledge_point_id`: `annotation.knowledge_point_id`。
- 重复批改同一提交时，建议 B 先删除旧的 `submission_annotations`，再写入新批注，避免前端看到重复批注。

### 5.2 前端 C 展示建议

- 分数区域展示 `score / max_score`。
- 总评展示 `overall_comment`。
- 优点和不足分别展示 `strengths`、`weaknesses`，数组为空时显示空状态。
- 批注列表展示 `annotations`：
  - 用 `annotation_type` 区分错误、警告、建议、表扬。
  - 用 `severity` 区分严重程度。
  - 优先展示 `position.quote`，再展示 `content`。
- 知识点得分展示 `knowledge_point_scores`，key 需要由 C 或 B 根据知识点列表映射成名称。

### 5.3 集成 D 验收建议

- 验证 LLM 正常时 `source=llm`。
- 验证 LLM 不可用时 `source=fallback`，但字段集合不变。
- 验证 `annotations` 一定是数组。
- 验证 `knowledge_point_scores` 一定是对象。
- 验证 B/C 使用这些字段时不需要额外判断 string/null/object 混合形态。
