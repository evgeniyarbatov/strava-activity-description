# Architecture

## Overview

Run Reflection is a linear data pipeline. Raw GPX/TCX exports enter at one end; a dated journal markdown file comes out the other. Each intermediate step enriches a per-activity JSON payload in `data/activities/` without mutating earlier sources (`data/raw`, `data/gpx`).

```
data/raw (GPX + TCX)
    │
    ▼ merge.py ──────────────────────────► data/gpx/
    │
    ▼ activity.py ───────────────────────► data/activities/*.json
    │
    ├─ weather_traffic.py ◄── DynamoDB ◄── Lambda (OpenWeather + TomTom)
    ├─ uniqueness.py
    ├─ context.py ◄── goals.json
    └─ poi.py ◄── osm/city.osm
    │
    ▼ describe.py (CrewAI) ──────────────► journal/YYYY-MM-DD.md
```

Orchestration lives in the `Makefile`. `make analyze` runs the enrichment chain; `make reflect` runs generation.

## Design principles

1. **Enrich, don't report.** Prefer one strange true detail over a complete summary.
2. **Perspectives should disagree.** Each lens notices what the others ignore.
3. **Anti-quantization.** Weather, traffic, distance, and duration are translated into words before reaching LLM prompts. Raw numbers are deliberately kept out of most prompt context.
4. **Private by default.** Output is a personal journal, not audience-facing copy.

See `ROADMAP.md` for the longer-term vision.

## Data directories

| Path | Role | Committed |
|------|------|-----------|
| `data/raw/` | Input GPX and TCX exports | Sample files only; rest gitignored |
| `data/gpx/` | Merged GPX with HR/cadence extensions | Gitignored |
| `data/activities/` | Enriched activity JSON (working state) | Gitignored |
| `journal/` | Final reflections | Gitignored |
| `osm/` | Country PBF, city clip, boundary polygons | Polygons only; extracts gitignored |
| `prompts/` | CrewAI agent/task YAML and shared context template | Yes |
| `goals.json` | Personal distance and moving-time targets | Yes |

## Activity payload

Each file in `data/activities/` accumulates fields as the pipeline runs. Example shape after full enrichment:

```json
{
  "activity": {
    "start_date": "2026-03-14T23:23:39Z",
    "start_date_local": "2026-03-15T06:23:39Z",
    "distance": 23405,
    "moving_time": 8365,
    "map": { "polyline": "..." }
  },
  "weather": [
    { "description": "overcast clouds", "feels_like": "serenely balanced, neither extreme" }
  ],
  "traffic": [
    { "description": "blissfully unimpeded flow" }
  ],
  "uniqueness": { "description": "notable" },
  "activity_context": {
    "distance": "lengthy",
    "moving_time": "protracted",
    "time_of_day_description": "daybreak"
  },
  "geo": {
    "points_of_interest": ["lake", "park", "forest"]
  }
}
```

Numeric fields (`distance`, `moving_time`) stay in JSON for computation but are converted to adjectives before prompts. Weather and traffic arrays hold one entry per sampled hour during the run window.

## Idempotency

Scripts skip work when output already exists:

- `merge.py` — skips if merged GPX already written
- `activity.py` — skips if activity JSON exists
- `weather_traffic.py` — skips fields already present on the payload
- `uniqueness.py` — skips if `uniqueness` key exists
- `context.py` — only writes `activity_context` when missing
- `describe.py` — skips if `journal/YYYY-MM-DD.md` already exists

Re-running is safe; delete specific artifacts to force regeneration.

## Reflection generation

`scripts/describe.py` drives a CrewAI pipeline:

1. **Context assembly** — merges activity payload fields into `prompts/activity-context.txt`. City and country come from reverse-geocoding the route midpoint via Nominatim.
2. **Perspectives** — nine lenses run sequentially, each with its own `prompts/<lens>/agents.yaml` and `tasks.yaml`. A random `VARIATION_PROMPT` constrains style per lens.
3. **Synthesis** — `prompts/synthesis/` produces Afterglow, Tensions, and Residue from the perspective block.
4. **Output** — structured markdown written to `journal/`.

### Lenses

Artist, Monk (`buddhist-monk`), Memory, Scientist, Cartographer, Physiologist, Archivist, Dreamer, Contrarian.

### Output format

```markdown
# 2026-03-15

── Afterglow ──────────────────────────
[2–3 sentences]

── Perspectives ─────────────────────
Monk:      ...
Memory:    ...

── Tensions ─────────────────────────
[Where perspectives disagree]

── Residue ──────────────────────────
[One line to carry]
```

### Model selection

`REFLECTION_MODEL` in `ollama.env` selects the local Ollama model. Default is `mistral-nemo`. Supported models: `mistral-nemo`, `qwen2.5`, `gemma3`.

## Infrastructure

Terraform provisions:

- **DynamoDB** table `run-reflection-context` with TTL
- **Lambda** `run-reflection-context` — samples OpenWeather and TomTom at configured lat/lon
- **EventBridge** — morning cron (default 04:00–07:00 Ho Chi Minh time)

The Lambda writes items keyed by `date`, `hour`, and `context` (`weather` or `traffic`). `scripts/weather_traffic.py` scans by date and filters to the activity's hour window.

DynamoDB table name must match in `terraform/variables.tf` and `scripts/weather_traffic.py`.

## Key implementation choices

- **GPX/TCX matching** — timestamps aligned to the second; first GPX sharing keys with a TCX file wins.
- **Polyline simplification** — Shapely simplify at 10 m tolerance before encoding, keeping prompt size down.
- **Route uniqueness** — RDP-simplified lat/lon vectors (48 points), z-scored, compared via L2 distance plus weighted centroid and distance offsets; scores normalized per batch into words like `notable` or `routine`.
- **POI matching** — convex hull of the route buffered 20 m in local UTM; OSM nodes/ways tagged as water, park, forest, etc.
- **Weather/traffic wording** — bucket functions map numeric feels-like temperature and speed ratio into expressive phrases (city-neutral, no hardcoded location names).