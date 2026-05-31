from __future__ import annotations

import asyncio

from models.assignment import Assignment, Submission
from workers.grading_task import (
    _fallback_grading,
    _grade_with_llm,
    _safe_json_loads,
    _standardize_grading_payload,
)


def make_assignment(*, max_score: float = 100.0, knowledge_points: list[int] | None = None) -> Assignment:
    return Assignment(
        title="M3 自动批改测试作业",
        description="验证结构化批改输出",
        assignment_type="text",
        max_score=max_score,
        rubric={"correctness": 60, "clarity": 40},
        reference_answer="答案应包含核心概念、推理步骤和结论。",
        knowledge_points=knowledge_points or [1, 2],
    )


def test_safe_json_loads_extracts_markdown_json_block() -> None:
    raw = """
    下面是批改结果：
    ```json
    {
      "score": "88.5分",
      "overall_comment": "结构完整",
      "strengths": ["概念清晰"],
      "weaknesses": []
    }
    ```
    """

    data = _safe_json_loads(raw)

    assert data["score"] == "88.5分"
    assert data["overall_comment"] == "结构完整"


def test_standardize_grading_payload_normalizes_core_fields() -> None:
    assignment = make_assignment(max_score=80.0)

    result = _standardize_grading_payload(
        {
            "score": "95 分",
            "comment": "批改完成",
            "strengths": "步骤比较完整",
            "weaknesses": None,
        },
        assignment=assignment,
        source="llm",
    )

    assert result["score"] == 80.0
    assert result["overall_comment"] == "批改完成"
    assert result["strengths"] == ["步骤比较完整"]
    assert result["weaknesses"] == []
    assert result["annotations"] == []
    assert result["knowledge_point_scores"] == {"1": 100.0, "2": 100.0}
    assert result["source"] == "llm"


def test_standardize_grading_payload_normalizes_annotations_and_knowledge_scores() -> None:
    assignment = make_assignment(knowledge_points=[1, 2])

    result = _standardize_grading_payload(
        {
            "score": 60,
            "overall_comment": "存在部分问题",
            "annotations": [
                {
                    "annotation_type": "invalid-type",
                    "position": {"line": 3, "quote": "错误片段"},
                    "content": "这里需要补充定义",
                    "severity": "very-high",
                    "knowledge_point_id": "1",
                },
                {
                    "type": "warning",
                    "message": "该批注关联了不存在的知识点",
                    "severity": "high",
                    "knowledge_point_id": "999",
                },
                {
                    "annotation_type": "error",
                    "content": "",
                },
            ],
            "knowledge_point_scores": {
                "1": "72.5",
                "2": 108,
                "999": 40,
            },
        },
        assignment=assignment,
        source="llm",
    )

    assert result["annotations"] == [
        {
            "annotation_type": "suggestion",
            "position": {"type": "text", "line": 3, "quote": "错误片段"},
            "content": "这里需要补充定义",
            "severity": "medium",
            "knowledge_point_id": 1,
        },
        {
            "annotation_type": "warning",
            "position": {"type": "text"},
            "content": "该批注关联了不存在的知识点",
            "severity": "high",
            "knowledge_point_id": None,
        },
    ]
    assert result["knowledge_point_scores"] == {"1": 72.5, "2": 100.0}


def test_fallback_grading_uses_same_result_shape_as_llm() -> None:
    assignment = make_assignment(max_score=100.0, knowledge_points=[1, 2])
    submission = Submission(content="太短", file_path=None)

    llm_result = _standardize_grading_payload({}, assignment=assignment, source="llm")
    fallback_result = _fallback_grading(assignment=assignment, submission=submission, error="timeout")

    assert set(fallback_result) == set(llm_result)
    assert fallback_result["source"] == "fallback"
    assert isinstance(fallback_result["score"], float)
    assert isinstance(fallback_result["overall_comment"], str)
    assert isinstance(fallback_result["strengths"], list)
    assert isinstance(fallback_result["weaknesses"], list)
    assert isinstance(fallback_result["annotations"], list)
    assert isinstance(fallback_result["knowledge_point_scores"], dict)


def test_grade_with_llm_delegates_to_grading_agent_and_keeps_worker_contract(monkeypatch) -> None:
    captured: dict = {}

    class FakeGradingAgent:
        def __init__(self, config):
            captured["config"] = config

        async def grade(self, submission_content: str, assignment_info: dict) -> dict:
            captured["submission_content"] = submission_content
            captured["assignment_info"] = assignment_info
            return {
                "score": 88,
                "overall_comment": "agent graded",
                "strengths": ["clear"],
                "weaknesses": [],
                "annotations": [
                    {
                        "annotation_type": "warning",
                        "position": {"quote": "answer"},
                        "content": "needs detail",
                        "severity": "high",
                        "knowledge_point_id": 999,
                    }
                ],
                "knowledge_point_scores": {"999": 50},
                "source": "llm",
            }

    monkeypatch.setattr("workers.grading_task.GradingAgent", FakeGradingAgent)
    assignment = make_assignment(max_score=100.0, knowledge_points=[1])
    assignment.course_id = 7
    submission = Submission(content="answer", file_path=None)

    result = asyncio.run(_grade_with_llm(assignment=assignment, submission=submission))

    assert captured["config"].course_id == 7
    assert captured["assignment_info"]["knowledge_points"] == [1]
    assert "answer" in captured["submission_content"]
    assert result["score"] == 88.0
    assert result["source"] == "llm"
    assert result["annotations"][0]["knowledge_point_id"] is None
    assert result["knowledge_point_scores"] == {"1": 88.0}
