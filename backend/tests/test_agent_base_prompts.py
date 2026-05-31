from agent_core.agent_base import (
    build_qa_system_prompt,
    normalize_agent_grading_result,
    sanitize_history,
)


def test_build_qa_system_prompt_requires_grounded_answer() -> None:
    prompt = build_qa_system_prompt("base", "资料1:\nJava 使用 class 定义类。")

    assert "primary source for the answer" in prompt
    assert "material does not clearly provide it" in prompt
    assert "Java 使用 class 定义类" in prompt


def test_build_qa_system_prompt_handles_empty_context() -> None:
    prompt = build_qa_system_prompt("base", "")

    assert "No course material was retrieved" in prompt
    assert "does not explicitly provide the answer" in prompt


def test_sanitize_history_keeps_valid_recent_messages() -> None:
    history = [
        {"role": "system", "content": "ignore"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "tool", "content": "ignore"},
        {"role": "user", "content": ""},
    ]

    assert sanitize_history(history) == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_normalize_agent_grading_result_contract() -> None:
    result = normalize_agent_grading_result(
        {
            "score": "108 分",
            "comment": "整体完成",
            "strengths": "结构清楚",
            "annotations": [
                {
                    "type": "warning",
                    "position": {"quote": "缺少终止条件"},
                    "message": "递归必须有终止条件",
                    "level": "high",
                    "knowledge_point_id": "8",
                }
            ],
            "knowledge_point_scores": {"8": "72.5", "9": 120},
        },
        max_score=100,
    )

    assert result["score"] == 100.0
    assert result["overall_comment"] == "整体完成"
    assert result["strengths"] == ["结构清楚"]
    assert result["annotations"] == [
        {
            "annotation_type": "warning",
            "position": {"type": "text", "quote": "缺少终止条件"},
            "content": "递归必须有终止条件",
            "severity": "high",
            "knowledge_point_id": "8",
        }
    ]
    assert result["knowledge_point_scores"] == {"8": 72.5, "9": 100.0}
    assert result["source"] == "llm"
