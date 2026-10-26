# Decision register

Status: **accepted** (in force), **proposed** (awaiting independent review or owner), **owner** (owner-only, open), **superseded**.

| ID | Date | Decision | Status | By | Notes |
| --- | --- | --- | --- | --- | --- |
| D-000 | 2026-10-22 / 25 | Platform Æther (ligature in display text); companion PR-REX; "Powder Ranger" retired as a product name | accepted | Owner | BRAND.md §1 |
| D-001 | standing | Governor is the exclusive authority for companion-controlled controller output; the player is the final authority | accepted | Owner | Project instructions §4–5 |
| D-002 | 2026-10-26 | One UI base `#150809`; `#0c0405` kept as `--ink` (shadows, log wells, artwork) | proposed | Claude | Resolves BRAND.md §10.1 |
| D-003 | 2026-10-26 | Light `--ok` `#2c7442`→`#24663a`, `--warn` `#8a5a00`→`#7d5200` | proposed | Claude | Old values 4.21 and 4.38:1 on `--bg` |
| D-004 | 2026-10-26 | Accents: Æther `#f2c230`, PR-REX `#d9a9ad`, AACP `#8fb3c9` (light `#8a1c26`, `#8a3a44`, `#2f5a73`) | proposed | Claude | Owner may veto |
| D-005 | 2026-10-26 | Evidence status = the six project classifications; plus 8 operational states and 4 control states as closed sets | accepted | Project instructions §10; brief §10 | Enforced by `tests/interfaces/test_design_tokens.py` |
| D-006 | — | Application shell technology | owner | — | Not needed before DS-1. Recommendation: local web UI served by the runtime process, read-only first |
| D-007 | 2026-10-26 | Do not create seven `AETHER_*.md` files; keep one register per concern | proposed | Claude | |
| D-008 | 2026-10-26 | AACP lives in the active Æther repository under `protocols/aacp/` until used on one real task | proposed | Claude | |
| D-009 | 2026-10-26 | Active repository `POWDER-RANGER/aether-platform` (public, created 2026-10-26); `powder-ranger-bot` remains the read-only foundational reference | accepted | Owner; repo created | Supersedes earlier local-only note |
| D-010 | 2026-10-26 | Interfaces use Research Mode / Companion Mode; runtime mapping from reference `development` / `deployment` is an M1 item | accepted | Project instructions §5 | |
| D-011 | 2026-10-26 | Identity assets (wordmark, banners, site hero) keep the industrial steel-and-maroon treatment; application surfaces are flat and restrained | proposed | Claude | Reconciles owner direction 2026-10-22 with the design brief |
| D-012 | 2026-10-26 | Core docs and interfaces use ENV-xx, SCN-xx, DG-xx identifiers | accepted | Project instructions §8 | |
| D-013 | 2026-10-26 | Charter 1.0-draft with refinements R1–R7 (`docs/vision/CHARTER.md`) | proposed | Owner draft, refined by Claude | Owner to accept or amend |
| D-014 | 2026-10-26 | First M1 code is a port of the reference's verified control foundation (intent, Governor, log, motor, adapters) with its tests | proposed | Claude | Charter R2; `docs/architecture/LEGACY-REFERENCE.md` |
| D-015 | 2026-10-26 | Repository public; Æther's own code under MIT; third-party components keep their licenses (`THIRD-PARTY.md`); NitroGen code and weights never committed | accepted | Owner (license, visibility); Claude (third-party handling) | NitroGen's NVIDIA license is non-commercial research only and binds any setup that runs it |
| D-016 | 2026-10-26 | Repository boundaries enforced in code: `.gitignore` covers weights, keys, STOP files, `.env`, workstation records, logs and recordings; `tests/repo/` fails if any is tracked or not ignored, or if a personal Windows path appears in tracked files | accepted | Claude | `docs/security/SECRETS-POLICY.md` |
| D-017 | 2026-10-26 | `main` protected: changes arrive by pull request with the `test` CI checks passing; admins (owner) are not blocked | proposed | Claude; owner to apply or decline | Owner can relax it in repository settings |
| D-018 | 2026-10-26 | Python code lives under `src/`: `aether` (platform) and `prrex` (application). Controller authority (intent, Governor, log, motor, adapters) is platform-owned in `aether.control`; PR-REX backends live in `prrex.backends` | accepted | Claude | A top-level `platform/` package would shadow the standard library `platform` module |
| D-019 | 2026-10-26 | STOP file and log-sealing key stay at `~/.powder_ranger/` | accepted | Claude | Continuity with the reference runtime and existing logs; revisit when the runtime gets its own state directory |
