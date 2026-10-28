# M3 formal scenario gate packet — owner template

Complete and freeze this packet before formal SCN testing. Thresholds are intentionally absent here; do not infer or invent pass criteria.

## Scenario register

| Scenario ID | Definition path + SHA-256 | Environment | Mode (research/companion) | Owner approval | Notes |
|---|---|---|---|---|---|
| SCN-__ | | | | | |

## Required sample sizes

- Screening: **3 runs** per scenario for setup/debug only; screening is not a claim.
- Claims: **10+ runs** per scenario/mode, with raw samples and failures preserved.
- Any higher sample size must be written and frozen by the owner before execution.

## Frozen-file checklist

- [ ] Scenario definitions and referenced configuration files hashed and frozen.
- [ ] Reader ROIs and reader specifications hashed.
- [ ] Planner / policy configuration and software commit recorded.
- [ ] Threshold lock created by owner; no threshold is inferred from this template.
- [ ] Git working tree state recorded; no unreviewed changes.

## Hardware checklist

- [ ] MSI model, OS build, CPU, GPU, driver and available VRAM recorded.
- [ ] Controller, connection, passthrough and virtual-driver versions recorded.
- [ ] Capture backend, target display/window and resolution recorded.
- [ ] Model name, revision, weights hash, runtime and quantization recorded.
- [ ] Power, thermal, network and background-load conditions recorded.

## Failed-run definition

Owner must define scenario-specific failure criteria before the first formal run. At minimum, preserve and classify crash, hang/stall, capture loss, reader misread, planner timeout, Governor rejection, player override, E-stop, recording gap, and incomplete recording. Do not discard a run because it failed or produced inconvenient data. A player override or E-stop is recorded distinctly and is not automatically evidence of system failure; scenario-specific interpretation must be frozen in advance.

## Preservation checklist

- [ ] Preserve every run, including failed, interrupted, partial and screening runs.
- [ ] Preserve original frames and streams in a private local evidence store.
- [ ] Preserve manifest, exact configuration, commit, logs, environment and raw measurements.
- [ ] Preserve verifier output, hashes, timestamps and any redacted sharing copy separately.
- [ ] Never overwrite a failed run; reruns receive new run IDs.
