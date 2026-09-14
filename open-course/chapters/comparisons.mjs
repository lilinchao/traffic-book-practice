import {avg,bootstrap,errors} from './engine.mjs';
import {audit,hotspots,taxi,counting,DEFAULTS,MODEL_NAMES,BOROUGHS} from '../projects/engine.mjs';

const years={key:'year',label:'观测年份',options:['2013','2014','2015','2016','2017','2018'],value:'2017'};
const seed={key:'seed',label:'随机种子',min:0,max:4294967295,value:42};
const groups={key:'group',label:'日期总体',options:[['all','全部完整日期'],['weekday','周一至周五'],['weekend','周六、周日']],value:'all'};
const bikeModel={key:'model',label:'冻结模型',options:[['ridge','岭回归'],['poisson','泊松回归'],['mean','训练期均值']],value:'ridge'};
const forecastModel={key:'model',label:'冻结模型',options:Object.entries(MODEL_NAMES),value:'ridge'};
const borough={key:'borough',label:'行政区',options:[['all','全部'],['MANHATTAN','曼哈顿'],['BROOKLYN','布鲁克林'],['QUEENS','皇后区'],['BRONX','布朗克斯'],['STATEN ISLAND','斯塔滕岛']],value:'all'};
const line={key:'line',label:'计数线 x（米）',min:-20,max:55,value:15};
const gap={key:'gap',label:'最大连接间隔（秒）',options:['1.5','3','5'],value:'1.5'};
const spec=(id,chapter,title,question,change,fixed,observe,controls=[])=>({id,chapter,title,question,change,fixed,observe,controls});
export const EXPERIMENTS=[
 spec('duplicate-weight',2,'重复记录会把均值推向哪里？','同一个小时出现多行天气描述，能当作多次交通观测吗？','每个小时等权 / 按原始行数加权','相同年份、相同交通量观测；不删去真实高峰。','找到偏移最大的小时，解释重复权重为什么不等于更多车辆。',[years]),
 spec('missing-zero',2,'缺测填零，会制造怎样的趋势？','文件中没有这一小时，是否就代表没有车？','保留缺测 / 错误地把缺失时间标签填0','同一首末观测区间、同一组有效小时。','比较月均曲线与覆盖率；区分真实零交通量和没有记录。',[years]),
 spec('sample-size',3,'观察20天、60天、90天有何不同？','扩大样本后，区间一定会更窄吗？','抽样日期数20、60、90','相同日期总体、种子、1000次日级Bootstrap；较小样本嵌套在较大样本中。','比较区间宽度与估计值；不要把一次结果当作必然规律。',[groups,seed]),
 spec('sample-seeds',3,'换一批日期，结论稳不稳？','同样抽60天，换一批日期会怎样？','从起始种子连续取6个种子，重新抽样','相同日期总体、每次60天、1000次Bootstrap。','观察点估计和区间的位置；六次抽样不足以检验95%覆盖率。',[groups,seed]),
 spec('bootstrap-budget',3,'重采样更多次，等于采到更多数据吗？','增加计算次数，能否替代增加观测日期？','Bootstrap次数200、500、1000、2000','同一批60天、同一种子；只增加重采样次数。','点估计应完全相同，区间端点可能波动；计算稳定性不等于信息增加。',[groups,seed]),
 spec('bike-models',4,'三个模型在相同小时上比较','复杂模型是否在RMSE、MAE上都更好？','训练均值、岭回归、泊松回归','同一组公开练习测试ID；训练和验证协议不变，不重新调参。','分别读RMSE、MAE和有符号偏差，解释各指标回答的问题。',[{key:'period',label:'评价时段',options:[['all','全天'],['night','夜间22—05时'],['day','白天06—21时']],value:'all'}]),
 spec('bike-hour-errors',4,'总体误差会掩盖哪个小时？','全天表现尚可，是否意味着早晚高峰也可靠？','将冻结预测按0—23时分组','同一模型、同一公开测试期；分组不用于再训练。','找到MAE最高的小时，检查平均偏差是高估还是低估，并核对样本数。',[bikeModel]),
 spec('grid-scale',5,'网格越大，热点越集中吗？','250米和1000米网格选出的重点区域能直接等同吗？','网格边长250、500、1000米','同一批有效坐标、同一原点、按事故次数排序。','比较有记录网格数与前10网格覆盖率；尺度不同，面积和候选对象也不同。',[borough]),
 spec('hotspot-priority',5,'事故多与伤者多，是同一份清单吗？','有限排查名额应该优先看频次，还是伤者负担？','事故次数排序 / 伤者人数排序','500米网格、同一行政区、各取前10个网格；并列按网格坐标排序。','核对两份名单的交集及各网格的两类计数；两种排序都不是单位暴露风险。',[borough]),
 spec('forecast-horizon',6,'提前1、3、6小时预测有多大差别？','时间跨度变长，误差变化是否来自样本不同？','预测跨度1、3、6小时','先取三个跨度共同的目标时间，再比较同一模型家族；各跨度有独立训练参数。','比较误差，不要假设误差必然单调增加；检查共同样本数量。',[forecastModel]),
 spec('forecast-months',6,'一个季度的分数会掩盖月份变化吗？','模型在7月有效，8月和9月是否仍然有效？','7、8、9月的评价子集','1小时预测；所选模型和上周同期基线使用各月相同ID。','比较逐月MAE与偏差；样本量和季节变化同时存在，不能直接推断原因。',[forecastModel]),
 spec('taxi-denominator',7,'平日总量更大，就代表每天更忙吗？','23个平日和8个周末日能直接比较累计上车量吗？','累计量 / 除以各自日期数后的日均量','同一地区、2024年1月、全部小时；包括无保留记录的日历日。','同时读总量、日期数、日均和24小时曲线，解释分母的作用。',[{key:'borough',label:'地区',options:Object.entries(BOROUGHS),value:'Queens'}]),
 spec('taxi-profile',7,'规模与出行节律，如何分开看？','一个地区总量较小，是否仍可能有明显的晚高峰？','绝对上车量 / 各地区内部24小时占比','曼哈顿、皇后区、布鲁克林；同一日期类型；各地区独立归一化。','比较高峰小时和夜间份额，不把占比高误读成绝对上车量高。',[{key:'day',label:'日期类型',options:[['all','全部日期'],['weekday','平日'],['weekend','周末']],value:'all'}]),
 spec('count-stride',8,'少看几帧，会漏掉还是延后计数？','抽帧后的事件数相同，就代表结果没有变化吗？','每1、5、10个时间帧保留一次','同一计数线、双向、0.3米死区、相同连接间隔；相对密集采样规则比较。','同时检查事件集合和匹配事件的时间差；基准规则不是人工真值。',[line,gap]),
 spec('count-band',8,'死区防抖会不会改变触发时刻？','计数线附近的缓冲区越宽越好吗？','单侧死区宽度0、0.3、1、2米','保留全部帧、相同计数线、双向与最大连接间隔；以0米规则为对照。','检查事件数量、增减的ID和触发时差；没有独立真值，不判断哪组更准确。',[line,gap])
];
export const defaultsFor=e=>Object.fromEntries(e.controls.map(c=>[c.key,String(c.value)]));
const sum=a=>a.reduce((s,x)=>s+x,0);
const pct=(a,b)=>b?100*a/b:null;
const models={mean:['训练期均值',4],ridge:['岭回归',5],poisson:['泊松回归',6]};
const chart=(type,unit,labels,series)=>({type,unit,labels,series});
const s=(name,values)=>({name,values});
const result=(columns,rows,visual,note,metrics={})=>({columns,rows,chart:visual,note,metrics});
const intervals=items=>({type:'interval',unit:'交通量（辆/小时）；横线为95%百分位Bootstrap区间，圆点为样本均值',labels:items.map(x=>x[0]),points:items.map(([,r])=>({estimate:r.estimate,lower:r.lower,upper:r.upper})),reference:items[0][1].observed_reference});
function inference(id,data,c){
 const variants=id==='sample-size'?[20,60,90]:id==='sample-seeds'?Array.from({length:6},(_,i)=>(Number(c.seed)+i)>>>0):[200,500,1000,2000];
 const items=variants.map(v=>{const cfg={...c,n:60,repetitions:1000};if(id==='sample-size')cfg.n=v;else if(id==='sample-seeds')cfg.seed=v;else cfg.repetitions=v;return [id==='sample-size'?`${v}天`:id==='sample-seeds'?`种子${v}`:`${v}次`,bootstrap(data.rows,cfg)];});
 const rows=items.map(([label,r])=>[label,r.n_days,r.seed,r.repetitions,r.estimate,r.lower,r.upper,r.upper-r.lower]);
 return result(['方案','日期数','种子','重采样次数','估计均值','区间下限','区间上限','区间宽度'],rows,intervals(items),'虚线仅为所选文件中完整观测日期的参考均值，不是真实总体已知参数。日期近似独立是本方法的假设；相邻日期相关、缺失日期与选择偏差没有被Bootstrap自动解决。',{方案数:rows.length,观测日期参考均值:items[0][1].observed_reference});
}
function duplicate(data,c){
 const r=audit(data,{year:c.year,method:'unique'});
 const rows=r.rows.map(x=>[...x,x[4]-x[3]]),worst=rows.reduce((a,b)=>Math.abs(b[5])>Math.abs(a[5])?b:a);
 return result([...r.columns,'加权减去重（辆/小时）'],rows,chart('line','平均交通量（辆/小时）',r.labels,r.series),r.note,{重复行:r.metrics['重复行'],最大偏移小时:worst[0],最大绝对偏移:Math.abs(worst[5])});
}
function missing(data,c){
 const selected=data.rows.filter(r=>r[0].startsWith(c.year)),observed=new Map(),calendar=new Map();
 if(!selected.length)throw Error('所选年份没有记录。');
 for(const [t,v] of selected){const m=t.slice(0,7);if(!observed.has(m))observed.set(m,[]);observed.get(m).push(v);}
 // UTC arithmetic enumerates naive local labels, without reconstructing DST.
 for(let t=Date.parse(selected[0][0]+'Z'),end=Date.parse(selected.at(-1)[0]+'Z');t<=end;t+=3600000){const m=new Date(t).toISOString().slice(0,7);calendar.set(m,(calendar.get(m)||0)+1);}
 const rows=[...calendar].map(([m,expected])=>{const a=observed.get(m)||[];return [m,expected,a.length,expected-a.length,pct(a.length,expected),avg(a),sum(a)/expected];});
 return result(['月份','范围内时间标签数','有效小时','缺失标签','覆盖率（%）','观测均值','缺测误填0后的均值'],rows,chart('line','交通量（辆/小时）',rows.map(r=>r[0]),[s('仅有效观测',rows.map(r=>r[5])),s('缺测填0（错误示范）',rows.map(r=>r[6]))]),`只在${selected[0][0]}至${selected.at(-1)[0]}之间枚举本地时间标签，不恢复夏令时，首末月份可能不完整。没有观测的整月均值留空；填0曲线仅为错误处理的反事实演示，不写回原始数据，也不是推荐插补法。`,{有效小时:selected.length,缺失标签:sum(rows.map(r=>r[3]))});
}
function bikeComparison(id,data,c){
 if(id==='bike-models'){
  const a=data.rows.filter(r=>c.period==='all'||(c.period==='night'?(r[2]>=22||r[2]<6):(r[2]>=6&&r[2]<22)));
  const rows=Object.values(models).map(([name,index])=>[name,...Object.values(errors(a.map(r=>r[3]),a.map(r=>r[index])))]);
  return result(['模型','样本数','RMSE','MAE','平均预测偏差'],rows,chart('bars','误差（次/小时），越小越好',rows.map(r=>r[0]),[s('RMSE',rows.map(r=>r[2])),s('MAE',rows.map(r=>r[3]))]),'同一批测试ID逐行配对；预测来自Python中已训练的冻结模型，网页只重算误差。实测天气是条件回归输入，不等于未知未来天气时的预测。',{共同测试小时:a.length,模型数:3});
 }
 const [name,index]=models[c.model];
 const rows=Array.from({length:24},(_,h)=>{const a=data.rows.filter(r=>r[2]===h),e=errors(a.map(r=>r[3]),a.map(r=>r[index]));return [h,e.样本数,avg(a.map(r=>r[3])),e.MAE,e.RMSE,e.平均预测偏差];});
 const worst=rows.reduce((a,b)=>b[3]>a[3]?b:a);
 return result(['小时','样本数','实测均值','MAE','RMSE','平均预测偏差'],rows,chart('line','误差（次/小时）；偏差=预测减实测',rows.map(r=>`${r[0]}时`),[s('MAE',rows.map(r=>r[3])),s('有符号偏差',rows.map(r=>r[5]))]),`${name}的公开练习测试结果。小时子集不同，样本数和交通量级也可能不同；子组诊断不应被用于反复试探测试标签调参。`,{最大MAE小时:worst[0],该小时MAE:worst[3],该小时样本:worst[1]});
}
function spatial(id,data,c){
 if(id==='grid-scale'){
  const rows=[250,500,1000].map(cell=>{const r=hotspots(data,{...c,cell,weight:'count'}),top=r.rows.slice(0,10);return [cell,r.metrics['可落图记录'],r.rows.length,top.length,sum(top.map(r=>r[1])),pct(sum(top.map(r=>r[1])),r.metrics['可落图记录'])];});
  return result(['边长（米）','可落图事故','有记录网格','实际取前K格','前K格事故数','前K格覆盖率（%）'],rows,chart('bars','前K格事故覆盖率（%）',rows.map(r=>`${r[0]}米`),[s('覆盖率',rows.map(r=>r[5]))]),'K=min(10,有记录网格数)。同一个K不代表相同面积；不同尺度的网格ID不能直接求交集。仅报告事故记录集中程度，不是事故概率或暴露量校正风险。');
 }
 const a=hotspots(data,{...c,cell:500,weight:'count'}).rows,b=hotspots(data,{...c,cell:500,weight:'injured'}).rows;
 const topA=a.slice(0,10),topB=b.slice(0,10),rankA=new Map(a.map((r,i)=>[r[0],i+1])),rankB=new Map(b.map((r,i)=>[r[0],i+1])),byId=new Map(a.map(r=>[r[0],r]));
 const ids=[...new Set([...topA,...topB].map(r=>r[0]))],both=ids.filter(id=>rankA.get(id)<=10&&rankB.get(id)<=10).length;
 const rows=ids.map(id=>{const r=byId.get(id);return [id,r[1],r[2],rankA.get(id),rankB.get(id),rankA.get(id)<=10&&rankB.get(id)<=10?'两者均入选':rankA.get(id)<=10?'仅次数入选':'仅伤者入选'];});
 return result(['网格ID','事故次数','伤者人数','次数名次','伤者名次','名单归属'],rows,chart('bars','排序名次（数值越小越靠前）',ids,[s('次数名次',rows.map(r=>r[3])),s('伤者名次',rows.map(r=>r[4]))]),'只比较两份前10名单的并集。图中较短的柱代表更靠前的名次，并非计数更少。伤者人数来自事故报告；未加入交通暴露量、道路环境或报告完整性校正。',{共同入选网格:both,名单并集:ids.length,'Jaccard交并比（%）':pct(both,ids.length)});
}
function forecasting(id,data,c){
 const index=Object.keys(MODEL_NAMES).indexOf(c.model)+2;
 if(id==='forecast-horizon'){
  const keys=['1','3','6'],sets=keys.map(h=>new Map(data.horizons[h].rows.map(r=>[r[0],r]))),common=[...sets[0].keys()].filter(t=>sets.every(m=>m.has(t)));
  const rows=sets.map((m,i)=>{const a=common.map(t=>m.get(t)),e=errors(a.map(r=>r[1]),a.map(r=>r[index]));return [+keys[i],e.样本数,e.RMSE,e.MAE,e.平均预测偏差];});
  return result(['跨度（小时）','共同样本数','RMSE','MAE','平均预测偏差'],rows,chart('bars','预测误差（辆/小时）',keys.map(h=>`${h}小时`),[s('RMSE',rows.map(r=>r[2])),s('MAE',rows.map(r=>r[3]))]),'三个跨度严格对齐目标时间交集。每个跨度的模型在相同年份协议下独立训练，使用起报时刻已知的信息；网页不重新训练。前日/上周同期可能在不同跨度给出完全相同的预测，这是基线定义的结果，不伪造差异。',{共同目标时刻:common.length,原1小时样本:data.horizons['1'].rows.length});
 }
 const rows=['07','08','09'].map(month=>{const a=data.horizons['1'].rows.filter(r=>r[0].slice(5,7)===month),e=errors(a.map(r=>r[1]),a.map(r=>r[index])),b=errors(a.map(r=>r[1]),a.map(r=>r[4]));return [`${+month}月`,a.length,e.MAE,b.MAE,e.平均预测偏差,avg(a.map(r=>r[1]))];});
 return result(['月份','样本数','所选模型MAE','上周同期MAE','所选模型偏差','实测均值'],rows,chart('bars','MAE（辆/小时）',rows.map(r=>r[0]),[s(MODEL_NAMES[c.model],rows.map(r=>r[2])),s('上周同期基线',rows.map(r=>r[3]))]),'每月内部按相同测试ID比较；三个月份的观测不同，不能把差异全部归因于概念漂移。所选模型若就是上周同期，两组结果应相同。');
}
function mobility(id,data,c){
 const names=Object.keys(BOROUGHS);
 if(id==='taxi-denominator'){
  const i=names.indexOf(c.borough),runs=['weekday','weekend'].map(day=>taxi(data,{day,period:'all',normalize:'daily'}));
  const rows=runs.map((r,j)=>{const total=sum(r.exportRows.filter(x=>x[0]===BOROUGHS[c.borough]).map(x=>x[2]));return [j?'周末':'平日',r.metrics['日期数'],total,total/r.metrics['日期数']];});
  return result(['日期类型','日历日期数','累计上车记录','日均上车记录'],rows,chart('line','每日日均该小时上车记录（条）',Array.from({length:24},(_,h)=>`${h}时`),runs.map((r,j)=>s(j?'周末（8天）':'平日（23天）',r.matrix[i]))),'平日指周一至周五，不剔除节假日。日均按全部所选日历日期计算。零组仅表示本快照无保留记录，上车量不等于全部交通需求。');
 }
 const r=taxi(data,{day:c.day,period:'all',normalize:'total'}),chosen=['Manhattan','Queens','Brooklyn'],profiles=chosen.map(b=>{const a=r.matrix[names.indexOf(b)],total=sum(a);return {b,a,total,share:a.map(x=>pct(x,total))};});
 const rows=profiles.flatMap(({b,a,total,share})=>a.map((v,h)=>[BOROUGHS[b],h,v,share[h],total]));
 return result(['地区','小时','累计上车记录','地区内小时占比（%）','地区全天总量'],rows,chart('line','各地区内部小时占比（%）',Array.from({length:24},(_,h)=>`${h}时`),profiles.map(p=>s(BOROUGHS[p.b],p.share))),'每条曲线的24小时占比之和为100%；它描述节律而非规模。原始计数同时列在表中，零总量时占比留空。空间单元是行政区，不是单个站点或个人轨迹。');
}
const eventKey=r=>`${r[0]}:${r[2]}`;
function trajectories(id,data,c){
 const values=id==='count-stride'?[1,5,10]:[0,.3,1,2],key=id==='count-stride'?'stride':'band';
 const runs=values.map(value=>counting(data,{...DEFAULTS.counting,...c,[key]:value}));
 const baseline=new Map(runs[0].rows.map(r=>[eventKey(r),r])),details=[];
 const rows=runs.map((r,i)=>{
  const events=new Map(r.rows.map(e=>[eventKey(e),e])),matched=r.rows.filter(e=>baseline.has(eventKey(e))),missing=[...baseline.keys()].filter(k=>!events.has(k)),added=[...events.keys()].filter(k=>!baseline.has(k));
  const differences=matched.map(e=>e[1]-baseline.get(eventKey(e))[1]);
  for(const k of new Set([...baseline.keys(),...events.keys()])){const a=baseline.get(k),b=events.get(k);details.push([values[i],(a||b)[0],(a||b)[2],a?.[1]??null,b?.[1]??null,a&&b?b[1]-a[1]:null,a&&b?'共同事件':a?'相对基准未触发':'相对基准新增']);}
  return [values[i],r.rows.length,matched.length,missing.length,added.length,avg(differences),differences.length?Math.max(...differences.map(Math.abs)):null,r.metrics['采样后轨迹点']];
 });
 const out=result([key==='stride'?'采样帧间隔':'单侧死区（米）','事件数','匹配事件','相对未触发','相对新增','匹配平均时差（秒）','最大绝对时差（秒）','保留轨迹点'],rows,chart('bars','跨线事件数（非准确率）',values.map(v=>key==='stride'?`每${v}帧`:`${v}米`),[s('事件数',rows.map(r=>r[1]))]),'基准为本表第一组规则，不是人工真值。按轨迹ID和方向匹配；时差=当前触发时刻减基准触发时刻。没有匹配事件时，时差留空。数量相同也应核对事件集合和时差。SinD已平滑轨迹不用于证明原始视频检测性能。',{基准事件:baseline.size,规则组数:values.length});
 out.detail={columns:['规则值','轨迹ID','方向','基准触发秒','当前触发秒','当前减基准（秒）','状态'],rows:details};return out;
}
export function runComparison(id,data,input={}){
 const e=EXPERIMENTS.find(x=>x.id===id);if(!e)throw Error('未知对照实验。');
 const c={...defaultsFor(e),...input};
 for(const field of e.controls){const value=c[field.key];if(field.options){if(!field.options.some(o=>String(Array.isArray(o)?o[0]:o)===String(value)))throw Error('无效选项：'+field.label);}else if(String(value).trim()===''||!Number.isInteger(Number(value))||Number(value)<field.min||Number(value)>field.max)throw Error('检查范围：'+field.label);}
 if(!data||!Array.isArray(data.rows)&&!data.horizons)throw Error('缺少真实数据快照。');
 const r=id==='duplicate-weight'?duplicate(data,c):id==='missing-zero'?missing(data,c):e.chapter===3?inference(id,data,c):e.chapter===4?bikeComparison(id,data,c):e.chapter===5?spatial(id,data,c):e.chapter===6?forecasting(id,data,c):e.chapter===7?mobility(id,data,c):trajectories(id,data,c);
 return {...r,id,title:e.title,config:c,protocol:{change:e.change,fixed:e.fixed},source:data.meta,metrics:{对照行数:r.rows.length,...r.metrics}};
}
