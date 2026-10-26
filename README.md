# Æther platform

Local repository for `POWDER-RANGER/aether-platform` (not yet created on GitHub; `docs/decisions/DECISIONS.md` D-009).

> The player is the legend. PR-REX is the body double.

Æther is the platform. PR-REX is its principal application. AACP governs how agents build both. Start with `docs/vision/CHARTER.md`.

## Status

| Part | Status |
| --- | --- |
| Charter, ecosystem map, decision register, reference inventory | Draft for owner review |
| Design system (tokens, components, gallery, tests) | VERIFIED: tests pass, rendering checked |
| AACP | Proposed specification |
| Platform core, PR-REX runtime, Governor | NOT IMPLEMENTED here; verified reference code to be ported (D-014) |

## Layout (directories appear when their first file does)

| Path | Contents |
| --- | --- |
| `docs/vision/` | `CHARTER.md`, `BRAND.md` |
| `docs/architecture/` | `ECOSYSTEM.md`, `RESOURCE-INDEX.md`, `LEGACY-REFERENCE.md` |
| `docs/decisions/` | `DECISIONS.md` |
| `docs/security/` | `SECRETS-POLICY.md`: what is never committed, and how that is enforced |
| `docs/workstation/` | `SETUP.md`: reproducible workstation setup and the `ENVIRONMENT.md` template |
| `scripts/workstation/` | `Test-Workstation.ps1`: workstation verification |
| `protocols/aacp/specification/` | `AACP.md` |
| `interfaces/shared/design/` | Design system: `DESIGN-SYSTEM.md`, tokens, components, gallery, fonts |
| `scripts/brand/` | `build_tokens.py` |
| `tests/interfaces/` | Design-token tests |
| `tests/repo/` | Repository-boundary tests |

## Design system in one minute

Link `interfaces/shared/design/tokens.css`, then `components.css`; put `class="ae"` on `<body>`; set `data-product` to `aether`, `prrex` or `aacp`. Every capability shows an evidence status, every running part an operational state; mock data only inside `.demo-frame`. Change a value in `tokens.json`, run `python scripts/brand/build_tokens.py`, then `pytest`.

## License

MIT for Æther's own code (`LICENSE`). Third-party components keep their own licenses; see `THIRD-PARTY.md`. NitroGen, the current reflex backend, is licensed for non-commercial research only and is not included here.
