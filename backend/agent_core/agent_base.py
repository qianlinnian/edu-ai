"""Unified Agent SDK for course-specific teaching agents."""

from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from agent_core.llm_provider import BaseLLMProvider, get_llm_provider
from agent_core.rag_chain import get_context
from core.normalization import (
    extract_json_object,
    extract_json_object_list,
    normalize_bounded_score,
    normalize_string_list,
)


DEFAULT_QA_SYSTEM_PROMPT = (
    "You are the EduAI course assistant. Answer accurately, concisely, and with clear next steps."
)
DEFAULT_GRADING_SYSTEM_PROMPT = (
    "You are the EduAI grading assistant. Return structured grading output that can be rendered directly."
)


@dataclass
class AgentConfig:
    """Runtime configuration shared by all EduAI agents."""

    name: str = "EduAgent"
    course_id: int = 0
    system_prompt: str = DEFAULT_QA_SYSTEM_PROMPT
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-max"
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[str] = field(default_factory=list)
    top_k: int = 5
    similarity_threshold: float | None = None


def sanitize_history(history: list[dict] | None, *, max_messages: int = 12) -> list[dict[str, str]]:
    """Keep only valid recent user/assistant messages before calling the LLM."""

    if not history:
        return []

    output: list[dict[str, str]] = []
    for item in history[-max_messages:]:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            output.append({"role": role, "content": content})
    return output


def build_qa_system_prompt(base_prompt: str, retrieved_context: str) -> str:
    """Build the RAG-grounded system prompt used by QAAgent."""

    if not retrieved_context.strip():
        return (
            f"{base_prompt}\n\n"
            "No course material was retrieved for this question. Say clearly that the material does not "
            "explicitly provide the answer, then answer cautiously from general course knowledge."
        )

    return (
        f"{base_prompt}\n\n"
        "Use the following course material as the primary source for the answer:\n\n"
        f"{retrieved_context}\n\n"
        "Answer requirements:\n"
        "1. Prefer concepts, steps, terms, and conclusions that appear in the material.\n"
        "2. If the material gives a procedure, answer in that procedure instead of general advice.\n"
        "3. Do not invent rules, facts, data, or conclusions not present in the material.\n"
        "4. If the material is insufficient, explicitly say the material does not clearly provide it.\n"
        "5. Keep the answer concise and concrete."
    )


def _safe_json_object(raw_text: str) -> dict[str, Any]:
    return extract_json_object(raw_text, error_message="LLM output must be a JSON object")


def _safe_json_array(raw_text: str) -> list[dict[str, Any]]:
    return extract_json_object_list(raw_text, list_key="exercises", error_message="LLM output must be a JSON array")


def _normalize_score(value: Any, max_score: float) -> float:
    return normalize_bounded_score(value, max_score)


def normalize_agent_grading_result(data: dict[str, Any] | None, *, max_score: float) -> dict[str, Any]:
    """Normalize GradingAgent output into the contract used by downstream modules."""

    data = data if isinstance(data, dict) else {}
    annotations = data.get("annotations")
    if not isinstance(annotations, list):
        annotations = []

    normalized_annotations: list[dict[str, Any]] = []
    for item in annotations:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or item.get("comment") or item.get("message") or "").strip()
        if not content:
            continue
        position = item.get("position") if isinstance(item.get("position"), dict) else {}
        normalized_annotations.append(
            {
                "annotation_type": str(item.get("annotation_type") or item.get("type") or "suggestion"),
                "position": {"type": "text", **position},
                "content": content,
                "severity": str(item.get("severity") or item.get("level") or "medium"),
                "knowledge_point_id": item.get("knowledge_point_id"),
            }
        )

    knowledge_scores = data.get("knowledge_point_scores")
    if not isinstance(knowledge_scores, dict):
        knowledge_scores = {}

    return {
        "score": _normalize_score(data.get("score"), max_score),
        "max_score": max_score,
        "overall_comment": str(data.get("overall_comment") or data.get("comment") or "Automatic grading completed.").strip(),
        "strengths": normalize_string_list(data.get("strengths")),
        "weaknesses": normalize_string_list(data.get("weaknesses")),
        "annotations": normalized_annotations,
        "knowledge_point_scores": {
            str(key): _normalize_score(value, 100.0)
            for key, value in knowledge_scores.items()
        },
        "source": str(data.get("source") or "llm"),
    }


class EduAgentBase(ABC):
    """Base class for course agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._llm: BaseLLMProvider | None = None
        self._tools: dict[str, dict[str, Any]] = {}

    @property
    def llm(self) -> BaseLLMProvider:
        if self._llm is None:
            self._llm = get_llm_provider(self.config.llm_provider, self.config.llm_model)
        return self._llm

    def register_tool(self, name: str, func, description: str = "") -> None:
        self._tools[name] = {"func": func, "description": description}

    async def chat(self, query: str, history: list[dict] | None = None, context: dict | None = None) -> str:
        messages = [{"role": "system", "content": self.config.system_prompt}]
        messages.extend(sanitize_history(history))
        messages.append({"role": "user", "content": query})
        return await self.llm.chat(messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens)

    async def chat_stream(self, query: str, history: list[dict] | None = None, context: dict | None = None):
        messages = [{"role": "system", "content": self.config.system_prompt}]
        messages.extend(sanitize_history(history))
        messages.append({"role": "user", "content": query})
        async for chunk in self.llm.chat_stream(
            messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens
        ):
            yield chunk

    async def grade(self, submission_content: str, assignment_info: dict) -> dict:
        return {
            "score": 0,
            "max_score": float(assignment_info.get("max_score", 100) if assignment_info else 100),
            "overall_comment": "This agent does not implement grading.",
            "strengths": [],
            "weaknesses": [],
            "annotations": [],
            "knowledge_point_scores": {},
            "source": "fallback",
        }

    async def analyze_learning(self, student_id: int, course_id: int) -> dict:
        return {"mastery": {}, "weak_points": [], "suggestions": []}

    async def generate_exercise(self, knowledge_points: list, difficulty: int = 2, count: int = 5) -> list[dict]:
        return []

    @classmethod
    def from_config(cls, config_dict: dict) -> "EduAgentBase":
        return cls(AgentConfig(**config_dict))


class QAAgent(EduAgentBase):
    """Course Q&A agent with RAG grounding."""

    async def _build_messages(
        self,
        *,
        query: str,
        history: list[dict] | None = None,
        context: dict | None = None,
    ) -> list[dict[str, str]]:
        db = context["db"] if context and "db" in context else None
        retrieved_context = ""
        if db is not None and self.config.course_id:
            retrieved_context = await get_context(
                db=db,
                course_id=self.config.course_id,
                query=query,
                top_k=self.config.top_k,
            )

        messages = [{"role": "system", "content": build_qa_system_prompt(self.config.system_prompt, retrieved_context)}]
        messages.extend(sanitize_history(history))
        messages.append({"role": "user", "content": query})
        return messages

    async def chat(self, query: str, history: list[dict] | None = None, context: dict | None = None) -> str:
        messages = await self._build_messages(query=query, history=history, context=context)
        return await self.llm.chat(messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens)

    async def chat_stream(self, query: str, history: list[dict] | None = None, context: dict | None = None):
        messages = await self._build_messages(query=query, history=history, context=context)
        async for chunk in self.llm.chat_stream(
            messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens
        ):
            yield chunk


class GradingAgent(EduAgentBase):
    """Assignment grading agent that returns a stable structured payload."""

    async def grade(self, submission_content: str, assignment_info: dict) -> dict:
        assignment_info = assignment_info or {}
        max_score = float(assignment_info.get("max_score") or 100)
        prompt_payload = {
            "assignment": {
                "title": assignment_info.get("title"),
                "description": assignment_info.get("description"),
                "assignment_type": assignment_info.get("assignment_type"),
                "max_score": max_score,
                "rubric": assignment_info.get("rubric"),
                "reference_answer": assignment_info.get("reference_answer"),
                "knowledge_points": assignment_info.get("knowledge_points") or [],
            },
            "submission_content": submission_content,
        }
        messages = [
            {
                "role": "system",
                "content": (
                    f"{self.config.system_prompt or DEFAULT_GRADING_SYSTEM_PROMPT}\n"
                    "Return only a JSON object with: score, overall_comment, strengths, weaknesses, "
                    "annotations, knowledge_point_scores."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Grade the assignment according to the assignment description, rubric, reference answer, "
                    "and student submission.\n"
                    "Each annotation must contain annotation_type, position, content, severity, and "
                    "knowledge_point_id.\n"
                    "Use position.quote when possible so the frontend can locate the feedback.\n\n"
                    f"{json.dumps(prompt_payload, ensure_ascii=False)}"
                ),
            },
        ]
        raw = await self.llm.chat(messages, temperature=0.2, max_tokens=self.config.max_tokens)
        return normalize_agent_grading_result(_safe_json_object(raw), max_score=max_score)


class ExerciseAgent(EduAgentBase):
    """Exercise-generation agent interface."""

    async def generate_exercise(self, knowledge_points: list, difficulty: int = 2, count: int = 5) -> list[dict]:
        payload = {
            "knowledge_points": knowledge_points,
            "difficulty": difficulty,
            "count": count,
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "Return only a JSON array. Each item must contain question, options, answer, "
                    "explanation, knowledge_point_ids, difficulty."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        raw = await self.llm.chat(messages, temperature=0.3, max_tokens=self.config.max_tokens)
        return _safe_json_array(raw)
