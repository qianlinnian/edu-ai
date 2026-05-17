# Assignment 页面前端联调说明

当前后端已经具备作业创建、作业提交、AI 批改、附件解析、批改结果查询、学情更新能力。前端主要需要把 `Assignment` 页面从 mock 数据改成真实 API 联调。

## 1. 需要修改的文件

- `frontend/src/pages/Assignment/index.tsx`
- `frontend/src/services/api.ts`

## 2. 当前问题

`Assignment/index.tsx` 里目前主要还是静态 mock 数据：

```ts
const ASSIGNMENTS = [...]
const SUBMISSIONS = [...]
const STUDENT_ASSIGNMENTS = [...]
```

提交作业弹窗现在也只是弹出成功提示，没有真正调用后端：

```tsx
onOk={() => { message.success('提交成功，等待 AI 批改'); setSubmitOpen(null) }}
```

这些需要改成真实接口。

## 3. services/api.ts 需要补充

当前已经有：

```ts
assignmentAPI.list(courseId)
assignmentAPI.create(data)
assignmentAPI.submit(assignmentId, content, file)
assignmentAPI.getResult(submissionId)
assignmentAPI.getAnnotations(submissionId)
```

还需要补一个老师查看提交列表的接口：

```ts
listSubmissions: (assignmentId: number) =>
  api.get(`/assignments/${assignmentId}/submissions`)
```

建议最终 Assignment API 保持如下：

```ts
export const assignmentAPI = {
  list: (courseId: number) => api.get('/assignments', { params: { course_id: courseId } }),
  create: (data: any) => api.post('/assignments', data),
  submit: (assignmentId: number, content?: string, file?: File) => {
    const form = new FormData()
    if (content) form.append('content', content)
    if (file) form.append('file', file)
    return api.post(`/assignments/${assignmentId}/submit`, form)
  },
  listSubmissions: (assignmentId: number) => api.get(`/assignments/${assignmentId}/submissions`),
  getResult: (submissionId: number) => api.get(`/assignments/submissions/${submissionId}/result`),
  getAnnotations: (submissionId: number) => api.get(`/assignments/submissions/${submissionId}/annotations`),
}
```

## 4. 老师端：作业列表

把 mock 的 `ASSIGNMENTS` 改为接口数据：

```ts
assignmentAPI.list(courseId)
```

对应后端：

```text
GET /api/v1/assignments?course_id=xxx
```

后端返回字段主要有：

```ts
{
  id: number
  course_id: number
  title: string
  description: string | null
  assignment_type: string
  max_score: number
}
```

如果页面需要课程名、截止时间、提交人数，目前后端作业接口还没有完整返回这些字段，可以先在前端弱化展示，或者后续再补后端字段。

## 5. 老师端：创建作业

创建作业弹窗需要调用：

```ts
assignmentAPI.create(data)
```

对应后端：

```text
POST /api/v1/assignments
```

建议表单字段：

```ts
{
  course_id: number
  title: string
  description?: string
  assignment_type: 'text' | 'code' | 'file' | 'mixed'
  max_score: number
  rubric?: object
  reference_answer?: string
  knowledge_points?: number[]
}
```

`rubric` 和 `reference_answer` 不需要单独上传路径，也不需要单独接口。它们就是作业的补充信息，创建作业时一起提交即可。

如果前端暂时不想做复杂 JSON 编辑器，可以先用文本框收集评分标准，然后包装成对象：

```ts
rubric: {
  description: values.rubricText
}
```

参考答案可以直接用文本框：

```ts
reference_answer: values.referenceAnswer
```

如果老师不填，后端会使用默认评分标准：

```text
正确性 60%、完整性 25%、表达清晰度 15%
```

## 6. 老师端：查看提交列表

老师点击某个作业后，不要再使用 mock `SUBMISSIONS`。

改为调用：

```ts
assignmentAPI.listSubmissions(assignmentId)
```

对应后端：

```text
GET /api/v1/assignments/{assignment_id}/submissions
```

返回的是提交记录，主要字段：

```ts
{
  id: number
  assignment_id: number
  student_id: number
  content: string | null
  file_path: string | null
  status: 'PENDING' | 'GRADING' | 'GRADED' | 'FAILED'
  submitted_at: string
}
```

如果需要显示分数，需要对已批改的 submission 调用：

```ts
assignmentAPI.getResult(submissionId)
```

## 7. 学生端：作业列表

学生端也应使用：

```ts
assignmentAPI.list(courseId)
```

当前后端还没有单独区分“我的提交状态”的聚合接口，所以第一版可以这样做：

- 作业列表先展示所有课程作业。
- 点击“提交作业”后拿到 `submissionId`。
- 提交后显示“等待 AI 批改”。
- 之后用 `getResult(submissionId)` 查询批改结果。

更完整的版本可以后续让后端补一个“我的作业 + 我的提交状态”接口。

## 8. 学生端：提交作业

提交弹窗需要真正调用：

```ts
assignmentAPI.submit(assignmentId, content, file)
```

对应后端：

```text
POST /api/v1/assignments/{assignment_id}/submit
```

提交成功后，后端返回：

```ts
{
  id: number
  status: string
  message: string
}
```

这里的 `id` 是 `submissionId`，前端需要保存下来，用于后续查询批改结果。

## 9. 文件上传类型

当前前端是：

```tsx
accept=".py,.pdf,.doc,.docx"
```

建议改为：

```tsx
accept=".py,.txt,.md,.pdf,.docx,.pptx,.xlsx,.csv,.json"
```

暂时不要放 `.doc`。老 Word `.doc` 后端不稳定支持，当前稳定支持的是 `.docx`。

后端 worker 会从 MinIO 读取附件，并解析以下类型后交给 LLM 批改：

```text
pdf, docx, pptx, xlsx, txt, md, py, json, csv
```

## 10. 批改结果展示

提交后调用：

```ts
assignmentAPI.getResult(submissionId)
```

对应后端：

```text
GET /api/v1/assignments/submissions/{submission_id}/result
```

如果返回 `404`，说明 worker 还没有批改完，前端显示：

```text
等待 AI 批改
```

如果成功，展示：

```ts
{
  score: number
  max_score: number
  overall_comment: string
  strengths: string[]
  weaknesses: string[]
}
```

建议页面显示：

- 分数：`score / max_score`
- 总评：`overall_comment`
- 优点：`strengths`
- 不足：`weaknesses`

## 11. 前端最小完成标准

本阶段前端最小可交付目标：

1. 老师可以创建作业。
2. 老师可以看到某课程作业列表。
3. 学生可以提交文本或文件。
4. 提交后可以看到“等待 AI 批改”。
5. worker 批改完成后，前端可以展示分数和评语。
6. 文件上传限制和后端支持类型一致。

## 12. 后端当前状态

后端已经支持：

- 文本提交。
- 文件提交。
- MinIO 保存附件。
- worker 异步批改。
- PDF / DOCX / PPTX / XLSX / TXT / MD / PY / JSON / CSV 附件解析。
- LLM 批改优先。
- LLM 失败时规则兜底。
- 批改后写入掌握度和弱点预警。

前端接完 API 后，需要用真实页面跑一次完整流程。
