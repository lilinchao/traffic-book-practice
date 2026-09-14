import {PROJECTS,CHAPTERS,RUBRIC} from './catalog.js';
import {ENGINES,DEFAULTS,MODEL_NAMES} from './engine.mjs';
const $=s=>document.querySelector(s),main=$('#main'),KEY='traffic-projects-v1',NL=String.fromCharCode(10);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>v==null?'无有效样本':typeof v==='number'?v.toLocaleString('zh-CN',{maximumFractionDigits:Number.isInteger(v)?0:2}):String(v);
const list=arr=>`<ul class="plain-list">${arr.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
const csvNames={audit:'metro-hours.csv',forecast:'forecast.json',hotspots:'nyc-crashes-2024-01.csv',taxi:'taxi-borough-date-hour.csv',counting:'sind-tianjin-120s.csv'};
const reportFields={hypothesis:'研究问题与假设',finding:'主要发现与证据',limits:'限制与可能反例',reproduction:'复现方式与文件说明'};
let current=null,dataset=null,result=null,routeToken=0,replayTimer=null,filter='all',storageOK=true;
const cache=new Map();
let state={version:1,projects:{}};
function validConfig(id,raw={}){
  const d={...DEFAULTS[id]};
  const enums={year:['all','2012','2013','2014','2015','2016','2017','2018'],method:['unique','raw'],horizon:['1','3','6'],model:Object.keys(MODEL_NAMES),period:id==='taxi'?['all','night','day']:['all','peak','offpeak'],month:['all','07','08','09'],borough:['all','MANHATTAN','BROOKLYN','QUEENS','BRONX','STATEN ISLAND','UNKNOWN'],cell:['250','500','1000'],weight:['count','injured'],day:['all','weekday','weekend'],normalize:['daily','total'],direction:['both','positive','negative'],stride:['1','5','10'],type:['all','car','bus','bicycle','motorcycle','tricycle','truck']};
  for(const k of Object.keys(d))if(Object.hasOwn(raw,k)){
    const v=String(raw[k]);
    if(enums[k]&&!enums[k].includes(v))throw Error('不支持的参数：'+k);
    if(['line','band','gap'].includes(k)){const [lo,hi]=k==='line'?[-20,55]:k==='band'?[0,3]:[0.1,5];if(!Number.isFinite(+v)||+v<lo||+v>hi)throw Error('参数超出范围：'+k);}
    d[k]=v;
  }return d;
}
function cleanRecord(id,r={}){
  const p=PROJECTS.find(p=>p.id===id),answers={},checks={};
  for(const k of [...p.stages.map(s=>s[0]),...Object.keys(reportFields)])answers[k]=typeof r.answers?.[k]==='string'?r.answers[k].slice(0,20000):'';
  for(const s of p.stages)checks[s[0]]=r.checks?.[s[0]]===true&&answers[s[0]].trim().length>=20;
  const runs=(Array.isArray(r.runs)?r.runs:[]).slice(-20).map(x=>({time:String(x.time||'').slice(0,40),config:validConfig(id,x.config),metrics:Object.fromEntries(Object.entries(x.metrics||{}).filter(([k,v])=>k.length<100&&(v===null||typeof v==='number'&&Number.isFinite(v)))),sourceSha:String(x.sourceSha||'').slice(0,64)}));
  return {answers,checks,runs,config:validConfig(id,r.config)};
}
try{const loaded=JSON.parse(localStorage.getItem(KEY)||'null');if(loaded?.version===1)for(const p of PROJECTS)if(loaded.projects?.[p.id])state.projects[p.id]=cleanRecord(p.id,loaded.projects[p.id]);localStorage.setItem(KEY,JSON.stringify(state));}catch{storageOK=false;$('#storage-warning').hidden=false;}
function record(id){return state.projects[id]??(state.projects[id]=cleanRecord(id));}
function completed(p){return p.stages.filter(s=>record(p.id).checks[s[0]]).length;}
function updateProgress(){if($('#progress')&&current)$('#progress').textContent=`自查 ${completed(current)}/4 阶段，已保存 ${record(current.id).runs.length} 次实验。${storageOK?'草稿已存本机。':'请导出备份。'} 此状态不代表教师验收。`;}
function persist(){if(storageOK)try{localStorage.setItem(KEY,JSON.stringify(state));}catch{storageOK=false;$('#storage-warning').hidden=false;}updateProgress();}
async function loadData(p){if(!cache.has(p.file))cache.set(p.file,fetch(`projects/data/${p.file}.json`).then(r=>{if(!r.ok)throw Error('数据HTTP '+r.status);return r.json();}).catch(e=>{cache.delete(p.file);throw e;}));return cache.get(p.file);}
function stopReplay(){if(replayTimer)clearInterval(replayTimer);replayTimer=null;}
function home(){
 current=null;dataset=null;result=null;stopReplay();document.title='交通数据挖掘 · 项目实践';
 main.innerHTML=`<section class="hero" id="home"><div><p class="eyebrow">PROJECT-BASED LEARNING / OPEN COURSE</p><h1>交通数据挖掘<br>项目实践</h1><p class="lead">以真实交通任务组织实践。完成数据审计、方法对照与结果解释，交付一份能复核过程、也能说明局限的项目成果。</p><div class="actions"><a class="button" href="#project/audit">从数据审计开始</a><a class="button secondary" href="#projects">选择专题项目</a></div></div><aside class="hero-evidence"><p class="eyebrow">第一项任务 / 数据接收审计</p><h2>48,204 行记录，<br>为什么不等于 48,204 个小时？</h2><div class="pair"><div><strong>40,575</strong><span>不同小时标签</span></div><div><strong>7,629</strong><span>重复记录行</span></div></div><p>数字来自 UCI I-94 原始文件的去重审计。先检验数据能否回答问题，再讨论选择什么模型。</p></aside></section>
 <div class="route-strip" aria-label="项目基本流程">${[['01 任务界定','明确问题与交付物'],['02 数据审计','核查来源和口径'],['03 方法对照','保留基线与实验'],['04 结果解释','分析误差和边界'],['05 成果答辩','提交可复现证据']].map(r=>`<div>${r[0]}<small>${r[1]}</small></div>`).join('')}</div>
 <section class="section" id="projects"><div class="section-head"><div><p class="eyebrow">5 个项目 / 跨章节组织</p><h2>选择一个值得做完整的问题</h2></div><p>建议完成共同基础，再按兴趣选择专题。项目时长是参考工作量，可由教师按课时安排；每个项目均包含四个里程碑和成果验收要求。</p></div><div class="filter-row" role="group" aria-label="按教材章节查看项目"><button data-filter="all" aria-pressed="${filter==='all'}">全部项目</button>${CHAPTERS.map((n,i)=>`<button data-filter="${i+1}" aria-pressed="${filter===String(i+1)}" title="${esc(n)}">第${i+1}章</button>`).join('')}</div><div class="project-list">${PROJECTS.map(p=>`<article class="project-card" style="--project-color:${p.color}" ${filter!=='all'&&!p.chapters.includes(+filter)?'hidden':''}><span class="project-index">${p.number}</span><div><div class="project-meta"><span>${p.level}</span><span>建议 ${p.time}</span><span>自查 ${completed(p)}/4</span></div><h3><a href="#project/${p.id}">${p.title}</a></h3><p>${p.subtitle}</p><div class="project-meta"><span>关联第 ${p.chapters.join('、')} 章</span><span>${p.dataset}</span></div></div><div class="project-summary"><strong>最终交付</strong><p>${p.deliverables.join('、')}</p><a href="#project/${p.id}">查看任务书与工作台</a></div></article>`).join('')}</div></section>
 <section class="teaching two-col"><div><h3>建议怎样组织课堂？</h3><p>2—3人小组完成数据审计，再选择一个专题做深入分析。课堂用于讨论方案与质疑结果，课外完成代码复现和成果整理。可安排一次中期检查和一次结题答辩。</p><a href="projects/TEACHING_GUIDE.md">教师实施指南</a></div><div><h3>理论、项目与工具各有位置</h3><p>教材解释概念与方法。项目要求形成完整证据。原有小实验保留在方法工具箱，供按需复习，不以实验数量代替项目深度。</p><div class="actions"><a href="chapter-01/">第一章交互课堂</a><a href="methods.html">历史方法工具箱</a><a href="projects/project-kit.zip" download>下载全套项目包</a></div></div></section>`;
}
function select(name,label,options,value){return `<label class="control">${esc(label)}<select name="${name}">${options.map(o=>{const [v,t]=Array.isArray(o)?o:[o,o];return `<option value="${esc(v)}" ${String(v)===value?'selected':''}>${esc(t)}</option>`;}).join('')}</select></label>`;}
function number(name,label,min,max,step,value){return `<label class="control">${esc(label)}<input type="number" name="${name}" min="${min}" max="${max}" step="${step}" value="${value}" required></label>`;}
function controls(p,c){
 if(p.id==='audit')return select('year','年份',[['all','全部年份'],...Array.from({length:7},(_,i)=>String(2012+i))],c.year)+select('method','主分析口径',[['unique','按小时去重'],['raw','原始行权重']],c.method);
 if(p.id==='forecast')return select('horizon','预测跨度（小时）',['1','3','6'],c.horizon)+select('model','观察模型',Object.entries(MODEL_NAMES),c.model)+select('month','测试月份',[['all','7—9月'],['07','7月'],['08','8月'],['09','9月']],c.month)+select('period','目标时段',[['all','全部'],['peak','高峰'],['offpeak','非高峰']],c.period);
 if(p.id==='hotspots')return select('borough','行政区',[['all','全部'],['MANHATTAN','曼哈顿'],['BROOKLYN','布鲁克林'],['QUEENS','皇后区'],['BRONX','布朗克斯'],['STATEN ISLAND','斯塔滕岛'],['UNKNOWN','未知']],c.borough)+select('cell','网格边长（米）',['250','500','1000'],c.cell)+select('weight','清单排序口径',[['count','事故次数'],['injured','伤者人数']],c.weight);
 if(p.id==='taxi')return select('day','日期类型',[['all','全部日期'],['weekday','周一至周五'],['weekend','周六、周日']],c.day)+select('period','时段',[['all','全天'],['night','夜间22—05时'],['day','白天06—21时']],c.period)+select('normalize','展示口径',[['daily','每日日均'],['total','累计总量']],c.normalize);
 return number('line','计数线 x（米）',-20,55,1,c.line)+select('direction','计数方向',[['both','双方向'],['positive','x 增加方向'],['negative','x 减少方向']],c.direction)+select('stride','每隔多少帧采样',['1','5','10'],c.stride)+number('band','单侧死区（米）',0,3,.1,c.band)+number('gap','最大相邻间隔（秒）',.1,5,.1,c.gap)+select('type','车辆类型',[['all','全部类别'],...dataset.meta.types],c.type);
}
function dataFacts(p,m){
 const entries=p.id==='audit'?[['原始行',m.rawRows],['不同小时',m.hours],['重复行',m.duplicateRows],['冲突交通量小时',m.conflictingHours]]:p.id==='forecast'?[['训练','2017年'],['验证','2018年1—6月'],['测试','2018年7—9月'],['模型','4个基线 + 岭回归']]:p.id==='hotspots'?[['月份','2024年1月'],['记录总数',m.rawRows],['有效坐标',m.validCoordinates],['无法落图',m.rawRows-m.validCoordinates]]:p.id==='taxi'?[['月份','2024年1月'],['原始行',m.rawRows],['保留上车记录',m.keptTrips],['排除非当月',m.excluded]]:[['片段长度','120秒'],['轨迹点',m.rows],['参与轨迹',m.tracks],['行人文件','未包含']];
 return `<dl class="data-facts">${entries.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(fmt(v))}</dd>`).join('')}</dl>`;
}
function projectPage(p){
 const r=record(p.id),m=dataset.meta;
 main.innerHTML=`<header class="project-heading"><a class="back" href="#projects">返回项目目录</a><p class="eyebrow">PROJECT ${p.number} / ${p.level}</p><h1>${p.title}</h1><p class="question">${p.question}</p><div class="project-meta"><span>建议 ${p.time}</span><span>关联第 ${p.chapters.join('、')} 章</span><span>${p.dataset}</span></div><p id="progress" class="progress"></p></header>
 <nav class="project-nav" aria-label="项目内导航">${[['brief','任务书'],['data','数据卡'],['workbench','分析工作台'],['stages','里程碑'],['submission','代码与报告'],['rubric','验收标准']].map(([a,b])=>`<a href="#project/${p.id}/${a}">${b}</a>`).join('')}</nav>
 <section id="brief" class="section"><h2>项目任务书</h2><p class="brief">${p.commission}</p><div class="two-col"><div class="deliverables"><strong>需要提交什么？</strong>${list(p.deliverables)}</div><div><h3>开始之前，明确分析边界</h3>${list(p.boundaries)}</div></div></section>
 <section id="data" class="section"><div class="section-head"><h2>数据卡与追溯信息</h2><p>数据快照固定，后续官网记录可能修订。复现时请核对哈希，不能把不同版本的结果混在一起。</p></div><div class="data-grid"><div class="data-card"><h3><a href="${p.source.url}" target="_blank" rel="noopener">${p.source.title}</a></h3>${dataFacts(p,m)}<p>${p.source.details}</p><div class="source-downloads"><a href="projects/data/${csvNames[p.id]}" download>下载分析数据</a><a href="projects/data/${p.file}.json" download>快照与元数据 JSON</a></div></div><div class="data-card"><h3>来源、许可与处理</h3><p>${p.source.license}</p><p>整理日期：${esc(m.retrieved)}<br>原始文件 SHA-256：</p><code>${esc(m.sha256)}</code><div class="source-downloads"><a href="projects/python/prepare_data.py" download>数据准备与处理代码</a><a href="projects/DATA_SOURCES.md">完整数据说明</a>${p.id==='counting'?'<a href="projects/data/SIND-LICENSE.txt">SinD 原始许可</a>':''}</div></div></div></section>
 <section id="workbench" class="section"><div class="section-head"><h2>分析工作台</h2><p>参数变化会重新计算所选数据的结果。保存实验形成对照记录，再用 Python 修改方法或扩大分析，不能只提交默认图。</p></div><div class="workbench"><form class="controls" id="config-form">${controls(p,r.config)}</form><div class="lab-output" id="lab-output"></div><div class="lab-actions"><button id="save-run">保存本次实验</button><button class="secondary" id="export-csv">导出当前结果 CSV</button><button class="secondary" id="reset-config">恢复默认参数</button><span class="feedback" id="lab-feedback" role="status"></span></div></div><details id="run-history"><summary>实验对照记录（最多保留20次）</summary><div id="run-list"></div></details></section>
 <section id="stages" class="section"><div class="section-head"><h2>四个里程碑</h2><p>每个阶段写下自己的依据，再勾选自查。网页不会把“点过按钮”或“运行成功”当作完成学习。</p></div>${p.stages.map(([id,title,lead,prompt,deliver])=>`<article class="stage"><div><h3>${title}</h3><p><strong>${lead}</strong><br>${prompt}</p><p>阶段成果：${deliver}</p></div><div><label for="answer-${id}" class="muted">分析记录与证据</label><textarea id="answer-${id}" data-answer="${id}" maxlength="20000" placeholder="写出数据依据、比较配置和你的判断，不只描述操作步骤。">${esc(r.answers[id])}</textarea><label class="check-row"><input type="checkbox" data-check="${id}" ${r.checks[id]?'checked':''} ${r.answers[id].trim().length<20?'disabled':''}>我已整理本阶段证据，等待教师验收（至少记录20字后可自查）</label></div></article>`).join('')}</section>
 <section id="submission" class="section"><div class="section-head"><h2>代码复现与项目报告</h2><p>网页是探索入口，Python是扩展分析的起点。报告应解释为什么采用某种规则，以及结果支持什么、不支持什么。</p></div><div class="two-col"><div><h3>运行同口径的参考分析</h3><p class="muted">下载项目包并解压，在解压目录打开终端。基线分析仅使用Python标准库；重新下载数据和训练模型时再安装扩展依赖。</p><pre class="code-block">python python/analyze.py --project ${p.id}&#10;python python/analyze.py --project ${p.id} --config experiment.json&#10;# 从官方原始数据重新准备快照与训练&#10;python -m pip install -r python/requirements.txt&#10;python python/prepare_data.py --output data</pre><div class="actions"><a class="button" href="projects/project-kit.zip" download>下载项目包</a><a href="projects/notebooks/${p.id}.ipynb" download>学生工作本</a><a href="projects/python/analyze.py">阅读分析源码</a></div></div><div><h3>提高项目深度</h3>${list(p.extensions)}<p class="notice">不自动提交到服务器，不自动评分。导出的报告和数据由你自行提交给教师；不要填写姓名、学号或敏感信息。</p></div></div><div class="report-fields">${Object.entries(reportFields).map(([id,title])=>`<label>${title}<textarea data-answer="${id}" maxlength="20000" placeholder="结合本项目的实验记录填写。">${esc(r.answers[id])}</textarea></label>`).join('')}</div><div class="actions"><button id="export-report">导出项目报告 Markdown</button><button class="secondary" id="export-record">导出记录与当前配置 JSON</button><label class="button secondary">恢复本项目记录<input id="import-record" type="file" accept="application/json,.json" hidden></label></div><p id="import-feedback" class="feedback" role="status"></p></section>
 <section id="rubric" class="section"><div class="section-head"><h2>验收与评价</h2><p>以下为建议的100分评价量规，供教师按实际教学调整。自查状态、记录字数和实验次数不自动换算为成绩。</p></div><div class="rubric">${RUBRIC.map(([n,w,d])=>`<div><strong>${w}<small>分</small></strong><h3>${n}</h3><p>${d}</p></div>`).join('')}</div><h3>本项目的最低验收要求</h3>${list(p.acceptance)}<div class="actions"><a href="#projects">回到项目目录</a><button class="secondary danger" id="clear-record">清除此项目的本机草稿</button></div></section>`;
 if(['hotspots','taxi','counting'].includes(p.id))$('#submission .two-col > div:last-child').insertAdjacentHTML('beforeend',`<h3>可运行的深入对照</h3><pre class="code-block">python python/extensions.py --project ${p.id}</pre><a href="projects/python/extensions.py">阅读扩展分析代码</a>`);
 const importLabel=$('#import-record').parentElement;importLabel.tabIndex=0;importLabel.setAttribute('role','button');importLabel.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();$('#import-record').click();}});
 updateProgress();runAnalysis();renderHistory();
}
function table(columns,rows,limit=20,caption='结果表'){return `<div class="table-wrap"><table><caption>${esc(caption)}${rows.length>limit?`（前${limit}行，共${rows.length}行，导出可获取全部）`:''}</caption><thead><tr>${columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,limit).map(r=>`<tr>${r.map(v=>`<td>${esc(fmt(v))}</td>`).join('')}</tr>`).join('')}</tbody></table>${rows.length?'':'<p class="empty">当前条件下没有结果，请调整筛选。</p>'}</div>`;}
function lineChart(r){
 const max=Math.max(1,...r.series.flatMap(s=>s.values.filter(v=>v!=null))),colors=['#126b63','#ba6a37'];
 const w=1040,h=320,left=67,right=20,top=18,bottom=48,n=r.labels.length;
 const x=i=>left+i*(w-left-right)/Math.max(n-1,1),y=v=>h-bottom-(v/max)*(h-top-bottom);
 const grid=Array.from({length:5},(_,i)=>{const v=max*i/4;return `<line x1="${left}" y1="${y(v)}" x2="${w-right}" y2="${y(v)}" stroke="#e0e6e2"/><text x="${left-9}" y="${y(v)+4}" text-anchor="end" fill="#53686d" font-size="12">${Math.round(v).toLocaleString()}</text>`;}).join('');
 const ticks=r.labels.map((t,i)=>i===0||i===n-1||i%Math.ceil(n/6)===0?`<text x="${x(i)}" y="${h-16}" text-anchor="${i===0?'start':i===n-1?'end':'middle'}" fill="#53686d" font-size="12">${esc(t)}</text>`:'').join('');
 const paths=r.series.map((s,j)=>{let drawing=false;const d=s.values.map((v,i)=>{if(v==null){drawing=false;return '';}const c=drawing?'L':'M';drawing=true;return `${c}${x(i).toFixed(1)},${y(v).toFixed(1)}`;}).join(' ');return `<path d="${d}" fill="none" stroke="${colors[j]}" stroke-width="2.5"/>`;}).join('');
 return `<div class="chart-scroll"><svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(r.unit)}"><title>${esc(r.series.map(s=>s.name).join('与'))}，小屏可横向滑动，数据见表格或CSV</title>${grid}${paths}${ticks}</svg></div><div class="legend">${r.series.map((s,i)=>`<span><i style="background:${colors[i]}"></i>${esc(s.name)}</span>`).join('')}</div>`;
}
function heatmap(r){const max=Math.max(1,...r.matrix.flat());return `<div class="table-wrap"><table class="heatmap"><caption>${esc(r.unit)}，颜色越深表示记录越多</caption><thead><tr><th>地区 / 小时</th>${r.hours.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${r.matrix.map((row,i)=>`<tr><th scope="row">${r.rowLabels[i]}</th>${r.hours.map(h=>`<td style="background:rgba(18,107,99,${(.06+.45*row[h]/max).toFixed(3)})">${fmt(row[h])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
function runAnalysis(){
 stopReplay();
 try{
  result=ENGINES[current.id](dataset,record(current.id).config);
  const r=result;let plot=r.series?lineChart(r):r.matrix?heatmap(r):'<canvas id="plot" width="1100" height="430" aria-label="实际数据坐标图，明细见下方表格"></canvas>';
  if(current.id==='counting')plot+=`<div class="replay-controls"><button class="secondary" id="play">播放轨迹</button><label for="replay-time">时刻 <output id="time-label">0.0秒</output></label><input type="range" id="replay-time" min="0" max="119.9" step="0.1" value="0" aria-label="轨迹回放时刻"></div>`;
  $('#lab-output').innerHTML=`<div class="stats">${Object.entries(r.metrics).map(([k,v])=>`<div><small>${esc(k)}</small><strong>${esc(fmt(v))}</strong></div>`).join('')}</div><p class="unit">${esc(r.unit)}</p>${plot}<p class="lab-note">${esc(r.note)}</p>${table(r.columns,r.rows,20,current.id==='counting'?'跨线事件清单':'结果对照')}`;
  if(current.id==='hotspots')drawSpatial();
  if(current.id==='counting')drawReplay(0);
  $('#lab-feedback').textContent='已按当前配置计算。';
 }catch(e){result=null;$('#lab-output').innerHTML=`<p class="notice">计算失败：${esc(e.message)}</p>`;}
}
function axes(canvas,bounds){
 const ctx=canvas.getContext('2d'),[xmin,xmax,ymin,ymax]=bounds,w=Math.max(200,canvas.getBoundingClientRect().width),h=w<700?320:430,pad=40,dpr=Math.min(2,window.devicePixelRatio||1);
 canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);canvas.style.height=h+'px';ctx.setTransform(dpr,0,0,dpr,0,0);
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#f6f7f4';ctx.fillRect(0,0,w,h);
 const scale=Math.min((w-2*pad)/(xmax-xmin),(h-2*pad)/(ymax-ymin));
 const ox=(w-(xmax-xmin)*scale)/2,oy=(h-(ymax-ymin)*scale)/2;
 const xy=(x,y)=>[ox+(x-xmin)*scale,h-oy-(y-ymin)*scale];
 ctx.fillStyle='#53686d';ctx.font='14px Microsoft YaHei';ctx.fillText(`x: ${xmin.toFixed(1)} 至 ${xmax.toFixed(1)} 米`,20,h-10);ctx.fillText(`y: ${ymin.toFixed(1)} 至 ${ymax.toFixed(1)} 米`,20,20);
 return {ctx,xy,scale,h};
}
function drawSpatial(){
 const r=result,canvas=$('#plot');if(!r.points.length)return;
 const xs=r.points.map(p=>p.x),ys=r.points.map(p=>p.y),size=r.size;
 const {ctx,xy,scale}=axes(canvas,[Math.min(...xs)-size,Math.max(...xs)+size,Math.min(...ys)-size,Math.max(...ys)+size]);
 const weight=record(current.id).config.weight,max=Math.max(1,...r.cells.map(c=>c[weight]));
 for(const c of r.cells){const [x,y]=xy(c.col*size,(c.row+1)*size);ctx.fillStyle=`rgba(169,89,36,${.08+.75*c[weight]/max})`;ctx.fillRect(x,y,Math.max(2,size*scale),Math.max(2,size*scale));}
 ctx.strokeStyle='#233b42';ctx.lineWidth=2;
 for(const c of r.cells.slice(0,3)){const [x,y]=xy(c.col*size,(c.row+1)*size);ctx.strokeRect(x,y,Math.max(2,size*scale),Math.max(2,size*scale));}
}
function drawReplay(t){
 const data=dataset.rows,xs=data.map(r=>r[2]),ys=data.map(r=>r[3]);
 const {ctx,xy,h}=axes($('#plot'),[Math.min(...xs)-3,Math.max(...xs)+3,Math.min(...ys)-3,Math.max(...ys)+3]);
 const line=result.line,band=+record(current.id).config.band,[a,b]=[xy(line,Math.min(...ys)-3),xy(line,Math.max(...ys)+3)];
 const left=xy(line-band,0)[0],right=xy(line+band,0)[0];ctx.fillStyle='#b7593122';ctx.fillRect(left,46,right-left,h-90);
 ctx.strokeStyle='#b75931';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
 const target=t*1000,latest=new Map(),trails=new Map();
 for(const row of result.replayRows)if(row[1]<=target&&target-row[1]<2000){if(!trails.has(row[0]))trails.set(row[0],[]);trails.get(row[0]).push(row);if(target-row[1]<1200)latest.set(row[0],row);}
 ctx.strokeStyle='#799e9888';ctx.lineWidth=2;
 for(const trail of trails.values()){ctx.beginPath();trail.forEach((r,i)=>{const [px,py]=xy(r[2],r[3]);if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);});ctx.stroke();}
 for(const [id,ts,x,y,type] of latest.values()){
  const [px,py]=xy(x,y);ctx.fillStyle=type==='car'||type==='bus'?'#126b63':'#685087';ctx.beginPath();ctx.arc(px,py,5,0,2*Math.PI);ctx.fill();ctx.font='11px Microsoft YaHei';ctx.fillText(id,px+7,py-5);
 }
 ctx.fillStyle='#233b42';ctx.font='14px Microsoft YaHei';ctx.fillText(`${t.toFixed(1)}秒 / ${latest.size}个ID / 已触发${result.rows.filter(r=>r[1]<=t).length}次事件`,20,43);
 $('#time-label').textContent=t.toFixed(1)+'秒';
}
function renderHistory(){const runs=record(current.id).runs;$('#run-list').innerHTML=runs.length?table(['时间','配置','指标'],runs.map(r=>[r.time,JSON.stringify(r.config),Object.entries(r.metrics).map(([k,v])=>k+': '+fmt(v)).join('；')]),20,'手动保存的实验记录（本机）'):'<p class="muted">还没有实验记录。改变配置后，点击“保存本次实验”建立对照。</p>';}
function download(name,content,type='text/plain;charset=utf-8'){const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function csv(columns,rows){const safe=v=>{let s=v==null?'':String(v);if(typeof v==='string'&&/^[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return String.fromCharCode(0xfeff)+[columns,...rows].map(r=>r.map(safe).join(',')).join(String.fromCharCode(13,10));}
function markdownReport(){
 const p=current,r=record(p.id),lines=[`# ${p.title}：项目报告草稿`,'','> 此文件由本机草稿导出，不代表教师验收。请附当前结果CSV和配置JSON。','',`数据来源：${p.source.url}`,`原始数据SHA-256：${dataset.meta.sha256}`,`许可：${p.source.license}`,''];
 for(const [id,title] of p.stages)lines.push('## '+title,'',r.answers[id]||'待填写','');
 for(const [id,title] of Object.entries(reportFields))lines.push('## '+title,'',r.answers[id]||'待填写','');
 lines.push('## 当前参数','','```json',JSON.stringify(r.config,null,2),'```','','## 实验记录');
 for(const run of r.runs)lines.push('',`### ${run.time}`,'','```json',JSON.stringify(run,null,2),'```');
 lines.push('','## 提交前检查','',...p.acceptance.map(x=>'- [ ] '+x));return lines.join(NL);
}
main.addEventListener('input',e=>{
 if(e.target.dataset.answer&&current){const id=e.target.dataset.answer,r=record(current.id);r.answers[id]=e.target.value;const check=main.querySelector(`[data-check="${id}"]`);if(check){check.disabled=e.target.value.trim().length<20;if(check.disabled){check.checked=false;r.checks[id]=false;}}persist();}
 if(e.target.id==='replay-time')drawReplay(+e.target.value);
});
main.addEventListener('change',async e=>{
 if(!current)return;
 if(e.target.closest('#config-form')){if(!$('#config-form').reportValidity())return;try{record(current.id).config=validConfig(current.id,Object.fromEntries(new FormData($('#config-form'))));persist();runAnalysis();}catch(err){$('#lab-feedback').textContent=err.message;}}
 if(e.target.dataset.check){record(current.id).checks[e.target.dataset.check]=e.target.checked;persist();}
 if(e.target.id==='import-record'){
  const file=e.target.files[0],importProject=current.id;if(!file)return;
  try{
   if(file.size>2000000)throw Error('记录文件不能超过2MB。');
   const value=JSON.parse(await file.text());if(current?.id!==importProject)return;
   if(value.version!==1||value.project!==current.id)throw Error('请选择当前项目导出的版本1记录文件。');
   const cleaned=cleanRecord(current.id,value.record);
   if(!confirm('恢复将替换本项目的本机草稿。继续前请确认已导出需要保留的记录。'))return;
   state.projects[current.id]=cleaned;persist();projectPage(current);$('#import-feedback').textContent='已恢复本项目记录。导入的实验记录仍需自行核查。';
  }catch(err){if(current?.id===importProject&&$('#import-feedback'))$('#import-feedback').textContent='导入失败：'+err.message;}
 }
});
main.addEventListener('submit',e=>e.preventDefault());
main.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.filter){filter=b.dataset.filter;home();$('#projects').scrollIntoView();return;}
 if(b.id==='retry'){route();return;}
 if(!current)return;
 const r=record(current.id);
 if(b.id==='save-run'&&result){r.runs.push({time:new Date().toISOString(),config:{...r.config},metrics:{...result.metrics},sourceSha:dataset.meta.sha256});r.runs=r.runs.slice(-20);persist();renderHistory();$('#lab-feedback').textContent=`已保存实验，当前${r.runs.length}次。最多保留最近20次，请及时导出。`;}
 if(b.id==='export-csv'&&result)download(current.id+'-results.csv',csv(result.exportColumns||result.columns,result.exportRows||result.rows),'text/csv;charset=utf-8');
 if(b.id==='reset-config'){r.config={...DEFAULTS[current.id]};persist();$('#config-form').innerHTML=controls(current,r.config);runAnalysis();}
 if(b.id==='export-report')download(current.id+'-report.md',markdownReport(),'text/markdown;charset=utf-8');
 if(b.id==='export-record')download(current.id+'-experiment.json',JSON.stringify({version:1,project:current.id,exported:new Date().toISOString(),config:r.config,sourceSha:dataset.meta.sha256,record:r},null,2),'application/json');
 if(b.id==='clear-record'&&confirm('清除本项目的草稿与实验记录？其他项目不会受到影响。')){delete state.projects[current.id];persist();projectPage(current);}
 if(b.id==='play'){
  if(replayTimer){stopReplay();b.textContent='播放轨迹';}
  else{b.textContent='暂停回放';replayTimer=setInterval(()=>{const slider=$('#replay-time');let t=+slider.value+.2;if(t>119.9)t=0;slider.value=t;drawReplay(t);},200);}
 }
});
document.addEventListener('visibilitychange',()=>{if(document.hidden){stopReplay();if($('#play'))$('#play').textContent='播放轨迹';}});
async function route(){
 const hash=location.hash.slice(1)||'home';if(hash==='main')return;
 if(/^(lab|start|learn|open|ch0[3-8])$/.test(hash)){location.replace('methods.html#'+hash);return;}
 const [kind,id,section]=hash.split('/');
 if(kind!=='project'){routeToken++;home();if(hash==='projects')$('#projects').scrollIntoView();else window.scrollTo(0,0);return;}
 const p=PROJECTS.find(p=>p.id===id);
 if(!p){routeToken++;current=null;stopReplay();main.innerHTML='<p class="notice">未找到这个项目。<a href="#projects">返回项目目录</a></p>';return;}
 if(current?.id===id&&dataset){if(section)document.getElementById(section)?.scrollIntoView();return;}
 const token=++routeToken;stopReplay();current=null;dataset=null;main.innerHTML='<p class="loading" role="status">正在读取真实数据快照…</p>';
 try{const data=await loadData(p);if(token!==routeToken)return;current=p;dataset=data;document.title=p.title+' · 交通项目实践';projectPage(p);if(section)document.getElementById(section)?.scrollIntoView();else window.scrollTo(0,0);}
 catch(err){if(token!==routeToken)return;main.innerHTML=`<p class="notice">数据未能读取：${esc(err.message)}。请检查网络或下载项目包后通过本地HTTP服务器打开。</p><button id="retry">重试</button>`;}
}
window.addEventListener('hashchange',route);
let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(!current||!$('#plot')||!result)return;if(current.id==='counting')drawReplay(+$('#replay-time').value);else if(current.id==='hotspots')drawSpatial();},100);});
await route();
