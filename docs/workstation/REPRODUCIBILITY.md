# Reproducibility

CI uses Python 3.11 and 3.13 on Ubuntu and Windows. Install the pinned packages with python -m pip install -r requirements-dev.lock, then install the project without resolving or downloading a second build environment: python -m pip install -e . --no-deps --no-build-isolation. Run python -m pytest -q, ruff check ., and ruff format --check ..

The requirements-dev.lock pins setuptools (the PEP 517 build backend), runtime dependencies and the test/lint tools installed by CI. Optional Windows/hardware extras are deliberately excluded because CI does not install them. Keep this lock synchronized with the CI install commands and pyproject.toml direct requirements.

RunIdentity records run ID, mode, environment, scenario, Git revision/dirty state, Python, OS, machine, backend names/version/weights hashes and settings SHA-256. Reproducibility gaps include CPU/microcode, GPU/driver/runtime, controller, display geometry/refresh, model quantization/runtime/device, lock hash, locale/timezone, power/thermal profile, display scaling, ROI/reader hashes, random seeds and capture/recording rates. These must be measured, not inferred. Synthetic tests are not live capture evidence.
