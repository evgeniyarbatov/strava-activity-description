from string import Formatter

from scripts.describe import (
    ACTIVITY_CONTEXT_PATH,
    PERSONA_LABELS,
    PROMPT_CONFIGS,
    PROMPT_INPUT_KEYS,
    load_yaml_config,
)


def template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name:
            fields.add(field_name)
    return fields


def test_activity_context_template_includes_all_inputs() -> None:
    required = set(PROMPT_INPUT_KEYS)
    activity_context = ACTIVITY_CONTEXT_PATH.read_text(encoding="utf-8")
    fields = template_fields(activity_context)
    missing = required - fields
    assert not missing, f"{ACTIVITY_CONTEXT_PATH} missing: {sorted(missing)}"


def test_persona_labels_include_new_perspectives() -> None:
    expected = {
        "artist",
        "buddhist-monk",
        "memory",
        "scientist",
        "cartographer",
        "physiologist",
        "archivist",
        "dreamer",
        "contrarian",
    }
    assert set(PERSONA_LABELS) == expected


def test_prompt_configs_exist() -> None:
    for prompt_config in PROMPT_CONFIGS:
        assert prompt_config.agents_path.exists(), f"Missing {prompt_config.agents_path}"
        assert prompt_config.tasks_path.exists(), f"Missing {prompt_config.tasks_path}"


def test_task_templates_use_activity_context() -> None:
    for prompt_config in PROMPT_CONFIGS:
        tasks = load_yaml_config(prompt_config.tasks_path)
        assert len(tasks) == 1
        task_config = next(iter(tasks.values()))
        fields = template_fields(task_config["description"])
        assert "activity_context" in fields
        assert "variation_prompt" not in fields
        assert "draft_description" not in fields


def test_prompt_agents_have_single_persona() -> None:
    for prompt_config in PROMPT_CONFIGS:
        agents = load_yaml_config(prompt_config.agents_path)
        assert len(agents) == 1
        assert "personality_editor" not in agents


def test_persona_agents_exclude_strava_framing() -> None:
    for prompt_config in PROMPT_CONFIGS:
        agents = load_yaml_config(prompt_config.agents_path)
        for agent_config in agents.values():
            text = "\n".join(
                str(agent_config.get(key, ""))
                for key in ("role", "goal", "backstory")
            ).lower()
            assert "strava" not in text


