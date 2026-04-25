from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from agent_core.agent_base import AgentConfig, QAAgent
from agent_core.rag_chain import retrieve_chunks
from core.database import async_session


def expected_letter(item: dict[str, Any]) -> str | None:
    for point in item.get("expected_points", []):
        letters = re.findall(r"\b([A-D])\b", str(point))
        if letters:
            return letters[-1]
    return None


def answer_letter(text: str) -> str | None:
    patterns = [
        r"ANSWER[:：]\s*([A-D])",
        r"ANS[:：]\s*([A-D])",
        r"OPTION[:：]\s*([A-D])",
        r"^\s*([A-D])\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).upper()

    letters = re.findall(r"\b([A-D])\b", text)
    return letters[0].upper() if letters else None


def build_mcq_prompt(item: dict[str, Any]) -> str:
    options = item.get("options", {})
    lines = [
        "Answer the following multiple-choice question strictly from the retrieved course material.",
        "Output exactly two lines:",
        "ANSWER: <A/B/C/D>",
        "REASON: <one short sentence>",
        "",
        f"QUESTION: {item['question']}",
        "OPTIONS:",
    ]
    for key in ["A", "B", "C", "D"]:
        if key in options:
            lines.append(f"{key}. {options[key]}")
    return "\n".join(lines)


async def evaluate(
    checklist_path: Path,
    course_id: int,
    top_k: int,
    llm_provider: str,
    llm_model: str,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    items = yaml.safe_load(checklist_path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("Checklist file must parse to a list of questions.")

    config = AgentConfig(
        name="MCQ Eval Agent",
        course_id=course_id,
        system_prompt="You are a course teaching assistant. Answer strictly from the course materials.",
        llm_provider=llm_provider,
        llm_model=llm_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    agent = QAAgent(config)

    results: list[dict[str, Any]] = []
    async with async_session() as db:
        for idx, item in enumerate(items, start=1):
            query = item["question"]
            chunks = await retrieve_chunks(db, course_id, query, top_k=top_k)
            response = await agent.chat(build_mcq_prompt(item), history=[], context={"db": db})

            expected = expected_letter(item)
            actual = answer_letter(response or "")
            correct = expected is not None and actual == expected

            result = {
                "index": idx,
                "question": query,
                "expected": expected,
                "actual": actual,
                "correct": correct,
                "retrieved_count": len(chunks),
                "top_chunk_preview": chunks[0].content[:120] if chunks else "",
                "response": response,
            }
            results.append(result)
            print(f"{idx:02d}. expected={expected} actual={actual} correct={correct}")

    total = len(results)
    correct_count = sum(1 for result in results if result["correct"])
    retrieval_nonempty = sum(1 for result in results if result["retrieved_count"] > 0)

    return {
        "course_id": course_id,
        "checklist_path": str(checklist_path),
        "total_questions": total,
        "correct": correct_count,
        "accuracy": round(correct_count / total, 4) if total else 0.0,
        "retrieval_nonempty": retrieval_nonempty,
        "wrong_questions": [
            {
                "index": result["index"],
                "question": result["question"],
                "expected": result["expected"],
                "actual": result["actual"],
                "response": result["response"],
            }
            for result in results
            if not result["correct"]
        ],
        "results": results,
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a multiple-choice checklist against one course.")
    parser.add_argument("--checklist", required=True, help="UTF-8 checklist markdown/yaml file path.")
    parser.add_argument("--course-id", type=int, required=True, help="Course id used for retrieval.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve per question.")
    parser.add_argument("--llm-provider", default="dashscope", help="LLM provider used by QAAgent.")
    parser.add_argument("--llm-model", default="qwen-max", help="LLM model used by QAAgent.")
    parser.add_argument("--temperature", type=float, default=0.1, help="Generation temperature.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Generation max tokens.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    checklist_path = Path(args.checklist).expanduser().resolve()
    if not checklist_path.exists():
        print(f"checklist not found: {checklist_path}")
        return 1

    summary = await evaluate(
        checklist_path=checklist_path,
        course_id=args.course_id,
        top_k=args.top_k,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    print("---SUMMARY---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
