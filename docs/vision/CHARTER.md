# Æther: project charter

Version 1.0-draft, 2026-10-26. Source: the owner's charter "Æther — Unified Intelligence & Companion Platform", refined against the Æther Project instructions and the verified state of the reference codebase. Refinements are listed in §10. Repository: `POWDER-RANGER/aether-platform` (proposed; not yet created).

## 1. Purpose

Build a unified, local-first intelligence and companion platform for gaming-intelligence research, accessibility, and accountable AI-assisted engineering.

> The player is the legend. PR-REX is the body double.
> The player directs; the companion plays. The player remains the authority.

## 2. Three responsibilities

| | Role | Owns | Never |
| --- | --- | --- | --- |
| **Æther** | Platform | Configuration, logging, recording and replay, runtime process management, model-backend interfaces, experiment and evidence management, the application interface | Issues controller output except through the Governor |
| **PR-REX** | Principal application | Perception, world state, planning, reflex execution, recovery, player interaction, accessibility assistance, evaluation | Replaces the player; bypasses the Governor |
| **AACP** | Protocol | Agent and session provenance, task records, evidence, independent review, acceptance, handoffs | Runs at runtime; depends on or is depended on by PR-REX |

## 3. The Governor

The Governor is the exclusive authority for companion-controlled controller output. No component writes to a controller except through it. It enforces player override, emergency stop and halt latch, freshness and sequence checks, replay protection, delegation permissions, confidence and focus gates, output limits, the watchdog, neutral output on stop or fault, and an auditable intent log. These are safety invariants owned by the owner.

## 4. Operating modes

Two configurations, never evaluated as one:

- **Research Mode**: controlled experiments. Controller output is enabled per experiment, always through the Governor, with experimental motor behavior allowed. Every safety invariant in §3 applies.
- **Companion Mode**: player-directed assistance with human-like motor limits and the delegation the player grants: goal-level direction, per-control sharing, propose-and-confirm, interruptible autonomy, or whole-controller delegation. The player sets how control returns.

Research results never stand in for Companion results, or the reverse.

## 5. Architectural rules

| Rule | Consequence |
| --- | --- |
| One platform, bounded systems | No duplicate infrastructure |
| Local-first | Local models, processing and storage; cloud only where it measurably helps |
| Human authority | Player override and stop take precedence over everything |
| Explicit permissions | Every agent capability has a defined boundary |
| Evidence before claims | Status uses VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, BLOCKED, NOT IMPLEMENTED; no simulated data shown as real |
| Separate scorecards | Intelligence and accessibility are evaluated separately |
| Reproducible experiments | Configuration, model, inputs and results are recorded and versioned |
| Fast path stays fast | Supervisory reasoning never blocks the reflex path or the Governor tick |
| Protocol-based collaboration | AACP governs substantial engineering work once accepted |
| Minimal dependencies | No services, frameworks or costs without a stated need |
| Reuse verified work | Port what the reference codebase has verified; do not rebuild it |
| Expand after verification | A capability grows only after the previous one is evidenced |
| Neutral identifiers | ENV-xx, SCN-xx, DG-xx in core docs and interfaces |

## 6. Repository layout (target)

```text
aether-platform/
├── docs/            vision/ architecture/ doctrine/ decisions/ roadmaps/ terminology/
├── platform/        core/ configuration/ observability/ recording/ backends/
├── applications/    pr-rex/ (perception/ intelligence/ planning/ interaction/ input/ governor/ motor/ accessibility/ evaluation/)
├── protocols/       aacp/ (specification/ schemas/ session-receipts/ review/ examples/)
├── research/        intelligence/ accessibility/ experiments/
├── interfaces/      shared/design/ web/ desktop/
├── integrations/    models/ hardware/ controllers/
├── configuration/   environments/ (ENV-xx profiles) scenarios/ (SCN-xx, DG-xx)
├── tests/           platform/ pr-rex/ aacp/ interfaces/ integration/ system/
├── scripts/
└── history/         provenance of migrated material; never rewritten
```

A directory is created when its first real file arrives, not before. Orchestration, a capability registry, an event bus and agent lifecycle management are added when a second consumer needs them.

## 7. Reference repository

`POWDER-RANGER/powder-ranger-bot` is retired and read-only. It is the foundational reference for the owner's original objectives and for code that has already run. Migration follows `docs/architecture/LEGACY-REFERENCE.md`: inventory every branch (not only `main`), classify each item as verified, built-but-unverified, prototype or abandoned, port verified items with their tests, and record provenance in `history/`.

## 8. First milestone (M1, engineering foundation)

In order. Each step ends with recorded evidence.

1. **Repository and doctrine.** This charter, the doctrine (authority, safety invariants, evidence rules), contribution rules, AACP proposal.
2. **Contracts.** Interfaces between capture, PR-REX backends, the Governor, the controller adapters and recording; permission boundaries.
3. **Port the verified control foundation** from the reference: intent packets and signing, Governor and policy, kill switch, hash-chained log, motor model, controller adapters, with their tests. Re-run the tests and the virtual-pad check on the MSI.
4. **Platform core.** Configuration (Research and Companion profiles), logging, synchronized recording, runtime process start and stop, replaceable backend interface.
5. **Close M1 verification gaps.** Physical controller passthrough, live player override, axis direction, stop triggers and hardware protection; diagnose the stalls and unexpected exits seen in ENV-01.
6. **Engineering scorecard E-01 to E-10** and the Command Center surface that shows it, built on the design system.

Expansion into perception, world state and intelligence (M2) begins only after M1 evidence.

## 9. Explicitly avoided

Rebuilding the reference bot before inventory; heavyweight infrastructure; mandatory cloud services; dashboards before the services behind them work; merging Research and Companion behavior; agent authority over controller output outside the Governor; treating unit tests as proof of system behavior; multiple repositories for components that evolve together; committing model weights.

## 10. Refinements to the owner's draft

| # | Draft | Refined | Reason |
| --- | --- | --- | --- |
| R1 | Research Mode: no autonomous controller output by default | Output enabled per experiment, through the Governor | Project instructions: experimental motor behavior in Research Mode; M3 evaluates both modes |
| R2 | PR-REX proof of operation initially without controller output | Port and re-verify the existing control foundation first | Governor, adapters and motor model already have 132 passing tests and ran live on the MSI |
| R3 | Core = capability registry, events, agent lifecycle | Core = configuration, logging, recording, process management, backend interface | Project §13: no abstraction without a concrete need |
| R4 | Full directory tree at the start | Directories created on first real file | Smallest credible foundation |
| R5 | Governor not named | §3 | Fixed invariant |
| R6 | Evidence terms unspecified | Six project classifications | Project §10 |
| R7 | Legacy inventory scope unspecified | Every branch, including open PRs #10 and #11 | Latest verified work exists only there |

## 11. Open decisions (owner)

| Decision | Recommendation |
| --- | --- |
| Visibility | Owner's call |
| License | Reference is MIT; NitroGen weights are research-only and stay out of the repository under any license |
| Language | Python 3.11+: the reference runtime and NitroGen are Python |
| Interface priority | Local web UI served by the runtime process, read-only first; one codebase covers desktop, tablet and Fold 6 |
| Execution environment | Local-first on the MSI; remote only with a measured advantage |
| Repository creation | Owner creates `POWDER-RANGER/aether-platform` or authorizes `gh` on the MSI |
