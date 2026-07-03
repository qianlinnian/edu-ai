# EduAI Grading Generalization Supplement

Date: 2026-06-30
Status: supplementary evidence for `R7121` grading scope

## Purpose

This note records the post-refactor grading evidence after removing the recursion-specific scoring floor from the main grading path.

Current grading path focus:

- structured rubric and dimension-first scoring
- course-material grounding passed into grading
- generic text-answer fairness recheck for boundary-score cases

It no longer relies on a recursion-only scoring floor in the primary grading flow.

## Current Grading Method

The current grading method is not a pure rule engine and not a simple exact-match checker.
It is an LLM-based grading flow with structured scoring constraints and course-material grounding.

Current scoring flow:

1. Build the grading input from:
   - assignment title and description
   - assignment type
   - rubric
   - reference answer
   - student submission
2. Retrieve relevant course material chunks and pass them in as `course_material_context`.
3. Ask the grading agent to score dimension by dimension first, then sum the dimension scores into the final score.
4. For boundary-score text answers, trigger one extra review pass to reduce under-scoring or over-scoring on concise answers.

This means the grading method is best described as:

- `dimension-first grading`
- `rubric-constrained grading`
- `reference-answer-aware grading`
- `RAG-grounded grading`
- `boundary-case review pass`

## How Reference Answer and Rubric Are Used

The grading agent explicitly receives both:

- `reference_answer`
- `rubric`

Therefore the current grading path is designed to consider teacher-provided answer expectations and teacher-provided scoring criteria.

Safe interpretation:

- if the rubric says certain required points must appear, the grader is expected to score against those points
- if the reference answer clearly states the expected answer structure, the grader is expected to use it as the high-score standard
- if a student answer is highly aligned with the reference answer and satisfies the rubric dimensions, the grader should assign a very high score

Important boundary:

- the current system does **not** implement a hard deterministic rule saying "string exactly matches the reference answer, therefore full marks must be assigned"
- instead, the LLM uses the reference answer and rubric as grading evidence and constraints

So the current behavior is:

- exact or near-exact alignment with the teacher reference answer will usually lead to a very high score
- but a strict "exact match always equals 100" guarantee is not currently hard-coded as a deterministic scoring rule

## Code Changes Relevant to This Evidence

- grading prompt and review-aware payload:
  - `backend/agent_core/agent_base.py`
- grading worker grounding and generic review path:
  - `backend/workers/grading_task.py`
- reusable evaluation script with YAML assignment config:
  - `backend/script/evaluate_grading_draft.py`

## Current Automated Regression Baseline

Command:

```powershell
conda activate edu
pytest backend/tests -q
```

Observed result:

- `100 passed`

## Current Grading Evaluation Results

### 1. Recursion explanation set

- Case file:
  - `data/test/grading-eval-cases-recursion-25cases-2026-06-29.yaml`
- Result file:
  - `docs/test-reports/grading-eval-local-rerun-25cases-2026-06-29.json`

Observed result:

- `23 / 25 = 0.92`

Interpretation:

- The post-refactor generic path still keeps the recursion set above the `>= 90%` threshold.
- Two good-band cases remain conservative at `85`, so this is no longer the earlier `25 / 25` result from the recursion-specific floor path.

### 2. Non-recursive stack-vs-queue concept-comparison set

- Case file:
  - `data/test/grading-eval-cases-stack-queue-12cases-2026-06-30.yaml`
- Result file:
  - `docs/test-reports/grading-eval-stack-queue-12cases-2026-06-30.json`

Observed result:

- `11 / 12 = 0.9167`

Interpretation:

- This gives direct non-recursive evidence for concept-comparison grading.
- The remaining miss is a good-band answer scored at `83`, just below its expected minimum `84`.

## Safe Current Statement

For the current tested scope, EduAI grading now has:

- one recursion text-explanation set above `90%`
- one non-recursive concept-comparison text set above `90%`
- a green backend regression baseline of `100 passed`

## Unsafe Current Statement

This evidence still does **not** prove universal grading fairness for every course, every assignment type, or every rubric style.
