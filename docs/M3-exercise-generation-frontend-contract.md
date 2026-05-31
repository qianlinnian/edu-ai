# M3 个性化练习生成前端对接说明

## 目标

学生在练习中心点击“根据薄弱点生成练习”后，前端调用后端接口。后端会读取该学生在课程内的学情掌握度与知识点信息，优先调用 LLM 生成中文个性化练习题，并写入 `generated_exercises`。如果 LLM 不可用，后端会回退到题库推荐或兜底题，保证页面可用。

## 接口

`POST /api/v1/exercises/generate`

认证：需要学生登录态 Bearer Token。当前接口会校验用户角色为 `student`，并确认该学生已加入 `course_id` 对应课程。

请求体：

```json
{
  "course_id": 2,
  "knowledge_point_ids": [8, 9],
  "exercise_type": "choice",
  "difficulty": 2,
  "count": 3,
  "use_llm": true
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `course_id` | number | 是 | 当前课程 ID |
| `knowledge_point_ids` | number[] | 否 | 指定知识点。为空或不传时，后端会根据学生学情自动选择薄弱知识点 |
| `exercise_type` | string | 否 | 当前建议传 `"choice"` |
| `difficulty` | number | 否 | 难度 1-5，默认 2 |
| `count` | number | 否 | 生成数量，后端限制 1-10，默认 5 |
| `use_llm` | boolean | 否 | 是否调用 LLM，默认 `true`。调试题库推荐时可传 `false` |

## 返回体

```json
{
  "message": "Generated 3 exercises",
  "source": "generated",
  "generation_method": "llm",
  "exercises": [
    {
      "id": 21,
      "source": "generated",
      "generation_method": "llm",
      "type": "choice",
      "question": "以下关于递归终止条件的说法正确的是？",
      "options": [
        { "key": "A", "label": "递归函数不需要终止条件" },
        { "key": "B", "label": "终止条件用于结束递归并防止无限调用" },
        { "key": "C", "label": "递归只能调用一次自身" },
        { "key": "D", "label": "递归函数不能返回值" }
      ],
      "answer": "B",
      "explanation": "递归必须包含终止条件，否则可能无限递归并导致栈溢出。",
      "difficulty": 2,
      "knowledge_point_ids": [8],
      "generated_exercise_id": 21
    }
  ]
}
```

`source` 取值：

| 值 | 含义 |
|---|---|
| `generated` | 来自 `generated_exercises`，提交作答时使用 `generated_exercise_id` |
| `pool` | 从 `exercise_pool` 题库匹配 |
| `empty` | 没有可返回题目 |

`generation_method` 取值：

| 值 | 含义 |
|---|---|
| `llm` | LLM 根据学情生成 |
| `fallback` | LLM 失败且题库不足时的兜底生成 |
| `null` | 题库题或空结果 |

## 前端按钮建议

练习中心增加按钮：

- 文案：`根据薄弱点生成练习`
- 点击后调用 `POST /exercises/generate`
- loading 文案：`AI 正在根据你的学情生成练习...`
- 成功后用返回的 `exercises` 替换当前题目列表
- 如果 `source === "generated" && generation_method === "llm"`，可显示标签 `AI 生成`
- 如果 `source === "pool"`，可显示标签 `题库推荐`
- 如果 `source === "generated" && generation_method === "fallback"`，可提示 `AI 生成失败，已提供兜底练习`

## 作答接口保持不变

LLM 生成题应使用返回的 `generated_exercise_id` 提交作答：

`POST /api/v1/exercises/attempt`

```json
{
  "generated_exercise_id": 21,
  "student_answer": "B"
}
```

题库题仍使用：

```json
{
  "exercise_id": 5,
  "student_answer": "B"
}
```
