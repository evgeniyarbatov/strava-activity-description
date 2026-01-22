from __future__ import annotations
from bisect import bisect_right
from pathlib import Path
from scripts.utils import load_json, write_json

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
GOALS_PATH = Path("goals.json")

DISTANCE_WORDS = [
    "minuscule",
    "tiny",
    "petite",
    "brief",
    "short",
    "compact",
    "modest",
    "fair",
    "moderate",
    "respectable",
    "substantial",
    "solid",
    "lengthy",
    "considerable",
    "extensive",
    "ambitious",
    "massive",
    "monumental",
    "colossal",
    "epic",
    "gargantuan",
    "heroic",
    "legendary",
    "ultra",
]

MOVING_TIME_WORDS = [
    "fleeting",
    "swift",
    "quick",
    "nippy",
    "brisk",
    "expeditious",
    "efficient",
    "moderate",
    "steady",
    "sustained",
    "prolonged",
    "extended",
    "lengthy",
    "protracted",
    "arduous",
    "drawn-out",
    "grueling",
    "grinding",
    "marathon",
    "exhausting",
    "punishing",
    "epic",
    "all-consuming",
    "never-ending",
]

GOAL_FIELDS = [
    ("distance", DISTANCE_WORDS),
    ("moving_time", MOVING_TIME_WORDS),
]


def describe_value(value: float, values: list[float], words: list[str]) -> str | None:
    if not values:
        return None
    position = bisect_right(values, value)
    percentile = position / len(values)
    index = min(len(words) - 1, int(percentile * len(words)))
    return words[index]


def describe_goal(value: float, goal: float, words: list[str]) -> str:
    ratio = value / goal
    index = min(len(words) - 1, int(ratio * (len(words) - 1)))
    return words[index]


def build_context(
    activity: dict,
    goals: dict[str, float],
) -> dict:
    context: dict[str, str] = {}
    for field, words in GOAL_FIELDS:
        value = activity.get(field)
        goal = goals.get(field)
        if not isinstance(value, (int, float)) or not isinstance(goal, (int, float)):
            continue
        context[field] = describe_goal(float(value), float(goal), words)
    return context


def main() -> None:
    goals = load_json(GOALS_PATH)
    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload.get("activity") or {}
        payload["activity_context"] = build_context(activity, goals)
        write_json(path, payload)


if __name__ == "__main__":
    main()