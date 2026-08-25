# Roadmap

## North Star

This project is not a Strava caption generator. The goal is to **enrich the experience of running** — to surface dimensions of a run that consciousness misses, forgets, or smooths over.

When you run, you live inside a narrow band of attention: breath, rhythm, the next turn, a fleeting mood. The data remembers differently. It holds the shape of the route against every prior route. It knows where your heart rate climbed while your mind was elsewhere. It sees the city waking up in traffic patterns you only felt as background noise. These are not better truths than lived experience. They are **different truths**, and different truths pull in different directions. That tension is the point.

The output should not quantize the run into metrics and labels. It should **pull at the subconscious** — fragments, images, contradictions, questions — so that new ideas can emerge after the run is over. You read something days later and remember a corner you did not notice, or feel a run differently than you did at the finish.

---

## Connects to

This is the deepest instance of a pattern that shows up across the portfolio: turn a personal data trace into a second, non-literal reading of an experience — data as a set of eyes you don't have while it's happening.

- **[private]** — its own description already calls itself a "companion spirit to gpx-art"; it's an even closer companion to this repo, since it's also built from morning runs and also aims at something abstract and felt rather than measured. Worth asking whether a run could eventually get both a visual ([private]) and a written (run-reflection) second-pass from the same GPX + footage.
- **[private]** — same instinct (capture what the conscious mind drops during a run) through a different channel, voice instead of data enrichment. Could plausibly become a tenth "lens" here, or run-reflection could pull transcribed audio in as raw material for the archivist/memory personas.
- **[private]** — same technique (LLM reading external signal for insight into a state of mind) applied to photographs instead of runs; the anti-quantization principles here (words over numbers, disagreement over consensus) are a rubric that repo doesn't have yet.
- **[private]** — mines LLM chat history for self-knowledge; run-reflection mines runs. Both are instances of "build a corpus of yourself and read it back for what you missed," and the private-ranking idea in Phase 6 here is exactly the kind of calibration loop [private]' analysis pipeline could reuse.
- **[private]**, **[private]** — narrower, single-effect versions of the same underlying move (physical sensation → a legible artifact); good places to test whether a technique proven here generalizes, before adding a tenth lens to this repo's already-rich set.

## What Exists Today

**What works:**

- **Nine lenses, private journal tone.** Artist, monk, memory, scientist, cartographer, physiologist, archivist, dreamer, contrarian — each reads the same activity through a different ethic. Goals are reframed as readers of the run, not Strava caption writers.
- **Anti-quantization in the data layer.** Weather, traffic, distance, and duration are translated into words (`"protracted"`, `"blissfully unimpeded flow"`, `"notable"`) before they reach the model. Raw numbers are deliberately kept out of most prompts.
- **Route memory.** Uniqueness scoring compares today's path against your history — a perspective you cannot hold in your head across hundreds of runs.
- **Environmental context.** POI categories, time-of-day phrases, and sampled weather/traffic add layers you may not have consciously registered.
- **Controlled variation.** Variation prompts introduce structural constraints that keep outputs from converging on the same generic running prose.
- **Journal output.** Dated files in `journal/YYYY-MM-DD.md` (one section per lens).
- **One command.** Drop GPX into `data/raw`, run `make` — enrichment then reflection.

**Gaps:**

- Output is still a stack of perspective sections — no Afterglow / Tensions / Residue synthesis.
- HR, cadence, elevation, and pace are in GPX but stripped before enrichment; the physiologist lens infers from duration/weather only.
- No temporal arc beyond uniqueness: each run is mostly isolated from longer story.
- No private ranking of what lingered (model, lens, or phrase).

---

## Principles Going Forward

1. **Enrich, don't report.** Prefer one strange true detail over a complete summary. Prefer a question over an answer.
2. **Perspectives should disagree.** If the monk and the scientist say the same thing in different words, something failed. Each lens should notice what the others ignore.
3. **Data is a viewpoint, not a verdict.** Uniqueness is not a grade. Heart rate drift is not a judgment. They are invitations to look again.
4. **Subconscious over summary.** Optimize for what lingers — an image, a phrase, a mismatch — not for accuracy of coverage.
5. **Private by default.** This is a journal between you and your runs, not content for an audience.

---

## Done: Reframe the Output

*Shift from "pick a description" to "receive a constellation of perspectives."*

- Personas re-aimed as private-journal readers (not Strava writers).
- Lenses added: cartographer, physiologist, archivist, dreamer, contrarian.
- Post-run deliverable: `journal/YYYY-MM-DD.md` via bare `make`.

Still open from this phase: Afterglow / Tensions / Residue format (see Synthesis below).

---

## Phase 2: Unlock the Body-Data Perspective

*HR, cadence, elevation, and pace are in the files but not in the story.*

### 2.1 Extract physiological episodes

From GPX (and TCX if added), derive **episodes** rather than aggregates:

- Where heart rate rose fastest (effort you may not have registered)
- Where cadence steadied or broke (rhythm as meditation or struggle)
- Elevation changes correlated with pace shifts (the hill you thought was nothing)
- A "drift index" — how much the second half differed from the first in pace and HR

Translate these into language, not numbers: `"a long quiet middle"`, `"effort arriving late"`, `"cadence held when pace did not"`.

### 2.2 Felt vs. measured gaps

The most interesting material lives in **disagreement between body-data and context**:

- Easy morning, but HR says otherwise
- New route, but pace identical to your Tuesday loop
- Monk-calm weather, physiologist-spiky heart rate

Add a dedicated enrichment step (`scripts/physiology.py`) so the physiologist and contrarian lenses can specialize in these gaps.

### 2.3 Rhythm as texture

Cadence and pace variance can describe **texture** — choppy, gliding, mechanical, searching — without ever stating SPM or min/km. This is data serving sensation, not replacing it.

---

## Phase 3: Temporal Memory

*A single run is a sentence in a longer book.*

### 3.1 Run-to-run narrative

With enough history, the archivist lens can surface:

- Routes you keep returning to vs. routes you try once
- Seasonal patterns (same park, different light, different effort)
- Distance and duration drift over weeks — not as training metrics, but as life rhythm

### 3.2 What you keep forgetting

Track which POI categories, weather conditions, and route shapes appear most often but are **rarely mentioned** in generated reflections. These are candidates for prompts that deliberately surface the invisible background of your running life.

### 3.3 Milestone runs without milestones

Detect runs that are unremarkable by numbers but remarkable by position in history — your 100th run past a particular lake, the first dawn run after a gap, a route that closes a loop you opened months ago. Not achievements. **Continuity markers.**

---

## Phase 4: Synthesis and Emergence

*Let the perspectives talk to each other.*

### 4.1 Structured reflection format

```
── Afterglow ──────────────────────────
[2–3 sentences. Not a summary. An opening image or question.]

── Perspectives ─────────────────────
Monk:      ...
Memory:    ...
[Each 1–2 sentences. Deliberately incomplete.]

── Tensions ─────────────────────────
[Where perspectives disagree. This section is the most valuable one.]

── Residue ──────────────────────────
[One line to carry. No attribution. Yours to misremember.]
```

### 4.2 Tension extraction

After all personas generate, a synthesis pass that:

1. Identifies where outputs agree (often boring — the obvious reading)
2. Identifies where they disagree (the interesting reading)
3. Produces the `Tensions` section from disagreements only

Lightweight second-pass agent whose sole job is to find friction, not resolve it.

### 4.3 Residue generation

A final pass that reads all perspectives and the tensions, then outputs **one line with no attribution** — something that could have come from any of the lenses or from none of them. Designed to be misremembered. Designed to pull.

### 4.4 Controlled surprise

Introduce occasional **wild cards** — a prompt that must use a random POI, a weather phrase, or a physiological episode as the *only* subject of the reflection. Not every run. Enough to break habit.

---

## Phase 5: Sensory Expansion

*More dimensions, still not more metrics.*

### 5.1 Micro-geography

Beyond POI categories, describe **transitions** — forest to garden to lake, open to enclosed, quiet corridor to traffic edge. The run as a sequence of rooms, not a list of tags.

### 5.2 Sound and light (inferred)

From time of day, weather, traffic, and tree cover (OSM), infer ambient qualities without claiming precision: `"filtered light"`, `"engine-dampened"`, `"bird-hour"`. Always hedged. Always suggestive.

### 5.3 Seasonal and cultural context

Optional enrichment from calendar and location — Tet preparations, monsoon approaching, the week the jacarandas bloom. Only when grounded in real external data, never invented.

---

## Phase 6: Personal Calibration

*Learn what pulls for you, not what scores well.*

### 6.1 Private ranking

After reading a reflection, mark what lingered — not "best model" but "what stayed with me." Over time, this trains which lenses, variation prompts, and data dimensions deserve more weight — without turning the project into an optimization loop.

Optional offline eval set: prompts, outputs, raw activity data, and your rankings, so you can compare models and prompt shapes deliberately (exportable as a private dataset if useful).

### 6.2 Prompt evolution from your reactions

Periodically review rankings and adjust persona backstories, variation weights, and which data fields each lens receives. The system should drift toward **your** subconscious, not generic good prose.

### 6.3 Anti-goals

Explicitly avoid:

- Leaderboards, PRs, training load scores
- Outputs that sound like they belong on Strava, Instagram, or a race report
- Convergence — if every model and persona start sounding the same, increase variation and disagreement

---

## What This Is Not

- A training dashboard
- A social media content tool
- A way to describe runs more accurately
- A replacement for the felt experience of running

It is a **second pass** on your own experience — one that uses data as a set of eyes you do not have while you are moving.

---

## Near-Term Next Steps

Ordered by impact and proximity to existing code:

1. **Synthesis pass** — Afterglow / Tensions / Residue in `describe.py` from the nine perspectives.
2. **`scripts/physiology.py`** — extract HR/cadence/pace episodes from GPX; bucket into language; feed physiologist/contrarian.
3. **Archivist depth** — leverage uniqueness and run history for temporal narrative beyond a single uniqueness word.
4. **Private ranking** — simple annotation for what lingered (JSON or markdown beside the journal).

---

## Open Questions

- Should any perspective be allowed to be **wrong** — to hallucinate mood or memory — if it produces a true feeling?
- How much delay between run and reflection is ideal? Same evening? Next morning? After the next run?
- Is there value in re-reading old reflections before a new run, or does that break the subconscious pull?
- When perspectives agree completely, is that a signal to inject more wild-card variation next time?

These are worth answering through use, not upfront design.
