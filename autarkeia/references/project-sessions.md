# Vault and project sessions

Open a project for focused work. Open the vault for planning across projects, reflection about your whole life, or creating your first project. Starting in a project supplies the default topic; it is not a technical read or network boundary.

## Find the instructions before reading memory or writing

Read `AGENTS.md` in the opened folder. Claude's `CLAUDE.md` normally contains only `@AGENTS.md`; if that import was not loaded, read `AGENTS.md` explicitly. A legacy vault may instead have its full contract in `CLAUDE.md`.

- A vault contract identifies this folder as the vault and describes its memory and Projects rules. Verify its three files `memory/facts.md`, `memory/decisions.md`, and `memory/tasks.md`. Those files alone do not identify a vault: a project has them too.
- A project instruction identifies this folder as a project and names its vault contract with a relative path. Resolve that path relative to the project folder, not the shell's later working directory. Read the target contract and verify it describes the enclosing vault, that its three memory files exist, and that the project's resolved path is inside that vault's `projects/`. Read the enclosing project instructions from outermost to innermost before the active project's own rules. Each child's recorded parent must match its actual enclosing project. Do not follow a symlink out of the vault.
- Missing, unreadable, inconsistent or ambiguous references: stop before writes and ask the user to identify the vault or approve correcting the reference. Do not search the disk, create a replacement vault, or infer a vault from `memory/facts.md`. An older project without these instructions may still be used from a session opened at its vault; directly opening it requires adding the short project instructions with the owner's approval.

Use resolved paths for subsequent operations. Moving the whole vault preserves relative references. Moving a project on its own may require correcting them. These checks prevent ordinary mistakes; they are not proof against maliciously edited instructions.

## Focus and ownership

The opened project is the default focus until the user explicitly names another scope. The vault is the default when opened at its root. Do not ask which project on every turn. When a user explicitly switches, read the new scope's rules first and say once that the focus changed; do not change files merely to remember a chat's focus.

Unqualified paths in a skill (`memory/`, `docs/`, `archive/`, `inbox/`, `reviews/`, `NEXT-ACTIONS.md`) are relative to that skill's active scope, unless it explicitly says vault-level. `projects/<name>/` means the project's actual path from the vault, which may include parents; never append it to the current project path.

Project work goes to that project's files, including its own `memory/daily/` log, created when first needed. Clearly personal, cross-project information belongs to the vault; opening a project does not turn every statement into a project fact. Decide the owner from the content and the user's request. Ask only when genuinely unclear. Read the owner's rules before writing. Do not copy a whole mixed conversation into one log.

Vault rules always apply; enclosing project rules also apply to children. A child may add stricter rules, never loosen its parents. Read parent instructions for inheritance; do not read parent or sibling memory merely because it exists. Private-content and no-pointer rules govern every output, including the parent project's overview and the chat's cross-project summaries. A no-pointer child contributes nothing identifying it to any ancestor's files.

Project facts, decisions, tasks and full log entries stay with their owner. A vault log may carry a permitted one-line pointer; it never needs a duplicate of project content. Existing files are not automatically moved by this update.

## Whole-vault and focused commands

**Setup** is for the vault's owner, once. From a project, identify its vault and explain that first setup runs in a fresh vault session; do not create vault folders in the project or repeat personal onboarding there.

**Daily debrief**, **weekly debrief**, **realign**, **health-check**, **improve**, and **sparring** use the active scope. A project debrief is about that project. For whole-life reflection or a combined work picture, use the vault, or explicitly ask for the whole vault in the current chat. Do not silently broaden a focused command.

For **realign** and **health-check**, include the active scope and its descendant projects. At vault level start in `projects/`; inside a project start with its child project folders. A project has the three memory files; a nested project also has the project instructions above. Read rules before memory. Do not descend into `memory/`, `docs/`, `archive/`, `inbox/`, `reviews/`, hidden directories or symlinks when looking for projects: filed copies are not live projects. A malformed declared project is a finding, not permission to recreate it. Older first-level projects with no instructions remain discoverable from the vault. No fixed nesting limit.

Project health checks check its three memory files and instruction references, not the vault's required folder set. Missing daily logs, inboxes or document folders are normal until needed. Keep the existing approval rules for repairs. A project overview is its own `NEXT-ACTIONS.md`; the vault overview is the combined view. Neither rewrites the other's file.
