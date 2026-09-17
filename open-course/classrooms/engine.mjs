import {bootstrap,avg,errors} from '../chapters/engine.mjs';
import {hotspots,counting,DEFAULTS} from '../projects/engine.mjs';
import {EXPERIMENTS,defaultsFor,runComparison} from '../chapters/comparisons.mjs';
export const INPUTS={3:{daily:'chapters/data/ch03.json'},4:{algorithm:'chapters/data/algorithms/ch4.json'},5:{crashes:'projects/data/crashes.json',algorithm:'chapters/data/algorithms/ch5.json'},6:{audit:'projects/data/audit.json',forecast:'projects/data/forecast.json',algorithm:'chapters/data/algorithms/ch6.json'},7:{taxi:'projects/data/taxi.json',algorithm:'chapters/data/algorithms/ch7.json'},8:{sind:'projects/data/sind.json',algorithm:'chapters/data/algorithms/ch8.json'}};
const choice=(key,label,options,value)=>({key,label,options:options.map(x=>Array.isArray(x)?x:[String(x),String(x)]),value:String(value??(Array.isArray(options[0])?options[0][0]:options[0]))});
const number=(key,label,min,max,value,step=1)=>({key,label,min,max,value:String(value),step});
const period=choice('period','评价时段',[['all','全天'],['morning','07—09时'],['evening','16—18时'],['night','22—05时']]);
const forecastModel=choice('model','预测方法',[['ARIMA','ARIMA'],['SARIMA','SARIMA'],['week','上周同期'],['calendar','星期小时均值']],'SARIMA');
const region=choice('region','区域',[['all','四区域'],['Manhattan','曼哈顿'],['Brooklyn','布鲁克林'],['Queens','皇后区'],['Bronx','布朗克斯']]);
const custom={
 'daily-change':[],gradient:[number('eta','学习率',0.01,1.2,0.15,.01),number('steps','迭代次数',1,50,15),number('initial','初始估计（辆/小时）',0,10000,0)],
 'day-distribution':[],conditional:[number('threshold','均值阈值（辆/小时）',0,8000,5000,100)],
 'bike-models':[period],'bike-errors':[choice('model','模型',['OLS','Poisson','NB2'],'NB2')],'bike-under':[period],dispersion:[number('alpha','NB2离散系数α',0,1,.05,.05)],
 'coordinate-quality':[],kde:[choice('bandwidth','带宽（米）',[250,500,1000],500)],dbscan:[choice('eps','邻域半径（米）',[150,350,700],350),choice('minimum','邻域最低点数',[5,15],5)],
 'hour-profile':[],'lag-correlation':[choice('lag','最大滞后（小时）',[48,168],48)],origin:[choice('horizon','提前小时',[1,3,6],3)],
 'forecast-models':[choice('horizon','提前小时',[1,3,6],1),period],'forecast-horizons':[forecastModel,period],
 dtw:[number('dayA','2017年1月日期A',1,31,3),number('dayB','2017年1月日期B',1,31,7),choice('window','最大允许错位（小时）',[0,1,3,6],3),choice('scale','曲线尺度',[['raw','原始交通量'],['standard','分别标准化']])],
 'regional-models':[region],clusters:[choice('k','日型数量K',[2,3,4,5],3),choice('seed','随机种子',[42,7,19],42)],'cluster-stability':[choice('k','日型数量K',[2,3,4,5],3)],
 association:[choice('stride','采样步长（帧）',[1,5,10],5)],crossing:[number('line','计数线x（米）',-20,55,15),choice('band','单侧死区（米）',[0,.3,1,2],.3),choice('stride','采样步长（帧）',[1,5,10],1)]
};
export function controls(id){return custom[id]||EXPERIMENTS.find(e=>e.id===id)?.controls||[];}
export function defaults(id){return Object.fromEntries(controls(id).map(c=>[c.key,String(c.value)]));}
function validate(id,c){for(const f of controls(id)){const v=c[f.key];if(f.options?!f.options.some(o=>String(Array.isArray(o)?o[0]:o)===String(v)):String(v).trim()===''||!Number.isFinite(+v)||+v<f.min||+v>f.max||(f.step===1&&!Number.isInteger(+v)))throw Error('参数不在允许范围：'+f.label);}}
const sum=a=>a.reduce((s,v)=>s+v,0);
const series=(name,values)=>({name,values});
const plot=(type,unit,labels,sets)=>({type,unit,labels,series:sets});
const out=(columns,rows,chart,note,compute='根据真实观测在浏览器重新计算')=>({columns,rows,chart,note,compute});
const inPeriod=(h,p)=>p==='all'||p==='morning'&&h>=7&&h<=9||p==='evening'&&h>=16&&h<=18||p==='night'&&(h>=22||h<6);
const errorRow=(name,y,p)=>{const e=errors(y,p);return [name,e.样本数,e.MAE,e.RMSE,e.平均预测偏差];};
const errorOutput=(rows,unit,note)=>out(['方法','样本数',`MAE（${unit}）`,`RMSE（${unit}）`,`预测减实测（${unit}）`],rows,plot('bars',`误差（${unit}）`,rows.map(r=>r[0]),[series('MAE',rows.map(r=>r[2])),series('RMSE',rows.map(r=>r[3]))]),note,'根据冻结预测重新计算；不在浏览器拟合模型');
export function forecastRows(D,model,h){
 const d=D.algorithm.details;
 if(model==='ARIMA'||model==='SARIMA')return d.predictions[Object.keys(d.predictions).find(k=>k.startsWith(model+'('))][h];
 const m=new Map(D.forecast.horizons[h].rows.map(r=>[r[0],r[model==='week'?4:5]]));
 const values=d.targets.map(t=>m.get(t));if(values.some(v=>!Number.isFinite(v)))throw Error('共同目标未能匹配周期基线');return values;
}
export function runLab(id,D,input={}){
 const c={...defaults(id),...input};validate(id,c);
 if(!Object.hasOwn(custom,id)&&EXPERIMENTS.some(e=>e.id===id)){
  const data=D.daily||D.crashes||D.taxi||D.sind;
  return {...runComparison(id,data,c),compute:'根据真实观测在浏览器重新计算'};
 }
 if(id==='daily-change'){
  const a=D.daily.rows.slice(0,31),rows=a.slice(1).map((r,i)=>{const days=(Date.parse(r.date)-Date.parse(a[i].date))/86400000;return [r.date,days,(r.peak_mean-a[i].peak_mean)/days];});
  return out(['日期','距前个有效日期（天）','平均变化率（辆/小时/天）'],rows,plot('line','日际变化率（辆/小时/天）',rows.map(r=>r[0].slice(5)),[series('相邻有效日差分',rows.map(r=>r[2]))]),'仅展示抽样框前31个有效日期的日际变化。跨日缺口按实际日期间隔换算；不代表连续时间导数。');
 }
 if(id==='gradient'){
  const y=D.daily.rows.map(r=>r.peak_mean),m=avg(y);let theta=+c.initial;const rows=[];
  for(let i=0;i<=+c.steps;i++){rows.push([i,theta,avg(y.map(v=>(v-theta)**2))]);theta-=+c.eta*2*(theta-m);}
  return out(['迭代','常数估计（辆/小时）','均方误差（辆/小时）²'],rows,plot('line','常数估计（辆/小时）',rows.map(r=>String(r[0])),[series('梯度下降估计',rows.map(r=>r[1])),series('完整日期参考均值',rows.map(()=>m))]),'直接拟合全部358个完整日期，用于解释优化过程，无留出测试。常数模型不解释交通变化原因。', '在真实交通量上执行常数最小二乘梯度下降');
 }
 if(id==='day-distribution'||id==='conditional'){
  const rows=['weekday','weekend'].map(g=>{const a=D.daily.rows.filter(r=>r.day_type===g).map(r=>r.peak_mean),m=avg(a);return id==='conditional'?[g==='weekday'?'周一至周五':'周六、周日',a.length,a.filter(v=>v>+c.threshold).length,a.filter(v=>v>+c.threshold).length/a.length*100]:[g==='weekday'?'周一至周五':'周六、周日',a.length,m,Math.sqrt(sum(a.map(v=>(v-m)**2))/(a.length-1))];});
  return out(id==='conditional'?['日期组','完整日期','超过阈值日期','经验比例（%）']:['日期组','完整日期','均值（辆/小时）','样本标准差（辆/小时）'],rows,plot('bars',id==='conditional'?'超过阈值比例（%）':'平均交通量（辆/小时）',rows.map(r=>r[0]),[series(id==='conditional'?'经验条件比例':'日期均值',rows.map(r=>r[id==='conditional'?3:2]))]),'只描述完整日期文件，不剔除节假日。高交通量阈值不是拥堵标准。');
 }
 if(id.startsWith('bike-')){
  const a=D.algorithm.details.test_rows, names=D.algorithm.details.prediction_names;
  if(id==='bike-errors'){
   const j=names.indexOf(c.model)+4,rows=Array.from({length:24},(_,h)=>{const s=a.filter(r=>r[2]===h),e=errors(s.map(r=>r[3]),s.map(r=>r[j]));return [h,s.length,e.MAE,e.RMSE,e.平均预测偏差];});
   return out(['钟点','小时数','MAE（次/小时）','RMSE（次/小时）','预测减实测（次/小时）'],rows,plot('line','误差（次/小时）',rows.map(r=>r[0]+'时'),[series('MAE',rows.map(r=>r[2])),series('平均偏差',rows.map(r=>r[4]))]),'按钟点重算全部测试期误差。正负偏差可能抵消，不意味着逐小时准确。','冻结预测分组评价');
  }
  const a0=a.filter(r=>inPeriod(r[2],c.period));
  if(id==='bike-under'){
   const rows=names.map((name,i)=>[name,a0.length,sum(a0.map(r=>Math.max(r[3]-r[i+4],0))),a0.filter(r=>r[i+4]<r[3]).length]);
   return out(['方法','小时数','未抵消低估累计（次）','低估小时数'],rows,plot('bars','累计低估（次）',names,[series('未抵消低估量',rows.map(r=>r[2]))]),'仅在被评价小时上累计模型低估。不是缺车数量、流失订单或潜在需求。','冻结预测误差重新汇总');
  }
  return errorOutput(names.map((n,i)=>errorRow(n,a0.map(r=>r[3]),a0.map(r=>r[i+4]))),'次/小时','4376个公开测试小时按所选时段筛选。主协议OLS/Poisson/NB2，不混用旧模型。');
 }
 if(id==='dispersion'){
  const mu=[10,50,100,200,500],rows=mu.map(v=>[v,v,v+(+c.alpha)*v*v]);
  return out(['条件均值','泊松方差','NB2方差'],rows,plot('line','条件方差（次数²）',mu.map(String),[series('Poisson',mu),series('NB2',rows.map(r=>r[2]))]),'这些均值为明确指定的数学演示输入，不是真实新观测。改变α只展示方差关系，未重新训练模型。','公式关系演示，非观测结果');
 }
 if(id==='coordinate-quality'){
  const groups=[...new Set(D.crashes.rows.map(r=>r[2]))].sort(),rows=groups.map(g=>{const a=D.crashes.rows.filter(r=>r[2]===g),n=a.filter(r=>r[7]).length;return [g||'未记录',a.length,n,a.length-n,n/a.length*100];});
  return out(['行政区','事故记录','有效位置','坐标排除','位置覆盖（%）'],rows,plot('bars','记录数',rows.map(r=>r[0]),[series('有效位置',rows.map(r=>r[2])),series('坐标排除',rows.map(r=>r[3]))]),'坐标排除不等于事故不存在。未知行政区记录也可能具有可用位置。');
 }
 if(id==='kde'){
  const d=D.algorithm.details,h=+c.bandwidth,den=2*Math.PI*h*h*d.xy_m.length;
  const all=d.cells.map(([col,row],i)=>{const x=(col+.5)*500,y=(row+.5)*500;let z=0;for(const [a,b] of d.xy_m)z+=Math.exp(-((x-a)**2+(y-b)**2)/(2*h*h));return [col+':'+row,x/1000,y/1000,z/den*1e6,i];});
  const top=all.slice().sort((a,b)=>b[3]-a[3]||a[4]-b[4]).slice(0,10);
  return {...out(['网格ID','东向km','北向km','密度1/km²'],top.map(r=>r.slice(0,4)),plot('bars','概率密度（1/km²）',top.map(r=>r[0]),[series('最高10处固定评价点',top.map(r=>r[3]))]),'7068有效点与2069固定500米网格中心。此处高斯KDE直接重新求和，不将概率密度解释为风险。'),map:all.map(r=>[r[1],r[2],r[3]]),mapLabel:'局部东向/北向（km），无路网底图',mapMode:'density'};
 }
 if(id==='dbscan'){
  const d=D.algorithm.details,labels=d.dbscan[`${c.eps}-${c.minimum}`],m=new Map();for(const l of labels)m.set(l,(m.get(l)||0)+1);
  const rows=[...m].sort((a,b)=>b[1]-a[1]).map(([k,v])=>[k===-1?'噪声':`簇${k}`,v]);
  return {...out(['类别','事故点数'],rows,plot('bars','事故点数',rows.slice(0,10).map(r=>r[0]),[series('最大10类（含噪声）',rows.slice(0,10).map(r=>r[1]))]),'切换既有Python DBSCAN标签并重新统计，不在浏览器重新拟合。噪声标签不是错误观测。','冻结DBSCAN结果浏览与统计'),map:d.xy_m.map(([x,y],i)=>[x/1000,y/1000,labels[i]]),mapMode:'cluster',mapLabel:'局部东向/北向（km），同一事故点集'};
 }
 if(id==='hour-profile'){
  const a=D.audit.rows.filter(r=>r[0].startsWith('2017'));
  const rows=Array.from({length:24},(_,h)=>[h,...[false,true].map(weekend=>avg(a.filter(r=>+r[0].slice(11,13)===h&&[0,6].includes(new Date(r[0].slice(0,10)+'T00:00Z').getUTCDay())===weekend).map(r=>r[1])))]);
  return out(['钟点','周一至周五均值','周末均值'],rows,plot('line','交通量（辆/小时）',rows.map(r=>r[0]+'时'),[series('周一至周五',rows.map(r=>r[1])),series('周末',rows.map(r=>r[2]))]),'2017训练段有效小时按组计算，无缺测填0，不把周一至周五自动视为剔除节假日的工作日。');
 }
 if(id==='lag-correlation'){
  const a=D.audit.rows.filter(r=>r[0].startsWith('2017')),m=new Map(a.map(r=>[Date.parse(r[0]+'Z'),r[1]])),rows=[];
  for(let k=1;k<=+c.lag;k++){const pairs=[];for(const [t,v] of m){const u=m.get(t-k*3600000);if(u!==undefined)pairs.push([v,u]);}const x=avg(pairs.map(r=>r[0])),y=avg(pairs.map(r=>r[1]));const r=sum(pairs.map(a=>(a[0]-x)*(a[1]-y)))/Math.sqrt(sum(pairs.map(a=>(a[0]-x)**2))*sum(pairs.map(a=>(a[1]-y)**2)));rows.push([k,pairs.length,r]);}
  return out(['滞后小时','有效观测对','成对Pearson相关'],rows,plot('line','相关系数',rows.map(r=>String(r[0])),[series('精确小时标签配对',rows.map(r=>r[2]))]),'每个滞后分别计算成对均值与相关，不等同于所有软件默认ACF。Z仅作本地标签运算轴，不恢复时区偏移。');
 }
 if(id==='origin'){
  const rows=D.algorithm.details.targets.slice(0,8).map(t=>[t,new Date(Date.parse(t+'Z')-(+c.horizon)*3600000).toISOString().slice(0,16),+c.horizon]);
  return out(['目标本地标签','最后可用小时标签','提前小时'],rows,null,'使用起点的过滤状态。Z只用于无时区干扰的标签减法，不代表源时间转成UTC。表仅展示共同目标的前8条。');
 }
 if(id.startsWith('forecast-')){
  const d=D.algorithm.details,indices=d.targets.map((t,i)=>i).filter(i=>inPeriod(+d.targets[i].slice(11,13),c.period));
  const variants=id==='forecast-horizons'?[1,3,6].map(h=>[c.model,String(h)]):['calendar','week','ARIMA','SARIMA'].map(m=>[m,String(c.horizon)]);
  const names={calendar:'星期小时均值',week:'上周同期',ARIMA:'ARIMA',SARIMA:'SARIMA'};
  const rows=variants.map(([m,h])=>{const prediction=forecastRows(D,m,h);return errorRow(id==='forecast-horizons'?`提前${h}小时`:names[m],indices.map(i=>d.actual[i]),indices.map(i=>prediction[i]));});
  return errorOutput(rows,'辆/小时','全年训练2017年；验证2018年上半年；测试7—9月。全部方案先固定2169共同目标，再筛选相同时段。不把图表切换称为重新训练。');
 }
 if(id==='dtw'){
  const day=n=>'2017-01-'+String(n).padStart(2,'0'),get=n=>{const a=D.audit.rows.filter(r=>r[0].startsWith(day(n)));if(a.length!==24)throw Error('所选日期不是24小时完整记录，请换日期。');const v=a.map(r=>r[1]);if(c.scale==='raw')return v;const m=avg(v),sd=Math.sqrt(avg(v.map(x=>(x-m)**2)));if(!sd)throw Error('常数曲线不能进行此标准化');return v.map(x=>(x-m)/sd);};
  const a=get(c.dayA),b=get(c.dayB),w=+c.window,m=Array.from({length:25},()=>Array(25).fill(Infinity));m[0][0]=0;
  for(let i=1;i<=24;i++)for(let j=Math.max(1,i-w);j<=Math.min(24,i+w);j++)m[i][j]=Math.abs(a[i-1]-b[j-1])+Math.min(m[i-1][j],m[i][j-1],m[i-1][j-1]);
  const unit=c.scale==='raw'?'辆/小时':'标准化值（无量纲）';
  return out(['钟点',day(c.dayA),day(c.dayB)],a.map((v,i)=>[i,v,b[i]]),plot('line',unit,a.map((_,i)=>i+'时'),[series(day(c.dayA),a),series(day(c.dayB),b)]),`DTW累计绝对代价=${m[24][24].toFixed(3)}，允许错位±${w}小时，未按路径长度归一化。代价取决于幅值尺度与路径约束，不是预测误差或显著性。`);
 }
 if(id==='regional-models'){
  const d=D.algorithm.details,cols=c.region==='all'?[0,1,2,3]:[d.nodes.indexOf(c.region)];
  const y=d.actual.flatMap(row=>cols.map(j=>row[j]));
  return errorOutput(Object.entries(d.predictions).map(([name,a])=>errorRow(name,y,a.flatMap(row=>cols.map(j=>row[j])))),'条/小时','训练1—21日，验证22—24日，测试25—31日。全体672区域小时，每个单独区域168小时。零组是本快照无保留记录。');
 }
 if(id==='clusters'){
  const d=D.algorithm.details,labels=d.memberships[`${c.k}-${c.seed}`],rows=labels.map((g,i)=>[`01-${String(i+1).padStart(2,'0')}`,g+1,d.profile_totals[i]]);
  return out(['日期','簇标签','原始日总量（条）'],rows,plot('bars','保留上车记录（日总量）',rows.map(r=>r[0]),[series('原始日总量',rows.map(r=>r[2]))]),'聚类使用31日×168维全日占比，不用上图总量拟合。表中查看成员并结合总量解释。簇编号可互换，不能直接比编号。','冻结KMeans成员与真实规模联合浏览');
 }
 if(id==='cluster-stability'){
  const t=D.algorithm.cases['similar-days'].tables[0],rows=t.rows.filter(r=>r[0]===+c.k);
  return out(t.columns,rows,plot('bars','ARI（相对种子42）',rows.map(r=>'种子'+r[1]),[series('ARI',rows.map(r=>r[3]))]),t.note,'读取已有Python轮廓系数与ARI计算结果，不重新拟合');
 }
 if(id==='association'){
  const t=D.algorithm.cases['crossing-rule'].tables,rows=t[0].rows.filter(r=>r[0]===+c.stride);
  return out(t[0].columns,rows,plot('bars','通行事件（次）',rows.map(r=>r[1]==='kalman'?'卡尔曼':'位置保持'),[series('同采样源ID事件',rows.map(r=>r[2])),series('新ID事件',rows.map(r=>r[3]))]),t[0].note+' 完整身份对核查见本章案例。','读取真实执行的匿名关联结果，未重新运行检测器');
 }
 if(id==='crossing'){
  const r=counting(D.sind,{...DEFAULTS.counting,...c});
  return {...out(r.columns,r.rows,plot('bars','通行事件（次）',['+x','−x'],[series('规则事件',[r.metrics['正方向事件'],r.metrics['负方向事件']])]),r.note),map:D.sind.rows.filter(r=>+r[0]<=3).map(r=>[r[2],r[3],+r[0]]),mapMode:'cluster',mapLabel:'源ID 1—3轨迹点，地面x/y（米），全部77源ID参与计数',line:+c.line};
 }
 throw Error('未知实验：'+id);
}
export function codeExample(chapter){
 const configs={3:['sample-size',{group:'all',seed:42}],4:['bike-models',{period:'morning'}],5:['grid-scale',{borough:'all'}],6:['forecast-models',{horizon:3,period:'morning'}],7:['regional-models',{region:'Queens'}],8:['crossing',{line:15,band:.3,stride:5}]};
 const [id,config]=configs[chapter];
 return `// JavaScript：本机实际执行，可修改参数。\n// data为本章真实快照；runLab为公开计算模块。\nconst result = runLab(${JSON.stringify(id)}, data, ${JSON.stringify(config,null,2)});\nprint(result.columns);\nprint(result.rows);\nprint(result.note);`;
}
