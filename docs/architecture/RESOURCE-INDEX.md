# Resource index

Verified 2026-10-26 by Claude (claude-opus-5-5) from the MSI (`%USERPROFILE%`) and the public GitHub API. Each line says how it was checked. Nothing here is inferred from a name.

## Repositories

| Repository | Status | Role | Checked by |
| --- | --- | --- | --- |
| [POWDER-RANGER/powder-ranger-bot](https://github.com/POWDER-RANGER/powder-ranger-bot) | **Retired, reference-only** (project instructions §12). Last push 2026-10-25; open PRs #10, #11 (stacked), dependabot #6, #7, #12. Do not modify. | The only Æther / PR-REX codebase found; source of BRAND.md and the font. Governor, intent packets, motor model, NitroGen runner, Game Packs, site (GitHub Pages). | Local clone `~\Aether\powder-ranger-bot`, `git fetch`, REST `/pulls` |
| [MineDojo/NitroGen](https://github.com/MineDojo/NitroGen) | Third-party, upstream. Research-only license. | Reflex model server PR-REX calls over ZMQ (port 5555). | Local clone `~\Aether\NitroGen` at `3260844`; untracked `.venv` only |
| [POWDER-RANGER/.github](https://github.com/POWDER-RANGER/.github) | Org community files. Last push 2026-07-16. | Possible later home for org-wide AACP templates. | Public API listing |
| [POWDER-RANGER/powder-ranger.github.io](https://github.com/POWDER-RANGER/powder-ranger.github.io) | Portfolio site. | Not an Æther component. | Public API listing |

**No active Æther repository exists** among the 52 public repositories under POWDER-RANGER (DECISIONS D-009). Private repositories were not enumerable at discovery time (before `gh` was installed). Unauthenticated listing sees public repositories only.

Not Æther, despite similar names: `PS4RemotePlayInterceptor` (fork), `SerpentAI` (archived fork), `RLBotGUI` (archived fork), `dojin-d`, `nine-realities-netcode`.

## Branches of the retired powder-ranger-bot (2026-10-26, read-only)

| Branch | State |
| --- | --- |
| `main` | `4c6963d`, merge of PR #8 |
| `claude/dev-friendly` | PR #10 → main. First MSI session results; NitroGen not gated on the firewall rule |
| `claude/main-designations` | PR #11 → `claude/dev-friendly`. Designations, BRAND.md v1, TREE.md |
| `claude/brand-baseline` | BRAND.md v1 only; superseded by `claude/main-designations` (same commit content plus more) |
| `docs/aether-pr-rex-charter-architecture` | Points at the same commit as `main`. **Empty**: no charter or architecture content was ever pushed to it |
| `claude/aether-name`, `claude/aether-steel`, `claude/aether-rewrite`, `pages/add-social-metadata` | Merged |

## Local working copies on the MSI

| Path | What it is |
| --- | --- |
| `~\Aether\aether-platform` | **Local git repository for `POWDER-RANGER/aether-platform` (no remote yet)**: charter, design system, ecosystem docs, AACP proposal |
| `~\Aether\powder-ranger-bot` | Clone of the retired repository on `claude/dev-friendly`; its `.venv` (Python 3.11.16) is used as the test interpreter. A local branch created 2026-10-26 was deleted unpushed |
| `~\Aether\checks\design` | Scratch: render probes, screenshots, one-off patch scripts (not part of any repository) |
| `~\Aether\powder-ranger` | **Not a git repo.** Extracted from `~\Aether\powder-ranger.zip` (2026-10-21). An older snapshot of the same package; treat as stale |
| `~\Aether\NitroGen`, `~\Aether\weights`, `~\Aether\wheels` | NitroGen clone, model weights (`ng.pt`), cached wheels |
| `~\Aether\*.ps1`, `*.log`, `*.done` | Setup and test run scripts and their logs from 2026-10-20 to 2026-10-24 |
| `~\.powder_ranger\` | `log.key` (machine-local log sealing key). STOP file location |

## Discovery targets named in the initiation directive

Searched for by file name under `~\Aether`, `~\Documents`, `~\Downloads`, `~\.powder_ranger` and in every branch of powder-ranger-bot. **None exist.** They may live in a Claude Project or a ChatGPT conversation, which this session cannot read.

| Requested file | Found | Nearest existing equivalent |
| --- | --- | --- |
| `AETHER_MASTER_CONTEXT.md` | No | The Æther Project description and instructions; `docs/architecture/ECOSYSTEM.md` |
| `AETHER_DOCUMENTATION_INDEX.md` | No | `README.md` of this folder; reference `docs/TREE.md` |
| `AETHER_PROJECT_STATE_AND_VERIFICATION.md` | No | Reference `docs/VERIFICATION.md`; `interfaces/shared/design/DESIGN-SYSTEM.md` §10 for the design system |
| `AETHER_AGENT_HANDOFF_AND_CONTINUITY.md` | No | `protocols/aacp/specification/AACP.md` §8 |
| `AETHER_REQUIREMENTS_REGISTRY.md` | No | None. Requirements are spread across README rules of engagement and SECURITY.md |
| `AETHER_DECISION_REGISTER.md` | No | `docs/decisions/DECISIONS.md` (this folder) |
| `AETHER_RISK_REGISTER.md` | No | `SECURITY.md` (threat model) and `docs/REVIEW-2026-10.md` (findings F1–F13) |

Not recreated as seven files (D-007). A requirements registry belongs in the active repository at M1.

## Tools available to this session (2026-10-26)

| Tool | State |
| --- | --- |
| Shell on the MSI (Desktop Commander, PowerShell) | Working. The Windows interface for every local step. No separate "Windows MCP" server is installed. |
| Folder link to the MSI for file transfer | Unavailable 2026-10-26: the desktop window was not open for the access prompt |
| Microsoft Edge headless on the MSI | Working; used for render checks |
| git on the MSI | 2.56.0; credential manager configured; fetch works |
| `gh` on the MSI | 2.103.2, installed 2026-10-26 to a recorded non-default path; exact paths in the local workstation record `%USERPROFILE%\Aether\ENVIRONMENT.md` (kept out of this public repository) |
| GitHub from the cloud session | Token invalid; REST limited to repo-scoped paths |
| Public GitHub REST from the MSI | Working, unauthenticated (public data only) |
| Python | 3.14 system; project `.venv` (3.11) in the clone |
| Node | 24.19 |
