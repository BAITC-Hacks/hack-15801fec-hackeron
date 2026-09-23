# STRUCTURE_PLAN — general structure plan

**Status:** draft for agents, not yet implemented. Nothing in this file is code; it is the
shared map that parallel agents claim scopes against.
**Source of truth for requirements and data:** `INSTRUCTIONS.md` (root).
**Owner:** whoever claims `agents/**` — announce changes in `AGENT_CHAT.md` first.

---

## 1. Goal

A working simulator for the «Аким на 5 часов» task: every team starts from the same
budget (100) and the same district dataset, makes **exactly 5** decisions from a catalogue
of 14 measures, and receives an **Astana Quality of Life Score** plus an AI-generated
explanation of the result, its trade-offs and risks (`INSTRUCTIONS.md`, Part I).

Two hard separations drive the whole structure:

1. **Numbers are computed deterministically in code.** The `Score` formula, lag scaling,
   synergies and the critical-value penalty are pure functions (`INSTRUCTIONS.md`,
   Part II §3).
2. **The LLM explains, it does not calculate.** The AI layer receives already-computed
   deltas, per-measure contributions and validation results, and turns them into prose,
   comparisons and recommendations. It must never invent or recompute a number.

## 2. Scope and non-goals

In scope (must-have, per Part I): single shared budget, 5 decisions across the 5
directions, budget enforcement, AI analysis, `Score` calculation, explanation of
strengths/risks/consequences.

Out of scope for the first milestone (optional, per Part I): multi-team comparison,
unexpected-event simulation, automatic presentation generation. These should be
*possible* to add later without restructuring — that is what the layering below buys us.

## 3. Target repository layout

Planned shape (names are a proposal to be pinned in `AGENT_CHAT.md` before coding):

```
.
├── AGENTS.md               # coordination protocol (exists)
├── AGENT_CHAT.md           # append-only agent log (exists)
├── DOCUMENTATION.md        # repo/provenance docs (exists)
├── INSTRUCTIONS.md         # merged task instructions (exists)
├── README.md               # human entry point: what it is, how to run it
├── agents/                 # agent-facing working docs (this folder)
│   ├── README.md           # purpose + index of agent files
│   ├── STRUCTURE_PLAN.md   # this file
│   └── ...                 # later: interface notes, decision records, workstream logs
├── data/                   # machine-readable transcription of INSTRUCTIONS.md Part II
│   ├── districts.json      # 5 districts × 10 indicators + population share
│   ├── measures.json       # 14 measures (id, direction, type, cost, lag, effects)
│   └── rules.json          # weights, synergies, incompatibilities, budget, H
├── src/                    # application code (one responsibility per module)
│   ├── data/               # loader + schema validation for data/*.json
│   ├── engine/             # pure scoring: apply measures → districts → Score
│   ├── validator/          # rule checks on a selection
│   ├── solver/             # enumerate/rank valid 5-measure sets (optional, cheap)
│   ├── ai/                 # LLM prompt + explanation layer (no arithmetic)
│   └── app/                # CLI and/or thin web API + UI
└── tests/                  # golden cases, engine unit tests, validator rule tests
```

Rules of thumb that keep this mergeable while several agents work at once:

- `data/` is **transcribed**, never invented: every number must be traceable to
  `INSTRUCTIONS.md` Part II. Keep the source section reference in a comment or a
  `source` field.
- `src/engine/` and `src/validator/` stay **pure and dependency-free** (no I/O, no LLM):
  they are the part that must be testable and trustworthy.
- `src/ai/` may only consume a `ScoreResult` object; it must not import `src/engine/`
  internals.
- Optional features get their own module instead of edits inside `engine/`.

## 4. Components

| # | Component | Responsibility | Reads | Produces |
| --- | --- | --- | --- | --- |
| C1 | Data loader | Load/validate `data/*.json` into typed objects; fail loudly on schema drift | `data/` | in-memory dataset |
| C2 | Validator | Check budget ≤ 100, exactly 5 decisions, no repeats, district required for type «Район» and forbidden for «Город», ≤ 2 measures per direction, incompatibilities (M1/M3, M4/M7 same district, M5/M13 same district) | selection | `ValidationResult {valid, reasons[]}` |
| C3 | Scoring engine | Lag scaling `(8 − L)/8`, synergies (not lag-scaled), `clip(·, 0, 100)`, district score `D_d = Σ w_k·I'`, city `D_avg = Σ pop_d·D_d`, `Score = 0.7·D_avg + 0.3·min(D_d) − N_crit`, with `N_crit` = district×indicator pairs strictly below 40 | dataset + valid selection | `ScoreResult` incl. per-district and per-measure deltas |
| C4 | Solver (optional) | Enumerate valid sets (14 measures, exactly 5, ≤ 2 per direction) and rank by `Score`; also useful as a test oracle | dataset | ranked sets |
| C5 | AI explanation | Turn `ScoreResult` into explanation, trade-offs, per-measure contribution, recommendations and "what if" comparisons | `ScoreResult` (+ LLM API) | narrative + suggested next sets |
| C6 | App surface | CLI first, web UI if time allows: budget meter, selection, score reveal, district visualisation | C1–C5 | user-facing flow |
| C7 | Tests | Golden cases + property/rule tests; must reproduce the two numbers given in the source | all above | pass/fail |

## 5. Interfaces to pin before implementation

These are **drafts** — per `AGENTS.md`, agree on them in `AGENT_CHAT.md` before parallel
work starts, then treat them as frozen.

```text
SelectionItem   { measure_id: str, district: str | None }
Selection       { items: SelectionItem[] }              # length must be 5
ValidationResult{ valid: bool, reasons: str[] }
DistrictDelta   { district: str, indicator: str, before: float, after: float, delta: float }
ScoreResult     {
  valid: bool, validation: ValidationResult,
  budget_used: int, cost_total: int,          # cost_total must equal budget_used
  districts: { name: str, before: float, after: float, deltas: DistrictDelta[] }[],
  district_scores: { before: float, after: float }[],
  d_avg: float, min_district: float, n_crit: int,
  score: float, score_delta: float,           # score_delta vs. "no action" baseline
  contributions: { measure_id: str, district: str | None, indicator: str, delta: float }[]
}

validate(selection, dataset) -> ValidationResult
score(selection, dataset)    -> ScoreResult        # invalid selection -> valid=false, no score
explain(score_result,          # C5; the only place an LLM is called
        question: str | None) -> str
```

Contract notes:

- An **invalid** selection gets no score at all — the validator returns the reason
  (rule 7), so `ScoreResult.score` must be nullable/explicitly absent, not `0`.
- `contributions` is the contract with the AI layer: it is what makes explanation
  possible without the LLM doing arithmetic.
- Baseline for `score_delta` is the no-action case: **52.56** (`INSTRUCTIONS.md`,
  Part II §3).

## 6. Parallel workstreams

Scopes are deliberately disjoint so several agents can work simultaneously (`AGENTS.md`:
"claim scopes, not files").

| W | Scope | Deliverable | Depends on |
| --- | --- | --- | --- |
| W1 | `data/**` | `districts.json`, `measures.json`, `rules.json` transcribed from Part II, with loader | — (start first, unblocks everything) |
| W2 | `src/validator/**`, `tests/validator_*` | rule checks + one test per rule 1–8 | W1 |
| W3 | `src/engine/**`, `tests/engine_*` | scoring pipeline + golden tests | W1, W2 interface |
| W4 | `src/ai/**` | prompt/explanation layer over `ScoreResult` | W3 interface (`ScoreResult`) |
| W5 | `src/app/**` | CLI, then optional web UI + district visualisation | W3 |
| W6 | `src/solver/**` | enumeration + ranking (optional; also tests W3) | W3 |
| W7 | `README.md` | run instructions, scenario walkthrough, architecture summary (judging: 25 pts for README/reproducibility) | W5 |

**Critical path:** W1 → W2 → W3 → (W4, W5) → W7.

## 7. Milestones

1. **M0 — skeleton pinned.** Layout agreed, `data/` schema in `AGENT_CHAT.md`, empty
   modules committed that import cleanly.
2. **M1 — numbers correct.** Engine reproduces the source's baseline **52.56** and the
   example set's **≈ 56.5** for `M7→Нура, M8→Нура, M10→Нура, M12→город, M5→Сарыарка`
   (cost 95), including the M10+M12 synergy. The source explicitly says *"Перепроверьте
   это кодом"* — a mismatch means the engine or our reading of the formula is wrong, and
   must be logged as a `BLOCKER`/`NOTE` in `AGENT_CHAT.md`, not silently patched.
3. **M2 — playable.** CLI takes 5 decisions, validates, scores, prints deltas.
4. **M3 — explained.** AI layer produces strengths/risks/consequences from real numbers.
5. **M4 — demo-ready.** README walkthrough, visualisation, one optional feature if time.

## 8. Conventions

- Python unless the team pins otherwise; type hints on public interfaces; no hidden state.
- Constants (weights, budget, `H = 8`, critical threshold 40, synergies) live in
  `data/rules.json` — never hard-coded inside `engine/`.
- Every engine/validator change comes with a test that fails before and passes after.
- Commit small, scoped, and prefixed (`engine:`, `validator:`, `data:`, `docs:`); pull
  `--rebase` before each commit (`AGENTS.md`).
- Keep `main` runnable: if something must land broken, say so in `AGENT_CHAT.md`.

## 9. Open questions (resolve in `AGENT_CHAT.md`)

1. Tech stack: Python CLI only, or a web UI (needed for the "visualise district changes"
   optional point)? Decide before W5 starts.
2. Language of the UI and of the AI output: Russian or English or both?
3. LLM access: which provider/key is available to the team, and is the explanation judged
   offline (recorded transcripts) for reproducibility?
4. Do we ship the solver (W6) as a "hint" feature, or keep it private as a test oracle?
5. Where does the final `README.md` walkthrough live for judging — root `README.md`, or
   root `README.md` linking to a short `docs/`-style page?
