// Public local self-check, not proof of independent authorship or a course grade.
const check=(ok,message)=>{if(!ok)throw Error(message);};
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const vector=(v,n,test=finite)=>Array.isArray(v)&&v.length===n&&v.every(test);
const unique=a=>new Set(a).size===a.length;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function crossingEvents(rows,line=15,band=.3,gap=1.5){
 const states=new Map(),seen=new Set(),events=[];
 for(const [id,t,x] of [...rows].sort((a,b)=>a[1]-b[1])){
  const side=x<line-band?-1:x>line+band?1:0,previous=states.get(String(id)),old=previous&&t-previous.t<=gap?previous:null;
  if(old&&side&&old.side&&side!==old.side){const direction=side>0?'+x':'-x',key=String(id)+'|'+direction;if(!seen.has(key)){events.push([id,t,direction]);seen.add(key);}}
  states.set(String(id),{t,side:side||(old?.side||0)});
 }
 return events;
}
export function validatePrimary(project,bundle,ref){
 const chapter=typeof project==='number'?project:project.chapter;
 check(bundle&&bundle.schema==='traffic-primary-v1','需要工作本导出的traffic-primary-v1 JSON。');
 check(bundle.chapter===chapter&&bundle.protocol===ref.protocol,'章节或主实验协议不匹配；旧CSV与其他协议不能混用。');
 for(const [path,sha] of Object.entries(ref.inputs))check(bundle.inputs?.[path]===sha,`输入版本不匹配：${path}`);
 check(bundle.config&&typeof bundle.config==='object'&&!Array.isArray(bundle.config),'缺少实验配置。');
 const o=bundle.outputs;check(o&&typeof o==='object','缺少outputs。');
 const rows=[],metrics={},warnings=['自报哈希与文件自测不能证明实际训练、无泄漏或独立完成；教师仍需审阅代码和工程解释。'];
 if(ref.truth){
  const t=o.predictions;check(t&&same(t.columns,['id','model','prediction'])&&Array.isArray(t.rows),'预测表需含id,model,prediction。');
  const truth=new Map(ref.truth),models=new Map(),allowed=[...ref.models,...(ref.optional_models||[])];
  for(const r of t.rows){
   check(Array.isArray(r)&&r.length===3&&typeof r[0]==='string'&&truth.has(r[0])&&allowed.includes(r[1])&&finite(r[2]),'存在未知ID、模型或非有限预测。');
   check(r[2]>=0,'交通量/租借量预测不得为负；请明确采用的非负处理。');
   if(!models.has(r[1]))models.set(r[1],new Map());const m=models.get(r[1]);check(!m.has(r[0]),'同模型存在重复ID。');m.set(r[0],r[2]);
  }
  for(const name of ref.models)check(models.has(name),`缺少必做模型：${name}`);
  for(const [name,pred] of models){check(pred.size===truth.size,`${name}须覆盖相同${truth.size}个目标。`);let abs=0,sq=0,bias=0;for(const [id,y] of truth){const d=pred.get(id)-y;abs+=Math.abs(d);sq+=d*d;bias+=d;}check([abs,sq,bias].every(finite),'预测导致指标数值溢出，请检查单位与数值范围。');rows.push([name,truth.size,abs/truth.size,Math.sqrt(sq/truth.size),bias/truth.size]);}
  metrics.targets=truth.size;metrics.models=models.size;metrics.predictions=t.rows.length;
 }
 if(chapter===5){
  check(same(o.grid_ids,ref.grid_ids),'空间评价网格ID或顺序不匹配。');
  for(const h of ['250','500','1000'])check(vector(o.density?.[h],ref.grid_ids.length,x=>finite(x)&&x>=0),`KDE ${h}米需覆盖全部固定网格。`);
  for(const eps of [150,350,700])for(const n of [5,15])check(vector(o.clusters?.[`${eps}-${n}`],ref.point_ids.length,x=>Number.isInteger(x)&&x>=-1),'缺少完整DBSCAN成员标签。');
  check(Array.isArray(o.candidates)&&o.candidates.length>=3&&unique(o.candidates.map(c=>c.grid_id)),'须提交至少3个不重复候选地点。');
  for(const c of o.candidates){check(ref.grid_ids.includes(c.grid_id)&&finite(c.east_m)&&finite(c.north_m)&&typeof c.reason==='string'&&c.reason.trim().length>=8&&typeof c.evidence_needed==='string'&&c.evidence_needed.trim().length>0,'候选地点须含有效ID、位置、理由和待补充证据。');const [x,y]=c.grid_id.split(':').map(Number);check(Math.abs(c.east_m-(x+.5)*500)<1e-6&&Math.abs(c.north_m-(y+.5)*500)<1e-6,'候选坐标与500米网格中心不一致。');}
  if(o.candidates.some(c=>/待学生|待匹配|自动高密度/.test(c.reason+' '+c.road_object)))warnings.push('存在自动候选或待核实道路对象；这是有效计算文件，但现场排查论证尚未完成。');
  Object.assign(metrics,{grids:ref.grid_ids.length,points:ref.point_ids.length,candidates:o.candidates.length});
 }
 if(chapter===7){
  for(const k of [2,3,4,5])for(const seed of [42,7,19]){const key=`${k}-${seed}`;check(vector(o.memberships?.[key],31,x=>Number.isInteger(x)&&x>=0&&x<k),`缺少${key}的31日成员。`);check(Array.isArray(o.centers?.[key])&&o.centers[key].length===k&&o.centers[key].every(r=>vector(r,168,x=>finite(x)&&x>=-1e-12)&&Math.abs(r.reduce((a,b)=>a+b,0)-1)<1e-6),`${key}中心需为168维占比。`);}
  metrics.clusteringRuns=12;warnings.push('聚类这里只核查标签、中心结构；不能据此证明全月聚类未泄漏到预测训练中。');
 }
 if(chapter===8){
  check(bundle.config.line_x_m===15&&bundle.config.band_m===.3&&bundle.config.count_gap_s===1.5,'主自测固定x=15米、死区0.3米、间断上限1.5秒；其他规则请另附分析。');
  const times=[...new Set(ref.points.map(r=>r[1]))].sort((a,b)=>a-b);let total=0,events=0;
  for(const stride of [1,5,10])for(const mode of ['position','kalman']){
   const run=o.runs?.[`${stride}-${mode}`],selected=new Set(times.filter((_,i)=>i%stride===0)),expected=new Map(ref.points.filter(r=>selected.has(r[1])).map(r=>[r[0]+'|'+r[1],r]));
   check(run&&Array.isArray(run.assignments)&&run.assignments.length===expected.size,'缺少指定采样的完整身份指派。');
   const seen=new Set(),perFrame=new Set();let lastTime=-Infinity;
   for(const r of run.assignments){check(Array.isArray(r)&&r.length===5&&typeof r[0]==='string'&&Number.isInteger(r[1])&&r[1]>=0&&r.slice(2).every(finite),'身份指派字段无效。');const key=r[0]+'|'+r[2],source=expected.get(key),frameKey=r[1]+'|'+r[2];check(source&&!seen.has(key)&&!perFrame.has(frameKey)&&r[2]>=lastTime&&Math.abs(source[2]-r[3])<1e-8&&Math.abs(source[3]-r[4])<1e-8,'身份指派遗漏、重复、乱序或改写了实测坐标。');seen.add(key);perFrame.add(frameKey);lastTime=r[2];}
   const calculated=crossingEvents(run.assignments.map(r=>[r[1],r[2],r[3],r[4]]));
   const normalize=a=>a.map(r=>[String(r[0]),Number(r[1]).toFixed(6),r[2]].join('|')).sort();
   check(Array.isArray(run.events)&&run.events.every(r=>Array.isArray(r)&&r.length===3&&finite(r[1])&&['+x','-x'].includes(r[2]))&&same(normalize(run.events),normalize(calculated)),'通行事件与新ID轨迹和固定计数规则不一致。');
   total+=run.assignments.length;events+=calculated.length;
  }
  Object.assign(metrics,{trackingRuns:6,assignments:total,events});warnings.push('SinD源ID用于事后审计，不是视频检测真值；真实视频单独按影像协议评价。');
 }
 return {metrics,columns:['模型','共同目标数','MAE','RMSE','平均偏差'],rows,warnings,note:'主实验文件结构、范围与可重算结果已核查；不等于工程成果已验收。'};
}
