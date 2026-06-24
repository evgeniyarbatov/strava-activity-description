# Setup

## Python

```bash
make install
```

Creates `.venv/` and installs `requirements.txt`. Scripts run from the repo root as `python -m scripts.<module>`.

## API keys

```bash
cp ollama.env.sample ollama.env
cp openweather.env.sample openweather.env
cp tomtom.env.sample tomtom.env
```

| File | Used by |
|------|---------|
| `ollama.env` | `scripts/describe.py` — `API_KEY` for Ollama Cloud; optional `REFLECTION_MODEL` (default `gemini-3-flash-preview`) |
| `openweather.env` | Terraform Lambda — `OPENWEATHER_API_KEY` |
| `tomtom.env` | Terraform Lambda — `TOMTOM_API_KEY` |

Real `.env` files are gitignored.

## Ollama

Pull local models used as fallbacks or alternatives to cloud models:

```bash
ollama pull mistral-nemo
ollama pull qwen2.5
ollama pull gemma3
```

Local models connect to `http://localhost:11434` by default. Cloud models use `https://api.ollama.com`.

## Weather and traffic (AWS)

`scripts/weather_traffic.py` reads hourly samples from DynamoDB. The Lambda that writes them is provisioned by Terraform.

1. Set AWS credentials in your shell.
2. Update the S3 backend in `terraform/terraform.tf`.
3. Set `latitude` and `longitude` in `terraform/variables.tf` for your running location.
4. Deploy:

```bash
cd terraform && terraform init && terraform apply
```

Or from the repo root: `make deploy` (runs tests first).

See [terraform/README.md](../terraform/README.md) for Lambda schedule and DynamoDB details.

## City OSM data

POI enrichment needs a clipped city extract. Install `wget`, `osmconvert`, and `osmium`, then set `BOUNDARY_POLY` in the `Makefile` to your city's polygon in `osm/`:

```bash
make country   # downloads vietnam-latest.osm.pbf (or change OSM_URL)
make city      # writes osm/city.osm.pbf and osm/city.osm
```

Override the boundary for another city:

```bash
make city BOUNDARY_POLY=osm/your-city.poly
```

## Goals

Edit `goals.json` with your personal distance (meters) and moving-time (seconds) targets. `scripts/context.py` uses these to pick distance and duration adjectives relative to your norms.

## Per run

1. Update `goals.json` if needed.
2. Drop matching GPX and TCX files into `data/raw`.
3. `make analyze` — merges, enriches, and writes `data/activities/*.json`.
4. `make reflect` — writes `journal/YYYY-MM-DD.md` (skips dates that already have a file).