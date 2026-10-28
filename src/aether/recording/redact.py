from __future__ import annotations
import json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
def redact_run(run_dir,output_dir,boxes):
 src,out=Path(run_dir).resolve(),Path(output_dir).resolve()
 if not src.is_dir() or src==out or src in out.parents:raise ValueError('output must be outside source run')
 for b in boxes:
  if len(b)!=4 or not(0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1):raise ValueError(f'invalid normalized ROI: {b}')
 if out.exists():raise FileExistsError(out)
 shutil.copytree(src,out)
 for p in (out/'frames').glob('*') if (out/'frames').is_dir() else []:
  if p.suffix.lower() not in {'.jpg','.jpeg','.png'}:continue
  with Image.open(p) as im:
   im=im.convert('RGB');d=ImageDraw.Draw(im)
   for x0,y0,x1,y1 in boxes:d.rectangle((round(x0*im.width),round(y0*im.height),round(x1*im.width),round(y1*im.height)),fill=(0,0,0))
   im.save(p,quality=95)
 m=out/'manifest.json';data=json.loads(m.read_text()) if m.exists() else {};data['redaction']={'redacted':True,'source_run_id':data.get('identity',{}).get('run_id',src.name),'boxes_normalized':[list(b) for b in boxes]};m.write_text(json.dumps(data,indent=2),encoding='utf-8');return out
def assert_shareable(run_dir,for_sharing=False):
 if not for_sharing:return
 try:d=json.loads((Path(run_dir)/'manifest.json').read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError) as ex:raise ValueError('cannot share without valid manifest') from ex
 if not d.get('redaction',{}).get('redacted',False):raise ValueError('sharing refused: unredacted frames')
