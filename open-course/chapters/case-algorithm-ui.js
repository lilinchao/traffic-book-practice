import {ALGORITHM_GUIDES} from './algorithm-guides.js';
import {ALGORITHM_EVIDENCE,ALGORITHM_META} from './data/algorithm-evidence.js';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>v!==0&&Math.abs(v)<.01?v.toExponential(3):v.toLocaleString('zh-CN',{maximumFractionDigits:3});
const colors=['#3046c5','#d2622d','#21826d','#9867b4','#687787'];
const code='chapters/python/case_algorithms.py';
const links=e=>`<a href="${code}" download>下载本章算法代码</a><a href="${e.file}" download>下载完整运行结果 JSON</a><a href="chapters/ALGORITHMS.md">复现步骤与依赖</a>`;
export function algorithmMethods(id,table){
 const g=ALGORITHM_GUIDES[id],e=ALGORITHM_EVIDENCE[id];if(!g)return '';
 return '<div class="case-algorithm-method"><p class="eyebrow">本章算法 · 已在真实快照上运行</p><h3>'+esc(g.title)+'</h3><p class="case-algorithm-chapters">教材对应：'+esc(g.sections)+'</p><p>'+esc(g.question)+'</p>'+table({title:'算法表达、符号与交通含义',columns:['模型或指标','定义与解释'],rows:g.formulas})+'<ol class="case-method-steps">'+g.steps.map(([h,p])=>'<li><h3>'+esc(h)+'</h3><p>'+esc(p)+'</p></li>').join('')+'</ol><div class="actions">'+links(e)+'</div><pre><code>python chapters/python/case_algorithms.py --chapter '+e.chapter+'</code></pre></div>';
}
function chart(e,v){
 const W=760,H=340,L=68,R=26,T=38,B=58,w=W-L-R,h=H-T-B;
 const text=(x,y,t,anchor='middle')=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="11" fill="#5b656a">${esc(t)}</text>`;
 let drawing='',legend=[];
 if(v.kind==='map'){
  const xy=e.mapXY,xs=xy.map(p=>p[0]),ys=xy.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(w/(maxX-minX),h/(maxY-minY)),left=L+(w-(maxX-minX)*scale)/2;
  const max=Math.max(...e.views.filter(v=>v.kind==='map').flatMap(v=>v.values));
  drawing=xy.map(([x,y],i)=>`<circle cx="${left+(x-minX)*scale}" cy="${H-B-(y-minY)*scale}" r="2.8" fill="#3046c5" opacity="${.06+.94*v.values[i]/max}"><title>${esc(`东向${fmt(x)}km，北向${fmt(y)}km；密度${fmt(v.values[i])}`)}</title></circle>`).join('');
  for(let i=0;i<=4;i++){const f=i/4;drawing+=text(left+(maxX-minX)*scale*f,H-B+18,fmt(minX+(maxX-minX)*f));drawing+=text(left-8,H-B-(maxY-minY)*scale*f,fmt(minY+(maxY-minY)*f),'end');}
  drawing+=text(W/2,H-12,'局部东向距离（km）；纵轴：局部北向距离（km）');
  legend=[['#3046c5','密度越高颜色越深；共用色阶最大值 '+fmt(max)]];
 }else{
  const n=v.labels.length,sets=v.kind==='clusters'?[{name:'日规模',values:v.values}]:v.series;
  const max=Math.max(1,...sets.flatMap(s=>s.values))*1.12,y=value=>H-B-value/max*h;
  for(let i=0;i<=4;i++){const value=max*i/4;drawing+=`<line x1="${L}" y1="${y(value)}" x2="${W-R}" y2="${y(value)}" stroke="#e4e8e8"/>`+text(L-8,y(value)+4,fmt(value),'end');}
  if(v.kind==='line'){
   for(const [j,s] of sets.entries()){
    const xx=i=>L+i*w/Math.max(1,n-1);
    drawing+=`<polyline fill="none" stroke="${colors[j%colors.length]}" stroke-width="${j===0?2.5:1.7}" points="${s.values.map((p,i)=>`${xx(i)},${y(p)}`).join(' ')}"/>`;
    drawing+=s.values.map((p,i)=>`<circle cx="${xx(i)}" cy="${y(p)}" r="3.5" fill="transparent"><title>${esc(v.labels[i]+' · '+s.name+'：'+fmt(p))}</title></circle>`).join('');
   }
  }else{
   const slot=w/n,bw=slot*.76/sets.length;
   for(const [j,s] of sets.entries())drawing+=s.values.map((p,i)=>`<rect x="${L+slot*i+slot*.12+j*bw}" y="${y(p)}" width="${Math.max(.5,bw-1)}" height="${H-B-y(p)}" fill="${v.kind==='clusters'?colors[v.groups[i]%colors.length]:colors[j%colors.length]}"><title>${esc(v.labels[i]+' · '+(v.kind==='clusters'?'簇'+(v.groups[i]+1):s.name)+'：'+fmt(p))}</title></rect>`).join('');
  }
  const indices=Array.from(new Set([0,...Array.from({length:Math.min(n,7)},(_,i)=>Math.round(i*(n-1)/Math.max(1,Math.min(n,7)-1))),n-1]));
  drawing+=indices.map(i=>text(v.kind==='line'?L+i*w/Math.max(1,n-1):L+(i+.5)*w/n,H-B+20,v.labels[i],i===0?'start':i===n-1?'end':'middle')).join('');
  legend=v.kind==='clusters'?[...new Set(v.groups)].sort().map(k=>[colors[k%colors.length],'簇'+(k+1)]):sets.map((s,i)=>[colors[i%colors.length],s.name]);
 }
 return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(v.label+'；'+v.unit)}"><title>${esc(v.label+'。'+v.note)}</title>${text(L,18,v.unit,'start')}${drawing}</svg><div class="case-chart-legend">${legend.map(([c,n])=>`<span><i style="background:${c}"></i>${esc(n)}</span>`).join('')}</div><p class="tiny">${esc(v.note)}</p>`;
}
export function algorithmResults(id,table){
 const g=ALGORITHM_GUIDES[id],e=ALGORITHM_EVIDENCE[id];if(!g)return '';
 return '<div class="case-algorithm-results"><p class="eyebrow">章节算法实证 · '+esc(ALGORITHM_META.edition)+'</p><h3>'+esc(g.title)+'</h3><div class="case-result-protocol"><strong>本轮计算协议</strong><p>'+esc(e.protocol)+'</p><small>下图切换已执行的Python结果，不在浏览器重新训练；完整预测、标签、参数和输入哈希可下载核查。</small></div><div class="case-algorithm-lab" data-algorithm-case="'+id+'"><div class="case-algorithm-options" aria-label="算法结果视图">'+e.views.map((v,i)=>'<button type="button" class="outline" data-algorithm-view="'+i+'" data-algorithm-id="'+id+'" aria-pressed="'+(i===0)+'">'+esc(v.label)+'</button>').join('')+'</div><div class="case-algorithm-figure" aria-live="polite">'+chart(e,e.views[0])+'</div></div>'+e.tables.map(table).join('')+'<div class="case-algorithm-findings"><h3>算法结果如何回答交通问题</h3>'+g.findings.map(p=>'<p>'+esc(p)+'</p>').join('')+'<p><strong>研究任务：</strong>'+esc(g.next)+'</p></div><div class="actions">'+links(e)+'</div><details><summary>本轮算法输入与运行版本</summary>'+table({title:'算法结果及输入SHA-256',columns:['文件','SHA-256'],rows:[[e.file,ALGORITHM_META.files[e.file]],...Object.entries(e.inputs)]})+'<p class="tiny">'+esc(JSON.stringify(ALGORITHM_META.versions[e.chapter]))+'</p></details></div><h3 class="case-previous-results">前置统计与既有对照协议</h3><p class="tiny">以下保留此前的资料审计与基础实验。训练编码、目标集合或评价对象与本轮不同时，分别解释，不能拼接成同一组模型成绩。</p>';
}
export function algorithmMarkdown(id,stage,table){
 const g=ALGORITHM_GUIDES[id],e=ALGORITHM_EVIDENCE[id];if(!g)return [];
 if(stage==='method')return ['### 本章算法：'+g.title,'','教材对应：'+g.sections,'',g.question,'',table({title:'算法表达、符号与交通含义',columns:['模型或指标','定义与解释'],rows:g.formulas}),...g.steps.flatMap(([h,p])=>['#### '+h,'',p,'']),'```sh','python chapters/python/case_algorithms.py --chapter '+e.chapter,'```',''];
 return ['### 章节算法实证结果','',e.protocol,'','网页交互切换固定Python运行结果，不在浏览器重新训练。','',...e.tables.map(table),'### 算法结果如何回答交通问题','',...g.findings.flatMap(p=>[p,'']),'研究任务：'+g.next,'','算法代码：'+code,'完整输出：'+e.file,'输出SHA-256：'+ALGORITHM_META.files[e.file],'运行版本：'+JSON.stringify(ALGORITHM_META.versions[e.chapter]),'输入SHA-256：',...Object.entries(e.inputs).map(([p,h])=>'- '+p+'：'+h),'','### 前置统计与既有对照协议','','以下原有实验和本轮协议不同时分别解释，不拼接成绩。',''];
}
export function algorithmReferences(id){return ALGORITHM_GUIDES[id]?.references||[];}
export function algorithmIntro(id){const g=ALGORITHM_GUIDES[id];return g?'<div class="case-algorithm-intro"><strong>本轮新增：'+esc(g.title)+'</strong><p>对应'+esc(g.sections)+'。方法、参数与真实运行结果已纳入正文。</p><button type="button" class="outline" data-algorithm-jump>查看章节算法实证 ↓</button></div>':'';}
export function handleAlgorithmAction(button){
 if(button.hasAttribute('data-algorithm-jump')){const section=document.getElementById('case-evaluation');section?.focus({preventScroll:true});section?.scrollIntoView({block:'start'});return true;}
 if(button.dataset.algorithmView===undefined)return false;
 const id=button.dataset.algorithmId,e=ALGORITHM_EVIDENCE[id],index=Number(button.dataset.algorithmView),lab=button.closest('[data-algorithm-case]');
 if(!e||!e.views[index]||!lab)return true;
 lab.querySelectorAll('[data-algorithm-view]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.algorithmView)===index)));
 lab.querySelector('.case-algorithm-figure').innerHTML=chart(e,e.views[index]);return true;
}
