# 平台适配说明

## 当前口径
当前仅实现“模拟平台接入”，不伪装成真实超星或钉钉集成。

后端行为：
- 接收上游平台传入的 `course_id`
- 接收上游平台传入的 `role`
- 接收上游平台传入的 `launch_ticket` 或 `auth_code`
- 由 EduAI 后端签发嵌入用 `token`
- 由 EduAI 后端返回最终 `widget_url`

## 字段来源统一定义
- `widget_url`: 由 EduAI 后端生成，格式为 `/widget/chat?course={course_id}&token={embed_token}`
- `token`: 由 EduAI 后端签发，不由上游平台直接提供
- `course_id`: 由上游平台请求参数提供
- `role`: 由上游平台请求参数提供
- `launch_ticket` / `auth_code`: 由上游平台请求参数提供，仅用于模拟接入上下文，不做真实签名校验

## 超星模拟接口
- 路径：`POST /api/v1/platform/chaoxing/lti-launch`
- 请求：
  - `course_id`
  - `role`
  - `launch_ticket`

## 钉钉模拟接口
- 路径：`GET /api/v1/platform/dingtalk/auth`
- 请求：
  - `course_id`
  - `role`
  - `code`

## 当前未实现部分
- 未接入真实超星 LTI SDK
- 未接入真实钉钉 OAuth / SDK
- 未做真实回调签名校验
- 未做生产级 token 生命周期编排
