from __future__ import annotations

from bisect import bisect_right
from pathlib import Path

from scripts.utils import load_json, write_json

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
STRAVA_ACTIVITIES_PATH = DATA_DIR / "strava_activities.json"
GOALS_PATH = Path("goals.json")

DISTANCE_WORDS = [
    "tiny",
    "very short",
    "short",
    "brief",
    "light",
    "modest",
    "medium",
    "solid",
    "long",
    "very long",
    "big",
    "huge",
    "massive",
    "epic",
    "monster",
    "ultra",
]
MOVING_TIME_WORDS = [
    "instant",
    "quick",
    "short",
    "brisk",
    "light",
    "modest",
    "steady",
    "solid",
    "long",
    "very long",
    "drawn-out",
    "grinding",
    "exhausting",
    "epic",
    "all-day",
    "never-ending",
]
AVERAGE_HR_WORDS = [
    "restful",
    "easy",
    "relaxed",
    "comfortable",
    "steady",
    "moderate",
    "working",
    "strong",
    "hard",
    "very hard",
    "intense",
    "pushing",
    "demanding",
    "redline",
    "maxed",
    "searing",
]
MAX_HR_WORDS = [
    "low",
    "gentle",
    "easy",
    "comfortable",
    "steady",
    "firm",
    "strong",
    "hard",
    "very hard",
    "intense",
    "fierce",
    "all-out",
    "redline",
    "maxed",
    "peak",
    "sky-high",
]
CADENCE_WORDS = [
    "slow",
    "lazy",
    "easygoing",
    "casual",
    "relaxed",
    "steady",
    "smooth",
    "snappy",
    "quick",
    "brisk",
    "rapid",
    "fast",
    "fleet",
    "spinning",
    "whirring",
    "blazing",
]

GOAL_FIELDS = [
    ("distance", DISTANCE_WORDS),
    ("moving_time", MOVING_TIME_WORDS),
]

HISTORY_FIELD_CONFIGS = [
    ("average_hr", "average_heartrate", AVERAGE_HR_WORDS),
    ("max_hr", "max_heartrate", MAX_HR_WORDS),
    ("average_cadence", "average_cadence", CADENCE_WORDS),
]


def collect_history(strava_activities: list[dict]) -> dict[str, list[float]]:
    history = {field: [] for field, _, _ in HISTORY_FIELD_CONFIGS}
    for item in strava_activities:
        activity = item.get("activity") or {}
        for field, history_key, _ in HISTORY_FIELD_CONFIGS:
            value = activity.get(history_key)
            if isinstance(value, (int, float)):
                history[field].append(float(value))
    for values in history.values():
        values.sort()
    return history


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
    history: dict[str, list[float]],
    goals: dict[str, float],
) -> dict:
    context: dict[str, str] = {}
    for field, words in GOAL_FIELDS:
        value = activity.get(field)
        goal = goals.get(field)
        if not isinstance(value, (int, float)) or not isinstance(goal, (int, float)):
            continue
        context[field] = describe_goal(float(value), float(goal), words)
    for field, _, words in HISTORY_FIELD_CONFIGS:
        value = activity.get(field)
        if not isinstance(value, (int, float)):
            continue
        description = describe_value(float(value), history[field], words)
        if description:
            context[field] = description
    return context


def main() -> None:
    strava_activities = load_json(STRAVA_ACTIVITIES_PATH)
    history = collect_history(strava_activities)
    goals = load_json(GOALS_PATH)

    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload.get("activity") or {}
        payload["activity_context"] = build_context(activity, history, goals)
        write_json(path, payload)


if __name__ == "__main__":
    main()
