import {EXPERIMENTS,defaultsFor,runComparison} from './comparisons.mjs';
import {toCSV} from './engine.mjs';

const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>v==null?'无数据':typeof v==='number'?v.toLocaleString('zh-CN',{maximumFractionDigits:3}):esc(v);
const colors=['#177fa4','#b67534','#8b62a4'];
const tick=v=>Number(v.toPrecision(3)).toLocaleString('zh-CN',{maximumFractionDigits:2});
const memory=new Map();
function table(columns,rows){return `<div class="table-scroll comparison-table"><table><thead><tr>${columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${fmt(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
function plot(c){
 const values=c.type==='interval'?c.points.flatMap(p=>[p.lower,p.upper]).concat(c.reference):c.series.flatMap(s=>s.values).filter(v=>v!=null);
 const interval=c.type==='interval',low=interval?Math.min(...values):Math.min(0,...values),high=Math.max(...values),span=high-low||1;
 const min=low-(interval?0.08:0)*span,max=high+.08*span;
 const w=760,h=interval?Math.max(240,c.labels.length*42+85):310,L=interval?118:68,R=24,T=26,B=64;
 const x=i=>L+i*(w-L-R)/Math.max(1,c.labels.length-1),y=v=>h-B-(v-min)/(max-min)*(h-T-B);
 const tx=v=>L+(v-min)/(max-min)*(w-L-R),ry=i=>T+20+i*38;
 let body='';
 if(interval){
  body=Array.from({length:5},(_,i)=>{const v=min+(max-min)*i/4;return `<line x1="${tx(v)}" x2="${tx(v)}" y1="${T}" y2="${h-B}" stroke="#e4eaf0"/><text x="${tx(v)}" y="${h-B+22}" text-anchor="${i===0?'start':i===4?'end':'middle'}">${tick(v)}</text>`;}).join('');
  body+=`<line x1="${tx(c.reference)}" x2="${tx(c.reference)}" y1="${T}" y2="${h-B}" stroke="#8b62a4" stroke-dasharray="5 4"/>`;
  body+=c.points.map((p,i)=>`<text x="${L-12}" y="${ry(i)+4}" text-anchor="end">${esc(c.labels[i])}</text><line x1="${tx(p.lower)}" x2="${tx(p.upper)}" y1="${ry(i)}" y2="${ry(i)}" stroke="#177fa4" stroke-width="4"/><circle cx="${tx(p.estimate)}" cy="${ry(i)}" r="6" fill="#177fa4"><title>${esc(c.labels[i])}：${fmt(p.estimate)}，区间${fmt(p.lower)}至${fmt(p.upper)}</title></circle>`).join('');
 }else{
  body=Array.from({length:5},(_,i)=>{const v=min+(max-min)*i/4;return `<line x1="${L}" x2="${w-R}" y1="${y(v)}" y2="${y(v)}" stroke="#e4eaf0"/><text x="${L-9}" y="${y(v)+4}" text-anchor="end">${tick(v)}</text>`;}).join('');
  if(min<0)body+=`<line x1="${L}" x2="${w-R}" y1="${y(0)}" y2="${y(0)}" stroke="#7e8e99" stroke-dasharray="4 3"/>`;
  const step=(w-L-R)/c.labels.length;
  for(const [k,s] of c.series.entries()){
   if(c.type==='bars'){const bw=step*.7/c.series.length;body+=s.values.map((v,i)=>v==null?'':`<rect x="${L+i*step+step*.15+k*bw}" y="${y(Math.max(v,0))}" width="${bw-2}" height="${Math.abs(y(v)-y(0))}" rx="2" fill="${colors[k]}"><title>${esc(c.labels[i])} · ${esc(s.name)}：${fmt(v)}</title></rect>`).join('');}
   else{let active=false;const d=s.values.map((v,i)=>{if(v==null){active=false;return '';}const op=active?'L':'M';active=true;return `${op}${x(i)},${y(v)}`;}).join(' ');body+=`<path d="${d}" fill="none" stroke="${colors[k]}" stroke-width="2.4"/>`+s.values.map((v,i)=>v==null?'':`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${colors[k]}"><title>${esc(c.labels[i])} · ${esc(s.name)}：${fmt(v)}</title></circle>`).join('');}
  }
  const every=Math.max(1,Math.ceil(c.labels.length/8));
  body+=c.labels.map((label,i)=>(i%every&&i!==c.labels.length-1)?'':`<text x="${c.type==='bars'?L+(i+.5)*step:x(i)}" y="${h-B+25}" text-anchor="${c.type==='bars'?'middle':i===0?'start':i===c.labels.length-1?'end':'middle'}">${esc(label)}</text>`).join('');
 }
 return `<figure class="comparison-figure"><figcaption>${esc(c.unit)}</figcaption><div class="plot-scroll"><svg class="comparison-plot" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(c.unit)}"><title>${esc(c.unit)}；精确值见下方表格</title>${body}</svg></div><div class="legend">${interval?'<span><i style="background:#177fa4"></i>样本均值与区间</span><span><i style="background:#8b62a4"></i>文件观测参考均值</span>':c.series.map((s,i)=>`<span><i style="background:${colors[i]}"></i>${esc(s.name)}</span>`).join('')}</div></figure>`;
}
const control=(c,value)=>`<label>${esc(c.label)}${c.options?`<select name="compare-${c.key}">${c.options.map(o=>{const [v,label]=Array.isArray(o)?o:[o,o];return `<option value="${esc(v)}" ${String(v)===String(value)?'selected':''}>${esc(label)}</option>`;}).join('')}</select>`:`<input name="compare-${c.key}" type="number" min="${c.min}" max="${c.max}" step="1" value="${esc(value)}" required>`}</label>`;
export function mountComparisons(anchor,p,data,onSave,download){
 const list=EXPERIMENTS.filter(e=>e.chapter===p.chapter);if(!list.length)return;
 const section=document.createElement('section');section.className='article-section comparison-lab';section.id='comparison-lab';anchor.after(section);
 const shortcut=document.createElement('button');shortcut.type='button';shortcut.className='outline comparison-jump';shortcut.textContent=`直接查看本章${list.length}个专题对照 ↓`;anchor.before(shortcut);
 shortcut.addEventListener('click',()=>{section.tabIndex=-1;section.focus({preventScroll:true});section.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});});
 let chosen=list.find(e=>e.id===memory.get(p.id)?.id)||list[0],output=null;
 const query=s=>section.querySelector(s);
 function controlsValue(){return Object.fromEntries([...new FormData(query('form'))].map(([k,v])=>[k.replace('compare-',''),v]));}
 function markDirty(){output=null;query('[data-comparison-save]').disabled=true;query('[data-comparison-csv]').disabled=true;query('[data-comparison-json]').disabled=true;query('[data-comparison-status]').textContent='参数已改变，请重新运行对照。';query('[data-comparison-result]').innerHTML='<p class="empty">结果已过期。运行后显示新配置下的完整对照。</p>';}
 function run(){
  if(!query('form').reportValidity())return;
  const c=controlsValue();memory.set(p.id,{id:chosen.id,config:c});
  try{
   output=runComparison(chosen.id,data,c);
   query('[data-comparison-result]').innerHTML=`${plot(output.chart)}<p class="analysis-note">${esc(output.note)}</p><details class="comparison-values" open><summary>对照结果表 · ${output.rows.length}行</summary>${table(output.columns,output.rows)}</details>${output.detail?`<details><summary>逐事件核对 · ${output.detail.rows.length}行</summary>${table(output.detail.columns,output.detail.rows)}</details>`:''}`;
   for(const sel of ['[data-comparison-save]','[data-comparison-csv]','[data-comparison-json]'])query(sel).disabled=false;
   query('[data-comparison-status]').textContent='已按本专题独立配置完成计算；未改变上方自由实验参数。';
   query('[data-comparison-command]').textContent='node chapters/compare.mjs '+chosen.id+' '+Object.entries(c).map(([k,v])=>`--${k}=${v}`).join(' ');
  }catch(e){markDirty();query('[data-comparison-result]').innerHTML=`<p class="notice error">${esc(e.message)}</p>`;query('[data-comparison-status]').textContent='计算未完成，请检查参数。';}
 }
 function render(){
  output=null;const stored=memory.get(p.id),c=stored?.id===chosen.id?stored.config:defaultsFor(chosen);
  section.innerHTML=`<div class="section-heading"><h3>专题对照实验</h3><span class="pill">本章新增 ${list.length} 个</span></div><p>先选一个问题，再一次运行多组方案。各专题的配置独立于上方自由实验，数据快照保持不变。</p><div class="comparison-picker" role="group" aria-label="选择对照专题">${list.map((e,i)=>`<button class="outline comparison-choice" type="button" data-comparison-id="${e.id}" aria-pressed="${e.id===chosen.id}"><small>对照 ${String(i+1).padStart(2,'0')}</small><span>${esc(e.title)}</span></button>`).join('')}</div><div class="comparison-workspace"><p class="eyebrow">${esc(chosen.title)}</p><h4>${esc(chosen.question)}</h4><dl class="comparison-protocol"><dt>改变什么</dt><dd>${esc(chosen.change)}</dd><dt>固定什么</dt><dd>${esc(chosen.fixed)}</dd><dt>观察什么</dt><dd>${esc(chosen.observe)}</dd></dl><form class="controls" aria-label="专题对照参数">${chosen.controls.map(f=>control(f,c[f.key])).join('')}</form><div class="actions"><button type="button" data-comparison-run>运行整组对照</button><button type="button" class="outline" data-comparison-reset>恢复本专题默认值</button></div><p class="tiny" data-comparison-status role="status"></p><div data-comparison-result></div><div class="actions"><button type="button" data-comparison-save disabled>保存整组对照到报告</button><button type="button" class="outline" data-comparison-csv disabled>导出对照表 CSV</button><button type="button" class="outline" data-comparison-json disabled>导出完整实验 JSON</button></div><details class="comparison-code"><summary>复现这组实验的代码</summary><p>下载八章资料包并解压，在根目录用Node.js 18或更新版本运行以下命令。它与网页调用同一个计算模块，不需要安装第三方依赖。CSV写到标准输出，完整配置与结果JSON写到标准错误输出；可用 <code>&gt; result.csv 2&gt; result.json</code> 保存。</p><pre data-comparison-command></pre><p><a href="chapters/comparisons.mjs" target="_blank" rel="noopener">查看实际计算源码</a> · <a href="chapters/compare.mjs" download>下载命令行入口</a> · <a href="chapters/chapter-projects.zip" download>下载含数据与依赖模块的资料包</a></p><p class="tiny">第4、6章使用已有Python模型的冻结预测，只重算误差；其他专题直接在真实观测记录上计算。不提供云端训练或虚构成绩。</p></details></div>`;
  run();
 }
 section.addEventListener('input',e=>{if(e.target.closest('form'))markDirty();});
 section.addEventListener('change',e=>{if(e.target.closest('form'))markDirty();});
 section.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.comparisonId){chosen=list.find(x=>x.id===b.dataset.comparisonId);render();query(`[data-comparison-id="${chosen.id}"]`).focus({preventScroll:true});}
  if(b.hasAttribute('data-comparison-run'))run();
  if(b.hasAttribute('data-comparison-reset')){memory.set(p.id,{id:chosen.id,config:defaultsFor(chosen)});render();query('[data-comparison-reset]').focus({preventScroll:true});}
  if(!output)return;
  if(b.hasAttribute('data-comparison-save')){onSave(output);query('[data-comparison-status]').textContent='整组参数、结果表和数据版本已保存到本机，可随项目报告导出。';}
  if(b.hasAttribute('data-comparison-csv'))download(p.id+'_'+output.id+'.csv',toCSV(output.columns,output.rows),'text/csv;charset=utf-8');
  if(b.hasAttribute('data-comparison-json'))download(p.id+'_'+output.id+'.json',JSON.stringify(output,null,2),'application/json');
 });
 render();
}
