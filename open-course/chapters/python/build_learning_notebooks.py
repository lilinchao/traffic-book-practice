"""Generate the eight single-version, executable chapter notebooks."""
import hashlib
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
PROTOCOLS = json.loads((ROOT/'chapters/data/project-protocols.json').read_text(encoding='utf-8'))
NOTEBOOKS = {}


def md(text):
    return dict(cell_type='markdown', metadata={}, source=dedent(text).strip()+'\n')


def code(text):
    return dict(cell_type='code', metadata={}, execution_count=None, outputs=[], source=dedent(text).strip()+'\n')


def start(chapter, title):
    q = PROTOCOLS[f'ch{chapter:02}']
    return [md(f'''# 第{chapter}章 {title}

本工作本是一份连续的实践，不另分学生任务版与参考版。按单元逐步运行，在参数区修改条件，记录自己的结果和解释；不要只执行整章脚本后截一张图。

**协议：** `{q['id']}`  
**必做：** {'；'.join(q['required'])}  
**对象：** {q['unit']}  
**样本：** {q['population']}  
**划分：** {q['split']}  
**比较：** {q['comparison']}

先解压完整资料包，在其目录内运行。安装 `python -m pip install -r chapters/python/{'video' if chapter==8 else 'learning'}-requirements.txt`，再启动Jupyter。代码只读取固定真实数据；输出写入`outputs/chXX/`，不覆盖原数据。

每一步的“请解释”需用本次实际结果回答。默认参考配置可直接运行，但自动生成文件不代表学生已完成分析。'''), code('''
from pathlib import Path
import sys, json
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'chapters/data').is_dir() and (p/'projects/data').is_dir())
sys.path.insert(0, str(ROOT/'chapters/python'))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
from learning_support import metrics, metric_table, csv_file, primary, predictions_table, report, save_plot
THREADS = threadpool_limits(limits=1)
print('Data root:', ROOT)
''')]


n = start(1, '交通问题与数据方案')
n += [md('''## 1. 读取真实来源及观测定义
请解释：记录少是否必然说明需求小？任选两种来源，比较观测对象和限制。'''), code('''
sources = pd.read_csv(ROOT/'chapters/data/ch01_sources.csv')
display(sources)
'''), md('''## 2. 直接查看数据样本
这不是把数据拼成一个总体。请比较事故一行与出租车聚合一行分别代表什么。'''), code('''
snapshots = {}
for name in ['audit', 'crashes', 'taxi', 'sind']:
    item = json.loads((ROOT/f'projects/data/{name}.json').read_text(encoding='utf-8'))
    snapshots[name] = {'rows': len(item['rows']), 'first_observation': item['rows'][0]}
display(pd.DataFrame(snapshots).T)
'''), md('''## 3. 写出问题-指标-字段关系
修改下方列表，将示例问题改成自己的具体任务。没有相应字段的指标不得列为已测得。'''), code('''
plan = pd.DataFrame([
    ['事故排查', '2024年1月哪些位置需优先核查', '事故记录数', 'crashes.rows: id/lat/lon', '不能直接得出风险率'],
    ['出租车运营', '同一区域夜间日均服务量如何变化', '上车记录条/小时/日', 'taxi.rows: date/borough/hour/count', '未观测未满足需求']
], columns=['scenario', 'question', 'indicator', 'observed_fields', 'boundary'])
display(plan)
csv_file(ROOT/'outputs/ch01/problem_variables.csv', plan.columns, plan.values)
'''), md('''## 4. 导出方案证据并完成文字论证
需提交两种来源适配对照、许可清单和最低可行方案。下面只生成证据与待回答问题，不伪造已开展的调查。'''), code('''
report(ROOT, 1, '交通数据分析最低可行方案', {'来源数量': len(sources), '问题变量表': plan.to_string(index=False)}, ['为什么选择该对象与尺度？', '哪些判断仍需补充数据？', '如何合规获取和验证？'])
''')]
NOTEBOOKS[1] = n

n = start(2, '交通监测数据整编')
n += [md('''## 1. 读取原表与观测时刻
请解释：同小时多行是否就是重复车辆？此处是一份小时交通量表，不是逐车记录。'''), code('''
raw = pd.read_csv(ROOT/'chapters/data/ch02_raw.csv', keep_default_na=False)
raw['time'] = pd.to_datetime(raw['date_time'])
display(raw.head())
print('Raw rows:', len(raw), 'Distinct hours:', raw['time'].nunique())
'''), md('''## 2. 冲突核查先于去重
修改检查字段时，解释为什么不能任意保留第一条不同值。时间缺口与字段空值要分别检查。'''), code('''
conflicts = raw.groupby('time').traffic_volume.nunique()
assert not (conflicts > 1).any(), 'Different traffic volumes share a timestamp; investigate before deduplication'
audit = []
for year, part in raw.groupby(raw.time.dt.year):
    start_time, end_time = part.time.min(), part.time.max()
    skeleton = pd.date_range(start_time, end_time, freq='h')
    audit.append([int(year), len(part), part.time.nunique(), len(part)-part.time.nunique(), len(skeleton.difference(part.time))])
quality = pd.DataFrame(audit, columns=['year','raw_rows','unique_hours','extra_rows','missing_labels_within_coverage'])
display(quality)
csv_file(ROOT/'outputs/ch02/quality_audit.csv', quality.columns, quality.values)
'''), md('''## 3. 生成整编结果并比较日变化曲线
下面不将缺测补0。修改统计年份，说明你在比较哪些日期的均值。'''), code('''
clean = raw.drop_duplicates('time').sort_values('time')
assert len(clean) == 40575
csv_file(ROOT/'outputs/ch02/ch02_clean.csv', ['local_time','volume'], zip(clean.time.dt.strftime('%Y-%m-%dT%H:%M'),clean.traffic_volume))
YEAR = 2017  # 可修改；须与图的解释一致
weighted = raw[raw.time.dt.year == YEAR].groupby(raw.time.dt.hour).traffic_volume.mean()
unique = clean[clean.time.dt.year == YEAR].groupby(clean.time.dt.hour).traffic_volume.mean()
plt.figure(figsize=(9,4)); plt.plot(weighted.index,weighted,label='Raw-row weighted'); plt.plot(unique.index,unique,label='Unique hours')
plt.xlabel('Local hour');plt.ylabel('Vehicles/hour');plt.legend();save_plot(ROOT,2,'hourly_profile')
'''), md('''## 4. 写出数据接收结论
选择一处曲线差异和一段缺口，说明可能原因与所需核查证据。'''), code('''
report(ROOT,2,'道路监测数据接收说明',{'质量审计':quality.to_string(index=False),'整编小时数':len(clean),'比较年份':YEAR},['去重的证据是什么？','最大差异时段如何解释？','哪些缺口仍需向数据提供方核查？'])
''')]
NOTEBOOKS[2] = n

n = start(3, '早高峰抽样调查')
n += [md('''## 1. 核查日期总体
请解释：358个完整日期与365个日历日期的差别，为什么不能将三个小时当作三个调查日？'''), code('''
daily = pd.read_csv(ROOT/'chapters/data/ch03_daily.csv')
assert len(daily)==358 and daily.date.is_unique
display(daily.groupby('day_type').peak_mean.agg(['count','mean']))
print('Excluded dates:', sorted(set(pd.date_range('2017-01-01','2017-12-31').strftime('%Y-%m-%d'))-set(daily.date)))
'''), md('''## 2. 参数与随机抽样
主协议固定B=1000、seed=42。若改种子或日期类型，将其作为另一组实验记录，不能将不同总体成绩混用。'''), code('''
SAMPLE_SIZES = [20,60,90]
B = 1000
SEED = 42
GROUP = 'all'  # all / weekday / weekend
pool = daily if GROUP=='all' else daily[daily.day_type==GROUP]
assert B>=50 and all(2<=n<=len(pool) for n in SAMPLE_SIZES)
# 与网页相同的LCG和Fisher-Yates顺序，便于逐项复核。
def random_stream(seed):
    state = seed
    while True:
        state = (1664525*state + 1013904223) % 2**32
        yield state/2**32
def sample_and_bootstrap(n):
    rnd = random_stream(SEED)
    order = list(range(len(pool)))
    for i in range(len(order)-1,0,-1):
        j=int(next(rnd)*(i+1));order[i],order[j]=order[j],order[i]
    sample=pool.iloc[order[:n]]
    values=sample.peak_mean.to_numpy(float)
    boot=np.array([np.mean([values[int(next(rnd)*n)] for _ in range(n)]) for _ in range(B)])
    return sample,boot
'''), md('''## 3. 形成区间并比较调查工作量
阅读并修改重采样代码。请解释：B增加与调查日期数增加分别改变什么？'''), code('''
rows=[]
for n_days in SAMPLE_SIZES:
    sample,boot=sample_and_bootstrap(n_days)
    lower,upper=np.quantile(boot,[.025,.975])
    rows.append([sample.peak_mean.mean(),lower,upper,n_days,(upper-lower)/2])
    csv_file(ROOT/f'outputs/ch03/sample_{n_days}.csv',sample.columns,sample.values)
result=pd.DataFrame(rows,columns=['estimate','lower','upper','n_days','half_width'])
display(result)
csv_file(ROOT/'outputs/ch03/interval_comparison.csv',result.columns,result.values)
csv_file(ROOT/'outputs/ch03/ch03_submission.csv',result.columns[:4],[result.iloc[1,:4]])
plt.figure(figsize=(8,4));plt.errorbar(result.n_days,result.estimate,yerr=[result.estimate-result.lower,result.upper-result.estimate],fmt='o',capsize=5)
plt.xlabel('Survey days');plt.ylabel('Peak mean, vehicles/hour');save_plot(ROOT,3,'survey_precision')
'''), md('''## 4. 提出有条件的调查建议
不能将较窄区间解释为已经消除非随机缺失、日期相关和道路代表性问题。'''), code('''
report(ROOT,3,'早高峰抽样调查建议',{'参数':{'seed':SEED,'B':B,'group':GROUP},'区间':result.to_string(index=False)},['选多少调查日，依据是什么？','完整日期筛选可能带来什么偏差？','对未来日期和其他断面能否外推？'])
''')]
NOTEBOOKS[3] = n

n = start(4, '高峰租借量估计与回归对照')
n += [md('''## 1. 分别读取训练、验证和测试输入
测试标签在参数冻结后才用于评价。天气是当小时实测条件，不等于已实现天气未知时的提前预测。'''), code('''
FILES=['chapters/data/ch04_'+name+'.csv' for name in ['train','validation','test','solution']]
train,valid,test=[pd.read_csv(ROOT/p) for p in FILES[:3]]
print(len(train),len(valid),len(test));display(train.head())
NUMERIC=['temp','atemp','hum','windspeed']
CATEGORICAL=['mnth','hr','holiday','weekday','weathersit']
assert not {'casual','registered','cnt'} & set(NUMERIC+CATEGORICAL)
'''), md('''## 2. 只用训练集拟合预处理
请检查独热编码为什么删除首类别，为什么不同时放入重复表达的season、workingday。若改变输入列，须标明新配置。'''), code('''
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
transform=ColumnTransformer([('numeric',StandardScaler(),NUMERIC),('calendar',OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=False),CATEGORICAL)])
X=sm.add_constant(transform.fit_transform(train),has_constant='add')
Xv=sm.add_constant(transform.transform(valid),has_constant='add')
Xt=sm.add_constant(transform.transform(test),has_constant='add')
y=train.cnt.to_numpy(float)
assert np.linalg.matrix_rank(X)==X.shape[1]
print('Design matrix:',X.shape)
'''), md('''## 3. 实际拟合OLS、泊松和NB2
修改ALPHAS后只能根据验证期选取，不依据测试误差选参。请解释NB2的条件方差假设。'''), code('''
ALPHAS=[0.05,0.2,0.5,1.0]
models={'OLS':sm.OLS(y,X).fit(),'Poisson':sm.GLM(y,X,family=sm.families.Poisson()).fit(maxiter=200)}
trials=[]
for alpha in ALPHAS:
    fitted=sm.GLM(y,X,family=sm.families.NegativeBinomial(alpha=alpha)).fit(maxiter=200)
    assert fitted.converged
    trials.append((metrics(valid.cnt,fitted.predict(Xv))['RMSE'],alpha,fitted))
_,chosen_alpha,models['NB2']=min(trials,key=lambda r:(r[0],r[1]))
validation=pd.DataFrame([[a,score] for score,a,_ in trials],columns=['alpha','validation_RMSE'])
display(validation);print('Frozen alpha:',chosen_alpha)
'''), md('''## 4. 在共同4376小时评价
此时才读取测试标签。比较平均偏差与RMSE是否给出相同模型顺序；不要求NB2一定获胜。'''), code('''
truth=pd.read_csv(ROOT/FILES[3]).set_index('id')
assert set(test.id)==set(truth.index)
actual=truth.loc[test.id,'cnt'].to_numpy(float)
predictions={name:np.maximum(0,m.predict(Xt)) for name,m in models.items()}
scores=metric_table(actual,predictions);display(scores)
periods=[]
for period,hours in [('morning',[7,8,9]),('evening',[16,17,18])]:
    mask=test.hr.isin(hours).to_numpy()
    for name,pred in predictions.items():periods.append({'period':period,'model':name,**metrics(actual[mask],pred[mask])})
peak=pd.DataFrame(periods);display(peak)
'''), md('''## 5. 画出日内形态并导出自己的结果
图为按小时平均，不能代替逐条误差。主结果JSON可在网页“主实验成果自测”导入。'''), code('''
plt.figure(figsize=(10,4))
for name,values in {'observed':actual,**predictions}.items():
    profile=pd.Series(values).groupby(test.hr.to_numpy()).mean()
    plt.plot(profile.index,profile,label=name)
plt.xlabel('Hour');plt.ylabel('Rentals/hour');plt.legend();save_plot(ROOT,4,'hourly_service')
outputs={'predictions':predictions_table(test.id,predictions),'validation':validation.to_dict('records'),'peak':peak.to_dict('records')}
bundle=primary(ROOT,4,FILES,{'numeric':NUMERIC,'categorical':CATEGORICAL,'alpha_candidates':ALPHAS,'selected_alpha':chosen_alpha},outputs)
csv_file(ROOT/'outputs/ch04/predictions.csv',outputs['predictions']['columns'],outputs['predictions']['rows'])
csv_file(ROOT/'outputs/ch04/peak_errors.csv',peak.columns,peak.values)
'''), md('''## 6. 完成高峰服务量估计报告
引用一个低估较大的时段，说明为何不能将租借量误差直接换算成需要调运的车辆数。'''), code('''
report(ROOT,4,'共享单车高峰服务量估计报告',{'共同小时数':len(actual),'总体误差':scores.to_string(index=False),'高峰误差':peak.to_string(index=False)},['哪种模型适合本次服务量估计？','早晚高峰的主要问题是什么？','进一步做站点调度还缺什么？'])
''')]
NOTEBOOKS[4] = n

n = start(5,'事故候选地点筛查')
n += [md('''## 1. 固定有效点集与距离单位
不要对真实未知坐标进行插值补造。此局部距离近似服务教学对照，正式工程需要适当投影与误差检查。'''), code('''
FILES=['projects/data/crashes.json']
raw=json.loads((ROOT/FILES[0]).read_text(encoding='utf-8'))['rows']
valid=[r for r in raw if r[7]]
xy=np.array([[(r[4]+74.3)*111320*np.cos(np.deg2rad(40.73)),(r[3]-40.45)*111320] for r in valid])
assert len(raw)==7542 and len(valid)==7068
cells=sorted({tuple(map(int,r)) for r in np.floor(xy/500)})
grid_ids=[f'{x}:{y}' for x,y in cells]
probe=(np.array(cells)+.5)*500
print('Total / valid / excluded:',len(raw),len(valid),len(raw)-len(valid),'Probe cells:',len(probe))
'''), md('''## 2. 自己运行KDE带宽比较
KDE输出归一化概率密度，不是具有暴露分母的事故风险。改变BANDWIDTHS后重新执行，而不是只切换现成图片。'''), code('''
from sklearn.neighbors import KernelDensity
BANDWIDTHS=[250,500,1000]
density={str(h):np.exp(KernelDensity(kernel='gaussian',bandwidth=h).fit(xy).score_samples(probe))*1e6 for h in BANDWIDTHS}
top=lambda v:np.argsort(-v,kind='stable')[:20]
kde_table=pd.DataFrame([[h,float(d.max()),len(set(top(d))&set(top(density['500'])))] for h,d in density.items()],columns=['bandwidth_m','max_density_per_km2','top20_overlap_500m'])
display(kde_table)
'''), md('''## 3. 实际运行DBSCAN并检查巨簇
修改EPS或MIN_SAMPLES，查看哪些配置过碎、哪些产生巨簇。簇少或噪声少不必然更好。'''), code('''
from sklearn.cluster import DBSCAN
EPS=[150,350,700]
MIN_SAMPLES=[5,15]
clusters={};rows=[]
for eps in EPS:
    for minimum in MIN_SAMPLES:
        labels=DBSCAN(eps=eps,min_samples=minimum).fit_predict(xy)
        clusters[f'{eps}-{minimum}']=labels.tolist()
        sizes=np.bincount(labels[labels>=0])
        rows.append([eps,minimum,len(sizes),int((labels<0).sum()),int(sizes.max(initial=0))])
dbscan_table=pd.DataFrame(rows,columns=['eps_m','min_samples','clusters','noise','largest_cluster'])
display(dbscan_table)
'''), md('''## 4. 候选地图与现场排查清单
先按500米KDE给出3个可回查的候选示例。请编辑SELECTED和SITE_NOTES，写出自己的选择理由；代码不能替你确认道路结构或设施问题。'''), code('''
from collections import Counter
counts=Counter(tuple(map(int,r)) for r in np.floor(xy/500))
SELECTED=top(density['500'])[:3].tolist()  # 可改成固定评价点索引
SITE_NOTES={}  # 例如 {索引:'结合具体数据写选择依据；道路对象需另核实'}
candidates=[]
for i in SELECTED:
    col,row=cells[i]
    candidates.append({'grid_id':grid_ids[i],'east_m':float(probe[i,0]),'north_m':float(probe[i,1]),'accidents':counts[(col,row)],'density':float(density['500'][i]),'reason':SITE_NOTES.get(i,'自动高密度候选示例，待学生结合事故和道路资料核查'),'road_object':'待匹配路段或交叉口','evidence_needed':'道路结构、设施、交通暴露与现场记录'})
plt.figure(figsize=(8,6));plt.scatter(probe[:,0]/1000,probe[:,1]/1000,c=density['500'],s=5,cmap='Blues');plt.colorbar(label='Probability density / km2')
plt.scatter(probe[SELECTED,0]/1000,probe[SELECTED,1]/1000,c='red',marker='x')
plt.axis('equal');plt.xlabel('Local east / km');plt.ylabel('Local north / km');save_plot(ROOT,5,'candidate_map')
display(pd.DataFrame(candidates))
'''), md('''## 5. 导出空间证据
保存密度、簇成员与候选清单，而不只保存截图。主实验网格ID为“列:行”，以当前固定原点与500米评价网格解释，旧CSV自测另有旧格式说明。'''), code('''
outputs={'grid_ids':grid_ids,'density':{h:v.tolist() for h,v in density.items()},'clusters':clusters,'candidates':candidates}
primary(ROOT,5,FILES,{'bandwidths':BANDWIDTHS,'eps':EPS,'min_samples':MIN_SAMPLES,'grid_m':500},outputs)
csv_file(ROOT/'outputs/ch05/candidates.csv',candidates[0].keys(),[r.values() for r in candidates])
csv_file(ROOT/'outputs/ch05/dbscan_memberships.csv',['collision_id',*clusters],[[r[0],*[labels[i] for labels in clusters.values()]] for i,r in enumerate(valid)])
report(ROOT,5,'事故候选地点现场核查报告',{'KDE':kde_table.to_string(index=False),'DBSCAN':dbscan_table.to_string(index=False),'候选清单':pd.DataFrame(candidates).to_string(index=False)},['为什么选择这3处候选范围？','参数变化导致哪些结论不稳定？','实际道路排查还缺什么资料？'])
''')]
NOTEBOOKS[5] = n

n = start(6,'断面交通量多提前量预测')
n += [md('''## 1. 建立真实时间骨架和共同目标
请解释：主实验采用2169个共同目标，与旧1小时2190目标有什么区别？不要把缺失小时压缩成相邻小时。'''), code('''
FILES=['projects/data/audit.json','projects/data/forecast.json']
audit=json.loads((ROOT/FILES[0]).read_text(encoding='utf-8'))['rows']
frozen=json.loads((ROOT/FILES[1]).read_text(encoding='utf-8'))['horizons']
index=pd.date_range('2017-01-01','2018-09-30T23:00',freq='h')
source=pd.Series({pd.Timestamp(r[0]):r[1] for r in audit},dtype=float)
series=source.reindex(index)/1000
train=series.loc[:'2017-12-31T23:00']
common=sorted(set.intersection(*[set(r[0] for r in frozen[str(h)]['rows']) for h in [1,3,6]]))
targets=index.get_indexer(pd.to_datetime(common))
assert len(common)==2169 and len(train)==8760 and train.isna().sum()==47
actual=series.iloc[targets].to_numpy()*1000
'''), md('''## 2. 在训练期实际拟合模型
先运行下面预定阶数。若比较其他阶数，只根据验证期评价选择，再冻结参数；不得挑选测试期表现最好的一组当作独立结果。'''), code('''
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from case_algorithms import state_forecasts
DEFINITIONS=[('ARIMA',(2,0,0),(0,0,0,0)),('SARIMA',(2,0,0),(1,0,0,24))]
fitted_models={}
for name,order,seasonal in DEFINITIONS:
    model=SARIMAX(train,order=order,seasonal_order=seasonal,trend='c').fit(disp=False,maxiter=150)
    assert model.mle_retvals['converged'], name+' did not converge'
    fitted_models[name]=model
    print(name,model.params.to_dict())
'''), md('''## 3. 检查验证期与训练残差
极小p值提示仍有自相关，不等于模型完全无效。数值下溢为0不表示数学上的概率恰为零。'''), code('''
val_positions=np.flatnonzero((index>='2018-01-01')&(index<'2018-07-01')&series.notna())
filtered_models={};diagnostics=[]
for name,order,seasonal in DEFINITIONS:
    fitted=fitted_models[name]
    filtered=SARIMAX(series,order=order,seasonal_order=seasonal,trend='c').filter(fitted.params)
    filtered_models[name]=filtered
    validation_prediction=state_forecasts(filtered,val_positions,[1])[1]*1000
    residual=pd.Series(fitted.filter_results.standardized_forecasts_error[0],index=train.index).where(train.notna()).iloc[72:]
    longest=max((g.dropna() for _,g in residual.groupby(residual.isna().cumsum())),key=len)
    pvalue=float(acorr_ljungbox(longest,lags=[24],model_df=3 if seasonal[0] else 2).lb_pvalue.iloc[0])
    diagnostics.append({'model':name,'validation_RMSE':metrics(series.iloc[val_positions].to_numpy()*1000,validation_prediction)['RMSE'],'residual_n':len(longest),'LjungBox24_p':pvalue})
display(pd.DataFrame(diagnostics))
'''), md('''## 4. 按起点过滤状态滚动预测
函数只取t-h的过滤状态，不使用平滑状态。阅读`case_algorithms.py`的`state_forecasts`，说明为什么修改未来观测不应改变同一起点的预测。'''), code('''
predictions={}
for name,model in filtered_models.items():
    for h,values in state_forecasts(model,targets,[1,3,6]).items():
        predictions[f'{name}|h={h}']=values*1000
for h in [1,3,6]:
    rows={r[0]:r for r in frozen[str(h)]['rows']}
    predictions[f'Week|h={h}']=np.array([rows[t][4] for t in common])
    predictions[f'Calendar|h={h}']=np.array([rows[t][5] for t in common])
scores=metric_table(actual,predictions);display(scores)
peak_mask=np.isin(pd.to_datetime(common).hour,[7,8,9,16,17,18])
peak=metric_table(actual[peak_mask],{k:v[peak_mask] for k,v in predictions.items()});display(peak)
'''), md('''## 5. 预先固定图示窗口与失败样本
图只展示前72个共同目标，不挑最好片段。失败样本按绝对误差排序用于诊断，不能事后删掉再宣称改善。'''), code('''
HORIZON=3  # 可改为1或6
plt.figure(figsize=(11,4));plt.plot(common[:72],actual[:72],label='Observed')
for name in ['ARIMA','SARIMA','Calendar']:
    plt.plot(common[:72],predictions[f'{name}|h={HORIZON}'][:72],label=name)
plt.xticks([0,24,48,71],[common[i][5:16] for i in [0,24,48,71]],rotation=20)
plt.ylabel('Vehicles/hour');plt.legend();save_plot(ROOT,6,'forecast_window')
worst=np.argsort(-abs(predictions[f'SARIMA|h={HORIZON}']-actual))[:10]
failures=pd.DataFrame({'target':np.array(common)[worst],'actual':actual[worst],'prediction':predictions[f'SARIMA|h={HORIZON}'][worst]})
display(failures)
'''), md('''## 6. 交付主实验结果与运行适用性报告
JSON包含四方法三个提前量，不混入旧2190行CSV接口。'''), code('''
outputs={'predictions':predictions_table(common,predictions),'diagnostics':diagnostics,'peak':peak.to_dict('records')}
primary(ROOT,6,FILES,{'definitions':DEFINITIONS,'horizons':[1,3,6],'fit_end':'2017-12-31T23:00'},outputs)
csv_file(ROOT/'outputs/ch06/predictions.csv',outputs['predictions']['columns'],outputs['predictions']['rows'])
csv_file(ROOT/'outputs/ch06/failures.csv',failures.columns,failures.values)
report(ROOT,6,'断面交通量预测适用性报告',{'共同目标':len(common),'全期误差':scores.to_string(index=False),'高峰误差':peak.to_string(index=False),'失败样本':failures.to_string(index=False)},['不同提前量分别适合什么运行任务？','MAE与RMSE的排序为什么不同？','用于拥堵预警还缺哪些变量与验证？'])
''')]
NOTEBOOKS[6]=n

n=start(7,'分区运营预测与典型服务日')
n += [md('''## 1. 分开建立预测矩阵与探索性日画像
四区域预测有时间留出；全月聚类只用于探索，不可将其作为留出预测的输入。'''),code('''
FILES=['projects/data/taxi.json']
raw=json.loads((ROOT/FILES[0]).read_text(encoding='utf-8'))['rows']
NODES=['Manhattan','Brooklyn','Queens','Bronx']
boroughs=sorted({r[1] for r in raw})
matrix=np.zeros((31*24,4));profiles=np.zeros((31,len(boroughs)*24))
for date,borough,hour,count in raw:
    day=int(date[-2:])-1
    profiles[day,boroughs.index(borough)*24+hour]+=count
    if borough in NODES:matrix[day*24+hour,NODES.index(borough)]+=count
training=matrix[:21*24]
valid_idx=np.arange(21*24,24*24);test_idx=np.arange(24*24,31*24)
actual=matrix[test_idx]
print(matrix.shape,profiles.shape,actual.shape)
'''),md('''## 2. 构造滞后特征并在验证期选阶
查看X、y和模型系数。单区域AR只读取该区域自己的滞后，VAR读取全部四区域。'''),code('''
from learning_support import lag_design,fit_lag
LAGS=[1,3,24]
X_example,y_example=lag_design(training,3)
print('VAR lag-3 design:',X_example.shape,y_example.shape)
predictions={};selected={};validation=[]
for name,multi in [('AR',False),('VAR',True)]:
    trials=[]
    for lag in LAGS:
        model,predict=fit_lag(training,lag,multi)
        pred=np.maximum(0,np.array([predict(matrix[:t]) for t in valid_idx]))
        score=metrics(matrix[valid_idx].ravel(),pred.ravel())['RMSE']
        validation.append([name,lag,score]);trials.append((score,lag,model,predict))
    _,lag,model,predict=min(trials,key=lambda r:(r[0],r[1]))
    selected[name]=lag
    predictions[name]=np.maximum(0,np.array([predict(matrix[:t]) for t in test_idx]))
predictions['Calendar']=np.array([training[t%168::168].mean(axis=0) for t in test_idx])
predictions['Last']=matrix[test_idx-1]
display(pd.DataFrame(validation,columns=['model','lag','validation_RMSE']))
'''),md('''## 3. 比较共同672个区域小时
请解释：总体RMSE改善是否意味着每个区域都改善？'''),code('''
scores=metric_table(actual.ravel(),{k:v.ravel() for k,v in predictions.items()});display(scores)
node_scores=pd.DataFrame([{'region':region,'model':name,**metrics(actual[:,j],p[:,j])} for j,region in enumerate(NODES) for name,p in predictions.items()])
display(node_scores)
REGION='Queens'
j=NODES.index(REGION)
plt.figure(figsize=(11,4));plt.plot(actual[:,j],label='Observed')
for name in ['AR','VAR','Calendar']:plt.plot(predictions[name][:,j],label=name)
plt.xlabel('Test-hour index, Jan 25-31');plt.ylabel('Retained pickups/hour');plt.title(REGION);plt.legend();save_plot(ROOT,7,'regional_prediction')
'''),md('''## 4. 独立实施12组KMeans与成员一致性核查
中心向量表示相对时空形态。不要将簇编号直接命名为已确认的出行目的。'''),code('''
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score,adjusted_rand_score
K_VALUES=[2,3,4,5]
SEEDS=[42,7,19]
shares=profiles/profiles.sum(axis=1,keepdims=True)
memberships={};centers={};cluster_rows=[]
for k in K_VALUES:
    reference=None
    for seed in SEEDS:
        model=KMeans(n_clusters=k,n_init=10,random_state=seed).fit(shares)
        if reference is None:reference=model.labels_
        memberships[f'{k}-{seed}']=model.labels_.tolist()
        centers[f'{k}-{seed}']=model.cluster_centers_.tolist()
        cluster_rows.append([k,seed,float(silhouette_score(shares,model.labels_)),float(adjusted_rand_score(reference,model.labels_)),int(np.bincount(model.labels_).min())])
cluster_scores=pd.DataFrame(cluster_rows,columns=['K','seed','silhouette','ARI_vs_first_seed','smallest_cluster_days']);display(cluster_scores)
'''),md('''## 5. 联读形态与原始规模
修改VIEW，看看同一日期是否换组。柱高是日总量，颜色是占比聚类，两者不是同一变量。'''),code('''
VIEW='4-42'
plt.figure(figsize=(11,4));plt.bar(np.arange(1,32),profiles.sum(axis=1),color=plt.get_cmap('tab10')(np.array(memberships[VIEW])))
plt.xlabel('January day');plt.ylabel('Retained pickups/day');plt.title(VIEW);save_plot(ROOT,7,'typical_days')
ids=[f'2024-01-{t//24+1:02}T{t%24:02}:00|{b}' for t in test_idx for b in NODES]
outputs={'predictions':predictions_table(ids,{k:v.ravel() for k,v in predictions.items()}),'memberships':memberships,'centers':centers,'cluster_scores':cluster_scores.to_dict('records')}
primary(ROOT,7,FILES,{'nodes':NODES,'lags':LAGS,'selected_lags':selected,'K':K_VALUES,'seeds':SEEDS},outputs)
csv_file(ROOT/'outputs/ch07/predictions.csv',outputs['predictions']['columns'],outputs['predictions']['rows'])
csv_file(ROOT/'outputs/ch07/typical_day_memberships.csv',['date',*memberships],[[f'2024-01-{i+1:02}',*[v[i] for v in memberships.values()]] for i in range(31)])
report(ROOT,7,'分区运营研判与典型服务日报告',{'总体误差':scores.to_string(index=False),'分区误差':node_scores.to_string(index=False),'聚类稳定性':cluster_scores.to_string(index=False)},['哪些区域适合采用多区域预测？','哪些日型对初始化敏感？','运营假设还需哪些供给或候车数据验证？'])
''')]
NOTEBOOKS[7]=n

n=start(8,'匿名轨迹关联与交通调查')
n += [md('''## 1. 读取测得坐标，定义实验参数
这是SinD平滑地面轨迹，不是原始视频。阅读`associate`的常速度预测、卡尔曼更新和匈牙利分配，明确输入不包含源ID。'''),code('''
from case_algorithms import associate,count_events
FILES=['projects/data/sind.json']
raw=json.loads((ROOT/FILES[0]).read_text(encoding='utf-8'))['rows']
TIMES=sorted({r[1] for r in raw})
by_time={t:[] for t in TIMES}
for row in raw:by_time[row[1]].append(row)
STRIDES=[1,5,10]
GATE=5.0
MAX_AGE=1.5
print('Coordinates / source IDs:',len(raw),len({r[0] for r in raw}))
'''),md('''## 2. 构造匿名帧并真实运行关联器
每帧随机重排点，防止顺序隐含源身份。修改GATE或MAX_AGE时须作为另一组配置记录；计数规则先保持不变。'''),code('''
runs={}
for stride in STRIDES:
    kept=TIMES[::stride]
    rng=np.random.default_rng(42)
    ordered=[[by_time[t][i] for i in rng.permutation(len(by_time[t]))] for t in kept]
    frames=[(t/1000,np.array([[r[2],r[3]] for r in rows])) for t,rows in zip(kept,ordered)]
    for mode in ['position','kalman']:
        labels=associate(frames,mode,gate=GATE,max_age=MAX_AGE)
        audit=[]
        for rows,assigned in zip(ordered,labels):
            for row,new_id in zip(rows,assigned):
                audit.append([str(row[0]),new_id,row[1]/1000,row[2],row[3]])
        predicted=[[r[1],r[2],r[3],r[4]] for r in audit]
        reference=[[r[0],r[2],r[3],r[4]] for r in audit]
        runs[f'{stride}-{mode}']={'assignments':audit,'events':count_events(predicted),'reference_events':count_events(reference)}
'''),md('''## 3. 计算身份连续性与分方向计数
请解释：一致比例高为什么还可能存在大量碎片？总事件数一致为什么不代表100%计数正确？'''),code('''
audit_rows=[]
for variant,run in runs.items():
    last_track={};last_source={};correct=total=switches=0
    for source,track,time,x,y in run['assignments']:
        if track in last_track and time-last_track[track][1]<=1.5:
            total+=1;correct+=last_track[track][0]==source
        if source in last_source and time-last_source[source][1]<=1.5 and track!=last_source[source][0]:switches+=1
        last_track[track]=(source,time);last_source[source]=(track,time)
    events=run['events']
    audit_rows.append([variant,len({r[1] for r in run['assignments']}),correct/total if total else None,switches,len(run['reference_events']),len(events),sum(r[2]=='+x' for r in events),sum(r[2]=='-x' for r in events)])
scores=pd.DataFrame(audit_rows,columns=['variant','generated_tracks','source_pair_agreement','ID_changes','source_events','new_events','positive','negative']);display(scores)
'''),md('''## 4. 定位并回看错误身份连接
按可核查错接对生成清单，逐条检查。这里不是独立人工视频标注。'''),code('''
VIEW='10-kalman'
run=runs[VIEW];last={};wrong=[]
for source,track,time,x,y in run['assignments']:
    if track in last and source!=last[track][0] and time-last[track][1]<=1.5:
        wrong.append([track,last[track][0],source,time,x,y])
    last[track]=(source,time)
wrong_table=pd.DataFrame(wrong,columns=['new_track','previous_source','current_source','time_s','x_m','y_m']);display(wrong_table.head(10))
plt.figure(figsize=(9,4));plt.bar(scores.variant,scores.new_events,label='New IDs');plt.plot(scores.variant,scores.source_events,'ko-',label='Source ID reference')
plt.xticks(rotation=25);plt.ylabel('Crossing events');plt.legend();save_plot(ROOT,8,'identity_to_count')
'''),md('''## 5. 导出调查证据与人工核查记录表
输出包含每次运行的身份指派与事件表。请在核查表记录真实观察依据，不把算法输出重新命名为人工真值。'''),code('''
primary(ROOT,8,FILES,{'strides':STRIDES,'gate_m':GATE,'max_age_s':MAX_AGE,'line_x_m':15,'band_m':.3,'count_gap_s':1.5}, {'runs':runs})
csv_file(ROOT/'outputs/ch08/events.csv',['variant','track_id','time_s','direction'],[[variant,*event] for variant,run in runs.items() for event in run['events']])
csv_file(ROOT/'outputs/ch08/wrong_associations.csv',wrong_table.columns,wrong_table.values)
csv_file(ROOT/'outputs/ch08/manual_audit.csv',['source_material','frame_or_time','object_reference','direction','observation','reviewer','status'],[['SinD trajectory (not video)',r[3],r[0],'to verify','to inspect','','pending'] for r in wrong[:10]])
report(ROOT,8,'分方向通行调查及身份误差分析',{'关联与事件':scores.to_string(index=False),'错接样例':wrong_table.head(10).to_string(index=False)},['哪一类关联错误影响了通行计数？','采样与门限是否改变结论？','哪些结论还必须用授权视频和独立标注验证？'])
''')]
n += [md('''## 6. 补齐真实影像链路：夜间步行街调查
这是独立影像协议`ch08-night-pedestrian-v1`，与SinD的米制轨迹不混合。按`VIDEO_LESSON.md`先确认非商业教学许可。首次安装video-requirements.txt并运行prepare_video_lesson.py下载固定模型。下方读取真实35秒视频，打印帧率和图像尺寸。'''),code('''
import cv2
from video_lesson import DATA,PROTOCOL,detect,load_annotations,evaluate,export
capture=cv2.VideoCapture(str(DATA/'mot17-04-raw.mp4'))
print('Frames / fps / width / height:',[capture.get(k) for k in [cv2.CAP_PROP_FRAME_COUNT,cv2.CAP_PROP_FPS,cv2.CAP_PROP_FRAME_WIDTH,cv2.CAP_PROP_FRAME_HEIGHT]])
ok,frame=capture.read();capture.release();assert ok
plt.figure(figsize=(12,7));plt.imshow(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));plt.axhline(300,color='orange');plt.title('Raw night street; image counting line y=300');plt.axis('off');save_plot(ROOT,8,'real_video_first_frame')
'''),md('''## 7. 对真实帧运行YOLOX
模型不读取人工框或源ID，不在本片段训练。实际CPU推理需要几分钟。可阅读detect内的预处理与后处理；不要用已有结果文件冒充本次推理。'''),code('''
from prepare_video_lesson import main as prepare_video_assets
if not (ROOT/'outputs/video-models/yolox.onnx').exists():prepare_video_assets()
detected=detect(ROOT/'outputs/video-models/yolox.onnx')
print('Actual inferred frames:',len(detected['frames']))
'''),md('''## 8. 独立标注核验、关联与事件评价
此时读取人工框与ID，仅用于评价。阅读evaluate中的位置归一化、卡尔曼关联、IoU匹配和事件身份匹配。两个固定阈值都报告，不能只留下更好的一组。'''),code('''
annotations=load_annotations()
video_result=evaluate(detected,annotations)
video_scores=pd.DataFrame([{'threshold':threshold,**r['metrics']} for threshold,r in video_result['runs'].items()])
display(video_scores)
display(pd.DataFrame([[threshold,*r] for threshold,run in video_result['runs'].items() for r in run['directions']],columns=['threshold','image_direction','reference_events','model_events','bias']))
'''),md('''## 9. 导出并逐条回看，不将总数接近当准确
results.json独立于SinD主JSON。review.csv是待核查清单，不是已完成的人工记录。请回看至少一处漏检、错接或事件不匹配，再填写交通调查解释。'''),code('''
export(video_result,ROOT/'outputs/ch08-video')
for threshold,run in video_result['runs'].items():
    missed=[video_result['reference_events'][i] for i in run['missed_reference']]
    print('Threshold / missed annotation-derived events:',threshold,missed[:5])
''')]
NOTEBOOKS[8]=n


def main():
    index={}
    for chapter,cells in NOTEBOOKS.items():
        key=f'ch{chapter:02}'
        for i,cell in enumerate(cells):
            cell['id']=f'{key}-{i:02}'
        notebook=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={
            'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
            'language_info':{'name':'python','version':'3.12'},
            'course_protocol':PROTOCOLS[key]['id']})
        content=json.dumps(notebook,ensure_ascii=False,indent=1)+'\n'
        path=ROOT/'chapters/notebooks'/f'{key}.ipynb'
        path.write_text(content,encoding='utf-8',newline='\n')
        index[key]={'path':f'chapters/notebooks/{key}.ipynb','protocol':PROTOCOLS[key]['id'],
                    'cells':len(cells),'code_cells':sum(c['cell_type']=='code' for c in cells),
                    'steps':[c['source'].splitlines()[0].removeprefix('## ') for c in cells if c['cell_type']=='markdown' and c['source'].startswith('## ')],
                    'sha256':hashlib.sha256(content.encode()).hexdigest()}
    (ROOT/'chapters/data/learning-notebooks.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print('Generated',len(NOTEBOOKS),'step-by-step notebooks;',sum(v['code_cells'] for v in index.values()),'executable code cells')


if __name__=='__main__':
    main()
