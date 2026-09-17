import {COURSES} from './later.js';
import {INPUTS,controls,defaults,codeExample} from './engine.mjs';
import {esc,fmt,plot,mapPlot,table} from './plots.mjs';
import {toCSV} from '../chapters/engine.mjs';
const chapter=+document.body.dataset.chapter,course=COURSES[chapter],main=document.querySelector('main');
const base=new URL('../',import.meta.url),engine=new URL('engine.mjs',import.meta.url).href;
let data=null,manifest=null,active=-1,present=false,worker=null,timer=null,blobURL=null,loading=null,token=0,storageOK=true;
const key=`traffic-classroom-${chapter}-20260917`;let notes={},records=[];
try{const v=JSON.parse(localStorage.getItem(key)||'{}');if(v.notes&&typeof v.notes==='object')notes=v.notes;if(Array.isArray(v.records))records=v.records.slice(-50);}catch{storageOK=false;}
function persist(){try{localStorage.setItem(key,JSON.stringify({notes,records}));storageOK=true;}catch{storageOK=false;}document.querySelector('#storage').hidden=storageOK;}
function download(name,content,type='text/plain'){const u=URL.createObjectURL(new Blob([content],{type:type+';charset=utf-8'})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000);}
async function loadData(){if(data)return data;if(loading)return loading;loading=(async()=>{const d={};for(const [k,path] of Object.entries(INPUTS[chapter])){const r=await fetch(new URL(path,base));if(!r.ok)throw Error(`读取数据失败（${r.status}）：${path}`);d[k]=await r.json();}const r=await fetch(new URL('classrooms/manifest.json',base));if(!r.ok)throw Error('无法读取来源清单');manifest=await r.json();data=d;return d;})();try{return await loading;}finally{loading=null;}}
function stop(){if(worker)worker.terminate();worker=null;clearTimeout(timer);if(blobURL)URL.revokeObjectURL(blobURL);blobURL=null;}
function compute(id,config,code){return new Promise((resolve,reject)=>{
 stop();blobURL=URL.createObjectURL(new Blob([`import {runLab} from ${JSON.stringify(engine)};onmessage=e=>{try{const {id,config,data,code}=e.data;let result;if(code){const lines=[];let length=0;const print=x=>{const s=typeof x==='string'?x:JSON.stringify(x,null,2);length+=s.length;if(length>100000)throw Error('输出超过100000字符，请缩小预览');lines.push(s);};new Function('data','runLab','print','"use strict";\\n'+code)(data,runLab,print);result={text:lines.join('\\n')};}else result=runLab(id,data,config);postMessage({result});}catch(e){postMessage({error:e.message});}};`],{type:'text/javascript'}));
 worker=new Worker(blobURL,{type:'module'});worker.onmessage=e=>{stop();e.data.error?reject(Error(e.data.error)):resolve(e.data.result);};worker.onerror=e=>{stop();reject(Error(e.message||'计算线程加载失败'));};timer=setTimeout(()=>{stop();reject(Error('计算超过20秒，已停止。可修改参数后重试。'));},20000);worker.postMessage({id,config,data,code});
});}
const control=(f)=>`<label>${esc(f.label)}${f.options?`<select name="${f.key}">${f.options.map(o=>{const [v,label]=Array.isArray(o)?o:[o,o];return `<option value="${esc(v)}" ${String(v)===String(f.value)?'selected':''}>${esc(label)}</option>`;}).join('')}</select>`:`<input name="${f.key}" type="number" min="${f.min}" max="${f.max}" step="${f.step||1}" value="${f.value}" required>`}</label>`;
async function mountLab(page,root,myToken){
 root.innerHTML='<p role="status">正在读取本章真实数据…</p>';
 try{await loadData();}catch(e){if(myToken!==token)return;root.innerHTML=`<p class="warning">${esc(e.message)}</p><button data-retry>重新读取</button>`;root.querySelector('button').onclick=()=>mountLab(page,root,myToken);return;}
 if(myToken!==token)return;
 const isCode=page.lab==='code';let output=null,version=0;
 root.innerHTML=`<p class="eyebrow">${isCode?'可编辑代码 / JavaScript':'参数对照 / 真实数据'}</p><h2>${isCode?'在浏览器中修改并执行代码':'先预测变化，再运行对照'}</h2>${isCode?`<p>JavaScript在本机工作线程执行。完整Python训练请进入下方本章工作本。请只运行可信代码，勿粘贴密钥或个人资料。</p><label>实验代码<textarea id="editor" spellcheck="false" aria-label="JavaScript实验代码">${esc(codeExample(chapter))}</textarea></label>`:`<form aria-label="实验参数">${controls(page.lab).map(control).join('')}</form>`}<div class="actions"><button class="primary" data-run>运行${isCode?'代码':'实验'}</button><button data-stop disabled>停止</button><button data-reset>恢复默认</button><button data-save disabled>保存到课堂记录</button><button data-json disabled>导出JSON</button><button data-csv disabled>${isCode?'下载代码':'导出CSV'}</button></div><p class="status" role="status"></p><div class="result" aria-live="polite"></div>`;
 const q=s=>root.querySelector(s),status=q('.status'),result=q('.result');
 const invalidate=()=>{version++;output=null;stop();q('[data-stop]').disabled=true;q('[data-run]').disabled=false;for(const s of ['save','json','csv'])q(`[data-${s}]`).disabled=true;status.textContent='参数或代码已改变，请重新运行。';result.innerHTML='';};
 root.addEventListener('input',invalidate);root.addEventListener('change',invalidate);
 q('[data-stop]').onclick=()=>{invalidate();status.textContent='已停止，可重新运行。';};
 q('[data-reset]').onclick=()=>mountLab(page,root,myToken);
 const run=async()=>{
  if(!isCode&&!q('form').reportValidity())return;
  invalidate();const v=version,config=isCode?{}:Object.fromEntries(new FormData(q('form'))),code=isCode?q('#editor').value:null;
  status.textContent='正在计算…';q('[data-run]').disabled=true;q('[data-stop]').disabled=false;
  try{const r=await compute(page.lab,config,code);if(token!==myToken||version!==v)return;output={chapter,page:page.id,lab:page.lab,config,code,computedAt:new Date().toISOString(),sources:manifest.inputs[chapter],result:r};
   result.innerHTML=isCode?`<pre>${esc(r.text||'执行完成，无print输出。')}</pre>`:`<p class="compute">${esc(r.compute)}</p>${mapPlot(r)}${plot(r.chart)}<p class="warning">${esc(r.note)}</p><details open><summary>结果表（${r.rows.length}行）</summary>${table(r.columns,r.rows)}</details>${r.detail?`<details><summary>逐事件对照</summary>${table(r.detail.columns,r.detail.rows)}</details>`:''}`;
   status.textContent='本次计算完成。保存后可与其他参数结果一起导出。';for(const s of ['save','json','csv'])q(`[data-${s}]`).disabled=false;
  }catch(e){if(token!==myToken||version!==v)return;status.textContent='未完成：'+e.message;}
  finally{if(token===myToken&&version===v){q('[data-run]').disabled=false;q('[data-stop]').disabled=true;}}
 };
 q('[data-run]').onclick=run;
 q('[data-save]').onclick=()=>{if(!output)return;records.push(output);records=records.slice(-50);persist();status.textContent=storageOK?'已保存到本机课堂记录。':'本机存储不可用，请立即导出当前记录。';};
 q('[data-json]').onclick=()=>output&&download(`ch0${chapter}-${page.id}.json`,JSON.stringify(output,null,2),'application/json');
 q('[data-csv]').onclick=()=>{if(!output)return;download(`ch0${chapter}-${page.id}.${isCode?'js':'csv'}`,isCode?output.code:toCSV(output.result.columns,output.result.rows),isCode?'text/javascript':'text/csv');};
 if(!isCode)run();
}
function renderRecord(){
 main.innerHTML=`<p class="eyebrow">第${chapter}章 / 课堂记录</p><h1>我的交通问题分析</h1><p>每章独立保存，最近50次手动保存的实验。课堂记录不代表正式课程成绩，不上传到服务器。</p>${['研究问题与范围','参数对照与主要发现','工程解释与证据缺口'].map((t,i)=>`<label class="note-label">${t}<textarea data-note="${i}" maxlength="6000">${esc(notes[i]||'')}</textarea></label>`).join('')}<p>已保存${records.length}次实验。</p><div class="actions"><button id="export-record">导出完整记录JSON</button><button id="export-report">导出报告Markdown</button><button id="clear">清空本章记录</button></div>${table(['教学页','实验','时间'],records.slice().reverse().map(r=>[r.page,r.lab,r.computedAt]))}`;
 main.querySelectorAll('[data-note]').forEach(e=>e.oninput=()=>{notes[e.dataset.note]=e.value;persist();});
 document.querySelector('#export-record').onclick=()=>download(`ch0${chapter}-课堂记录.json`,JSON.stringify({chapter,version:'20260917',notes,records},null,2),'application/json');
 document.querySelector('#export-report').onclick=()=>download(`ch0${chapter}-课堂报告.md`,`# 第${chapter}章 ${course.title}\n\n${['研究问题与范围','参数对照与主要发现','工程解释与证据缺口'].map((t,i)=>`## ${t}\n\n${notes[i]||'尚未填写'}\n`).join('\n')}\n## 实验记录\n\n${records.map(r=>`### ${r.page}\n\n时间：${r.computedAt}\n\n参数：${JSON.stringify(r.config)}\n\n${r.result.note||'见配套JSON输出'}\n`).join('\n')}\n完整结果表及来源哈希请同时导出JSON。\n`,'text/markdown');
 document.querySelector('#clear').onclick=()=>{if(confirm('仅清空本章课堂笔记与实验记录？')){notes={};records=[];persist();renderRecord();}};
}
function home(){main.innerHTML=`<p class="eyebrow">第${chapter}章 / 交通运输工程</p><h1>${course.title}</h1><p class="lead">${course.mission}</p><p class="intro">${esc(course.data)}。以交通问题组织课堂，把数学表达、计算结果和工程解释联系起来。</p><div class="actions"><a class="button primary" href="#${course.pages[0].id}">开始课堂</a><a class="button" href="chapter-0${chapter}.pptx" download>下载本章PPT</a><a class="button" href="../#project/ch0${chapter}/code">完整Python项目</a></div><section class="overview"><h2>本章学习目标</h2><ol>${course.goals.map(t=>`<li>${esc(t)}</li>`).join('')}</ol><p class="small">建议${course.minutes}。${course.pages.length}个教学页，可按课堂时间分次讲授。</p></section><h2>课堂路线</h2><div class="route-list">${course.pages.map((p,i)=>`<a href="#${p.id}"><span>${String(i+1).padStart(2,'0')}</span><div><small>${p.section}${p.lab?' / 交互实验':''}</small><strong>${p.title}</strong></div></a>`).join('')}</div><h2>案例与章节衔接</h2><p>课堂解释与完整项目互相配合，专题实验不代替完整算法训练。已完成前两章的数据方案与编程准备后，逐步完成本章项目。</p>${caseLinks()}<p class="source">来源：<a href="${course.source}" target="_blank" rel="noopener">${course.sourceLabel}</a>。<a href="../classrooms/README.md">运行方式与许可</a></p>`;}
function caseLinks(){return `<div class="actions">${course.cases.map((id,i)=>`<a class="button" href="../#case/${id}">案例${i+1}：完整研究分析</a>`).join('')}<a class="button" href="../#project/ch0${chapter}">本章实践项目</a><a class="button" href="../chapters/notebooks/ch0${chapter}.ipynb" download>Python工作本</a></div>`;}
function renderPage(p){
 main.innerHTML=`<p class="eyebrow">第${chapter}章 / ${p.section}</p><h1>${esc(p.title)}</h1><p class="lead">${esc(p.lead)}</p><section class="explain">${p.body.map(t=>`<p>${esc(t)}</p>`).join('')}</section>${p.formula?`<section class="formula"><pre>${esc(p.formula)}</pre><p>${esc(p.symbols)}</p></section>`:''}${p.table?table(p.table.headers,p.table.rows):''}${p.video?`<figure class="video"><video controls playsinline preload="metadata" src="../chapters/data/video/mot17-04-web.mp4" aria-label="MOT17-04夜间步行街35秒视频"></video><figcaption>MOT17-04，原片35秒，30帧/秒。CC BY-NC-SA 3.0。浏览器预览为H.264转码，不自动播放。<a href="../#project/ch08/code">进入完整影像核查项目</a></figcaption></figure>`:''}${p.quiz?`<fieldset class="quiz"><legend>课堂判断</legend>${p.quiz.options.map((t,i)=>`<button data-answer="${i}">${esc(t)}</button>`).join('')}<p class="feedback" role="status"></p></fieldset>`:''}${p.lab?'<section class="lab" id="lab"></section>':''}<section class="discussion"><h2>课堂讨论</h2><p>${esc(p.question)}</p><label>我的解释<textarea class="page-note" maxlength="6000" placeholder="先说明交通对象与统计口径，再解释结果…">${esc(notes['page:'+p.id]||'')}</textarea></label></section><details class="connections"><summary>完整案例与Python实践</summary>${caseLinks()}<p>课堂代码采用JavaScript本机计算，模型拟合按Python工作本执行，冻结结果始终明确标注。</p></details><p class="source">本章资料：<a href="${course.source}">${course.sourceLabel}</a>。教材对应${p.section}，课堂表述另行编写。<a href="../classrooms/manifest.json">输入哈希</a></p>`;
 main.querySelector('.page-note').oninput=e=>{notes['page:'+p.id]=e.target.value;persist();};
 if(p.quiz)main.querySelectorAll('[data-answer]').forEach(b=>b.onclick=()=>{main.querySelector('.feedback').textContent=(+b.dataset.answer===p.quiz.correct?'判断正确。':'请再核对信息边界。')+p.quiz.explain;});
 if(p.lab)mountLab(p,main.querySelector('#lab'),token);
}
function route(){stop();token++;const hash=location.hash.slice(1)||'start';if(hash==='content'){main.focus();return;}active=course.pages.findIndex(p=>p.id===hash);if(hash==='record')renderRecord();else if(active<0)home();else renderPage(course.pages[active]);
 document.querySelector('#nav').innerHTML=`<a href="#start" ${active<0&&hash!=='record'?'aria-current="page"':''}>课堂首页</a>${course.pages.map((p,i)=>`<a href="#${p.id}" ${i===active?'aria-current="page"':''}><small>${p.section}</small>${p.title}</a>`).join('')}<a href="#record" ${hash==='record'?'aria-current="page"':''}>课堂记录与报告</a>`;
 document.querySelector('#page-label').textContent=active<0?(hash==='record'?'课堂记录':'课堂首页'):`${active+1} / ${course.pages.length}`;document.querySelector('#prev').disabled=active<0;document.querySelector('#next').disabled=active===course.pages.length-1;document.title=`${active<0?'第'+chapter+'章 '+course.title:course.pages[active].title} · 交通数据挖掘开放课堂`;window.scrollTo(0,0);}
function move(delta){const i=Math.max(-1,Math.min(course.pages.length-1,active+delta));location.hash=i<0?'start':course.pages[i].id;}
document.querySelector('#prev').onclick=()=>move(-1);document.querySelector('#next').onclick=()=>move(1);
function projection(v){present=v;document.body.classList.toggle('present',v);document.querySelector('#present').textContent=v?'退出投影':'课堂投影';document.querySelector('#present').setAttribute('aria-pressed',String(v));if(v&&active<0)location.hash=course.pages[0].id;}
document.querySelector('#present').onclick=()=>projection(!present);
document.addEventListener('keydown',e=>{if(e.key==='Escape')projection(false);if(!present||e.target.closest('input,textarea,select,button,a,[contenteditable]'))return;if(['ArrowRight','PageDown'].includes(e.key)){e.preventDefault();move(1);}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();move(-1);}});
document.querySelector('#storage').hidden=storageOK;window.addEventListener('hashchange',route);window.addEventListener('pagehide',stop);route();
