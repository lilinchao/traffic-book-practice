from pathlib import Path
import csv, collections, datetime as dt, gzip, hashlib, io, json, sys, urllib.request, zipfile

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]; C=ROOT/'chapters';D=C/'data';D.mkdir(parents=True,exist_ok=True)
B=ROOT/'.cache/chapter-sources';B.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(C/'python'))
import ch03_inference, ch04_regression
import pandas as pd

def write_json(path, data): path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
def write_csv(path,columns,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(columns);w.writerows(rows)

# Existing common snapshots are included in the kit. Their upstream pipeline is
# projects/python/prepare_data.py. Check the same source before exposing raw input.
metro=B/'metro.zip'
if not metro.exists():
    with urllib.request.urlopen('https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip',timeout=120) as r:metro.write_bytes(r.read())
assert hashlib.sha256(metro.read_bytes()).hexdigest()==json.loads((ROOT/'projects/data/audit.json').read_text(encoding='utf-8'))['meta']['sha256'], 'Upstream source changed; review before combining versions'
with zipfile.ZipFile(metro) as z:
    name=next(n for n in z.namelist() if '.csv' in n);raw_csv=z.read(name)
    (D/'ch02_raw.csv').write_bytes(gzip.decompress(raw_csv) if name.endswith('.gz') else raw_csv)

# A day is included only if all three 07:00, 08:00, 09:00 hours are observed.
hours=json.loads((ROOT/'projects/data/audit.json').read_text(encoding='utf-8'))
days=collections.defaultdict(list)
for time,volume,*_ in hours['rows']:
    if time.startswith('2017') and int(time[11:13]) in [7,8,9]:days[time[:10]].append(volume)
rows=[]
for date,values in sorted(days.items()):
    if len(values)==3:rows.append({'date':date,'day_type':'weekend' if dt.date.fromisoformat(date).weekday()>=5 else 'weekday','peak_mean':round(sum(values)/3,6)})
write_csv(D/'ch03_daily.csv',['date','day_type','peak_mean'],[list(r.values()) for r in rows])
summary=ch03_inference.analyze(rows)
write_json(D/'ch03.json',{'meta':{'source':hours['meta'],'observedDays':len(rows),'excludedDays':365-len(rows),'definition':'2017年每日07、08、09时交通量的均值；仅保留三小时均观测到的日期'},'rows':rows,'reference':summary})

url='https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip'
raw=B/'bike-original.zip'
if not raw.exists():
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'TrafficCourse'}),timeout=120) as r:raw.write_bytes(r.read())
blob=raw.read_bytes()
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    hour_name=next(n for n in z.namelist() if n.endswith('hour.csv'))
    df=pd.read_csv(io.BytesIO(z.read(hour_name)))
    (D/'BIKE_README.txt').write_bytes(z.read(next(n for n in z.namelist() if n.lower().endswith('readme.txt'))))
# The label components casual and registered are deliberately not supplied as predictors.
df=df.rename(columns={'instant':'id'})
fields=['id','dteday']+ch04_regression.FEATURES+['cnt']
training=df[df.dteday<'2012-01-01'][fields]
validation=df[(df.dteday>='2012-01-01')&(df.dteday<'2012-07-01')][fields]
test=df[df.dteday>='2012-07-01'][fields]
training.to_csv(D/'ch04_train.csv',index=False)
validation.to_csv(D/'ch04_validation.csv',index=False)
test.drop(columns=['cnt']).to_csv(D/'ch04_test.csv',index=False)
test[['id','cnt']].to_csv(D/'ch04_solution.csv',index=False)
sample,predictions,models=ch04_regression.train(D)
for model in models:
    model['test']=ch04_regression.metrics(test.cnt,predictions[model['id']])
    pd.DataFrame({'id':test.id,'cnt':predictions[model['id']].round(6)}).to_csv(D/f'ch04_{model["id"]}_submission.csv',index=False)
retrieved=dt.datetime.fromtimestamp(raw.stat().st_mtime,dt.timezone.utc).date().isoformat()
write_json(D/'ch04.json',{'meta':{'source':url,'url':'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset','sha256':hashlib.sha256(blob).hexdigest(),'retrieved':retrieved,'license':'CC BY 4.0, Hadi Fanaee-T (2013), DOI:10.24432/C5W894','rawRows':len(df),'trainRows':len(training),'validationRows':len(validation),'testRows':len(test),'split':'2011训练；2012年1至6月验证；2012年7至12月公开练习测试','features':ch04_regression.FEATURES},'models':models,'rows':[[int(i),date,int(hour),int(y),*[round(float(predictions[k][j]),6) for k in ['mean','ridge','poisson']]] for j,(i,date,hour,y) in enumerate(test[['id','dteday','hr','cnt']].itertuples(index=False,name=None))]})
forecast=json.loads((ROOT/'projects/data/forecast.json').read_text(encoding='utf-8'))
fr=forecast['horizons']['1']['rows']
write_csv(D/'ch06_test.csv',['id'],[[r[0]] for r in fr])
write_csv(D/'ch06_sample_submission.csv',['id','volume'],[[r[0],r[2]] for r in fr])
write_csv(D/'ch06_solution.csv',['id','volume'],[[r[0],r[1]] for r in fr])
write_json(D/'ch06_scoring.json',{'rows':[[r[0],r[1]] for r in fr],'sourceSha':forecast['meta']['sha256']})
print(json.dumps({'ch03':{'days':len(rows),'default':{k:v for k,v in summary.items() if k!='bootstrap_means'}},'ch04':{'rows':len(df),'train':len(training),'validation':len(validation),'test':len(test),'models':models},'ch06Rows':len(fr)},ensure_ascii=False,indent=2))
