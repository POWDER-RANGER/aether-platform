# Security policy

## Reporting a vulnerability

Report security issues privately to the repository owner. Do not open a public issue that includes exploit details or secret material.

## Repository boundaries

The following are never committed (enforced by `.gitignore`, `tests/repo/test_repository_boundaries.py`, and GitHub secret scanning with push protection):

- Model weights and checkpoints
- Signing keys and certificates
- `.env` files and tokens
- Workstation records (`ENVIRONMENT.md`)
- Session logs and recordings

See `docs/security/SECRETS-POLICY.md` for the full policy.

## If a secret is committed

1. Rotate or revoke the credential first.
2. Remove it from the branch.
3. Record the incident in `docs/decisions/DECISIONS.md` without repeating the secret value.
