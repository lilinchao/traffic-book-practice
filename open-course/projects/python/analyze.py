"""Reproduce project workbench results using the frozen real-data snapshots.

Standard-library baseline. Edit the analysis functions for your extension.
python python/analyze.py --project forecast --config forecast-experiment.json
"""
import argparse, collections, csv, datetime as dt, json, math
from pathlib import Path

DEFAULTS={
 'audit':{'year':'2018','method':'unique'},
 'forecast':{'horizon':'1','model':'ridge','period':'all','month':'all'},
 'hotspots':{'borough':'all','cell':'500','weight':'count'},
 'taxi':{'day':'all','period':'all','normalize':'daily'},
 'counting':{'line':'15','direction':'both','stride':'1','band':'0.3','gap':'1.5','type':'all'},
}
FILES={'audit':'audit','forecast':'forecast','hotspots':'crashes','taxi':'taxi','counting':'sind'}
MODEL_NAMES={'last':'上一已知值','day':'前日同期','week':'上周同期','calendar':'训练期星期小时均值','ridge':'岭回归'}
BOROUGHS={'Manhattan':'曼哈顿','Brooklyn':'布鲁克林','Queens':'皇后区','Bronx':'布朗克斯','Staten Island':'斯塔滕岛','EWR':'EWR','Unknown':'未知'}
DATA=Path(__file__).resolve().parents[1]/'data'
def avg(values): return sum(values)/len(values) if values else None
def weekend(s): return dt.date.fromisoformat(s[:10]).weekday()>=5
def hour(s): return int(s[11:13])

def validate(project,raw):
    out=DEFAULTS[project].copy()
    enums={'year':['all']+[str(y) for y in range(2012,2019)],'method':['raw','unique'],'horizon':['1','3','6'],'model':list(MODEL_NAMES),'period':['all','night','day'] if project=='taxi' else ['all','peak','offpeak'],'month':['all','07','08','09'],'borough':['all','MANHATTAN','BROOKLYN','QUEENS','BRONX','STATEN ISLAND','UNKNOWN'],'cell':['250','500','1000'],'weight':['count','injured'],'day':['all','weekday','weekend'],'normalize':['daily','total'],'direction':['both','positive','negative'],'stride':['1','5','10'],'type':['all','car','bus','truck','bicycle','motorcycle','tricycle']}
    for k,v in raw.items():
        if k not in out: raise ValueError('Unknown configuration key: '+k)
        v=str(v)
        if k in enums and v not in enums[k]: raise ValueError('Unsupported value for '+k)
        if k in ['line','band','gap']:
            lo,hi={'line':(-20,55),'band':(0,3),'gap':(.1,5)}[k]
            if not math.isfinite(float(v)) or not lo<=float(v)<=hi: raise ValueError('Out of range: '+k)
        out[k]=v
    return out

def audit(data,c):
    rows=[r for r in data['rows'] if c['year']=='all' or r[0].startswith(c['year'])]
    if not rows: return {'metrics':{'有效小时':0},'columns':[],'rows':[]}
    raw=sum(r[2] for r in rows)
    expected=(dt.datetime.fromisoformat(rows[-1][0])-dt.datetime.fromisoformat(rows[0][0])).total_seconds()/3600+1
    table=[]
    for h in range(24):
        g=[r for r in rows if hour(r[0])==h];n=sum(r[2] for r in g)
        table.append([h,len(g),n,avg([r[1] for r in g]),sum(r[1]*r[2] for r in g)/n if n else None])
    return {'metrics':{'原始行':raw,'不同小时':len(rows),'重复行':raw-len(rows),'范围内缺失时间标签':expected-len(rows)},'columns':['小时','不同小时样本数','原始行数','去重均值','原始行加权均值'],'rows':table}

def error_metrics(rows,index):
    if not rows: return [0,None,None,None]
    errors=[r[index]-r[1] for r in rows]
    return [len(rows),avg([abs(e) for e in errors]),math.sqrt(avg([e*e for e in errors])),avg(errors)]

def forecast(data,c):
    peak=[7,8,9,16,17,18]
    rows=[r for r in data['horizons'][c['horizon']]['rows'] if (c['month']=='all' or r[0][5:7]==c['month']) and (c['period']=='all' or (hour(r[0]) in peak)==(c['period']=='peak'))]
    index=list(MODEL_NAMES).index(c['model'])+2
    n,mae,rmse,bias=error_metrics(rows,index)
    table=[[name]+error_metrics(rows,i+2) for i,name in enumerate(MODEL_NAMES.values())]
    return {'metrics':{'有效测试样本':n,'MAE（辆/小时）':mae,'RMSE（辆/小时）':rmse,'平均预测偏差':bias},'columns':['方法','样本数','MAE','RMSE','平均预测减实测'],'rows':table,'exportColumns':['目标本地时间','实测','上一已知值','前日同期','上周同期','星期小时均值','岭回归'],'exportRows':rows}

def project_xy(lat,lon): return (lon+74.3)*111320*math.cos(math.radians(40.73)),(lat-40.45)*111320
def hotspots(data,c):
    selected=[r for r in data['rows'] if c['borough']=='all' or r[2]==c['borough']]
    valid=[r for r in selected if r[7]];size=int(c['cell']);cells={}
    for r in valid:
        x,y=project_xy(r[3],r[4]);col,row=math.floor(x/size),math.floor(y/size)
        cell=cells.setdefault((col,row),{'count':0,'injured':0})
        cell['count']+=1;cell['injured']+=r[5]
    ordered=sorted(cells.items(),key=lambda v:(-v[1][c['weight']],v[0]))
    table=[[f'{col}:{row}',v['count'],v['injured'],round(40.45+(row+.5)*size/111320,6),round(-74.3+(col+.5)*size/(111320*math.cos(math.radians(40.73))),6)] for (col,row),v in ordered]
    return {'metrics':{'筛选记录':len(selected),'可落图记录':len(valid),'坐标排除':len(selected)-len(valid),'有记录网格':len(cells)},'columns':['网格ID','事故记录数','伤者人数','中心纬度','中心经度'],'rows':table}

def taxi(data,c):
    dates=[f'2024-01-{d:02}' for d in range(1,32)]
    dates=[d for d in dates if c['day']=='all' or weekend(d)==(c['day']=='weekend')]
    hours=[h for h in range(24) if c['period']=='all' or (h>=22 or h<6)==(c['period']=='night')]
    matrix={b:[0]*24 for b in BOROUGHS}
    for d,b,h,n in data['rows']:
        if d in dates and h in hours: matrix[b][h]+=n
    den=len(dates) if c['normalize']=='daily' else 1
    table=sorted([[BOROUGHS[b],sum(v),sum(v)/den] for b,v in matrix.items()],key=lambda r:-r[2])
    return {'metrics':{'筛选上车记录':sum(sum(v) for v in matrix.values()),'日期数':len(dates),'每天选取小时数':len(hours),'未知地区记录':sum(matrix['Unknown'])},'columns':['行政区','上车记录总数','每日日均所选时段记录' if c['normalize']=='daily' else '所选时段记录'],'rows':table,'exportColumns':['行政区','小时','原始记录数','展示值','日期分母'],'exportRows':[[BOROUGHS[b],h,matrix[b][h],matrix[b][h]/den,den] for b in matrix for h in hours]}

def counting(data,c):
    times=sorted({r[1] for r in data['rows']});keep=set(times[::int(c['stride'])])
    rows=[r for r in data['rows'] if r[1] in keep and (c['type']=='all' or r[4]==c['type'])]
    previous={};counted=set();events=[]
    line,band,gap=float(c['line']),float(c['band']),float(c['gap'])*1000
    for ident,t,x,y,kind in rows:
        side=-1 if x<line-band else 1 if x>line+band else 0
        prev=previous.get(ident)
        if prev and t-prev['time']>gap: prev=None
        if side and prev and prev['side'] and side!=prev['side']:
            direction='positive' if side>0 else 'negative';key=(ident,direction)
            if key not in counted and c['direction'] in ['both',direction]:
                events.append([ident,t/1000,'+x' if direction=='positive' else '-x',kind,x,y]);counted.add(key)
        previous[ident]={'time':t,'side':side or (prev['side'] if prev else 0)}
    return {'metrics':{'跨线事件':len(events),'正方向事件':sum(e[2]=='+x' for e in events),'负方向事件':sum(e[2]=='-x' for e in events),'采样后轨迹点':len(rows)},'columns':['轨迹ID','检测到另一侧时刻（秒）','方向','类型','x（米）','y（米）'],'rows':events}

ANALYSES={'audit':audit,'forecast':forecast,'hotspots':hotspots,'taxi':taxi,'counting':counting}
def run(project,config=None,data_dir=DATA):
    c=validate(project,config or {})
    data=json.loads((Path(data_dir)/(FILES[project]+'.json')).read_text(encoding='utf-8'))
    result=ANALYSES[project](data,c)
    return {'project':project,'config':c,'sourceSha':data['meta']['sha256'],**result}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',choices=DEFAULTS,required=True)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--data',type=Path,default=DATA)
    parser.add_argument('--output',type=Path,default=Path('outputs'))
    args=parser.parse_args();config={}
    if args.config:
        value=json.loads(args.config.read_text(encoding='utf-8-sig'))
        if 'project' in value and value['project']!=args.project: raise ValueError('Configuration belongs to another project')
        config=value.get('config',value)
    result=run(args.project,config,args.data)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/(args.project+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    with (args.output/(args.project+'-results.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(result.get('exportColumns',result['columns']));writer.writerows(result.get('exportRows',result['rows']))
    print(json.dumps(result['metrics'],ensure_ascii=True))

if __name__=='__main__':main()
