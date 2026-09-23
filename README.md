# Autarkeia v0.4 — trusted-circle test

A working copy of a way of using Claude Code: files are the memory, the chat is not.

Same skill names as the system this was taken from. None of that person's life, projects, or private rules.

This is not a public product.

## Skills

| Skill | What it does |
|---|---|
| `setup` | First session: who this is for, what comes first, one job, one cycle |
| `distill` | Write what this session changed |
| `daily-debrief` | Close the day with a few questions |
| `weekly-debrief` | See the week |
| `checkpoint` | Quick mark so you can continue |
| `librarian` | File a document |
| `email` | Intake from `inbox/` — never send |
| `realign` | Rebuild the open-work picture |
| `health-check` | Is the vault still a system |
| `brainstorm` | Structured second opinion |
| `improve` | Capture friction — propose only |
| `outbound-writing` | Draft a message — never send |
| `sparring` | Think out loud with push-back |

What was stripped: someone else's biography, their email machine, their therapy notes, their other products. The moves are here. The life is yours.

## Setup (once, together)

On the machine that already has Claude Code:

1. Put this folder somewhere ordinary, for example `Documents/autarkeia-plugin`.
2. In Terminal:

```bash
claude plugin marketplace add /absolute/path/to/autarkeia-plugin
claude plugin install autarkeia@autarkeia-plugin
```

3. Copy `vault-template` to a new folder with your name on it, for example `Documents/my-os`.
4. Open **that** folder in Claude Code. Not this plugin folder — the vault.
5. Restart Claude Code if the commands do not appear.

Skills from a plugin carry its name. Type `/autarkeia:distill`, or just say **distill** in a sentence — both work.
6. Say: **setup**. It asks who this is for, what comes first, and the one job this vault should hold, then runs one real cycle and stops. One question at a time. If it stops early, say **setup** again next time and it continues.

If install complains, copy `autarkeia/skills/` into `your-vault/.claude/skills/` and open the vault anyway.

## How to use it

Do real work in that vault folder. End of a session: **distill**. End of a day: **daily debrief**. End of a week: **weekly debrief**. A document: **librarian**. Emails you dropped in `inbox/`: **email**.

It runs on your own Claude account. Thirteen skills against a vault that grows for a month is real usage. If you start hitting limits, say so — that is a result, not a failure.

The test is whether this is useful and meaningful for you after weeks of actual work.
