# Run Reflection

Enrich the experience of running — surface dimensions of a run that consciousness misses, forgets, or smooths over.

Each run becomes a private reflection: multiple perspectives that disagree, tensions between them, and one line to carry.

> **Monk:** The overcast sky filters light through trees, casting a calm on the streets. Each step mirrors breath and movement, each moment fleeting yet clear.
>
> **Contrarian:** You will call this an easy morning; the duration says otherwise.

## Quick start

```bash
# one-time (see docs/setup.md)
make install
make country && make city

# every run
# 1. drop GPX into $DATA_DIR/raw (default: ~/data/run-reflection/raw)
make
# → $DATA_DIR/journal/YYYY-MM-DD.md (default: ~/data/run-reflection/journal)
```

`make` runs the full pipeline: parse GPX, enrich (weather, traffic, uniqueness, context, POI), then write the journal reflection. Steps are idempotent — re-running is safe.

Generated/enriched data and the journal are written outside the repo, under `DATA_DIR` (default `$DATA_ROOT/run-reflection`, `DATA_ROOT` default `~/data`). Override per-run with `make <target> DATA_ROOT=/path/to/shared` or `make <target> DATA_DIR=/tmp/run-42`.

First-time setup also needs Ollama models, AWS/Terraform for weather/traffic context, and API keys — see [docs/setup.md](docs/setup.md).

## Documentation

- [Architecture](docs/architecture.md) — pipeline, data flow, activity payload, prompts, infrastructure
- [Scripts](docs/scripts.md) — what each module does and how it works
- [Setup](docs/setup.md) — full first-time configuration

## Commands

| Command | Purpose |
|---------|---------|
| `make` | Full pipeline: GPX → journal |
| `make analyze` | Enrichment only (`$DATA_DIR/activities/`) |
| `make reflect` | Analyze + journal reflection |
| `make install` | Create venv and install dependencies |
| `make country` / `make city` | One-time OSM setup |
| `make test` | Run pytest |
| `make deploy` | Run tests, then `terraform apply` |
