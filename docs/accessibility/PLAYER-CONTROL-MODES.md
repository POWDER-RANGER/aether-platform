# Player control delegation modes

Design notes only; no mode or input method is implemented. Governor remains sole controller-output authority. UI and interruption details are design assumptions unless sourced below.

## Goal-level delegation
Player sees goal, scope, expiry and phase; interrupts by revoking delegation or E-stop. Governor enforces scope, expiry, player override and neutral output on E-stop. Shared autonomy background: https://arxiv.org/abs/2501.08389 (retrieved 2026-10-28); Æther UX is an assumption.

## Per-control sharing
Player sees ownership per control and conflicts; interrupts by reclaiming controls or E-stop. Governor prevents delegated writes to player-owned controls. Accessibility/shared-control background: https://arxiv.org/abs/2509.02132 (retrieved 2026-10-28); exact UX is an assumption.

## Propose-and-confirm
Player sees proposed action, confidence, rationale, affected controls and duration; interrupts by rejecting/expiry or E-stop. Governor requires explicit authorization before output. Confirmation flow is a design assumption; background https://doi.org/10.1145/3772318.3791080 (retrieved 2026-10-28).

## Interruptible autonomy
Player sees active goal and action chunk; interrupts through player input or E-stop. Governor preserves player precedence, TTL, stale/replay rejection and neutral output on stop/fault. Fast/slow architecture background: https://arxiv.org/abs/2512.20188 (retrieved 2026-10-28); guarantees are project requirements.

## Whole-controller delegation
Player sees full scope, active state, expiry and stop affordance; interrupts through player override or E-stop. Governor enforces revocation, override precedence, neutral E-stop output and audit. This mode is a design assumption; background https://arxiv.org/abs/2501.08389 (retrieved 2026-10-28).
