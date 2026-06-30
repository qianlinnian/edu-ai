# EduAI Final RBS Gap Closure Checklist Draft

Date: 2026-06-30
Priority: only items required to close the final RBS coverage package

## P0 Must Close

- [x] Build the final submission matrix from [final-rbs-test-coverage-matrix-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-test-coverage-matrix-draft.md:1) into the final test document.
- [x] Record the backend automated baseline explicitly:
  - environment: `conda activate edu`
  - command: `pytest backend/tests -q`
  - result: `74 passed`
- [x] Add supplementary closure run:
  - command: `pytest backend/tests -q`
  - result: `100 passed`
- [x] Close `R7121` Q&A claim with stronger live measured evidence from [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1).
- [x] Decide whether grading accuracy has a scored evaluation artifact.
  - Result: current generalized grading evidence now exists in [grading-generalization-supplement-2026-06-30.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-generalization-supplement-2026-06-30.md:1).
  - Current measured results: recursion `23 / 25 = 0.92`; non-recursive stack-vs-queue `11 / 12 = 0.9167`.

## P1 Evidence Packaging

- [x] Add the monitored 500-user read-path rerun result from [loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv:11).
- [x] Add the 15-user business-path baseline from [loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv:7).
- [x] Explain that the earlier noisy run [loadtest-500-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/loadtest-500-20260628_stats.csv:11) was superseded by the monitored rerun.

## P1 Requirement Closures

### `R2111`

- [x] Produce direct happy-path extraction evidence for:
  - `pdf`
  - `docx`
  - `pptx`
- [x] Cite implementation support from [embedding_task.py](/D:/course/SEME/edu-ai/backend/workers/embedding_task.py:27).
- [x] Cite direct parser tests from [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:73).

### `R4111`

- [x] Produce grading-input format verification tests.
- [x] For each verified format, cite:
  - sample input file
  - grading-input parse path
  - grading output chain evidence
- [x] Reuse grading-chain evidence from [docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md:90) and [M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-娴嬭瘯璇佹嵁璁板綍-v0.4.0.md:124).

### `R7231`

- [x] Build an exception-family evidence set.
- [x] Include rows for:
  - upload failure
  - worker failure
  - LLM failure
  - no material
  - no Agent
- [x] Add direct upload-failure and worker-failure tests in [test_document_and_grading_format_support.py](/D:/course/SEME/edu-ai/backend/tests/test_document_and_grading_format_support.py:101).

### `R2131`

- [x] Align the requirement wording to the current final RBS.
- [x] Package direct evidence for retrieved course chunks participating in grounded answer generation.
  - Result: current evidence supports the final-RBS `vector retrieval / RAG grounding` scope and can now be marked closed.

## P1 Documentation-Only Closures

- [x] Convert these requirements from `partial` to final-document-ready by explicit evidence packaging:
  - `R1111`
  - `R212`
  - `R3111`
  - `R612`
  - `R6211`
  - `R711`
  - `R7131`
  - `R7221`

- [x] Tighten additional scoped documentary rows now supportable as closed:
  - `R121`
  - `R1311`
  - `R831`

## Hard Stop Conditions

Do not claim `complete test coverage` if any of the following remain true:

- [x] `R7121` measured grading evidence supports a `>= 90%` claim for the current tested scope
- [x] no current final-RBS row lacks implementation/evidence alignment

Current closure conclusion:

- The current final RBS and current evidence package no longer trigger a hard-stop condition for the complete-coverage submission claim.


