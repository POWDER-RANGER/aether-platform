from __future__ import annotations
import re,sys
from pathlib import Path
LABELS={'VERIFIED','PARTIALLY VERIFIED','UNVERIFIED','FAILED','BLOCKED','NOT IMPLEMENTED'}
STATUS=re.compile(r'(?im)^\s*status\s*[:|]\s*([^|\n]+)')
LINK=re.compile(r'!?\[[^]]*\]\(([^)]+)\)')
PATH=re.compile(r'\x60((?:src|tests|scripts|docs|configuration|interfaces|evidence)/[^\x60]+)\x60')
def check(root:Path):
 e=[]; docs=[root/'README.md',*((root/'docs').rglob('*.md') if (root/'docs').exists() else [])]
 for p in docs:
  if not p.is_file():continue
  s=p.read_text(encoding='utf-8')
  for m in STATUS.finditer(s):
   label=m.group(1).strip().strip('*_').upper()
   if label not in LABELS:e.append(f'{p.relative_to(root)}: invalid status label {label!r}')
  for target in LINK.findall(s):
   target=target.strip().split()[0].strip('<>').split('#',1)[0].split('?',1)[0]
   if target and not re.match(r'^(https?://|mailto:|#|data:)',target,re.I) and not (p.parent/target).resolve().exists():e.append(f'{p.relative_to(root)}: broken link {target!r}')
  for path in PATH.findall(s):
   if not (root/path).exists():e.append(f'{p.relative_to(root)}: cited path does not exist: {path}')
 for p in root.rglob('*'):
  if not p.is_file() or '.git' in p.parts or '.pytest_tmp' in p.parts:continue
  rel=p.relative_to(root).as_posix()
  if rel.startswith(('configuration/','docs/protocols/')) or p.suffix.lower() not in {'.md','.yaml','.yml','.json','.py','.toml','.txt'}:continue
  try: lines=p.read_text(encoding='utf-8').splitlines()
  except UnicodeDecodeError:continue
  for n,line in enumerate(lines,1):
   if 'PROPOSED' in line.upper() and 'THRESHOLD' in line.upper() and 'NOT FROZEN' not in line.upper():e.append(f'{rel}:{n}: proposed threshold missing NOT FROZEN')
 return e
def main():
 e=check(Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve());print('\n'.join(e) if e else 'Documentation checks passed');return int(bool(e))
if __name__=='__main__':raise SystemExit(main())
