# Project Charter
## Embeddable Cross-Course AI Agent General Architecture Platform
## 1. Project Identification

| Field | Details |
| :--- | :--- |
| **Project Name** | Embeddable Cross-Course AI Agent General Architecture Platform |
| **Date of Authorization** | March 29, 2026 |
| **Project Start Date** | March 30, 2026 |
| **Project End Date** | June 14, 2026 |
| **Version** | 1.0 |

## 2. Project Stakeholders

| Name | Title / Role | Student ID | E-mail |
| :--- | :--- | :--- | :--- |
| 冯俊财 | AI Architect / Backend Engineer | 2353924 | 20614667@qq.com |
| 路清怡 | Backend Engineer | 2352996 | 849014041@qq.com |
| 张诗蔻 | Frontend Engineer | 2353240 | 2987991635@qq.com |
| 纪鹏 | Test & Documentation Engineer | 2351869 | jp3274313334@163.com |

## 3. Project Description

**Background:**
The current higher education sector suffers from "fragmented intelligent teaching." Each course independently develops its own AI teaching support system, leading to architectural heterogeneity, duplicate construction, and high integration costs. Existing systems lack a unified standard for embedding into mainstream Learning Management Systems (LMS) such as Chaoxing (超星) and DingTalk (钉钉). Furthermore, course-specific knowledge cannot be transferred or reused across disciplines, and assignment grading remains generic—lacking fine-grained annotation feedback that simulates a teacher's hand-written corrections.

**Description of the challenge or opportunity:**
There is a pressing need for a standardized, reusable AI Agent architecture that enables different courses to rapidly build and deploy intelligent teaching assistants without redundant engineering effort. Large Language Model (LLM) technology now makes it feasible to provide annotated, context-aware feedback at scale—transforming AI grading from "usable" to "precisely useful."

**Overview of the desired impact:**
This project delivers **EduAI**, a general-purpose AI Agent platform that: (1) provides a standardized SDK for rapid course-Agent development; (2) enables seamless embedding into Chaoxing and DingTalk via a lightweight iframe Widget; (3) performs annotation-style assignment grading with ≥ 95% accuracy; (4) analyzes student learning states and generates targeted exercises to close individual knowledge gaps.


## 4. Measurable Organizational Value (MOV)

The MOV defines the measurable value this project must deliver to justify its investment.

> **Primary MOV:** Enable universities to reduce the cost and time of building intelligent teaching systems for new courses, while delivering grading feedback quality that matches or exceeds manual teacher annotation.

| Area | Goal | Metric | Target Value |
| --- | --- | --- | --- |
| **Quality** | Deliver accurate in-course Q&A | Answer accuracy on core knowledge points | ≥ 95% |
| **Quality** | Deliver teacher-level grading feedback | Key error annotation accuracy (location + content) | ≥ 95% |
| **Cost** | Reduce duplicate AI system development effort | Reuse one SDK for ≥ 2 course types without code changes | Demonstrated in demo |
| **Performance** | Support large-scale concurrent access | Concurrent users supported | ≥ 500 |
| **Adoption** | Enable embedding in mainstream LMS platforms | Platforms supported via iframe/Widget | ≥ 2 (Chaoxing, DingTalk) |



## 5. Project Scope

**What is included in the scope of this project:**

- Unified AI Agent SDK (`AgentBase`, `QAAgent`, `GradingAgent`, `ExerciseAgent`) supporting multiple course types
- Knowledge middleware: document ingestion (PDF/Word/PPT), vector embedding (pgvector), knowledge graph, hybrid retrieval (vector + BM25 + Rerank)
- Refined intelligent engine: annotation-style grading (text, code, image), learning analytics (mastery matrix, early warning), personalized exercise generation
- RESTful API backend (FastAPI, 8 route groups: Auth, Courses, Agents, Assignments, Chat, Analytics, Exercises, Platform)
- Full frontend management portal (React 18, 9 pages): Login, Dashboard, Course Management, Intelligent Q&A, Assignment Management, Grading Result Viewer, Analytics Dashboard, Exercise Center, Agent Visual Builder
- Embeddable Widget (iframe-compatible lightweight chat/grading window for LMS integration)
- Platform adaptation layer: technical specification and simulated interfaces for Chaoxing (LTI) and DingTalk (H5)
- Cloud deployment: Docker Compose + Nginx + HTTPS on a cloud server

**What is outside the scope of this project:**

- Native mobile application (iOS/Android)
- Real-time live-class features (video streaming, screen sharing)
- Full production API certification and live integration with Chaoxing or DingTalk (simulated adaptation only, as permitted by competition rules)
- Automated billing or payment systems
- Support for physical lab equipment or hardware-linked experiments



## 6. Project Schedule Summary

- **Project start date:** March 30, 2026
- **Project end date:** June 14, 2026
- **Duration:** 11 weeks

**Key Milestones:**

| Milestone | Description | Target Date |
| :--- | :--- | :--- |
| **M1 — Foundation Ready** | Environment running; LLM API connected; database tables created; JWT auth working | April 12, 2026 |
| **M2 — Q&A MVP** | Upload course material → AI answers from course knowledge (accuracy ≥ 90%) | April 26, 2026 |
| **M3 — Teaching Loop Complete** | Submit assignment → AI annotates → learning analytics → exercises generated | May 17, 2026 |
| **M4 — Full Feature Complete** | Platform embedding + Agent visual builder complete; Q&A ≥ 95%, grading ≥ 95% | May 31, 2026 |
| **M5 — Project Delivery** | System fully deployed on cloud server; end-to-end demo validated; project documentation complete | June 14, 2026 |


## 7. Requirement Breakdown Structure (RBS)

1.0  Functional Requirements

  1.1  Unified AI Agent Framework
         Support rapid development and standardized deployment of
         course-specific AI Agents across different disciplines.

  1.2  Knowledge Middleware
         Standardized representation, storage, and retrieval of course
         knowledge; support cross-course knowledge transfer and reuse.

  1.3  Platform Adaptation
         Provide standardized interfaces for embedding into Chaoxing
         and DingTalk via iframe / H5 Widget.

  1.4  Intelligent Q&A
         Support multi-turn course Q&A; answer accuracy on core
         knowledge points ≥ 95%.

  1.5  Assignment Grading & Annotation
         Support multi-modal assignment grading (text, code, image);
         provide inline annotation feedback at error locations,
         simulating teacher hand-written corrections; key error
         annotation accuracy ≥ 95% (location + content).

  1.6  Learning Analytics & Early Warning
         Perform multi-dimensional analysis of individual and class-level
         knowledge weaknesses based on grading results and learning
         behavior; provide early warning for at-risk students.

  1.7  Personalized Exercise Generation
         Automatically generate or match targeted exercises based on
         identified knowledge weaknesses; implement "assess–grade–
         practice" closed loop.

  1.8  Agent Visual Builder
         Provide a visual, drag-and-drop tool for teachers to construct
         and customize course AI Agents without deep technical knowledge.

2.0  Non-Functional Requirements

  2.1  Performance: support ≥ 500 concurrent users
  2.2  Accuracy: Q&A ≥ 95%; grading annotation ≥ 95%
  2.3  Architecture: microservice-based, independently deployable components
  2.4  Security: role-based access control (teacher / student)
  2.5  Course coverage: support multiple course types via the same SDK

3.0  Constraints

  3.1  Primary LLM: Tongyi Qianwen (qwen-max / qwen-vl-max)
  3.2  Platform integration: technical specification only; real
         Chaoxing / DingTalk certification not required
  3.3  Timeline: fixed end date June 14, 2026



## 8. Work Breakdown Structure (WBS) & Hours Estimation

1.0  Project Management                                        24 hrs
  1.1  Project initiation & charter                              4 hrs
  1.2  Weekly progress meetings & tracking                      12 hrs
  1.3  Risk monitoring & issue resolution                        4 hrs
  1.4  Final review & submission coordination                    4 hrs

2.0  Requirements & System Design                              40 hrs
  2.1  Requirements elicitation & RBS                           8 hrs
  2.2  System architecture design                              12 hrs
  2.3  Database schema design                                   8 hrs
  2.4  API interface specification                              8 hrs
  2.5  UI/UX wireframes (9 pages)                               4 hrs

3.0  Infrastructure & DevOps                                   32 hrs
  3.1  Docker Compose environment setup                         8 hrs
  3.2  Database migration (Alembic)                             4 hrs
  3.3  Async task configuration (Celery + Redis)                8 hrs
  3.4  File storage setup (MinIO)                               4 hrs
  3.5  Cloud server deployment (Nginx)                          8 hrs

4.0  Backend Development                                      160 hrs
  4.1  Core infrastructure (auth, database models, seed data)  24 hrs
  4.2  Agent SDK (AgentBase, QAAgent, GradingAgent,
       ExerciseAgent, LLM provider integration)                40 hrs
  4.3  Knowledge middleware (document parsing, embedding,
       vector storage, knowledge graph)                        28 hrs
  4.4  Refined intelligent engine (grading, multimodal,
       learning analytics, exercise generation)                40 hrs
  4.5  API routes (8 groups)                                   28 hrs

5.0  Frontend Development                                      96 hrs
  5.1  Project setup & shared components                        8 hrs
  5.2  Login / Register page                                    4 hrs
  5.3  Dashboard                                                8 hrs
  5.4  Course management page                                  10 hrs
  5.5  Intelligent Q&A chat page                               10 hrs
  5.6  Assignment management + grading annotation viewer       16 hrs
  5.7  Analytics dashboard                                     10 hrs
  5.8  Exercise center                                          8 hrs
  5.9  Agent visual builder                                    12 hrs
  5.10 Platform configuration page                              4 hrs
  5.11 Embeddable Widget                                        6 hrs

6.0  Platform Adaptation                                       16 hrs
  6.1  Chaoxing adapter (simulated) + technical doc             8 hrs
  6.2  DingTalk adapter (simulated) + technical doc             8 hrs

7.0  Testing & Quality Assurance                               40 hrs
  7.1  Unit tests (backend API, Agent logic)                   12 hrs
  7.2  Q&A accuracy validation (≥ 95%)                          8 hrs
  7.3  Grading accuracy validation (≥ 95%)                     10 hrs
  7.4  Performance test (500-user concurrency)                  4 hrs
  7.5  End-to-end integration testing                           6 hrs

8.0  Documentation & Submission                                32 hrs
  8.1  Project overview introduction                            4 hrs
  8.2  Detailed technical solution document                    12 hrs
  8.3  Presentation PPT                                         8 hrs
  8.4  Demo video recording & editing                           8 hrs

| WBS | Module | Estimated Hours | Primary Responsible |
| :--- | :--- | :--- | :--- |
| 1.0 | Project Management | 24 hrs | All members |
| 2.0 | Requirements & System Design | 40 hrs | All members |
| 3.0 | Infrastructure & DevOps | 32 hrs | 冯俊财 / 纪鹏 |
| 4.0 | Backend Development | 160 hrs | 冯俊财 (AI/Agent) + 纪鹏 (API/data) |
| 5.0 | Frontend Development | 96 hrs | 张诗蔻 |
| 6.0 | Platform Adaptation | 16 hrs | 纪鹏 |
| 7.0 | Testing & QA | 40 hrs | 路清怡 |
| 8.0 | Documentation & Submission | 32 hrs | 路清怡 |
| | **Total** | **440 hrs** | |



## 9. Project Budget Summary

| Item | Description | Estimated Cost (CNY) |
| :--- | :--- | :--- |
| Cloud Server | 4 vCPU / 8 GB RAM, rented as needed for deployment| ¥ 100 |
| LLM API Credits | Tongyi Qianwen (qwen-max / qwen-vl-max) | ¥ 300 |
| Object Storage | Aliyun OSS / MinIO for course files | ¥ 50 |
| **Total** | | **¥ 450** |

---

## 10. Quality Issues

**Specific quality requirements:**

| Requirement | Metric | Target |
| :--- | :--- | :--- |
| Q&A accuracy | Core knowledge-point answer correctness | ≥ 95% |
| Grading annotation accuracy | Key error annotation (location + content) correctness on sample assignments | ≥ 95% |
| System availability | Uptime during demo and evaluation period | ≥ 99% |
| API response time | Non-AI endpoint latency | < 2 seconds |
| Concurrency | Simultaneous active users | ≥ 500 |

**Quality assurance approach:**
- All backend pull requests require peer code review before merging.
- Q&A accuracy is measured against a 50-question ground-truth set per course.
- Grading accuracy is measured against the sample assignments provided by the competition (key-error annotations pre-labeled by team members).
- Celery async tasks and Redis caching are used to maintain responsiveness under load.

---

## 11. Resources Required

**People:**
- 4 team members (roles defined in Section 2)

**Technology:**

| Category | Tool / Technology |
| :--- | :--- |
| Frontend | React 18, TypeScript, Vite, Ant Design 5, ECharts, React Flow |
| Backend | FastAPI (Python 3.11), SQLAlchemy 2.0, Alembic, Celery |
| AI / LLM | LangChain 0.3, LangGraph, Tongyi Qianwen (qwen-max, qwen-vl-max), DeepSeek |
| Database | PostgreSQL 16 + pgvector, Redis 7, MinIO |
| DevOps | Docker Compose, Nginx, Aliyun ECS, GitHub Actions |
| Collaboration | GitHub (code), Feishu (communication), VS Code |

**Facilities:**
- Cloud server (Aliyun ECS, provisioned by Week 2)
- Each member's local development machine
- GitHub repository for version control and CI

---

## 12. Assumptions and Risks

**Assumptions:**
1. The team has valid API access to Tongyi Qianwen (qwen-max, qwen-vl-max) throughout the project.
2. Competition rules allow simulated platform adaptation; real Chaoxing/DingTalk API certification is not required.
3. All team members can commit approximately 10 hours per week to the project.

**Key Risks:**

| Risk | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| LLM API latency degrades user experience | Medium | High | SSE streaming output; Redis caching for frequent questions |
| Grading / Q&A accuracy fails to reach 95% | Medium | High | Per-type prompt templates; few-shot examples; iterative calibration with sample data |
| Schedule slippage due to exam season (late May) | Medium | Medium | Front-load core AI features in Weeks 3–7; documentation and video in final 2 weeks |
| Insufficient demo data for convincing showcase | Low | Medium | 路清怡 dedicates time in Weeks 1–4 to prepare 2–3 complete course datasets |
| Chaoxing/DingTalk real integration complexity | Low | Low | Competition rules permit technical-spec-only adaptation; no live integration required |

**Constraints:**
- Fixed end date: June 14, 2026; no extensions possible.
- Budget capped at approximately ¥ 800 (cloud + LLM API costs).
- Team size is fixed at 4 members; no external contractors.

---

## 13. Project Administration

**Communications Plan:**
- Weekly team sync meeting (Sunday evenings, 60 min) to review progress against milestones.
- Daily async updates via group chat (Feishu) for blockers and code review requests.
- GitHub Issues used to track bugs; GitHub Projects board tracks WBS task status.
- All code merged to `main` branch via Pull Requests only.

**Scope Management Plan:**
- Any proposed scope changes must be evaluated for impact on the June 14 deadline before acceptance.
- Core features (Q&A, grading, analytics, exercises) take priority. Creative features (Agent visual builder, platform adapter) are secondary if time is short.
- The Project Manager (冯俊财) has final authority on scope decisions.

**Quality Management Plan:**
- Mandatory peer code review for all pull requests before merging.
- Q&A and grading accuracy tested at each milestone; results recorded and prompt templates revised if targets are missed.
- End-to-end integration test performed in Week 10 covering all 9 UI pages and all 8 API route groups.

---

## 14. Acceptance and Approval

This Project Charter is approved by all team members, confirming the project objectives, scope, schedule, and responsibilities described above.

| Role | Name | Signature | Date |
| :--- | :--- | :--- | :--- |
| Team Leader / Project Manager | 冯俊财 | | March 29, 2026 |
| Team Member | 张诗蔻 | | March 29, 2026 |
| Team Member | 纪鹏 | | March 29, 2026 |
| Team Member | 路清怡 | | March 29, 2026 |

---

## 15. Appendices

### Appendix A — Gantt Chart

> W1 = Mar 30–Apr 5 … W11 = Jun 8–Jun 14 | `█` active | `▒` testing/review

```
Task                                    W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11
                                       3/30 4/6 4/13 4/20 4/27 5/4 5/11 5/18 5/25 6/1 6/8
─────────────────────────────────────────────────────────────────────────────────────────
1.0  Project Management                ████ ████ ████ ████ ████ ████ ████ ████ ████ ████ ████
2.0  Requirements & System Design      ████ ████
3.0  Infrastructure & DevOps           ████ ████                                      ████
4.0  Backend Development                    ████ ████ ████ ████ ████ ████ ████
5.0  Frontend Development                        ████ ████ ████ ████ ████ ████
6.0  Platform Adaptation                                                  ████ ████
7.0  Testing & QA                      ▒▒▒▒ ▒▒▒▒ ▒▒▒▒ ▒▒▒▒ ▒▒▒▒ ▒▒▒▒ ▒▒▒▒ ████ ████ ████
8.0  Documentation & Submission                                                    ████ ████
─────────────────────────────────────────────────────────────────────────────────────────
     MILESTONES:                        M1        M2             M3        M4        M5
                                  Foundation  Q&A MVP      Teaching   Full Feat  Delivery
                                      Apr 12    Apr 26         May 17    May 31    Jun 14
```

