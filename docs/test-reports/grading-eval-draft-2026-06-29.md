# EduAI Grading Evaluation Draft

Date: 2026-06-29
Status: limited-scope draft evidence for `R7121` grading side

## Findings First

1. A real grading evaluation draft now exists.
2. The draft used the deployed server's real LLM configuration and invoked the actual `_grade_with_llm` path.
3. The current draft result is `3 / 3 = 1.0` on a score-band-match metric.
4. This draft improves the evidence base for `R7121`, but it is still too small and too manually constructed to close the full `grading accuracy >= 90%` requirement by itself.

## Execution Context

- Server runtime:
  - `/home/eduai/miniconda3/envs/edu/bin/python`
- Working directory:
  - `/home/eduai/edu-ai/backend`
- Code path:
  - [grading_task.py](/D:/course/SEME/edu-ai/backend/workers/grading_task.py:272)

## Evaluation Design

### Metric

- `score_band_match_accuracy`

### Cases

- `grading_eval_bad_recursion`
  - expected band: `0-40`
- `grading_eval_mid_recursion`
  - expected band: `60-80`
- `grading_eval_good_recursion`
  - expected band: `85-100`

The cases are rubric-aligned recursion explanations designed to test whether the current grading path can distinguish:

- clearly incorrect answers
- partially correct answers
- strong answers

## Result Artifact

- [grading-eval-draft-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-draft-2026-06-29.json:1)

Observed result:

- `total_cases = 3`
- `passed_cases = 3`
- `accuracy = 1.0`

## Interpretation

What this draft now proves:

- The real deployed grading path can be executed against a small controlled evaluation set.
- The current grading model distinguished low/mid/high quality recursion answers correctly on this draft set.

What this draft still does not prove:

- It does not yet prove final-RBS-level `grading accuracy >= 90%` across a sufficiently broad course-project evaluation set.
- It does not yet provide enough case volume or course diversity to close `R7121` on its own.

## Current Use in the Final Closure Package

This artifact should be cited as:

- a new measured grading-evaluation draft
- stronger than pure grading samples
- still insufficient for a full `R7121` closure claim
