# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project purpose

Enrich the experience of running — not Strava captions. A linear pipeline turns GPX exports into a private journal reflection: multiple lenses that disagree, tensions between them, and one line to carry. See `ROADMAP.md` for north star and evolution plan.

## Key conventions

- **City boundary**: controlled by `BOUNDARY_POLY` in the Makefile (default `osm/ho-chi-minh-city.poly`). Switch cities via the polygon file, not by renaming pipeline outputs.
- **City OSM artifacts**: generic `city` names (`osm/city.osm.pbf`, `osm/city.osm`). Built with `make country` then `make city`.
- **Scripts run from repo root** as modules: `make <target>` or `.venv/bin/python -m scripts.<module>`.
- **Activity payload**: each run is a JSON file in `data/activities/` enriched in place by later steps. Earlier sources (`data/raw`) are not mutated.
- **Journal output**: `scripts/describe.py` writes `journal/YYYY-MM-DD.md` (one file per run date; skips existing entries). Legacy `data/descriptions/` is not the current deliverable.
- **Anti-quantization**: weather, traffic, distance, and duration are bucketed into words before reaching prompts. Avoid introducing raw numbers into prompt context unless explicitly required.
- **DynamoDB table**: `run-reflection-context` (Terraform default and `scripts/weather_traffic.py` constant must stay aligned).

## Documentation

Detailed docs live in `docs/`:

- [docs/architecture.md](docs/architecture.md) — pipeline, data flow, activity payload, prompts, infrastructure
- [docs/scripts.md](docs/scripts.md) — per-module behavior
- [docs/setup.md](docs/setup.md) — first-time configuration

## Pipeline (run in order)

```bash
make install
make country && make city   # one-time OSM setup
make analyze                # activity → weather/traffic → uniqueness → context → poi
make reflect                # CrewAI multi-lens reflection → journal/
```

Override city: `make city BOUNDARY_POLY=osm/your-city.poly`

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
- When changing run steps or Makefile targets, keep `README.md`, `docs/`, and this file in sync.
- Preserve idempotent/skipping behavior: `weather_traffic.py` skips already-enriched fields; `describe.py` skips existing journal entries.
- Do not commit generated data, OSM extracts, API keys, or journal entries (see `.gitignore` files under `data/`, `osm/`, `journal/`).
- Match existing style: minimal comments, focused diffs, no drive-by refactors.

## Do not

- Treat this as a Strava description generator — agent goals and output format should serve private reflection.
- Put raw metrics into prompts where the pipeline deliberately translates them to words first.
- Rename `city.osm.pbf` / `city.osm` back to city-specific filenames in pipeline outputs.
- Commit `.env` files or real API keys.