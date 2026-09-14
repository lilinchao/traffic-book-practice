"""Download official data and create frozen, auditable classroom snapshots.

python prepare_data.py --output ../data --cache ./raw-cache
Requires pandas, numpy, pyarrow and scikit-learn. No generated traffic data.
"""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import argparse, datetime, gzip, hashlib, io, json, time, zipfile
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

SIND_REV='930e4dea78d924c6e9a58ff8e378331f93bba8ec'
FETCH_DATES={}
SOURCES={
 'metro':'https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip',
 'taxi':'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2024-01.parquet',
 'zones':'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv',
 'sind':f'https://media.githubusercontent.com/media/SOTIF-AVLab/SinD/{SIND_REV}/Data/Tianjin/8_2_1/Veh_smoothed_tracks.csv',
 'sind_license':f'https://raw.githubusercontent.com/SOTIF-AVLab/SinD/{SIND_REV}/LICENSE',
}

def fetch(url,path):
    if path.exists():
        FETCH_DATES[url]=datetime.datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        return path.read_bytes()
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'TrafficProjectCourse/1.0'}),timeout=180) as r: b=r.read()
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b)
            FETCH_DATES[url]=datetime.date.today().isoformat()
            return b
        except Exception:
            if attempt==2: raise
            time.sleep(2*(attempt+1))

def clean_json(v):
    if isinstance(v,dict): return {str(k):clean_json(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean_json(x) for x in v]
    if isinstance(v,np.generic): v=v.item()
    if isinstance(v,float) and not np.isfinite(v): return None
    return v

def write(output,name,payload):
    output.mkdir(parents=True,exist_ok=True)
    (output/(name+'.json')).write_text(json.dumps(clean_json(payload),ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    print('Prepared',name,flush=True)

def provenance(blob,url,**extra):
    return {'url':url,'sha256':hashlib.sha256(blob).hexdigest(),'retrieved':FETCH_DATES.get(url,datetime.date.today().isoformat()),**extra}

def metro_data(cache,out):
    b=fetch(SOURCES['metro'],cache/'metro.zip')
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        name=next(n for n in z.namelist() if n.endswith('.csv.gz'))
        raw=pd.read_csv(io.BytesIO(gzip.decompress(z.read(name))))
    raw['date']=pd.to_datetime(raw['date_time'])
    g=raw.groupby('date')['traffic_volume']
    if (g.nunique()>1).any(): raise ValueError('Conflicting hourly traffic volume: review before merging')
    clean=g.first().sort_index()
    counts=g.size().reindex(clean.index)
    rows=[[t.strftime('%Y-%m-%dT%H:%M'),int(v),int(n)] for t,v,n in zip(clean.index,clean,counts)]
    meta=provenance(b,SOURCES['metro'],source='John Hogue, UCI Metro Interstate Traffic Volume (2019)',license='CC BY 4.0',citation='https://doi.org/10.24432/C5X60B',rawRows=len(raw),hours=len(clean),duplicateRows=len(raw)-len(clean),conflictingHours=0,zeroKelvin=int((raw.temp==0).sum()),start=rows[0][0],end=rows[-1][0],columns=['local_time','volume','raw_multiplicity'],scope='I-94 westbound ATR301; local clock labels, no DST reconstruction, no gap imputation')
    write(out,'audit',{'meta':meta,'rows':rows})
    pd.DataFrame(rows,columns=meta['columns']).to_csv(out/'metro-hours.csv',index=False)
    return clean,meta

def forecast_data(clean,meta,out):
    train_period=clean.loc['2017']
    calendar=train_period.groupby([train_period.index.weekday,train_period.index.hour]).mean().to_dict()
    results={}
    for h in [1,3,6]:
        target=clean.index
        origin=target-pd.Timedelta(hours=h)
        frame=pd.DataFrame({'time':target,'origin':origin,'actual':clean.values})
        frame['last']=clean.reindex(origin).values
        frame['day']=clean.reindex(target-pd.Timedelta(hours=24)).values
        frame['week']=clean.reindex(target-pd.Timedelta(hours=168)).values
        frame['origin_day']=clean.reindex(origin-pd.Timedelta(hours=24)).values
        frame['origin_week']=clean.reindex(origin-pd.Timedelta(hours=168)).values
        frame['calendar']=[calendar.get((t.weekday(),t.hour),float(train_period.mean())) for t in target]
        frame=frame.dropna().copy()
        t=frame.time.dt
        x=np.column_stack([frame['last'],frame.origin_day,frame.origin_week,np.sin(2*np.pi*t.hour/24),np.cos(2*np.pi*t.hour/24),np.sin(2*np.pi*t.dayofweek/7),np.cos(2*np.pi*t.dayofweek/7)])
        train=(frame.time>='2017-01-01')&(frame.time<'2018-01-01')
        val=(frame.time>='2018-01-01')&(frame.time<'2018-07-01')
        test=(frame.time>='2018-07-01')&(frame.time<'2018-10-01')
        scores=[]
        for alpha in [0.1,10,1000]:
            model=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(x[train],frame.loc[train,'actual'])
            scores.append((mean_absolute_error(frame.loc[val,'actual'],np.maximum(0,model.predict(x[val]))),alpha,model))
        score,alpha,model=min(scores,key=lambda a:a[0])
        frame.loc[test,'ridge']=np.maximum(0,model.predict(x[test]))
        records=[]
        for r in frame[test].itertuples():
            records.append([r.time.strftime('%Y-%m-%dT%H:%M'),round(r.actual,3),round(r.last,3),round(r.day,3),round(r.week,3),round(r.calendar,3),round(r.ridge,3)])
        results[str(h)]={'rows':records,'alpha':alpha,'validationMAE':float(score),'trainN':int(train.sum()),'validationN':int(val.sum()),'testN':int(test.sum()),'testMAE':{k:float(mean_absolute_error(frame.loc[test,'actual'],frame.loc[test,k])) for k in ['last','day','week','calendar','ridge']}}
    write(out,'forecast',{'meta':{**meta,'columns':['target_time','actual','last','day','week','calendar','ridge'],'train':'2017','validation':'2018-01 to 2018-06','test':'2018-07 to 2018-09','protocol':'Rolling forecast, latest observation available at origin=t-h. Fixed 2017 training, alpha selected only on validation. Common complete cases per horizon. No future weather, no interpolation.'},'horizons':results})

def crash_data(cache,out):
    base='https://data.cityofnewyork.us/resource/h9gi-nx95.json'
    where="crash_date >= '2024-01-01T00:00:00' AND crash_date < '2024-02-01T00:00:00'"
    query={'$select':'collision_id,crash_date,borough,latitude,longitude,number_of_persons_injured,number_of_persons_killed','$where':where,'$order':'collision_id','$limit':50000}
    url=base+'?'+urlencode(query)
    b=fetch(url,cache/'nyc-january-2024.json')
    count_url=base+'?'+urlencode({'$select':'count(*) as n','$where':where})
    total=int(json.loads(fetch(count_url,cache/'nyc-january-count.json'))[0]['n'])
    raw=json.loads(b)
    assert len(raw)==total and total<50000,'API result truncated or snapshot count changed'
    assert len({r['collision_id'] for r in raw})==len(raw)
    def number(v):
        try: return float(v)
        except (TypeError,ValueError): return None
    rows=[]
    for r in raw:
        lat,lon=number(r.get('latitude')),number(r.get('longitude'))
        valid=lat is not None and lon is not None and 40.45<lat<41 and -74.3<lon<-73.65
        rows.append([r['collision_id'],r['crash_date'][:10],r.get('borough','UNKNOWN'),lat,lon,int(r.get('number_of_persons_injured',0)),int(r.get('number_of_persons_killed',0)),valid])
    meta=provenance(b,url,source='NYC Open Data / NYPD Motor Vehicle Collisions - Crashes',license='NYC Open Data original terms',rawRows=total,validCoordinates=sum(r[-1] for r in rows),start='2024-01-01',end='2024-01-31',columns=['id','date','borough','latitude','longitude','injured','killed','valid_coordinates'],scope='All API records for January 2024 at retrieval; reporting and location completeness limits apply. No traffic exposure denominator.')
    write(out,'crashes',{'meta':meta,'rows':rows})
    pd.DataFrame(rows,columns=meta['columns']).to_csv(out/'nyc-crashes-2024-01.csv',index=False)

def taxi_data(cache,out):
    b=fetch(SOURCES['taxi'],cache/'green_tripdata_2024-01.parquet')
    zone_bytes=fetch(SOURCES['zones'],cache/'taxi_zone_lookup.csv')
    raw=pd.read_parquet(io.BytesIO(b))
    zones=pd.read_csv(io.BytesIO(zone_bytes)).set_index('LocationID')
    raw_n=len(raw)
    data=raw[(raw.lpep_pickup_datetime>='2024-01-01')&(raw.lpep_pickup_datetime<'2024-02-01')].copy()
    data['date']=data.lpep_pickup_datetime.dt.strftime('%Y-%m-%d')
    data['hour']=data.lpep_pickup_datetime.dt.hour
    data['borough']=data.PULocationID.map(zones.Borough).fillna('Unknown')
    agg=data.groupby(['date','borough','hour']).size().reset_index(name='count')
    rows=agg.values.tolist()
    assert sum(r[-1] for r in rows)==len(data)==56549
    meta=provenance(b,SOURCES['taxi'],source='NYC TLC green taxi records, January 2024',license='NYC TLC original terms',rawRows=raw_n,keptTrips=len(data),excluded=raw_n-len(data),columns=['date','borough','hour','count'],scope='Pickup records only; not all travel demand or unmet demand. Zero group counts mean no retained record, not no travel.',zoneUrl=SOURCES['zones'],zoneSha256=hashlib.sha256(zone_bytes).hexdigest())
    write(out,'taxi',{'meta':meta,'rows':rows})
    agg.to_csv(out/'taxi-borough-date-hour.csv',index=False)

def sind_data(cache,out):
    b=fetch(SOURCES['sind'],cache/'sind-8_2_1.csv')
    assert hashlib.sha256(b).hexdigest()=='c377452a22ad0d57e2ebc9a8bccf050ef50c32c10ce35d7984a12edc24e532b5'
    license_bytes=fetch(SOURCES['sind_license'],cache/'SIND-LICENSE.txt')
    raw=pd.read_csv(io.BytesIO(b))
    raw.columns=raw.columns.str.strip()
    t0=float(raw.timestamp_ms.min())
    clip=raw[(raw.timestamp_ms>=t0)&(raw.timestamp_ms<t0+120000)].copy()
    clip['timestamp_ms']=clip.timestamp_ms-t0
    clip['track_id']=clip.track_id.astype(str)
    cols=['track_id','timestamp_ms','x','y','agent_type']
    clip=clip[cols].sort_values(['timestamp_ms','track_id'])
    clip[['x','y']]=clip[['x','y']].round(4)
    assert not clip.duplicated(['track_id','timestamp_ms']).any()
    meta=provenance(b,SOURCES['sind'],source='Xu et al. SIND (ITSC 2022), public Tianjin 8_2_1 sample',license='Custom dataset terms prohibit commercial use; see SIND-LICENSE.txt (not unmodified CC0)',commit=SIND_REV,columns=cols,rawRows=len(raw),rows=len(clip),tracks=clip.track_id.nunique(),durationSeconds=120,originalStartMs=t0,scope='First 120 seconds of published smoothed vehicle trajectories. Excludes pedestrian file. Replay is not source video, detector output or independently checked counting ground truth.',types=sorted(clip.agent_type.unique().tolist()))
    write(out,'sind',{'meta':meta,'rows':clip.values.tolist()})
    clip.to_csv(out/'sind-tianjin-120s.csv',index=False)
    (out/'SIND-LICENSE.txt').write_bytes(license_bytes)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    parser.add_argument('--cache',type=Path,default=Path('raw-cache'))
    args=parser.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    args.output.mkdir(parents=True,exist_ok=True)
    clean,meta=metro_data(args.cache,args.output)
    forecast_data(clean,meta,args.output)
    crash_data(args.cache,args.output)
    taxi_data(args.cache,args.output)
    sind_data(args.cache,args.output)

if __name__=='__main__': main()
