(function(){
  'use strict';
  const {esc,fmt,table}=ClassroomLabs, C=ClassroomCore, D=OBSERVATIONS, pages=LESSON.pages;
  const main=document.getElementById('content'),key='traffic-ch2-classroom-v1';
  let storageOK=true,active=-1,present=false;
  let state={notes:{},experiments:[]};
  try{const saved=JSON.parse(localStorage.getItem(key)||'null');if(saved&&typeof saved.notes==='object'&&saved.notes!==null&&Array.isArray(saved.experiments)){state={notes:saved.notes,experiments:saved.experiments.slice(-60)};}}
  catch{storageOK=false;}
  function persist(){try{localStorage.setItem(key,JSON.stringify(state));storageOK=true;}catch{storageOK=false;}document.getElementById('storage-warning').hidden=storageOK;}
  function record(type,parameters,results){
    state.experiments.push({time:new Date().toISOString(),page:pages[active]?.id||'start',type,parameters,results});
    state.experiments=state.experiments.slice(-60);persist();
  }
  function download(name,text,type='text/plain'){
    const blob=new Blob([type.startsWith('text/csv')?'\ufeff':'',text],{type:type+';charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
  }
  function report(){return {course:'交通数据挖掘理论与应用',chapter:2,protocol:D.protocol,classroomVersion:D.version,exportedAt:new Date().toISOString(),
    sourceHashes:D.hashes,scope:'I-94西向ATR 301历史小时资料；NYC事故和SinD轨迹是独立扩展示例，不拼接为同一总体。',
    coreAudit:{rawRows:D.rows.length,uniqueHours:CLASSROOM_MODEL.hours.length,conflicts:CLASSROOM_MODEL.conflicts.length,years:Array.from({length:7},(_,i)=>C.audit(CLASSROOM_MODEL,2012+i))},
    notes:state.notes,experiments:state.experiments,
    limits:['记录仅证明页面计算或代码执行，不代表已经完成后续主项目。','缺测不填0；不重建夏令时；不从交通量直接判断拥堵。','仅保留最近60项课堂操作；Python文字输出最多记入10,000字符，SQL为预览结果。']};}
  function renderReport(el){
    const fields=[['question','交通任务与观测范围','明确断面、方向、时间范围、单位，以及准备支持哪项调查或分析。'],['decision','数据接收与整编意见','依据质量审计说明可接收哪些字段、怎样去重、哪些记录需要核查。'],['limits','使用限制与补充资料','说明缺口、天气多标签、覆盖范围和现有数据不能支持的工程判断。']];
    el.innerHTML=`<h3>我的数据接收说明</h3><p>最近${state.experiments.length}项已计算的交互或代码结果。首次进入可视化实验也会记录默认配置；这不是完成度评分。</p>${fields.map(([id,title,placeholder])=>`<label class="field">${title}<textarea data-note="${id}" maxlength="10000" placeholder="${placeholder}">${esc(state.notes[id]||'')}</textarea></label>`).join('')}<div class="controls"><button class="primary" data-json>导出完整JSON记录</button><button data-md>导出接收说明Markdown</button><button data-clear>清空本课记录</button></div><p class="save-status" role="status"></p><details><summary>查看最近操作和源文件校验</summary>${table(['实验','页面','时间'],state.experiments.slice(-12).reverse().map(r=>[r.type,r.page,r.time]))}<pre>${esc(JSON.stringify(D.hashes,null,2))}</pre></details>`;
    const status=()=>el.querySelector('.save-status').textContent=storageOK?'记录保存在本机浏览器；未上传，可导出备份。':'浏览器未允许保存或空间不足。当前仍可操作，请立即导出记录；关闭页面可能丢失。';status();
    el.querySelectorAll('[data-note]').forEach(t=>t.oninput=()=>{state.notes[t.dataset.note]=t.value;persist();status();});
    el.querySelector('[data-json]').onclick=()=>download('ch02-classroom-record.json',JSON.stringify(report(),null,2),'application/json');
    el.querySelector('[data-md]').onclick=()=>{const r=report();download('ch02-data-acceptance.md',`# 第二章：道路监测数据接收说明\n\n协议：${r.protocol}\n\n导出：${r.exportedAt}\n\n${fields.map(([id,title])=>`## ${title}\n\n${state.notes[id]||'（尚未填写）'}\n`).join('\n')}\n## 来源与质量审计\n\n原始${r.coreAudit.rawRows}行；${r.coreAudit.uniqueHours}个唯一小时；${r.coreAudit.conflicts}个交通量冲突小时。缺测未填0。\n\n\`\`\`json\n${JSON.stringify(r.coreAudit.years,null,2)}\n\`\`\`\n\n## 输入SHA-256\n\n\`\`\`json\n${JSON.stringify(r.sourceHashes,null,2)}\n\`\`\`\n\n## 课堂实验记录\n\n${r.experiments.map(x=>`### ${x.type} (${x.page})\n\n${x.time}\n\n\`\`\`json\n${JSON.stringify({parameters:x.parameters,results:x.results},null,2)}\n\`\`\`\n`).join('\n')}\n## 边界\n\n${r.limits.map(x=>'- '+x).join('\n')}\n`,'text/markdown');};
    el.querySelector('[data-clear]').onclick=()=>{if(!confirm('仅清空第二章课堂的说明与实验记录？第一章和主项目记录不受影响。'))return;state={notes:{},experiments:[]};persist();renderReport(el);};
  }
  window.ClassroomApp={download,renderReport,report};
  function home(){
    const labs=pages.filter(p=>p.lab).length;
    main.innerHTML=`<section class="hero"><p class="eyebrow">CHAPTER 02 / 编程实践基础</p><h1>先把交通数据弄清楚，<br>再让代码给出答案。</h1><p>接收一份道路监测数据，经过数据库查询、Python整编和可视化核查，交付可以用于早高峰调查与交通量预测的数据表。</p><div class="pipeline"><div><small>01 / DEFINE</small><strong>识别交通对象</strong></div><div><small>02 / ORGANIZE</small><strong>组织小时观测</strong></div><div><small>03 / INSPECT</small><strong>检查时空口径</strong></div><div><small>04 / DELIVER</small><strong>交付可信数据</strong></div></div></section><div class="numbers"><div><strong>${pages.length}</strong><span>教学页</span></div><div><strong>${labs}</strong><span>交互与成果模块</span></div><div><strong>48,204</strong><span>真实原始记录</span></div><div><strong>SQL + Python</strong><span>可修改、可执行</span></div></div><p class="lead">一个交通任务贯穿全章：I-94西向ATR 301断面的历史观测，能否直接用于早高峰调查？</p><p>沿用第一章“问题—数据—方法—证据”的思路。本章不急于换模型，而是把观测单元、数据库关系、缺测和单位问题落实到代码、图表与数据接收说明。</p><div class="controls"><a class="button primary" href="#mission">进入交互课堂</a><a class="button" href="#sql">直接体验SQL</a><a class="button" href="#python">直接体验Python</a><a class="button" href="../#project/ch02/code">完整项目工作本</a></div><div class="cards">${LESSON.sections.map(([id,title,desc,minutes])=>`<a class="card" href="#${id}"><small>${id} / 约${minutes}分钟</small><h2>${title}</h2><p>${desc}</p><span>进入这一节 →</span></a>`).join('')}</div><div class="takeaway"><b>上课建议</b><p>90分钟主线：数据库25分钟，Python处理30分钟，可视化20分钟，复现与交付15分钟。另留45分钟上机，修改SQL、Python并完成数据接收说明。课堂投影按页切换，编辑代码时方向键仍用于移动光标。</p></div><h2>本课怎样连接后续章节？</h2><p>整编出40,575个唯一小时，第三章进一步形成358个完整早高峰日期；第六章保留小时骨架与缺口进行多提前量预测。事故坐标和天津轨迹分别作为第五、八章的工具预习，数据来源不混用。</p><p><a href="#handoff">查看第二至八章实践衔接 →</a></p><div class="feedback warn"><b>离线与联网边界</b><br>课文、真实数据、可视化和SQL随离线资料包提供。Python首次使用需点击加载在线环境；也可用资料包内脚本在本地Python运行。无注册、无商业报名、不上传课堂操作记录。</div><p class="source-note">数据：UCI / John Hogue (2019)，Metro Interstate Traffic Volume，CC BY 4.0。原始行、唯一小时和缺口不是同一概念。本课解释遵守原始本地时间标签，不恢复夏令时。</p>`;
  }
  function route(){
    let hash;try{hash=decodeURIComponent(location.hash.slice(1)||'start');}catch{hash='start';}if(hash==='content'){main.focus();return;}
    ClassroomRuntimes.cancelBusy();
    if(LESSON.sections.some(s=>s[0]===hash))hash=pages.find(p=>p.section===hash).id;
    active=pages.findIndex(p=>p.id===hash);
    if(active<0){if(hash!=='start')location.replace('#start');home();}
    else{
      const p=pages[active],siblings=pages.filter(x=>x.section===p.section),s=LESSON.sections.find(s=>s[0]===p.section);
      main.innerHTML=`<p class="eyebrow">${esc(p.tag)}</p><h1>${esc(p.title)}</h1><p class="lead">${esc(p.lead)}</p><nav class="step-links" aria-label="本节教学页">${siblings.map((x,i)=>`<a href="#${x.id}" class="${x.id===p.id?'active':''}" ${x.id===p.id?'aria-current="page"':''}>${s[0]} · ${i+1}</a>`).join('')}</nav><div class="body-lines">${p.body.map(t=>`<p>${esc(t)}</p>`).join('')}</div>${p.lab?`<section class="lab"><p class="lab-label">INTERACTIVE / ${esc(s[1])}</p><div id="experiment"></div></section>`:''}<p class="prompt">课堂追问：${esc(p.question)}</p><div class="takeaway"><b>本页要点</b><br>${esc(p.takeaway)}</div><p class="source-note">${['coordinates'].includes(p.id)?'扩展数据：NYC Open Data 2024年1月事故快照；坐标示意不是风险或道路真值。':p.id==='trajectory'?'扩展数据：SinD天津8_2_1，120秒快照中的3个源ID；提供方平滑轨迹，遵守原许可非商业限制。':'主线数据：UCI Metro Interstate Traffic Volume，I-94西向ATR 301断面；使用课程固定真实快照。'} <a href="README.md">数据、许可与运行说明</a></p>`;
      if(p.lab)ClassroomLabs.mount(p.lab,document.getElementById('experiment'),record);
    }
    document.title=(active<0?'第2章 编程实践基础':pages[active].title)+' · 交通数据挖掘开放课堂';
    document.getElementById('nav').innerHTML=`<a class="chapter-link ${active<0?'active':''}" href="#start"><b>课堂首页</b>道路监测数据接收</a>`+LESSON.sections.map(([id,title])=>`<a class="chapter-link ${pages[active]?.section===id?'active':''}" href="#${id}"><b>${id} ${title}</b>${pages.filter(p=>p.section===id).length}个教学页</a>`).join('');
    document.getElementById('page-label').textContent=active<0?'课堂首页':`${active+1} / ${pages.length} · ${pages[active].section}`;
    document.getElementById('prev').disabled=active<0;document.getElementById('next').disabled=active===pages.length-1;
    window.scrollTo(0,0);
  }
  function move(delta){const next=active+delta;location.hash=next<0?'start':pages[Math.min(next,pages.length-1)].id;}
  function projection(value){present=value;document.body.classList.toggle('present',present);document.getElementById('exit').hidden=!present;document.getElementById('present').textContent=present?'退出投影':'课堂投影';document.getElementById('present').setAttribute('aria-pressed',String(present));if(present&&active<0)location.hash=pages[0].id;}
  document.getElementById('prev').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);
  document.getElementById('present').onclick=()=>projection(!present);document.getElementById('exit').onclick=()=>projection(false);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){projection(false);return;}if(!present||document.querySelector('dialog[open]')||e.target.closest('input,textarea,select,button,a,[contenteditable]'))return;if(['ArrowRight','PageDown'].includes(e.key)){e.preventDefault();move(1);}else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();move(-1);}});
  const dialog=document.getElementById('source-dialog');
  document.getElementById('source-body').innerHTML=`<h3>教材结构与教学范围</h3><p>按第二章“编程实践基础”的2.1数据库、2.2 Python数据处理、2.3可视化、2.4实践环境组织。课堂活动另行编写，不改动书稿，不把工具演示冒充后续模型项目。</p><h3>真实数据与署名</h3><p><a href="https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume" target="_blank" rel="noopener">John Hogue (2019), UCI Metro Interstate Traffic Volume</a>，DOI:10.24432/C5X60B，CC BY 4.0。原始CSV48,204行，核查后40,575个唯一小时；本地标签不重建夏令时。完整原始CSV随资料包提供。</p><p><a href="https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95" target="_blank" rel="noopener">NYC Open Data事故记录</a>：2024年1月7,542条，采用既有课程7,068个有效坐标。不补造位置，遵守原始使用条款。</p><p><a href="https://github.com/SOTIF-AVLab/SinD" target="_blank" rel="noopener">SOTIF-AVLab / SinD</a>：固定提交930e4dea78d924c6e9a58ff8e378331f93bba8ec，天津8_2_1前120秒中3个源ID；位置已由提供方平滑。自定义非商业许可见<a href="data/SIND-LICENSE.txt">随附原文</a>。</p><h3>代码运行与隐私</h3><p>SQL使用固定sql.js 1.14.2（MIT），以本机SQLite执行，不连接外部数据库。Python使用固定Pyodide 0.29.3，点击运行才向jsDelivr请求环境与NumPy、Pandas。运行在浏览器工作线程中，默认代码不上传数据；不要在公共课堂代码中粘贴密钥或敏感信息。</p><p>执行有停止按钮和时限。SQL每次从固定数据副本开始，Python每次重建输入；网页展示结果不是预先写好的答案。离线模式不保证Python环境可用，可改用附带本地脚本。第三方网络故障不会阻止其他实验。</p><h3>许可与复现</h3><p>课程原创代码MIT、原创讲解CC BY-SA 4.0；第三方数据和运行时遵守各自许可。来源与SHA-256见<a href="data/manifest.json">数据清单</a>，具体步骤见<a href="README.md">README</a>。冲突注入和坐标交换均为明确标注的错误对照，不进入真实成果。</p>`;
  document.getElementById('sources').onclick=()=>dialog.showModal();document.getElementById('close').onclick=()=>dialog.close();
  document.getElementById('storage-warning').hidden=storageOK;
  window.addEventListener('hashchange',route);window.addEventListener('pagehide',()=>ClassroomRuntimes.cancelBusy());route();
})();
