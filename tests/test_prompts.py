from string import Formatter

from scripts.describe import (
    ACTIVITY_CONTEXT_PATH,
    PERSONA_LABELS,
    PROMPT_CONFIGS,
    PROMPT_INPUT_KEYS,
    SYNTHESIS_CONFIG,
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


def test_synthesis_config_exists() -> None:
    assert SYNTHESIS_CONFIG.agents_path.exists()
    assert SYNTHESIS_CONFIG.tasks_path.exists()


def test_task_templates_use_common_inputs() -> None:
    for prompt_config in PROMPT_CONFIGS:
        tasks = load_yaml_config(prompt_config.tasks_path)
        task_items = list(tasks.items())
        assert len(task_items) >= 2
        _, first_task = task_items[0]
        _, last_task = task_items[-1]
        first_fields = template_fields(first_task["description"])
        last_fields = template_fields(last_task["description"])
        assert "activity_context" in first_fields
        assert "variation_prompt" in first_fields
        assert "draft_description" in last_fields


def test_prompt_agents_include_personality_editor() -> None:
    for prompt_config in PROMPT_CONFIGS:
        agents = load_yaml_config(prompt_config.agents_path)
        assert "personality_editor" in agents


def test_persona_agents_exclude_strava_framing() -> None:
    for prompt_config in PROMPT_CONFIGS:
        agents = load_yaml_config(prompt_config.agents_path)
        for agent_config in agents.values():
            text = "\n".join(
                str(agent_config.get(key, ""))
                for key in ("role", "goal", "backstory")
            ).lower()
            assert "strava" not in text


def test_synthesis_tasks_use_perspectives_block() -> None:
    tasks = load_yaml_config(SYNTHESIS_CONFIG.tasks_path)
    for task_config in tasks.values():
        fields = template_fields(task_config["description"])
        assert "perspectives_block" in fields