from __future__ import annotations

from agent_core.agent_base import (
    build_grading_dimensions,
    build_grading_rubric_guidance,
    normalize_agent_grading_result,
)
from models.assignment import Assignment, Submission
from workers.grading_task import (
    _apply_reference_answer_match_rule,
    _should_review_text_grading,
    _standardize_grading_payload,
)


def make_assignment(*, max_score: float = 100.0) -> Assignment:
    return Assignment(
        title="dimension grading test",
        description="validate dimension-first grading",
        assignment_type="text",
        max_score=max_score,
        rubric={
            "dimensions": [
                {"name": "correctness", "max_score": 60, "criteria": "core concept correctness"},
                {"name": "completeness", "max_score": 25, "criteria": "required coverage"},
                {"name": "clarity", "max_score": 15, "criteria": "clear explanation"},
            ]
        },
        reference_answer="Define recursion, explain base case, explain convergence.",
        knowledge_points=[1, 2],
    )


def test_build_grading_dimensions_from_structured_rubric() -> None:
    assignment = make_assignment()

    dimensions = build_grading_dimensions(assignment.rubric, max_score=assignment.max_score, assignment_type="text")

    assert dimensions == [
        {"name": "correctness", "max_score": 60.0, "criteria": "core concept correctness"},
        {"name": "completeness", "max_score": 25.0, "criteria": "required coverage"},
        {"name": "clarity", "max_score": 15.0, "criteria": "clear explanation"},
    ]


def test_build_grading_rubric_guidance_falls_back_for_text_only_rubric() -> None:
    guidance = build_grading_rubric_guidance({"text": "grade by concept quality"}, max_score=100, assignment_type="text")

    assert guidance["rubric_text"] == "grade by concept quality"
    assert [item["name"] for item in guidance["dimensions"]] == ["correctness", "completeness", "clarity"]


def test_normalize_agent_grading_result_keeps_dimension_scores() -> None:
    result = normalize_agent_grading_result(
        {
            "score": 88,
            "dimension_scores": {"correctness": "55", "completeness": 20, "clarity": 13},
            "overall_comment": "good answer",
        },
        max_score=100,
    )

    assert result["dimension_scores"] == {"correctness": 55.0, "completeness": 20.0, "clarity": 13.0}


def test_standardize_grading_payload_uses_dimension_score_sum() -> None:
    assignment = make_assignment()

    result = _standardize_grading_payload(
        {
            "score": 10,
            "dimension_scores": {"correctness": 50, "completeness": 20, "clarity": 12},
            "overall_comment": "dimension-first grading",
        },
        assignment=assignment,
        source="llm",
    )

    assert result["dimension_scores"] == {"correctness": 50.0, "completeness": 20.0, "clarity": 12.0}
    assert result["score"] == 82.0


def test_should_review_text_grading_for_mid_band_text_answer() -> None:
    assignment = make_assignment()
    submission = Submission(
        content=(
            "A stack uses LIFO and a queue uses FIFO. "
            "Stacks support push/pop and suit undo or call stacks, while queues support "
            "enqueue/dequeue and suit scheduling or BFS."
        )
    )

    assert _should_review_text_grading(
        assignment=assignment,
        submission=submission,
        grading_payload={
            "score": 72.0,
            "dimension_scores": {"correctness": 42.0, "completeness": 18.0, "clarity": 12.0},
            "overall_comment": "candidate for review",
            "source": "llm",
        },
    )


def test_should_not_review_text_grading_for_short_answer() -> None:
    assignment = make_assignment()
    submission = Submission(content="Stack is LIFO and queue is FIFO.")

    assert not _should_review_text_grading(
        assignment=assignment,
        submission=submission,
        grading_payload={
            "score": 72.0,
            "dimension_scores": {"correctness": 42.0, "completeness": 18.0, "clarity": 12.0},
            "overall_comment": "too short for recheck",
            "source": "llm",
        },
    )


def test_should_not_review_text_grading_for_high_score_answer() -> None:
    assignment = make_assignment()
    submission = Submission(
        content=(
            "A stack uses LIFO and supports push, pop, and top. "
            "A queue uses FIFO and supports enqueue, dequeue, and front. "
            "They are used in call stacks, undo, scheduling, and BFS."
        )
    )

    assert not _should_review_text_grading(
        assignment=assignment,
        submission=submission,
        grading_payload={
            "score": 95.0,
            "dimension_scores": {"correctness": 57.0, "completeness": 24.0, "clarity": 14.0},
            "overall_comment": "already high confidence",
            "source": "llm",
        },
    )


def test_reference_answer_exact_match_applies_full_score_rule() -> None:
    assignment = make_assignment()
    assignment.reference_answer = "A stack uses LIFO and a queue uses FIFO."
    submission = Submission(content="A stack uses LIFO and a queue uses FIFO.")

    result = _apply_reference_answer_match_rule(
        {
            "score": 82.0,
            "dimension_scores": {"correctness": 50.0, "completeness": 20.0, "clarity": 12.0},
            "overall_comment": "llm result",
            "source": "llm",
        },
        assignment=assignment,
        submission=submission,
    )

    assert result["score"] == 100.0
    assert result["dimension_scores"] == {"correctness": 60.0, "completeness": 25.0, "clarity": 15.0}
    assert result["source"] == "llm+reference_match_rule"


def test_reference_answer_explicit_answer_pattern_applies_full_score_rule() -> None:
    assignment = make_assignment()
    assignment.reference_answer = "标准答案是：栈是后进先出，队列是先进先出。"
    submission = Submission(content="栈是后进先出，队列是先进先出")

    result = _apply_reference_answer_match_rule(
        {
            "score": 76.0,
            "dimension_scores": {"correctness": 46.0, "completeness": 18.0, "clarity": 12.0},
            "overall_comment": "llm result",
            "source": "llm",
        },
        assignment=assignment,
        submission=submission,
    )

    assert result["score"] == 100.0
    assert result["source"] == "llm+reference_match_rule"


def test_reference_answer_non_match_keeps_original_score() -> None:
    assignment = make_assignment()
    assignment.reference_answer = "The answer is queue uses FIFO."
    submission = Submission(content="Stack uses LIFO.")

    result = _apply_reference_answer_match_rule(
        {
            "score": 76.0,
            "dimension_scores": {"correctness": 46.0, "completeness": 18.0, "clarity": 12.0},
            "overall_comment": "llm result",
            "source": "llm",
        },
        assignment=assignment,
        submission=submission,
    )

    assert result["score"] == 76.0
    assert result["source"] == "llm"
