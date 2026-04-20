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
        if not self.api_key:
            raise ValueError("DashScope API Key未配置，请设置DASHSCOPE_API_KEY环境变量或在配置文件中指定")

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
        raise Exception(f"DashScope API error: function(chat), status_code: {response.status_code} - {response.message}")

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
                else:
                    raise Exception(f"DashScope API error: function(chat_stream) - empty content in response")
            else:
                raise Exception(f"DashScope API error: function(chat_stream), status_code: {response.status_code} - {response.message}")

    async def embedding(self, texts: list[str]) -> list[list[float]]:
        import dashscope
        dashscope.api_key = self.api_key
        response = dashscope.TextEmbedding.call(
            model=settings.QWEN_EMBEDDING_MODEL,
            input=texts,
        )
        if response.status_code == 200:
            return [item["embedding"] for item in response.output["embeddings"]]
        raise Exception(f"DashScope Embedding error: function(embedding), status_code: {response.status_code} - {response.message}")


class ZhipuProvider(BaseLLMProvider):
    """智谱GLM Provider"""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.ZHIPU_MODEL
        self.api_key = api_key or settings.ZHIPU_API_KEY
        if not self.api_key:
            raise ValueError("智谱API Key未配置，请设置ZHIPU_API_KEY环境变量或在配置文件中指定")

    async def chat(self, messages: list[dict], **kwargs) -> str:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        response = client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        if response.status_code == 200:
            return response.choices[0].message.content
        raise Exception(f"智谱API error: function(chat), status_code: {response.status_code} - {response.message}")

    async def chat_stream(self, messages: list[dict], **kwargs):
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        response = client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
        raise Exception(f"智谱API error: function(chat_stream), status_code: {response.status_code} - {response.message}")
    async def embedding(self, texts: list[str]) -> list[list[float]]:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=self.api_key)
        results = []
        for text in texts:
            response = client.embeddings.create(model="embedding-3", input=text)
            results.append(response.data[0].embedding)
        return results


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek Provider（OpenAI兼容接口）"""

    BASE_URL = "https://api.deepseek.com"

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.DEEPSEEK_MODEL
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError("DeepSeek API Key未配置，请设置DEEPSEEK_API_KEY环境变量或在配置文件中指定")

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.BASE_URL)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        client = self._get_client()
        response = client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], **kwargs):
        client = self._get_client()
        response = client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embedding(self, texts: list[str]) -> list[list[float]]:
        # DeepSeek暂无Embedding API，回退到DashScope
        fallback = DashScopeProvider()
        return await fallback.embedding(texts)


def get_llm_provider(provider: str = None, model: str = None) -> BaseLLMProvider:
    """获取LLM Provider实例"""
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    if provider == "dashscope":
        return DashScopeProvider(model=model)
    elif provider == "zhipu":
        return ZhipuProvider(model=model)
    elif provider == "deepseek":
        return DeepSeekProvider(model=model)
    else:
        raise ValueError(f"不支持的LLM Provider: {provider}")
