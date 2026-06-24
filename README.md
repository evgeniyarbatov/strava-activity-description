# Run Reflection

Enrich the experience of running — surface dimensions of a run that consciousness misses, forgets, or smooths over.

Each run becomes a private reflection: multiple perspectives that disagree, tensions between them, and one line to carry.

#### Sample Perspectives

> **Monk:** The overcast sky filters light through trees, casting a calm on the streets. Each step mirrors breath and movement, each moment fleeting yet clear.

> **Memory:** The reservoir is flat and gray. I carry that silence into the morning streets, keeping my breath even while the city starts its rush.

> **Contrarian:** You will call this an easy morning; the duration says otherwise.

## Prompt Configs

CrewAI configs live per lens in `prompts/<lens>/agents.yaml` and `prompts/<lens>/tasks.yaml`, with shared context in `prompts/activity-context.txt`, a personal-voice revision task, and a synthesis pass in `prompts/synthesis/`.

**Lenses:** Artist, Monk, Memory, Scientist, Cartographer, Physiologist, Archivist, Dreamer, Contrarian.

## Design

This repo is a small, linear data pipeline. Each script is intended to be run in order, and each step enriches the activity payload without mutating earlier sources:

1. `scripts/merge.py` merges GPX location tracks with TCX cadence/HR samples.
2. `scripts/activity.py` produces activity JSON (distance, moving time, polyline).
3. `scripts/weather_traffic.py` adds weather/traffic samples from DynamoDB.
4. `scripts/uniqueness.py` scores routes against prior runs.
5. `scripts/context.py` derives adjectives based on goals and time-of-day.
6. `scripts/poi.py` adds nearby POI categories from OSM data.
7. `scripts/describe.py` generates a run reflection into `journal/`.

### Output Format

Each reflection is structured for slow reading:

```
── Afterglow ──────────────────────────
[2–3 sentences. An opening image or question.]

── Perspectives ─────────────────────
Monk:      ...
Memory:    ...
[Each lens, 1–2 sentences. Deliberately incomplete.]

── Tensions ─────────────────────────
[Where perspectives disagree.]

── Residue ──────────────────────────
[One line to carry. No attribution.]
```

### Notes

- GPX/TCX matching uses shared timestamps.
- Polylines are simplified to reduce prompt size while keeping route shape intact.
- Uniqueness compares RDP-simplified lat/lon vectors, centroid offsets, and distance, then uses per-batch normalization to map scores into descriptive words.
- POI matching uses the convex hull of the route buffered by 20 meters to approximate a corridor around the run.
- Weather and traffic descriptions are bucketed into expressive text to avoid raw numbers in the prompts.
- Prompt context is centralized in `prompts/activity-context.txt`
- Variation prompts introduce controlled randomness to keep generated outputs fresh.

## Run

### First-time setup

1. Install Python dependencies:
   ```bash
   make install
   ```
2. Create API key files from the samples and fill in your keys:
   ```bash
   cp ollama.env.sample ollama.env
   cp openweather.env.sample openweather.env
   cp tomtom.env.sample tomtom.env
   ```
   Set `REFLECTION_MODEL` in `ollama.env` to choose which model generates reflections (defaults to `gemini-3-flash-preview`).
3. Install Ollama and pull local models used by the reflection pipeline:
   ```bash
   ollama pull mistral-nemo
   ollama pull qwen2.5
   ollama pull gemma3
   ```
4. Deploy weather/traffic sampling to AWS so `scripts/weather_traffic.py` can read context from DynamoDB:
   1. Set AWS credentials in your shell for the target account.
   2. Update the S3 backend in `terraform/terraform.tf`.
   3. Set `latitude` and `longitude` in `terraform/variables.tf` for your running location.
   4. Deploy:
      ```bash
      cd terraform && terraform init && terraform apply
      ```
5. Build city OSM data for POI enrichment. Install `wget`, `osmconvert`, and `osmium`, then point `BOUNDARY_POLY` in the `Makefile` at your city's boundary polygon in `osm/`:
   ```bash
   make country
   make city
   ```
   This downloads the country extract and writes `osm/city.osm.pbf` and `osm/city.osm`.

### Each run

1. Update `goals.json` with your personal distance and moving-time targets.
2. Drop matching GPX and TCX files into `data/raw`.
3. Run the enrichment pipeline:
   ```bash
   make analyze
   ```
   This merges GPX/TCX into `data/gpx`, builds activity JSON in `data/activities`, and enriches each activity with weather, traffic, route uniqueness, context, and POIs.
4. Generate the reflection:
   ```bash
   make reflect
   ```
   Output is written to `journal/YYYY-MM-DD.md` (one file per run date; existing entries are skipped).

### Optional

- Run tests before deploy: `make test`
- Deploy infrastructure from the repo root: `make deploy`