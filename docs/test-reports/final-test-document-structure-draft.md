# EduAI Final Test Document Structure Draft

Date: 2026-06-29
Purpose: submission-oriented final test document structure

## Proposed File

- `docs/test-reports/final-test-document.md`

## Proposed Table of Contents

1. Executive Conclusion
   - Whether complete final-RBS coverage can be claimed
   - Boundary statements for any non-closed requirements

2. Test Scope and Requirement Source
   - Final RBS source:
     - [docs/rbs-wbs-schedule+gantt.md](/D:/course/SEME/edu-ai/docs/rbs-wbs-schedule+gantt.md:1)
   - Scope of this document
   - Definitions:
     - automated test evidence
     - functional evidence
     - deployment/performance evidence
     - documentation evidence

3. Test Environment and Execution Baseline
   - backend environment
   - `conda activate edu`
   - `pytest backend/tests -q`
   - observed result: `74 passed`
   - deployment health evidence

4. Final RBS-First Coverage Matrix
   - one row per final RBS requirement
   - columns:
     - requirement id
     - requirement summary
     - automated test evidence
     - functional evidence
     - document evidence
     - status
     - gap
     - closure action

5. Requirement Deep Dives
   - `R7121` accuracy target
   - `R2111` content extraction formats
   - `R4111` grading format support
   - `R7231` exception-family coverage
   - `R213` retrieval-scope clarification

6. Automated Test Evidence
   - test suite list
   - selected high-signal test cases
   - note that no formal `pytest-cov` artifact exists

7. Functional and E2E Evidence
   - M3 teaching loop
   - M4 main flow validation
   - current UI/browser evidence limits

8. Deployment and Performance Evidence
   - deployment health
   - 500-user read-path monitored rerun
   - 15-user business-path baseline
   - earlier noisy run and why it is not the primary cited result

9. Accuracy Evidence
   - Q&A evaluation result
   - grading evaluation result or explicit gap statement

10. Gap Closure Checklist
   - reuse [final-rbs-gap-closure-checklist-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-gap-closure-checklist-draft.md:1)

11. Final Claim Boundary
   - exact safe wording for submission
   - exact wording that should be avoided

## Required Appendices

### Appendix A: Evidence File Index

- [tmp_test_coverage_audit.md](/D:/course/SEME/edu-ai/tmp_test_coverage_audit.md:1)
- [final-rbs-test-coverage-matrix-draft.md](/D:/course/SEME/edu-ai/docs/test-reports/final-rbs-test-coverage-matrix-draft.md:1)
- [data/dataStructure/datastructure-eval-results.json](/D:/course/SEME/edu-ai/data/dataStructure/datastructure-eval-results.json:4)
- [docs/test-reports/2026-05-26-M3-end-to-end-test-record.md](/D:/course/SEME/edu-ai/docs/test-reports/2026-05-26-M3-end-to-end-test-record.md:1)
- [docs/test-reports/M4-测试证据记录-v0.4.0.md](/D:/course/SEME/edu-ai/docs/test-reports/M4-测试证据记录-v0.4.0.md:1)
- [docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-500-monitored2m-final-20260628_stats.csv:1)
- [docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv](/D:/course/SEME/edu-ai/docs/test-reports/autodl-20260628/round2/loadtest-business-clean-15u-20260628_stats.csv:1)

### Appendix B: Open Items That Still Block a Full Claim

- grading accuracy result for `R7121`
- hybrid retrieval evidence or scope correction for `R213`
- compact format matrices for `R2111` and `R4111`
- exception-family closure wording and evidence for `R7231`
