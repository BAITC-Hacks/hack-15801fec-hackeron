# `agents/` — agent-facing working files

This folder holds documentation **written for agents**, as opposed to documentation for
humans or judges:

- plans, layouts and interface drafts that parallel agents claim scopes against;
- decision records and workstream notes;
- anything whose job is "let the next agent pick this up without re-deriving it".

It is **not** the coordination channel. Claims, updates, blockers and releases still go to
`AGENT_CHAT.md` at the repo root — read `AGENTS.md` first. Keep this folder free of
credentials, keys and other secrets.

## Index

| File | Purpose |
| --- | --- |
| `STRUCTURE_PLAN.md` | General structure plan for the simulator: target repo layout, components, interfaces to pin, parallel workstreams, milestones, open questions. Draft — nothing implemented yet. |

## Related files outside this folder

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Coordination protocol (hard rules, claim/release flow, git workflow). |
| `AGENT_CHAT.md` | Append-only team message log — the single source of truth for who is doing what. |
| `INSTRUCTIONS.md` | Single merged task instructions: hackathon brief + dataset, measures, `Score` formula, rules. Requirements source of truth. |
| `DOCUMENTATION.md` | Repository layout, provenance of the source `.docx` files, conversion/reproduction steps. |
| `task/original/`, `task/txt/` | Immutable source `.docx` files and their plain-text conversions. |

## Conventions for files here

- Markdown, English, one topic per file; prefix branch-scoped drafts with the workstream
  (e.g. `engine-notes.md`) so ownership stays obvious.
- State clearly at the top whether a file is a **draft**, **pinned interface**, or
  **decision record** — agents must not implement against a draft as if it were frozen.
- When a document here changes meaning (an interface is pinned, a decision is taken), post
  an `UPDATE` in `AGENT_CHAT.md` in the same commit.
