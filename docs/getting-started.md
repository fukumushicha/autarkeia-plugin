# Getting started

Your first hour, step by step, in the Claude desktop app. The [README](../README.md) says what this is and why; this guide is the clicks.

Button names change between app versions. If one here does not match what you see, look for the nearest equivalent; the steps stay the same.

## 1. What you need

- A paid Claude plan (Pro, Max, Team or Enterprise). The free plan does not include Claude Code.
- The Claude desktop app. It has a **Code** tab: that is where this plugin runs. Cowork and ordinary chats do not load it.
- Claude Code itself, installed once in Terminal (open Terminal from Applications → Utilities and paste this line):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

It shows no progress while it downloads. When it finishes, open a new Terminal window and run `claude --version`. A version number means it worked. This command is Anthropic's own; their install page has the details and the Windows version: https://code.claude.com/docs/en/setup

## 2. Install the plugin and make your vault

In Terminal:

```bash
claude plugin marketplace add fukumushicha/autarkeia-plugin
claude plugin install autarkeia@autarkeia-plugin
```

You may see `SSH not configured, cloning` before `Successfully added marketplace`. That is fine, as long as the success line follows.

Then make your vault, a folder of your own that starts as a copy of the template:

```bash
cp -R ~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template ~/Documents/my-os
```

Quit the Claude app completely and open it again, so it sees the plugin.

## 3. Open the vault in the Code tab

1. In the **Code** tab, start a new session.
2. Choose the project folder: pick `Documents/my-os` (use the option to choose a folder, not a recent one, the first time).
3. When it asks whether to trust the folder, say yes. It is your own folder.
4. Type `/`. The plugin's commands appear in the list with its name, for example **autarkeia:setup**. If they do not, quit and reopen the app.

Always open the vault folder itself, never a folder inside it. Projects live inside the vault, and the vault's rules apply to all of them.

## 4. Run setup

Type **setup** and answer one question at a time: your name, your language, what this vault is for, how it should talk to you, what comes first in your life, and one real job. Skip any question you are not ready for; it waits.

When it wants to change its own rules (how to talk to you), it shows you the lines first and writes them only after your yes. That is on purpose: the AI does not change its own rules on its own.

Setup runs once. Later, to change something it asked, just say it in any session: "call me Sam", "my priorities have changed", "talk to me more briefly". It shows a rules change before writing it.

## 5. End the session with distill

Say **distill**. It writes what this session changed into files: today's log in `memory/daily/`, plus facts, decisions and tasks. Open the vault in Finder and look: that is the memory. The chat is not.

Then archive the chat: hover over the session in the sidebar and click the archive icon. Archiving only hides the chat from the list. It is not the vault's `archive/` folder, which is where original documents are kept.

## 6. Permission modes: how often it asks you

The mode menu next to the message box sets which actions need your click. The desktop app offers **Manual**, **Accept edits**, **Plan**, **Auto** and **Bypass permissions**.

- **Auto** is a good start: it asks before some actions and lets ordinary ones through. Stay here until you have seen what it asks.
- **Bypass permissions** asks nothing. It has to be allowed first (Settings → Claude Code → "Allow bypass permissions mode", on Pro and Max), and then chosen for each session.

Read this before choosing bypass:

> Bypass removes the app's approval prompts. Autarkeia still tells the agent to ask before sending, paying, deleting or changing rules, but those instructions are not a lock. A mistake can run, including a command that sends something out, without another prompt.

## 7. Effort: how thorough the work is

The effort setting next to the model sets how long and how carefully it works on a request. It does not change what it is allowed to do; that is the permission mode.

- **Medium** for everyday work.
- **High** or above for something that matters and must be right, especially reviewing work an earlier session did. A fresh session at high effort is a good reviewer.

Higher effort uses more of your plan's limits. The usage view shows how much is left.

## 8. One task per session

Long sessions use your limits faster, and when a conversation gets very long the app shortens it, so detail can be lost before you save. The habit:

1. One task per session.
2. **distill** before you close it.
3. New session for the next task.

If a new topic comes up halfway, say **handover**. It writes a short note with the goal, what is done, what was decided and the next step, and gives you one line to paste into a fresh session. Then distill the old one.

You can run several sessions at once on different work. A session sees another session's work only once it is saved to a file; it does not see the other chat. Sessions share some files (the daily log, the registers, `NEXT-ACTIONS.md`), so avoid two sessions changing the same file at the same moment.

## 9. Bring in what you already have

Your first day does not have to start empty. If you already keep notes, documents or a project in another tool, ask Claude to look at it and propose how to bring it in. Example requests:

- "Audit my project in <tool> and prepare a plan to bring it into this vault."
- "Audit the folder <path>. Copy the originals into the archive. Do not move or delete anything."

What helps:

- **Say where things are** rather than attaching a whole folder. A project in another app may not be a folder on your disk at all; its documents may live only inside that app. If so, say so, or export them.
- **Copy, do not move.** Keep the old copies until you decide. Nothing is deleted without your yes.
- **Earlier AI output is marked as such**, not treated as fact. Rules from another tool are material to read, not rules to adopt.
- **One person, one project.** A family member's papers belong in their own project, not yours.
- **Knowledge moves; automations stay.** Facts and documents come into the vault. Connections (Gmail in another app, scheduled jobs, databases) keep running where they are.

## 10. Recordings

A recording of an appointment or a call is an original, like a scanned letter.

1. Get the file onto the Mac (from a phone: share or AirDrop the voice memo).
2. Drop it in the vault's `inbox/` and say **librarian**. This is better than attaching a medical recording in the chat.
3. It files the audio, then proposes a transcript. That needs a transcription tool already on your Mac (Whisper is one); it runs on your computer, takes a while for a long recording, and stops if you close the laptop. If there is none, it says so. It will not install one or send the audio online without your yes.

The transcript itself is read by Claude like any other file, so it goes to Anthropic. Transcribing locally keeps the audio on your Mac; it does not keep the transcript there.

## 11. Two computers, and backup

- **Sync**: put the vault in a folder that syncs (Google Drive, Dropbox, iCloud or similar) and open the same folder on both machines. Wait until it has finished syncing before starting a session on the other machine. Keep the folder fully downloaded: a sync that swaps files for online-only placeholders breaks reading.
- **Backup** is a copy somewhere else that survives a dead or lost disk. Version history on the same disk (for example `git`) is not a backup.
- Whoever syncs or backs up the folder holds a copy of everything in it, health records included. Choose on purpose.
- Code you write with Claude belongs on GitHub or similar, not in the synced vault.

## 12. Settings worth knowing

All optional.

- **Remote Control**: carry on a session from your phone while the computer stays on. Turn it on per session, or for all new sessions in Settings → Claude Code.
- **Claude in Chrome**: lets Claude use websites in your browser. Only if you want that.
- **Notifications**: useful when several sessions run at once and one is waiting for you.
- **Automatic plugin updates**: off by default for this plugin. Type `/plugin` in a session, open the Marketplaces tab, choose `autarkeia-plugin`, then **Enable auto-update**. New versions arrive when a session starts and are used from the next session. Changes to your vault's own rules still come only through **health check**, after your yes.

## 13. Second opinions

Codex (OpenAI) and Grok (xAI) can read your vault and review what Claude did. Setup, sign-in and what leaves your computer: [second-opinion.md](second-opinion.md). A printed version number proves a reviewer is installed, not that it is signed in; the guide's "Check it works" section has a real test ("brainstorm: test that codex answers").

## 14. Email

The **email** command reads emails you save into `inbox/`. It does not open your Gmail. A Gmail connection you set up in another app (for example Cowork) stays there.
