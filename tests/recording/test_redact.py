import json
import numpy as np
import pytest
from PIL import Image
from aether.recording.redact import redact_run,assert_shareable
def test_redact_copy_and_gate(tmp_path):
 src=tmp_path/'src';(src/'frames').mkdir(parents=True);Image.fromarray(np.full((20,20,3),255,dtype=np.uint8)).save(src/'frames/00000001.jpg',quality=100);(src/'manifest.json').write_text(json.dumps({'identity':{'run_id':'r1'}}));out=redact_run(src,tmp_path/'out',[(.25,.25,.75,.75)]);assert json.loads((out/'manifest.json').read_text())['redaction']['source_run_id']=='r1';assert_shareable(out,True)
 with Image.open(out/'frames/00000001.jpg') as im:assert im.getpixel((10,10))==(0,0,0)
 with pytest.raises(ValueError,match='unredacted'):assert_shareable(src,True)
