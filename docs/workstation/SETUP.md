# Workstation setup

How to set up a Windows workstation for Æther with every tool in a recorded, non-default location. The machine's own record (`ENVIRONMENT.md`) stays outside the repository; the template at the end of this file is its shape.

## Rules

1. Install tools under one root you choose, e.g. `%USERPROFILE%\Aether\tools\<tool>\<version>\`. Never rely on an installer's default path.
2. Prefer official release archives with published checksums over installers. Verify the checksum before extracting.
3. Every change to `PATH`, environment variables or global git config is written to `ENVIRONMENT.md` with the command to undo it.
4. Use the GitHub noreply address for commits (`<id>+<login>@users.noreply.github.com`); GitHub rejects pushes that expose a private address.

## Steps

| # | Step | Command (PowerShell) |
| --- | --- | --- |
| 1 | Download GitHub CLI release zip and checksums into `<root>\gh\downloads\` | `Invoke-WebRequest <release-url> -OutFile <file>` |
| 2 | Verify SHA-256 against `gh_<ver>_checksums.txt` | `(Get-FileHash <zip> -Algorithm SHA256).Hash` |
| 3 | Extract to `<root>\gh\<ver>\` | `Expand-Archive <zip> -DestinationPath <root>\gh\<ver>` |
| 4 | Add `<root>\gh\<ver>\bin` to the user `Path`; set user `GH_CONFIG_DIR` to `<root>\gh\config` | `[Environment]::SetEnvironmentVariable(...,'User')` |
| 5 | Sign in (device flow; token goes to Windows Credential Manager) | `gh auth login --hostname github.com --git-protocol https --web --scopes workflow` |
| 6 | Let git use gh for github.com | `gh auth setup-git --hostname github.com` |
| 7 | Clone and set the repo-local identity | `git config user.name "<name>"`; `git config user.email <noreply>` |
| 8 | Workstation verification | `scripts\workstation\Test-Workstation.ps1 -GhExe <path> -Python <path>` |
| 9 | Repository verification | `python -m pytest`, `ruff check .`, then CI on the pushed commit |

Steps 8 and 9 are different claims. Step 8 passing means the machine is ready; it says nothing about the code. Only step 9 and CI say the code works.

## ENVIRONMENT.md template

```markdown
# Æther workstation record (<machine>)

## Installed tools
| Tool | Version | Path | How installed (source, checksum) | Date |

## Environment changes (user scope)
| Variable | Change | Undo |

## Git configuration changes
| Scope | Setting | Value | Undo |

## Folders
| Path | Purpose |
```
