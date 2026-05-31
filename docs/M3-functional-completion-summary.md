# M3 Functional Completion Summary

Date: 2026-05-26

## Milestone Target

M3 target: complete the teaching loop from AI grading / learning analytics to personalized exercise generation.

## Completed Functions

### Backend

- `POST /api/v1/exercises/generate` generates targeted exercises for student users.
- Generation uses course knowledge points and student mastery state.
- LLM generation path writes records to `generated_exercises`.
- Fallback path keeps the exercise workflow available when LLM output is unavailable.
- `POST /api/v1/exercises/attempt` accepts either `exercise_id` or `generated_exercise_id`.
- Attempt submission updates `exercise_attempts`.
- Attempt submission updates `student_knowledge_mastery`.
- Attempt submission refreshes `learning_alerts`.

### Frontend

- Exercise Center now has a `根据薄弱点生成练习` button.
- Button click calls `POST /api/v1/exercises/generate`.
- Returned exercises replace the active question list.
- The UI distinguishes:
  - `AI 生成`
  - `题库推荐`
  - `兜底练习`
- Generated exercises submit answers with `generated_exercise_id`.
- Pool exercises submit answers with `exercise_id`.

### Verification Materials

- End-to-end test record: `docs/test-reports/2026-05-26-M3-end-to-end-test-record.md`
- Screenshot: `docs/test-reports/screenshots/m3-exercise-ai-generated-2026-05-26.png`
- Demo data backup: `data/backups/m3-demo-data-2026-05-26.sql`

## Acceptance Status

M3 is functionally complete in the local integration environment. The verified test flow used `student_01`, generated 3 LLM exercises for `CS101`, submitted an answer through `generated_exercise_id`, and confirmed database updates for generated exercises, attempts, mastery, and alerts.
