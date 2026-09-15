/* MIT. Classroom tasks use the same protocols and frozen evidence as chapters 2-8. */
window.TRAFFIC_CLASSROOM = (() => {
 'use strict';
 const B=window.PROJECT_BRIDGE;
 const ROOT=location.protocol==='file:'?'https://lilinchao.github.io/traffic-book-practice/open-course/':'../';
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const $=(q,r)=>r.querySelector(q);
 const project=id=>B.projects.find(p=>p.id===id);
 const link=(id,tab='overview')=>ROOT+'#project/'+id+'/'+tab;
 const resource=p=>ROOT+p;
 const MISSIONS=[
  {id:'corridor',title:'早高峰监测与预测',service:'道路运行监测与调查资源安排',chapters:['ch02','ch03','ch06'],source:'I-94西向ATR301单断面小时交通量',
   problem:'监测记录如何形成可信的早高峰调查基准，并支持提前1、3或6小时的运行准备？',
   object:'固定方向、固定断面；抽样以日期为单位，预测以目标小时为单位。',measure:'2017年07-09时平均交通量及其不确定性；2018年7-9月目标小时交通量，单位均为辆/小时。',
   missing:'缺少速度、占有率和排队资料，不能仅由断面交通量判断拥堵等级或制定信号配时。',
   task:'先完成数据审计，再独立讨论调查精度与预测时效；两项实验使用不同年份，不能混用分母。',
   outcome:'断面监测数据接收意见、调查方案与高峰预测适用性说明',caseId:'forecast-origin',slide:'baseline'},
  {id:'bike',title:'共享单车高峰服务准备',service:'共享单车运营分析',chapters:['ch04'],source:'Capital Bikeshare系统小时租借记录',
   problem:'在给定日历与天气条件下，如何估计系统小时租借量，并识别早晚高峰的低估问题？',
   object:'系统小时租借次数，不是单个站点库存，也不是所有潜在骑行需求。',measure:'2012年下半年4376个测试小时；租借量为次/小时，单独核查07-09时与16-18时。',
   missing:'站点可用车、空桩、调运和未满足需求均未观测，不能把预测低估量直接当作需要调入的车辆数。',
   task:'审查输入何时可获得，再用OLS、泊松与NB2在同一时间切分上比较；天气实测不冒充事前预报。',
   outcome:'高峰服务量估计、分时段误差与站点补充调查清单',caseId:'bike-leakage',slide:'service'},
  {id:'safety',title:'道路事故候选地点排查',service:'道路交通安全排查',chapters:['ch05'],source:'纽约2024年1月道路事故公开记录',
   problem:'排查人力有限时，哪些有记录区域值得优先核查，定位缺失又会遗漏哪些证据？',
   object:'事故事件与候选范围；网格或聚类边界不直接等于道路、路口或行政责任范围。',measure:'7542条事故中7068个位置可用；固定500米网格，并比较KDE带宽和DBSCAN邻域。',
   missing:'缺少交通暴露量、完整路网与现场设施信息，事故集中不等于单位暴露风险更高，更不证明治理效果。',
   task:'先审计能否落图，再比较网格、核密度与密度聚类，最后为至少3处候选范围列现场核查问题。',
   outcome:'候选点位清单、定位质量审计与现场调查任务',caseId:'no-coordinates',slide:'safety'},
  {id:'taxi',title:'出租车分区与夜间运营',service:'分区域出租车服务研判',chapters:['ch07'],source:'纽约2024年1月绿出租车上车记录',
   problem:'不同地区的上车活动如何随时段变化，哪些典型服务日值得分别复盘？',
   object:'已实现的绿出租车服务记录；四区域预测与七类地区日画像是两种不同统计对象。',measure:'留出预测为4区域×7天×24小时=672单元；日型聚类为31日×168维地区-小时占比。',
   missing:'没有候车时间、车辆可用性和未成单需求，不能用记录多少直接宣布供需缺口或车辆增配数量。',
   task:'将AR/VAR留出预测与全月KMeans日型分析分开，既看地区误差，也核查聚类稳定性。',
   outcome:'分区运营研判、典型日画像与需求调查假设',caseId:'weekday-denominator',slide:'taxi'},
  {id:'pedestrian',title:'夜间步行交通调查',service:'基于影像的分方向通行调查',chapters:['ch08'],source:'MOT17-04夜间街道影像；SinD天津地面轨迹为另一独立实验',
   problem:'夜间遮挡与身份中断，会怎样传递为断面通行量的漏计和误计？',
   object:'同一匿名目标穿过指定计数线的事件，不是累计检测框或全部出现在画面中的人数。',measure:'MOT17共35秒、1050帧；参考事件来自提供方人工框/ID。SinD位置为米，影像位置为像素，不能拼接。',
   missing:'画面缺少地面尺度与更长调查时段，不能推断行人速度、道路通行能力或小时设计流量。',
   task:'由YOLOX检测、运动预测与一对一关联形成事件，再对照独立标注逐事件回看，不以总数相等证明准确。',
   outcome:'分方向事件清单、误计漏计复核与调查适用性说明',caseId:'trajectory-not-video',slide:'night-video'}
 ];
 const fields=[['object','研究对象与时空范围'],['question','具体交通问题与预期用途'],['indicator','指标、单位及数据字段'],['sources','至少两种真实来源的适配比较与许可'],['method','拟采用的方法与评价证据'],['limits','缺少的数据与不能下的结论']];
 const storageKey='traffic-ch1-project-brief-v1';
 function readDrafts(){try{const x=JSON.parse(localStorage.getItem(storageKey));return x&&x.version===1&&x.drafts&&typeof x.drafts==='object'&&!Array.isArray(x.drafts)?x:{version:1,selected:'corridor',drafts:{}};}catch{return {version:1,selected:'corridor',drafts:{}};}}
 function saveDrafts(value){try{localStorage.setItem(storageKey,JSON.stringify(value));return true;}catch{return false;}}
 function download(name,content,type='text/markdown;charset=utf-8'){
  const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function bridge(ids,task=''){
  return `<aside class="practice-bridge" aria-label="后续章节实践"><p class="bridge-label">从本课问题走向章节项目</p>${task?`<p>${esc(task)}</p>`:''}<div class="bridge-grid">${ids.map(id=>{const p=project(id);return `<div><a href="${link(id)}"><strong>第${p.chapter}章 · ${esc(p.title)}</strong></a><p>${esc(p.protocol.required.join(' / '))}</p><a href="${link(id,'code')}">进入代码实验</a> · <a href="${link(id,'cases')}">阅读交通案例</a></div>`;}).join('')}</div></aside>`;
 }
 function home(){return `<section class="mission-home"><p class="eyebrow">交通问题 / 工程证据 / 章节实践</p><h2>选择一个交通任务，沿着证据继续研究</h2><p>下面是五个独立交通场景，不是同一城市的数据拼接。第一章完成问题定义；后续章节回答“怎样计算、怎样验证、交付什么”。</p><div class="mission-grid">${MISSIONS.map((m,i)=>{
  const index=window.LESSON.slides.findIndex(s=>s.lab===m.slide);
  return `<a class="mission-card" href="#s${index}"><span class="mission-number">0${i+1} / ${esc(m.service)}</span><h3>${esc(m.title)}</h3><p>${esc(m.problem)}</p><small>${m.chapters.map(id=>'第'+project(id).chapter+'章').join(' → ')} · 任务与算法相连</small></a>`;
 }).join('')}</div><div class="controls"><a class="download" href="#plan">填写本课研究方案</a><a href="#pathways">查看八章实践路径</a></div></section>`;}
 function brief(root){
  const state=readDrafts();let current=MISSIONS.find(m=>m.id===state.selected)||MISSIONS[0];
  function draw(){
   const draft=state.drafts[current.id]||{};
   root.innerHTML=`<p class="lab-label">本课交付 / 一页交通问题定义书</p><h3>把课堂观察写成可执行的研究方案</h3><label>选择交通任务<select data-mission>${MISSIONS.map(m=>`<option value="${m.id}"${m.id===current.id?' selected':''}>${esc(m.title)}</option>`).join('')}</select></label><div class="mission-context"><strong>${esc(current.service)}</strong><p>${esc(current.problem)}</p><dl><dt>真实数据</dt><dd>${esc(current.source)}</dd><dt>观测对象</dt><dd>${esc(current.object)}</dd><dt>指标提示</dt><dd>${esc(current.measure)}</dd><dt>工程边界</dt><dd>${esc(current.missing)}</dd></dl></div><div class="brief-fields">${fields.map(([key,title])=>`<label>${title}<textarea name="${key}" rows="3" maxlength="3000" placeholder="结合上面的交通任务，用自己的语言说明">${esc(typeof draft[key]==='string'?draft[key]:'')}</textarea></label>`).join('')}</div><div class="controls"><button data-brief-check>检查填写完整性</button><button class="primary" data-brief-export>导出研究方案 Markdown</button><button data-brief-reset>清除本任务草稿</button></div><p data-brief-status role="status" class="subtle">草稿仅保存在本浏览器；跨设备前请导出。不上传、不评分，也不自动判断研究结论是否正确。</p>${bridge(['ch01',...current.chapters],current.task)}<p class="subtle">导出内容可用于第1章项目的问题定义书；后续各章沿用其中的问题、单位与边界，按各章要求另交实验结果。不自动写入已有项目笔记。</p>`;
   $('[data-mission]',root).onchange=e=>{current=MISSIONS.find(m=>m.id===e.target.value);state.selected=current.id;saveDrafts(state);draw();};
   const capture=()=>{state.drafts[current.id]=Object.fromEntries(fields.map(([key])=>[key,$(`[name="${key}"]`,root).value]));return state.drafts[current.id];};
   const persist=()=>{capture();$('[data-brief-status]',root).textContent=saveDrafts(state)?'已在本机保存当前任务草稿；这不是自动评分。':'本机存储不可用，草稿只保留在当前页面，请立即导出。';};
   root.querySelectorAll('textarea').forEach(e=>e.addEventListener('input',persist));
   $('[data-brief-check]',root).onclick=()=>{const draft=capture(),missing=fields.filter(([k])=>!draft[k].trim()).map(([,name])=>name);$('[data-brief-status]',root).textContent=missing.length?'尚未填写：'+missing.join('、')+'。':`${fields.length}项内容已填写。请人工复核对象、单位、信息可用性和结论边界；完整不代表正确。`;};
   $('[data-brief-export]',root).onclick=()=>{
    const draft=capture();saveDrafts(state);
    const content=`# 第1章交通问题定义书：${current.title}\n\n> 学生研究方案草稿，不是已实施工程成果。\n\n数据：${current.source}\n\n`+fields.map(([k,title])=>`## ${title}\n\n${draft[k].trim()||'待填写'}\n`).join('\n')+`\n## 后续实验与交付\n\n${current.task}\n\n`+['ch01',...current.chapters].map(id=>{const p=project(id);return `- 第${p.chapter}章：${p.title}；协议 ${p.protocol.id}。\n  交付：${p.protocol.deliverables.join('；')}。\n  https://lilinchao.github.io/traffic-book-practice/open-course/#project/${id}/code`;}).join('\n')+`\n\n## 使用边界\n\n${current.missing}\n`;
    download('ch01-'+current.id+'-问题定义书.md',content);
   };
   $('[data-brief-reset]',root).onclick=()=>{delete state.drafts[current.id];saveDrafts(state);draw();};
  }draw();
 }
 function pathways(root){
  root.innerHTML=`<p class="lab-label">八章实践 / 当前主实验协议</p><h3>每章接着解决什么交通问题？</h3><label>按交通任务查看<select data-path-filter><option value="all">全部八章</option>${MISSIONS.map(m=>`<option value="${m.id}">${esc(m.title)}</option>`).join('')}</select></label><div data-path-cards></div><p class="subtle">第2、3、6章沿用同一道路数据，但统计总体和时间范围不同。自行车、出租车、事故和视频案例来自其他场景，不拼接成一个虚构项目。</p>`;
  function draw(){const id=$('[data-path-filter]',root).value,m=MISSIONS.find(m=>m.id===id);const ps=m?B.projects.filter(p=>p.id==='ch01'||m.chapters.includes(p.id)):B.projects;
   $('[data-path-cards]',root).innerHTML=ps.map(p=>`<article class="path-card"><div class="path-index">${String(p.chapter).padStart(2,'0')}</div><div><p class="bridge-label">${esc(p.chapterName)}</p><h4>${esc(p.title)}</h4><dl><dt>本章解决</dt><dd>${esc(p.protocol.tasks[0][1])}</dd><dt>主实验方法</dt><dd>${esc(p.protocol.required.join('；'))}</dd><dt>观察单位</dt><dd>${esc(p.protocol.unit)}</dd><dt>共同口径</dt><dd>${esc(p.protocol.population)}</dd><dt>交付成果</dt><dd>${esc(p.protocol.deliverables.join('；'))}</dd></dl><div class="controls"><a class="download" href="${link(p.id)}">查看项目任务</a><a href="${link(p.id,'code')}">代码与分步工作本</a><a href="${ROOT}#case/${p.cases[0].id}">交通研究案例</a></div><small>主实验协议：${esc(p.protocol.id)}</small></div></article>`).join('');
  }$('[data-path-filter]',root).onchange=draw;draw();
 }
 function service(root,{graph,table,fmt}){
  const features=[['calendar','日历与钟点','可事先确定，可作为模型输入。',true],['weather','当小时实测天气','仅适用于已知天气条件的估计；做事前预测须换成当时已发布的预报并重新评价。',true],['casual','当小时非注册用户租借量 casual','这是总租借量的组成项，事后才知道，不应作为输入。',false],['registered','当小时注册用户租借量 registered','与casual相加即为目标cnt，使用它会造成标签泄漏。',false]];
  root.innerHTML=`<p class="lab-label">共享单车运营 / 真实4376测试小时</p><h3>低估高峰租借量，就该调入同样数量的车吗？</h3><p>先检查估计时能知道什么，再解释模型误差。这里估计系统租借次数，不直接作站点调运决策。</p><fieldset class="feature-check"><legend>哪些字段可以用于本章“给定天气条件”的小时估计？</legend>${features.map(([id,title])=>`<label><input type="checkbox" value="${id}"> ${esc(title)}</label>`).join('')}</fieldset><button data-feature-check>核对信息边界</button><div data-feature-result class="feedback" role="status" hidden></div><label>核查服务时段<select data-service-period><option value="all">全日</option><option value="morning">早高峰07-09时</option><option value="evening">晚高峰16-18时</option><option value="night">夜间00-05时</option></select></label><div data-service-chart></div><div data-service-table></div><p class="subtle">共同时间切分：2011年训练、2012年上半年验证、下半年测试。NB2参数仅由验证期选；网页按已计算的逐小时预测重新分组，不重新训练。</p><div class="feedback">平均偏差=预测−观测，负值表示整体低估；MAE是平均绝对误差。“低估小时数”不是缺车次数。调运还需站点库存、空桩、调运成本和未满足需求。</div>`;
  $('[data-feature-check]',root).onclick=()=>{const chosen=new Set([...root.querySelectorAll('input:checked')].map(e=>e.value));const box=$('[data-feature-result]',root);box.hidden=false;box.textContent=features.map(([id,title,note,yes])=>(chosen.has(id)===yes?'判断符合本任务：':'请再核对：')+title+'。'+note).join('\n');};
  function draw(){const rows=B.bike.periods[$('[data-service-period]',root).value];graph($('[data-service-chart]',root),{labels:rows.map(r=>r.model),series:[{name:'共同测试时段MAE',values:rows.map(r=>r.mae),color:'#087e82'}],bars:true,unit:'次/小时',title:'系统小时租借量估计误差'});$('[data-service-table]',root).innerHTML=table([['模型','测试小时','MAE（次/小时）','平均偏差（次/小时）','低估小时数'],...rows.map(r=>[r.model,r.n,fmt(r.mae,1),fmt(r.bias,1),r.underestimated])]);}
  $('[data-service-period]',root).onchange=draw;draw();
 }
 function safety(root){
  const choices=[['错误口径','只把7068个有效位置放进分母，并把点最多的范围称为最危险路口。','7542条事故中有474条无法按当前规则落图。只看地图会忽略这部分事件；还没有道路几何与交通暴露量，不能直接判断路口风险。'],['可执行排查','保留7542条记录的审计，标明7068个有效点，以事故集聚生成待核查的候选范围。','这个方案能支持候选范围筛查：比较500米网格、KDE及DBSCAN，再为至少3处候选范围列出位置、依据、暴露量缺口与现场设施核查问题。'],['因果跳跃','选出事故最多的网格，就直接认定信号配时导致事故并修改配时。','事故空间分布不能单独识别成因。还需要冲突类型、流量、设施、信号与治理前后对照等证据，不能由热图直接推出措施效果。']];
  root.innerHTML=`<p class="lab-label">道路安全排查 / 真实事故记录口径</p><h3>地图没画出来的事故，能从排查任务中消失吗？</h3><div class="stats"><span>原始事故<strong>7542</strong></span><span>有效位置<strong>7068</strong></span><span>不能落图<strong>474</strong></span></div><p>有效坐标覆盖率为${(7068/7542*100).toFixed(1)}%。该比例只描述位置资料覆盖，不是热点识别准确率，也不是道路安全水平。</p><fieldset class="feature-check"><legend>你会向现场排查人员提交哪种任务？</legend>${choices.map((r,i)=>`<label><input name="safety-plan" type="radio" value="${i}"> ${esc(r[1])}</label>`).join('')}</fieldset><div data-safety-result class="feedback" role="status" hidden></div><p class="subtle">课堂先确定“排查什么”；第5章再计算“候选范围如何随尺度变化”。现场道路名称与管理对象必须复核，不能给网格编造一个路口名。</p>`;
  root.addEventListener('change',e=>{if(e.target.name!=='safety-plan')return;const box=$('[data-safety-result]',root);box.hidden=false;box.textContent=choices[+e.target.value][2];box.className='feedback'+(e.target.value==='1'?'':' warn');});
 }
 const period=(h,key)=>key==='all'||(key==='morning'?h>=7&&h<=9:key==='evening'?h>=16&&h<=18:key==='night'?h<=5:h===+key);
 function forecast(root,{graph,table,fmt}){
  root.innerHTML=`<p class="lab-label">道路运行准备 / 与第6章相同的2169目标</p><h3>提前多久准备，误差集中在哪里？</h3><p>预测I-94西向单断面目标小时交通量，不把交通量直接解释为拥堵等级。先看周期基线，再选看第6章时序模型。</p><div class="controls"><label>运行准备提前量<select data-horizon><option value="1">1小时</option><option value="3">3小时</option><option value="6">6小时</option></select></label><label>关注时段<select data-forecast-period><option value="all">全日</option><option value="morning">早高峰07-09时</option><option value="evening">晚高峰16-18时</option><option value="night">夜间00-05时</option></select></label><label><input type="checkbox" data-advanced> 同时查看第6章ARIMA / SARIMA</label></div><p data-origin class="subtle"></p><div data-forecast-chart></div><div data-forecast-table></div><div data-forecast-feedback class="feedback" role="status"></div><details><summary>同一目标时刻的观测与预测示例</summary><div data-forecast-examples></div></details><button data-forecast-export>下载当前对照的逐小时CSV</button><p class="subtle">2017年拟合，2018年上半年验证，7-9月测试；1/3/6小时始终使用相同2169目标。基线取课程冻结值（保留3位小数），ARIMA/SARIMA来自实际拟合结果。筛选只重新计算评价，不训练模型。旧6533小时入门比较和2190小时补充接口不参与本表排名。</p>`;
  function selected(){const h=+$('[data-horizon]',root).value,key=$('[data-forecast-period]',root).value,columns=[['星期×小时历史均值',2],['上周同期',3]];if($('[data-advanced]',root).checked)columns.push(['ARIMA',4+[1,3,6].indexOf(h)*2],['SARIMA',5+[1,3,6].indexOf(h)*2]);return {h,columns,rows:B.forecast.rows.filter(r=>period(+r[0].slice(11,13),key))};}
  function draw(){const {h,columns,rows}=selected();const summary=columns.map(([name,c])=>{const e=rows.map(r=>r[c]-r[1]);return {name,mae:e.reduce((s,v)=>s+Math.abs(v),0)/e.length,bias:e.reduce((s,v)=>s+v,0)/e.length};});
   $('[data-origin]',root).textContent=`例如目标为08:00，${h}小时提前量的起点为${String(8-h).padStart(2,'0')}:00。只能使用起点及此前已收到的信息。当前共同目标 ${rows.length} 个小时。`;
   graph($('[data-forecast-chart]',root),{labels:summary.map(r=>r.name),series:[{name:'相同目标MAE',values:summary.map(r=>r.mae),color:'#087e82'}],bars:true,title:'断面小时交通量的共同目标预测误差'});
   $('[data-forecast-table]',root).innerHTML=table([['方法','共同小时','MAE（辆/小时）','偏差（辆/小时）'],...summary.map(r=>[r.name,rows.length,fmt(r.mae,1),fmt(r.bias,1)])]);
   const sample=rows.slice(0,6);$('[data-forecast-examples]',root).innerHTML=table([['目标本地时刻','观测（辆/小时）',...columns.map(r=>r[0])],...sample.map(r=>[r[0].replace('T',' '),r[1],...columns.map(([,c])=>fmt(r[c],1))])]);
   $('[data-forecast-feedback]',root).textContent='先确认目标、时段与信息边界相同，再比较误差。周期基线在1/3/6小时下数值不变，因为日历可预先确定、上周观测早已可用；它们不会随起点更新。ARIMA/SARIMA会使用不同起点的状态。误差更小也不等于可以直接给出拥堵预警或信号方案。';
  }
  root.addEventListener('change',draw);$('[data-forecast-export]',root).onclick=()=>{const {h,columns,rows}=selected();download('ch01-ch06-h'+h+'-forecast.csv','\uFEFF'+[['target_time','actual',...columns.map(r=>r[0])],...rows.map(r=>[r[0],r[1],...columns.map(([,c])=>r[c])])].map(r=>r.join(',')).join('\r\n'),'text/csv;charset=utf-8');};draw();
 }
 function nightVideo(root,{table,cleanups}){
  root.innerHTML=`<p class="lab-label">真实夜间街道 / 独立标注 / 第8章同源结果</p><h3>参考计数15次，模型也数出15次，就合格了吗？</h3><p>MOT17-04提供35秒夜间步行街视频。这里调查画面计数线的分方向通行事件，不推断地点的小时需求或通行能力。</p><button data-night-load class="primary">加载真实夜间视频（约12.6MB）</button><div data-night-player></div><div class="controls"><label>查看已计算的检测阈值<select data-night-threshold><option value="0.35">0.35</option><option value="0.6">0.60</option></select></label><button data-night-reveal>揭示逐事件核验结果</button></div><div data-night-counts class="stats" role="status"></div><div data-night-evidence hidden></div><p data-night-status class="subtle" role="status"></p><p class="subtle">视频为官方压缩视频的同帧序H.264播放副本；推理读取原文件。来源MOTChallenge，Milan等；数据与衍生视频CC BY-NC-SA 3.0，模型Apache-2.0。参考事件由提供方人工框与ID按同一计数规则导出，不是本课重新人工标注。网页只展示冻结结果，不现场执行YOLOX。</p><p><a href="${resource('chapters/VIDEO_LESSON.md')}">查看完整协议、来源与许可</a> · <a href="${link('ch08','code')}">进入第8章逐帧标注与代码实验</a></p>`;
  let revealed=false;
  function draw(){const key=$('[data-night-threshold]',root).value,r=B.video.runs[key],m=r.metrics;$('[data-night-counts]',root).innerHTML=`<span>参考通过事件<strong>${m.reference_events}</strong>次</span><span>模型通过事件<strong>${m.predicted_events}</strong>次</span>`;
   const box=$('[data-night-evidence]',root);box.hidden=!revealed;box.innerHTML=table([['逐事件结果','数量','交通调查含义'],['正确匹配',m.event_TP,'身份、方向、时差满足独立匹配规则'],['误计',m.event_FP,'预测事件没有对应参考事件'],['漏计',m.event_FN,'参考事件未得到对应预测事件']])+`<div class="feedback">${key==='0.35'?'15=15掩盖了2次误计与2次漏计，误差在总数上恰好抵消。':'提高阈值后总数为11次，仍有1次误计和5次漏计，不能只看检测框“更干净”。'}完整调查还要核查方向、时刻、身份关联和规则是否一致。</div><button data-night-seek>回看约14.17秒的参考漏计附近</button><p class="subtle">本页计数线仅辅助定位，不叠加目标框。无法仅凭这里的裸视频确定是哪位行人；第8章提供人工框/ID与模型轨迹的逐帧对照。</p>`;
   $('[data-night-seek]',root).onclick=()=>{const video=$('video',root);if(!video||video.readyState<1){$('[data-night-status]',root).textContent='请先加载视频，等待元数据就绪后再定位。';return;}video.pause();video.currentTime=13.5;$('[data-night-status]',root).textContent='已暂停在13.5秒，向后观察14.17秒附近；具体目标与匹配证据请到第8章核查。';};
  }
  $('[data-night-reveal]',root).onclick=()=>{revealed=true;draw();};$('[data-night-threshold]',root).onchange=draw;
  $('[data-night-load]',root).onclick=()=>{const button=$('[data-night-load]',root);button.disabled=true;button.textContent='视频已加载，可使用播放器控制';$('[data-night-player]',root).innerHTML=`<div class="night-frame"><video controls playsinline preload="metadata" aria-label="MOT17-04真实夜间街道视频" src="${resource('chapters/data/video/mot17-04-web.mp4')}"></video><div class="count-line"><span>计数线 y=300像素</span></div></div>`;const video=$('video',root);video.onerror=()=>{$('[data-night-status]',root).textContent='视频暂时无法加载。其他交互仍可使用；可通过下方第8章入口或官方来源查看。';button.disabled=false;button.textContent='重新加载视频';};cleanups.push(()=>{video.pause();video.removeAttribute('src');video.load();});};draw();
 }
 const labs={brief,pathways,service,safety,baseline:forecast,'night-video':nightVideo};
 return {MISSIONS,bridge,home,link,resource,mount:(root,key,helpers)=>labs[key](root,helpers),labNames:Object.keys(labs)};
})();
