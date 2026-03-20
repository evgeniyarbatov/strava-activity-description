from string import Formatter

from scripts.describe import (
    ACTIVITY_CONTEXT_PATH,
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


def test_prompt_configs_exist() -> None:
    for prompt_config in PROMPT_CONFIGS:
        assert prompt_config.agents_path.exists(), f"Missing {prompt_config.agents_path}"
        assert prompt_config.tasks_path.exists(), f"Missing {prompt_config.tasks_path}"


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
