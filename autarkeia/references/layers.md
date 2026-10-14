# Where memory goes

One vault. The chat is not memory.

| File | What belongs here |
|---|---|
| `memory/daily/YYYY-MM-DD.md` | Everything that happened. Write here first, except what a project's rules keep inside the project: then a pointer at most. |
| `memory/facts.md` | What is currently true. Newest at the top. |
| `memory/decisions.md` | What was chosen, and why. Newest at the top. |
| `memory/tasks.md` | What is still to do. Done items leave this file. |
| `PRIORITIES.md` | What matters, in order. The user writes this. |
| `NEXT-ACTIONS.md` | Generated picture of open work. `/realign` rebuilds it. Never edit by hand. |
| `docs/` | Documents we filed. `docs/register.md` is the list. |
| `inbox/` | Drop files and emails here. |
| `reviews/` | Second-opinion packets from `/brainstorm`. |
| `memory/ops/friction.md` | Things that keep going wrong, from `/improve`. Propose only. |
| `memory/ops/improvement-proposals.md` | Proposals from `/improve`. Nothing here is applied without you saying yes. |

If `projects/<name>/memory/` exists, that project owns its own facts, decisions, and tasks. The vault copies only a one-line pointer. If `projects/<name>/AGENTS.md` exists, it holds that project's own rules: read it before writing to the project. It adds to the vault's `AGENTS.md` and never loosens it.

## Entry shape

```
- **fact**: [plain sentence]. (YYYY-MM-DD)
```

Types: `fact`, `decision`, `constraint`, `observation`, `task`, `health`.

Never write durable facts into Claude's hidden project memory.
