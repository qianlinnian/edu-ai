# EduAI Grading Evaluation Expanded Result

Date: 2026-06-29
Status: primary measured grading evidence for current `R7121` audit

## Findings First

1. The expanded real-LLM grading evaluation does **not** support the claim `grading accuracy >= 90%`.
2. The current measured result is:
   - `total_cases = 9`
   - `passed_cases = 6`
   - `accuracy = 0.6667`
3. This is stronger evidence than the earlier 3-case draft because it uses:
   - a larger fixed case set
   - a reproducible evaluation script
   - the deployed server's real LLM environment

## Reproducible Assets

- Evaluation script:
  - [evaluate_grading_draft.py](/D:/course/SEME/edu-ai/backend/script/evaluate_grading_draft.py:1)
- Fixed case set:
  - [grading-eval-cases-recursion-2026-06-29.yaml](/D:/course/SEME/edu-ai/data/test/grading-eval-cases-recursion-2026-06-29.yaml:1)
- Measured result artifact:
  - [grading-eval-expanded-2026-06-29.json](/D:/course/SEME/edu-ai/docs/test-reports/grading-eval-expanded-2026-06-29.json:1)

## Metric

- `score_band_match_accuracy`

Interpretation:

- Each case defines an expected score band for a bad / mid / good recursion explanation.
- A case passes only when the real grading output score falls into the expected band.

## Result Summary

- `bad`: `3 / 3`
- `mid`: `1 / 3`
- `good`: `2 / 3`
- overall: `6 / 9 = 0.6667`

## Audit Interpretation

What this result proves:

- The grading side now has a reproducible measured artifact.
- The artifact is strong enough to reject a blanket `grading accuracy >= 90%` claim for the current tested scope.

What this result does not prove:

- It does not prove the overall grading system is unusable.
- It does not prove the final grading accuracy for every course/task type.

## Current Conclusion for `R7121`

- Q&A side: still supported above 90% on the existing measured dataset
- Grading side: currently **not** supported at `>= 90%` by measured evidence

Therefore:

- `R7121` remains `partial`
- The final submission should not claim complete closure of `R7121`
