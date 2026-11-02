# Contributing to aether-platform

## Setup

```
git clone https://github.com/POWDER-RANGER/aether-platform.git
cd aether-platform
python -m pip install -r requirements-dev.lock
python -m pip install -e . --no-deps --no-build-isolation
```

## Run tests

```
python scripts/docs/check_docs.py
python -m pytest -q
ruff check .
ruff format --check .
```

All checks must pass before a pull request is merged.

## Branch and pull request flow

1. Create a branch from `main`: `git switch -c <type>/<short-topic>` (`feat/`, `fix/`, `docs/`, `chore/`).
2. Keep changes focused; one concern per pull request.
3. Run the test command above and confirm it passes.
4. Open a pull request using the template. Describe what changed, how it was verified, and the status of any documentation claims.
5. Merge after CI is green.

## Documentation standards

Label claims by evidence level:

- **verified** - exercised by tests or inspected directly
- **documented** - described in the repository, not independently exercised
- **planned** - intended, not yet implemented

## Do not commit

API keys, tokens, credentials, machine-local paths, personal data, or runtime state. Use placeholders such as `<WORKSTATION_ROOT>` in path examples.

## AI assistance and credit

AI-assisted work is disclosed. Commits written with AI assistance carry a trailer:

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

Pull requests state AI involvement in the disclosure section of the template.

## Conduct and security

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately through the repository security advisory form, not public issues.