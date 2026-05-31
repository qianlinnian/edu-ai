import asyncio

from agent_core.agent_base import AgentConfig, QAAgent, build_qa_system_prompt


class FakeStreamLLM:
    def __init__(self):
        self.messages = None

    async def chat(self, messages, **kwargs):
        self.messages = messages
        return "unused"

    async def chat_stream(self, messages, **kwargs):
        self.messages = messages
        for chunk in ["part-1", "part-2"]:
            yield chunk

    async def embedding(self, texts):
        return []


def test_qa_agent_chat_stream_uses_rag_context(monkeypatch):
    async def fake_get_context(*, db, course_id, query):
        return "Material: recursion requires a base case."

    monkeypatch.setattr("agent_core.agent_base.get_context", fake_get_context)
    monkeypatch.setattr("agent_core.agent_base.get_llm_provider", lambda provider, model: FakeStreamLLM())

    agent = QAAgent(AgentConfig(course_id=7, system_prompt="base prompt"))
    fake_llm = agent.llm

    async def run():
        chunks = []
        async for chunk in agent.chat_stream(
            query="What is recursion?",
            history=[{"role": "user", "content": "previous"}],
            context={"db": object()},
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())

    assert chunks == ["part-1", "part-2"]
    assert fake_llm.messages is not None
    assert fake_llm.messages[0]["content"] == build_qa_system_prompt(
        "base prompt",
        "Material: recursion requires a base case.",
    )
    assert fake_llm.messages[-1] == {"role": "user", "content": "What is recursion?"}
