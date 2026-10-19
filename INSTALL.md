# Install Autarkeia

One installation procedure for an agent working on your computer or a person following it manually. [README](README.md) explains the product; [Getting started](docs/getting-started.md) begins after installation.

**Default: let your agent do the routine steps.** Read this guide before running commands. Inspect the existing installation, choose the relevant path, preserve the owner’s files, then verify the result. An agent with only web access cannot perform these local steps: use a local Claude Code or Codex session, or follow the same commands in Terminal.

The commands and paths below are macOS examples. For Windows or Linux, use the vendor’s instructions for that system, resolve the actual home and marketplace locations, and adapt the file-copy commands to the shell. Do not run macOS paths blindly or claim those platforms were tested here.

## 1. Inspect before installing

- Use the owner’s chosen app. If none is named and exactly one of Claude Code or Codex is ready, use that; if both are ready, ask which they want. Installing both is optional.
- Check the selected command: `claude --version` or `codex --version`. A version number proves the command exists, not that it is signed in or that the plugin loads.
- Inspect configured marketplaces and installed plugins with `claude plugin marketplace list` and `claude plugin list`, or `codex plugin marketplace list` and `codex plugin list`. If a command is unavailable, inspect that command’s help and the vendor’s current documentation; do not invent a substitute.
- Use a vault path the owner has already supplied. Otherwise propose `~/Documents/my-os` and confirm where they want their personal files. Check that exact destination, including whether it is a symlink. Do not search through unrelated personal folders.
- An existing vault has its rules in `AGENTS.md` (or a full `CLAUDE.md` in older vaults) and memory files such as `memory/facts.md`. Read its rules before working inside it. If the destination exists but is not clearly a vault, stop before copying and resolve the destination with the owner.

**Choose the path:** for a fresh install, continue below. If Autarkeia is already installed in this app, use [Updates](#updates), then reuse your existing vault or create one in step 4 if you do not yet have one. To add a second app, install the plugin in that app but reuse the existing vault; skip template copying. Never install another copy simply because you cannot see the first one.

## 2. Prerequisites, only if missing

You need Claude Code or Codex and an account that can use it. This guide uses a Claude plan with Claude Code access or a ChatGPT plan with Codex access; it does not set up API billing. Do not buy a plan, accept terms or change account settings on the owner’s behalf.

If no local agent is available yet, the owner can do this section manually and then paste the README’s installation request into that agent. In macOS, open Terminal from Applications → Utilities.

### Claude Code

Follow [Anthropic’s installation instructions](https://code.claude.com/docs/en/setup). Its macOS installer is:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

The installer may show no progress while downloading. When it finishes, open a fresh Terminal and check `claude --version`. Run `claude` and let the owner complete sign-in. If they prefer the desktop app, use the **Code** tab, not Cowork or ordinary chat; the command line is used for the plugin commands below.

### Codex

Follow [OpenAI’s installation instructions](https://developers.openai.com/codex/cli). Its macOS installer is:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Open a fresh Terminal and check `codex --version`. Run `codex` and let the owner choose **Sign in with ChatGPT** and complete sign-in.

For either app, let the owner handle credentials, trust prompts and consent. Do not enable bypass permissions, change security settings or install optional reviewers to finish this installation. If an app restart is needed, save or hand over the active work first and ask the owner to reopen it.

## 3. Install the plugin in the selected app

Skip a marketplace-add command if the expected marketplace is already configured. Confirm it refers to this repository before reusing it; if the name points somewhere else, show the owner the configured source and stop before removing or replacing it.

### Claude Code

```bash
claude plugin marketplace add fukumushicha/autarkeia-plugin
claude plugin install autarkeia@autarkeia-plugin
```

### Codex

```bash
codex plugin marketplace add fukumushicha/autarkeia-plugin
codex plugin add autarkeia@autarkeia-plugin
```

Check the command results and plugin inventory. An error or a partial download is not a completed install. A warning such as `SSH not configured, cloning` can be harmless if the command subsequently reports success; verify the result rather than judging the warning alone.

## 4. Create a new vault or reuse an existing one

**Existing vault:** skip this copy step. Use the same folder, even when adding another app. See [Older vaults](#older-vaults) if its rules predate `AGENTS.md`.

**New vault:** resolve the chosen absolute destination and confirm it does not exist, including as a symlink, immediately before copying. Confirm the source template contains `AGENTS.md` and `memory/facts.md`. Only then run the relevant command below, substituting the owner’s agreed destination if different. The destination’s parent folder must exist. Never copy into, merge with, or replace an existing folder.

After a standard GitHub install, the template is normally in the marketplace checkout below. A custom `CODEX_HOME` or Claude configuration directory changes these paths; inspect the marketplace inventory rather than assuming the default.

Claude Code:

```bash
cp -R ~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template ~/Documents/my-os
```

Codex:

```bash
cp -R ~/.codex/.tmp/marketplaces/autarkeia-plugin/vault-template ~/Documents/my-os
```

If the source is absent, locate the configured marketplace checkout. If it is still absent, stop and report the exact marketplace path checked. Do not create a replacement template from memory. The plugin supplies the skills; your separate vault holds your own rules and personal information.

## 5. Open the vault and verify

Start a fresh session in the vault root. For the example path:

Claude Code:

```bash
cd ~/Documents/my-os
claude
```

Codex:

```bash
cd ~/Documents/my-os
codex
```

In Claude’s desktop app, start a session in the **Code** tab and choose that same vault folder. If the plugin does not appear, fully quit and reopen the app after saving active work. Let the owner answer any folder-trust prompt.

Before declaring installation complete, verify in that fresh session:

1. The selected app lists `autarkeia@autarkeia-plugin` as installed and enabled, with its version.
2. The working folder is the intended vault root. `AGENTS.md`, `memory/facts.md`, `memory/decisions.md` and `memory/tasks.md` exist. An older vault may need the consented rule migration below first.
3. The agent reads the vault’s actual rules. Codex reads `AGENTS.md`; Claude reads it through the vault’s `CLAUDE.md` import. Ask it to name the rule file it read and summarize the approval boundaries from that file. Merely finding the file is not this check.
4. The Autarkeia **setup** skill is available and its instructions can be read. In Claude, type `/` and look for `autarkeia:setup`; in Codex, inspect the available skills or ask it to identify the Autarkeia setup skill. Do not substitute the repository’s contributor instructions for the vault’s rules.

Report the app and plugin version, vault location, checks that passed, and anything still requiring sign-in or a restart. If a check could not run, say installation is awaiting verification and give the exact remaining step.

**Installation and personal setup are different.** Once verification passes, say **setup** to begin [Getting started](docs/getting-started.md). The owner supplies their name, priorities and first job, one question at a time. Never invent their answers or mark personal setup complete because the plugin installed. If setup was completed previously, continue normal work instead.

## Updates

Update the plugin without replacing an existing vault. If the plugin is installed but you do not yet have a vault, run the update commands, then return to step 4 to create one before attempting the verification in step 5. In Claude Code:

```bash
claude plugin marketplace update autarkeia-plugin
claude plugin update autarkeia@autarkeia-plugin
```

In Codex:

```bash
codex plugin marketplace upgrade autarkeia-plugin
codex plugin add autarkeia@autarkeia-plugin
```

Save active work, then reopen Claude or start a fresh Codex session. Repeat the installation checks above. Never copy the template over your existing vault. New skills and fixes arrive with the plugin. Your existing contract is not replaced. **Health check** proposes the specific template updates it knows how to compare, including the v0.4.10 safety additions; it does not automatically synchronize the whole contract. Approve only the proposed changes you want.

**Human-step rule (2026-10-20):** after updating the marketplace above, ask your agent: “Add only the ‘When a human step is needed’ bullet from the updated vault template to my vault's rules, preserving everything else.” The template is `~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template/AGENTS.md` for Claude Code or `~/.codex/.tmp/marketplaces/autarkeia-plugin/vault-template/AGENTS.md` for Codex. Read that exact bullet, show it for approval, then add it once to the vault's own `AGENTS.md` (or its older `CLAUDE.md` contract). If the updated template does not contain the heading, report that the rule could not be retrieved; do not reconstruct it from a summary. **Health check does not insert this rule.**

**Automatic updates in Claude Code:** off by default for this plugin. If the owner wants them, type `/plugin`, open **Marketplaces**, choose `autarkeia-plugin`, then **Enable auto-update**. Claude fetches updates at session start and uses them in the next session. This does not change the vault’s rules. The Codex path here is the manual update procedure above; do not assume Claude’s menu exists in Codex.

## Older vaults

A vault made before v0.4.2 has its rules in `CLAUDE.md` and no `AGENTS.md`. It keeps working in Claude Code; Codex does not read those rules until they move. In the vault, say **health check**: it reads the older contract and offers to move the rules to the new layout. Review and approve that change, then start a fresh session before normal work. A vault made before v0.4.4 has no `archive/`, no "How to work" section in its rules, and a four-column `docs/register.md` without hashes; it keeps working. Copy `archive/README.md` and that section from `vault-template/AGENTS.md` when you want them, or ask your agent to; the librarian adds a hash column to the old register the first time it files something.

A vault made before v0.4.5 still offers `git init` as a backup in its rules, and its example of a private project uses an older name. Say **health check**: it shows the current lines and replaces only those after your yes, leaving everything you wrote yourself.

Distill’s bundled local transcript reader requires Python 3 (`python3 --version`). It does not change retention or turn on history recording. If Python or retained history is unavailable, extraction reports partial coverage. Older vault rules may still list checkpoint: the skill has been removed, but do not delete earlier checkpoint records. Update that obsolete skill-table row only with the owner’s approval, preserving their other rules. Handover remains available.

A vault made before v0.4.10 may lack **Source material and credentials**. The updated skills already apply those rules when invoked; ordinary conversations need the contract additions too. Say **health check** to compare and approve that section and the private-project urgent-log/overview wording, or ask your agent to show those exact additions from `vault-template/AGENTS.md`. Preserve your own rules; never replace the whole contract. Updating the plugin does not automatically make this change.

## Troubleshooting

- **Command not found:** open a fresh Terminal and check the vendor’s installation instructions. Do not repeatedly reinstall over an unexplained failure.
- **Marketplace or install command fails:** preserve the error and inspect the configured source, network access and command help. If GitHub access is the problem, download this repository through GitHub’s **Code → Download ZIP**, extract it into a separate folder, then add that absolute folder as the marketplace source with `claude plugin marketplace add /absolute/path/to/autarkeia-plugin` or `codex plugin marketplace add /absolute/path/to/autarkeia-plugin`. Use the same plugin install command for your app. The template is in that downloaded folder. A downloaded copy does not refresh from GitHub automatically; use the normal GitHub source once access works, after checking the existing marketplace configuration.
- **Skills missing:** check that the plugin is installed and enabled in the same app and configuration directory as the new session. Reopen the app. Do not scatter manual copies of skills into the vault to hide a failed installation.
- **Existing destination:** reuse it only if it is the intended vault. Otherwise choose a new location with the owner; never delete or overwrite it.
- **Rules missing in Codex:** inspect whether this is an older vault and follow the consented migration above, then start a fresh session.

Optional external reviewers have their own [second-opinion guide](docs/second-opinion.md); they are not prerequisites for Autarkeia.
