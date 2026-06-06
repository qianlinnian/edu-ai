import pytest

from agent_core.agent_base import (
    AgentConfig,
    QAAgent,
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


@pytest.mark.asyncio
async def test_qa_agent_uses_configured_top_k_for_rag(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_context(*, db, course_id, query, top_k):
        captured["db"] = db
        captured["course_id"] = course_id
        captured["query"] = query
        captured["top_k"] = top_k
        return "资料1:\n命中上下文"

    class FakeLLM:
        async def chat(self, messages, temperature, max_tokens):
            captured["messages"] = messages
            return "ok"

    monkeypatch.setattr("agent_core.agent_base.get_context", fake_get_context)

    agent = QAAgent(AgentConfig(course_id=12, top_k=8, system_prompt="base"))
    agent._llm = FakeLLM()

    result = await agent.chat("什么是栈？", context={"db": object()})

    assert result == "ok"
    assert captured["course_id"] == 12
    assert captured["query"] == "什么是栈？"
    assert captured["top_k"] == 8
    assert "命中上下文" in captured["messages"][0]["content"]
