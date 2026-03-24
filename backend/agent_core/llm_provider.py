"""LLM Provider 抽象层 - 支持多模型切换"""
from abc import ABC, abstractmethod
from core.config import get_settings

settings = get_settings()


class BaseLLMProvider(ABC):
    """LLM提供者基类"""

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """对话补全"""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs):
        """流式对话补全"""
        ...

    @abstractmethod
    async def embedding(self, texts: list[str]) -> list[list[float]]:
        """文本向量化"""
        ...


class DashScopeProvider(BaseLLMProvider):
    """通义千问 Provider"""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.QWEN_MODEL
        self.api_key = api_key or settings.DASHSCOPE_API_KEY

    async def chat(self, messages: list[dict], **kwargs) -> str:
        import dashscope
        dashscope.api_key = self.api_key
        response = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",
            **kwargs,
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        raise Exception(f"DashScope API error: {response.code} - {response.message}")

    async def chat_stream(self, messages: list[dict], **kwargs):
        import dashscope
        dashscope.api_key = self.api_key
        responses = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",
            stream=True,
            incremental_output=True,
            **kwargs,
        )
        for response in responses:
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if content:
                    yield content

    async def embedding(self, texts: list[str]) -> list[list[float]]:
        import dashscope
        dashscope.api_key = self.api_key
        response = dashscope.TextEmbedding.call(
            model=settings.QWEN_EMBEDDING_MODEL,
            input=texts,
        )
        if response.status_code == 200:
            return [item["embedding"] for item in response.output["embeddings"]]
        raise Exception(f"DashScope Embedding error: {response.code} - {response.message}")


class ZhipuProvider(BaseLLMProvider):
    """智谱GLM Provider"""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.ZHIPU_MODEL
        self.api_key = api_key or settings.ZHIPU_API_KEY

    async def chat(self, messages: list[dict], **kwargs) -> str:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        response = client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], **kwargs):
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        response = client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    async def embedding(self, texts: list[str]) -> list[list[float]]:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        results = []
        for text in texts:
            response = client.embeddings.create(model="embedding-3", input=text)
            results.append(response.data[0].embedding)
        return results


def get_llm_provider(provider: str = None, model: str = None) -> BaseLLMProvider:
    """获取LLM Provider实例"""
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    if provider == "dashscope":
        return DashScopeProvider(model=model)
    elif provider == "zhipu":
        return ZhipuProvider(model=model)
    else:
        raise ValueError(f"不支持的LLM Provider: {provider}")
