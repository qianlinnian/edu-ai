"""统一Agent框架SDK - 所有课程Agent的基类"""
from abc import ABC
from dataclasses import dataclass, field
from agent_core.llm_provider import BaseLLMProvider, get_llm_provider
from agent_core.rag_chain import get_context

@dataclass
class AgentConfig:
    """Agent基础配置"""
    name: str = "EduAgent"
    course_id: int = 0
    system_prompt: str = "你是一个智能教学助手。"
    llm_provider: str = "dashscope" # 后续应当扩展为 可选 provider 模型
    llm_model: str = "qwen-max"
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[str] = field(default_factory=list) # 可选工具列表，后续可扩展为更复杂的工具配置


class EduAgentBase(ABC):
    """教育Agent基类 - 所有课程Agent继承此类"""

    def __init__(self, config: AgentConfig):
        """"初始化Agent,加载LLM提供者"""
        self.config = config
        self.llm: BaseLLMProvider = get_llm_provider(config.llm_provider, config.llm_model)
        self._tools: dict = {}

    def register_tool(self, name: str, func, description: str = ""):
        """注册自定义工具 未来可能扩展支持工具调用"""
        self._tools[name] = {"func": func, "description": description}

    async def chat(self, query: str, history: list[dict] = None, context: dict = None) -> str:
        """负责通话调用 - 智能答疑 - 子类可重写以实现RAG等增强逻辑"""
        messages = [{"role": "system", "content": self.config.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})
        return await self.llm.chat(messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens)

    async def chat_stream(self, query: str, history: list[dict] = None, context: dict = None):
        """流式智能答疑 用于实现边生成边展示的交互体验 - 子类可重写以实现RAG等增强逻辑"""
        messages = [{"role": "system", "content": self.config.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})
        async for chunk in self.llm.chat_stream(
            messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens
        ):
            yield chunk

    async def grade(self, submission_content: str, assignment_info: dict) -> dict:
        """作业批改 - 子类应重写""" 
        return {"score": 0, 
                "max_score": assignment_info.get("max_score", 100)if assignment_info else 100,
                "comment": "批改功能待实现",
                "strengths": [],
                "weaknesses": [],
                "annotations": []
        }

    async def analyze_learning(self, student_id: int, course_id: int) -> dict:
        """学情分析 - 子类可重写"""
        # TODO: 实现默认学情分析
        return {"mastery": {}, "weak_points": [], "suggestions": []}

    async def generate_exercise(self, knowledge_points: list, difficulty: int = 2, count: int = 5) -> list[dict]:
        """生成练习题 - 子类可重写"""
        # TODO: 实现默认练习生成
        return []

    @classmethod
    def from_config(cls, config_dict: dict) -> "EduAgentBase":
        """从配置字典创建Agent实例 方便从数据库中调用config创建Agent"""
        config = AgentConfig(**config_dict)
        return cls(config)


class QAAgent(EduAgentBase):
    """答疑Agent - 基于RAG的课程答疑"""

    def __init__(self, config: AgentConfig):
        super().__init__(config) 

    async def chat(self, query: str, history: list[dict] = None, context: dict = None) -> str:
        """先查询课程资料 后面接着聊天生成回答 - 实现RAG增强的答疑逻辑"""
        db = context["db"] if context and "db" in context else None
        retrieved_context = ""
        if db is not None and self.config.course_id:
            retrieved_context = await get_context(
                db=db,
                course_id=self.config.course_id,
                query=query,
            )
        system_prompt = self.config.system_prompt
        if retrieved_context:
            system_prompt = (
                f"{self.config.system_prompt}\n\n"
                f"以下是与用户问题相关的课程资料：\n{retrieved_context}\n\n"
                f"请优先依据这些资料回答；如果资料不足，请明确说明。"
            )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        return await self.llm.chat(messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens)


class GradingAgent(EduAgentBase):
    """批改Agent - 作业智能批改"""

    async def grade(self, submission_content: str, assignment_info: dict) -> dict:
        # TODO: 实现精细化批改逻辑
        return await super().grade(submission_content, assignment_info)


class ExerciseAgent(EduAgentBase):
    """练习Agent - 个性化练习生成"""

    async def generate_exercise(self, knowledge_points: list, difficulty: int = 2, count: int = 5) -> list[dict]:
        # TODO: 实现练习生成逻辑
        return await super().generate_exercise(knowledge_points, difficulty, count)
