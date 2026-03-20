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
from geopy.geocoders import Nominatim

from scripts.utils import load_env, load_json, parse_iso

load_env(Path("api-keys/ollama.env"))

OLLAMA_CLOUD_MODELS = [
    "gemini-3-flash-preview",
]
OLLAMA_CLOUD_HOST = "https://api.ollama.com"
OLLAMA_MODELS = [
    *OLLAMA_CLOUD_MODELS,
    "mistral-nemo",
    "gemma3",
    "qwen2.5",
]

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
DESCRIPTIONS_DIR = DATA_DIR / "descriptions"
PROMPTS_DIR = Path("prompts")
ACTIVITY_CONTEXT_PATH = PROMPTS_DIR / "activity-context.txt"
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


def list_prompt_labels() -> list[str]:
    labels: list[str] = []
    for path in sorted(PROMPTS_DIR.iterdir()):
        if path.is_dir():
            labels.append(path.name)
    return labels


PROMPT_CONFIGS = [
    PromptConfig(
        label=label,
        agents_path=PROMPTS_DIR / label / "agents.yaml",
        tasks_path=PROMPTS_DIR / label / "tasks.yaml",
    )
    for label in list_prompt_labels()
]


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

    # Reverse geocode the midpoint of the route for location context.
    geolocator = Nominatim(user_agent="strava-activity-description")
    city, country = location_from_polyline(activity["map"]["polyline"], geolocator)

    uniqueness_description = payload["uniqueness"]["description"]
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


def resolve_ollama_endpoint(model: str) -> tuple[str, str, str | None]:
    model_name = model if "/" in model else f"ollama/{model}"
    if model in OLLAMA_CLOUD_MODELS:
        api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            raise ValueError("Missing Ollama API key in api-keys/ollama.env.")
        base_url = OLLAMA_CLOUD_HOST
    else:
        base_url = os.getenv("OLLAMA_LOCAL_HOST", "http://localhost:11434")
        api_key = None
    return model_name, base_url, api_key


def build_llm(model: str) -> LLM:
    model_name, base_url, api_key = resolve_ollama_endpoint(model)

    # CrewAI's LLM signature changes across versions; only pass supported args.
    params = inspect.signature(LLM).parameters
    kwargs: dict[str, Any] = {"model": model_name}
    if "temperature" in params:
        kwargs["temperature"] = 0.7
    if "base_url" in params:
        kwargs["base_url"] = base_url
    elif "api_base" in params:
        kwargs["api_base"] = base_url
    if api_key and "api_key" in params:
        kwargs["api_key"] = api_key

    os.environ["OLLAMA_API_BASE"] = base_url
    os.environ["OLLAMA_HOST"] = base_url
    if api_key:
        os.environ["OLLAMA_API_KEY"] = api_key

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
    crew = Crew(agents=[agent], tasks=[task])
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


def build_markdown(
    activity_id: str,
    inputs: dict,
) -> str:
    lines = [f"# {activity_id}", ""]
    activity_context = render_activity_context(inputs)
    for prompt_config in PROMPT_CONFIGS:
        agents_config, tasks_config = load_prompt_config(prompt_config)

        variation_prompt = random.choice(VARIATION_PROMPTS)
        task_inputs = {
            "activity_context": activity_context,
            "variation_prompt": variation_prompt,
        }
        lines.append(f"## {prompt_config.label}")
        for model in OLLAMA_MODELS:
            crew_output = run_prompt_pipeline(
                agents_config, tasks_config, model, task_inputs
            )
            ollama_output = to_single_line(crew_output)
            print(f"{prompt_config.label} - {model}")
            print(ollama_output)
            lines.append(f"### {model}")
            lines.append(ollama_output)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    DESCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        activity_id = activity_path.stem
        output_path = DESCRIPTIONS_DIR / f"{activity_id}.md"
        if output_path.exists():
            continue
        payload = load_json(activity_path)
        inputs = prompt_inputs(payload)
        output_path.write_text(
            build_markdown(activity_id, inputs),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
