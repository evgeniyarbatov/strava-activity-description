# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history.

#### Artistic

> In Hà Nội's gentle morning drizzle, legs slice through dew-kissed streets, breeze whispering past ears as clouds shift overhead.

#### Monk

> As I begin my run under the gentle caress of the dew-kissed morning, the light rain whispers softly against my skin, reminding me of the transient nature of all things.

#### Memory

> The rain had softened to a drizzle, barely kissing my cheeks as I ran. A lone bicycle bell chimed behind me, its sound swallowed by the dampened morning.

#### Scientist

> Initiating run at 07:04 in Hà Nội, Vietnam; conditions: light rain, overcast clouds. Duration expeditious, no significant conversation exchanged throughout the compact route.

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
- Uniqueness compares z-scored raw lat/lon samples plus distance and uses per-batch normalization to map scores into descriptive words.
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
