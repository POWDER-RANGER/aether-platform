# Reproducibility

CI uses Python 3.11 and 3.13 on Ubuntu and Windows. Install pinned packages with python -m pip install -r requirements-dev.lock, then python -m pip install -e . --no-deps. Run pytest, ruff check and ruff format --check.

RunIdentity records run ID, mode, environment, scenario, Git revision/dirty state, Python, OS, machine, backend names/version/weights hashes and settings SHA-256. Gaps include CPU/microcode, GPU/driver/runtime, controller, display geometry/refresh, model quantization/runtime/device, lock hash, locale/timezone, power/thermal profile, display scaling, ROI/reader hashes, random seeds and capture/recording rates. These must be measured, not inferred. Synthetic tests are not live capture evidence.
