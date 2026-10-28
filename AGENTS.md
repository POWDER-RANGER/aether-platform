# Agent instructions — Æther / PR-REX

## Build, test and lint
- Python >=3.11. Install: `python -m pip install -e ".[dev]"`.
- Tests: `python -m pytest -q`.
- Lint: `ruff check .`; format check: `ruff format --check .`.
- CI matrix: Ubuntu and Windows, Python 3.11 and 3.13. Do not alter the matrix without owner approval.

## Module map
- `src/aether/control/`: Governor, intent validation, safety and controller output. Protected boundary.
- `src/aether/capture/`: screen and frame sources.
- `src/aether/perception/`: frame buffer, ROI readers and world state.
- `src/prrex/`: reflex backends, supervisor and planner.
- `src/aether/recording/`: run manifests, frames, streams and replay.
- `src/aether/server/`: local read-only Command Center.
- `src/aether/sim/`: deterministic synthetic-only fixtures.
- `tests/`: CI tests; synthetic fixtures must say SYNTHETIC.
- `docs/protocols/`, `docs/gates/`, `docs/security/`: protocols, gates and reviews.
- `evidence/`: immutable run evidence; failed runs are preserved.

## Non-negotiable Governor rule
Governor is the sole controller-output authority. No backend, planner, observer, capture source or UI may write controller output directly. Preserve player override and E-stop precedence, neutral output on stop/fault, rejection of stale/invalid/replayed intents, and the distinction between intended, commanded, delivered and observed values. Slow supervisory work must not block the reflex path.

## Evidence labels
Use only: VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, BLOCKED, NOT IMPLEMENTED. Synthetic CI evidence is not hardware or gameplay evidence. Do not call a defect RESOLVED without reproduction, evidence-backed diagnosis, fix, and ten clean runs. Keep proposed thresholds marked NOT FROZEN until owner approval.

## Where evidence goes
Write immutable run records under `evidence/<criterion-or-scenario>/<run_id>/`; retain raw frames, streams, manifests, logs, verifier output and failures. Redacted exports are separate copies and never replace originals. Include run ID, UTC date, criterion/scenario, commit and evidence label.

## Do not
- Never edit `src/aether/control/` or the reference repository `POWDER-RANGER/powder-ranger-bot` without explicit owner authorization.
- Never merge, close, or mark a draft PR ready unless explicitly instructed.
- Never change `docs/STATUS.md` capability labels or M1–M6 order without owner approval.
- Never invent CI, database, production, hardware, gameplay or benchmark results.
- Never commit model weights, secrets, intent keys, personal captures or unredacted private evidence.
- Never use commercial game titles in fixtures or docs.
- Never add unapproved dependencies or change CI matrix/thresholds.
- Never treat synthetic frames, replay, or a mock backend as live capture or delivered controller output.
- Never add a controller output path outside Governor.
- Never overwrite failed runs or silently drop evidence.
- NitroGen is non-commercial research only; do not redistribute weights/code or imply commercial permission.
