# AACP: Æther Agent Accountability & Continuity Protocol

Version 0.2, **proposed**, 2026-10-26. Drafted by Claude (claude-opus-5-5). Not in force until reviewed by a second agent and accepted by the owner (§7, class C).

## 1. Purpose

Several AI agents work in this repository. Shared file access does not tell anyone who did what, why, what was checked, or what was accepted. AACP is the minimum set of rules and GitHub conventions that does. It is repository-native: it uses issues, branches, pull requests, reviews, commit trailers and Markdown files. It adds no database, service or tracker.

AACP governs engineering work only. It never runs in a play session and has no relationship to the Governor or PR-REX at runtime.

## 2. Objects and where they live

| Object | GitHub carrier | Identifier |
| --- | --- | --- |
| Task | Issue created from `.github/ISSUE_TEMPLATE/aacp-task.yml`, label `aacp:task` | `#<issue>` |
| Candidate (one implementation) | Branch `<platform>/<issue>-<slug>` and a PR that says `AACP-Task: #<issue>` | PR number |
| Evidence | The PR's Evidence section (§6), plus CI runs and linked logs | PR number + row |
| Review | A GitHub review or review comment by a different agent or the owner, starting `AACP-Review:` | Review URL |
| Decision | A row in `docs/decisions/DECISIONS.md` | `D-###` |
| Handoff | `protocols/aacp/session-receipts/<YYYY-MM-DD>-<issue-or-slug>.md`, linked from the PR | File path |

Nothing lives only in a chat. If it is not in one of these places, the next agent cannot see it.

## 3. Identity and provenance

Agent attribution is separate from Git author and from signing.

- **Git author** is whoever's credentials made the commit. It says nothing about which model wrote the change.
- **Signing** proves which key made the commit. It also says nothing about the model.
- **Agent attribution** is a commit trailer and a line in the PR body:

```text
AACP-Agent: claude/claude-opus-5-5          # <platform>/<model id as the platform reports it>
AACP-Task: #<issue>
```

An agent states the model identifier its platform gives it, not a marketing name it guesses. If the platform does not say, the agent writes `unknown`.

## 4. Task registration

Substantial work (more than a typo, a dependency bump or a one-line fix) starts from a task. The issue form records: objective; acceptance criteria (each one checkable); base commit; scope in and out; dependencies; agents assigned or invited; acceptance class (§7).

## 5. Competing candidates

Two or more agents may take the same task. Each opens its own branch and PR against the same base. The task issue lists the candidate PRs. Candidates are compared against the task's acceptance criteria, row by row, in a comparison comment on the issue. The losing PRs are closed, not deleted; their branches stay as record.

## 6. Evidence

Every PR body has an Evidence section, one row per claim:

| Capability | Status | Command or method | Result | Environment | Commit | Reported by |
| --- | --- | --- | --- | --- | --- | --- |

Status uses the six project classifications: VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, BLOCKED, NOT IMPLEMENTED. Every row also names who produced the evidence:

- **author**: the implementing agent ran it and pasted the command and output, or linked the CI run.
- **independent**: a different agent or the owner re-ran it on the stated commit.

An author row can reach at most PARTIALLY VERIFIED for acceptance purposes; VERIFIED for acceptance needs an independent row or CI. Nothing is reported as passing without the output or the CI link. "Should work" is UNVERIFIED.

## 7. Review and acceptance

An agent never accepts its own substantial work.

| Class | Covers | Acceptance needs |
| --- | --- | --- |
| A, routine | Docs, refactors, tests, tooling, visual changes within the design system | CI green and one independent review that reaches VERIFIED on the acceptance criteria |
| B, significant | Architecture, interfaces between processes, security-relevant code, anything in `powder_ranger/governor/` | Independent technical review by another agent, with the review naming what it re-ran; owner informed |
| C, owner | Mission, player authority, Governor authority, safety invariants, project scope, this protocol | The owner, in writing on the PR or issue |

Merging is acceptance. Only the owner merges class B and C. The owner may merge any class.

Claude and ChatGPT participate symmetrically: either may implement, review, challenge or verify; neither is the other's standing supervisor. Disagreement is written on the PR with evidence; the owner breaks ties.

## 8. Handoffs

When an agent stops before a task is accepted, it writes a handoff so another agent can continue without the conversation. Sections:

1. Task and acceptance criteria (link)
2. Baseline: branch, base commit, head commit
3. Done, with commits
4. Evidence so far (table from §6)
5. Not done
6. Known limits and open questions, including anything that needs the owner
7. Next concrete steps, in order
8. Environment notes: machines, paths, tools that did and did not work

## 9. Bootstrap

This protocol's own adoption is class C. Proposed steps (DESIGN-SYSTEM.md roadmap M3):

1. A second agent reviews this file and posts `AACP-Review:` on the PR.
2. The owner accepts, revises or rejects.
3. If accepted: add `aacp:task`, `aacp:candidate`, `aacp:owner` labels; add the Evidence section to `.github/pull_request_template.md`; run one real task end to end.

The issue form `.github/ISSUE_TEMPLATE/aacp-task.yml` is included as a draft so reviewers can see the shape.
