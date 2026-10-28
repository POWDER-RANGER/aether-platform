from __future__ import annotations
import re,sys
from pathlib import Path
LABELS={'VERIFIED','PARTIALLY VERIFIED','UNVERIFIED','FAILED','BLOCKED','NOT IMPLEMENTED'}
STATUS=re.compile(r'(?im)^\s*\*{0,2}status:\*{0,2}\s*([^|\n]+)')
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
  if doc.relative_to(root).as_posix()=='docs/architecture/LEGACY-REFERENCE.md':continue
  lines=content.splitlines();i=0
  while i<len(lines):
   if not lines[i].strip().startswith('|'):
    i+=1;continue
   block=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    block.append(lines[i]);i+=1
   header=block[0].lower()
   if 'requested file' in header:continue
   cells=[c.strip().lower() for c in block[0].strip('|').split('|')]
   status_columns=[n for n,c in enumerate(cells) if c=='status']
   if doc.relative_to(root).as_posix()!='docs/decisions/DECISIONS.md':
    for row in block[2:]:
     values=[c.strip().strip('*_').upper() for c in row.strip('|').split('|')]
     for col in status_columns:
      if col<len(values) and values[col] and values[col] not in LABELS:
       errors.append(f'{doc.relative_to(root)}: invalid table status label {values[col]!r}')
   columns=[n for n,c in enumerate(cells) if c in {'path','file path','repository path','evidence path'}]
   for row in block[2:]:
    values=[c.strip() for c in row.strip('|').split('|')]
    for col in columns:
     if col>=len(values):continue
     for cited in PATH.findall(values[col]):
      if any(token in cited for token in ('{','}','*','<','>','...')):continue
      if not (root/cited).exists():errors.append(f'{doc.relative_to(root)}: cited table path does not exist: {cited}')
 for path in root.rglob('*'):
  if not path.is_file() or '.git' in path.parts or '.pytest_tmp' in path.parts:continue
  rel=path.relative_to(root).as_posix()
  if rel.startswith(('configuration/','docs/protocols/')) or path.suffix.lower() not in {'.md','.yaml','.yml','.json','.py','.toml','.txt'}:continue
  try:source=path.read_text(encoding='utf-8')
  except UnicodeDecodeError:continue
  for number,line in enumerate(source.splitlines(),1):
   if 'PROPOSED' in line.upper() and 'THRESHOLD' in line.upper() and 'NOT FROZEN' not in line.upper():
    errors.append(f'{rel}:{number}: proposed threshold missing NOT FROZEN')
 return errors
def main():
 errors=check(Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve())
 print('\n'.join(errors) if errors else 'Documentation checks passed')
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
