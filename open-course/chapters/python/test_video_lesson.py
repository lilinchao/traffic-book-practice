"""Check independent annotations, event matching and frozen video evidence."""
import json
import numpy as np
from video_lesson import ROOT,DATA,evaluate,load_annotations,events,iou,match_boxes,file_sha

assert events([[1,0,10,290],[1,.1,10,300],[1,.2,10,310]])==[[1,.2,'down']]
assert events([[1,0,10,290],[1,1,10,310]])==[]
assert iou([[0,0,10,10]],[[0,0,10,10]])[0,0]==1
matches,ignored=match_boxes([[0,0,10,10],[20,0,10,10]],[[0,0,10,10]],[[20,0,10,10]])
assert matches==[(0,0)] and ignored==[1]
d=json.loads((DATA/'detections.json').read_text(encoding='utf-8'))
assert [r['frame'] for r in d['frames']]==list(range(1,1051,3))
frozen=json.loads((DATA/'results.json').read_text(encoding='utf-8'))
computed=evaluate(d,load_annotations())
assert computed==frozen
for name,run in computed['runs'].items():
    m=run['metrics'];assert m['GT_boxes']==m['TP']+m['FN']
    assert m['reference_events']==m['event_TP']+m['event_FN']
    assert m['predicted_events']==m['event_TP']+m['event_FP']
    for pi,gi,dt in run['event_matches']:
        track,time,direction=run['predicted_events'][pi]
        source,rt,rd=computed['reference_events'][gi]
        frame=next(f for f in run['frames'] if abs(f['time_s']-time)<1e-8)
        prediction=next(p for p in frame['predicted'] if p[0]==track)
        assert prediction[6]==source and direction==rd and abs(time-rt)<=.5
preview=json.loads((DATA/'preview.json').read_text())
assert file_sha(DATA/preview['file'])==preview['sha256']
print('PASS: video input inventory, independent frame matches, ignore rules, count deadband/gaps, 2 complete evaluations and event identity/time matching')
