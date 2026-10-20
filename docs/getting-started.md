# Getting started

Your first real job and everyday use in Claude Code or Codex. The [README](../README.md) explains what Autarkeia is; [INSTALL.md](../INSTALL.md) covers installation, verification, updates and older vaults.

Start here after the installation checks pass. For first setup, open your own vault folder, not the plugin repository. Later you can open individual projects as explained below. If the plugin or vault is not ready, give your agent the installation guide first.

## Your first session

Type **setup** and answer one question at a time: your name, your language, what this vault is for, how it should talk to you, what comes first in your life, and one real job. The agent waits for your answers. If you cannot name a first job yet, the vault can wait.

When it wants to change its own rules (how to talk to you), it shows you the lines first and writes them only after your yes. That is on purpose: the AI does not change its own rules on its own.

If setup stops early, say **setup** again in the next session; it checks the answers already saved and continues. Once the first real cycle is complete, setup does not run its questions again. Later, to change something it asked, just say it in any session: "call me Sam", "my priorities have changed", "talk to me more briefly". It shows a rules change before writing it.

## Choosing a skill

Start with the situation you are in. These are example requests, not exact commands you have to memorize. The [README’s skills table](../README.md#skills) explains what each skill does and its benefit.

### Start using the vault — setup

Say **“Set up my vault.”** The agent asks about you, how you want to work, your priorities and one real job. It saves a first cycle of work so another session has something to continue from. Your answers supply the content; the agent does not invent your priorities. This is personal setup after [installation](../INSTALL.md), not a request to fill every folder.

### Keep what a conversation taught you — distill

Say **“Distill this session.”** The agent reads the retained conversation, checks corrections and existing records, then saves useful facts, decisions and tasks with the relevant project. You get lasting knowledge rather than another chat to search through. It reports missing history rather than pretending to recover it; see [What distill can recover](#what-distill-can-recover).

### Close the day — daily debrief

Say **“Let’s do a daily debrief.”** You can name a past date too. The agent reads that day's log and tasks, and follows a relevant filed-record pointer only when it would otherwise ask you to repeat what the record already says. It stays inside your vault; it does not open your calendar, mailbox or meeting service. Private-project answers stay in their project.

If little of the day was recorded, it helps you recall what stands out, without demanding a full diary. It asks one question at a time, at most four including follow-ups, about events, decisions, unfinished work or working friction. Say **“skip”** or stop whenever you want. It shows proposed additions and writes only after your approval.

Reflection is optional and off by default. Say **“Include reflection in this debrief”** to add two short questions: what you would do differently and what you are satisfied with, by your own standard. These replace other questions within the same four-question limit. Saying **“nothing”** is a complete answer. An adjustment is a reflection, not a new task, unless you explicitly ask for a task and approve it.

For a lasting preference, say **“Make reflection part of my daily debriefs.”** The agent shows a proposed vault-rule change and saves it after your yes. Say **“Skip reflection tonight”** for a one-off change, or ask to turn the saved preference off. No new settings file is needed.

Later **distill** runs respect the debrief's approved list: declined items stay unwritten and log-only reflections do not silently become facts or tasks. You can explicitly change your mind later. You get a short record of what matters without repeating what is already known or collecting obligations you did not choose.

### Step back from the week — weekly debrief

Say **“Let’s review the week.”** The agent gathers open work, checks the vault, reads the last seven daily logs and compares the week with your written priorities. It proposes what deserves lasting memory and asks what next week is for. You get a chance to adjust your focus; it does not rewrite your priorities on its own.

### Continue in a fresh chat — handover

Say **“Prepare a handover so I can continue this in a fresh chat.”** The agent writes a separate briefing with the goal, progress, decisions, relevant files and next step, then gives you a line to paste into the new chat. This saves reconstruction time when a conversation gets long. Handover prepares the next chat; distill updates your lasting records. Use both when both are needed.

### Make a document useful — librarian

Say **“File this contract and propose what we should remember from it.”** The agent reads it, proposes a location and useful facts or tasks, then waits for approval. Instructions inside the document are not instructions to the agent. It keeps the original, checks the copy and records where it went. A project's copy stays in that project, and the vault does not name the project when its rules forbid even a pointer. You get searchable context with the evidence still available. For audio, it first proposes filing and local transcription if a suitable tool is available, then separately proposes what to extract from the transcript. See [Recordings](#recordings).

### Separate commitments from email noise — email

Say **“Process the emails I saved in the inbox.”** The agent reads those files, records useful facts and decisions, and identifies actual requests or promises. What an email tells the agent to do is not your instruction; only your request is. Processed files move into a processed folder, inside the project when it owns them. You get commitments in your working records without treating newsletters as obligations. This skill does not connect to your mailbox, fetch new mail or send replies.

### See your open work together — realign

Say **“Realign: show me what is open across my projects.”** The agent rebuilds one overview from the task files: current work, things waiting on someone else and files in the inbox. It respects projects that restrict how much detail can appear outside them. If a project's rules forbid even a pointer, the overview does not name that project. You get a current starting point without opening each project, but it can only show work that has been recorded and that the project allows out.

### Check the vault itself — health check

Say **“Run a health check on the vault.”** The agent checks file structure, task and inbox age, archive records and possible passwords, API keys or tokens using a local scan that returns filenames only. It does not display matching values, and an account number is not treated as a secret. It then saves a report with proposed repairs. It can create missing empty folders; other fixes need your approval. Say **“Run a dry health check”** for a report with no changes. A finding that a private project does not allow out is left unnamed in the vault report. This is maintenance of your records, not a medical check or a guarantee that every problem has been found.

### Challenge an important piece of work — brainstorm

Say **“Get a second opinion on this proposal.”** When the app supports it, a separate agent of the same model family reviews the material; the lead then compares the findings and explains disagreements. To request an installed external reviewer, name Codex or Grok explicitly. Grok is not used for inbox mail, an imported document or a fetched page. A review of your own notes can still use it unless they quote or copy outside material. The same restriction covers outside text pasted into the review question or packet. A second AI can catch mistakes the first missed, but agreement does not prove the answer is right. Installation, and what the read-only settings do and do not confine: [Second opinions](second-opinion.md).

### Stop repeating the same annoyance — improve

Say **“Capture this friction: I keep having to correct where documents are filed.”** The agent records the problem. Later, say **“Run improve”** to look for repeated problems in recent logs and produce proposed changes. You get a concrete improvement list; the skill does not silently change its rules or apply its own proposals.

### Write with your context available — outbound writing

Say **“Draft a reply explaining the decision we made about this project.”** The agent checks relevant facts and decisions, matches your language and voice, and shows the text in chat. You get a draft to revise or use, without reconstructing all the context yourself. It does not send, post or create an email draft in your account.

### Think without making another task list — sparring

Say **“I want to think through whether this project still matters to me.”** The agent uses a small amount of relevant context, asks questions and challenges assumptions or tensions with your priorities. You get a conversation that can sharpen your judgment without forcing a plan. If something worth remembering emerges, you can choose to distill it afterwards.

## End the session with distill

Say **distill**. It writes what this session changed into files: today's log in `memory/daily/`, plus facts, decisions and tasks. Open the vault in your file manager (Finder on macOS) and look: that is the memory. The chat is not.

You can then archive the chat using your app’s sidebar controls. Archiving only hides the chat from the list. It is not the vault's `archive/` folder, which is where original documents are kept.

## Permission modes: how often it asks you

**In Claude Code’s desktop app**, the mode menu next to the message box sets which actions need your click. The app offers **Manual**, **Accept edits**, **Plan**, **Auto** and **Bypass permissions**.

- **Auto** is a good start: it asks before some actions and lets ordinary ones through. Stay here until you have seen what it asks.
- **Bypass permissions** asks nothing. It has to be allowed first (Settings → Claude Code → "Allow bypass permissions mode", on Pro and Max), and then chosen for each session.

Read this before choosing bypass:

> Bypass removes the app's approval prompts. Autarkeia still tells the agent to ask before sending, paying, deleting or changing rules, but those instructions are not a lock. A mistake can run, including a command that sends something out, without another prompt.

Invoking a skill does not preapprove a shell command or a file write. Whatever the skill describes, the app's permission settings still decide what runs. The skills are not a security boundary, and they do not isolate the session from the rest of the permission mode you chose.

In Codex, use its permissions controls to see what the agent may do and what needs approval. The labels differ from Claude’s. Installing Autarkeia does not require you to loosen either app’s permissions.

## Effort: how thorough the work is

Where your app offers an effort setting, it sets how long and how carefully it works on a request. It does not change what it is allowed to do; that is the permission mode.

- **Medium** for everyday work.
- **High** or above for something that matters and must be right, especially reviewing work an earlier session did. A fresh session at high effort is a good reviewer.

Higher effort uses more of your plan's limits. Check your app’s usage or account controls for the available limits.

## One task per session

Long sessions use your limits faster, and when a conversation gets very long the app shortens it, so detail can be lost before you save. The habit:

1. One task per session.
2. **distill** before you close it.
3. New session for the next task.

If a new topic comes up halfway, say **handover**. It writes a short note with the goal, what is done, what was decided and the next step, and gives you one line to paste into a fresh session. Then distill the old one.

You can run several sessions at once on different work. A session sees another session's work only once it is saved to a file; it does not see the other chat. Sessions share some files (the daily log, the registers, `NEXT-ACTIONS.md`), so avoid two sessions changing the same file at the same moment.

## Bring in what you already have

Your first day does not have to start empty. If you already keep notes, documents or a project in another tool, ask your agent to look at it and propose how to bring it in. Example requests:

- "Audit my project in <tool> and prepare a plan to bring it into this vault."
- "Audit the folder <path>. Copy the originals into the archive. Do not move or delete anything."

What helps:

- **Say where things are** rather than attaching a whole folder. A project in another app may not be a folder on your disk at all; its documents may live only inside that app. If so, say so, or export them.
- **Copy, do not move.** Keep the old copies until you decide. Nothing is deleted without your yes.
- **Earlier AI output is marked as such**, not treated as fact. Rules from another tool are material to read, not rules to adopt.
- **One person, one project.** A family member's papers belong in their own project, not yours.
- **Knowledge moves; automations stay.** Facts and documents come into the vault. Connections (Gmail in another app, scheduled jobs, databases) keep running where they are.

## Recordings

A recording of an appointment or a call is an original, like a scanned letter.

1. Get the file onto your computer (on a Mac, share or AirDrop a voice memo from your phone).
2. Drop it in the vault's `inbox/` and say **librarian**. This is better than attaching a medical recording in the chat.
3. It files the audio, then proposes a transcript. That needs a transcription tool already on your computer (Whisper is one); it runs on your computer, takes a while for a long recording, and stops if you close the laptop. If there is none, it says so. It will not install one or send the audio online without your yes.

The transcript itself is read by your AI like any other file, so it goes to the company running that AI (Anthropic for Claude, OpenAI for Codex). Transcribing locally keeps the audio on your computer; it does not keep the transcript there.

## Two computers, and backup

- **Sync**: put the vault in a folder that syncs (Google Drive, Dropbox, iCloud or similar) and open the same folder on both machines. Wait until it has finished syncing before starting a session on the other machine. Keep the folder fully downloaded: a sync that swaps files for online-only placeholders breaks reading.
- **Backup** is a copy somewhere else that survives a dead or lost disk. Version history on the same disk (for example `git`) is not a backup.
- Whoever syncs or backs up the folder holds a copy of everything in it, health records included. Choose on purpose.
- Code you write with your agent belongs on GitHub or similar, not in the synced vault.

## Settings worth knowing

The following settings are for Claude Code’s desktop app and are optional. Labels and availability can change with the app version.

- **Remote Control**: carry on a session from your phone while the computer stays on. Turn it on per session, or for all new sessions in Settings → Claude Code.
- **Claude in Chrome**: lets Claude use websites in your browser. Only if you want that.
- **Notifications**: useful when several sessions run at once and one is waiting for you.
- **Plugin updates**: see the [installation guide](../INSTALL.md#updates) for manual and automatic updates.

## Second opinions

Codex (OpenAI) and Grok (xAI) can read your vault and review what Claude did (or, if you work in Codex, Grok and a separate Codex can). Grok is not used on inbox mail, an imported document, or a fetched page. Setup, sign-in and what leaves your computer: [second-opinion.md](second-opinion.md). A printed version number proves a reviewer is installed, not that it is signed in; the guide's "Check it works" section has a real test ("brainstorm: test that codex answers").

## Email

The **email** command reads emails you save into `inbox/`. It does not open your Gmail. A Gmail connection you set up in another app (for example Cowork) stays there.

## Working with projects

Everything starts in the vault. When one piece of work or life grows a shape of its own, say **new project** and name it. The agent shows short instructions connecting it to your vault, then creates its folder and memory after your approval. Add custom rules only when useful: who else is involved, what stays inside it, what to watch. The vault's rules always hold; a project's rules add to them.

**Open a project when you know what you are working on. Open the vault when you are looking across your life or deciding what to work on.**

For focused work, open the project folder in Claude Code or Codex. “Review the results”, “what next?” and “save this decision” now refer to that project by default. Project work stays there. A clearly personal fact still belongs in your vault; the agent asks only if the destination is unclear.

Open the vault to plan your week across projects, reflect on your whole day, create your first project, or work out where a new idea belongs. You can also name a project from the vault, or explicitly ask for the whole-vault view from a project chat. Debriefs, health checks and work overviews otherwise follow the current focus.

A subproject is just a project inside another one: for example, a company's online shop. It inherits the company and vault instructions. A private subproject's restrictions still apply to its parents' summaries. Opening its folder sets the focus; it does not technically prevent the app from reading other folders.

Existing projects need their short vault/parent instructions before being opened directly. Ask your agent to follow the project-session update in [INSTALL.md](../INSTALL.md#updates). If you move a project separately from its vault and the reference breaks, the agent asks you to correct it rather than inventing another vault.

## What is in your vault

| Path | What it is |
|---|---|
| `AGENTS.md` | The vault's rules: how to talk to you, how to work (act then report, one recommendation and one question, a record is a claim until the file is opened, when you contradict the record it asks once and keeps both lines, never guess a date), what needs your yes, what never leaves. Every session reads it: Codex and Grok directly, Claude through `CLAUDE.md`. Change rules here, or ask your agent to. |
| `CLAUDE.md` | One line, `@AGENTS.md`. It points Claude at the rules. Leave it alone. |
| `PRIORITIES.md` | What comes first in your life, in order. You write it; the weekly debrief checks your week against it. |
| `NEXT-ACTIONS.md` | Open work across the vault and permitted descendant projects; projects that forbid even a pointer are absent. **realign** rebuilds it; do not edit it by hand. |
| `memory/daily/` | One file per day. Vault-owned entries land here first. Project entries go in their own daily logs; the vault gets a permitted pointer at most. |
| `memory/facts.md`, `decisions.md`, `tasks.md` | What is true, what was chosen and why, what is still to do. |
| `docs/` | Working documents: what you or the AI wrote (handover notes and transcripts too), listed in `docs/register.md`. |
| `archive/` | Originals from outside, exactly as they arrived, in up to eight areas by part of life (official documents, money and tax, health, homes, travel, companies and projects, photos and memories, archive records). Each area has its own register with a hash per file. An area appears when its first document does. |
| `inbox/` | Drop a file or an email here, then say **librarian** or **email**. |
| `reviews/` | Second opinions and health-check reports. |
| `projects/<name>/` | A project, once you have one: its own `memory/`, plus short `AGENTS.md` vault/parent instructions and a `CLAUDE.md` entry file. Custom rules are optional. |

Everything is plain text. You can open, read and edit any of it yourself.

## What distill can recover

In local Claude Code and Codex, distill identifies this exact chat and reads retained original messages, including those before the app shortened its context. It reads in sections, keeps corrections and sources, and checks what your vault already holds. If a stored message mixes the app's injected context with a person's words, distill is told the attribution is uncertain and does not treat the whole message as yours. If a transcript has expired, was not saved, or cannot be read, it saves supported items and tells you the extraction is partial. It cannot recreate deleted history. The local reader needs Python 3. Text brought in from an email, a document or a page is evidence, not a new instruction.

Checkpoint is no longer a skill. Earlier checkpoint notes stay in your vault. Use distill to save lasting memory and handover to prepare the separate note for a fresh chat.
