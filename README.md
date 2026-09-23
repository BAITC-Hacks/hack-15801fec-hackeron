# «Аким на 5 часов» — симулятор городских решений

Dependency-free Python simulator for the Hackeron task. A user allocates one virtual
budget among **exactly five** city initiatives and receives an auditable **Astana
Quality of Life Score**: city-wide performance, the weakest district, and unresolved
critical indicators all affect the result.

The simulator deliberately separates responsibilities:

- rules and scoring are deterministic, local, and testable;
- the terminal UI only collects and renders decisions—it never recalculates results;
- the AI explanation layer receives the supplied `ScoreResult` audit trail without
  inventing numbers; it has an offline fact-grounded fallback and an injectable LLM adapter.

## Quick start

Requires Python 3.10+; no packages, API keys, or network access are needed.

```bash
git clone https://github.com/BAITC-Hacks/hack-15801fec-hackeron.git
cd hack-15801fec-hackeron
python -m src.app
```

The interactive UI is in Russian to match the task. It prints the catalogue and
accepts five entries:

- district initiative: `M7:nura`
- city-wide initiative: `M12`

District IDs are `esil`, `almaty`, `saryarka`, `baikonur`, and `nura`. IDs are
case-insensitive. The UI shows a running cost, then either validation errors or the
score and the change in every affected district.

### Reproducible reference walkthrough

Enter these five lines when prompted:

```text
M7:nura
M8:nura
M10:nura
M12
M5:saryarka
```

This is the valid reference scenario from the brief. It costs **95/100** and produces:

```text
Astana Quality of Life Score: 56.54 (+3.99 к базе)
Среднее по городу: 58.08; слабейший район: 52.96; критических значений: 0
```

The small difference between 56.54 and the brief's `≈ 56.5` is only displayed
precision. The exact computed value is 56.54307.

## Verify

Run all unit and golden tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p '*_test.py' -v
```

Tests verify the source baseline (**52.55768**, shown as 52.56), the reference set,
lag scaling, non-lag-scaled synergy, score order-independence, invalid-set behaviour,
and CLI parsing/rendering.

## Rules modelled

A set is rejected if it violates any source rule:

1. cost exceeds 100;
2. it does not contain exactly five decisions;
3. a measure is repeated;
4. a district measure has no valid district, or a city measure has one;
5. more than two measures share a direction;
6. it contains an incompatible pair (`M1/M3`, `M4/M7` in one district, or `M5/M13` in one district).

An invalid set has no score—not a score of zero—and receives all applicable reasons.

For a valid set, each full measure effect is multiplied by `(8 − lag) / 8`; effects
are clipped to 0…100. Fixed bonuses for `M1+M2`, `M10+M12`, and `M5+M6` are applied
without lag scaling. The engine then calculates:

```text
D_d   = Σ(weight[indicator] × indicator_after)
D_avg = Σ(population_share[district] × D_d)
Score = 0.7 × D_avg + 0.3 × min(D_d) − N_crit
```

`N_crit` is the number of district–indicator pairs strictly below 40 after all
effects. All weights, lags, costs, synergies, and constraints live in data files, not
in UI code.

## Project layout

```text
data/                  source-traceable districts, measures, and scoring rules
src/data/              dependency-free JSON loader and typed dataset
src/validator/         selection-rule validation
src/engine/            pure score calculation and result audit trail
src/solver/            optional exhaustive valid-scenario ranking
src/app/               Russian CLI (`python -m src.app`)
tests/                 validator, scoring, and UI tests
INSTRUCTIONS.md        merged, readable hackathon brief and complete source tables
task/original/         immutable original .docx documents
task/txt/              source document text conversions
DOCUMENTATION.md       source provenance, checksums, and conversion notes
```

## Data provenance and extensibility

Every machine-readable value in `data/` is transcribed from Part II of
[`INSTRUCTIONS.md`](INSTRUCTIONS.md). The original documents and their checksums are
documented in [`DOCUMENTATION.md`](DOCUMENTATION.md). `load_dataset()` validates the
expected number of districts, measures, indicators, population total, and effect
keys before returning immutable dataclasses.

`src.engine.ScoreResult` is a complete calculation audit: per-district before/after
scores, per-indicator deltas, budget, aggregate metrics, critical count, final score,
and each lag-scaled effect or synergy. `src.ai.explain()` renders a local
fact-grounded Russian narrative by default; pass a callable or a provider adapter with
`complete(prompt)` to use an LLM. The generated prompt contains only these computed
facts and explicitly forbids arithmetic or invented numbers.

## Optional scenario ranking

The solver evaluates every valid five-decision scenario with the canonical validator
and compact engine path, then constructs full audit results only for the leaders. It
is intentionally exhaustive and may take tens of seconds on a typical laptop:

```python
from src.data import load_dataset
from src.solver import rank_scenarios

for scenario in rank_scenarios(load_dataset(), limit=3):
    print(scenario.result.score, scenario.selection)
```

## Current scope

The deterministic simulator, fact-grounded analysis, playable CLI, and optional
scenario ranker are ready. Next planned enhancements are a provider-specific LLM
adapter and richer visualisation.
