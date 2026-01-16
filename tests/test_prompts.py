from string import Formatter

from scripts.describe import PROMPT_FILES, PROMPT_INPUT_KEYS


def template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name:
            fields.add(field_name)
    return fields


def test_prompt_templates_include_all_inputs() -> None:
    required = set(PROMPT_INPUT_KEYS)
    for _, path in PROMPT_FILES:
        template = path.read_text(encoding="utf-8")
        fields = template_fields(template)
        missing = required - fields
        assert not missing, f"{path} missing: {sorted(missing)}"
