from __future__ import annotations

import inspect
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polyline
import yaml
from crewai import Agent, Crew, LLM, Task
from crewai.events.listeners.tracing.utils import set_suppress_tracing_messages
from geopy.geocoders import Nominatim

from scripts.utils import load_env, load_json, parse_iso

load_env(Path("ollama.env"))
set_suppress_tracing_messages(True)

OLLAMA_MODELS = [
    "mistral-nemo",
    "gemma3",
    "qwen2.5",
]

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
JOURNAL_DIR = Path("journal")
PROMPTS_DIR = Path("prompts")
ACTIVITY_CONTEXT_PATH = PROMPTS_DIR / "activity-context.txt"
SYNTHESIS_LABEL = "synthesis"
PERSONA_LABELS = [
    "artist",
    "buddhist-monk",
    "memory",
    "scientist",
    "cartographer",
    "physiologist",
    "archivist",
    "dreamer",
    "contrarian",
]
PERSONA_DISPLAY_NAMES = {
    "artist": "Artist",
    "buddhist-monk": "Monk",
    "memory": "Memory",
    "scientist": "Scientist",
    "cartographer": "Cartographer",
    "physiologist": "Physiologist",
    "archivist": "Archivist",
    "dreamer": "Dreamer",
    "contrarian": "Contrarian",
}
PERSPECTIVE_LABEL_WIDTH = max(len(name) + 1 for name in PERSONA_DISPLAY_NAMES.values()) + 1
PROMPT_INPUT_KEYS = [
    "distance_context",
    "moving_time_context",
    "start_time_local",
    "time_of_day_description",
    "feels_like",
    "weather_description",
    "city_name",
    "country",
    "uniqueness_description",
    "traffic_description",
    "points_of_interest",
]
VARIATION_PROMPTS = [
    # Sensory & Perceptual
    "Lean on a single vivid sensory detail (sound, smell, or texture).",
    "Name one color or quality of light.",
    "Use one unusual verb to describe movement or air.",
    "Let a single sound anchor the whole scene.",
    "Name one smell that defines the moment.",
    "Notice one texture underfoot or against skin.",
    "Let temperature be the dominant sensation.",
    "Focus on breath — its rhythm, weight, or quality.",

    # Compositional & Structural
    "Frame the moment as a snapshot rather than a sequence.",
    "Include one brief, unexpected metaphor rooted in the surroundings.",
    "Let a small contrast shape the sentence (calm body, busy street).",
    "Build the sentence around a single object noticed in passing.",
    "Open with the environment, close with the body.",
    "Open with the body, close with the environment.",
    "Use juxtaposition between effort and stillness.",
    "Let the sentence turn on a single conjunction — but, yet, while.",

    # Temporal & Mood
    "Capture the feeling of a specific moment mid-run, not the whole.",
    "Suggest time of day without naming it directly.",
    "Evoke the mood of transition — beginning settling into rhythm.",
    "Let the city feel like it's waking up, winding down, or indifferent.",
    "Imply weather through its effect on the body, not its name.",
    "Convey effort as something almost forgotten rather than felt.",
    "Suggest the run is already over before it fully began.",

    # Voice & Distance
    "Write as if observing yourself from just outside your body.",
    "Be the last person noticing you as you pass.",
    "Let the surroundings be indifferent to the run entirely.",
    "Write as if describing a photograph taken mid-stride.",
    "Adopt the distance of a painter noting a small figure in a landscape.",
    "Make the city a character with no awareness of you.",

    # Constraint-based
    "Use no adjectives — carry everything with verbs and nouns.",
    "Use exactly one adjective. Make it count.",
    "Avoid any word that could appear in a fitness app.",
    "Say nothing about speed, distance, or time — only sensation.",
    "Let silence or absence be the defining quality.",
    "End on an image, not a feeling.",
]


@dataclass(frozen=True)
class PromptConfig:
    label: str
    agents_path: Path
    tasks_path: Path


PROMPT_CONFIGS = [
    PromptConfig(
        label=label,
        agents_path=PROMPTS_DIR / label / "agents.yaml",
        tasks_path=PROMPTS_DIR / label / "tasks.yaml",
    )
    for label in PERSONA_LABELS
]

SYNTHESIS_CONFIG = PromptConfig(
    label=SYNTHESIS_LABEL,
    agents_path=PROMPTS_DIR / SYNTHESIS_LABEL / "agents.yaml",
    tasks_path=PROMPTS_DIR / SYNTHESIS_LABEL / "tasks.yaml",
)


def most_common(values: list[str]) -> str:
    if not values:
        return ""
    return max(values, key=values.count)


def unique_join(values: list[str]) -> str:
    return ", ".join(dict.fromkeys(values))


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_pace(seconds_per_km: float) -> str:
    total_seconds = int(round(seconds_per_km))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}:{secs:02d}"


def activity_summary(
    activity: dict,
    weather_entries: list[dict],
    traffic_entries: list[dict],
) -> dict:
    start_time_local = parse_iso(activity["start_date_local"])
    start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")

    feels_like_values = [str(entry["feels_like"]) for entry in weather_entries]
    feels_like = most_common(feels_like_values)
    weather_description = unique_join(
        [str(entry["description"]) for entry in weather_entries]
    )

    traffic_description = unique_join(
        [str(entry["description"]) for entry in traffic_entries]
    )

    return {
        "start_time_local": start_time_local_str,
        "feels_like": feels_like,
        "weather_description": weather_description,
        "traffic_description": traffic_description,
    }


def midpoint_from_polyline(encoded: str) -> tuple[float, float]:
    coordinates = polyline.decode(encoded)
    return coordinates[len(coordinates) // 2]


def location_from_polyline(
    map_polyline: str, geolocator: Nominatim
) -> tuple[str | None, str | None]:
    median_lat, median_lng = midpoint_from_polyline(map_polyline)
    location = geolocator.reverse(
        (median_lat, median_lng), language="en", addressdetails=True
    )
    address = location.raw.get("address", {}) if location else {}
    return address.get("city"), address.get("country")


def prompt_inputs(payload: dict) -> dict:
    activity = payload["activity"]
    weather_entries = payload["weather"]
    traffic_entries = payload["traffic"]
    summary = activity_summary(activity, weather_entries, traffic_entries)
    activity_context = payload["activity_context"]
    points_of_interest = ", ".join(payload["geo"]["points_of_interest"])

    geolocator = Nominatim(user_agent="run-reflection")
    city, country = location_from_polyline(activity["map"]["polyline"], geolocator)

    uniqueness_description = (payload.get("uniqueness") or {}).get("description") or "uncomparable"
    time_of_day = activity_context["time_of_day_description"]
    summary.update(
        {
            "distance_context": activity_context["distance"],
            "moving_time_context": activity_context["moving_time"],
            "city_name": city,
            "country": country,
            "uniqueness_description": uniqueness_description,
            "time_of_day_description": time_of_day,
            "points_of_interest": points_of_interest,
        }
    )
    return summary


def render_activity_context(inputs: dict, template_path: Path | None = None) -> str:
    path = template_path or ACTIVITY_CONTEXT_PATH
    template = path.read_text(encoding="utf-8")
    return template.format(**inputs)


def journal_path_from_activity(activity: dict) -> Path:
    start_time_local = parse_iso(activity["start_date_local"])
    return JOURNAL_DIR / f"{start_time_local.strftime('%Y-%m-%d')}.md"


def reflection_model() -> str:
    return os.getenv("REFLECTION_MODEL", OLLAMA_MODELS[0])


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load YAML config files for CrewAI agents/tasks."""
    if not path.exists():
        raise FileNotFoundError(f"Missing CrewAI config: {path}")
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    return data or {}


def load_agents_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not config:
        raise ValueError("Expected at least 1 agent entry.")
    agents: dict[str, dict[str, Any]] = {}
    for name, details in config.items():
        if not isinstance(details, dict):
            raise ValueError(f"Invalid agent config for {name}")
        agents[name] = details
    return agents


def load_tasks_config(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if not config:
        raise ValueError("Expected at least 1 task entry.")
    tasks: list[tuple[str, dict[str, Any]]] = []
    for name, details in config.items():
        if not isinstance(details, dict):
            raise ValueError(f"Invalid task config for {name}")
        tasks.append((name, details))
    return tasks


def to_single_line(text: str) -> str:
    return " ".join(text.splitlines())


def resolve_ollama_endpoint(model: str) -> tuple[str, str]:
    model_name = model if "/" in model else f"ollama/{model}"
    base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    return model_name, base_url


def build_llm(model: str) -> LLM:
    model_name, base_url = resolve_ollama_endpoint(model)

    params = inspect.signature(LLM).parameters
    kwargs: dict[str, Any] = {"model": model_name}
    if "temperature" in params:
        kwargs["temperature"] = 0.7
    if "base_url" in params:
        kwargs["base_url"] = base_url
    elif "api_base" in params:
        kwargs["api_base"] = base_url

    os.environ["OLLAMA_API_BASE"] = base_url
    os.environ["OLLAMA_HOST"] = base_url

    return LLM(**kwargs)


def build_agent(agent_config: dict[str, Any], llm: LLM) -> Agent:
    config = dict(agent_config)
    config["llm"] = llm
    return Agent(**config)


def build_task(task_config: dict[str, Any], agent: Agent) -> Task:
    config = dict(task_config)
    config.pop("agent", None)
    return Task(agent=agent, **config)


def extract_result_text(result: Any) -> str:
    for attr in ("raw", "output"):
        if hasattr(result, attr):
            value = getattr(result, attr)
            if value:
                return str(value).strip()
    return str(result).strip()


def run_crewai_task(agent: Agent, task_config: dict[str, Any], inputs: dict[str, Any]) -> str:
    task = build_task(task_config, agent)
    crew = Crew(agents=[agent], tasks=[task], tracing=False)
    result = crew.kickoff(inputs=inputs)
    return extract_result_text(result)


def run_prompt_pipeline(
    agents_config: dict[str, dict[str, Any]],
    tasks_config: list[tuple[str, dict[str, Any]]],
    model: str,
    inputs: dict[str, Any],
) -> str:
    llm = build_llm(model)
    agents = {name: build_agent(config, llm) for name, config in agents_config.items()}
    task_inputs = dict(inputs)
    last_output = ""
    for task_name, task_config in tasks_config:
        agent_name = task_config.get("agent")
        if not agent_name:
            raise ValueError(f"Task {task_name} missing agent assignment.")
        if agent_name not in agents:
            raise ValueError(
                f"Task {task_name} expects agent {agent_name}, which is missing."
            )
        output = run_crewai_task(agents[agent_name], task_config, task_inputs)
        last_output = output
        task_inputs["draft_description"] = output
        task_inputs["previous_output"] = output
        task_inputs[task_name] = output
    return last_output


def load_prompt_config(
    prompt_config: PromptConfig,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, dict[str, Any]]]]:
    agents_config = load_yaml_config(prompt_config.agents_path)
    tasks_config = load_yaml_config(prompt_config.tasks_path)
    agents = load_agents_config(agents_config)
    tasks = load_tasks_config(tasks_config)
    for task_name, task_config in tasks:
        agent_name = task_config.get("agent")
        if agent_name and agent_name not in agents:
            raise ValueError(
                f"Task {task_name} expects agent {agent_name}, which is missing."
            )
    return agents, tasks


def format_perspectives_block(perspectives: dict[str, str]) -> str:
    lines = []
    for label in PERSONA_LABELS:
        display_name = PERSONA_DISPLAY_NAMES[label]
        text = perspectives[label]
        lines.append(f"{display_name}: {text}")
    return "\n".join(lines)


def format_perspective_line(label: str, text: str) -> str:
    display_name = f"{PERSONA_DISPLAY_NAMES[label]}:"
    return f"{display_name.ljust(PERSPECTIVE_LABEL_WIDTH)} {text}"


def run_perspectives(
    model: str,
    activity_context: str,
) -> dict[str, str]:
    perspectives: dict[str, str] = {}
    for prompt_config in PROMPT_CONFIGS:
        agents_config, tasks_config = load_prompt_config(prompt_config)
        variation_prompt = random.choice(VARIATION_PROMPTS)
        task_inputs = {
            "activity_context": activity_context,
            "variation_prompt": variation_prompt,
        }
        crew_output = run_prompt_pipeline(
            agents_config, tasks_config, model, task_inputs
        )
        perspective = to_single_line(crew_output)
        perspectives[prompt_config.label] = perspective
        print(f"{prompt_config.label}: {perspective}")
    return perspectives


def run_synthesis(
    model: str,
    activity_context: str,
    perspectives: dict[str, str],
) -> dict[str, str]:
    agents_config, tasks_config = load_prompt_config(SYNTHESIS_CONFIG)
    perspectives_block = format_perspectives_block(perspectives)
    task_inputs: dict[str, Any] = {
        "activity_context": activity_context,
        "perspectives_block": perspectives_block,
    }

    outputs: dict[str, str] = {}
    for task_name, task_config in tasks_config:
        agent_name = task_config.get("agent")
        if not agent_name:
            raise ValueError(f"Task {task_name} missing agent assignment.")
        llm = build_llm(model)
        agent = build_agent(agents_config[agent_name], llm)
        output = run_crewai_task(agent, task_config, task_inputs)
        outputs[task_name] = output
        task_inputs[task_name] = output
        if task_name == "generate_tensions":
            task_inputs["tensions"] = output
        print(f"{task_name}: {output}")
    return outputs


def section_header(title: str, width: int = 38) -> str:
    fill = max(1, width - len(title) - 3)
    return f"── {title} " + "─" * fill


def build_reflection(
    run_date: str,
    perspectives: dict[str, str],
    afterglow: str,
    tensions: str,
    residue: str,
) -> str:
    lines = [f"# {run_date}", ""]
    lines.append(section_header("Afterglow"))
    lines.append(afterglow.strip())
    lines.append("")
    lines.append(section_header("Perspectives"))
    for label in PERSONA_LABELS:
        lines.append(format_perspective_line(label, perspectives[label]))
    lines.append("")
    lines.append(section_header("Tensions"))
    lines.append(tensions.strip())
    lines.append("")
    lines.append(section_header("Residue"))
    lines.append(residue.strip())
    lines.append("")
    return "\n".join(lines)


def build_run_reflection(
    activity: dict,
    inputs: dict,
    model: str | None = None,
) -> str:
    selected_model = model or reflection_model()
    activity_context = render_activity_context(inputs)
    run_date = parse_iso(activity["start_date_local"]).strftime("%Y-%m-%d")

    perspectives = run_perspectives(selected_model, activity_context)
    synthesis = run_synthesis(selected_model, activity_context, perspectives)

    return build_reflection(
        run_date=run_date,
        perspectives=perspectives,
        afterglow=synthesis["generate_afterglow"],
        tensions=synthesis["generate_tensions"],
        residue=synthesis["generate_residue"],
    )


def main() -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        payload = load_json(activity_path)
        activity = payload["activity"]
        output_path = journal_path_from_activity(activity)
        if output_path.exists():
            continue
        inputs = prompt_inputs(payload)
        output_path.write_text(
            build_run_reflection(activity, inputs),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()