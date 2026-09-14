export const avg=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
export function errors(actual,predicted){
 if(!actual.length||actual.length!==predicted.length)throw Error('样本数量不一致。');
 const e=actual.map((v,i)=>predicted[i]-v);
 const result={样本数:e.length,RMSE:Math.sqrt(avg(e.map(x=>x*x))),MAE:avg(e.map(Math.abs)),平均预测偏差:avg(e)};
 if(Object.values(result).some(v=>!Number.isFinite(v)))throw Error('数值过大或不合法，无法计算有限误差。');
 return result;
}
export function bootstrap(rows,{n='60',repetitions='500',seed='42',group='all'}={}){
 n=Number(n);repetitions=Number(repetitions);seed=Number(seed);
 if(!['all','weekday','weekend'].includes(group))throw Error('未知日期类型。');
 const pool=rows.filter(r=>group==='all'||r.day_type===group);
 if(!Number.isInteger(n)||n<2||n>pool.length||!Number.isInteger(repetitions)||repetitions<50||repetitions>2000||!Number.isInteger(seed)||seed<0||seed>4294967295)throw Error('检查样本量、重复次数与随机种子。');
 let state=seed;const random=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};
 const sample=pool.slice();for(let i=sample.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[sample[i],sample[j]]=[sample[j],sample[i]];}
 const values=sample.slice(0,n).map(r=>Number(r.peak_mean)),means=[];
 for(let b=0;b<repetitions;b++){let total=0;for(let j=0;j<n;j++)total+=values[Math.floor(random()*n)];means.push(total/n);}
 means.sort((a,b)=>a-b);const q=p=>{const x=(means.length-1)*p,a=Math.floor(x);return means[a]+(means[Math.min(a+1,means.length-1)]-means[a])*(x-a);};
 return {n_days:n,available_days:pool.length,estimate:avg(values),lower:q(.025),upper:q(.975),observed_reference:avg(pool.map(r=>Number(r.peak_mean))),repetitions,seed,group,bootstrap_means:means};
}
export function bike(data,c){
 const rows=data.rows.filter(r=>c.period==='all'||(c.period==='night'?(r[2]>=22||r[2]<6):(r[2]>=6&&r[2]<22)));
 const names={mean:'训练期均值',ridge:'岭回归',poisson:'泊松回归'},index=Object.keys(names).indexOf(c.model)+4;
 if(index<4)throw Error('未知模型');
 const m=errors(rows.map(r=>r[3]),rows.map(r=>r[index]));
 return {metrics:m,columns:['模型','样本数','RMSE','MAE','平均预测偏差'],rows:Object.entries(names).map(([key,label],i)=>[label,...Object.values(errors(rows.map(r=>r[3]),rows.map(r=>r[i+4])))]),series:[{name:'实测',values:rows.slice(0,96).map(r=>r[3])},{name:names[c.model],values:rows.slice(0,96).map(r=>r[index])}],labels:rows.slice(0,96).map(r=>r[1].slice(5)+' '+r[2]+'时'),unit:'租借次数/小时；图示所选样本前96条，评价使用全部所选样本。',note:'模型在Python中训练；网页只重算冻结预测的分组误差。给定实测天气的条件回归不等于天气未知时的提前预测。',exportColumns:['id','cnt'],exportRows:rows.map(r=>[r[0],r[index]])};
}
export function parseCSV(text){
 if(text.length>6000000)throw Error('文件超过6MB限制。');
 text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],cell='',quoted=false,closed=false;
 for(let i=0;i<text.length;i++){
  const ch=text[i];
  if(quoted){if(ch==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=ch;continue;}
  if(ch==='"'){if(cell||closed)throw Error('CSV引号位置不合法。');quoted=true;continue;}
  if(ch===','||ch==='\r'||ch==='\n'){
   row.push(cell);cell='';closed=false;
   if(ch!==','){if(ch==='\r'&&text[i+1]==='\n')i++;if(row.some(v=>v!==''))rows.push(row);row=[];}continue;
  }
  if(closed)throw Error('CSV闭引号后只能出现分隔符。');cell+=ch;
 }
 if(quoted)throw Error('CSV含未闭合引号。');
 if(cell||row.length||closed){row.push(cell);if(row.some(v=>v!==''))rows.push(row);}
 if(!rows.length)throw Error('文件为空。');
 const header=rows.shift().map(x=>x.trim());
 if(header.some(x=>!x)||new Set(header).size!==header.length)throw Error('表头为空或重复。');
 if(rows.some(r=>r.length!==header.length))throw Error('部分行的列数与表头不一致。');
 return {header,rows};
}
export function toCSV(header,rows){
 const safe=x=>{let v=String(x??'');if(/^[=@]/.test(v))v="'"+v;return '"'+v.replaceAll('"','""')+'"';};
 return '\uFEFF'+[header,...rows].map(r=>r.map(safe).join(',')).join('\r\n');
}
const num=(value,label)=>{if(String(value).trim()===''||!Number.isFinite(Number(value)))throw Error(`${label}必须是有限数值，不能留空。`);return Number(value);};
export function validateSubmission(p,text,reference={}){
 if(p.id==='ch01'){
  if(text.length>200000)throw Error('报告不能超过20万字符。');
  const blocks=text.split(/^#{1,6}\s+/m).slice(1),required=['研究问题','数据方案','指标定义','局限与许可'];
  for(const title of required){const b=blocks.find(x=>x.split(/\r?\n/)[0].trim()===title);if(!b||b.split(/\r?\n/).slice(1).join('').trim().length<30)throw Error(`请在“${title}”标题下写至少30字分析。`);}
  return {type:'format',metrics:{已检查章节:4},note:'仅核查报告结构与是否填写。研究问题是否合理、证据是否充分仍需教师审核。'};
 }
 const {header,rows}=parseCSV(text);
 if(header.join(',')!==p.header.join(','))throw Error('需要表头：'+p.header.join(','));
 if(!rows.length&&p.id!=='ch08')throw Error('缺少数据行。');
 const unique=new Set();
 for(const r of rows){const key=p.id==='ch07'?r[0]+'|'+Number(r[1]):p.id==='ch08'?r[0]+'|'+r[2]:r[0];if(unique.has(key))throw Error('存在重复ID或重复统计单元：'+key);unique.add(key);}
 if(['ch04','ch06','ch02'].includes(p.id)){
  const expected=new Map(reference.rows.map(r=>[String(r[0]),Number(r[1])])),actual=[],predicted=[];
  if(rows.length!==expected.size)throw Error(`需要完整的${expected.size}行，当前${rows.length}行。`);
  for(const r of rows){if(!expected.has(r[0]))throw Error('存在未知ID：'+r[0]);const v=num(r[1],'结果');if(v<0)throw Error('结果不能为负数。');actual.push(expected.get(r[0]));predicted.push(v);}
  if(p.id==='ch02')return {type:'consistency',metrics:{记录数:rows.length,与参考不一致的行:actual.filter((v,i)=>v!==predicted[i]).length},note:'这是与公开参考清洗口径的一致性检查，不替代对处理规则的解释。'};
  return {type:'score',metrics:errors(actual,predicted),note:'公开练习标签上的本机自测，不是隐藏测试、正式成绩或跨学生排行榜。'};
 }
 if(p.id==='ch03'){
  if(rows.length!==1)throw Error('区间结果应只有1行。');const [estimate,lower,upper,n]=rows[0].map(x=>num(x,'区间结果'));
  if(lower>estimate||estimate>upper||lower<0||!Number.isInteger(n)||n<2||n>358)throw Error('检查区间顺序和日期样本量。');
 }else if(p.id==='ch05'){
  if(rows.length<3)throw Error('请提交至少3个候选网格。');
  const ids=new Set(reference.ids||[]);
  for(const [id,reason] of rows){if(!ids.has(id))throw Error('网格ID不在固定500米参考网格中：'+id);if(reason.trim().length<10)throw Error('每个候选网格需要至少10字的选择依据。');}
 }else if(p.id==='ch07'){
  const names=['Manhattan','Brooklyn','Queens','Bronx','Staten Island','EWR','Unknown'];
  if(rows.length!==168)throw Error('固定全天参考口径需要7地区×24小时，共168行。');
  for(const [borough,h,v] of rows){if(!names.includes(borough)||!Number.isInteger(num(h,'小时'))||+h<0||+h>23||num(v,'展示值')<0)throw Error('检查行政区、0至23时及非负展示值。');}
 }else if(p.id==='ch08'){
  const ids=new Set(reference.ids||[]);
  for(const [id,t,dir] of rows){if(!ids.has(id)||num(t,'事件秒数')<0||+t>=120||!['+x','-x'].includes(dir))throw Error('检查轨迹ID、0至120秒内的时间和+x/-x方向。');}
 }
 return {type:'format',metrics:{有效格式行数:rows.length},note:'格式检查通过，不代表结果正确或项目完成。请附配置、证据和分析报告供教师审阅。'};
}
