"""Deeper comparisons: spatial clustering, daily profiles and counting audits.

These are analysis starting points, not graded solutions. Uses the frozen data.
python python/extensions.py --project hotspots
python python/extensions.py --project taxi
python python/extensions.py --project counting --truth manual-events.csv
"""
import argparse, csv, datetime, json
from pathlib import Path
from analyze import DATA, run, project_xy

def save_csv(out,name,columns,rows):
    out.mkdir(parents=True,exist_ok=True)
    with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(columns);w.writerows(rows)

def spatial(out):
    import numpy as np
    from sklearn.cluster import DBSCAN
    data=json.loads((DATA/'crashes.json').read_text(encoding='utf-8'))
    records=[r for r in data['rows'] if r[7]]
    xy=np.array([project_xy(r[3],r[4]) for r in records])
    summaries=[]
    for eps in [150,350,700]:
        for minimum in [5,15]:
            labels=DBSCAN(eps=eps,min_samples=minimum).fit_predict(xy)
            clusters=len(set(labels)-{-1});noise=int((labels<0).sum())
            sizes=[int((labels==k).sum()) for k in set(labels) if k>=0]
            summaries.append([eps,minimum,clusters,noise,noise/len(labels),max(sizes,default=0)])
            save_csv(out,f'dbscan-{eps}-{minimum}.csv',['collision_id','x_m','y_m','cluster_id'],[[r[0],*p,int(k)] for r,p,k in zip(records,xy,labels)])
    save_csv(out,'dbscan-sensitivity.csv',['eps_m','min_samples','clusters','noise_points','noise_fraction','largest_cluster'],summaries)
    return 'DBSCAN clusters are density-connected groups, not independently validated high-risk road sections. Compare with grids and explain scale sensitivity.'

def profiles(out):
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    data=json.loads((DATA/'taxi.json').read_text(encoding='utf-8'))
    dates=[f'2024-01-{i:02}' for i in range(1,32)]
    boroughs=sorted({r[1] for r in data['rows']});matrix=np.zeros((31,len(boroughs)*24))
    for d,b,h,n in data['rows']:matrix[dates.index(d),boroughs.index(b)*24+h]+=n
    totals=matrix.sum(axis=1)
    if (totals==0).any():raise ValueError('A day has no retained observations: review before normalization')
    proportions=matrix/totals[:,None]
    comparison=[]
    for k in [2,3,4,5]:
        model=KMeans(n_clusters=k,n_init=10,random_state=42).fit(proportions)
        score=float(silhouette_score(proportions,model.labels_))
        comparison.append([k,score])
        save_csv(out,f'day-clusters-{k}.csv',['date','weekday_0_monday','retained_trips','cluster_id'],[[d,datetime.date.fromisoformat(d).weekday(),int(total),int(label)] for d,total,label in zip(dates,totals,model.labels_)])
        save_csv(out,f'cluster-centers-{k}.csv',['cluster_id','borough','hour','share'],[[j,b,h,float(center[bi*24+h])] for j,center in enumerate(model.cluster_centers_) for bi,b in enumerate(boroughs) for h in range(24)])
    save_csv(out,'day-cluster-comparison.csv',['k','silhouette_in_sample'],comparison)
    return 'Exploratory clustering of 31 daily profiles after dividing each day by its total. In-sample silhouette is not a prediction accuracy or evidence of unmet demand. Check whether normalization hides activity volume.'

def match_events(predicted,truth,tolerance=1.0):
    if tolerance<0:raise ValueError('Negative matching tolerance')
    used=set();matched=[];false_positive=[]
    for p in predicted:
        candidates=[(abs(float(t['time_s'])-p[1]),i) for i,t in enumerate(truth) if i not in used and str(t['track_id'])==str(p[0]) and str(t['direction']).lstrip("'")==p[2] and abs(float(t['time_s'])-p[1])<=tolerance]
        if candidates:
            delta,i=min(candidates);used.add(i);matched.append([p[0],p[1],p[2],float(truth[i]['time_s']),delta])
        else:false_positive.append(p)
    misses=[t for i,t in enumerate(truth) if i not in used]
    tp,fp,fn=len(matched),len(false_positive),len(misses)
    return {'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None},matched,false_positive,misses

def count_audit(out,truth_path,tolerance):
    comparison=[]
    for stride in ['1','5','10']:
        for gap in ['0.3','1.5']:
            result=run('counting',{'stride':stride,'gap':gap})
            comparison.append([stride,gap,*result['metrics'].values()])
    save_csv(out,'counting-sensitivity.csv',['stride_frames','max_gap_s','events','positive','negative','retained_points'],comparison)
    if not truth_path:return 'No manual labels supplied. Only rule sensitivity was measured. No counting accuracy has been claimed.'
    with truth_path.open(encoding='utf-8-sig',newline='') as f:truth=list(csv.DictReader(f))
    for t in truth:
        if not {'track_id','time_s','direction'}<=t.keys():raise ValueError('Manual labels require track_id,time_s,direction')
    result=run('counting')
    metrics,matched,fp,fn=match_events(result['rows'],truth,tolerance)
    (out/'manual-comparison.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    save_csv(out,'matched-events.csv',['track_id','observed_s','direction','manual_s','difference_s'],matched)
    save_csv(out,'unmatched-predictions.csv',result['columns'],fp)
    save_csv(out,'missed-manual-events.csv',['track_id','time_s','direction'],[[r['track_id'],r['time_s'],r['direction']] for r in fn])
    return 'Manual labels must be independent, complete for the same 120-second clip and use x=15m, both directions, all included vehicle classes. ID matching audits postprocessing, not independent detector tracking performance. '+json.dumps(metrics)

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',choices=['hotspots','taxi','counting'],required=True);p.add_argument('--output',type=Path,default=Path('outputs/extensions'));p.add_argument('--truth',type=Path);p.add_argument('--tolerance',type=float,default=1)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    note=spatial(a.output) if a.project=='hotspots' else profiles(a.output) if a.project=='taxi' else count_audit(a.output,a.truth,a.tolerance)
    (a.output/(a.project+'-interpretation.txt')).write_text(note,encoding='utf-8');print(note)
if __name__=='__main__':main()
