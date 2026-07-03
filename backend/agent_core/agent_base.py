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


def _normalize_dimension_scores(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}

    output: dict[str, float] = {}
    for key, raw_score in value.items():
        name = str(key or "").strip()
        if not name:
            continue
        output[name] = normalize_bounded_score(raw_score, 100.0)
    return output


def _default_grading_dimensions(*, max_score: float, assignment_type: str | None = None) -> list[dict[str, Any]]:
    normalized_type = str(assignment_type or "text").strip().lower()
    if normalized_type in {"text", "essay", "short_answer"}:
        ratios = [
            ("correctness", 0.6, "Check whether the core concepts and conclusions are correct."),
            ("completeness", 0.25, "Check whether the required key points are covered."),
            ("clarity", 0.15, "Check whether the explanation is clear and logically organized."),
        ]
    else:
        ratios = [
            ("correctness", 0.7, "Check whether the submission is factually and procedurally correct."),
            ("completeness", 0.2, "Check whether the required parts are covered."),
            ("clarity", 0.1, "Check whether the answer is understandable and well-structured."),
        ]

    dimensions: list[dict[str, Any]] = []
    remaining = round(max_score, 2)
    for index, (name, ratio, criteria) in enumerate(ratios):
        if index == len(ratios) - 1:
            dim_max = round(remaining, 2)
        else:
            dim_max = round(max_score * ratio, 2)
            remaining = round(remaining - dim_max, 2)
        dimensions.append({"name": name, "max_score": dim_max, "criteria": criteria})
    return dimensions


def build_grading_dimensions(
    rubric: Any,
    *,
    max_score: float,
    assignment_type: str | None = None,
) -> list[dict[str, Any]]:
    dimensions: list[dict[str, Any]] = []

    if isinstance(rubric, dict):
        raw_dimensions = rubric.get("dimensions")
        if isinstance(raw_dimensions, list):
            for item in raw_dimensions:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or item.get("id") or "").strip()
                if not name:
                    continue
                dim_max = normalize_bounded_score(item.get("max_score"), max_score)
                if dim_max <= 0:
                    continue
                dimensions.append(
                    {
                        "name": name,
                        "max_score": dim_max,
                        "criteria": str(item.get("criteria") or item.get("description") or "").strip(),
                    }
                )

        if not dimensions:
            numeric_items: list[tuple[str, float]] = []
            for key, raw_value in rubric.items():
                if key in {"text", "dimensions"}:
                    continue
                if isinstance(raw_value, (int, float)):
                    numeric_items.append((str(key).strip(), float(raw_value)))

            total = sum(value for _, value in numeric_items if value > 0)
            if total > 0:
                scale = max_score / total
                for name, value in numeric_items:
                    if not name or value <= 0:
                        continue
                    dimensions.append(
                        {
                            "name": name,
                            "max_score": round(value * scale, 2),
                            "criteria": "",
                        }
                    )

    if not dimensions:
        dimensions = _default_grading_dimensions(max_score=max_score, assignment_type=assignment_type)

    return dimensions


def build_grading_rubric_guidance(
    rubric: Any,
    *,
    max_score: float,
    assignment_type: str | None = None,
) -> dict[str, Any]:
    rubric_text = ""
    if isinstance(rubric, str):
        rubric_text = rubric.strip()
    elif isinstance(rubric, dict):
        rubric_text = str(rubric.get("text") or "").strip()

    return {
        "dimensions": build_grading_dimensions(rubric, max_score=max_score, assignment_type=assignment_type),
        "rubric_text": rubric_text,
    }


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

    dimension_scores = _normalize_dimension_scores(data.get("dimension_scores"))

    return {
        "score": normalize_bounded_score(data.get("score"), max_score),
        "max_score": max_score,
        "overall_comment": str(data.get("overall_comment") or data.get("comment") or "Automatic grading completed.").strip(),
        "dimension_scores": dimension_scores,
        "strengths": normalize_string_list(data.get("strengths")),
        "weaknesses": normalize_string_list(data.get("weaknesses")),
        "annotations": normalized_annotations,
        "knowledge_point_scores": {
            str(key): normalize_bounded_score(value, 100.0)
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
        rubric_guidance = build_grading_rubric_guidance(
            assignment_info.get("rubric"),
            max_score=max_score,
            assignment_type=assignment_info.get("assignment_type"),
        )
        prompt_payload = {
            "assignment": {
                "title": assignment_info.get("title"),
                "description": assignment_info.get("description"),
                "assignment_type": assignment_info.get("assignment_type"),
                "max_score": max_score,
                "rubric": assignment_info.get("rubric"),
                "grading_dimensions": rubric_guidance["dimensions"],
                "rubric_text": rubric_guidance["rubric_text"],
                "reference_answer": assignment_info.get("reference_answer"),
                "knowledge_points": assignment_info.get("knowledge_points") or [],
                "course_material_context": assignment_info.get("course_material_context") or "",
                "grading_review_context": assignment_info.get("grading_review_context") or {},
            },
            "submission_content": submission_content,
        }
        messages = [
            {
                "role": "system",
                "content": (
                    f"{self.config.system_prompt or DEFAULT_GRADING_SYSTEM_PROMPT}\n"
                    "Return only a JSON object. Do not use markdown fences.\n"
                    "You must score the submission dimension by dimension before giving the total score.\n"
                    "Required JSON keys: score, overall_comment, dimension_scores, strengths, weaknesses, "
                    "annotations, knowledge_point_scores.\n"
                    "Rules:\n"
                    "1. dimension_scores must use the exact grading dimension names provided.\n"
                    "2. Each dimension score must be between 0 and that dimension's max_score.\n"
                    "3. score must equal the sum of all dimension_scores.\n"
                    "4. Use the reference_answer as the standard for a high-scoring answer.\n"
                    "5. If course_material_context is provided, use it as grounded course evidence, "
                    "but do not let it override the rubric or the assignment's explicit grading criteria.\n"
                    "6. For text assignments, judge conceptual correctness, coverage of required points, "
                    "and clarity, not just length.\n"
                    "7. Grade the submission by its content quality even if it is written in a different "
                    "language than the prompt or reference answer.\n"
                    "8. For text assignments, do not penalize the student merely because no attachment was "
                    "submitted when plain text content is present.\n"
                    "9. If the submission is concise but conceptually correct, do not over-penalize it.\n"
                    "10. For concept-comparison or definition questions, award strong completeness when the "
                    "answer correctly covers the required contrasts, core operations or properties, and at "
                    "least one valid application context for each item, even if the examples are brief.\n"
                    "11. Do not reduce a clearly correct answer to a low band merely because it is compact; "
                    "reserve low or mid scores for missing required points, factual mistakes, or unclear logic.\n"
                    "12. If grading_review_context is provided, use it only to audit whether the previous "
                    "score was too harsh or too generous; still rescore independently from the rubric and "
                    "submission content.\n"
                    "13. Each annotation must contain annotation_type, position, content, severity, "
                    "and knowledge_point_id."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Grade the assignment according to the assignment description, structured grading dimensions, "
                    "rubric text, reference answer, optional grounded course material context, and student submission.\n"
                    "Work in this order:\n"
                    "1. Review the reference answer and rubric.\n"
                    "2. Review any course_material_context if provided and use it only as supporting course evidence.\n"
                    "3. Score each grading dimension separately.\n"
                    "4. Sum the dimension scores to produce the final score.\n"
                    "5. Explain the main strengths and weaknesses.\n"
                    "6. Add targeted annotations tied to quoted submission text when possible.\n"
                    "7. If a grading_review_context is present, explicitly check whether the previous result "
                    "under-scored a concise but correct answer or over-scored an incomplete one, then return "
                    "your own final rubric-based score.\n"
                    "Use position.quote whenever possible so the frontend can locate the feedback.\n\n"
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
