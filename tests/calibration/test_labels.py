import pytest
from aether.calibration.labels import append_label,score_labels
def test_label_store_and_score(tmp_path):
 p=tmp_path/'labels.jsonl';r=append_label(p,run_id='synthetic',frame_seq=1,roi='health',true_value=.8,labeller='owner');assert score_labels([r,{**r,'true_value':.4}],[.7,.5],'bar')['value']==pytest.approx(.1);assert score_labels([{'true_value':'yes'}],['yes'],'ocr')['value']==1.0;assert score_labels([],[],'template')['value'] is None
