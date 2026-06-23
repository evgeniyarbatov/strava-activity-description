# Roadmap

## North Star

This project is not a Strava caption generator. The goal is to **enrich the experience of running** — to surface dimensions of a run that consciousness misses, forgets, or smooths over.

When you run, you live inside a narrow band of attention: breath, rhythm, the next turn, a fleeting mood. The data remembers differently. It holds the shape of the route against every prior route. It knows where your heart rate climbed while your mind was elsewhere. It sees the city waking up in traffic patterns you only felt as background noise. These are not better truths than lived experience. They are **different truths**, and different truths pull in different directions. That tension is the point.

The output should not quantize the run into metrics and labels. It should **pull at the subconscious** — fragments, images, contradictions, questions — so that new ideas can emerge after the run is over. You read something days later and remember a corner you did not notice, or feel a run differently than you did at the finish.

---

## What Exists Today

The current pipeline already gestures toward this vision, even if the framing still says "Strava description."

**What works:**

- **Multiple lenses.** Artist, monk, memory, scientist — each persona reads the same activity through a different ethic. The monk notices impermanence; the memory-writer selects one detail and lets omission do the work; the scientist states what happened without metaphor. These viewpoints genuinely disagree about what matters.
- **Anti-quantization in the data layer.** Weather, traffic, distance, and duration are translated into words (`"protracted"`, `"blissfully unimpeded flow"`, `"notable"`) before they reach the model. Raw numbers are deliberately kept out of most prompts.
- **Route memory.** Uniqueness scoring compares today's path against your history — a perspective you cannot hold in your head across hundreds of runs.
- **Environmental context.** POI categories, time-of-day phrases, and sampled weather/traffic add layers you may not have consciously registered.
- **Controlled variation.** `VARIATION_PROMPTS` introduce structural constraints (single sensory detail, no adjectives, juxtaposition) that prevent the outputs from converging on the same generic running prose.

**What still anchors the wrong goal:**

- Agent goals and the personality editor are explicitly tuned for "Strava activity descriptions."
- The deliverable is a markdown grid of model × persona one-liners — useful for comparison, but shaped like copy-paste candidates.
- HR, cadence, elevation, and pace dynamics are captured in GPX/TCX but **stripped out** before enrichment. The body-data perspective is missing entirely.
- There is no synthesis step — the perspectives sit side by side but do not argue, resonate, or surprise each other.
- No temporal arc: each run is treated in isolation, not as part of a longer story your body and routes are telling.

---

## Principles Going Forward

1. **Enrich, don't report.** Prefer one strange true detail over a complete summary. Prefer a question over an answer.
2. **Perspectives should disagree.** If the monk and the scientist say the same thing in different words, something failed. Each lens should notice what the others ignore.
3. **Data is a viewpoint, not a verdict.** Uniqueness is not a grade. Heart rate drift is not a judgment. They are invitations to look again.
4. **Subconscious over summary.** Optimize for what lingers — an image, a phrase, a mismatch — not for accuracy of coverage.
5. **Private by default.** This is a journal between you and your runs, not content for an audience.

---

## Phase 1: Reframe the Output

*Shift from "pick a description" to "receive a constellation of perspectives."*

### 1.1 Rename and re-aim the personas

Keep the existing lenses but rewrite their goals. They are **readers of your run**, not writers for Strava. The personality editor should preserve your voice without polishing for public performance.

Candidate additions — each one a different direction to pull:

| Lens | What it sees that you don't |
|------|----------------------------|
| **Cartographer** | The route as geometry — loops, detours, places where you almost turned back |
| **Physiologist** | The body as instrument — where effort spiked, where it went quiet, mismatches between felt ease and measured load |
| **Archivist** | This run against your history — "you have passed this lake 14 times; today you went the long way" |
| **Dreamer** | Free association from POI and weather — not factual, but true to mood |
| **Contrarian** | Argues against your likely self-narrative ("you will call this easy; the second half says otherwise") |

### 1.2 Change the deliverable format

Instead of a flat list of one-liners, produce a **run reflection** structured for slow reading:

```
── Afterglow ──────────────────────────
[2–3 sentences. Not a summary. An opening image or question.]

── Perspectives ─────────────────────
Monk:      ...
Memory:    ...
Scientist: ...
[Each 1–2 sentences. Deliberately incomplete.]

── Tensions ─────────────────────────
[Where perspectives disagree. "The data says routine; the monk says new."
 This section is the most valuable one.]

── Residue ──────────────────────────
[One line to carry. No attribution. Yours to misremember.]
```

The `Residue` line is the only thing that might ever go anywhere public — and only if you want it to.

### 1.3 Post-run, not pre-post

The reflection should be read **after** the run, ideally hours later or the next morning. Consider a simple `make reflect` that generates output into a dated journal directory (`journal/2026-03-15.md`) rather than alongside activity IDs.

---

## Phase 2: Unlock the Body-Data Perspective

*HR, cadence, elevation, and pace are in the files but not in the story.*

### 2.1 Extract physiological episodes

From the merged GPX/TCX, derive **episodes** rather than aggregates:

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

Add a dedicated enrichment step (`scripts/physiology.py`) and a `physiologist` or `contrarian` lens that specializes in these gaps.

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

### 4.1 Tension extraction

After all personas generate, run a synthesis step that:

1. Identifies where outputs agree (often boring — the obvious reading)
2. Identifies where they disagree (the interesting reading)
3. Produces the `Tensions` section from disagreements only

This can be a lightweight second-pass agent whose sole job is to find friction, not resolve it.

### 4.2 Residue generation

A final pass that reads all perspectives and the tensions, then outputs **one line with no attribution** — something that could have come from any of the lenses or from none of them. Designed to be misremembered. Designed to pull.

### 4.3 Controlled surprise

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

Extend the TODO idea: after reading a reflection, mark what lingered. Not "best model" but "what stayed with me." Over time, this trains which lenses, variation prompts, and data dimensions deserve more weight — without turning the project into an optimization loop.

### 6.2 Prompt evolution from your reactions

Periodically review your rankings and adjust persona backstories, variation weights, and which data fields each lens receives. The system should drift toward **your** subconscious, not generic good prose.

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

1. **Rewrite persona goals** — remove Strava framing; aim each lens at a distinct perceptual blind spot.
2. **Add `scripts/physiology.py`** — extract HR/cadence/pace episodes from merged GPX; bucket into language.
3. **Restructure output** — Afterglow / Perspectives / Tensions / Residue format in `describe.py`.
4. **Add synthesis pass** — tension extraction and residue generation as final CrewAI tasks.
5. **Journal output** — dated files in `journal/` instead of (or in addition to) activity-ID markdown.
6. **Archivist lens** — leverage uniqueness and run history for temporal narrative.
7. **Private ranking** — simple JSON or markdown annotation for what lingered.

---

## Open Questions

- Should any perspective be allowed to be **wrong** — to hallucinate mood or memory — if it produces a true feeling?
- How much delay between run and reflection is ideal? Same evening? Next morning? After the next run?
- Is there value in re-reading old reflections before a new run, or does that break the subconscious pull?
- When perspectives agree completely, is that a signal to inject more wild-card variation next time?

These are worth answering through use, not upfront design.