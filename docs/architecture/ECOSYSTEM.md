# Æther, PR-REX and AACP

What each owns, how they relate, and where the record disagrees with itself. 2026-10-26. Authority order: the Æther Project instructions, then owner statements, then repository documents. Items needing the owner are marked **[owner]**.

## 1. Definitions

| | Æther | PR-REX | AACP |
| --- | --- | --- | --- |
| What | The platform: application, orchestration, research laboratory, evidence management | The companion and its runtime inside Æther | Agent Accountability & Continuity Protocol: how AI agents build Æther |
| Serves | Players, researchers, operators, the owner | The player | Engineering agents (Claude, ChatGPT) and the owner |
| Owns | Research Mode and Companion Mode configurations, environments (ENV-xx), scenarios (SCN-xx, DG-xx), recording, evaluation, the application shell | Perception, world state, planning, reflex execution, recovery; acts only through the Governor | Tasks, provenance, evidence, review, acceptance, handoffs |
| Never owns | Controller output (Governor) | Controller output (Governor); AACP | Anything at runtime |
| Exists today | Reference codebase only (retired repo): CLI, config, packs, reports | Reference codebase only: reflex runner, motor model, voice and gaze parsers | Proposal: `protocols/aacp/specification/AACP.md` |

The Governor is the exclusive authority for companion-controlled controller output. PR-REX proposes; the Governor decides; the player overrides. Fixed by the owner; not a design variable.

## 2. Boundaries

```text
            ┌──────────────────────────── ÆTHER ────────────────────────────┐
            │  Research Mode │ Companion Mode   (separate configs, separate results)
 Player ───►│  player channels ──► GOVERNOR ◄── PR-REX  (reflex fast path │ supervisor slow path)
 (authority)│                        │                                       │
            │                        ▼                                       │
            │                 virtual controller ──► environment (screen only)
            │  capture · world state · recording · replay · scorecards · shell
            └────────────────────────────────────────────────────────────────┘
 AACP ── outside the runtime ── governs how agents change the repository
```

1. No controller-output path bypasses the Governor, in code, diagrams or UI.
2. PR-REX is never presented as the one in control.
3. AACP is never inside the runtime; PR-REX has no authority over AACP.
4. Research Mode results are never evidence for Companion Mode, and the reverse.
5. Core docs and interfaces use ENV-xx, SCN-xx and DG-xx, not commercial titles.

## 3. Research tracks

Intelligence and accessibility are equal tracks with separate specifications, metrics and results. Neither specification exists yet. Scorecard thresholds are frozen before gate testing and belong to the owner **[owner]**.

## 4. Contradictions and gaps

| # | Finding | Handling |
| --- | --- | --- |
| C1 | `powder-ranger-bot` is retired and reference-only (project instructions §12), yet it holds the only Æther codebase, with open PRs #10 and #11 pushed 2026-10-25. No other Æther repository exists among the 52 public POWDER-RANGER repositories. | Not modified. A local branch made there on 2026-10-26 was removed before any push; work moved to `%USERPROFILE%\Aether\aether-platform`. Owner's charter names `POWDER-RANGER/aether-platform` (D-009); it is not yet created. |
| C2 | Project instructions require Research Mode and Companion Mode. The reference code has `mode: deployment` or `development`. | Interfaces use the project names. The runtime mapping is an M1 implementation item in the active repository. |
| C3 | The seven `AETHER_*.md` files named in the initiation directive exist nowhere this session can reach. | Not recreated as seven files (D-007). |
| C4 | Owner statement (2026-10-25): no policy layer between parser and virtual device, for reaction time. Reference architecture routes all producers through the Governor's policy check. | Unchanged; the Governor's authority is fixed. Measure parser-to-pad latency in M1 before any proposal. |
| C5 | ChatGPT design brief asks for a restrained research-lab look and no excessive gradients or glow; owner direction of 2026-10-22 asks for the Metal Gear-style industrial look pushed further. | Both kept, by surface: identity assets stay industrial, application surfaces stay restrained (D-011). **[owner]** may override. |
| C6 | Reference branch `docs/aether-pr-rex-charter-architecture` is empty (same commit as `main`). | Noted only. |
| C7 | `%USERPROFILE%\Aether\powder-ranger` is a stale non-git copy of the package. | Noted only; do not develop there. |
| C8 | Reference light-mode `--ok` and `--warn` fail AA for small text. | Fixed in tokens (D-003). |
| C9 | Private repositories could not be listed: cloud GitHub token invalid, `gh` absent on the MSI. | Rerun discovery once authenticated. |
