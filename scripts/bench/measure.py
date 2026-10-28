from __future__ import annotations

import sys

from aether.cli_ext import main


if __name__ == "__main__":
    raise SystemExit(main(["bench", *sys.argv[1:]]))
