import {CASE_STUDIES} from './case-studies.js';
import {CASE_EVIDENCE,CASE_EVIDENCE_META} from './data/case-evidence.js';
import {algorithmMethods,algorithmResults,algorithmMarkdown,algorithmReferences,algorithmIntro,handleAlgorithmAction} from './case-algorithm-ui.js';

export const CASE_SECTIONS=[
 ['background','研究背景与意义'],['setting','研究区域与数据'],
 ['problem','问题定义与工程指标'],['method','研究方法与技术路线'],
 ['evaluation','结果评价与分析'],['discussion','工程应用讨论与局限']
];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=v=>v==null?'无数据':typeof v==='number'?(v!==0&&Math.abs(v)<.01?v.toExponential(3):v.toLocaleString('zh-CN',{maximumFractionDigits:3})):String(v);
const paragraphs=rows=>rows.map(t=>'<p>'+esc(t)+'</p>').join('');
const href=(p,tab='code')=>'#project/'+p+'/'+tab;
function table(t){
 return '<div class="case-table-scroll '+(t.columns.length===2?'case-definitions':'')+'" tabindex="0" role="region" aria-label="'+esc(t.title)+'"><table><caption>'+esc(t.title)+'</caption><thead><tr>'+t.columns.map(c=>'<th scope="col">'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+t.rows.map(r=>'<tr>'+r.map(v=>'<td>'+esc(number(v))+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'+(t.note?'<p class="tiny">'+esc(t.note)+'</p>':'');
}
const scopeTable=s=>({title:'研究任务与分析边界',columns:['要素','本研究定义'],rows:s.scope});
const indicatorTable=s=>({title:'交通工程指标与计算口径',columns:['指标','定义、符号与单位'],rows:s.indicators});
const references=(c,s)=>[['原始数据与官方说明',c.source],...(s.references||[]),...algorithmReferences(c.id)];

export function renderCaseStudy(c,p,target,note){
 const s=CASE_STUDIES[c.id],e=CASE_EVIDENCE[c.id];
 const sections=CASE_SECTIONS.map(([key,title],i)=>{
  const body=key==='method'?'<ol class="case-method-steps">'+s.method.map(([h,t])=>'<li><h3>'+esc(h)+'</h3><p>'+esc(t)+'</p></li>').join('')+'</ol>':paragraphs(s[key]);
  const extra=key==='problem'?table(scopeTable(s))+table(indicatorTable(s)):key==='evaluation'?'<div class="case-result-protocol"><strong>实证结果与复现口径</strong><p>'+esc(e.protocol)+'</p><small>由固定真实数据快照计算或核查。在线调参不会自动改写本文结果；尚未实施的工程方案不列为实证成果。</small></div>'+e.tables.map(table).join(''):'';
  return '<section class="article-section case-section" id="case-'+key+'" tabindex="-1"><h2><span>'+String(i+1).padStart(2,'0')+'</span>'+title+'</h2>'+(key==='evaluation'?algorithmResults(c.id,table)+extra+body:body+extra+(key==='method'?algorithmMethods(c.id,table):''))+'</section>';
 }).join('');
 return '<div class="breadcrumbs"><a href="#cases">交通工程案例库</a><span>/</span><a href="#cases/'+c.chapter+'">第'+c.chapter+'章</a></div>'
 +'<header class="case-header"><p class="eyebrow">交通运输工程 · 第'+c.chapter+'章 · '+esc(c.type)+'</p><h1>'+esc(c.title)+'</h1><p>'+esc(c.lead)+'</p><div class="case-reading-meta"><span>论文式教学案例</span><span>真实数据 · 工程问题 · 可复算结果</span><span>更新：'+CASE_EVIDENCE_META.edition+'</span></div></header>'
 +'<div class="content-columns"><article class="reading case-reading"><section class="case-abstract" aria-labelledby="case-abstract-title"><h2 id="case-abstract-title">摘要</h2><p>'+esc(s.abstract)+'</p><div class="case-keywords"><strong>关键词</strong>'+s.keywords.map(k=>'<span>'+esc(k)+'</span>').join('')+'</div><p class="case-editorial-note">课程原创研究性教学材料，非已发表论文；不代表管理部门已实施的规划、调度或治理成果。</p></section>'
 +'<div class="case-central-question"><small>需要回答的交通工程问题</small><p>'+esc(c.question)+'</p><span>沿着“交通任务 → 观测指标 → 方法与证据 → 工程适用条件”阅读。</span></div>'
 +algorithmIntro(c.id)+'<nav class="case-toc" aria-label="案例分析目录">'+CASE_SECTIONS.map(([id,title],i)=>'<button type="button" class="outline" data-case-section="'+id+'"><span>'+String(i+1).padStart(2,'0')+'</span>'+title+'</button>').join('')+'</nav>'+sections
 +'<section class="case-conclusion"><h2>结论</h2><p>'+esc(s.takeaway)+'</p></section>'
 +'<section class="article-section case-assignment"><h2>研究报告与工程交付</h2><p>'+esc(s.assignment)+'</p><p class="tiny">报告应形成完整证据链：明确交通对象与尺度，说明字段和单位，复核比较条件，解释工程意义，分别列出已得到的结果与尚待验证的建议。</p><label>我的案例笔记<textarea id="case-note" data-case="'+c.id+'" maxlength="20000" placeholder="按摘要、背景、区域与数据、问题与指标、方法、结果、工程讨论和结论组织你的研究报告。">'+esc(note)+'</textarea></label><div class="actions"><button class="outline" id="export-case" data-case="'+c.id+'">导出案例笔记</button><button type="button" class="outline" data-download-study="'+c.id+'">下载案例全文 Markdown</button></div></section>'
 +'<section class="article-section case-references"><h2>参考资料</h2><ol>'+references(c,s).map(([title,url])=>'<li><a href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(title)+' ↗</a></li>').join('')+'</ol><p class="tiny">官方资料用于核查数据含义与方法背景，本文分析及其应用讨论为课程原创，不冒用数据提供方的研究结论。</p></section>'
 +'<details class="case-provenance"><summary>数据版本、处理链路与复现文件</summary><p>结果表由课程固定快照生成；现场调查、前瞻验证或治理评价未实施时，正文明确标记。文件哈希用于核对版本，不代表独立真值验证。</p>'
 +table({title:'本案例使用的文件及SHA-256',columns:['文件','SHA-256'],rows:e.files.map(path=>[path,CASE_EVIDENCE_META.files[path]])})
 +'<p><a href="chapters/build-case-evidence.mjs">证据表生成代码</a> · <a href="chapters/DATA_SOURCES.md">数据处理与许可</a> · <a href="chapters/CASEBOOK.md" download>下载完整16案例册</a></p>'
 +(c.id==='similar-days'?'<p>聚类原始输出：<a href="chapters/data/case-cluster-comparison.csv">类别数对照</a> · <a href="chapters/data/case-day-clusters-4.csv">K=4日期分组</a> · <a href="chapters/data/case-cluster-centers-4.csv">K=4中心向量</a>。使用现有Python扩展代码复算，版本与参数见本文结果口径。</p>':'')
 +'<p class="tiny">课程代码许可不覆盖第三方数据；SinD须遵循提供方包含禁止商业使用条款的原许可。</p></details></article>'
 +'<aside class="project-aside"><h3>对应实践</h3><p>第'+target.chapter+'章 · '+esc(target.title)+'</p><a class="button" href="'+href(c.target)+'">打开对应实验</a><section class="article-section"><h3>复核与对照分析</h3><p>'+esc(s.experiment.label)+'</p><a class="button outline" href="'+href(s.experiment.project)+'/'+s.experiment.id+'">打开配套专题</a><p class="tiny">按默认参数打开。先复核本文基准，再修改条件，另行解释对工程结论的影响。</p></section><section class="article-section"><h3>完整研究材料</h3><a href="chapters/CASEBOOK.md" download>下载完整案例册</a><p class="tiny">网页、单篇下载与案例册采用同一份研究内容和结果表。</p></section><a href="'+href(p.id,'cases')+'">查看本章全部案例 →</a></aside></div>';
}
const mdCell=v=>number(v).replaceAll('|','\\|').replaceAll('\n',' ');
const mdTable=t=>['','**'+t.title+'**','','| '+t.columns.map(mdCell).join(' | ')+' |','| '+t.columns.map(()=>'---').join(' | ')+' |',...t.rows.map(r=>'| '+r.map(mdCell).join(' | ')+' |'),'',t.note||'',''].join('\n');
export function caseToMarkdown(c){
 const s=CASE_STUDIES[c.id],e=CASE_EVIDENCE[c.id];
 return ['# 第'+c.chapter+'章 · '+c.title,'',c.lead,'','论文式教学案例；课程原创，非已发表论文，不代表已实施的工程成果。','','## 摘要','',s.abstract,'','关键词：'+s.keywords.join('；'),'','交通工程问题：'+c.question,'',
 ...CASE_SECTIONS.flatMap(([key,title])=>['## '+title,'',...(key==='method'?[...s.method.flatMap(([h,t],i)=>['### '+(i+1)+'. '+h,'',t,'']),...algorithmMarkdown(c.id,'method',mdTable)]:key==='evaluation'?[...algorithmMarkdown(c.id,'evaluation',mdTable),'结果口径：'+e.protocol,'',...e.tables.map(mdTable),...s.evaluation.flatMap(t=>[t,''])]:s[key].flatMap(t=>[t,''])),'',...(key==='problem'?[mdTable(scopeTable(s)),mdTable(indicatorTable(s))]:[])]),
 '## 结论','',s.takeaway,'','## 研究报告与工程交付','',s.assignment,'','## 参考资料','',...references(c,s).map(([title,url])=>'- ['+title+']('+url+')'),'','## 复现说明','',
 '[配套专题：'+s.experiment.label+'](https://lilinchao.github.io/traffic-book-practice/open-course/#project/'+s.experiment.project+'/code/'+s.experiment.id+')','',
 '固定快照与处理链路见DATA_SOURCES.md。计算或材料核查不代表独立真值验证；尚未实施的方案不作为既有成果。','',
 ...e.files.map(path=>'- '+path+'：SHA-256 '+CASE_EVIDENCE_META.files[path]),'',
 c.id==='similar-days'?'聚类通过projects/python/extensions.py --project taxi复算；scikit-learn 1.9.1，random_state=42，n_init=10。详细输出见chapters/data/case-*.csv。':'',''].join('\n');
}
export function handleCaseStudyAction(button,cases,download){
 if(handleAlgorithmAction(button))return true;
 if(button.dataset.caseSection){const section=document.getElementById('case-'+button.dataset.caseSection);if(section){section.focus({preventScroll:true});section.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});}return true;}
 if(button.dataset.downloadStudy){const c=cases.find(c=>c.id===button.dataset.downloadStudy);if(c)download(c.id+'_case.md',caseToMarkdown(c));return true;}
 return false;
}
