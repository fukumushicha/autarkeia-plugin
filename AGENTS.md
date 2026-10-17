# Working on this repository

These rules are for anyone changing the plugin itself: people and AI agents (Claude, Codex, Grok). They are not part of the plugin and are not installed with it.

## Keep each document responsible for one job

Every change a user could notice updates the user documentation **in the same commit**. That covers a skill's behaviour or wording a user sees, a command, the vault template, the install steps, the version, and anything in `tools/`.

- `README.md`: purpose, capabilities, supported apps, cost, version and the agent-led entry point. Keep installation commands out of it.
- `INSTALL.md`: the single shared installation procedure for agents and people; prerequisites, fresh installs, existing vaults, verification, updates, migrations and troubleshooting.
- `docs/getting-started.md`: first personal setup and everyday use after installation, for both apps; label app-specific controls explicitly.
- `docs/second-opinion.md` when `brainstorm` or the outside reviewers change.
- A tool's own README (for example `tools/email-stager/README.md`) when that tool changes.

Update the relevant document in the same commit. Touch the README when its overview, links or version change. A commit that changes `autarkeia/`, `vault-template/`, `tools/` or `docs/` without touching `README.md` says why in its message, on a line of its own: `README: unchanged (<reason>; updated guide: <path or not applicable>)`.

Before pushing, read the README and affected guides against what the change does, and check their links. Documentation that describes old behaviour is a bug, the same as broken code.

## One plugin, two apps: Claude Code and Codex

The skills, references and vault template exist once and serve both apps. Only the install files are separate. Keep the two in step on every change:

1. **The version is in four places, always the same number:** `.claude-plugin/marketplace.json` (twice: `metadata.version` and the plugin's `version`), `autarkeia/.claude-plugin/plugin.json`, `autarkeia/.codex-plugin/plugin.json`; plus the README title. A version left behind in one file means that app's users never see the update. Check before pushing: `grep -rn '"version"' .claude-plugin autarkeia/.claude-plugin autarkeia/.codex-plugin`.
2. **Skill wording works in both apps.** Name skills in plain words (**distill**, the distill skill), never as slash commands (`/distill`). A path that differs between the apps gives both (`~/.claude/plugins/marketplaces/autarkeia-plugin/...` and `~/.codex/.tmp/marketplaces/autarkeia-plugin/...`). Say "Claude Code or Codex", or "the app", where either can host. Claude-only steps (`/plugin`, `/autarkeia:distill`, `.claude/` fallback) are fine only where the text says they are for Claude.
3. **One procedure, two app paths.** Check any installation or update change in `INSTALL.md` against both app paths in the same commit. Keep personal setup in `docs/getting-started.md`, shared by both apps. Do not duplicate installation commands there or in the README.

Before publishing a release, install it once in each app from the pushed branch or a local path: `claude plugin validate .`, and in Codex a scratch `CODEX_HOME` with `codex plugin marketplace add <path>` and `codex plugin add autarkeia@autarkeia-plugin`, then confirm `codex debug prompt-input` lists every skill.
