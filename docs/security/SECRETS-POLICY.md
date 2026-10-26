# Secrets and repository boundaries

Applies to every contributor and agent. Enforced by `.gitignore`, `tests/repo/test_repository_boundaries.py`, and GitHub secret scanning with push protection (enabled on this repository).

## Never committed

| Item | Why | Guard |
| --- | --- | --- |
| Model weights and checkpoints (`*.pt`, `*.safetensors`, `*.ckpt`, `*.onnx`, `*.gguf`, `weights/`) | Size, and third-party licenses (NitroGen weights are NVIDIA non-commercial research only) | `.gitignore`, test |
| Signing and sealing keys (`*.key`, `*.pem`), including the intent-log sealing key | A leaked key lets anyone forge or re-seal intent logs | `.gitignore`, test |
| STOP files | Machine-local control state | `.gitignore`, test |
| Tokens, passwords, `.env` files | Credentials | `.gitignore`, secret scanning, push protection |
| Workstation records (`ENVIRONMENT.md`) | Personal paths and machine details | `.gitignore`; kept outside the repository |
| Session logs, recordings | May contain player input and screen content; collected only under the project's data rules | `.gitignore` |

## Boundaries

- The retired reference repository `POWDER-RANGER/powder-ranger-bot` is read-only. Read it; never commit or push to it.
- Third-party code is used from its own installation, not copied in, unless `THIRD-PARTY.md` lists it with its license.
- Scratch scripts and render probes live outside the repository unless deliberately promoted through a reviewed pull request.
- The legacy virtual environment may be used as an interpreter; it is never modified for this repository's convenience.
- Public documents use `%USERPROFILE%` or relative paths, never a personal account path.

## If a secret is committed

1. Revoke or rotate it first; removing it from history does not un-leak it.
2. Remove it from the branch and record the incident in `docs/decisions/DECISIONS.md` without repeating the secret.
