# EduAI Remaining Gap Evidence Note

Date: 2026-06-29
Scope: focused evidence note for the two still-open final RBS requirements

## Findings First

1. `R7121` is still open on the grading side.
   - The Q&A side is now strengthened by live server-side evidence for the actual uploaded data-structure course.
   - The repository contains real grading samples and grading-chain tests.
   - A larger measured grading artifact now exists, and it directly contradicts a `>= 90%` grading-accuracy claim for the current tested scope.
2. `R213` is still open as originally worded.
   - The repository clearly proves course-filtered vector retrieval and RAG grounding.
   - The repository does **not** clearly prove a tested `hybrid retrieval` implementation.

## `R7121` Grading Accuracy Search

### Q&A-side closure strengthening

The Q&A side now has stronger live evidence than the earlier local artifact:

- live server-side grouped evaluation summary:
  - [datastructure-qna-eval-supplement-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-qna-eval-supplement-2026-06-29.md:1)
- direct grouped result files:
  - [datastructure-eval-group-a-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-a-course3-2026-06-29.json:1)
  - [datastructure-eval-group-b-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-b-course3-2026-06-29.json:1)
  - [datastructure-eval-group-c-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-c-course3-2026-06-29.json:1)
  - [datastructure-eval-group-d-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-d-course3-2026-06-29.json:1)

Observed live result:

- actual uploaded course on server: `course_id = 3`
- grouped aggregate: `45 / 45 = 1.0`
- grouped aggregate retrieval coverage: `45 / 45`

Interpretation:

- the Q&A side of `R7121` is now supportable with live retrieval-grounded evidence
- the remaining blocker inside `R7121` is grading, not Q&A

### Search targets

The repository was searched for grading-accuracy evidence using terms including:

- `grading accuracy`
- `eval`
- `score`
- `ground truth`
- `manual score`
- `rubric`
- `90%`

### Directly found grading evidence

- Real/sample grading output document:
  - [docs/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/docs/M3-A-grading-samples.md:1)
- Test-side grading sample document:
  - [data/test/M3-A-grading-samples.md](/D:/course/SEME/edu-ai/data/test/M3-A-grading-samples.md:1)
- Grading payload/shape tests:
  - [test_grading_payload_standardization.py](/D:/course/SEME/edu-ai/backend/tests/test_grading_payload_standardization.py:1)
- Grading worker chain:
  - [grading_task.py](/D:/course/SEME/edu-ai/backend/workers/grading_task.py:61)
- Preliminary 3-case draft:
  - [grading-eval-draft-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-draft-2026-06-29.md:1)
  - [grading-eval-draft-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-draft-2026-06-29.json:1)
- Expanded 9-case measured result:
  - [grading-eval-expanded-2026-06-29.md](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-expanded-2026-06-29.md:1)
  - [grading-eval-expanded-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-expanded-2026-06-29.json:1)

### What these artifacts do prove

- The grading chain exists.
- The grading output shape is standardized.
- Real or sample grading outputs were recorded for specific submissions.
- Attachment parsing can feed grading input.
- A real LLM-backed grading evaluation can be executed on the server runtime.
- The expanded measured artifact reports `6 / 9 = 0.6667` on a score-band-match metric.

### What these artifacts do not prove

- The current measured set is still limited in scope and course diversity.
- Even within this limited scope, the measured result does not support a final `grading accuracy >= 90%` claim.

### `R7121` grading conclusion

- Current status: `open`
- Safe statement:
  - the repository proves grading functionality, grading-output standardization, and measured grading-evaluation artifacts
- Unsafe statement:
  - the repository proves `grading accuracy >= 90%`

## `R213` Retrieval Scope Search

### Directly found retrieval evidence

- Final RBS wording:
  - [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md:26)
- Retrieval implementation:
  - [rag_chain.py](/D:/course/SEME/edu-ai/backend/agent_core/rag_chain.py:1)
- Retrieval verification helper:
  - [test_rag_retrieval.py](/D:/course/SEME/edu-ai/backend/script/test_rag_retrieval.py:1)
- Design wording that repeatedly describes RAG retrieval:
  - [course-agent-scenarios.md](/D:/course/SEME/edu-ai/docs/course-agent-scenarios.md:15)
  - [milestone-review-meeting-summary.md](/D:/course/SEME/edu-ai/docs/milestone-review-meeting-summary.md:41)

### What the implementation proves

- Retrieval is filtered by `course_id`
- Retrieval uses vector similarity ordering via `cosine_distance`
- The shipped Q&A path is RAG-grounded

### What was not found

- No clear lexical/BM25/full-text retrieval path paired with vector retrieval
- No hybrid-ranking implementation
- No hybrid-retrieval tests
- No document that narrows `R213` to the current vector-only implementation

### `R213` conclusion

- Current status: `open`
- Scope clarification is complete:
  - current validated capability is `vector retrieval / RAG grounding`
- Unsafe statement:
  - the repository proves the final-RBS `hybrid retrieval` requirement as written

## Submission Impact

As long as both statements below remain true, the project should **not** claim complete final-RBS test coverage:

1. The current measured grading artifact for `R7121` does not support a `>= 90%` claim for the current tested scope
2. No real hybrid-retrieval proof exists for `R213`
