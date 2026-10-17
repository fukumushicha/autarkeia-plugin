# Getting started

Your first real job and everyday use in Claude Code or Codex. The [README](../README.md) explains what Autarkeia is; [INSTALL.md](../INSTALL.md) covers installation, verification, updates and older vaults.

Start here after the installation checks pass. Open your own vault folder, not the plugin repository and not a project inside the vault. If the plugin or vault is not ready, give your agent the installation guide first.

## Your first session

Type **setup** and answer one question at a time: your name, your language, what this vault is for, how it should talk to you, what comes first in your life, and one real job. The agent waits for your answers. If you cannot name a first job yet, the vault can wait.

When it wants to change its own rules (how to talk to you), it shows you the lines first and writes them only after your yes. That is on purpose: the AI does not change its own rules on its own.

If setup stops early, say **setup** again in the next session; it checks the answers already saved and continues. Once the first real cycle is complete, setup does not run its questions again. Later, to change something it asked, just say it in any session: "call me Sam", "my priorities have changed", "talk to me more briefly". It shows a rules change before writing it.

## End the session with distill

Say **distill**. It writes what this session changed into files: today's log in `memory/daily/`, plus facts, decisions and tasks. Open the vault in your file manager (Finder on macOS) and look: that is the memory. The chat is not.

You can then archive the chat using your app’s sidebar controls. Archiving only hides the chat from the list. It is not the vault's `archive/` folder, which is where original documents are kept.

## Permission modes: how often it asks you

**In Claude Code’s desktop app**, the mode menu next to the message box sets which actions need your click. The app offers **Manual**, **Accept edits**, **Plan**, **Auto** and **Bypass permissions**.

- **Auto** is a good start: it asks before some actions and lets ordinary ones through. Stay here until you have seen what it asks.
- **Bypass permissions** asks nothing. It has to be allowed first (Settings → Claude Code → "Allow bypass permissions mode", on Pro and Max), and then chosen for each session.

Read this before choosing bypass:

> Bypass removes the app's approval prompts. Autarkeia still tells the agent to ask before sending, paying, deleting or changing rules, but those instructions are not a lock. A mistake can run, including a command that sends something out, without another prompt.

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

Codex (OpenAI) and Grok (xAI) can read your vault and review what Claude did (or, if you work in Codex, Grok and a separate Codex can). Setup, sign-in and what leaves your computer: [second-opinion.md](second-opinion.md). A printed version number proves a reviewer is installed, not that it is signed in; the guide's "Check it works" section has a real test ("brainstorm: test that codex answers").

## Email

The **email** command reads emails you save into `inbox/`. It does not open your Gmail. A Gmail connection you set up in another app (for example Cowork) stays there.

## Working with projects

Everything starts in the vault. When one piece of work or life grows a shape of its own, say **new project** and name it. It gets its own folder and memory, and, sooner or later, its own rules: who else is involved, what stays inside it, what to watch. The vault's rules always hold; a project's rules add to them. Keep opening the vault folder, not the project.

## What is in your vault

| Path | What it is |
|---|---|
| `AGENTS.md` | The vault's rules: how to talk to you, how to work (act then report, one recommendation and one question, a record is a claim until the file is opened, when you contradict the record it asks once and keeps both lines, never guess a date), what needs your yes, what never leaves. Every session reads it: Codex and Grok directly, Claude through `CLAUDE.md`. Change rules here, or ask your agent to. |
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
