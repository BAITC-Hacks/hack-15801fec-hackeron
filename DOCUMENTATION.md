# DOCUMENTATION

Documentation for the `hack-15801fec-hackeron` submission: source-material provenance
and the layout of the delivered simulator.

## 1. Repository layout

```
.
├── data/              # districts, measures and canonical scoring rules
├── src/               # loader, validator, engine, explanation, CLI, web UI and solver
├── tests/             # automated verification
├── task/              # immutable source documents and their text conversions
├── README.md          # launch, architecture and walkthrough
├── JUDGE_SCORECARD.md # rubric-mapped verification guide for the jury
├── INSTRUCTIONS.md    # consolidated task brief, data and rules
└── DOCUMENTATION.md   # this provenance document
```

## 2. Source materials

Both source files are Microsoft Word (`.docx`, "Microsoft Word 2007+") documents for the
hackathon task **«Аким на 5 часов» — AI-симулятор управления города** (Astana Quality of
Life Score simulator). They were delivered in `task/` and moved unchanged into
`task/original/`, which is now the canonical, read-only copy.

| File | Contents |
| --- | --- |
| `HackAlem_AI_«Аким_на_5_часов»_AI_симулятор_управления_городом.docx` | Task brief: problem, user, deliverables, must-have/optional features, verification criteria, 100-point judging rubric |
| `Датасет районов.docx` | Data spec: 5 districts and 10 indicators (0–100), 14 measures with costs/lags/effects, synergies, incompatibilities, scoring formula, 8 rules |

Neither document contains embedded images (`word/media/` is absent in both `.docx`
packages); the brief's content is one text table plus paragraphs.

### Checksums (originals, for verification/provenance)

```
b448c1f73e954ec727789edd0177bebf8559e188b77c1cccf54cca70b00f68bb  HackAlem_AI_«Аким_на_5_часов»_AI_симулятор_управления_городом.docx
434128bfede06afe4d115c13a82fce874a3cf494a24679e1b227b88d4a8aba86  Датасет районов.docx
```

## 3. `INSTRUCTIONS.md` — the single instructions file

`INSTRUCTIONS.md` at the repository root merges **both** source documents into one
reading order, so nobody has to open two `.docx` files to understand the task:

- **Part I — Hackathon brief** (from the `HackAlem_AI_…` document): problem, user, task,
  input data, expected result, must-have, optional, data/access, verification criteria, and
  the evaluation rubric table.
- **Part II — Dataset, measures, score formula, rules** (from `Датасет районов`):
  district indicator dataset, district profiles, the 14-measure catalogue with cost/lag/
  effects, synergies, incompatibilities, the `Score` formula and weights, and the 8 rules.

Fidelity notes:

- Content is **transcribed, not rewritten or translated** — the original Russian wording is
  preserved. Numbers, weights, IDs, and the `Score` example are copied as-is.
- The only change is formatting: source tables are rendered as Markdown tables, and
  numbered/bulleted lists are normalized to Markdown. A source-document map is at the top
  of `INSTRUCTIONS.md`.
- `INSTRUCTIONS.md` is a derived artifact: if an original `.docx` is ever updated, the
  `.txt` conversions and `INSTRUCTIONS.md` must be regenerated (see below).

## 4. `.docx` → `.txt` conversion

Conversion was done with headless LibreOffice (no pandoc/python-docx in this environment):

```bash
cd task/original
soffice --headless --convert-to txt:Text --outdir ../txt *.docx
```

This produced UTF-8 (with BOM) text in `task/txt/`:

| Output | Lines | Bytes |
| --- | --- | --- |
| `HackAlem_AI_«Аким_на_5_часов»_AI_симулятор_управления_городом.txt` | 54 | 7 407 |
| `Датасет районов.txt` | 90 | 9 331 |

Checksums:

```
01ac8927a1ee3ccb6b0545a79f3ab83abf08db8aea4d85b356d259dd7e0a870b  HackAlem_AI_«Аким_на_5_часов»_AI_симулятор_управления_городом.txt
8b02bc54baadad374835022aa239d95e5fcd7934ad35f8293a30d0ab493c3ae7  Датасет районов.txt
```

Known limitations of the `.txt` output (they are why `INSTRUCTIONS.md` exists):

- **Tables lose their structure.** Cells are flattened to tab-separated lines, so
  indicator codes, measure rows, and weights are hard to read straight from `.txt`.
  `INSTRUCTIONS.md` restores them as real Markdown tables.
- Headings are not marked up; the `.txt` files are a flat text dump.
- Files carry a UTF-8 BOM (LibreOffice default), and the `HackAlem_AI_…` file has very
  long lines (up to ~338 characters).
- Cyrillic and «guillemet» characters in file names are preserved from the source; keep
  them quoted in shell commands.

## 5. Reproducing the derived files

```bash
# 1. Re-convert the originals to text
cd task/original
soffice --headless --convert-to txt:Text --outdir ../txt *.docx

# 2. Re-generate the merged instructions file from task/txt/*.txt
#    (INSTRUCTIONS.md is a hand-curated Markdown merge; re-apply Section 3's rules
#     and verify against the .txt sources)

# 3. Verify nothing drifted
sha256sum task/original/*.docx task/txt/*.txt
```

Only `libreoffice`/`soffice` is required to regenerate the text conversions; it is
not required to run the simulator. The delivered application, tests and launch steps are
described in `README.md`.

## 6. Submission contents

The repository retains the task originals and their provenance so that the synthetic
dataset and model rules can be audited against the brief. Do not overwrite or delete the
files in `task/original/`: they are the immutable originals of record.
