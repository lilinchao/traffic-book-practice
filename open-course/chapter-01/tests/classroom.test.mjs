import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {PROJECT_PROTOCOLS} from '../../chapters/project-protocols.js';

const here=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const course=path.dirname(here);
const sandbox={window:{},location:{protocol:'https:'}};
for(const file of ['data/project-bridge.js','lesson.js','project-paths.js'])vm.runInNewContext(fs.readFileSync(path.join(here,file),'utf8'),sandbox,{filename:file});
const B=sandbox.window.PROJECT_BRIDGE,L=sandbox.window.LESSON,C=sandbox.window.TRAFFIC_CLASSROOM;
const clean=x=>JSON.parse(JSON.stringify(x));
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;

test('all eight chapter protocols and evidence hashes match the current course',()=>{
 assert.equal(B.projects.length,8);
 for(const p of B.projects){assert.deepEqual(clean(p.protocol),PROJECT_PROTOCOLS[p.id]);assert.ok(p.cases.length);}
 for(const [file,sha] of Object.entries(B.inputs))assert.equal(createHash('sha256').update(fs.readFileSync(path.join(course,file))).digest('hex'),sha,file);
 assert.equal(L.slides.length,42);assert.equal(C.MISSIONS.length,5);
 assert.equal(L.slides.filter(s=>s.lab).length,17);
 for(const m of C.MISSIONS){assert.ok(L.slides.some(s=>s.lab===m.slide));for(const id of m.chapters)assert.ok(PROJECT_PROTOCOLS[id]);}
 for(const s of L.slides){for(const id of s.projects||[])assert.ok(PROJECT_PROTOCOLS[id]);for(const id of s.sources||[])assert.ok(L.sources[id]);}
 assert.ok(!C.home().includes('#s-1'));
});

test('first-chapter forecasts use exactly the same 2169 targets and all three horizons',()=>{
 const reference=JSON.parse(fs.readFileSync(path.join(course,'chapters/data/primary/ch06.json'),'utf8'));
 const original=JSON.parse(fs.readFileSync(path.join(course,'chapters/data/algorithms/ch6.json'),'utf8'));
 assert.deepEqual(clean(B.forecast.rows.map(r=>r.slice(0,2))),reference.truth);
 assert.equal(new Set(B.forecast.rows.map(r=>r[0])).size,2169);
 for(const r of B.forecast.rows){assert.equal(r.length,10);assert.ok(r.slice(1).every(x=>Number.isFinite(x)&&x>=0));}
 const summaries=original.cases['forecast-origin'].tables[0].rows;
 for(const h of [1,3,6])for(const [label,col] of [['训练期星期小时均值',2],['上周同期',3],['ARIMA(2,0,0)',4+[1,3,6].indexOf(h)*2],['SARIMA(2,0,0)(1,0,0)24',5+[1,3,6].indexOf(h)*2]]){
  const expected=summaries.find(r=>r[0]===label&&r[1]===h);
  assert.ok(Math.abs(mean(B.forecast.rows.map(r=>Math.abs(r[col]-r[1])))-expected[3])<1e-8,`${label} h=${h}`);
 }
});

test('rental summaries are recomputed from actual common test predictions',()=>{
 const d=JSON.parse(fs.readFileSync(path.join(course,'chapters/data/algorithms/ch4.json'),'utf8')).details;
 const periods={all:()=>true,morning:h=>h>=7&&h<=9,evening:h=>h>=16&&h<=18,night:h=>h<=5};
 for(const [period,accept] of Object.entries(periods)){
  const rs=d.test_rows.filter(r=>accept(r[2]));
  B.bike.periods[period].forEach((summary,i)=>{
   assert.equal(summary.n,rs.length);assert.equal(summary.model,d.prediction_names[i]);
   const errors=rs.map(r=>r[4+i]-r[3]);
   assert.ok(Math.abs(summary.mae-mean(errors.map(Math.abs)))<1e-8);
   assert.equal(summary.underestimated,errors.filter(e=>e<0).length);
  });
 }
 assert.equal(B.bike.periods.all[0].n,4376);
});

test('video totals do not hide errors; units and licenses remain separated',()=>{
 const v=JSON.parse(fs.readFileSync(path.join(course,'chapters/data/video/results.json'),'utf8'));
 for(const [key,r] of Object.entries(B.video.runs)){
  assert.deepEqual(clean(r.metrics),v.runs[key].metrics);
  const m=r.metrics;assert.equal(m.event_TP+m.event_FP,m.predicted_events);assert.equal(m.event_TP+m.event_FN,m.reference_events);
 }
 const m=B.video.runs['0.35'].metrics;assert.equal(m.predicted_events,m.reference_events);assert.equal(m.event_FP,2);assert.equal(m.event_FN,2);
 assert.equal(B.video.source.dataset_license,'CC BY-NC-SA 3.0');
 assert.deepEqual(clean(B.safety),{total:7542,valid:7068});
});
