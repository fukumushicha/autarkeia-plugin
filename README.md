# Autarkeia v0.4.5

A living record of you, in files you own. It remembers your past, runs your present, and carries you forward with whatever AI is best at the time.

## Why this exists

A life runs on many fronts at once: work, money, health, family, the things you are building. Each AI chat sees one conversation and forgets it. Nothing connects what you decided in March to what you are asking today.

**What this is.** Not the AI. The AI is hired help, replaced every few months by something better. This is the part that does not change: everything written down about you, plus the rules for how any AI works with you. Separate yourself from your tools, and the tools can keep improving without you starting over.

It does three things. It remembers your past: documents as they arrived, what was true, what you decided and why. It works your present: the open work across every part of your life, checked against what you said comes first. And it carries you forward: whatever model is best next year reads the same files and picks up where the last one left off.

Two layers keep it honest. The record is the originals, untouched. The story is what the system builds from them: facts, decisions, the patterns it notices. A record without the story is a pile of files; a story without the record flatters. You get both.

**The goal is your whole life, available to whatever AI you work with**, in files you own: what is true now, what you decided and why, what is still open, and the originals themselves, kept as they arrived, so a better model later can read them again and find what today's missed. Memory is the summary; the archive is the evidence. One without the other is half a system. The archive is organised the way a person looks for things: first the part of life (official documents, money and tax, health, homes, travel, companies and projects, photos and memories), then the person or thing, then the document type. Nothing is created until a document arrives.

**How this differs from a personal agent.** The personal agents you have heard of, Instinct, Meta's Muse and the ones that will follow, learn you inside their own service. The memory sits on the company's computer. You usually cannot open it, correct it or take it with you; what you tell the agent may be used to train the next version unless you opt out; and when the company changes direction, or a better model appears somewhere else, the years of context stay behind.

Here the memory is a folder on your own disk. You can open every file and see exactly what the AI knows about you. The model is only the reader: Claude today, something else when something else is better, and the folder does not care. The AI reads what it needs from it, and what it reads goes to the company that runs that AI (Anthropic, for Claude), the same as your chats. Nothing is handed to anyone else, deleted, sent, posted or paid without your yes. Those are rules the AI follows, not a lock; how much it may do without asking is set in the app (see [Getting started](docs/getting-started.md), permission modes).

The two are not enemies. You can keep a personal agent for errands and keep your life here. The question is only where the record of you lives: on their side or yours.

The test for every line in this README: when a friend asks what you are building, should they remember that AI works for you, or that something of you lasts?

The ideas behind it:

- **Models come and go; your memory should not.** AI models are replaced every few months. The files stay. Any capable model can read them, so a better model inherits everything instead of starting over.
- **Use the best model for the job, with everything it needs to know.** The vault belongs to no vendor. Claude runs it day to day; Codex and Grok can read the same files for a second opinion.
- **Plain files over databases.** You can open, read, back up and move every file yourself. Nothing is locked in an app, and you can see exactly what the AI knows about you.
- **Keep the original next to the summary.** Documents stay as they arrived. A future model can re-read them and pull out what today's missed.
- **Questions instead of blank pages.** The daily and weekly debriefs ask you a few questions and write down the answers. Nobody has to keep a journal.
- **Your priorities, written down.** `PRIORITIES.md` holds what matters to you, in order, and the weekly review checks your week against it.
- **No structure built in advance.** Folders and projects appear when real use needs them, not because a template said so. A project gets its own rules when it needs them, not before.
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
| `handover` | Note for a fresh session to carry on from, and the line to paste there |
| `librarian` | File a document or a recording |
| `email` | Intake from `inbox/` — never send |
| `realign` | Rebuild the open-work picture |
| `health-check` | Is the vault still a system |
| `brainstorm` | Second opinion: Claude, or Codex and Grok if you install them |
| `improve` | Capture friction — propose only |
| `outbound-writing` | Draft a message — never send |
| `sparring` | Think out loud with push-back |

The skills are the method. What goes into the vault is yours.

## Setup

**New to Claude Code?** Follow [docs/getting-started.md](docs/getting-started.md): the first hour, click by click, in the Claude desktop app. The short version is below.

You need a paid Claude plan and Claude Code. In the desktop app, this runs in the **Code** tab, not in Cowork or an ordinary chat. If `claude --version` in Terminal prints nothing, install it first with Anthropic's own line (details: https://code.claude.com/docs/en/setup):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then:

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

Fallback, if the two commands in step 1 fail: download this repository (green **Code** button, then **Download ZIP**), put the unzipped folder somewhere ordinary, for example `Documents/autarkeia-plugin`, and run `claude plugin marketplace add /absolute/path/to/autarkeia-plugin` followed by the same install command. If that complains too, copy `autarkeia/skills/` into `your-vault/.claude/skills/` and `autarkeia/references/` into `your-vault/.claude/references/`, and open the vault anyway.

## How to use it

Do real work in that vault folder, one task per session. End of a session: **distill**. A new topic halfway through: **handover**, then continue in a fresh session. End of a day: **daily debrief**. End of a week: **weekly debrief**. A document or a recording: **librarian**. Emails you dropped in `inbox/`: **email**.

A statement, a contract, a scan, anything that arrived from outside: drop it in `inbox/`, say **librarian**, and the original goes to `archive/` untouched, filed by part of life, then the person or thing, then the kind of document, with a hash in that area's register. Documents you or the AI wrote go to `docs/`. Facts taken out of either land in memory.

You do not have to start empty. Ask Claude to audit a folder or a project you already keep elsewhere and propose how to bring it in: originals are copied, never moved, and nothing is deleted without your yes. [Getting started](docs/getting-started.md) has example requests.

Everything starts in the vault. When one piece of work or life grows a shape of its own, say **new project** and name it. It gets its own folder and memory, and, sooner or later, its own rules: who else is involved, what stays inside it, what to watch. The vault's rules always hold; a project's rules add to them. Keep opening the vault folder, not the project.

## What is in your vault

| Path | What it is |
|---|---|
| `AGENTS.md` | The vault's rules: how to talk to you, how to work (act then report, one recommendation and one question, a record is a claim until the file is opened, when you contradict the record it asks once and keeps both lines, never guess a date), what needs your yes, what never leaves. Every session reads it: Codex and Grok directly, Claude through `CLAUDE.md`. Change rules here, or ask Claude to. |
| `CLAUDE.md` | One line, `@AGENTS.md`. It points Claude at the rules. Leave it alone. |
| `PRIORITIES.md` | What comes first in your life, in order. You write it; the weekly debrief checks your week against it. |
| `NEXT-ACTIONS.md` | Open work across the vault and every project. **realign** rebuilds it; do not edit it by hand. |
| `memory/daily/` | One file per day. Everything lands here first, except the details of a project whose rules keep them inside it. |
| `memory/facts.md`, `decisions.md`, `tasks.md` | What is true, what was chosen and why, what is still to do. |
| `docs/` | Working documents: what you or the AI wrote (handover notes and transcripts too), listed in `docs/register.md`. |
| `archive/` | Originals from outside, exactly as they arrived, in up to eight areas by part of life (official documents, money and tax, health, homes, travel, companies and projects, photos and memories, archive records). Each area has its own register with a hash per file. An area appears when its first document does. |
| `inbox/` | Drop a file or an email here, then say **librarian** or **email**. |
| `reviews/` | Second opinions and health-check reports. |
| `projects/<name>/` | A project, once you have one: its own `memory/`, and its own `AGENTS.md` and `CLAUDE.md` once it has its own rules. |

Everything is plain text. You can open, read and edit any of it yourself.

A vault made before v0.4.2 has its rules in `CLAUDE.md` and no `AGENTS.md`. It keeps working. Say **health check** and it offers to move the rules to the new layout. A vault made before v0.4.4 has no `archive/`, no "How to work" section in its rules, and a four-column `docs/register.md` without hashes; it keeps working. Copy `archive/README.md` and that section from `vault-template/AGENTS.md` when you want them, or ask Claude to; the librarian adds a hash column to the old register the first time it files something.

A vault made before v0.4.5 still offers `git init` as a backup in its rules, and its example of a private project uses an older name. Say **health check**: it shows the current lines and replaces only those after your yes, leaving everything you wrote yourself.

**Updating.** In Terminal:

```bash
claude plugin marketplace update autarkeia-plugin
claude plugin update autarkeia@autarkeia-plugin
```

Then quit and reopen Claude. Your vault is not replaced: never copy the template over it again. New skills and fixes arrive with the plugin; changes to the vault's own rules arrive through **health check**, shown before anything is written.

**Automatic updates.** Off by default for this plugin. To turn them on: in a Claude session type `/plugin`, open the Marketplaces tab, choose `autarkeia-plugin`, then **Enable auto-update**. Claude then fetches new versions when a session starts; the next session uses them. Your vault's rules still change only through **health check**.

## Second opinions

Second opinions from Codex or Grok, not only Claude: [docs/second-opinion.md](docs/second-opinion.md) says what to install and how to ask for them.

## Cost

It runs on your own Claude account. Fourteen skills against a vault that grows for a month is real usage; expect it to show in your plan's limits.

Day one can start with what you already have. The record compounds after that: it earns its place over weeks of real work.
