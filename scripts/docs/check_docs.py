from __future__ import annotations

import re
import sys
from pathlib import Path

LABELS = {"VERIFIED", "PARTIALLY VERIFIED", "UNVERIFIED", "FAILED", "BLOCKED", "NOT IMPLEMENTED"}
STATUS = re.compile(r"(?im)^\s*\*{0,2}status:\*{0,2}\s*([^|\n]+)")
LINK = re.compile(r"!? \[[^]]*\]\(([^)]+)\)", re.X)
PATH = re.compile(r"\x60((?:src|tests|scripts|docs|configuration|interfaces|evidence)/[^\x60]+)\x60")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    docs = [root / "README.md", *((root / "docs").rglob("*.md") if (root / "docs").exists() else [])]
    for doc in docs:
        if not doc.is_file():
            continue
        content = doc.read_text(encoding="utf-8")
        if doc.relative_to(root).as_posix() != "docs/decisions/DECISIONS.md":
            for match in STATUS.finditer(content):
                label = match.group(1).strip().strip("*_").upper()
                if label not in LABELS:
                    errors.append(f"{doc.relative_to(root)}: invalid status label {label!r}")
        for target in LINK.findall(content):
            target = target.strip().split()[0].strip("<>").split("#", 1)[0].split("?", 1)[0]
            if not target or re.match(r"^(https?://|mailto:|#|data:)", target, re.I):
                continue
            if not (doc.parent / target).resolve().exists():
                errors.append(f"{doc.relative_to(root)}: broken link {target!r}")
        if doc.relative_to(root).as_posix() == "docs/architecture/LEGACY-REFERENCE.md":
            continue
        lines = content.splitlines()
        index = 0
        while index < len(lines):
            if not lines[index].strip().startswith("|"):
                index += 1
                continue
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index])
                index += 1
            cells = [cell.strip().lower() for cell in block[0].strip("|").split("|")]
            if "requested file" in block[0].lower():
                continue
            status_columns = [n for n, cell in enumerate(cells) if cell in {"evidence status", "evidence label"}]
            if doc.relative_to(root).as_posix() != "docs/decisions/DECISIONS.md":
                for row in block[2:]:
                    values = [cell.strip().strip("*_").upper() for cell in row.strip("|").split("|")]
                    for column in status_columns:
                        if column < len(values) and values[column] and values[column] not in LABELS:
                            errors.append(f"{doc.relative_to(root)}: invalid table status label {values[column]!r}")
            path_columns = [n for n, cell in enumerate(cells) if cell in {"path", "file path", "repository path", "evidence path"}]
            for row in block[2:]:
                values = [cell.strip() for cell in row.strip("|").split("|")]
                for column in path_columns:
                    if column >= len(values):
                        continue
                    for cited in PATH.findall(values[column]):
                        if any(token in cited for token in ("{", "}", "*", "<", ">", "...")):
                            continue
                        if not (root / cited).exists():
                            errors.append(f"{doc.relative_to(root)}: cited table path does not exist: {cited}")
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".pytest_tmp" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("configuration/", "docs/protocols/")) or path.suffix.lower() not in {
            ".md", ".yaml", ".yml", ".json", ".py", ".toml", ".txt"
        }:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(source.splitlines(), 1):
            if "PROPOSED" in line.upper() and "THRESHOLD" in line.upper() and "NOT FROZEN" not in line.upper():
                errors.append(f"{relative}:{number}: proposed threshold missing NOT FROZEN")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    errors = check(Path(args[0] if args else ".").resolve())
    print("\n".join(errors) if errors else "Documentation checks passed")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
