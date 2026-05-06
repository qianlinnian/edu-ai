# EduAI Deck Copy (Concise, Markdown)

> Usage: each `---` block is one slide. RBS/WBS are provided as tables for easy pasting.

---

## 01. Project Overview

### Background & Pain Points
- Siloed course systems → duplicated engineering, inconsistent architectures
- LMS embedding is costly (Chaoxing / DingTalk)
- Weak cross-course reuse and fragmented knowledge presentation
- Grading feedback lacks teacher-style, inline, contextual annotations

### Goal & Value (MOV)
- Build **EduAI**: embeddable, reusable AI Agent platform
- Ship **SDK + Widget** to accelerate new-course rollout
- Provide **Q&A + annotation grading + analytics→exercises** learning loop

---

## 02. Scope & Key Stakeholders

### In Scope
- Agent SDK (QA / Grading / Exercise templates)
- Knowledge middleware (ingestion + hybrid retrieval)
- Teaching engine (Q&A, grading, analytics, exercises)
- Full-stack product (FastAPI APIs + React portal + iframe Widget)
- Platform adapters (spec + simulation) + cloud deployment (demo)

### Out of Scope
- Native mobile apps; live-class streaming
- Real certified LMS integration (simulation only)
- Billing/payment; hardware-lab integrations

### Key Stakeholders
- Project team (4 roles): PM/AI+BE, BE, FE, Test+Docs
- Requirement owner: course instructor(s)
- Users: students; TAs/instructors
- Constraints: competition rules, platform specs, fixed deadline

---

## 03. RBS (Requirement Breakdown) — Table

| Category | Requirement | What it delivers (concise) |
| --- | --- | --- |
| Functional | Unified Agent capability | Reusable agent SDK templates; multi-model/provider access |
| Functional | Knowledge processing & retrieval | PDF/Word/PPT ingestion; embeddings+pgvector; hybrid retrieval + rerank |
| Functional | Teaching interaction & Q&A | Multi-turn chat; course-grounded answers |
| Functional | Grading & annotation | Multi-modal grading; teacher-style inline annotations (structured output) |
| Functional | Analytics & exercises | Mastery/weakness analysis; personalized exercise generation loop |
| Functional | Embedding & management | iframe Widget; LMS adapter spec (Chaoxing/DingTalk); visual builder |

| NFR / Constraints | Target |
| --- | --- |
| Quality | Q&A accuracy ≥ 90%; annotation accuracy ≥ 90% |
| Performance | Concurrency ≥ 500; non-AI latency < 2s |
| Security/Architecture | RBAC; modular reusable architecture |
| Constraints | Tongyi Qianwen as primary LLM; simulated integration only; deadline **2026-06-14** |

---

## 04. WBS (Work Breakdown) — Table

| WBS | Module | Key deliverables (fits slide) |
| --- | --- | --- |
| 1.0 | Project management | Tracking, risk handling, weekly sync |
| 2.0 | Requirements & design | RBS/WBS, architecture, DB schema, API+UI specs |
| 3.0 | Infra & DevOps | Compose services, migrations, Celery/Redis, MinIO, deploy scripts |
| 4.0 | Backend development | Auth+RBAC, Agent SDK, RAG middleware, grading/analytics, 8 API groups |
| 5.0 | Frontend development | Portal pages + shared UI, Widget, builder integration |
| 6.0 | Platform adaptation | Chaoxing/DingTalk embedding specs + simulation |
| 7.0 | Testing & QA | Unit/API tests, accuracy/perf validation, E2E scenarios |
| 8.0 | Docs & submission | Report, demo video, final delivery package |

---

## 05. Responsibility Mapping (Functions / Owners)

### Role-to-Work Mapping
- **Backend A (LLM / Agent / RAG / Grading prompts)**
  - Agent SDK, Q&A pipeline, grading/annotation prompt & workflow design
- **Backend B (Data / Middleware / Tasks / Platform)**
  - knowledge processing, vector store, async workers, platform adapters
- **Frontend C (Portal / Widget / UI)**
  - management portal pages, component system, embeddable widget, agent builder UX
- **Integrated D (Testing / Data / Docs)**
  - test cases + demo data, end-to-end verification, reports & presentation materials

### Collaboration Rules (optional small print)
- PR-based workflow with mandatory peer review
- Weekly milestone sync; daily async updates for blockers and reviews

---

## 06. Schedule (11 Weeks)

| Week (Date) | Stage | Key Deliverables |
| --- | --- | --- |
| Week 1 (2026-03-30 ~ 04-05) | Definition & environment | Docker base services; repo conventions |
| Week 2 (2026-04-06 ~ 04-12) | Foundation ready (M1) | migrations/JWT, LLM connectivity, Celery+Redis, MinIO, pgvector |
| Week 3 (2026-04-13 ~ 04-19) | Knowledge MVP | upload → parse → chunk → embed → retrieve loop |
| Week 4 (2026-04-20 ~ 04-26) | Q&A MVP (M2) | course-aware Q&A; accuracy validation & iteration |
| Week 5 (2026-04-27 ~ 05-03) | Grading pipeline | assignment submission + grading workflow scaffolding |
| Week 6 (2026-05-04 ~ 05-10) | Annotation grading | key-error localization; frontend rendering integration |
| Week 7 (2026-05-11 ~ 05-17) | Teaching loop complete (M3) | analytics + exercise generation closed loop |
| Week 8 (2026-05-18 ~ 05-24) | Full integration | main user journeys end-to-end |
| Week 9 (2026-05-25 ~ 05-31) | Adaptation & builder (M4) | widget embedding; adapter specs; visual builder |
| Week 10 (2026-06-01 ~ 06-07) | Testing & optimization | accuracy/performance validation; UX polish |
| Week 11 (2026-06-08 ~ 06-14) | Deployment & delivery (M5) | cloud demo; final docs; final presentation package |
