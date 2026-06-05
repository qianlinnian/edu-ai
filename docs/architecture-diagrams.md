# EduAI 系统图表

本文档包含项目的架构图、数据流图和活动图。

---

## 1. 系统架构图

```mermaid
graph TB
    subgraph Client["客户端层"]
        WebApp["React Web 应用<br/>(localhost:5173)"]
        Widget["Embeddable Widget<br/>(iframe)"]
    end

    subgraph Frontend["前端服务"]
        Vite["Vite Dev Server"]
        AntD["Ant Design 5"]
        ECharts["ECharts 可视化"]
        ReactFlow["React Flow<br/>(Agent Builder)"]
    end

    subgraph API_Gateway["API 网关"]
        Nginx["Nginx<br/>(可选)"]
    end

    subgraph Backend["后端服务"]
        FastAPI["FastAPI<br/>(localhost:8000)"]

        subgraph Routes["路由模块"]
            Auth["/auth<br/>认证"]
            Courses["/courses<br/>课程"]
            Agents["/agents<br/>Agent"]
            Assignments["/assignments<br/>作业"]
            Chat["/chat<br/>答疑"]
            Analytics["/analytics<br/>学情"]
            Exercises["/exercises<br/>练习"]
            Platform["/platform<br/>平台适配"]
        end

        subgraph Core["核心模块"]
            AgentCore["Agent Core<br/>AgentBase / LLM Provider"]
            Education["Education Engine<br/>批改 / 学情 / 练习"]
            RAG["RAG Chain<br/>知识检索"]
        end
    end

    subgraph Middleware["中间件层"]
        Celery["Celery Worker<br/>异步任务"]
        Redis["Redis<br/>(缓存/队列)"]
    end

    subgraph Storage["存储层"]
        Postgres["PostgreSQL + pgvector<br/>(数据库/向量)"]
        MinIO["MinIO<br/>(文件存储)"]
    end

    subgraph LLM["大模型服务"]
        DashScope["通义千问<br/>(qwen-max)"]
        DeepSeek["DeepSeek"]
        Zhipu["智谱 GLM"]
    end

    WebApp --> Vite
    WebApp --> AntD
    WebApp --> ECharts
    WebApp --> ReactFlow
    WebApp --> Nginx

    Widget --> Nginx

    Nginx --> FastAPI

    FastAPI --> Routes
    Routes --> Core
    Core --> AgentCore
    Core --> Education
    Core --> RAG

    FastAPI --> Celery
    Celery --> Redis

    Celery --> LLM
    AgentCore --> LLM
    Education --> LLM

    FastAPI --> Postgres
    FastAPI --> MinIO
    Celery --> Postgres
    RAG --> Postgres
```

---

## 2. 技术架构图

```mermaid
graph LR
    subgraph Frontend["前端 React 18"]
        A1["TypeScript"]
        A2["Vite"]
        A3["Ant Design 5"]
        A4["React Router"]
        A5["Zustand"]
        A6["ECharts"]
        A7["React Flow"]
    end

    subgraph Backend["后端 Python"]
        B1["FastAPI"]
        B2["SQLAlchemy 2.0"]
        B3["Alembic"]
        B4["Pydantic"]
        B5["Celery"]
        B6["LangChain"]
    end

    subgraph Database["数据库"]
        C1["PostgreSQL 16"]
        C2["pgvector"]
        C3["Redis 7"]
    end

    subgraph Storage["对象存储"]
        D1["MinIO"]
    end

    subgraph LLM["大模型"]
        E1["通义千问"]
        E2["DeepSeek"]
        E3["智谱"]
    end

    Frontend --> Backend
    Backend --> Database
    Backend --> Storage
    Backend --> LLM
    Backend --> Redis
```

---

## 3. 核心数据流图 (DFD)

### 3.1 智能答疑数据流

```mermaid
flowchart LR
    subgraph Input["用户输入"]
        Q["问题"]
    end

    subgraph Process1["1. 问题处理"]
        V["验证请求"]
        S["创建会话"]
    end

    subgraph Process2["2. RAG 检索"]
        K["知识检索"]
        E["向量匹配"]
        C["上下文构建"]
    end

    subgraph Process3["3. LLM 生成"]
        M["调用 LLM"]
        G["生成回答"]
    end

    subgraph Process4["4. 结果处理"]
        P["持久化消息"]
        R["返回响应"]
    end

    subgraph Output["输出"]
        A["回答内容"]
        RAG["检索来源"]
    end

    Q --> V --> S --> K
    K --> E --> C
    C --> M --> G
    G --> P --> R
    R --> A
    E --> RAG
```

### 3.2 作业批改数据流

```mermaid
flowchart TB
    subgraph Submit["1. 作业提交"]
        SF["学生提交"]
        VF["验证表单"]
        ST["保存提交记录"]
    end

    subgraph Task["2. 异步任务"]
        CQ["入队 Celery"]
        TW["任务执行"]
        LL["调用 LLM 批改"]
    end

    subgraph Grading["3. 批改处理"]
        PP["解析结果"]
        SG["评分"]
        AN["生成批注"]
        UK["知识点分析"]
    end

    subgraph Storage["4. 结果存储"]
        GR["写入批改结果"]
        AN2["写入批注"]
        MK["更新掌握度"]
        AL["生成预警"]
    end

    subgraph Output["5. 结果返回"]
        RT["返回结果"]
        SH["学生查看"]
    end

    Submit --> Task --> Grading --> Storage --> Output
```

### 3.3 练习生成数据流

```mermaid
flowchart LR
    subgraph Trigger["触发"]
        TR["薄弱点分析"]
    end

    subgraph Generate["练习生成"]
        GK["获取知识点"]
        PD["难度设置"]
        GN["生成题目"]
    end

    subgraph Validate["作答反馈"]
        AT["学生答题"]
        CH["检查答案"]
        FB["反馈结果"]
    end

    subgraph Update["数据更新"]
        UP["更新掌握度"]
        RG["生成新练习"]
    end

    TR --> GK --> PD --> GN --> AT --> CH --> FB --> UP --> RG
```

---

## 4. 活动图

### 4.1 学生使用主流程

```mermaid
flowchart TD
    START([开始]) --> LOGIN[登录系统]
    LOGIN --> SELECT[选择课程]
    SELECT --> CHOOSE{选择功能}

    CHOOSE -->|答疑| QA[进入答疑页面]
    QA --> ASK[输入问题]
    ASK --> STREAM[流式接收回答]
    STREAM --> MORE{还有问题?}
    MORE -->|是| ASK
    MORE -->|否| BACK1[返回]

    CHOOSE -->|做作业| HOMEWORK[进入作业页面]
    HOMEWORK --> VIEW[查看作业]
    VIEW --> SUBMIT[提交作业]
    SUBMIT --> WAIT{等待批改}
    WAIT -->|完成| GRADE[查看批改结果]
    GRADE --> ANALYZE[查看薄弱点]
    ANALYZE --> BACK2[返回]

    CHOOSE -->|练习| EXERCISE[进入练习页面]
    EXERCISE --> GENERATE[生成练习]
    GENERATE --> DO[答题]
    DO --> CHECK[检查答案]
    CHECK --> CORRECT{是否正确}
    CORRECT -->|是| NEXT[下一题]
    CORRECT -->|否| LEARN[学习解释]
    LEARN --> NEXT
    NEXT --> FINISH{完成?}
    FINISH -->|否| DO
    FINISH -->|是| RESULT[查看结果]
    RESULT --> BACK3[返回]

    BACK1 & BACK2 & BACK3 --> CHOOSE
    BACK1 & BACK2 & BACK3 --> LOGOUT[退出登录]
    LOGOUT --> END([结束])
```

### 4.2 教师创建 Agent 流程

```mermaid
flowchart TD
    START([开始]) --> LOGIN[登录系统]
    LOGIN --> BUILDER[进入 Agent Builder]
    BUILDER --> TEMPLATE{选择模板?}

    TEMPLATE -->|空白| ADD[添加节点]
    TEMPLATE -->|预置| CONFIGURE[配置预置节点]

    ADD --> DRAG[拖拽节点]
    DRAG --> CONNECT[连接节点]
    CONNECT --> CONFIG[配置参数]

    CONFIGURE --> ADJUST[调整配置]

    CONFIG & ADJUST --> SETTING{设置完成?}

    SETTING -->|继续| ADD
    SETTING -->|保存| SAVE[保存 Agent]

    SAVE --> NAME[填写名称]
    NAME --> COURSE[关联课程]
    COURSE --> MODEL[选择模型]
    MODEL --> TEST[测试运行]

    TEST --> OK{测试通过?}
    OK -->|否| FIX[修改配置]
    FIX --> TEST

    OK -->|是| PUBLISH[发布 Agent 配置]
    PUBLISH --> MAP[映射为线性 QA 运行配置]
    MAP --> SUCCESS[创建成功]
    SUCCESS --> NOTE[当前边界：可视化配置器，不宣称通用 DAG 运行引擎]
    NOTE --> END([结束])
```

### 4.3 平台嵌入启动流程

```mermaid
flowchart TB
    START([开始]) --> PLATFORM{选择平台}

    PLATFORM -->|超星| CHAOXING[超星平台]
    CHAOXING --> LTI[点击 EduAI 嵌入]
    LTI --> REQUEST[发送模拟 LTI Launch]
    REQUEST --> VALIDATE[校验启动参数]
    VALIDATE -->|有效| REDIRECT[返回 Widget URL]
    VALIDATE -->|无效| ERROR1[返回错误]

    PLATFORM -->|钉钉| DINGTALK[钉钉 H5 应用]
    DINGTALK --> AUTH[获取免登授权码]
    AUTH --> EXCHANGE[模拟 code 换取会话]
    EXCHANGE -->|成功| REDIRECT2[返回 Widget URL]
    EXCHANGE -->|失败| ERROR2[返回错误]

    REDIRECT & REDIRECT2 --> WIDGET[加载 Widget]
    ERROR1 & ERROR2 --> SHOW[展示错误信息]

    WIDGET --> INIT[初始化会话]
    INIT --> READY[Widget 就绪]
    READY --> NOTE[当前边界：未覆盖真实平台联调、真实签名校验与业务回流]
    NOTE --> END([结束])
```

---

## 5. 模块交互时序图

### 5.1 答疑时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as FastAPI
    participant R as RAG
    participant L as LLM
    participant DB as PostgreSQL

    U->>F: 输入问题
    F->>B: POST /chat/send-stream
    B->>DB: 查询 Agent
    DB-->>B: Agent 配置
    B->>R: 检索知识
    R->>DB: 向量相似度查询
    DB-->>R: 相关文档
    R-->>B: 上下文
    B->>L: 调用 LLM
    L-->>B: 流式响应
    B->>DB: 保存消息
    B-->>F: SSE 流
    F-->>U: 逐步展示回答

    Note over U,L: 整个过程 2-5 秒
```

### 5.2 作业批改时序图

```mermaid
sequenceDiagram
    participant S as 学生
    participant F as 前端
    participant B as FastAPI
    participant C as Celery
    participant L as LLM
    participant DB as PostgreSQL

    S->>F: 提交作业
    F->>B: POST /assignments/{id}/submit
    B->>DB: 保存提交记录
    B-->>F: 提交成功
    B->>C: 触发批改任务
    C->>L: 调用 LLM 批改
    L-->>C: 批改结果
    C->>DB: 写入批改结果
    C->>DB: 写入批注
    C->>DB: 更新知识点掌握度
    C-->>F: 批改完成通知
    F->>B: 查询批改结果
    B->>DB: 获取结果
    DB-->>B: 结果数据
    B-->>F: 返回结果
    F-->>S: 展示批改结果
```

### 5.3 Agent Builder 保存时序图

```mermaid
sequenceDiagram
    participant T as 教师
    participant F as 前端
    participant B as FastAPI
    participant DB as PostgreSQL

    T->>F: 配置工作流
    T->>F: 点击保存
    F->>B: POST /agents/instances
    B->>DB: 创建 Agent 实例
    DB-->>B: 实例 ID
    B-->>F: 返回实例信息

    F->>B: POST /agents/workflows
    B->>DB: 创建工作流 DAG
    DB-->>B: 工作流 ID
    B-->>F: 返回工作流信息

    F-->>T: 保存成功提示
```

---

## 6. 数据库 ER 图（核心实体）

```mermaid
erDiagram
    USERS ||--o{ COURSES : "teaches"
    USERS ||--o{ ENROLLMENTS : "enrolled"
    USERS ||--o{ CHAT_SESSIONS : "creates"
    USERS ||--o{ SUBMISSIONS : "submits"

    COURSES ||--o{ AGENT_INSTANCES : "contains"
    COURSES ||--o{ ASSIGNMENTS : "has"
    COURSES ||--o{ ENROLLMENTS : "enrolled"
    COURSES ||--o{ COURSE_RESOURCES : "has"

    AGENT_INSTANCES ||--o{ CHAT_SESSIONS : "powers"
    AGENT_INSTANCES ||--o{ AGENT_WORKFLOWS : "has"

    ASSIGNMENTS ||--o{ SUBMISSIONS : "receives"
    SUBMISSIONS ||--|| GRADING_RESULTS : "produces"
    SUBMISSIONS ||--o{ SUBMISSION_ANNOTATIONS : "has"

    COURSE_RESOURCES ||--o{ RESOURCE_CHUNKS : "chunks"
    COURSE_RESOURCES ||--o{ KNOWLEDGE_UNITS : "defines"

    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : "contains"

    USERS {
        int id PK
        string username
        string email
        string hashed_password
        string full_name
        string role
    }

    COURSES {
        int id PK
        string name
        string code
        string domain
        int teacher_id FK
    }

    AGENT_INSTANCES {
        int id PK
        int course_id FK
        string name
        string system_prompt
        string llm_provider
        string llm_model
    }

    ASSIGNMENTS {
        int id PK
        int course_id FK
        string title
        string description
        datetime due_date
    }

    SUBMISSIONS {
        int id PK
        int assignment_id FK
        int student_id FK
        string content
        string file_path
    }

    GRADING_RESULTS {
        int id PK
        int submission_id FK
        int score
        string overall_comment
        json knowledge_point_scores
    }
```

---

## 7. 部署架构图

```mermaid
graph TB
    subgraph Cloud["云服务器"]
        subgraph Container["Docker Compose"]
            Nginx["Nginx<br/>:80/:443"]
            Backend["FastAPI<br/>:8000"]
            Worker["Celery Worker<br/>批改任务"]
        end

        subgraph Data["数据服务"]
            Postgres["PostgreSQL<br/>:5432"]
            Redis["Redis<br/>:6379"]
            MinIO["MinIO<br/>:9000/:9001"]
        end
    end

    subgraph External["外部服务"]
        LLM["大模型 API<br/>通义千问/DeepSeek"]
    end

    subgraph Client["客户端"]
        Browser["浏览器<br/>Web App"]
    end

    Browser --> Nginx
    Nginx --> Backend
    Backend --> Postgres
    Backend --> Redis
    Backend --> MinIO
    Backend --> LLM
    Worker --> Postgres
    Worker --> Redis
    Worker --> LLM
```

---
