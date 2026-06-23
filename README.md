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

1. Update `goals.json` to set your personal distance and moving time targets.
2. Add GPX/TCX to `data/raw`.
3. Run `make analyze` to merge GPX/TCX and enrich activities with weather/traffic context.
4. Run `make reflect` to generate reflections in `journal/YYYY-MM-DD.md`.

Set `REFLECTION_MODEL` in `ollama.env` to choose which model generates reflections (defaults to `gemini-3-flash-preview`).

## Dev Setup

1. Create the venv and install dependencies: `make install`.
2. Install Ollama and pull models:
   1. `ollama pull mistral-nemo`
   2. `ollama pull qwen2.5`
   3. `ollama pull gemma3`
3. Add API keys: create `ollama.env`, `openweather.env`, and `tomtom.env` from the `.env.sample` templates and fill in your keys.
4. Configure Terraform + AWS: set AWS credentials in your shell for the target account; update the S3 backend in `terraform/terraform.tf`; set latitude/longitude for weather + traffic sampling
5. Deploy infrastructure: `cd terraform && terraform init`, then `terraform apply`