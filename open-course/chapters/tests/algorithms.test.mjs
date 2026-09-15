import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ALGORITHM_GUIDES as guides} from '../algorithm-guides.js';
import {ALGORITHM_EVIDENCE as evidence,ALGORITHM_META as meta} from '../data/algorithm-evidence.js';
import {CASES,PROJECTS} from '../catalog.js';
import {caseToMarkdown,renderCaseStudy} from '../case-reader.js';
const root=new URL('../../',import.meta.url),raw={};
for(const [path,hash] of Object.entries(meta.files)){
 const bytes=await readFile(new URL(path,root));assert.equal(createHash('sha256').update(bytes).digest('hex'),hash);
 const r=JSON.parse(bytes);raw[r.chapter]=r;
 for(const [p,h] of Object.entries(r.inputs))assert.equal(createHash('sha256').update(await readFile(new URL(p,root))).digest('hex'),h);
}
assert.equal(Object.keys(evidence).length,10);assert.deepEqual(Object.keys(guides),Object.keys(evidence));
let tableCount=0,viewCount=0;
for(const c of CASES){
 const p=PROJECTS.find(p=>p.chapter===c.chapter),html=renderCaseStudy(c,p,p,''),md=caseToMarkdown(c);
 if(c.chapter<4){assert.ok(!html.includes('data-algorithm-case'));continue;}
 const g=guides[c.id],e=evidence[c.id];assert.equal(e.chapter,c.chapter);assert.equal(g.findings.length,3);assert.equal(g.steps.length,3);assert.ok(g.sections.startsWith(c.chapter+'.'));
 assert.deepEqual(e.tables,raw[c.chapter].cases[c.id].tables);
 assert.ok(html.includes('data-algorithm-case="'+c.id+'"'));assert.ok(html.includes('不在浏览器重新训练'));
 for(const text of [g.title,g.sections,...g.findings]){assert.ok(md.includes(text));assert.ok(html.includes(text));}
 assert.ok(md.includes(meta.files[e.file]));assert.ok(md.includes('前置统计与既有对照协议'));
 for(const v of e.views){
  assert.ok(v.note.length>25);viewCount++;
  const n=v.kind==='map'?e.mapXY.length:v.labels.length;
  const vectors=v.kind==='line'||v.kind==='bar'?v.series.map(s=>s.values):[v.values];
  for(const a of vectors){assert.equal(a.length,n);assert.ok(a.every(Number.isFinite));assert.ok(a.every(x=>x>=0));}
  if(v.groups)assert.equal(v.groups.length,n);
 }
 tableCount+=e.tables.length;
}
const almost=(a,b)=>assert.ok(Math.abs(a-b)<1e-8);
const rmse=(a,b)=>Math.sqrt(a.reduce((s,x,i)=>s+(x-b[i])**2,0)/a.length);
const d4=raw[4].details;
for(let model=0;model<3;model++)almost(rmse(d4.test_rows.map(r=>r[3]),d4.test_rows.map(r=>r[model+4])),raw[4].cases['bike-leakage'].tables[0].rows[model][3]);
for(const [name,h,n,mae,error] of raw[6].cases['forecast-origin'].tables[0].rows)if(raw[6].details.predictions[name]){assert.equal(n,2169);almost(rmse(raw[6].details.actual,raw[6].details.predictions[name][h]),error);}
const d7=raw[7].details;for(const [name,n,mae,error] of raw[7].cases['weekday-denominator'].tables[0].rows){assert.equal(n,672);almost(rmse(d7.actual.flat(),d7.predictions[name].flat()),error);}
assert.equal(raw[5].cases['no-coordinates'].tables[0].rows[2][3],20);
assert.equal(raw[8].details['10-kalman'].events.length,8);
assert.equal(tableCount,20);assert.equal(viewCount,36);
console.log(`PASS: 10 chapter-specific algorithms, ${tableCount} tables, ${viewCount} views, source/output hashes, complete Markdown and independent prediction RMSE.`);
