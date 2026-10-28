from __future__ import annotations
import re,sys
from pathlib import Path
LABELS={'VERIFIED','PARTIALLY VERIFIED','UNVERIFIED','FAILED','BLOCKED','NOT IMPLEMENTED'}
STATUS=re.compile(r'(?im)^\s*(?:\*\*)?status(?:\*\*)?\s*:\s*([^|\n]+)')
LINK=re.compile(r'!?\[[^]]*\]\(([^)]+)\)')
PATH=re.compile(r'\x60((?:src|tests|scripts|docs|configuration|interfaces|evidence)/[^\x60]+)\x60')
def check(root:Path):
 errors=[]
 docs=[root/'README.md',*((root/'docs').rglob('*.md') if (root/'docs').exists() else [])]
 for doc in docs:
  if not doc.is_file():continue
  content=doc.read_text(encoding='utf-8')
  if doc.relative_to(root).as_posix()!='docs/decisions/DECISIONS.md':
   for match in STATUS.finditer(content):
    label=match.group(1).strip().strip('*_').upper()
    if label not in LABELS:errors.append(f'{doc.relative_to(root)}: invalid status label {label!r}')
  for target in LINK.findall(content):
   target=target.strip().split()[0].strip('<>').split('#',1)[0].split('?',1)[0]
   if target and not re.match(r'^(https?://|mailto:|#|data:)',target,re.I) and not (doc.parent/target).resolve().exists():
    errors.append(f'{doc.relative_to(root)}: broken link {target!r}')
  lines=content.splitlines()
  header=next((line.lower() for line in lines if line.strip().startswith('|') and ('path' in line.lower() or 'file' in line.lower() or 'evidence' in line.lower())), '')
  if header and doc.relative_to(root).as_posix()!='docs/architecture/LEGACY-REFERENCE.md':
   for line in lines:
    if not line.strip().startswith('|'):continue
    for cited in PATH.findall(line):
     if any(token in cited for token in ('{','}','*','<','>','...')):continue
     if not (root/cited).exists():errors.append(f'{doc.relative_to(root)}: cited table path does not exist: {cited}')
 for path in root.rglob('*'):
  if not path.is_file() or '.git' in path.parts or '.pytest_tmp' in path.parts:continue
  rel=path.relative_to(root).as_posix()
  if rel.startswith(('configuration/','docs/protocols/')) or path.suffix.lower() not in {'.md','.yaml','.yml','.json','.py','.toml','.txt'}:continue
  try:content=path.read_text(encoding='utf-8')
  except UnicodeDecodeError:continue
  for number,line in enumerate(content.splitlines(),1):
   if 'PROPOSED' in line.upper() and 'THRESHOLD' in line.upper() and 'NOT FROZEN' not in line.upper():
    errors.append(f'{rel}:{number}: proposed threshold missing NOT FROZEN')
 return errors
def main():
 errors=check(Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve())
 print('\n'.join(errors) if errors else 'Documentation checks passed')
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
