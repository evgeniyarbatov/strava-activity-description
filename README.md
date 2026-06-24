# Run Reflection

Enrich the experience of running — surface dimensions of a run that consciousness misses, forgets, or smooths over.

Each run becomes a private reflection: multiple perspectives that disagree, tensions between them, and one line to carry.

> **Monk:** The overcast sky filters light through trees, casting a calm on the streets. Each step mirrors breath and movement, each moment fleeting yet clear.
>
> **Contrarian:** You will call this an easy morning; the duration says otherwise.

## Quick start

```bash
make install
cp ollama.env.sample ollama.env   # optional REFLECTION_MODEL override
make country && make city         # one-time OSM setup
make analyze                      # enrich activities from data/raw
make reflect                      # write journal/YYYY-MM-DD.md
```

Drop matching GPX and TCX files into `data/raw` before `make analyze`. First-time setup also requires Ollama models, AWS/Terraform for weather/traffic context, and API keys — see [docs/setup.md](docs/setup.md).

## Documentation

- [Architecture](docs/architecture.md) — pipeline, data flow, activity payload, prompts, infrastructure
- [Scripts](docs/scripts.md) — what each module does and how it works
- [Setup](docs/setup.md) — full first-time configuration

## Commands

| Command | Purpose |
|---------|---------|
| `make install` | Create venv and install dependencies |
| `make country` | Download country OSM extract |
| `make city` | Clip extract to city boundary → `osm/city.osm` |
| `make analyze` | Run enrichment pipeline |
| `make reflect` | Generate journal reflection |
| `make test` | Run pytest |
| `make deploy` | Run tests, then `terraform apply` |