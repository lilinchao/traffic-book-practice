"""Real night-street pedestrian detection, association and directional counting.

Teaching protocol, NOT the official MOT17 leaderboard metric. Video/annotation
derivatives retain CC BY-NC-SA 3.0; detector wrapper and model retain Apache-2.0.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from case_algorithms import associate
from learning_support import csv_file

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'chapters/data/video'
sys.path.insert(0, str(ROOT/'chapters/python/vendor/yolox'))
from yolox import YoloX

PROTOCOL = dict(id='ch08-night-pedestrian-v1',sequence='MOT17-04',frames=[1,1050],fps=30,
                sample_stride=3,thresholds=[0.35,0.60],nms_iou=.5,matching_iou=.5,
                line_axis='image_y',line_px=300,deadband_px=5,max_gap_s=.5,event_tolerance_s=.5,
                association_gate_px=45,position_scale_px=10,model='OpenCV Zoo YOLOX 2022nov COCO',
                scope='公开训练序列的固定教学复核，无本序列训练或调参，不是独立场景泛化测试')


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detect(model_path, video_path=DATA/'mot17-04-raw.mp4', stride=3):
    """Only raw images enter the detector; annotations are never loaded here."""
    cv2.setNumThreads(2)
    from prepare_video_lesson import VIDEO_SHA,MODEL_SHA
    if file_sha(video_path)!=VIDEO_SHA or file_sha(model_path)!=MODEL_SHA:
        raise ValueError('The fixed teaching input or model hash does not match')
    if stride!=3:raise ValueError('This protocol uses stride=3; changes require a new protocol')
    net = YoloX(str(model_path),confThreshold=.35,nmsThreshold=.5)
    capture = cv2.VideoCapture(str(video_path))
    n,fps,w,h = [capture.get(k) for k in [cv2.CAP_PROP_FRAME_COUNT,cv2.CAP_PROP_FPS,cv2.CAP_PROP_FRAME_WIDTH,cv2.CAP_PROP_FRAME_HEIGHT]]
    assert (int(n),fps,int(w),int(h)) == (1050,30,960,540), (n,fps,w,h)
    frames=[]
    for frame in range(1,1051):
        ok,image = capture.read()
        if not ok:raise ValueError(f'Video ended at frame {frame}')
        if (frame-1)%stride:continue
        rgb=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        scale=min(640/rgb.shape[0],640/rgb.shape[1])
        small=cv2.resize(rgb,(int(rgb.shape[1]*scale),int(rgb.shape[0]*scale)))
        padded=np.full((640,640,3),114,dtype=np.float32)
        padded[:small.shape[0],:small.shape[1]]=small
        result=net.infer(padded)
        people=[]
        for d in result:
            if int(d[-1])!=0:continue
            x,y,bw,bh=(d[:4]/scale).astype(float)
            x1,y1,x2,y2=max(0,x),max(0,y),min(w,x+bw),min(h,y+bh)
            if x2>x1 and y2>y1:people.append([x1,y1,x2-x1,y2-y1,float(d[-2])])
        frames.append({'frame':frame,'time_s':(frame-1)/fps,'detections':people})
        if len(frames)%25==0:print('Detected',len(frames),'sampled frames',flush=True)
    capture.release()
    return dict(protocol=PROTOCOL,video_sha256=file_sha(video_path),model_sha256=file_sha(model_path),
                opencv=cv2.__version__,width=int(w),height=int(h),frames=frames)


def load_annotations(path=DATA/'mot17-04-gt.txt'):
    if file_sha(path)!='f8cfbe36ef38a2e1857d7ebfe7d754b2355a3ffb9e1f9cedea435e86e4fbc948':
        raise ValueError('The fixed annotation file hash does not match')
    values=np.loadtxt(path,delimiter=',')
    frames={i:[] for i in range(1,1051)}
    for frame,ident,left,top,width,height,mark,category,visibility in values:
        frames[int(frame)].append([int(ident),(left-1)/2,(top-1)/2,width/2,height/2,int(mark),int(category),float(visibility)])
    return frames


def iou(a,b):
    if not len(a) or not len(b):return np.empty((len(a),len(b)))
    a,b=np.array(a,float),np.array(b,float)
    lo=np.maximum(a[:,None,:2],b[None,:,:2]);hi=np.minimum(a[:,None,:2]+a[:,None,2:4],b[None,:,:2]+b[None,:,2:4])
    inter=np.maximum(0,hi-lo).prod(axis=2)
    return inter/(a[:,2:4].prod(axis=1)[:,None]+b[:,2:4].prod(axis=1)[None,:]-inter)


def match_boxes(pred,truth,ignore):
    overlaps=iou(pred,truth);matches=[]
    if overlaps.size:
        rr,cc=linear_sum_assignment(np.where(overlaps>=.5,1-overlaps,1e6))
        matches=[(int(r),int(c)) for r,c in zip(rr,cc) if overlaps[r,c]>=.5]
    matched={p for p,_ in matches};ignored=[]
    overlap_ignore=iou(pred,ignore)
    for p in range(len(pred)):
        if p not in matched and overlap_ignore.shape[1] and overlap_ignore[p].max()>=.5:ignored.append(p)
    return matches,ignored


def events(rows,line=300,band=5,gap=.5):
    """rows: [id,time_s,foot_x,foot_y]; once per ID per image direction."""
    previous,seen,result={},set(),[]
    for ident,t,x,y in sorted(rows,key=lambda r:(r[1],r[0])):
        side=-1 if y<line-band else 1 if y>line+band else 0
        old=previous.get(ident)
        if old and t-old[0]>gap:old=None
        if old and side and old[1] and side!=old[1] and (ident,side) not in seen:
            seen.add((ident,side));result.append([ident,t,'down' if side>0 else 'up'])
        previous[ident]=(t,side or (old[1] if old else 0))
    return result


def evaluate(detection, annotations):
    all_reference=[[r[0],(f-1)/30,r[1]+r[3]/2,r[2]+r[4]] for f,rows in annotations.items() for r in rows if r[5]==1 and r[6]==1]
    reference_events=events(all_reference)
    result=dict(protocol=PROTOCOL,width=960,height=540,reference_events=reference_events,runs={},
                annotation_sha256=file_sha(DATA/'mot17-04-gt.txt'),video_sha256=detection['video_sha256'],model_sha256=detection['model_sha256'])
    for threshold in PROTOCOL['thresholds']:
        frames=[{**f,'detections':[d for d in f['detections'] if d[4]>=threshold]} for f in detection['frames']]
        positions=[(f['time_s'],np.array([[d[0]+d[2]/2,d[1]+d[3]] for d in f['detections']]).reshape(-1,2)/10) for f in frames]
        assignments=associate(positions,'kalman',gate=4.5,max_age=.5)
        visual=[];track_points=[];links={};gt_last={};switches=tp=fp=fn=ignored_count=gt_count=0
        for f,ids in zip(frames,assignments):
            gt=[r for r in annotations[f['frame']] if r[5]==1 and r[6]==1]
            ignored=[r for r in annotations[f['frame']] if r[6] in [2,7,8,12]]
            matches,excluded=match_boxes([d[:4] for d in f['detections']],[r[1:5] for r in gt],[r[1:5] for r in ignored])
            tp+=len(matches);fp+=len(ids)-len(matches)-len(excluded);fn+=len(gt)-len(matches);gt_count+=len(gt);ignored_count+=len(excluded)
            mapping={p:gt[g][0] for p,g in matches}
            for p,g in matches:
                ident,track,t=gt[g][0],ids[p],f['time_s']
                links[(track,round(t,6))]=ident
                if ident in gt_last and t-gt_last[ident][0]<=.5 and track!=gt_last[ident][1]:switches+=1
                gt_last[ident]=(t,track)
            predicted=[]
            for j,(d,ident) in enumerate(zip(f['detections'],ids)):
                track_points.append([ident,f['time_s'],d[0]+d[2]/2,d[1]+d[3]])
                predicted.append([ident,*d,mapping.get(j),j in excluded])
            visual.append({'frame':f['frame'],'time_s':f['time_s'],'predicted':predicted,'truth':gt})
        predicted_events=events(track_points)
        # Identity at the event frame comes from independent frame-IoU matching,
        # never from the trajectory's future majority identity or nearest event.
        eligible=[]
        for i,(track,t,direction) in enumerate(predicted_events):
            gt_id=links.get((track,round(t,6)))
            for j,(reference_id,rt,rd) in enumerate(reference_events):
                if gt_id==reference_id and direction==rd and abs(t-rt)<=.5:eligible.append((abs(t-rt),i,j))
        used_p,used_g=set(),set();matched_events=[]
        for dt,i,j in sorted(eligible):
            if i not in used_p and j not in used_g:used_p.add(i);used_g.add(j);matched_events.append([i,j,dt])
        direction_rows=[]
        for direction in ['up','down']:
            a=sum(r[2]==direction for r in reference_events);p=sum(r[2]==direction for r in predicted_events)
            direction_rows.append([direction,a,p,p-a])
        scores=dict(sampled_frames=len(frames),GT_boxes=gt_count,TP=tp,FP=fp,FN=fn,ignored_detections=ignored_count,
                    precision=tp/(tp+fp) if tp+fp else 0,recall=tp/(tp+fn) if tp+fn else 0,
                    matched_identity_changes=switches,reference_events=len(reference_events),predicted_events=len(predicted_events),
                    event_TP=len(used_p),event_FP=len(predicted_events)-len(used_p),event_FN=len(reference_events)-len(used_g))
        result['runs'][str(threshold)]=dict(metrics=scores,directions=direction_rows,frames=visual,
                                           predicted_events=predicted_events,event_matches=matched_events,
                                           missed_reference=[i for i in range(len(reference_events)) if i not in used_g],
                                           unmatched_predicted=[i for i in range(len(predicted_events)) if i not in used_p])
    return result


def export(result, output):
    output.mkdir(parents=True,exist_ok=True)
    (output/'results.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
    columns=['threshold',*next(iter(result['runs'].values()))['metrics']]
    csv_file(output/'metrics.csv',columns,[[threshold,*run['metrics'].values()] for threshold,run in result['runs'].items()])
    csv_file(output/'events.csv',['origin','threshold','track_id','time_s','image_direction'],
             [['annotation','',*r] for r in result['reference_events']]+[['model',threshold,*r] for threshold,run in result['runs'].items() for r in run['predicted_events']])
    csv_file(output/'review.csv',['threshold','event_type','time_s','track_id','direction','observation','reviewer','status'],
             [[threshold,'missed_annotation',*([run_event[1],run_event[0],run_event[2]]),'','','pending'] for threshold,run in result['runs'].items() for i in run['missed_reference'] for run_event in [result['reference_events'][i]]])
    print(json.dumps({k:r['metrics'] for k,r in result['runs'].items()},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--detect',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'outputs/ch08-video')
    args=parser.parse_args();cache=DATA/'detections.json'
    if args.detect:
        value=detect(ROOT/'outputs/video-models/yolox.onnx')
        cache.write_text(json.dumps(value,separators=(',',':')),encoding='utf-8')
    else:value=json.loads(cache.read_text(encoding='utf-8'))
    export(evaluate(value,load_annotations()),args.output)
