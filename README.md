# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history.

#### Artistic

> Morning whispers through overcast skies in Hà Nội, my legs gliding past gardens and lakes as I breathe in the city's slow awakening. Trees line the path like silent sentinels, their branches cradling dappled light.

#### Monk

> The overcast sky filters light through trees, casting a calm on the streets. Each step mirrors my breath and movement, as I wander through forest, garden, lake, and park, each moment fleeting yet clear.

#### Memory

> The reservoir is flat and gray. I carry that silence into the morning streets, keeping my breath even while the city starts its rush.

#### Scientist

> At daybreak on March 15, 2026, I set out for a run through Hà Nội's overcast skies. The route took me through forests, gardens, and parks, offering a mix of nature and the city’s hustle, all while moving smoothly despite the typical morning commotion.

## Prompt Configs

CrewAI configs live per prompt in `prompts/<prompt>/agents.yaml` and `prompts/<prompt>/tasks.yaml`, with shared context in `prompts/activity-context.txt` and a final personal-voice revision task.

## Design

This repo is a small, linear data pipeline. Each script is intended to be run in order, and each step enriches the activity payload without mutating earlier sources:

1. `scripts/merge.py` merges GPX location tracks with TCX cadence/HR samples.
2. `scripts/activity.py` produces activity JSON (distance, moving time, polyline).
3. `scripts/weather_traffic.py` adds weather/traffic samples from DynamoDB.
4. `scripts/uniqueness.py` scores routes against prior runs.
5. `scripts/context.py` derives adjectives based on goals and time-of-day.
6. `scripts/poi.py` adds nearby POI categories from OSM data.
7. `scripts/describe.py` renders descriptions for each prompt/model.

Key design choices:

- GPX/TCX matching uses shared timestamps rather than filenames to avoid brittle naming assumptions.
- Polylines are simplified to reduce prompt size while keeping route shape intact.
- Uniqueness compares RDP-simplified lat/lon vectors, centroid offsets, and distance, then uses per-batch normalization to map scores into descriptive words.
- POI matching uses the convex hull of the route buffered by 20 meters to approximate a corridor around the run.
- Weather and traffic descriptions are bucketed into expressive text to avoid raw numbers in the prompts.
- Prompt context is centralized in `prompts/activity-context.txt` so each prompt uses a consistent, shared vocabulary.
- Variation prompts introduce controlled randomness to keep generated outputs fresh.

## Run

1. Update `goals.json` to set your personal distance and moving time targets.
2. Add GPX/TCX to `data/raw`.
3. Run `make analyze` to merge GPX/TCX and enrich activities with weather/traffic context.
4. Run `make describe` to generate descriptions in `data/descriptions`.

## Dev Setup

1. Create the venv and install dependencies: `make install`.
2. Install Ollama and pull models:
   1. `ollama pull mistral-nemo`
   2. `ollama pull qwen2.5`
   3. `ollama pull gemma3`
3. Add API keys in `api-keys/`: `ollama.env`, `openweather.env`, and `tomtom.env`.
4. Configure Terraform + AWS: set AWS credentials in your shell for the target account; update the S3 backend in `terraform/terraform.tf`; set latitude/longitude for weather + traffic sampling
5. Deploy infrastructure: `cd terraform && terraform init`, then `terraform apply`
