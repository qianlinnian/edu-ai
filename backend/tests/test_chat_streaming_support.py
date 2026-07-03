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


class FakeDashScopeResponse:
    def __init__(self, *, status_code=200, content=None, message="ok"):
        self.status_code = status_code
        self.message = message
        self.output = type(
            "Output",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": content})()},
                    )()
                ]
            },
        )()


def test_qa_agent_chat_stream_uses_rag_context(monkeypatch):
    async def fake_get_context(*, db, course_id, query, top_k):
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


def test_dashscope_stream_ignores_empty_frames(monkeypatch):
    frames = [
        FakeDashScopeResponse(content=""),
        FakeDashScopeResponse(content=None),
        FakeDashScopeResponse(content="part-1"),
        FakeDashScopeResponse(content=[{"text": "part-2"}]),
    ]

    class FakeGeneration:
        @staticmethod
        def call(**kwargs):
            return frames

    monkeypatch.setattr("dashscope.Generation", FakeGeneration)

    provider = __import__("agent_core.llm_provider", fromlist=["DashScopeProvider"]).DashScopeProvider(
        model="qwen-max",
        api_key="test-key",
    )

    async def run():
        chunks = []
        async for chunk in provider.chat_stream([{"role": "user", "content": "hello"}]):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())
    assert chunks == ["part-1", "part-2"]
