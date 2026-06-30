# Data Structure Q&A Evaluation Supplement

Date: 2026-06-29
Scope: live server-side Q&A evaluation evidence for the data-structure course

## Findings First

1. The valid live course for the uploaded data-structure materials is `course_id=3`, not `course_id=2`.
2. The live server database state for `course_id=3` is:
   - `course_resources = 13`
   - `resource_chunks = 1126`
   - `agent_instances = 0`
3. Four grouped Q&A evaluation runs were executed against `course_id=3` using the repository script [evaluate_mcq_checklist.py](/D:/course/SEME/edu-ai/backend/script/evaluate_mcq_checklist.py:1).
4. All four grouped runs achieved full correctness with non-empty retrieval on every question:
   - group A: `10 / 10`, `retrieval_nonempty = 10`
   - group B: `10 / 10`, `retrieval_nonempty = 10`
   - group C: `5 / 5`, `retrieval_nonempty = 5`
   - group D: `20 / 20`, `retrieval_nonempty = 20`
5. Aggregated across the grouped runs, the live server-side Q&A result is `45 / 45 = 1.0` with `45 / 45` retrieval non-empty.

## Evidence Files

- Group A result:
  - [datastructure-eval-group-a-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-a-course3-2026-06-29.json:1)
- Group B result:
  - [datastructure-eval-group-b-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-b-course3-2026-06-29.json:1)
- Group C result:
  - [datastructure-eval-group-c-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-c-course3-2026-06-29.json:1)
- Group D result:
  - [datastructure-eval-group-d-course3-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/datastructure-eval-group-d-course3-2026-06-29.json:1)
- Grouped checklist inputs:
  - [datastructure-checklist-group-a-2026-06-29.yaml](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-checklist-group-a-2026-06-29.yaml:1)
  - [datastructure-checklist-group-b-2026-06-29.yaml](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-checklist-group-b-2026-06-29.yaml:1)
  - [datastructure-checklist-group-c-2026-06-29.yaml](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-checklist-group-c-2026-06-29.yaml:1)
  - [datastructure-checklist-group-d-extended-2026-06-29.yaml](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-checklist-group-d-extended-2026-06-29.yaml:1)

## Environment Clarification

The first live rerun was mistakenly executed on `course_id=2`.
That course currently has:

- `course_resources = 0`
- `resource_chunks = 0`
- `agent_instances = 0`

Its resulting `accuracy = 1.0` / `retrieval_nonempty = 0` artifact was therefore not used as final evidence, because it reflects unguided answer generation rather than course-grounded retrieval.

By contrast, the final cited evidence uses `course_id=3`, which is the actual uploaded `数据结构与算法` course on the server.

## Aggregate Result

| Group | Questions | Correct | Accuracy | Retrieval Non-empty |
| --- | --- | --- | --- | --- |
| A | 10 | 10 | `1.0` | 10 |
| B | 10 | 10 | `1.0` | 10 |
| C | 5 | 5 | `1.0` | 5 |
| D | 20 | 20 | `1.0` | 20 |
| Aggregate | 45 | 45 | `1.0` | 45 |

## Interpretation Boundary

What this supplement does prove:

- the current server-side data-structure course can answer this 45-question grouped MCQ set correctly
- retrieval returned non-empty context for every evaluated question
- the Q&A side of `R7121` is now supported by stronger live evidence than the older local artifact
- the stronger current measured scope is now a 45-question grouped MCQ set rather than only the original 25-question bank

What this supplement does not prove:

- independence from the original 25-question source bank, because the grouped checklists are derived from that same bank
- the grading side of `R7121`
- the `R213` hybrid-retrieval claim

## Safe Current Statement

For the current uploaded `数据结构与算法` course on the live server, the Q&A path now has direct measured evidence of `45 / 45 = 1.0` with non-empty retrieval for all evaluated questions.
