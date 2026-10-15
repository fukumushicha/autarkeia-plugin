# Second opinions from other AI models

The `brainstorm` skill gets you a second opinion on a decision, a document, or something an agent just did. Out of the box it asks a second Claude, which has a fresh context but the same training as the first. That catches slips; it does not catch the blind spots both share.

For a real second opinion, add a model from another company. Autarkeia can hand the review to **Codex** (OpenAI) or **Grok** (xAI). Each runs on your Mac, reads the files in your vault itself, and is blocked from changing them. That is the "agentic" part: the reviewer checks the actual file rather than trusting a summary of it.

## What you need

| | What it is | Account |
|---|---|---|
| **Claude Code** | You already have it. Hosts Autarkeia and the built-in Claude reviewer. | Your Claude account |
| **Codex CLI** | OpenAI's command-line agent | A ChatGPT account. OpenAI says Codex is included across ChatGPT plans, Free included, with usage limits that vary by plan. |
| **Grok Build** | xAI's command-line agent | An xAI account (sign in through the browser), or an xAI API key. Check x.ai for which plans include it. |

You can install one, both, or neither. With neither, `brainstorm` still works with the Claude reviewer.

## Install

Each of these is the vendor's own installer. Run them in Terminal.

**Codex** (official guide: https://developers.openai.com/codex/cli):

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Then run `codex` once, choose **Sign in with ChatGPT**, and finish the sign-in in your browser. Type `/quit` to leave.

**Grok Build** (official guide: https://docs.x.ai/build/overview):

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

Then sign in:

```bash
grok login
```

If either command says "command not found" afterwards, close Terminal and open it again.

## Check it works

```bash
codex --version
```

```bash
grok --version
```

Each should print a version number. You only need the ones you installed.

A version number proves the tool is installed, not that it is signed in. For a real test, open your vault in Claude Code and say **brainstorm: test that codex answers** (or grok). It sends a tiny question about a harmless file and shows the reply. A reply means it works end to end. "Not signed in" means: run `codex` (or `grok login`) in Terminal and sign in there, as in the Install section above.

## How to use it

In your vault, say:

| Say | Who reviews |
|---|---|
| **second opinion on** this decision | The built-in Claude reviewer |
| **send to codex** | Codex |
| **send to grok** | Grok |
| **all reviewers** | Every reviewer installed |

Nothing goes to Codex or Grok unless you name them. If you ask for a plain second opinion, Autarkeia uses Claude and tells you which outside reviewers are available.

What happens:

1. Claude writes its own view first and keeps it to itself, so it cannot steer the reviewer.
2. It writes a short packet in `reviews/` (or in a private project's own `reviews/`, where the answers then stay too): your question and which files to read.
3. Each reviewer reads those files in your vault and writes its answer next to the packet.
4. Claude puts the answers side by side. Where they disagree, you see both. It does not split the difference.
5. You get one recommendation and, if a decision is still yours, one question.

A review takes from one to several minutes per reviewer.

## What to know before you use it

- **Your vault is read-only to them, enforced by the Mac itself.** Codex runs with `-s read-only` and Grok with `--sandbox read-only`. If either tries to change a file in your vault, macOS refuses; we tested exactly this before publishing. Grok can still write in its own working folders (`~/.grok` and the system's temporary folders), which is why your vault must not live there.
- **The other company sees what the reviewer reads.** Whatever files Codex or Grok open are sent to OpenAI or xAI under your account, just as your conversations with Claude go to Anthropic. Read-only stops changes, not reading: a reviewer may open other files in your vault than the ones named. If a review touches your health, another person, or something you said was off the record, Autarkeia asks you before sending it out, even after you named the reviewer.
- **One known gap.** Grok's read-only setting stops file changes, but not its shell from reaching the internet. A file carrying hidden instructions, such as a web page or download you saved, could get Grok to send what it read somewhere else. Keep untrusted downloads out of reviews you send to Grok.
- **Keep your vault in an ordinary folder**, such as Documents. Grok's sandbox leaves temporary folders writable, so Autarkeia will not run Grok on a vault stored there.
- **It uses your own plan's limits.** A long review against a big vault is real usage. If you hit a limit, that is the plan, not a fault.

## If something goes wrong

- **"Not signed in"**: run `codex` (then choose Sign in with ChatGPT) or `grok login` again, in your own Terminal. Autarkeia never handles your password.
- **Grok returns almost nothing**: it sometimes stops on its first step. Autarkeia retries once on its own. If the second try also fails, it tells you the review did not finish and leaves that reviewer out.
- **"Command not found" inside Claude Code**: restart Claude Code after installing, so it sees the new command.
