import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {CASES,PROJECTS} from '../catalog.js';
import {CASE_STUDIES} from '../case-studies.js';
import {CASE_EVIDENCE,CASE_EVIDENCE_META} from '../data/case-evidence.js';
import {CASE_SECTIONS,caseToMarkdown,renderCaseStudy} from '../case-reader.js';
import {EXPERIMENTS,runComparison} from '../comparisons.mjs';
const root=new URL('../../',import.meta.url),book=await readFile(new URL('chapters/CASEBOOK.md',root),'utf8');
assert.equal(CASES.length,16);assert.deepEqual(Object.keys(CASE_STUDIES).sort(),CASES.map(c=>c.id).sort());assert.deepEqual(Object.keys(CASE_EVIDENCE).sort(),Object.keys(CASE_STUDIES).sort());
for(const [path,sha] of Object.entries(CASE_EVIDENCE_META.files))assert.equal(createHash('sha256').update(await readFile(new URL(path,root))).digest('hex'),sha,path);
const paragraphs=new Set();let tables=0;
for(const c of CASES){
 const s=CASE_STUDIES[c.id],e=CASE_EVIDENCE[c.id];assert.ok(JSON.stringify(s).length>=2300,c.id);
 assert.ok(s.abstract.length>=140,c.id+' abstract');assert.ok(s.keywords.length>=4);assert.ok(s.indicators.length>=3);assert.ok(s.discussion.length>=3);
 for(const key of ['background','setting','problem','evaluation','discussion']){assert.ok(s[key].length>=2);for(const p of s[key]){assert.ok(p.length>65,c.id+key);assert.ok(!paragraphs.has(p),'Repeated paragraph '+c.id);paragraphs.add(p);}}
 assert.equal(s.method.length,4);assert.ok(s.scope.length>=4);assert.ok(s.assignment.length>25);
 const project=PROJECTS.find(p=>p.id===s.experiment.project),experiment=EXPERIMENTS.find(e=>e.id===s.experiment.id);assert.equal(project.chapter,experiment.chapter);
 assert.ok(e.tables.length);assert.ok(e.files.every(p=>CASE_EVIDENCE_META.files[p]));assert.ok(e.protocol.length>20);
 for(const t of e.tables){assert.ok(t.rows.length);assert.ok(t.rows.every(r=>r.length===t.columns.length),c.id);for(const row of t.rows)for(const v of row)if(typeof v==='number')assert.ok(Number.isFinite(v));tables++;}
 const md=caseToMarkdown(c);assert.ok(book.includes(md),c.id+' booklet differs');
 const html=renderCaseStudy(c,PROJECTS.find(p=>p.chapter===c.chapter),PROJECTS.find(p=>p.id===c.target),'<img src=x onerror=alert(1)>');assert.ok(!html.includes('<img'));assert.ok(html.includes('&lt;img'));
 for(const [id,title] of CASE_SECTIONS){assert.ok(md.includes('## '+title));assert.ok(html.includes('id="case-'+id+'"'));}
 for(const p of [s.abstract,...s.setting,...s.discussion,...s.indicators.flat()]){assert.ok(md.includes(p)||md.includes(p.replaceAll('|','\\|')),c.id+' paper export omits content');assert.ok(html.includes(p.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')),c.id+' paper HTML omits content');}
 for(const p of s.evaluation)assert.ok(html.includes(p.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')));
}
const load=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));
const daily=await load('chapters/data/ch03.json'),crashes=await load('projects/data/crashes.json'),forecast=await load('projects/data/forecast.json'),tracks=await load('projects/data/sind.json');
assert.deepEqual(CASE_EVIDENCE['sample-size'].tables[0].rows,runComparison('sample-size',daily).rows);
assert.deepEqual(CASE_EVIDENCE['forecast-origin'].tables[0].rows,runComparison('forecast-horizon',forecast).rows);
assert.deepEqual(CASE_EVIDENCE['crossing-rule'].tables[0].rows,runComparison('count-stride',tracks).rows);
const missing=CASE_EVIDENCE['missing-time'].tables[0].rows;assert.equal(missing.length,7);assert.equal(daily.rows.length+missing.length,365);
const audit=CASE_EVIDENCE['no-coordinates'].tables[0].rows;assert.equal(audit.reduce((s,r)=>s+r[1],0),crashes.rows.length);assert.equal(audit.reduce((s,r)=>s+r[3],0),474);audit.forEach(r=>assert.equal(r[1],r[2]+r[3]));
const clustering=CASE_EVIDENCE['similar-days'].tables;assert.equal(clustering[0].rows.length,4);assert.ok(clustering[0].rows[0][1]>clustering[0].rows[2][1]);assert.equal(clustering[1].rows.reduce((s,r)=>s+r[1],0),31);
const dataFiles=await load('chapters/data/files.json');assert.ok(dataFiles.ch03);
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
const taxi=await load('projects/data/taxi.json'),bike=await load('chapters/data/ch04.json');
const regions=CASE_EVIDENCE['records-demand'].tables.at(-1).rows;
assert.equal(regions.reduce((s,r)=>s+r[1],0),taxi.rows.reduce((s,r)=>s+r[3],0));
for(const r of regions){close(r[2],r[1]/31);close(r[4],100*r[3]/r[1]);}
for(const [n,half,relative] of CASE_EVIDENCE['sample-size'].tables.at(-1).rows){const r=CASE_EVIDENCE['sample-size'].tables[0].rows.find(r=>r[1]===n);close(half,(r[6]-r[5])/2);close(relative,100*half/r[4]);}
for(const [period,model,n,actual,mae,rmse,bias,under] of CASE_EVIDENCE['bike-leakage'].tables.at(-1).rows){
 const hours=period==='07—09时'?[7,8,9]:period==='16—18时'?[16,17,18]:Array.from({length:24},(_,i)=>i).filter(h=>![7,8,9,16,17,18].includes(h));
 const rows=bike.rows.filter(r=>hours.includes(r[2])),index=model==='岭回归'?5:6,avg=a=>a.reduce((s,v)=>s+v,0)/a.length,d=rows.map(r=>r[index]-r[3]);
 assert.equal(n,rows.length);close(actual,avg(rows.map(r=>r[3])));close(mae,avg(d.map(Math.abs)));close(rmse,Math.sqrt(avg(d.map(v=>v*v))));close(bias,avg(d));close(under,100*avg(d.map(v=>Math.max(-v,0)))/actual);
}
const windows=[[7,8,9],[10,11,12,13,14,15],[16,17,18],[22,23,0,1,2,3,4,5]];
CASE_EVIDENCE['weekday-denominator'].tables.at(-1).rows.forEach((r,i)=>{const sums=[0,0];for(const row of taxi.rows){if(row[1]!=='Queens'||!windows[i].includes(row[2]))continue;const weekend=[0,6].includes(new Date(row[0]+'T00:00Z').getUTCDay());sums[+weekend]+=row[3];}close(r[2],sums[0]/23);close(r[3],sums[1]/8);close(r[4],100*(r[2]/r[3]-1));});
const direction=CASE_EVIDENCE['crossing-rule'].tables.at(-1).rows;
assert.deepEqual(direction.map(r=>r[3]),[6,5,6,3]);assert.equal(direction.reduce((s,r)=>s+r[1],0),9);assert.equal(direction.reduce((s,r)=>s+r[2],0),11);
for(const row of CASE_EVIDENCE['simple-baseline'].tables.at(-1).rows){const peak=row[0]!=='其他时段',index=row[1]==='岭回归'?6:5,rows=forecast.horizons['1'].rows.filter(r=>[7,8,9,16,17,18].includes(Number(r[0].slice(11,13)))===peak);assert.equal(row[2],rows.length);close(row[3],rows.reduce((s,r)=>s+Math.abs(r[index]-r[1]),0)/rows.length);}
assert.equal(tables,30);
console.log(`PASS: 16 engineering research cases, ${tables} evidence tables, ${16*CASE_SECTIONS.length} analysis sections, 10 verified input hashes, independent engineering metrics, escaped notes and identical booklet content.`);
