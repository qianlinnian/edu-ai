# Project Charter

Source: `docs/Project Charter.pdf`

> Note: This Markdown version is generated from PDF text extraction. Section structure and core content are preserved, but complex tables / diagrams are simplified.

Project Charter
Embeddable Cross-Course AI Agent General Architecture Platform
## 1. Project Identification
### Field Details
Project Name Embeddable Cross-Course AI Agent General Architecture Platform
Date of Authorization April 12, 2026
Project Start Date March 30, 2026
Project End Date June 14, 2026
Version 1.1
## 2. Project Stakeholders
### Stakeholders

| Name | Title / Role | Student ID | E-mail |
| --- | --- | --- | --- |
冯俊财 AI Architect / Backend 2353924 20614667@qq.com
路清怡 Backend 2352996 849014041@qq.com
张诗蔻 Frontend 2353240 2987991635@qq.com
纪鹏 Test / Frontend 2351869 jp3274313334@163.com
## 3. Project Description
Background:
The current education sector faces the phenomenon of "fragmented intelligent teaching."
Specifically, various courses develop independent intelligent teaching systems, leading to
architectural heterogeneity and duplicate construction due to the lack of technical
standardization. These systems are difficult to seamlessly embed into mainstream teaching
platforms like Chaoxing and DingTalk, causing integration difficulties. Furthermore, course-specific knowledge is hard to transfer effectively, resulting in fragmented knowledge

presentation. Existing systems also provide rough teaching guidance, lack refined analysis and
contextual annotation for assignment details.
Description of the challenge or opportunity:
There is a pressing need for a standardized, reusable AI Agent architecture that enables different
courses to rapidly build and deploy intelligent teaching assistants without redundant
engineering effort. Large Language Model (LLM) technology now makes it feasible to provide
annotated, context-aware feedback at scale—transforming AI grading from "usable" to
"precisely useful."
Overview of the desired impact:
This project delivers EduAI, a general-purpose AI Agent platform that: (1) provides a
standardized SDK for rapid course-Agent development; (2) enables seamless embedding into
Chaoxing and DingTalk via a lightweight iframe Widget; (3) performs annotation-style
assignment grading with ≥ 90% accuracy; (4) analyzes student learning states and generates
targeted exercises to close individual knowledge gaps.
## 4. Measurable Organizational Value
Primary MOV: Enable universities to reduce the cost and time of building intelligent teaching
systems for new courses, while delivering grading feedback quality that matches or exceeds
manual teacher annotation.
### MOV Table

| Area | Goal | Metric | Target Value |
| --- | --- | --- | --- |
Quality Deliver accurate in-course
Q&A Answer accuracy on core
knowledge points ≥ 90%
Quality Deliver teacher-level
grading feedback Key error annotation accuracy
(location + content) ≥ 90%
Cost Reduce duplicate AI
system development
effort Reuse one SDK for ≥ 2 course
types without code changes Demonstrated in demo
Performance Support large-scale
concurrent access Concurrent users supported ≥ 500
Adoption Enable embedding in
mainstream LMS
platforms Platforms supported via
iframe/Widget ≥ 2 (Chaoxing,
DingTalk)
## 5. Project Scope
What is included in the scope of this project:

1.Unified AI Agent SDK (AgentBase,QAAgent,GradingAgent, ExerciseAgent) supporting multiple
course types
2.Knowledge middleware: document ingestion (PDF/Word/PPT), vector embedding (pgvector),
knowledge graph, hybrid retrieval (vector + BM25 + Rerank)
3.Refined intelligent engine: annotation-style grading (text, code, image), learning analytics
(mastery matrix, early warning), personalized exercise generation
4.RESTful API backend (FastAPI, 8 route groups: Auth, Courses, Agents, Assignments, Chat,
Analytics, Exercises, Platform)
5.Full frontend management portal (React 18, 9 pages): Login, Dashboard, Course
Management, Intelligent Q&A, Assignment Management, Grading Result Viewer, Analytics
Dashboard, Exercise Center, Agent Visual Builder
6.Embeddable Widget (iframe-compatible lightweight chat/grading window for LMS
integration)
7.Platform adaptation layer: technical specification and simulated interfaces for Chaoxing (LTI)
and DingTalk (H5)
8.Cloud deployment: Docker Compose + Nginx + HTTPS on a cloud server
What is outside the scope of this project:
1.Native mobile application (iOS/Android)
2.Real-time live-class features (video streaming, screen sharing)
3.Full production API certification and live integration with Chaoxing or DingTalk (simulated
adaptation only, as permitted by competition rules)
4.Automated billing or payment systems
5.Support for physical lab equipment or hardware-linked experiments
## 6. Project Schedule Summary
•Project start date: March 30, 2026
•Project end date: June 14, 2026
•Duration: 11 weeks
### Key Milestones

| Milestone | Description | Target Date |
| --- | --- | --- |
Milestone Description Target Date
- M1 Foundation Ready: environment running; LLM API connected; database
schema migrated; JWT auth verified; Celery/Redis and MinIO validated April 12, 2026

| M2 | Q&A MVP: course material upload, resource processing, and course-aware AI Q&A available (accuracy ≥ 90%) | April 26, 2026 |
- M3 Full teaching loop: submit assignment → AI annotates → learning
analytics → exercises generated May 17, 2026
- M4 Full feature integration: platform embedding and Agent visual builder
completed; Q&A ≥ 90%; grading ≥ 90% May 31, 2026
- M5 System fully deployed on cloud server; end-to-end demo validated;
project documentation complete June 14, 2026
## 7. Requirement Breakdown Structure (RBS)
## 8. Work Breakdown Structure (WBS) & Hours Estimation
WBS diagrams are referenced in the source PDF and are not reproduced here.

## 9. Project Budget Summary
### Project Budget Summary

| Item | Description | Estimated Cost (CNY) |
| --- | --- | --- |
| Cloud Server | 4 vCPU / 8 GB RAM, rented as needed for deployment | ? 200 |
| LLM API Credits | Tongyi Qianwen (qwen-max / qwen-vl-max) | ? 300 |
| Object Storage | Aliyun OSS / MinIO for course files | ? 200 |

Total ¥ 700
## 10. Quality Issues
Specific quality requirements:
### Specific quality requirements

| Requirement | Metric | Target |
| --- | --- | --- |
| Q&A accuracy | Core knowledge-point answer correctness | ? 90% |
Grading
annotation
accuracy Key error annotation (location + content) correctness on sample
assignments ≥ 90%
| System availability | Uptime during demo and evaluation period | ? 99% |
| API response time | Non-AI endpoint latency | < 2 seconds |
| Concurrency | Simultaneous active users | ? 500 |
Quality assurance approach:
1.All backend pull requests require peer code review before merging.
2.Q&A accuracy is measured against a 50-question ground-truth set per course.
3.Grading accuracy is measured against the sample assignments provided by the competition
(key-error annotations pre-labeled by team members).
4.Celery async tasks and Redis caching are used to maintain responsiveness under load.
## 11. Resources Required
People:
4 team members (roles defined in Section 2)
Technology:
### Technology

| Category | Tool / Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Ant Design 5, ECharts, React Flow |
| Backend | FastAPI (Python 3.11), SQLAlchemy 2.0, Alembic, Celery |
| AI / LLM | LangChain 0.3, LangGraph, Tongyi Qianwen (qwen-max, qwen-vl-max), DeepSeek |
| Database | PostgreSQL 16 + pgvector, Redis 7, MinIO |

| DevOps | Docker Compose, Nginx, Aliyun ECS, GitHub Actions |
| Collaboration | GitHub (code), Feishu (communication), VS Code |
Facilities:
1.Cloud server (Aliyun ECS, provisioned by Week 2)
2.Each member's local development machine
3.GitHub repository for version control and CI
## 12. Assumptions and Risks
Assumptions:
1.The team has valid API access to Tongyi Qianwen (qwen-max, qwen-vl-max) throughout the
project.
2.Competition rules allow simulated platform adaptation; real Chaoxing/DingTalk API
certification is not required.
3.All team members can commit approximately 10 hours per week to the project.
Key Risks:
Risk Probability Impact Mitigation Strategy
LLM API latency degrades
user experience Medium High SSE streaming output; Redis caching for frequent
questions
Grading / Q&A accuracy
fails to reach 90% Medium High Per-type prompt templates; few-shot examples;
iterative calibration with sample data
Schedule slippage due to
exam season (late May) Medium Medium Front-load core AI features in Weeks 3‒7;
documentation and video in final 2 weeks
Insufficient demo data for
convincing showcase Low Medium Team member dedicates time in Weeks 1‒4 to
prepare 2‒3 complete course datasets
Chaoxing/DingTalk real
integration complexity Low Low Competition rules permit technical-spec-only
adaptation; no live integration required
Constraints:
1.Fixed end date: June 14, 2026; no extensions possible.

2.Budget capped at approximately ¥ 800 (cloud + LLM API costs).
3.Team size is fixed at 4 members; no external contractors.
## 13. Project Administration
Communications Plan:
1.Weekly team sync meeting to review progress against milestones.
2.Daily async updates via group chat (Feishu) for blockers and code review requests.
3.GitHub Issues used to track bugs; GitHub Projects board tracks WBS task status.
4.All code merged to the main branch via Pull Requests only.
Scope Management Plan:
1.Any proposed scope changes must be evaluated for impact on the June 14 deadline before
acceptance.
2.Core features (Q&A, grading, analytics, exercises) take priority. Creative features (Agent visual
builder, platform adapter) are secondary if time is short.
3.The Project Manager has final authority on scope decisions.
Quality Management Plan:
1.Mandatory peer code review for all pull requests before merging.
2.Q&A and grading accuracy tested at each milestone; results recorded and prompt templates
revised if targets are missed.
3.End-to-end integration test performed in Week 10 covering all 9 UI pages and all 8 API route
groups.
## 14. Acceptance and Approval
This Project Charter is approved by all team members, confirming the project objectives, scope,
schedule, and responsibilities described above.
### Acceptance and Approval

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
Team Leader 冯俊财
April 12, 2026
Team Member 张诗蔻
April 12, 2026
Team Member 纪鹏 April 12, 2026

Team Member 路清怡
April 12, 2026
## 15. Appendices
Appendix A — Gantt Chart