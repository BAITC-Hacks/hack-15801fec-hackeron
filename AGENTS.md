# AGENTS.md — Read this before you touch anything

## Why this file exists

This repository is a **shared, multi-agent workspace**. Several agents (and humans)
work in it **at the same time**, on the same branch, from different machines and
sessions. Files can appear, change, or be rewritten between the moment you read
them and the moment you write to them.

That means:

- **You are not alone here.** Assume another agent is editing right now.
- **Nothing is "yours" permanently.** Files you just created may be modified by
  someone else minutes later — and that is expected, not an error.
- **You are responsible for not breaking other agents' work**, and they are
  responsible for not breaking yours. Coordination is the only thing that makes
  this work.

## Hard rules

1. **Pull before you work, and pull often.** Run `git pull --rebase` before you
   start any task, and again before every commit/push. Stale local state is the
   number one cause of merge conflicts and lost work here.
2. **Never force-push, never `git reset --hard`, never rewrite shared history.**
   Do not rebase or amend commits that are already pushed to `origin/main`.
   Do not delete files or branches you did not create unless a human explicitly
   told you to.
3. **Never blindly overwrite a file to "resolve" a conflict.** Read both
   versions and merge the intent. If you cannot merge safely, say so in
   `AGENT_CHAT.md` and wait for a human or the other agent.
4. **Announce before you edit, and after you finish.** Every non-trivial change
   gets an entry in `AGENT_CHAT.md` (see below).
5. **Commit small and often.** Many small, focused commits produce trivial
   conflicts; one huge commit at the end produces disasters.
6. **Never commit secrets**, tokens, credentials, `.env` files, or large
   binaries. Check `git status` before staging.

## Communication: `AGENT_CHAT.md` is the team channel

`AGENT_CHAT.md` at the repo root is the **single source of truth for what
everyone is doing**. It is an append-only log. Treat it as a message bus between
agents.

**Before starting work:**

1. `git pull --rebase` (so the chat log is current).
2. Read the **last ~30 entries** of `AGENT_CHAT.md`.
3. If someone has already claimed the area you want to touch, or is mid-task on
   something that overlaps, **do not start**. Coordinate first.

**Then post a claim entry** using this format:

```
### [YYYY-MM-DD HH:MM UTC] <agent-name> — CLAIM
Scope:      <files/dirs/modules you will touch>
Task:       <what you are doing, one or two lines>
ETA:        <rough time>
Blocking:   <anything you need from others, or "none">
```

**While working**, post `UPDATE` entries whenever: you change your scope, you
finish a milestone, you hit a blocker, or you are about to leave the repo
unfinished. Use:

```
### [YYYY-MM-DD HH:MM UTC] <agent-name> — UPDATE | BLOCKER | RELEASE | NOTE
<what changed / what you need / what you learned / what you handed off>
```

**When you finish** (or stop for more than a few minutes), always post a
`RELEASE` entry freeing the scope you claimed:

```
### [YYYY-MM-DD HH:MM UTC] <agent-name> — RELEASE
Scope:  <scope you are freeing>
State:  <done / partial / abandoned>
Left:   <unfinished work, TODOs, broken things, know-how the next agent needs>
```

Rules for the chat log:

- **Append only.** Never rewrite, reorder, or "clean up" old entries — other
  agents may be reading them as they pull.
- Keep entries short and factual. Timestamps in UTC. Include your agent name.
- Write it *before* you go silent. An agent that dies without a `RELEASE` entry
  blocks everyone else.
- If you find a stale claim with no activity for a long time, post a `NOTE`
  asking about it instead of silently taking it over.

## Planning protocol

- **Claim scopes, not files.** "I'm working on `src/api/*`" is better than
  "I'm editing `src/api/routes.ts`" — it gives you room and tells others the
  boundary.
- **Two agents must not claim overlapping scopes.** If you need to touch a
  claimed scope, message the owner in `AGENT_CHAT.md` and wait for their
  `RELEASE` (or split the work explicitly).
- **Sequence dependent work.** If task B needs task A's output, say so in the
  `Blocking:` field and do not start B until A is released.
- **Prefer separate files over shared files.** When two agents must touch one
  file, serialize: one goes first, releases, then the other pulls and edits.
- **Pin interfaces early.** Agreement on function signatures, API shapes, and
  file layout belongs in `AGENT_CHAT.md` *before* implementation, so parallel
  work can proceed without conflict.

## Git workflow

```bash
git pull --rebase                    # before you start
# ... work in small increments ...
git status                           # verify what you are about to commit
git pull --rebase                    # again, right before committing
git add <specific files>             # not `git add -A` blindly
git commit -m "<scope>: <what and why>"
git pull --rebase && git push        # if the push is rejected, pull --rebase and retry
```

- If a rebase conflict appears: **stop and read both sides.** Resolve file by
  file, then log a `NOTE` in `AGENT_CHAT.md` describing the resolution. If it is
  not obvious, leave the working tree clean and ask a human.
- If the push is rejected, that means another agent pushed. Pull `--rebase`,
  re-run your tests, and push again. Never `--force`.
- Keep `main` always in a runnable state. If you must land something broken,
  say so loudly in `AGENT_CHAT.md`.

## Quick checklist for every session

- [ ] `git pull --rebase` done
- [ ] Last ~30 `AGENT_CHAT.md` entries read
- [ ] No overlapping claim by another agent
- [ ] `CLAIM` entry posted with scope
- [ ] Work done in small commits
- [ ] `git pull --rebase` before commit and push
- [ ] `RELEASE` entry posted with state and leftovers
- [ ] No secrets, no force-push, no deleted data
