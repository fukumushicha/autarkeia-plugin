# Autarkeia v0.4.9

A living record of you, in files you own. It remembers your past, runs your present, and carries you forward with whatever AI is best at the time.

## Start here

**Ask your agent to install it.** Give an agent that can work on your computer this request:

> Install Autarkeia from https://github.com/fukumushicha/autarkeia-plugin, following its INSTALL.md. Check what is already installed and whether I already have a vault. Preserve existing files and permissions. Complete the installation checks, then help me start the first session. Ask me when you need sign-in, consent or a personal choice; do not answer setup questions for me.

The agent handles the commands; you provide access and your own answers. An ordinary web chat without access to your computer can explain the steps, but cannot perform the local installation.

- [Installation guide](INSTALL.md): the shared procedure for agents and people, including updates and existing vaults. If you do not have an agent yet, start with its prerequisites.
- [Getting started](docs/getting-started.md): your first real job and everyday use, after installation.
- [Changelog](CHANGELOG.md): what changed in every published version, including upgrade notes.

Autarkeia runs in **Claude Code or Codex**, using your own account. Claude's ordinary chat and Cowork are not the Claude Code installation described here. The installation guide uses macOS examples; it identifies what needs adapting on other systems.

## Why this exists

A life runs on many fronts at once: work, money, health, family, the things you are building. Each AI chat sees one conversation and forgets it. Nothing connects what you decided in March to what you are asking today.

**What this is.** Not the AI. The AI is hired help, replaced every few months by something better. This is the part that does not change: everything written down about you, plus the rules for how any AI works with you. Separate yourself from your tools, and the tools can keep improving without you starting over.

It does three things. It remembers your past: documents as they arrived, what was true, what you decided and why. It works your present: the open work across every part of your life, checked against what you said comes first. And it carries you forward: whatever model is best next year reads the same files and picks up where the last one left off.

Two layers keep it honest. The record is the originals, untouched. The story is what the system builds from them: facts, decisions, the patterns it notices. A record without the story is a pile of files; a story without the record flatters. You get both.

**The goal is your whole life, available to whatever AI you work with**, in files you own: what is true now, what you decided and why, what is still open, and the originals themselves, kept as they arrived, so a better model later can read them again and find what today's missed. Memory is the summary; the archive is the evidence. One without the other is half a system. The archive is organised the way a person looks for things: first the part of life (official documents, money and tax, health, homes, travel, companies and projects, photos and memories), then the person or thing, then the document type. Nothing is created until a document arrives.

**How this differs from a personal agent.** The personal agents you have heard of, Instinct, Meta's Muse and the ones that will follow, learn you inside their own service. The memory sits on the company's computer. You usually cannot open it, correct it or take it with you; what you tell the agent may be used to train the next version unless you opt out; and when the company changes direction, or a better model appears somewhere else, the years of context stay behind.

Here the memory is a folder on your own disk. You can open every file and see exactly what the AI knows about you. The model is only the reader: Claude today, something else when something else is better, and the folder does not care. The AI reads what it needs from it, and what it reads goes to the company that runs that AI (Anthropic for Claude, OpenAI for Codex), the same as your chats. Nothing is handed to anyone else, deleted, sent, posted or paid without your yes. Those are rules the AI follows, not a lock; how much it may do without asking is set in the app (see [Getting started](docs/getting-started.md), permission modes).

The two are not enemies. You can keep a personal agent for errands and keep your life here. The question is only where the record of you lives: on their side or yours.

The test for every line in this README: when a friend asks what you are building, should they remember that AI works for you, or that something of you lasts?

The ideas behind it:

- **Models come and go; your memory should not.** AI models are replaced every few months. The files stay. Any capable model can read them, so a better model inherits everything instead of starting over.
- **Use the best model for the job, with everything it needs to know.** The vault belongs to no vendor. Claude Code or Codex runs it day to day, with the same skills; Codex and Grok can read the same files for a second opinion.
- **Plain files over databases.** You can open, read, back up and move every file yourself. Nothing is locked in an app, and you can see exactly what the AI knows about you.
- **Keep the original next to the summary.** Documents stay as they arrived. A future model can re-read them and pull out what today's missed.
- **Questions instead of blank pages.** The daily and weekly debriefs ask you a few questions and write down the answers. Nobody has to keep a journal.
- **Your priorities, written down.** `PRIORITIES.md` holds what matters to you, in order, and the weekly review checks your week against it.
- **No structure built in advance.** Folders and projects appear when real use needs them, not because a template said so. A project gets its own rules when it needs them, not before.
- **You decide; it operates.** It writes your notes without asking every time. It never sends, posts, pays or deletes without your yes.

The name comes from the Greek *autarkeia*: self-sufficiency, having what you need within your own reach.

## Skills

Skills are repeatable ways of working with your agent. Ask in ordinary language; the agent follows a defined process, reads the relevant records, and saves the result when the workflow calls for it. You do not need to learn special commands.

| Skill | What it does | What you gain |
|---|---|---|
| **Setup** | Asks about you, your priorities and one real job, then saves the first conversation about that work. | A useful starting point built around your life, without designing a whole system first. |
| **Distill** | Reads the retained conversation and saves important facts, decisions and tasks in the right place. | Less background to repeat in future chats, and useful decisions that survive the conversation. |
| **Daily debrief** | Reads relevant filed records before asking about your day, decisions and unfinished work, then saves what you approve. Reflection is optional. | A record of what matters while it is fresh, without writing a journal from scratch. |
| **Weekly debrief** | Reviews the week’s records and open work against your priorities, then asks what to carry forward. | A chance to notice when daily activity is pulling you away from what matters and choose your next focus. |
| **Handover** | Writes a briefing for a fresh chat: the goal, progress, relevant files and next step. | You can change conversations without reconstructing the whole task yourself. |
| **Librarian** | Proposes where to file a document and what to remember, then preserves the original and saves approved facts or tasks. Can also arrange local transcription of recordings. | Documents become useful context for future work, with the original evidence available to check. |
| **Email** | Reads emails saved into the vault, extracts useful information and separates real commitments from information. Does not open your mailbox or send replies. | Important requests enter your working records without every newsletter becoming another obligation. |
| **Realign** | Combines open tasks across projects into one overview of current work, waiting items and the inbox. | You can see what needs attention without opening every project separately. |
| **Health check** | Checks for missing files, old unfinished tasks, archive inconsistencies and possible credentials; reports problems and proposes repairs. | You can catch maintenance problems before they make the system harder to rely on. |
| **Brainstorm** | Gets a separate AI review of a decision, document or piece of work, then compares the findings and explains disagreements. | Another chance to spot weak assumptions, mistakes and overlooked alternatives before acting. Agreement is not proof. |
| **Improve** | Records recurring friction and proposes changes for your approval. | Annoyances can lead to deliberate improvements instead of recurring indefinitely or triggering unapproved changes. |
| **Outbound writing** | Drafts or proofreads a message using relevant facts from your records and your own voice, without sending it. | Less time reconstructing context and composing replies, while you control what goes out in your name. |
| **Sparring** | Helps you think through a question, challenges assumptions and points out tensions with your stated priorities. | Space to think with someone who pushes back, without automatically creating another task list. |

Distill uses the exact current conversation in local Claude Code and Codex. It reads retained original messages in sections, checks corrections and existing memory, and tells you when history is missing. Python 3 is needed for the bundled local reader. Retention or disabled history can limit recovery. Checkpoint has been removed; existing saved notes stay untouched. Handover still writes a separate note for a fresh session.

See [Choosing a skill](docs/getting-started.md#choosing-a-skill) for example requests and what each leaves you with. What goes into the vault is yours.

## Everyday use

When a task needs something only you can do, the agent prepares what it can within your authorization, gives you the exact remaining action, and continues after you report the result. It records completion only when the outcome is confirmed. Existing approvals still apply. New vaults include this rule. For an existing vault, ask: “Add only the ‘When a human step is needed’ rule from the current vault template to my vault's rules, preserving everything else.” Updating the plugin alone does not rewrite your vault's rules.

Work in your vault folder. Say **setup** for the first session, **distill** before closing a session, **daily debrief** at the end of a day and **weekly debrief** at the end of a week. Say **librarian** to file a document or recording. [Getting started](docs/getting-started.md) explains these habits, projects and what is in your vault.

Daily debrief stays within four questions. It uses relevant records already in your vault, helps you recall a lightly recorded day, and keeps private-project answers in the right place. Say **“Include reflection in this debrief”** to add what you would do differently and what you feel satisfied with; reflection is off by default. Later saves respect what you approved or declined. See [Daily debrief](docs/getting-started.md#close-the-day--daily-debrief).

Optional tool, not for day one: [`tools/genome-check/`](tools/genome-check/README.md) compares a raw genome file (a sequencing VCF, or a 23andMe or AncestryDNA download) with ClinVar, the public database of what DNA variants are known to mean, on your own computer, and shows what changed since the last check. Research-grade only. Its README has a request you can give your agent to fetch it, and says how to read the results.

## Cost

It runs on your own Claude or ChatGPT account. Thirteen skills against a vault that grows for a month is real usage; expect it to show in your plan's limits.

Day one can start with what you already have. The record compounds after that: it earns its place over weeks of real work.
