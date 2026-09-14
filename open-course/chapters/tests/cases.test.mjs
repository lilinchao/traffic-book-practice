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
 const s=CASE_STUDIES[c.id],e=CASE_EVIDENCE[c.id];assert.ok(JSON.stringify(s).length>=1200,c.id);
 for(const key of ['background','problem','evaluation']){assert.ok(s[key].length>=2);for(const p of s[key]){assert.ok(p.length>65,c.id+key);assert.ok(!paragraphs.has(p),'Repeated paragraph '+c.id);paragraphs.add(p);}}
 assert.equal(s.method.length,4);assert.ok(s.scope.length>=4);assert.ok(s.assignment.length>25);
 const project=PROJECTS.find(p=>p.id===s.experiment.project),experiment=EXPERIMENTS.find(e=>e.id===s.experiment.id);assert.equal(project.chapter,experiment.chapter);
 assert.ok(e.tables.length);assert.ok(e.files.every(p=>CASE_EVIDENCE_META.files[p]));assert.ok(e.protocol.length>20);
 for(const t of e.tables){assert.ok(t.rows.length);assert.ok(t.rows.every(r=>r.length===t.columns.length),c.id);for(const row of t.rows)for(const v of row)if(typeof v==='number')assert.ok(Number.isFinite(v));tables++;}
 const md=caseToMarkdown(c);assert.ok(book.includes(md),c.id+' booklet differs');
 const html=renderCaseStudy(c,PROJECTS.find(p=>p.chapter===c.chapter),PROJECTS.find(p=>p.id===c.target),'<img src=x onerror=alert(1)>');assert.ok(!html.includes('<img'));assert.ok(html.includes('&lt;img'));
 for(const [id,title] of CASE_SECTIONS){assert.ok(md.includes('## '+title));assert.ok(html.includes('id="case-'+id+'"'));}
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
console.log(`PASS: 16 detailed cases, ${tables} evidence tables, 64 analysis sections, 10 verified input hashes, valid experiment links, escaped notes and identical booklet content.`);
