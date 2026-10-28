# Measurement commands

These commands write measured output to `evidence/<criterion-or-tool>/<run_id>.json`. Raw samples are retained; no sample values are fabricated.

- `python -m aether.cli_ext bench tick --seconds 600` — in-process Governor tick intervals through its public `tick()` API and DryRunAdapter.
- `python -m aether.cli_ext bench capture --process <exact-process-name> --backend dxgi --seconds 60` — optional DXcam capture on the named process window. Hardware path is UNVERIFIED until run on the MSI.
- `python -m aether.cli_ext bench nonblocking --seconds 10 --supervisor-sleep 1.0` — synthetic frame source, NullReflex and fake Governor client; compares reflex cadence with a delayed supervisor. Synthetic-only, not gameplay evidence.
- `python -m aether.cli_ext bench inference --backend ollama --calls 5` — synthetic 256×256 RGB image, cold first call and warm latency samples.
- `python -m aether.cli_ext bench inference --backend ollama --calls 5 --concurrent` — starts Ollama and NitroGen inference calls concurrently; NitroGen requires a separately running upstream server. VRAM polling is skipped if `nvidia-smi` is absent.
- `python -m aether.cli_ext verify-run <run_dir>` — checks manifest, monotonic stream/frame timestamps, frame index versus JPEG files, and JSONL event parsing; writes an E-10 verdict and exits 1 on failure.

Hardware-dependent capture, model inference, GPU residency and Governor timing remain UNVERIFIED until the owner runs them on the target workstation. Never interpret synthetic nonblocking input as captured gameplay.
