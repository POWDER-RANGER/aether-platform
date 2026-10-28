# Synthetic regression goldens

Golden outputs in tests/regression/golden are generated only from the deterministic SYNTHETIC scene. They are not live-capture or gameplay evidence.

To regenerate, run scripts/regression/update_golden.py --i-reviewed-the-diff. The flag is mandatory because changing a golden can silently normalize a regression. Review the complete JSON diff, compare it with the synthetic scene definition and intended reader/planner behavior, record the reason in the pull request, and retain the prior golden in Git history. Never update goldens merely to make a failing test pass. Owner review is required before changing any claimed acceptance criterion; this dataset contains no thresholds.
