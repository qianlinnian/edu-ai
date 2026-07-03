from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

BACKEND_DIR = Path(
    os.environ.get("EDUAI_BACKEND_DIR", Path(__file__).resolve().parent.parent)
).resolve()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from models.assignment import Assignment, Submission
from workers.grading_task import _grade_with_llm


def build_assignment(*, course_id: int, config: dict[str, Any] | None = None) -> Assignment:
    config = config or {}
    assignment = Assignment(
        title=str(config.get("title") or "Draft grading evaluation: recursion basics"),
        description=str(
            config.get("description")
            or "Explain recursion with termination condition and parameter convergence."
        ),
        assignment_type=str(config.get("assignment_type") or "text"),
        max_score=float(config.get("max_score") or 100.0),
        rubric=config.get("rubric")
        or {
            "dimensions": [
                {
                    "name": "correctness",
                    "max_score": 60,
                    "criteria": "Correctly define recursion, base case, and recursive progression.",
                },
                {
                    "name": "completeness",
                    "max_score": 25,
                    "criteria": "Cover the key required points and use an appropriate example or explanation.",
                },
                {
                    "name": "clarity",
                    "max_score": 15,
                    "criteria": "Explain the idea clearly with coherent structure and wording.",
                },
            ]
        },
        reference_answer=str(
            config.get("reference_answer")
            or (
                "A good recursion answer should define recursion, include a base case, "
                "and explain how each call moves toward the base case."
            )
        ),
        knowledge_points=config.get("knowledge_points") or [8, 9],
    )
    assignment.course_id = course_id
    return assignment


async def evaluate_case(case: dict[str, Any], *, course_id: int, assignment_config: dict[str, Any] | None = None) -> dict[str, Any]:
    assignment = build_assignment(course_id=course_id, config=assignment_config)
    submission = Submission(content=str(case["content"]), file_path=None)
    result = await _grade_with_llm(assignment=assignment, submission=submission)
    score = float(result["score"])
    expected_min = float(case["expected_min"])
    expected_max = float(case["expected_max"])
    passed = expected_min <= score <= expected_max
    return {
        "id": case["id"],
        "label": case["label"],
        "expected_min": expected_min,
        "expected_max": expected_max,
        "actual_score": score,
        "pass": passed,
        "source": result.get("source"),
        "overall_comment": result.get("overall_comment"),
    }


def _load_case_file(cases_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    raw_cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    if isinstance(raw_cases, list):
        return None, raw_cases
    if isinstance(raw_cases, dict):
        assignment = raw_cases.get("assignment")
        cases = raw_cases.get("cases")
        if not isinstance(cases, list):
            raise ValueError("Case file 'cases' must parse to a list.")
        if assignment is not None and not isinstance(assignment, dict):
            raise ValueError("Case file 'assignment' must parse to an object when provided.")
        return assignment, cases
    raise ValueError("Case file must parse to a list or an object with 'assignment' and 'cases'.")


async def evaluate(*, cases_path: Path, course_id: int) -> dict[str, Any]:
    assignment_config, raw_cases = _load_case_file(cases_path)

    results: list[dict[str, Any]] = []
    for case in raw_cases:
        evaluated = await evaluate_case(case, course_id=course_id, assignment_config=assignment_config)
        results.append(evaluated)
        print(
            f"{evaluated['id']}: "
            f"label={evaluated['label']} score={evaluated['actual_score']} pass={evaluated['pass']}"
        )

    total = len(results)
    passed = sum(1 for item in results if item["pass"])
    by_label: dict[str, dict[str, int]] = {}
    for item in results:
        bucket = by_label.setdefault(item["label"], {"total": 0, "passed": 0})
        bucket["total"] += 1
        if item["pass"]:
            bucket["passed"] += 1

    return {
        "metric": "score_band_match_accuracy",
        "course_id": course_id,
        "cases_path": str(cases_path),
        "assignment": assignment_config or {
            "title": "Draft grading evaluation: recursion basics",
            "description": "Explain recursion with termination condition and parameter convergence.",
            "assignment_type": "text",
        },
        "total_cases": total,
        "passed_cases": passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "by_label": by_label,
        "results": results,
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run a draft grading evaluation against the real grading path.")
    parser.add_argument("--cases", required=True, help="YAML case file.")
    parser.add_argument("--course-id", type=int, default=2, help="Course id used by the grading config.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    cases_path = Path(args.cases).expanduser().resolve()
    if not cases_path.exists():
        print(f"cases not found: {cases_path}")
        return 1

    summary = await evaluate(cases_path=cases_path, course_id=args.course_id)
    print("---SUMMARY---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
