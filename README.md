# Autarkeia v0.4.1

A file-based way of using Claude Code: files are the memory, the chat is not.

## Why this exists

A life runs on many fronts at once: work, money, health, family, the things you are building. Each AI chat sees one conversation and forgets it. Nothing connects what you decided in March to what you are asking today.

Autarkeia keeps that context in a folder of plain text files on your own computer. Every session reads it and writes back what changed, so the next session starts from what you already know, not from zero.

The ideas behind it:

- **Models come and go; your memory should not.** AI models are replaced every few months. The files stay. Any capable model can read them, so a better model inherits everything instead of starting over.
- **Use the best model for the job, with everything it needs to know.** The vault belongs to no vendor. Claude runs it day to day; Codex and Grok can read the same files for a second opinion.
- **Plain files over databases.** You can open, read, back up and move every file yourself. Nothing is locked in an app, and you can see exactly what the AI knows about you.
- **Keep the original next to the summary.** Documents stay as they arrived. A future model can re-read them and pull out what today's missed.
- **Questions instead of blank pages.** The daily and weekly debriefs ask you a few questions and write down the answers. Nobody has to keep a journal.
- **Your priorities, written down.** `PRIORITIES.md` holds what matters to you, in order, and the weekly review checks your week against it.
- **No structure built in advance.** Folders and projects appear when real use needs them, not because a template said so.
- **You decide; it operates.** It writes your notes without asking every time. It never sends, posts, pays or deletes without your yes.

The name comes from the Greek *autarkeia*: self-sufficiency, having what you need within your own reach.

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
| `brainstorm` | Second opinion: Claude, or Codex and Grok if you install them |
| `improve` | Capture friction — propose only |
| `outbound-writing` | Draft a message — never send |
| `sparring` | Think out loud with push-back |

The skills are the method. What goes into the vault is yours.

## Setup

On the machine that already has Claude Code:

1. Nothing to download. In Terminal:

```bash
claude plugin marketplace add fukumushicha/autarkeia-plugin
claude plugin install autarkeia@autarkeia-plugin
```

2. Make your vault: a copy of `vault-template` in a new folder with your name on it, for example `Documents/my-os`. The install left a copy of this repository on your Mac, so this works in the same Terminal:

```bash
cp -R ~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template ~/Documents/my-os
```

3. Open **that** folder in Claude Code. Not the plugin — the vault.
4. Restart Claude Code if the commands do not appear.

Skills from a plugin carry its name. Type `/autarkeia:distill`, or just say **distill** in a sentence — both work.

5. Say: **setup**. It asks who this is for, what comes first, and the one job this vault should hold, then runs one real cycle and stops. One question at a time. If it stops early, say **setup** again next time and it continues.

Fallback, if the two commands in step 1 fail: download this repository (green **Code** button, then **Download ZIP**), put the unzipped folder somewhere ordinary, for example `Documents/autarkeia-plugin`, and run `claude plugin marketplace add /absolute/path/to/autarkeia-plugin` followed by the same install command. If that complains too, copy `autarkeia/skills/` into `your-vault/.claude/skills/` and open the vault anyway.

## How to use it

Do real work in that vault folder. End of a session: **distill**. End of a day: **daily debrief**. End of a week: **weekly debrief**. A document: **librarian**. Emails you dropped in `inbox/`: **email**.

Second opinions from Codex or Grok, not only Claude: [docs/second-opinion.md](docs/second-opinion.md) says what to install and how to ask for them.

It runs on your own Claude account. Thirteen skills against a vault that grows for a month is real usage; expect it to show in your plan's limits.

It earns its place after weeks of real work, not on day one.
