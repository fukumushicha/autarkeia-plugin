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
| `docs/` | Working documents: written by them or an AI, or copies filed for reference. `docs/register.md` is the list. |
| `archive/` | Originals from outside, exactly as they arrived, by area of life. Each area has its own `register.md` with a hash per file. Layout and rules: `references/archive.md`. |
| `memory/tasks-archive.md` | Done tasks, with the date they were done. |
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

## When a fact changes

- Same topic, newer information: the new line supersedes. Mark the old line `superseded YYYY-MM-DD:` with the new sentence or a pointer to the new line. Never delete the old line.
- Different aspect of the same topic: both stay. Two entries about different aspects are not in conflict.
- A contradiction you cannot settle from a source: write neither as true. Note it in the daily log and ask.
- They corrected the record themselves: their answer is final. Record it beside the old line with the date.

## What wins

Only between competing claims about the same thing for the same time. Newer information about a later time supersedes regardless (an old signed lease does not outrank a confirmed move), and their own correction is final.

1. The more specific scope: a project's own facts beat the vault's facts about that project.
2. Within one scope, the higher provenance: a signed document beats a conversation; an original in `archive/` beats a summary of it.
3. Same scope and provenance: the most recent dated entry.

## A task line

Current state only: what it is, the next step, and if there is history a pointer to where it lives (the daily log, a decision, a document). The history itself does not go in the task line; a status change replaces the old status instead of stacking under it. Done items leave `tasks.md` the same session, into `memory/tasks-archive.md` with the date.

A flag is not a task. An action they agreed to or asked for that could not be finished in the session becomes a task with a next step and, when known, a date; otherwise the daily log says it was dropped. Something merely noticed stays an observation in the daily log, without an invented owner, deadline or disposal. Never leave an agreed action implicit in a log line.

Never write durable facts into Claude's hidden project memory.
