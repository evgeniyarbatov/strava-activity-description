from scripts.context import (
    AVERAGE_HR_WORDS,
    CADENCE_WORDS,
    DISTANCE_WORDS,
    MAX_HR_WORDS,
    MOVING_TIME_WORDS,
    build_context,
    collect_history,
    describe_goal,
    describe_value,
)


def test_collect_history_sorts_numeric_values() -> None:
    history = collect_history(
        [
            {"activity": {"average_heartrate": 150, "max_heartrate": 180, "average_cadence": 80}},
            {"activity": {"average_heartrate": 120, "max_heartrate": 170}},
            {"activity": {"average_heartrate": "fast"}},
        ]
    )

    assert history["average_hr"] == [120.0, 150.0]
    assert history["max_hr"] == [170.0, 180.0]
    assert history["average_cadence"] == [80.0]


def test_describe_value_uses_percentiles() -> None:
    words = ["low", "medium", "high", "top"]
    assert describe_value(2.0, [1.0, 2.0, 3.0, 4.0], words) == "high"


def test_describe_goal_scales_by_ratio() -> None:
    words = ["tiny", "medium", "large"]
    assert describe_goal(5.0, 10.0, words) == "medium"


def test_build_context_combines_goal_and_history() -> None:
    activity = {
        "distance": 5.0,
        "moving_time": 3600,
        "average_hr": 150,
        "max_hr": 180,
        "average_cadence": 80,
    }
    history = {
        "average_hr": [100.0, 140.0, 160.0],
        "max_hr": [120.0, 170.0, 190.0],
        "average_cadence": [60.0, 90.0, 100.0],
    }
    goals = {"distance": 10.0, "moving_time": 7200}

    context = build_context(activity, history, goals)

    assert context["distance"] == DISTANCE_WORDS[7]
    assert context["moving_time"] == MOVING_TIME_WORDS[7]
    assert context["average_hr"] == AVERAGE_HR_WORDS[10]
    assert context["max_hr"] == MAX_HR_WORDS[10]
    assert context["average_cadence"] == CADENCE_WORDS[5]
