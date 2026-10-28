# ÆTHER — Consolidated Audit, Artifact Inventory and Resource Plan

**Audit date:** 2026-10-28  
**Repository:** POWDER-RANGER/aether-platform  
**Mainline reference:** 5752dbc8391eb3f2b19f213f1fa37def42fce9f3  
**Primary workstation:** MSI Katana 15  
**Primary application:** PR-REX  
**Document status:** Consolidated working baseline; MSI filesystem inventory requires a fresh on-device enumeration.

## 1. Executive definition

ÆTHER is a local-first research, engineering and validation platform for gaming intelligence and accessibility. PR-REX is its principal intelligent gaming companion. The player remains the authority.

**Governing principle:** The player directs; the companion plays. The player can redirect, reclaim control or stop the system.

The central research question is how much reliable, transferable gameplay capability can be achieved through visual observation, learned behavior, structured reasoning and shared control, without requiring a hand-engineered agent for every game.

This document consolidates project purpose, audit scope, objectives, target architecture, implementation evidence, known artifacts, resource allocation and the next validation gates. It does not convert planned capabilities into implementation claims.

## 2. Audit scope

The audit covers:

1. **Platform architecture:** package boundaries, process lifecycle, configuration, events, dependencies and interfaces.
2. **Visual observation:** RGB capture, frame handling, OCR/HUD interpretation and world-state construction.
3. **Intelligence:** reflex backends, supervisory reasoning, planning, recovery and model replaceability.
4. **Control and safety:** Governor authority, signed intent, player override, delegation, focus checks, watchdog, STOP and neutral-on-fault behavior.
5. **Game integration:** versioned environment/game packs, test scenarios, controller adapters and game-state ground truth.
6. **Research evidence:** test results, hardware runs, synchronized recordings, logs, scorecards, reproducibility and limitations.
7. **Workstation resources:** MSI compute, memory, GPU/VRAM, storage, model assets, Python environments, dependencies, network and external services.
8. **Repository governance:** mainline status, legacy provenance, generated assets, secrets boundaries and documentation consistency.

### Out of scope

Unless the owner explicitly changes direction, the project does not include game-memory reading, DLL/code injection, anti-cheat circumvention, unrestricted autonomous authority over the player, commercial launch planning, public hosted consumer services, or modification of frozen historical prototypes.

A successful unit test, diagram, scaffold, mocked integration or single demonstration is not evidence of end-to-end gameplay capability.

## 3. Objectives and acceptance principles

- Establish an accurate, revision-specific repository and workstation baseline.
- Classify each capability as VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, BLOCKED or NOT IMPLEMENTED.
- Preserve the distinction between code existence, automated tests, hardware execution and real-game behavior.
- Keep the Governor as the only authority permitted to produce companion controller output.
- Ensure STOP, shutdown, watchdog and adapter faults lead to neutral output.
- Keep fast reflex execution independent of slower supervisory reasoning.
- Record intended, commanded, delivered and observed behavior as distinct evidence.
- Measure actual target-hardware latency, VRAM, RAM, CPU, disk and sustained operation before expanding model workloads.
- Keep research and companion modes on separate policies and scorecards.
- Require repeatable runs and evidence-backed diagnosis before marking reliability gates complete.

## 4. Target vision and architecture

The target runtime cycle is:

**Observe → Understand → Decide → Act → Verify → Learn**

| Layer | Intended responsibility |
|---|---|
| ÆTHER platform | Configuration, runtime, process management, observability, evidence, recording/replay and application shell |
| PR-REX perception | RGB frames, HUD/OCR readers, visual interpretation and structured world state |
| PR-REX supervisor | Subgoals, planning, recovery and high-level direction |
| Reflex backend | Fast learned or alternative gameplay action generation |
| Governor | Exclusive controller authority, intent validation, delegation, arbitration and safety |
| Motor model | Timing, smoothing, calibration and mode-specific output limits |
| Game Packs / environments | Versioned game-specific controls, objectives, readers and success detectors |
| Recorder and evaluator | Synchronized observations, inputs, outputs, replay and separate scorecards |
| AACP | Proposed external engineering accountability and continuity protocol; not part of the game runtime |

Research Mode and Companion Mode share infrastructure but must retain separate policies and evaluation. Player/game memory is deferred until after M3. NitroGen is a replaceable research candidate, not the definition of PR-REX.

## 5. Repository baseline and evidence boundary

The active repository is POWDER-RANGER/aether-platform; the legacy POWDER-RANGER/powder-ranger-bot repository is retired and reference-only. The legacy repository must not be modified.

The latest mainline merge identified for this audit is 5752dbc8391eb3f2b19f213f1fa37def42fce9f3 (28 October 2026). The owner reports that the subsequent consolidated mainline contains all intended PR merges, 260 local tests pass and all four GitHub CI jobs are green. The commit itself was fetched and confirms the PR #11 merge. The test count and complete CI state are owner-reported in the project conversation; this audit did not independently rerun them.

Earlier M1/M1.1 records document signed intent, Governor policy, hash-chained logs, virtual X360 output and keyboard/mouse output. Those records are historical evidence for their recorded runs, not a substitute for a fresh hardware retest. Current owner-side hardware-dependent gates remain open until the latest mainline is exercised on the MSI.

**Known status boundary:** NitroGen integration, capture under current mainline, physical controller passthrough, real-game input, model co-residency, supervisory vision, recording/replay and full PR-REX intelligence must not be described as verified without current evidence.

## 6. Artifact inventory

### 6.1 Repository artifacts

Repository root on the MSI, as recorded: C:\Users\ftrac\Aether\aether-platform\.

| Repository path | Purpose / artifact class |
|---|---|
| README.md | Project entry point and implementation status |
| SECURITY.md, THIRD-PARTY.md, LICENSE | Security, licensing and attribution |
| docs/vision/CHARTER.md, docs/vision/BRAND.md | Charter and identity |
| docs/architecture/ECOSYSTEM.md | ÆTHER / PR-REX / AACP responsibilities |
| docs/architecture/RESOURCE-INDEX.md | Repository and workstation resource references |
| docs/architecture/LEGACY-REFERENCE.md | Legacy inventory and migration map |
| docs/architecture/RUNTIME.md | Runtime slice architecture |
| docs/decisions/DECISIONS.md | Decision register |
| docs/STATUS.md | Living implementation status; older snapshot requires reconciliation |
| docs/verification/M1-CONTROL.md | M1 control verification record |
| docs/verification/M1.1-KEYBOARD-MOUSE.md | M1.1 keyboard/mouse verification record |
| docs/research/2026-10-28-inventory-and-evidence.md | Dated source-tree implementation inventory |
| docs/research/2026-10-28-external-source-notes.md | External research and source notes |
| docs/research/2026-10-28-driver-nitrogen-vlm-verification.md | Driver, NitroGen and VLM verification research |
| docs/research/OWNER-DECISIONS.md | Unresolved owner decisions |
| docs/workstation/SETUP.md | Windows workstation setup |
| docs/security/SECRETS-POLICY.md | Secret and local-artifact boundary |
| interfaces/shared/design/ | Design tokens, components, gallery and font assets |
| scripts/brand/build_tokens.py | Token generation tool |
| scripts/workstation/Test-Workstation.ps1 | Workstation verification script |
| tests/interfaces/, tests/repo/, tests/control/, tests/runtime/ | Automated tests |
| protocols/aacp/specification/AACP.md | AACP proposal |

This is a consolidated list of known paths from repository records, not a fresh exhaustive git ls-files manifest. The full tracked-file manifest must be generated from the audited mainline checkout.

### 6.2 Known MSI-local artifacts

Workstation root: C:\Users\ftrac\Aether\.

| Exact recorded location | Artifact / purpose | Inventory status |
|---|---|---|
| C:\Users\ftrac\Aether\aether-platform\ | Active repository checkout | Path recorded; current contents not locally enumerated in this audit |
| C:\Users\ftrac\Aether\powder-ranger-bot\ | Retired reference checkout; Python 3.11 environment used for earlier tests | Path recorded |
| C:\Users\ftrac\Aether\NitroGen\ | Upstream NitroGen checkout and separate environment | Path recorded |
| C:\Users\ftrac\Aether\weights\ng.pt | NitroGen model weights; earlier inventory recorded 1,974,723,762 bytes | Size is historical; current size/hash not rechecked |
| C:\Users\ftrac\Aether\wheels\ | Cached Python wheels | Path recorded; file list not rechecked |
| C:\Users\ftrac\Aether\ENVIRONMENT.md | Private workstation installation/environment record | Path recorded; contents intentionally not copied into public repository |
| C:\Users\ftrac\Aether\runs\m1.1\ | M1.1 test reports and run outputs | Path recorded; recursive manifest outstanding |
| C:\Users\ftrac\Aether\runs\m1.1\logs\kbmtest-*.jsonl | Keyboard/mouse intent and run logs | Pattern recorded; exact filenames and hashes outstanding |
| C:\Users\ftrac\Aether\checks\m1\ | M1 check artifacts | Path recorded; recursive manifest outstanding |
| C:\Users\ftrac\Aether\checks\design\ | Render probes, screenshots and one-off patch scripts | Path recorded; recursive manifest outstanding |
| C:\Users\ftrac\Aether\powder-ranger.zip | Older extracted package archive | Historical/stale snapshot |
| C:\Users\ftrac\Aether\*.ps1, *.log, *.done | Setup/test scripts, logs and completion markers | Pattern recorded; exact names outstanding |
| C:\Users\ftrac\.powder_ranger\log.key | Machine-local intent-log sealing key | Sensitive; do not copy to repository or inventory its contents |
| C:\Users\ftrac\.powder_ranger\ | STOP-file and runtime security state | Sensitive operational state; do not publish contents |

No generated-file inventory can honestly be called comprehensive until the MSI is scanned recursively and each file is classified as tracked source, generated documentation, build output, test report, log, screenshot, model/cache, secret or disposable scratch. No unverified local path is inferred here.

### 6.3 Required inventory record

For every file, record: absolute path, relative path (where applicable), size in bytes, last-write timestamp, SHA-256, file class, owning subsystem, tracked/ignored/untracked status, retention requirement and whether it is safe to publish. Never hash or disclose secret contents in a public report; record only their existence, path and access-control status in a private inventory.

## 7. Allocated resources

### Confirmed / recorded

| Resource | Allocation or state | Qualification |
|---|---|---|
| Primary workstation | MSI Katana 15 | Primary ÆTHER development/test machine |
| GPU | NVIDIA RTX 4060 Laptop GPU, 8 GB VRAM | Hardware model/capacity recorded; current load and free VRAM unknown |
| NitroGen weights | ng.pt, historically 1,974,723,762 bytes | Disk size record, not VRAM requirement |
| Python | Python 3.11.16 project environment recorded | Exact active interpreter for current mainline must be rechecked |
| Dependencies | Earlier environment recorded DXcam 0.3.0, NumPy 2.4.6, OpenCV 5.0.0.93, psutil 7.2.2, pyzmq 27.2.0 and vgamepad 0.1.0 | Historical version snapshot |
| Source control | Public GitHub repository and Actions CI | Four green jobs and 260 passing local tests are owner-reported for the current merged state |
| Local security state | Log-sealing key and STOP path under .powder_ranger | Must remain machine-local |
| Local model/dependency cache | NitroGen checkout, weights and cached wheels | Current occupancy not measured |

### Unknown / not yet measured

Exact CPU model and utilization, installed system RAM, current disk capacity/free space, per-directory storage use, GPU memory headroom, model cold/warm latency, sustained inference throughput, capture latency on current mainline, network throughput, power/thermal behavior, and cloud/API spend or quotas. Do not fabricate these values.

## 8. Resource projection map

The following is a planning map, not a claim that resources have been reserved or provisioned.

| Workload | Compute / memory pressure | Storage pressure | Gate before expansion |
|---|---|---|---|
| Governor and controller | Low-to-moderate CPU; strict timing and fault isolation | Small logs | Re-run control and STOP tests on current mainline |
| Runtime and event processing | CPU and memory proportional to event volume | Append-only evidence growth | Measure event throughput, retention and disk quota |
| Screen capture | GPU/display and memory bandwidth; frame buffers | High if raw frames retained | Measure capture timing, selected-display behavior and bounded buffering |
| Reflex inference | GPU VRAM and inference latency | Model weights/cache | Verify NitroGen loopback-only service, model hash, peak VRAM and sustained timing |
| Supervisory VLM/OCR | Potentially high VRAM and latency | Model/cache and prompt/frame artifacts | Benchmark alone and concurrently with reflex; no model selection by model-card claims alone |
| Recording/replay | CPU, RAM and disk write throughput | Potentially dominant storage consumer | Define cadence, compression, quota, retention and export policy |
| Evaluation | CPU for analysis; repeat-run overhead | Reports, logs, frame samples and metadata | Freeze score definitions and preserve provenance |
| Command Center | Modest local runtime/UI overhead | Small static/build assets | Read-only first; only after runtime data contracts are stable |

### Recommended resource accounting

Before any additional large model or recording feature is added, collect a baseline with the game idle, game running, reflex only, supervisor only, and reflex plus supervisor. Capture total/free system RAM, total/free GPU memory, per-process GPU use, CPU utilization, disk free space, model load time, warm median/p95 inference latency, frame-capture latency and temperature/power where available.

Set explicit caps for model cache, recordings, event logs and scratch space. Keep raw recordings opt-in and quota-bound. Keep model weights and secrets outside Git. Remote compute remains optional and requires measured benefit over local execution.

## 9. Next actions, in order

1. On the MSI, verify the checked-out repository path, branch and HEAD; reconcile it with mainline 5752dbc and subsequent merges if any.
2. Generate exhaustive git ls-files and recursive filesystem manifests for the repository and the ÆTHER working root. Include ignored/untracked files, but redact secrets.
3. Hash and classify generated outputs; identify duplicate, stale and orphaned artifacts without deleting anything.
4. Record CPU, RAM, GPU, VRAM, disk and network baselines.
5. Re-run current-mainline automated tests and the four CI jobs; preserve exact commands, commit SHA and outputs.
6. Re-run Governor, STOP, virtual controller and keyboard/mouse checks under an owner-approved hardware session.
7. Verify NitroGen binds only to loopback, verify key permissions and test clean shutdown.
8. Measure capture and reflex behavior on the current MSI environment.
9. Only then benchmark a supervisory model concurrently with the reflex backend.
10. Implement synchronized recording, scorecards and a read-only Command Center after their evidence/data contracts are stable.

## 10. Authority and change control

The project charter and owner decisions govern scope. The Governor remains the only controller-output authority. The legacy repository remains read-only. Model weights, signing keys, STOP files, environment records, recordings containing private information and machine-specific secrets must not enter the public repository.

This document is a consolidated audit baseline. Its MSI inventory and resource measurements remain provisional until the direct workstation scan and current-mainline verification are attached as evidence.
