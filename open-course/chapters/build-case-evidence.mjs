import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {runComparison} from './comparisons.mjs';
import {bootstrap,parseCSV} from './engine.mjs';
import {forecast,counting,DEFAULTS,BOROUGHS} from '../projects/engine.mjs';

const root=new URL('../',import.meta.url),hashes={};
async function read(path){const bytes=await readFile(new URL(path,root));hashes[path]=createHash('sha256').update(bytes).digest('hex');return bytes.toString('utf8');}
const audit=JSON.parse(await read('projects/data/audit.json'));
const daily=JSON.parse(await read('chapters/data/ch03.json'));
const bike=JSON.parse(await read('chapters/data/ch04.json'));
const crashes=JSON.parse(await read('projects/data/crashes.json'));
const series=JSON.parse(await read('projects/data/forecast.json'));
const taxi=JSON.parse(await read('projects/data/taxi.json'));
const tracks=JSON.parse(await read('projects/data/sind.json'));
const clusters=parseCSV(await read('chapters/data/case-cluster-comparison.csv'));
const memberships=parseCSV(await read('chapters/data/case-day-clusters-4.csv'));
await read('chapters/data/case-cluster-centers-4.csv');
const sum=a=>a.reduce((s,v)=>s+v,0);
const table=(title,columns,rows,note='')=>({title,columns,rows,note});
const from=(title,r,limit)=>table(title,r.columns,limit?r.rows.slice(0,limit):r.rows,limit?`仅列前${Math.min(limit,r.rows.length)}行，共${r.rows.length}行；完整结果见配套专题。`:'全部对照行。');
const entry=(files,protocol,tables)=>({files,protocol,tables});
const counts=runComparison('taxi-denominator',taxi),priority=runComparison('hotspot-priority',crashes),duplicate=runComparison('duplicate-weight',audit);
const dates=new Set(audit.rows.map(r=>r[0]));
const missing=[];for(let i=0;i<365;i++){const date=new Date(Date.UTC(2017,0,1+i)).toISOString().slice(0,10),hours=['07','08','09'].filter(h=>!dates.has(`${date}T${h}:00`));if(hours.length)missing.push([date,hours.join('、'),hours.length]);}
const groupRows=['all','weekday','weekend'].map((group,i)=>{const r=bootstrap(daily.rows,{n:60,repetitions:1000,seed:42,group});return [['全部日期','平日','周末'][i],r.available_days,r.observed_reference,r.estimate,r.lower,r.upper];});
const auditRows=[...new Set(crashes.rows.map(r=>r[2]))].sort().map(b=>{const rows=crashes.rows.filter(r=>r[2]===b),valid=rows.filter(r=>r[7]).length;return [b,rows.length,valid,rows.length-valid,100*(rows.length-valid)/rows.length];});
const model=runComparison('bike-models',bike),strides=runComparison('count-stride',tracks),bands=runComparison('count-band',tracks);
const groups=[0,1,2,3].map(k=>{const rows=memberships.rows.filter(r=>Number(r[3])===k),totals=rows.map(r=>Number(r[2]));return [k,rows.length,Math.min(...totals),Math.max(...totals),sum(totals)/totals.length,rows.map(r=>r[0].slice(5)).join('、')];});
const auditFile=['projects/data/audit.json'],dailyFiles=[...auditFile,'chapters/data/ch03.json'],crashFile=['projects/data/crashes.json'],bikeFile=['chapters/data/ch04.json'],taxiFile=['projects/data/taxi.json'],trackFile=['projects/data/sind.json'],forecastFile=['projects/data/forecast.json'];
const mean=a=>a.length?sum(a)/a.length:null;
const errors=(rows,actual,predicted)=>{const d=rows.map(r=>r[predicted]-r[actual]);return [mean(d.map(Math.abs)),Math.sqrt(mean(d.map(v=>v*v))),mean(d)];};
const weekday=date=>![0,6].includes(new Date(date+'T12:00:00Z').getUTCDay());
const taxiRegions=Object.entries(BOROUGHS).map(([key,label])=>{const rows=taxi.rows.filter(r=>r[1]===key),total=sum(rows.map(r=>r[3])),night=sum(rows.filter(r=>r[2]>=22||r[2]<6).map(r=>r[3]));return [label,total,total/31,night,total?100*night/total:null];});
const taxiPeriods=[['早间07—09时',[7,8,9]],['日间10—15时',[10,11,12,13,14,15]],['傍晚16—18时',[16,17,18]],['夜间22—05时',[22,23,0,1,2,3,4,5]]].map(([label,hours])=>{const rows=taxi.rows.filter(r=>r[1]==='Queens'&&hours.includes(r[2])),a=sum(rows.filter(r=>weekday(r[0])).map(r=>r[3]))/23,b=sum(rows.filter(r=>!weekday(r[0])).map(r=>r[3]))/8;return [label,hours.length,a,b,b?100*(a/b-1):null];});
const bikePeriods=[['07—09时',[7,8,9]],['16—18时',[16,17,18]],['其他时段',Array.from({length:24},(_,h)=>h).filter(h=>![7,8,9,16,17,18].includes(h))]].flatMap(([label,hours])=>{const rows=bike.rows.filter(r=>hours.includes(r[2]));return [['岭回归',5],['泊松回归',6]].map(([name,index])=>[label,name,rows.length,mean(rows.map(r=>r[3])),...errors(rows,3,index),100*sum(rows.filter(r=>r[index]<r[3]).map(r=>r[3]-r[index]))/sum(rows.map(r=>r[3]))]);});
const forecastPeriods=['peak','offpeak'].flatMap(period=>{const r=forecast(series,{horizon:'1',model:'ridge',month:'all',period});return r.rows.filter(row=>[r.rows[3][0],r.rows[4][0]].includes(row[0])).map(row=>[period==='peak'?'07—09、16—18时':'其他时段',...row]);});
const eventRows=counting(tracks,DEFAULTS.counting).rows;
const directionBins=Array.from({length:4},(_,i)=>{const rows=eventRows.filter(r=>r[1]>=30*i&&(i===3?r[1]<=120:r[1]<30*(i+1)));return [`${i*30}—${(i+1)*30}秒`,rows.filter(r=>r[2]==='+x').length,rows.filter(r=>r[2]==='-x').length,rows.length];});
export const evidence={
 'records-demand':entry(taxiFile,'2024年1月；先比较Queens平日/周末全天日均，再汇总全部地区规模与夜间活动；日均使用完整日历日期分母。',[from('皇后区已发生上车活动',counts)]),
 'problem-metric':entry(crashFile,'全部行政区；固定500米网格；次数/伤者各取前10；固定并列规则。',[table('两份候选名单的一致程度',['共同入选格','并集格','交并比（%）'],[[priority.metrics['共同入选网格'],priority.metrics['名单并集'],priority.metrics['Jaccard交并比（%）']]]),from('候选并集摘录',priority,6)]),
 'duplicate-hours':entry(auditFile,'2017年；同钟点跨日期比较；按绝对均值偏移排序，仅显示最大5组。',[table('原文件规模核查',['原始行','不同小时','重复行','冲突小时'],[[audit.meta.rawRows,audit.meta.hours,audit.meta.duplicateRows,audit.meta.conflictingHours]]),table('均值偏移最大的钟点',duplicate.columns,[...duplicate.rows].sort((a,b)=>Math.abs(b[5])-Math.abs(a[5])).slice(0,5),'单位为辆/小时；偏移=原始行加权均值减小时等权均值。')]),
 'missing-time':entry(dailyFiles,'2017年；每天07、08、09时必须齐全；按本地标签对齐，不恢复夏令时。',[table('被排除的早高峰日期',['日期','缺失钟点','缺失小时数'],missing),table('样本覆盖',['日历日期','完整日期','排除日期','排除比例（%）'],[[365,daily.rows.length,missing.length,100*missing.length/365]])]),
 'sample-size':entry(dailyFiles,'全部完整日期；种子42；1000次百分位Bootstrap；20/60/90天嵌套抽样。',[from('同种子的样本量对照',runComparison('sample-size',daily))]),
 'daily-blocks':entry(dailyFiles,'各日期总体独立抽60天；种子42；1000次日级Bootstrap；平日未剔除节假日。',[table('不同日期总体对应不同目标',['日期总体','可用日期数','观测参考均值','60天样本均值','区间下限','区间上限'],groupRows,'三个总体不是三种模型；全部值的单位均为辆/小时。')]),
 'bike-leakage':entry(bikeFile,'标签分量从特征中排除；所有模型按2011/2012上半年/2012下半年切分，参数仅在验证集选择。',[from('合法特征下的冻结模型结果',model)]),
 'poisson-ridge':entry(bikeFile,'4,376个共同测试ID；先评价全天，再按钟点与指定观察窗分组；训练/验证协议固定；浏览器不重新训练。',[from('三模型误差',model),from('岭回归MAE最高的小时',{...runComparison('bike-hour-errors',bike),rows:runComparison('bike-hour-errors',bike).rows.sort((a,b)=>b[3]-a[3])},3)]),
 'grid-size':entry(crashFile,'7,068个有效坐标；固定原点；全部行政区；250/500/1000米；按事故次数排序。',[from('相同点集的尺度敏感性',runComparison('grid-scale',crashes))]),
 'no-coordinates':entry(crashFile,'按行政区分别计算记录总数、坐标有效数、排除数；UNKNOWN不直接当作坐标缺失。',[table('坐标覆盖审计',['行政区','总记录','有效坐标','排除记录','组内排除率（%）'],auditRows),table('总体覆盖',['总记录','有效坐标','排除记录','排除率（%）'],[[crashes.rows.length,crashes.meta.validCoordinates,crashes.rows.length-crashes.meta.validCoordinates,100*(crashes.rows.length-crashes.meta.validCoordinates)/crashes.rows.length]])]),
 'simple-baseline':entry(forecastFile,'1小时任务；全部2,190个共同目标时刻；2018年7至9月；各方法信息不得越过起点。',[from('同样本基线与岭回归',forecast(series,{horizon:'1',model:'ridge',month:'all',period:'all'}))]),
 'forecast-origin':entry(forecastFile,'1/3/6小时任务目标时间交集；岭回归；每跨度独立训练；不更改1小时提交接口。',[from('2,169个共同目标时刻的跨度对照',runComparison('forecast-horizon',series))]),
 'weekday-denominator':entry(taxiFile,'Queens；2024年1月；全部小时；平日23天、周末8天。',[from('累计量与典型日期不能混读',counts)]),
 'similar-days':entry([...taxiFile,'chapters/data/case-cluster-comparison.csv','chapters/data/case-day-clusters-4.csv','chapters/data/case-cluster-centers-4.csv'],'重新执行现有projects/python/extensions.py --project taxi；scikit-learn 1.9.1；31×168日内占比；random_state=42；n_init=10。',[table('类别数与样本内轮廓系数',['类别数K','样本内轮廓系数'],clusters.rows.map(r=>r.map(Number)),'越高表示当前距离定义下样本内分离较好，不是预测准确率。'),table('K=4时的日期组成与原始规模',['簇标签','日期数','最小日总量','最大日总量','平均日总量','日期（月-日）'],groups,'簇标签无顺序；原始总量单位为上车记录条数。')]),
 'crossing-rule':entry(trackFile,'前120秒；x=15米；双向；最大间隔1.5秒。采样对照固定0.3米死区，死区对照固定每1帧。',[from('采样规则与匹配事件时间',strides),from('死区变化与事件集合',bands)]),
 'trajectory-not-video':entry(trackFile,'数据条件核查，不是完整视觉系统性能测试；未提供视频、逐帧框标注或独立计数真值。',[table('当前材料能支持的评价',['材料或评价层','现有条件','可以报告'],[['平滑轨迹',`${tracks.rows.length}点，${new Set(tracks.rows.map(r=>r[0])).size}个ID，前120秒`,'给定轨迹下的规则输出'],['目标检测','无当前课程检测器输出与逐帧真值','不报告检测平均精度等数值'],['跨帧跟踪','没有独立预测轨迹与身份真值对照','不报告独立跟踪性能'],['交通事件','有规则输出，无独立完整人工事件真值','报告参数敏感性，不报告准确率']])])
};
evidence['records-demand'].tables.push(table('各地区已实现出租车服务与夜间活动',['地区','全月上车记录（条）','日均记录（条/日）','夜间记录（条）','夜间占比（%）'],taxiRegions,'夜间按每日22—05钟点筛选；EWR为机场类别，Unknown为未匹配地区，不等同于行政区。'));
evidence['sample-size'].tables.push(table('调查精度与观测工作量',['调查天数','区间半宽（辆/小时）','相对样本均值半宽（%）'],[20,60,90].map(n=>{const r=bootstrap(daily.rows,{n,repetitions:1000,seed:42,group:'all'});return [n,(r.upper-r.lower)/2,100*(r.upper-r.lower)/2/r.estimate];}),'用于比较当前抽样方案；不是交通调查规范规定的精度或最小天数。'));
for(const id of ['bike-leakage','poisson-ridge'])evidence[id].tables.push(table('通勤相关时段的租借量估计与低估诊断',['时段','模型','小时样本数','实测均值（次/小时）','MAE（次/小时）','RMSE（次/小时）','偏差（次/小时）','未抵消低估量占比（%）'],bikePeriods,'07—09、16—18时为教学观察时段，不表示数据已标注出行目的；最后一列为Σmax(实测−估计,0)/Σ实测，不是缺车率，也不是需要补投的车辆比例。'));
evidence['simple-baseline'].tables.push(table('道路运行关注时段的预测表现',['时段','方法','样本数','MAE（辆/小时）','RMSE（辆/小时）','偏差（辆/小时）'],forecastPeriods,'高峰观察窗预先固定为07—09、16—18时；这里只比较断面交通量误差，不评价拥堵、延误或控制收益。'));
evidence['weekday-denominator'].tables.push(table('皇后区分时服务活动及日期差异',['小时组','每日期包含小时数','平日日均（条/日）','周末日均（条/日）','平日相对周末差异（%）'],taxiPeriods,'每行是对应时段的日均合计；不比较不同时长时段的平均小时强度。用于同一行内比较日期类型。'));
evidence['crossing-rule'].tables.push(table('虚拟检测线分方向、分时段通行事件',['观测窗口','+x事件（次）','−x事件（次）','合计（次）'],directionBins,'左闭右开，最后一段包含120秒端点。正负方向为地面坐标方向，不擅自对应东西向、进口道或转向；30秒不是信号周期。'));
const text='// Generated by chapters/build-case-evidence.mjs. Do not edit numeric results by hand.\nexport const CASE_EVIDENCE = '+JSON.stringify(evidence,null,2)+';\nexport const CASE_EVIDENCE_META = '+JSON.stringify({edition:'2026-09-15',sourceBaseCommit:'23ed671925d731d7510d68fd78228f1bc2738dc0',files:hashes},null,2)+';\n';
await writeFile(new URL('data/case-evidence.js',import.meta.url),text,'utf8');
console.log(`Built evidence for ${Object.keys(evidence).length} cases; ${Object.keys(hashes).length} source files hashed.`);
