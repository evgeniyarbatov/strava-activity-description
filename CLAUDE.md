# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project purpose

Enrich the experience of running — not Strava captions. A linear pipeline turns GPX/TCX exports into a private journal reflection: multiple lenses that disagree, tensions between them, and one line to carry. See `ROADMAP.md` for north star and evolution plan.

## Key conventions

- **City boundary**: controlled by `BOUNDARY_POLY` in the Makefile (default `osm/ho-chi-minh-city.poly`). Switch cities via the polygon file, not by renaming pipeline outputs.
- **City OSM artifacts**: generic `city` names (`osm/city.osm.pbf`, `osm/city.osm`). Built with `make country` then `make city`.
- **Scripts run from repo root** as modules: `make <target>` or `.venv/bin/python -m scripts.<module>`.
- **Activity payload**: each run is a JSON file in `data/activities/` enriched in place by later steps. Earlier sources (`data/raw`, `data/gpx`) are not mutated.
- **Journal output**: `scripts/describe.py` writes `journal/YYYY-MM-DD.md` (one file per run date; skips existing entries). Legacy `data/descriptions/` is not the current deliverable.
- **Anti-quantization**: weather, traffic, distance, and duration are bucketed into words before reaching prompts. Avoid introducing raw numbers into prompt context unless explicitly required.
- **DynamoDB table**: `run-reflection-context` (Terraform default and `scripts/weather_traffic.py` constant must stay aligned).

## Pipeline (run in order)

```bash
make install
# one-time: API keys, Ollama models, Terraform deploy, OSM extract
make country
make city        # needs osmconvert + osmium; uses BOUNDARY_POLY
make analyze     # merge → activity → weather/traffic → uniqueness → context → poi
make reflect     # CrewAI multi-lens reflection → journal/
```

Override city: `make city BOUNDARY_POLY=osm/your-city.poly`

## Script reference

| Module | Input | Output / effect |
|--------|-------|-----------------|
| `scripts/merge.py` | `data/raw/*.gpx`, `*.tcx` | `data/gpx/` merged tracks (matched by timestamp) |
| `scripts/activity.py` | `data/gpx/` | `data/activities/*.json` with distance, moving time, polyline |
| `scripts/weather_traffic.py` | activity JSON, DynamoDB | adds `weather` and `traffic` arrays (expressive text) |
| `scripts/uniqueness.py` | activity JSON | adds `uniqueness.description` vs prior routes |
| `scripts/context.py` | activity JSON, `goals.json` | adds `activity_context` (distance/duration/time-of-day words) |
| `scripts/poi.py` | activity JSON, `osm/city.osm` | adds `geo.points_of_interest` along buffered route hull |
| `scripts/describe.py` | enriched activity JSON | `journal/YYYY-MM-DD.md` via CrewAI |

Shared helpers live in `scripts/utils.py` (`load_json`, `write_json`, `parse_iso`, `load_env`).

## Prompt / reflection architecture

- Shared template: `prompts/activity-context.txt` (filled from activity payload fields).
- Per-lens CrewAI configs: `prompts/<lens>/agents.yaml` and `prompts/<lens>/tasks.yaml`.
- Lenses: artist, buddhist-monk, memory, scientist, cartographer, physiologist, archivist, dreamer, contrarian.
- Synthesis pass: `prompts/synthesis/`.
- Model selection: `REFLECTION_MODEL` in `ollama.env` (default `gemini-3-flash-preview` via Ollama Cloud); local models also supported (`mistral-nemo`, `qwen2.5`, `gemma3`).
- `VARIATION_PROMPTS` in `describe.py` inject controlled randomness — preserve this when editing generation logic.

Reflection structure (Afterglow → Perspectives → Tensions → Residue) is defined in `README.md`.

## Infrastructure

- `terraform/` provisions DynamoDB, Lambda, IAM, and EventBridge for hourly weather/traffic sampling.
- Lambda handler: `terraform/lambda/lambda_function.py` (OpenWeather + TomTom → DynamoDB with TTL).
- API keys: `openweather.env`, `tomtom.env` (from `.env.sample` templates; real files gitignored).
- Location: `latitude` / `longitude` in `terraform/variables.tf`.
- Deploy: `cd terraform && terraform init && terraform apply`, or `make deploy` (runs tests first).

## External tools

- **wget**: downloads country PBF (`make country`)
- **osmconvert / osmium**: clip to city polygon (`make city`)
- **Ollama**: local models for reflection pipeline
- **AWS credentials**: required for `scripts/weather_traffic.py` at analyze time

## Python environment

- Python 3.12, virtual env at `.venv/`
- Dependencies in `requirements.txt` (crewai, boto3, shapely, polyline, geopy, pyyaml, etc.)
- Tests: `make test` (pytest in `tests/`)

## Design principles (when editing prompts or pipeline logic)

From `ROADMAP.md`:

1. Enrich, don't report — one strange true detail over a complete summary.
2. Perspectives should disagree — each lens notices what others ignore.
3. Data is a viewpoint, not a verdict — no grading tone.
4. Subconscious over summary — optimize for what lingers.
5. Private by default — journal between runner and runs, not audience content.

## When making changes

- Keep polygon paths configurable via Makefile / constants at top of scripts, not hardcoded city names in pipeline outputs.
- When changing DynamoDB table name, update both `terraform/variables.tf` and `scripts/weather_traffic.py`.
- When changing run steps or Makefile targets, keep `README.md` and this file in sync.
- Preserve idempotent/skipping behavior: `weather_traffic.py` skips already-enriched fields; `describe.py` skips existing journal entries.
- Do not commit generated data, OSM extracts, API keys, or journal entries (see `.gitignore` files under `data/`, `osm/`, `journal/`).
- Match existing style: minimal comments, focused diffs, no drive-by refactors.

## Do not

- Treat this as a Strava description generator — agent goals and output format should serve private reflection.
- Put raw metrics into prompts where the pipeline deliberately translates them to words first.
- Rename `city.osm.pbf` / `city.osm` back to city-specific filenames in pipeline outputs.
- Commit `.env` files or real API keys.