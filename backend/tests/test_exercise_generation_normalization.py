from __future__ import annotations

from education.exercise_engine import _normalize_generated_item, _safe_json_loads
from models.exercise import ExerciseType


def test_safe_json_loads_extracts_fenced_exercise_array() -> None:
    raw = """
    ```json
    [
      {
        "question": "递归函数为什么需要终止条件？",
        "options": [
          {"key": "A", "label": "避免无限递归"},
          {"key": "B", "label": "提高变量数量"}
        ],
        "answer": "A",
        "knowledge_point_ids": [8]
      }
    ]
    ```
    """

    data = _safe_json_loads(raw)

    assert data[0]["question"] == "递归函数为什么需要终止条件？"
    assert data[0]["answer"] == "A"


def test_normalize_generated_item_keeps_displayable_choice_shape() -> None:
    item = {
        "stem": "以下关于栈的说法正确的是？",
        "choices": ["A. 先进先出", "B. 后进先出", "C. 随机访问", "D. 只能存整数"],
        "correct_answer": "B",
        "analysis": "栈的核心特征是后进先出。",
        "difficulty": 2,
        "target_knowledge_points": ["3"],
    }

    result = _normalize_generated_item(
        item,
        fallback_knowledge_point_ids=[1],
        fallback_difficulty=1,
        exercise_type=ExerciseType.CHOICE,
    )

    assert result is not None
    assert result["question"] == "以下关于栈的说法正确的是？"
    assert result["options"] == [
        {"key": "A", "label": "先进先出"},
        {"key": "B", "label": "后进先出"},
        {"key": "C", "label": "随机访问"},
        {"key": "D", "label": "只能存整数"},
    ]
    assert result["answer"] == "B"
    assert result["knowledge_point_ids"] == [3]

