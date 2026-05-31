# 综合 D 周报 纪鹏

## 一、工作目标

本阶段主要负责 M4 全功能集成的测试验证、平台适配、文档整理以及 Agent Builder 对接工作。对应 M4 里程碑的"平台嵌入与 Agent 可视化构建器完成"目标。

对应 WBS：
- W6.1 超星嵌入规格准备
- W6.2 钉钉嵌入规格准备
- W5.3 Agent Builder 页面开发
- W5.4 iframe Widget 构建
- W7.1 后端 API 测试
- W7.2 接口验证与端到端测试
- W8.1 交付文档与测试报告整理

## 二、已完成工作

### 1. 平台适配接口实现与验证

#### 超星 LTI 接口
- 路径：`POST /api/v1/platform/chaoxing/lti-launch`
- 实现内容：接收 LTI 启动请求，返回 platform、status、widget_url
- 错误处理：参数缺失时返回明确错误信息
- 验证结果：✅ 符合验证口径

#### 钉钉认证接口
- 路径：`GET /api/v1/platform/dingtalk/auth`
- 实现内容：接收免登授权码，返回 platform、status、widget_url
- 错误处理：code 参数缺失时返回明确错误
- 验证结果：✅ 符合验证口径

### 2. Agent Builder 功能完善

#### 后端 API
- 修复 `POST /api/v1/agents/instances` 事务问题（添加 commit）
- 修复 `POST /api/v1/agents/workflows` 缺少 is_active 字段问题
- 新增流式问答接口 `POST /api/v1/chat/send-stream`
  - 支持 SSE 事件流
  - 事件格式：`chunk` → `done`/`error`

#### 前端对接
- `frontend/src/services/api.ts` 新增 `saveAndPublish` 方法
- `frontend/src/pages/AgentBuilder/index.tsx` 保存/发布按钮对接后端 API
- 前端默认 course_id 修正为 3（Python程序设计）

### 3. 端到端测试执行

使用 Python requests 脚本完成以下场景测试：

| 测试场景 | 接口 | 状态 | 备注 |
|----------|------|------|------|
| 普通问答 | `POST /chat/send` | ✅ 通过 | Session ID: 5 |
| 流式问答 | `POST /chat/send-stream` | ✅ 部分通过 | 90 个 chunk |
| 超星 LTI | `POST /platform/chaoxing/lti-launch` | ✅ 通过 | 符合口径 |
| 钉钉认证 | `GET /platform/dingtalk/auth` | ✅ 通过 | 符合口径 |
| Agent 创建 | `POST /agents/instances` | ✅ 通过 | ID: 8 |
| 工作流创建 | `POST /agents/workflows` | ✅ 通过 | ID: 1 |

### 4. 测试文档整理

| 文档 | 路径 | 说明 |
|------|------|------|
| M4 测试计划 | `docs/test-reports/M4-测试计划-v0.4.0.md` | 6 个 E2E 场景定义 |
| M4 证据记录 | `docs/test-reports/M4-测试证据记录-v0.4.0.md` | 完整请求/响应记录 |
| 交付材料清单 | `docs/M4-交付材料清单与追踪矩阵.md` | Charter/RBS/WBS 对齐 |
| 系统测试报告 | `docs/test-reports/2026-04-22-系统测试报告-v0.1.0.md` | 已更新含 M4 结果 |

### 5. 环境搭建与数据准备

- 配置本地开发环境 `.env` 文件
- 安装后端依赖 `requirements.txt`
- 执行数据库迁移 `alembic upgrade head`
- 创建 pgvector 扩展
- 初始化测试数据：
  - 用户：test_teacher / password123 (ID: 4)
  - 课程：Python程序设计 (ID: 3)
  - Agent：Python答疑Agent (ID: 3, 8)

## 三、遗留问题

| 问题 | 影响 | 后续处理 |
|------|------|----------|
| LLM API 偶发空响应 | 流式问答偶发中断 | M5 增加重试机制 |
| 前端 Widget 浏览器测试 | 完整 E2E 验证 | 前端 C 启动后验证 |
| BUG-001 注册功能 | 无法创建新用户 | 后端 A 排查 |
| 部分 UI 问题 | 用户体验 | M5 阶段处理 |

## 四、工时统计

累计工时：约 18 小时

| WBS | 工作内容 | 工时 |
|-----|----------|------|
| W6.1 | 超星嵌入规格准备 | 2h |
| W6.2 | 钉钉嵌入规格准备 | 2h |
| W5.3 | Agent Builder 页面开发 | 3h |
| W5.4 | iframe Widget 构建 | 1h |
| W7.1 | 后端 API 测试 | 4h |
| W7.2 | 接口验证与端到端测试 | 4h |
| W8.1 | 交付文档与测试报告整理 | 2h |
| **合计** | | **18h** |

## 五、下阶段工作

1. 持续追踪 BUG-001 注册功能修复
2. 配合前端完成 Widget 和 Builder 浏览器端 E2E 测试
3. 准备 M5 交付阶段文档
4. 补充数据库备份与演示材料
