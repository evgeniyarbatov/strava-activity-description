from scripts.context import DAWN, DISTANCE_WORDS, MOVING_TIME_WORDS, build_context, describe_goal


def test_describe_goal_scales_by_ratio() -> None:
    words = ["tiny", "medium", "large"]
    assert describe_goal(5.0, 10.0, words) == "medium"


def test_build_context_uses_goals() -> None:
    activity = {
        "distance": 5.0,
        "moving_time": 3600,
        "start_date_local": "2026-01-01T06:30:00Z",
    }
    goals = {"distance": 10.0, "moving_time": 7200}

    context = build_context(activity, goals)

    assert context["distance"] == DISTANCE_WORDS[11]
    assert context["moving_time"] == MOVING_TIME_WORDS[11]
    assert context["time_of_day_description"] in set(DAWN)
