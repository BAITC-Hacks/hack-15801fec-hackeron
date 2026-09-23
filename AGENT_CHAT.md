# AGENT_CHAT.md — agent coordination log

Append-only log. Read the last ~30 entries before starting work, post a `CLAIM`
before you touch anything, and post a `RELEASE` when you stop. See `AGENTS.md`
for the full protocol.

Entry types: `CLAIM`, `UPDATE`, `BLOCKER`, `RELEASE`, `NOTE`.

Format:

```
### [YYYY-MM-DD HH:MM UTC] <agent-name> — <TYPE>
Scope:      <files/dirs/modules>
Task:       <what you are doing / what changed / what you need>
Blocking:   <anything you need, or "none">
```

Rules: append only, never edit or delete past entries, timestamps in UTC.

---

### [2025-09-23 13:27 UTC] bootstrap — NOTE
Scope:      repo root
Task:       Created `AGENTS.md` (coordination protocol) and this `AGENT_CHAT.md`
            log. Repo had only `README.md` before this.
Blocking:   none
