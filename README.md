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
# 1. drop GPX into data/raw
make
# → journal/YYYY-MM-DD.md
```

`make` runs the full pipeline: parse GPX, enrich (weather, traffic, uniqueness, context, POI), then write the journal reflection. Steps are idempotent — re-running is safe.

First-time setup also needs Ollama models, AWS/Terraform for weather/traffic context, and API keys — see [docs/setup.md](docs/setup.md).

## Documentation

- [Architecture](docs/architecture.md) — pipeline, data flow, activity payload, prompts, infrastructure
- [Scripts](docs/scripts.md) — what each module does and how it works
- [Setup](docs/setup.md) — full first-time configuration

## Commands

| Command | Purpose |
|---------|---------|
| `make` | Full pipeline: GPX → journal |
| `make analyze` | Enrichment only (`data/activities/`) |
| `make reflect` | Analyze + journal reflection |
| `make install` | Create venv and install dependencies |
| `make country` / `make city` | One-time OSM setup |
| `make test` | Run pytest |
| `make deploy` | Run tests, then `terraform apply` |
