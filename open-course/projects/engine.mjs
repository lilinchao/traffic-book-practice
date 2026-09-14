export const mean=a=>a.length?a.reduce((s,v)=>s+v,0)/a.length:null;
export const weekday=t=>new Date(t.slice(0,10)+'T00:00:00Z').getUTCDay();
export const isWeekend=t=>[0,6].includes(weekday(t));
export const hour=t=>Number(t.slice(11,13));
export const MODEL_NAMES={last:'上一已知值',day:'前日同期',week:'上周同期',calendar:'训练期星期小时均值',ridge:'岭回归'};
export const BOROUGHS={Manhattan:'曼哈顿',Brooklyn:'布鲁克林',Queens:'皇后区',Bronx:'布朗克斯','Staten Island':'斯塔滕岛',EWR:'EWR',Unknown:'未知'};
export const DEFAULTS={audit:{year:'2018',method:'unique'},forecast:{horizon:'1',model:'ridge',period:'all',month:'all'},hotspots:{borough:'all',cell:'500',weight:'count'},taxi:{day:'all',period:'all',normalize:'daily'},counting:{line:'15',direction:'both',stride:'1',band:'0.3',gap:'1.5',type:'all'}};

export function audit(data,config){
  const rows=data.rows.filter(r=>config.year==='all'||r[0].startsWith(config.year));
  if(!rows.length)return {metrics:{'有效小时':0},columns:[],rows:[],series:[]};
  const raw=rows.reduce((s,r)=>s+r[2],0);
  const expected=(Date.parse(rows.at(-1)[0]+'Z')-Date.parse(rows[0][0]+'Z'))/3600000+1;
  const chart=Array.from({length:24},(_,h)=>{
    const group=rows.filter(r=>hour(r[0])===h);
    const n=group.length,weight=group.reduce((s,r)=>s+r[2],0);
    return [h,n,weight,mean(group.map(r=>r[1])),weight?group.reduce((s,r)=>s+r[1]*r[2],0)/weight:null];
  });
  return {metrics:{'原始行':raw,'不同小时':rows.length,'重复行':raw-rows.length,'范围内缺失时间标签':expected-rows.length},columns:['小时','不同小时样本数','原始行数','去重均值','原始行加权均值'],rows:chart,series:[{name:config.method==='unique'?'按小时去重':'按原始行权重',values:chart.map(r=>r[config.method==='unique'?3:4])},{name:config.method==='unique'?'原始行加权均值':'按小时去重均值',values:chart.map(r=>r[config.method==='unique'?4:3])}],labels:chart.map(r=>r[0]+'时'),unit:'平均交通量（辆/小时）',note:`所选记录范围：${rows[0][0]} 至 ${rows.at(-1)[0]}。缺口以首末记录之间的本地时间标签计算，不恢复夏令时。首末年份不是完整全年。两条曲线均由实际记录计算，重复行权重不能解释为更多通过车辆。`};
}

export function errorMetrics(rows,index){
  if(!rows.length)return {n:0,mae:null,rmse:null,bias:null};
  const errors=rows.map(r=>r[index]-r[1]);
  return {n:rows.length,mae:mean(errors.map(Math.abs)),rmse:Math.sqrt(mean(errors.map(v=>v*v))),bias:mean(errors)};
}
export function forecast(data,c){
  const set=data.horizons[c.horizon];
  const rows=set.rows.filter(r=>(c.month==='all'||r[0].slice(5,7)===c.month)&&(c.period==='all'||(c.period==='peak'?[7,8,9,16,17,18].includes(hour(r[0])):![7,8,9,16,17,18].includes(hour(r[0])))));
  const idx=['last','day','week','calendar','ridge'].indexOf(c.model)+2;
  const e=errorMetrics(rows,idx);
  const table=Object.keys(MODEL_NAMES).map((m,i)=>{const v=errorMetrics(rows,i+2);return [MODEL_NAMES[m],v.n,v.mae,v.rmse,v.bias];});
  const first=rows.slice(0,96);
  return {metrics:{'有效测试样本':rows.length,'MAE（辆/小时）':e.mae,'RMSE（辆/小时）':e.rmse,'平均预测偏差':e.bias},columns:['方法','样本数','MAE','RMSE','平均预测减实测'],rows:table,exportColumns:['目标本地时间','实测','上一已知值','前日同期','上周同期','星期小时均值','岭回归'],exportRows:rows,labels:first.map(r=>r[0].slice(5).replace('T',' ')),series:[{name:'实测',values:first.map(r=>r[1])},{name:MODEL_NAMES[c.model],values:first.map(r=>r[idx])}],unit:'交通量（辆/小时），仅绘制所选样本前96条',note:`训练2017年，验证2018年1—6月，测试7—9月。当前跨度${c.horizon}小时，训练样本${set.trainN}，验证样本${set.validationN}，验证选定alpha=${set.alpha}。所有方法按共同有效样本比较。高峰定义为7—9时和16—18时，不代表全部道路的高峰。图中相邻选中记录不一定连续，误差表使用全部选中样本。`};
}

export function projectXY(lat,lon){return [(lon+74.3)*111320*Math.cos(40.73*Math.PI/180),(lat-40.45)*111320];}
export function hotspots(data,c){
  const selected=data.rows.filter(r=>c.borough==='all'||r[2]===c.borough);
  const valid=selected.filter(r=>r[7]);
  const cells=new Map(),size=Number(c.cell);
  const points=valid.map(r=>{
    const [x,y]=projectXY(r[3],r[4]),col=Math.floor(x/size),row=Math.floor(y/size),id=col+':'+row;
    if(!cells.has(id))cells.set(id,{id,col,row,count:0,injured:0});
    const v=cells.get(id);v.count++;v.injured+=r[5];
    return {x,y,id};
  });
  const sorted=[...cells.values()].sort((a,b)=>b[c.weight]-a[c.weight]||a.col-b.col||a.row-b.row);
  const rows=sorted.map(v=>[v.id,v.count,v.injured,+(40.45+(v.row+.5)*size/111320).toFixed(6),+(-74.3+(v.col+.5)*size/(111320*Math.cos(40.73*Math.PI/180))).toFixed(6)]);
  return {metrics:{'筛选记录':selected.length,'可落图记录':valid.length,'坐标排除':selected.length-valid.length,'有记录网格':cells.size},columns:['网格ID','事故记录数','伤者人数','中心纬度','中心经度'],rows,points,cells:sorted,size,unit:'局部近似米制坐标，非道路底图',note:'固定网格原点为经度-74.3、纬度40.45，东西距离按纬度40.73近似换算。仅用于课堂尺度比较，正式距离分析需合适投影。颜色代表所选计数，不是风险或核密度。未知行政区仍可能有有效坐标。'};
}

export function taxi(data,c){
  const dates=Array.from({length:31},(_,i)=>`2024-01-${String(i+1).padStart(2,'0')}`).filter(d=>c.day==='all'||(c.day==='weekend'?isWeekend(d):!isWeekend(d)));
  const validDate=new Set(dates),hours=Array.from({length:24},(_,i)=>i).filter(h=>c.period==='all'||(c.period==='night'?h>=22||h<6:h>=6&&h<22));
  const hs=new Set(hours),names=Object.keys(BOROUGHS),m=names.map(()=>Array(24).fill(0));
  for(const [date,b,h,n] of data.rows)if(validDate.has(date)&&hs.has(h))m[names.indexOf(b)][h]+=n;
  const total=m.flat().reduce((s,v)=>s+v,0),den=c.normalize==='daily'?dates.length:1;
  const matrix=m.map(row=>row.map(v=>v/den));
  const sums=names.map((n,i)=>[BOROUGHS[n],m[i].reduce((s,v)=>s+v,0),matrix[i].reduce((s,v)=>s+v,0)]).sort((a,b)=>b[2]-a[2]);
  return {metrics:{'筛选上车记录':total,'日期数':dates.length,'每天选取小时数':hours.length,'未知地区记录':m.at(-1).reduce((s,v)=>s+v,0)},columns:['行政区','上车记录总数',c.normalize==='daily'?'每日日均所选时段记录':'所选时段记录'],rows:sums,matrix,rowLabels:names.map(n=>BOROUGHS[n]),hours,unit:c.normalize==='daily'?'每日日均该小时上车记录（条）':'该小时累计上车记录（条）',exportColumns:['行政区','小时','原始记录数','展示值','日期分母'],exportRows:names.flatMap((n,i)=>hours.map(h=>[BOROUGHS[n],h,m[i][h],matrix[i][h],den])),note:'夜间定义为22:00—次日05:59。平日按周一至周五，不剔除节假日。日均使用筛选后全部日历日期数，零组表示本快照无保留记录。上车活动不等于所有出行或未满足需求。'};
}

export function counting(data,c){
  const times=[...new Set(data.rows.map(r=>r[1]))].sort((a,b)=>a-b),stride=Number(c.stride);
  const keep=new Set(times.filter((_,i)=>i%stride===0));
  const rows=data.rows.filter(r=>keep.has(r[1])&&(c.type==='all'||r[4]===c.type));
  const previous=new Map(),counted=new Set(),events=[];
  const line=Number(c.line),band=Number(c.band),gap=Number(c.gap)*1000;
  for(const [id,t,x,y,type] of rows){
    const side=x<line-band?-1:x>line+band?1:0;
    let prev=previous.get(id);
    if(prev&&t-prev.time>gap)prev=null;
    if(side&&prev?.side&&side!==prev.side){
      const direction=side>0?'positive':'negative',key=id+':'+direction;
      if(!counted.has(key)&&(c.direction==='both'||c.direction===direction)){
        events.push([id,t/1000,direction==='positive'?'+x':'-x',type,x,y]);counted.add(key);
      }
    }
    previous.set(id,{time:t,side:side||(prev?.side??0)});
  }
  return {metrics:{'跨线事件':events.length,'正方向事件':events.filter(e=>e[2]==='+x').length,'负方向事件':events.filter(e=>e[2]==='-x').length,'采样后轨迹点':rows.length},columns:['轨迹ID','检测到另一侧时刻（秒）','方向','类型','x（米）','y（米）'],rows:events,replayRows:rows,line,unit:'SinD 平滑轨迹回放，地面坐标（米）',note:'每个ID每个方向最多计1次。进入线两侧死区时不立即改变侧别，超过最大观测间隔则重置连接。事件时间为首次观察到另一侧的采样时间，不是精确穿线时刻。事件数不是检测精度，没有独立人工真值时不计算准确率。'};
}
export const ENGINES={audit,forecast,hotspots,taxi,counting};
