from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from aether.sim.scene import SyntheticScene
def generate():
 scene=SyntheticScene(seed=17);rows=[]
 for seq in (1,30,60,90):
  f=scene.frame(seq,seq/30);rows.append({'seq':seq,'elapsed_s':seq/30,'shape':list(f.shape),'health_ratio':round(scene.health_ratio(seq/30),6),'pixel_sum':int(np.asarray(f,dtype=np.uint64).sum())})
 return {'kind':'SYNTHETIC','seed':17,'samples':rows}
def main():
 p=argparse.ArgumentParser();p.add_argument('--i-reviewed-the-diff',action='store_true');p.add_argument('--output',default='tests/regression/golden/scene.json');a=p.parse_args()
 if not a.i_reviewed_the_diff:p.error('explicit --i-reviewed-the-diff required')
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(generate(),indent=2,sort_keys=True)+'\\n',encoding='utf-8');return 0
if __name__=='__main__':raise SystemExit(main())
