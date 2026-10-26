# Reference repository: inventory and migration map

Source: `POWDER-RANGER/powder-ranger-bot`, retired and read-only. Read 2026-10-26 from branch `claude/main-designations` (`ad15296`), which contains everything on `main` (`4c6963d`) plus open PRs #10 and #11. Nothing here modifies that repository.

Its GitHub description ("YOLOv8 … Behavior Tree/GOAP … Ollama … DirectInput") describes the first prototype only. The current code is the Governor-based design.

## 1. Original objectives (first prototype, `history/`)

What the owner set out to build, and what the current design kept or dropped. Source: `history/README.md`.

| Kept | Dropped, and why |
| --- | --- |
| Assistance levels | Memory reading: the companion perceives the screen only |
| Input methods: eye, voice, blink, switch, BCI, hybrid | Placeholders that printed success without doing the work |
| Accessibility profile; voice command vocabulary; spoken status and alerts | Accessibility mode that never started the main loop |
| Human timing variation and rate limits | Two input paths able to drive the controller at once (now: Governor only) |
| Scancode input with no DLL injection | Unreliable blink, gaze and enemy detection methods |
| Local-only processing | Substring command matching; an LLM consulted every frame |
| Testing with disabled players | A roadmap marking unbuilt phases as complete |

The prototype's architecture text pairs an LLM for strategy, a learned policy for tactics and a rule engine for safety. That fast/slow split survives in the current project instructions as reflex path plus supervisor; the rule engine became the Governor.

## 2. Current reference code

| Area | Files | Status (reference record) | Migration |
| --- | --- | --- | --- |
| Intent packets, HMAC-SHA256 signing | `powder_ranger/intent.py` | VERIFIED (tests; live session) | Port to `applications/pr-rex/governor/` with tests |
| Governor, policy, safety (kill switch, focus) | `governor/governor.py`, `policy.py`, `safety.py`, `client.py` | VERIFIED: STOP file and Pause hotkey tripped the halt on the MSI; review fixes F1–F3, F5–F7 regression-tested | Port with tests; first M1 code |
| Hash-chained, sealed intent log | `governor/intent_log.py` | VERIFIED (chain OK, 170 records); seal not written when force-closed | Port; fix seal-on-forced-exit in M1 |
| Motor model, One Euro filter, calibration | `motor/` | Tests pass; calibration not run on hardware (UNVERIFIED live) | Port to `applications/pr-rex/motor/` |
| Virtual pad adapters (X360, DS4, dry run) | `output/adapters.py` | X360 VERIFIED by XInput read-back; DS4 axis direction UNVERIFIED | Port to `integrations/controllers/` |
| Window capture (dxcam) | `capture/screen.py` | VERIFIED: median 3.3 ms | Port to `platform/` capture; add full-frame retention and 256×256 reflex view |
| NitroGen reflex runner | `runners/nitrogen.py` | Round trip VERIFIED (225 ms synthetic, 450 ms live per 16-action chunk); play quality FAILED in ENV-01 | Port behind the backend interface as one replaceable backend |
| Player input, voice, gaze | `inputs/` | Keyboard ran live; physical pad, voice, gaze UNVERIFIED on hardware | Port; verify in M1 (pad) and later (voice, gaze after M3 per project scope) |
| Game Packs | `packs.py`, `packs/` | Tests pass | Port; rename pack content to ENV-xx profiles |
| Session report | `report.py` | Tests pass | Port into `platform/observability/` |
| CLI | `cli.py` | Working | Replace progressively with the platform runtime; keep commands that tests rely on |
| Config and profiles | `config/` | Working; modes are `deployment` / `development` | Map to Companion / Research profiles (D-010) |
| Setup and run scripts | `scripts/*.ps1` | Ran on the MSI | Port as needed |
| Site, brand, fonts, diagrams | `index.html`, `assets/`, `docs/BRAND.md` | Published (Pages) | Brand and fonts carried into `docs/vision/` and `interfaces/shared/design/` |
| Docs | `ARCHITECTURE.md`, `SECURITY.md`, `docs/FIELD-MANUAL.md`, `docs/VERIFICATION.md`, `docs/REVIEW-2026-10.md` | Current to 2026-10-25 | Source for doctrine, contracts and the M1 verification baseline |
| Tests and CI | `tests/` (132), `.github/workflows/ci.yml` | 132 passed on the MSI 2026-10-24 | Port with each module |

## 3. Known open findings to carry forward

From `docs/REVIEW-2026-10.md`: F4 NitroGen server binds all interfaces and unpickles requests (mitigated by a firewall rule, now optional in development); F8 spoken grants have no confirmation; F9 capture region fixed at start; F10 downscale method differs from NitroGen's client; F11 grant and resume messages replayable within a session; F13 ViGEmBus retired upstream. Also: no launcher heartbeat to the Governor; no per-control claims for the physical pad.

## 4. M1 verification gaps inherited

Player override during live play; physical pad passthrough; DS4 axis direction; staying in a race in ENV-01 (session left the race for the main menu: an "unexpected exit" to diagnose); the optional firewall lockdown.
