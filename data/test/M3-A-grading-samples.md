# M3-A Grading Samples

## 2. 附件批改样例

### 2.1 真实模型响应：附件递归答案

> 说明：本样例用于验证 A-7 附件批改链路。附件建议使用 `recursion_answer.txt` 上传。  
> 上传后，请将本文档中的 `file_path` 替换为后端实际返回、并且 MinIO 可读取的真实路径。  
> 文档中不得写入 API key、本地密钥路径或其他敏感配置。

#### 验证目标

本样例验证以下真实链路：

```text
附件 file_path
-> MinIO 读取
-> parse_resource_content 解析文本
-> _build_grading_content 拼进 prompt
-> _grade_with_llm 调真实模型
-> 标准化输出 annotations / knowledge_point_scores
```

#### 作业信息

- 作业标题：M3 附件批改样例：递归函数说明
- 满分：100
- 关联知识点：`[8, 9]`
- 评分标准：正确性 60%，完整性 25%，表达清晰度 15%
- 参考答案：递归函数应包含终止条件和递归调用过程，每次递归应逐步接近终止条件。
- 附件类型：txt
- file_path：`REPLACE_WITH_REAL_MINIO_FILE_PATH_AFTER_UPLOAD`

#### 附件文件

- 文件名：`recursion_answer.txt`
- 建议 MIME 类型：`text/plain`
- 编码：`UTF-8`

#### 附件原文

```text
递归函数就是函数调用自己。
例如 factorial(n) = n * factorial(n-1)。
我写递归时通常不需要终止条件，因为程序会自己停止。
```

#### 附件内容摘要

学生通过附件提交了递归函数说明，能说明函数调用自身和 factorial 示例，但错误认为递归不需要终止条件。

#### 标准化后的真实模型结果

> 注意：以下 JSON 结构应由 `_grade_with_llm()` 调用真实模型后，再经过 A 的标准化逻辑生成。  
> 如果实际运行结果的分数或评语不同，可以保留真实结果；但必须满足合格标准中的结构要求。

```json
{
  "score": 72,
  "overall_comment": "学生能够说明递归函数的基本含义，并给出了 factorial 的递归表达式示例，说明其理解了“函数调用自身”这一核心概念。但答案中错误地认为递归不需要终止条件，这是递归设计中的关键问题，可能导致无限递归或栈溢出。建议补充终止条件、递归推进过程以及递归调用逐步接近终止条件的说明。",
  "strengths": [
    "能够指出递归函数是函数调用自身。",
    "能够使用 factorial(n) = n * factorial(n-1) 作为递归示例。"
  ],
  "weaknesses": [
    "错误认为递归不需要终止条件。",
    "没有说明递归调用需要逐步接近终止条件。",
    "答案完整性不足，缺少 base case 和 recursive case 的区分。"
  ],
  "annotations": [
    {
      "position": {
        "quote": "递归函数就是函数调用自己。"
      },
      "comment": "该表述基本正确，说明学生理解了递归的核心定义。"
    },
    {
      "position": {
        "quote": "例如 factorial(n) = n * factorial(n-1)。"
      },
      "comment": "示例方向正确，但缺少 factorial(0) 或 factorial(1) 等终止条件。"
    },
    {
      "position": {
        "quote": "我写递归时通常不需要终止条件，因为程序会自己停止。"
      },
      "comment": "这是明显错误。递归函数必须设计终止条件，否则可能出现无限递归或栈溢出。"
    }
  ],
  "knowledge_point_scores": {
    "8": {
      "score": 38,
      "max_score": 50,
      "comment": "基本理解递归定义，但对终止条件理解有严重错误。"
    },
    "9": {
      "score": 34,
      "max_score": 50,
      "comment": "能够给出递归表达式示例，但没有完整说明递归过程和停止条件。"
    }
  },
  "source": "llm"
}
```

#### 合格标准检查

- `source` 是 `llm`
- `annotations` 是数组，且至少包含 1 条
- `knowledge_point_scores` 是对象
- `position.quote` 能对应附件里的原文片段
- `file_path` 是真实后端能读取的附件路径
- 文档里不包含 API key、本地密钥路径或其他敏感配置

#### 运行后需要替换的内容

- 将 `REPLACE_WITH_REAL_MINIO_FILE_PATH_AFTER_UPLOAD` 替换为真实上传后得到的 MinIO 路径。
- 将“标准化后的真实模型结果”替换为真实 LLM 调用后的标准化输出。
- 保留 `position.quote` 与附件原文的一致性，避免 quote 无法定位。
