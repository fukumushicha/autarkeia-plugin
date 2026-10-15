---
name: setup
description: "First session in a new vault: who this is for, what comes first, one job, one real cycle. Use when the user says setup, set up, first session, new vault, start here, or begin."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Setup

The first session. Four steps, in order, then stop. This is not a questionnaire and it does not build a system. It puts one real thing in the vault and shows that the next session will see it.

**Mode: ask, then act.** Each step is a question. Their answer is the approval: write it, with no second round. Their own life into their own vault is the ordinary case. Two exceptions: the contract change in step 1 is shown first and written after yes; and everything the contract lists under **When you must ask** (another person, anything off the record, anything that would leave this vault) is asked before it is written.

**One question at a time.** Ask, wait, write, next. Never show the whole list. Never put two questions in one message.

**Every answer lands in today's daily log first**, as one line in the setup block below, and only then in its own file. That is the order the contract sets.

## Before starting

**The contract** is `AGENTS.md`. Only if there is no `AGENTS.md` and `CLAUDE.md` holds more than the line `@AGENTS.md` (a vault made before v0.4.2), the contract is that `CLAUDE.md`; do not move or rename it.

Confirm the contract and `memory/facts.md` exist here. If not, stop and say so: this folder is not a vault. Tell them to copy `vault-template` to a folder of their own as step 2 of the plugin's README says (after a GitHub install it sits at `~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template`), open that folder in Claude Code, and say setup again. Do not create the vault for them.

Read the contract. Run `date "+%Y-%m-%d"` and `date "+%H:%M"`. Do not guess the date.

Search `memory/daily/` for the line `**Setup**: done`. If it exists, this vault is set up. Say so, say the rhythm (distill before closing a session, daily debrief at the end of a day), and stop. Setup does not run its questions again. If they want to change something it asked (their name, how to talk to them, their priorities, the first job), tell them to say it plainly in any session: priorities and the job are written like any other answer, and a change to how to talk is a contract change, shown first and written after yes. Projects and patterns come from use, not from setup.

Otherwise append `### Setup (HH:MM)` to today's log, `memory/daily/YYYY-MM-DD.md` (create it if needed), and go through the steps in order. That is the whole resume: nothing is skipped. Where an earlier `### Setup` block or a file already holds an answer (a name, a filled priority, a real task in place of the seed task), do not ask it fresh: show what you have, in one message, and ask once whether it still holds. Then write each confirmed answer exactly like a new one, block line first, then its file. Re-read a file before writing to it and do not add a line it already has. `not named yet` and `not run` are not answers; ask those again.

The block, one line per answer, added as each answer arrives:

```
### Setup (HH:MM)

- **Name**: ...
- **Language**: ...
- **For**: ...
- **How to talk**: [their answer]
- **Priorities**: 1 ... 2 ... 3 ...
- **Not doing on purpose**: ...
- **First job**: ... / not named yet
- **Cycle**: what landed in memory/ / not run
- **Setup**: done / stopped before the cycle
```

If someone else is helping with setup, the answers still come from the vault's owner.

## 1. Who

Four questions, one at a time. After each answer, add its line to the block.

1. What should I call you?
2. Which language do we work in? Use it from here on.
3. In one or two sentences: what is this vault for?
4. How do you want to be talked to? Short or long, plain or formal, what you want warned about and what you do not.

After question 3, write to `memory/facts.md`, newest at top: `- **fact**: [name], works in [language]. This vault is for [their sentence]. (YYYY-MM-DD)`.

The answer to question 4 goes into the block in full. It also belongs in the contract under **How to talk**, because every session reads it. That is a change to the contract: show the two or three lines you would add, in their words, and write them only after yes. Then add `. Contract: written` to the block line; if they say no, leave the contract as it is and add `. Contract: declined`. Until they answer, the line carries neither.

## 2. What comes first

Open `PRIORITIES.md`. Ask: what actually comes first in your life right now, three things, in order? Wait. Block line, then the numbered blanks. Then ask: what are you not doing on purpose? Wait. Block line, then the line under that heading.

If they answer with seven domains or a philosophy, ask them to pick three. Their words only. Add no tiers, scores, or structure from anywhere else.

## 3. One job

Ask: what is the first real piece of work or life this system should hold? One. In their words.

If they name several, ask which one they would be sorry to lose track of next week. If they cannot name one, say so plainly, write `**First job**: not named yet`, and go to Close. That is not a failure; the vault waits.

Block line, then replace the task **Name one job this vault is for** in `memory/tasks.md` with the job: `- [ ] **[job, their words]** -- [one line]. *(added: YYYY-MM-DD)*`.

Do not create projects during setup. One vault is enough to start; later, a "new project" request follows the contract's Projects section. If the job is about a body, the health clause in the contract holds from the first sentence.

## 4. One cycle

Talk about the job for a few minutes: what is true about it now, what was decided, what is still open. Then save it the way `/distill` does: run the distill skill if you can; if you cannot, read the plugin's `skills/distill/SKILL.md` and follow it (today's daily log first, under `### Session (HH:MM)`, then facts, decisions, tasks). Then open `memory/` and show them what landed, in their words: the next session will see this; the chat will not be there. Block line: what landed.

## Close

Also when stopping early at step 3.

Add the last line of the block: `**Setup**: done` if the cycle ran, otherwise `**Setup**: stopped before the cycle`. The next session continues from the block.

One sentence to close: what is now in the vault, and the rhythm: distill before you close a session, daily debrief at the end of a day.

Do not teach the other skills. Do not fill in projects, patterns, or anything they did not say. Those come from use.
