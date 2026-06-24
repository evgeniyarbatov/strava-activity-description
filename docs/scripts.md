# Scripts

All modules live under `scripts/` and run from the repo root:

```bash
.venv/bin/python -m scripts.<module>
```

Or via `make analyze` / `make reflect`. Shared helpers are in `scripts/utils.py`.

---

## merge.py

**Purpose:** Combine TCX heart-rate and cadence samples with GPX location tracks.

**Input:** `data/raw/*.gpx`, `data/raw/*.tcx`

**Output:** `data/gpx/<uuid>.gpx` — one merged file per matched TCX

**How it works:**

1. Parse each TCX into a timestamp → `(heart_rate, cadence)` map.
2. For each TCX, find the first GPX file that shares any timestamp keys.
3. Filter GPX points to those present in the TCX map.
4. Write a new GPX with `gpxtpx:TrackPointExtension` elements carrying `hr` and `cad` on matching trackpoints.

Output filenames are deterministic UUIDs derived from the TCX filename (`uuid.uuid5`). Each GPX file is consumed by at most one TCX match. Skips output if the target file already exists.

GPX files without a matching TCX are ignored. TCX files without a matching GPX are skipped silently.

---

## activity.py

**Purpose:** Parse merged GPX tracks into Strava-shaped activity JSON.

**Input:** `data/gpx/*.gpx`

**Output:** `data/activities/<stem>.json`

**How it works:**

1. Parse trackpoints (lat, lon, time, optional ele/hr/cad).
2. Compute total distance via geopy haversine between consecutive points.
3. Set `moving_time` as seconds from first to last timestamp.
4. Simplify the track with Shapely (`SIMPLIFY_DISTANCE_M = 10`) and encode as a Google polyline.
5. Write payload with `start_date` (UTC Zulu), `start_date_local` (local time with Z suffix), `distance` (meters, int), `moving_time`, and `map.polyline`.

Skips GPX files whose output JSON already exists.

---

## weather_traffic.py

**Purpose:** Attach weather and traffic context from DynamoDB to each activity.

**Input:** `data/activities/*.json`, DynamoDB table `run-reflection-context`

**Output:** Same files, with `weather` and `traffic` arrays added

**How it works:**

1. For each activity, derive the run date and hour window (`start_hour` through `end_hour`, inclusive, plus one hour buffer).
2. Scan DynamoDB for all items on that date.
3. Filter items by hour range and `context` field (`weather` or `traffic`).
4. Map raw API values to expressive text:
   - **Weather** — `feels_like` temperature (°C) → bucketed phrases via `feels_like_description()`.
   - **Traffic** — `currentSpeed / freeFlowSpeed` ratio → bucketed phrases via `traffic_description()`.
5. Write arrays of `{description, feels_like}` (weather) or `{description}` (traffic).

Skips enrichment for fields already present on the payload. Requires AWS credentials configured for boto3.

Weather/traffic samples are written by the Terraform Lambda on a morning schedule. If no items exist for the run date, arrays will be empty.

---

## uniqueness.py

**Purpose:** Score how different today's route is compared to all other activities in the batch.

**Input:** `data/activities/*.json`

**Output:** Same files, with `uniqueness.description` added

**How it works:**

1. Build a reference vector per activity: decode polyline → simplify at 35 m → z-score lat/lon separately → pad/trim to 48 points → concatenate into a 96-dim vector.
2. Also store centroid (mean lat/lon) and distance in meters.
3. For each activity, compute combined distance to every other activity:
   - L2 norm between route vectors
   - Plus `DISTANCE_WEIGHT` (0.35) × z-scored distance difference
   - Plus `CENTROID_WEIGHT` (0.2) × z-scored centroid offset
4. Raw score from median ratio of minimum distance to median distance.
5. Normalize all raw scores in the batch to [1, 100], then map to one of 16 words (`mundane` … `ultra`).

Skips activities that already have a `uniqueness` key. With only one activity in the batch, no score is written.

---

## context.py

**Purpose:** Derive human-readable distance, duration, and time-of-day context from goals.

**Input:** `data/activities/*.json`, `goals.json`

**Output:** Same files, with `activity_context` added

**How it works:**

1. Load personal goals (`distance` in meters, `moving_time` in seconds).
2. For each activity, compute `value / goal` ratio and index into ordered word lists:
   - Distance: `minuscule` … `ultra` (24 words)
   - Moving time: `fleeting` … `never-ending` (24 words)
3. Pick a random time-of-day phrase from hour windows (deep night, dawn, morning, midday, afternoon, early evening, evening, late night).

Only writes `activity_context` when the key is missing. `time_of_day_description` is randomized on each run — the same hour may get different wording.

---

## poi.py

**Purpose:** Tag which OSM point-of-interest categories appear along the run corridor.

**Input:** `data/activities/*.json`, `osm/city.osm`

**Output:** Same files, with `geo.points_of_interest` added

**How it works:**

1. Stream-parse OSM XML for nodes and ways matching `POI_TAGS` (water, waterway, natural, leisure, landuse categories).
2. For ways, compute centroid of node refs (polygon if closed, line otherwise).
3. Decode activity polyline → convex hull → buffer 20 m in local UTM (pyproj).
4. Collect unique category labels for POIs inside the buffered hull.
5. Store sorted list under `geo.points_of_interest` (underscores replaced with spaces).

Requires `make city` to produce `osm/city.osm` first. Activities without a polyline get an empty list.

---

## describe.py

**Purpose:** Generate the multi-lens journal reflection via CrewAI.

**Input:** Fully enriched `data/activities/*.json`

**Output:** `journal/YYYY-MM-DD.md`

**How it works:**

1. **`prompt_inputs()`** — aggregate weather (most common feels_like, unique condition strings), traffic, context adjectives, POI list, uniqueness word; reverse-geocode route midpoint for `city_name` and `country`.
2. **`render_activity_context()`** — fill `prompts/activity-context.txt` template.
3. **`run_perspectives()`** — for each of nine lenses, load YAML configs, inject a random variation prompt, run agent task chain, collect one-line perspective.
4. **`run_synthesis()`** — pass perspectives block to synthesis agents for Afterglow, Tensions, Residue.
5. **`build_reflection()`** — assemble formatted markdown.

Skips activities whose journal file already exists. Model from `REFLECTION_MODEL` env var or default local model (`mistral-nemo`).

### Prompt configs

| Lens | Directory |
|------|-----------|
| Artist | `prompts/artist/` |
| Monk | `prompts/buddhist-monk/` |
| Memory | `prompts/memory/` |
| Scientist | `prompts/scientist/` |
| Cartographer | `prompts/cartographer/` |
| Physiologist | `prompts/physiologist/` |
| Archivist | `prompts/archivist/` |
| Dreamer | `prompts/dreamer/` |
| Contrarian | `prompts/contrarian/` |
| Synthesis | `prompts/synthesis/` |

Each lens directory has `agents.yaml` and `tasks.yaml`. Tasks typically draft then revise; synthesis tasks read the full perspectives block.

---

## utils.py

**Purpose:** Shared helpers used across the pipeline.

| Function | Role |
|----------|------|
| `parse_iso()` | Parse ISO 8601 timestamps; accepts trailing `Z` |
| `load_json()` / `write_json()` | UTF-8 JSON I/O with stable indentation |
| `load_env()` | Load dotenv file (used by `describe.py` for `ollama.env`) |

No `main()` — import only.