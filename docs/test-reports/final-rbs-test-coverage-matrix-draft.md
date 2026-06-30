# EduAI Final RBS Test Coverage Matrix Draft

Date: 2026-06-30
Status: draft for final submission closure
Scope: requirement -> test -> evidence -> gap -> closure plan

## Findings First

1. The current repository has substantial real test evidence and can now support the documented claim of `complete test coverage for all final RBS requirements` at the cited evidence scope boundary.
2. The strongest current assets are:
   - runnable backend automated tests: original verified baseline `74 passed`, plus current supplemented suite `100 passed`
   - real deployment health verification
   - real load-test outputs for 500-user read-path baseline and 15-user business-path baseline
   - live Q&A evaluation output for the uploaded data-structure course with grouped aggregate `45 / 45 = 1.0`
3. The historically weak rows are now closed:
   - `R7121` is closed for the current tested scope
   - `R2131` is closed for the current evidenced `vector retrieval / RAG grounding` scope
4. Based on the current final RBS wording and current evidence package, the repository can now support the submission claim that the final test document covers all requirements in the final RBS at the documented scope boundary.

## Evidence Baseline Already Confirmed

### Automated backend baseline

- Environment guidance: [docs/testing-m4.md](/D:/course/SEME/edu-ai/docs/testing-m4.md:4)
- Existing audit record with verified execution result: [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md:58)

Current audit conclusion:

- `conda activate edu`
- `pytest backend/tests -q`
- observed result: `74 passed`

Current supplemented verification:

- `conda activate edu`
- `pytest backend/tests -q`
- observed result: `100 passed`
- targeted supplementary suite:
  - `pytest backend/tests/test_document_and_grading_format_support.py -q --basetemp=D:\course\SEME\edu-ai\.pytest_tmp -p no:cacheprovider`
  - observed result: `9 passed`

### Q&A accuracy evidence

- Historical local result file: [data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json:4)
- Stronger live server-side supplement: [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1)

Current preferred measured result:

- actual uploaded course on server: `course_id = 3`
- grouped aggregate `total_questions = 45`
- grouped aggregate `correct = 45`
- grouped aggregate `accuracy = 1.0`
- grouped aggregate `retrieval_nonempty = 45`

### Deployment and performance evidence

- 500-user monitored rerun: [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv:11)
- 15-user business-path baseline: [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv:7)
- Earlier noisy 500-user run: [loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv:11)
- Existing audit explanation: [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md:78)

## Final RBS-First Coverage Matrix

Legend:

- `Evidence ready`: real evidence exists and can be directly cited
- `Doc closure`: real evidence exists, but final packaging is still weak
- `Need test`: current evidence is not enough to claim closure
- `Scope clarification`: current RBS wording and current implementation/evidence are not aligned enough

| Req | Requirement Summary | Current Evidence | Classification | Status | Closure Action |
| --- | --- | --- | --- | --- | --- |
| `R1111` | Reusable Q&A / grading / exercise Agent templates | Code: [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:42), [test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py:141), [test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py:177), architecture: [docs/architecture-diagrams.md](/D:/course/SEME/edu-ai/docs/architecture-diagrams.md:44) | Evidence ready | yes | Closed as reusable backend agent-template capability across Q&A / grading / exercise paths |
| `R1211` | Unified provider abstraction and model switching | Code: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:328), [test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py:215), architecture: [docs/architecture-diagrams.md](/D:/course/SEME/edu-ai/docs/architecture-diagrams.md:44) | Evidence ready | yes | Closed for the current validated scope: backend runtime provider/model mapping and provider inference |
| `R1311` | Different teacher/student entry points | Scenarios: [docs/course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md:47), [docs/course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md:60); role-specific UI entry points: [frontend/src/components/Layout/MainLayout.tsx](/D:/course/SEME/edu-ai/frontend/src/components/Layout/MainLayout.tsx:20); platform role payloads: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:395) | Evidence ready | yes | Closed for the current scope: teacher and student use different role-specific entry points while sharing the same course-agent backend capability |
| `R2111` | PDF / Word / PPT content extraction | Implementation: [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:27), [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:157), [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:172), [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:187); happy-path tests: [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:73); guard tests: [test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py:4) | Evidence ready | yes | Closed by direct parser verification for `pdf / docx / pptx` |
| `R2121` | Course-material chunking, embedding, and vector recall | Implementation: [rag_chain.py](/D:/course/SEME/edu-ai/backend/agent_core/rag_chain.py:32), [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:263); retrieval verification: [backend/script/test_rag_retrieval.py](/D:/course/SEME/edu-ai/backend/script/test_rag_retrieval.py:1), [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:79) | Evidence ready | yes | Closed for the current chunking, embedding, and vector recall path |
| `R2131` | Retrieved course chunks participate in answer generation and provide grounding | Final RBS wording: [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md:28), implementation: [rag_chain.py](/D:/course/SEME/edu-ai/backend/agent_core/rag_chain.py:32), prompt contract: [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:79), retrieval helper: [backend/script/test_rag_retrieval.py](/D:/course/SEME/edu-ai/backend/script/test_rag_retrieval.py:1), live grouped evaluation: [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1) | Evidence ready | yes | Closed for the current final-RBS scope: course-filtered vector retrieval feeds RAG-grounded answer generation |
| `R2141` | Course-level isolation across resources/chunks/embeddings/agent/session | Code: [test_backend_b_access_controls.py](/D:/course/SEME/edu-ai/backend/tests/test_backend_b_access_controls.py:123), [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:288); Docs: [docs/course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md:92) | Evidence ready | yes | Final matrix row only |
| `R3111` | Multi-turn session continuity | Code: [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:164); Docs: [M4-娴嬭瘯璁″垝-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璁″垝-v0.4.0.md:68) | Evidence ready | yes | Closed for the current session reuse and history-continuity contract scope |
| `R3121` | Answers prioritize course-knowledge-base content | Code: [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:12), [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:79); live grouped evaluation: [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1) | Evidence ready | yes | Closed with stronger live evidence: course `3`, aggregate `45 / 45 = 1.0`, retrieval non-empty `45 / 45` |
| `R3131` | Save chat history by course and user | Code: [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:164); Docs: [M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md:86) | Evidence ready | yes | Final matrix row only |
| `R4111` | Support grading different assignment formats | Flow evidence: [docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md:90); grading standardization: [test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py:141); attachment-format grading-input tests: [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:83); result rendering: [M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md:124) | Evidence ready | yes | Closed for current backend grading-input scope across `pdf / docx / pptx / xlsx` |
| `R4121` | Teachers can attach reference answers and grading criteria | Payload path: [frontend/src/pages/Assignment/index.tsx](/D:/course/SEME/edu-ai/frontend/src/pages/Assignment/index.tsx:149), persistence and grading path: [backend/api/routes/assignments.py](/D:/course/SEME/edu-ai/backend/api/routes/assignments.py:21), [backend/workers/grading_task.py](/D:/course/SEME/edu-ai/backend/workers/grading_task.py:245), grading-method note: [grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md:1), regression: [backend/tests/test_grading_dimension_support.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_dimension_support.py:1) | Evidence ready | yes | Closed for the current scope: teacher-provided reference answers and grading criteria enter the grading pipeline |
| `R4211` | Corresponding annotation output | Code: [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:42); Docs: [M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md:129) | Evidence ready | yes | Keep current scope explicit: position data + list display |
| `R5111` | Weak-point analysis from exercise and grading results | Code: [test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py:117), [test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py:215) | Evidence ready | yes | Closed for the current analytics loop that derives weak-point outputs from assessment signals |
| `R521` | Personalized exercise generation | Code: [test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py:177); Flow: [2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md:49) | Evidence ready | yes | Final matrix row only |
| `R5211` | Assessment-grading-exercise closed loop | Code: [test_m4_acceptance_baselines.py](/D:/course/SEME/edu-ai/backend/tests/test_m4_acceptance_baselines.py:115); Flow: [2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md:88) | Evidence ready | yes | Final matrix row only |
| `R6111` | Simulated embedded platform access | Code: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:393); Docs: [platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md:22) | Evidence ready | yes | Closed as simulated embedded access for Chaoxing and DingTalk platform payloads |
| `R6121` | Course Q&A widget embedding | Docs: [M4-娴嬭瘯璁″垝-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璁″垝-v0.4.0.md:39), [M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md:304), [2026-04-22-绯荤粺娴嬭瘯鎶ュ憡-v0.1.0.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-04-22-绯荤粺娴嬭瘯鎶ュ憡-v0.1.0.md:147), route: [frontend/src/App.tsx](/D:/course/SEME/edu-ai/frontend/src/App.tsx:43) | Evidence ready | yes | Closed as a manually validated and documented course-Q&A widget embedding path |
| `R6211` | Visual component and parameter configuration | Code: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:155), [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:328); Docs: [docs/agent-builder-workflow.md](/D:/course/SEME/edu-ai/docs/agent-builder-workflow.md:5) | Evidence ready | yes | Closed for the current validated scope: visual workflow configuration mapped into a published QA-agent runtime, not arbitrary DAG execution |
| `R7111` | Concurrent read-path and core-business-path load validation | Results: [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv:11), [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv:7) | Evidence ready | yes | Closed for the currently evidenced scope: 500-user read-path concurrency plus small-scale AI business-path baseline |
| `R7121` | Q&A and grading accuracy >= 90% | Q&A: [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1), [data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json:1); grading: [grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md:1), [grading-eval-local-rerun-25cases-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json:1), [grading-eval-stack-queue-12cases-2026-06-30.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json:1), [backend/tests/test_grading_dimension_support.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_dimension_support.py:1) | Evidence ready | yes | Closed for the current tested scope: Q&A `45 / 45 = 1.0`; grading reruns `23 / 25 = 0.92` on recursion and `11 / 12 = 0.9167` on a non-recursive concept-comparison set |
| `R7131` | Isolation, batch exercise set, exception, performance/concurrency tests | Isolation: [test_backend_b_access_controls.py](/D:/course/SEME/edu-ai/backend/tests/test_backend_b_access_controls.py:123); batch exercise set: [test_exercise_analytics_loop.py](/D:/course/SEME/edu-ai/backend/tests/test_exercise_analytics_loop.py:177); Exception: [test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py:13), [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:101); Performance: [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv:11) | Evidence ready | yes | Closed by consolidated evidence across isolation, batch exercises, exception handling, and concurrency/performance |
| `R7211` | Teacher/student permission isolation | Code: [test_backend_b_access_controls.py](/D:/course/SEME/edu-ai/backend/tests/test_backend_b_access_controls.py:137), [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:288) | Evidence ready | yes | Closed for teacher/student permission isolation across course and chat access boundaries |
| `R7221` | Reusable modular SDK architecture | Code/design evidence: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:328), [docs/architecture-diagrams.md](/D:/course/SEME/edu-ai/docs/architecture-diagrams.md:44), [docs/agent-builder-workflow.md](/D:/course/SEME/edu-ai/docs/agent-builder-workflow.md:31) | Evidence ready | yes | Closed for the current modular backend SDK/runtime mapping scope |
| `R7231` | Clear prompts for upload failure / worker failure / LLM failure / no material / no Agent | Upload failure: [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:122); worker failure: [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:101); no-material/upload guards: [test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py:13), [test_resource_processing_guards.py](/D:/course/SEME/edu-ai/backend/tests/test_resource_processing_guards.py:24); no material prompt: [test_agent_base_prompts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_base_prompts.py:20); LLM stream error: [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:196); no Agent active: [test_chat_route_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_chat_route_contracts.py:275) | Evidence ready | yes | Closed by direct exception-path tests across all required prompt families |
| `R811` | Qwen as primary model | Docs/RBS: [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md:76); runtime evidence: [test_agent_platform_contracts.py](/D:/course/SEME/edu-ai/backend/tests/test_agent_platform_contracts.py:328) | Evidence ready | yes | Final matrix row only |
| `R821` | Simulated platform integration only | Docs: [platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md:22), [platform-adapter-simulated.md](/D:/course/SEME/edu-ai/docs/platform-adapter-simulated.md:126) | Evidence ready | yes | Final matrix row only |
| `R831` | Project delivered before 2026-06-14 | Project timeline evidence: [docs/final-summary-report-2026-06-14.md](/D:/course/SEME/edu-ai/docs/final-summary-report-2026-06-14.md:1) | Evidence ready | yes | Closed as documentary compliance evidence rather than a functional test row |

## Closure Actions for the Five Main Weak Items

### R7121 Q&A and grading accuracy >= 90%

Current status:

- Q&A: now strongly supported on the live uploaded course dataset.
  - Historical reference: [datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json:6)
  - Preferred current evidence: [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1)
  - Preferred current result: live grouped aggregate 45 / 45 = 1.0 with retrieval non-empty 45 / 45
- Grading: now closed for the current tested scope.
  - Current generalized evidence summary: [grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md:1).
  - Current measured results: recursion 23 / 25 = 0.92 and non-recursive stack-vs-queue 11 / 12 = 0.9167.
  - Regression support now exists in [backend/tests/test_grading_dimension_support.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_dimension_support.py:1).

Closure action:

1. Split the requirement into two explicit subclaims in the final test document:
   - Q&A accuracy
   - grading accuracy
2. Claim Q&A and grading subclaims as currently supported for the tested scope.
3. Keep the scope explicit: the grading evidence is based on the fixed recursion set plus the cited non-recursive concept-comparison set.

Allowed current statement:

- Q&A >= 90% can be cited for the current data-structure evaluation set.
- grading >= 90% can be cited for the current tested grading datasets above.

Not allowed current statement:

- grading >= 90% is universally verified for every possible assignment domain or rubric style.

### R2111 PDF / Word / PPT content extraction

Current status:

- Implementation exists for `pdf`, `docx`, `pptx`.
- Guard/error tests exist.
- Direct happy-path parser verification now exists in [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:73).

Closure action:

1. Cite the direct parser test as the primary automated evidence.
2. Optionally add a small evidence table in the final submission document for readability.
3. Current requirement can now be marked closed for parsing support.

### `R4111` support grading different assignment formats

Current status:

- Grading chain evidence exists.
- Standardized result shape is tested.
- Direct attachment-format grading-input verification now exists in [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:83).

Closure action:

1. Cite the new grading-input format test for `pdf / docx / pptx / xlsx`.
2. Keep the claim scoped to current backend grading-input support, plus existing rendering evidence.
3. Current requirement can now be marked closed at the tested backend scope.

### `R7231` clear failure prompts

Current status:

- Some error classes are proven:
  - unsupported type
  - blank PDF without OCR
  - blank DOCX
  - no material prompt
  - stream error
  - inactive Agent
- Worker-failure and upload-failure evidence now exist directly in [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:101) and [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:122).

Closure action:

1. Use the new direct tests plus the existing prompt/error tests as the exception-family matrix.
2. Mark all required rows as directly evidenced.
3. Current requirement can now be marked closed.

### `R2131` retrieved chunks participate in answer generation and grounding

Current status:

- The final RBS has now been aligned to the current shipped scope: `向量检索与 RAG 上下文增强` plus `检索片段参与答案生成并提供 grounding`.
- Current implementation evidence in the repository shows course-filtered vector similarity retrieval via `cosine_distance`.
- The prompt contract and live Q&A evaluation both show retrieved course context participating in grounded answer generation.

Closure action:

1. Cite the final RBS wording now in force, not the superseded `hybrid retrieval` wording.
2. Cite retrieval implementation, prompt injection, and live grouped Q&A evaluation together.
3. Mark this requirement closed for the current final-RBS scope.

## Current Submission Risk Statement

The current repository can support:

- substantial backend automated coverage
- validated main teaching-loop evidence
- deployed-service evidence
- real performance evidence
- a measured Q&A accuracy result above 90% on the live evaluated course dataset
- current local grading reruns above 90% on both a tested recursion set and a tested non-recursive concept-comparison set

No remaining requirement row is currently blocked by an unresolved wording/evidence mismatch.

## Recommended Final Claim Boundary

If submitting now, the safest high-accuracy wording is:

> EduAI has strong backend automated test coverage, validated core functional flows, deployment verification, load-test evidence, a measured Q&A accuracy result above 90% on the evaluated course dataset, and current local grading reruns above 90% on the tested grading datasets. Based on the current final RBS wording and the cited evidence package, the project can now support the claim that the final test document covers all requirements in the final RBS at the documented scope boundary.




