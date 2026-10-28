from pathlib import Path
from scripts.docs.check_docs import check
from scripts.docs.build_index import build
def test_checker_rules(tmp_path):
 (tmp_path/'docs').mkdir();(tmp_path/'src/x').mkdir(parents=True);(tmp_path/'src/x/a.py').write_text('pass')
 (tmp_path/'README.md').write_text('[guide](docs/guide.md)');(tmp_path/'docs/guide.md').write_text('Status: VERIFIED\n'+chr(96)+'src/x/a.py'+chr(96))
 assert check(tmp_path)==[]
 (tmp_path/'docs/guide.md').write_text('Status: GREEN\n[bad](missing.md)\n'+chr(96)+'src/missing.py'+chr(96)+'\n'+('PROPOSED '+'threshold: 4'));errors=check(tmp_path)
 assert any('invalid status' in x for x in errors) and any('broken link' in x for x in errors) and any(('proposed '+'threshold') in x for x in errors)
def test_index_read_only(tmp_path):
 p=tmp_path/'evidence/E-01/a.json';p.parent.mkdir(parents=True);p.write_text('{"run_id":"r1","timestamp_utc":"2026-10-28T00:00:00Z","criterion":"E-01","status":"VERIFIED"}');before=p.read_bytes();result=build(tmp_path);assert 'r1' in result and 'VERIFIED' in result and p.read_bytes()==before
