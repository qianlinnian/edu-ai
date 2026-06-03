from __future__ import annotations

import json
import re
from typing import Any


def extract_json_value(raw_text: str) -> Any:
    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start_candidates = [idx for idx in (text.find("["), text.find("{")) if idx >= 0]
        if not start_candidates:
            raise
        start = min(start_candidates)
        end = max(text.rfind("]"), text.rfind("}"))
        if end <= start:
            raise
        return json.loads(text[start : end + 1])


def extract_json_object(raw_text: str, *, error_message: str = "Expected a JSON object") -> dict[str, Any]:
    data = extract_json_value(raw_text)
    if not isinstance(data, dict):
        raise ValueError(error_message)
    return data


def extract_json_object_list(
    raw_text: str,
    *,
    list_key: str | None = None,
    error_message: str = "Expected a JSON array",
) -> list[dict[str, Any]]:
    data = extract_json_value(raw_text)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and list_key and isinstance(data.get(list_key), list):
        return [item for item in data[list_key] if isinstance(item, dict)]
    raise ValueError(error_message)


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_bounded_score(value: Any, maximum: float) -> float:
    try:
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            numeric = float(match.group(0)) if match else 0.0
        else:
            numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return round(min(max(numeric, 0.0), float(maximum)), 2)
