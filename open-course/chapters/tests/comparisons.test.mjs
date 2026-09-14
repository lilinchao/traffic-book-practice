import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {EXPERIMENTS,runComparison,defaultsFor} from '../comparisons.mjs';
const root=new URL('../../',import.meta.url);
const paths={2:'projects/data/audit.json',3:'chapters/data/ch03.json',4:'chapters/data/ch04.json',5:'projects/data/crashes.json',6:'projects/data/forecast.json',7:'projects/data/taxi.json',8:'projects/data/sind.json'};
const datasets=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,JSON.parse(fs.readFileSync(new URL(p,root)))]));
const snapshot=JSON.stringify(datasets);
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
assert.equal(EXPERIMENTS.length,15);assert.equal(new Set(EXPERIMENTS.map(e=>e.id)).size,15);
let variants=0;
for(const e of EXPERIMENTS){
 const configs=[defaultsFor(e)];
 for(const f of e.controls)for(const v of f.options?f.options.map(o=>Array.isArray(o)?o[0]:o):[f.min,f.max])configs.push({...defaultsFor(e),[f.key]:String(v)});
 for(const config of configs){
  const r=runComparison(e.id,datasets[e.chapter],config);assert.ok(r.rows.length);assert.ok(r.rows.every(row=>row.length===r.columns.length));
  assert.deepEqual(r,runComparison(e.id,datasets[e.chapter],config),'deterministic '+e.id);
  function finite(v){if(typeof v==='number')assert.ok(Number.isFinite(v),e.id);else if(v&&typeof v==='object')Object.values(v).forEach(finite);}finite(r);
  if(r.chart.type==='interval')for(const p of r.chart.points)assert.ok(p.lower<=p.estimate&&p.estimate<=p.upper);
  if(e.id==='forecast-horizon')assert.equal(new Set(r.rows.map(row=>row[1])).size,1);
  if(e.id==='bootstrap-budget')assert.equal(new Set(r.rows.map(row=>row[4])).size,1);
  variants++;
 }
 assert.throws(()=>runComparison(e.id,datasets[e.chapter],{[e.controls[0].key]:'invalid'}));
 const cli=spawnSync(process.execPath,[fileURLToPath(new URL('chapters/compare.mjs',root)),e.id],{encoding:'utf8'});
 assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stderr),runComparison(e.id,datasets[e.chapter]));
}
assert.equal(JSON.stringify(datasets),snapshot,'inputs were mutated');
const raw={rows:[['2017-01-01T00:00',10,1],['2017-01-02T00:00',30,3]],meta:{}};
const d=runComparison('duplicate-weight',raw).rows[0];close(d[3],20);close(d[4],25);close(d[5],5);
const missing=runComparison('missing-zero',{rows:[['2017-01-31T23:00',100,1],['2017-03-01T00:00',200,1]],meta:{}}).rows;
assert.deepEqual(missing[1],['2017-02',672,0,672,0,null,0]);
const horizon=runComparison('forecast-horizon',datasets[6]);assert.equal(horizon.rows[0][1],2169);
const maps=[1,3,6].map(h=>new Map(datasets[6].horizons[h].rows.map(r=>[r[0],r]))),ids=[...maps[0].keys()].filter(k=>maps.every(m=>m.has(k)));
for(let i=0;i<3;i++){const residuals=ids.map(id=>maps[i].get(id)[6]-maps[i].get(id)[1]);close(horizon.rows[i][3],residuals.reduce((s,v)=>s+Math.abs(v),0)/ids.length);}
for(const row of runComparison('forecast-horizon',datasets[6],{model:'week'}).rows)close(row[2],runComparison('forecast-horizon',datasets[6],{model:'week'}).rows[0][2]);
const taxi=runComparison('taxi-denominator',datasets[7]);assert.equal(taxi.rows[0][1],23);assert.equal(taxi.rows[1][1],8);taxi.rows.forEach(r=>close(r[2]/r[1],r[3]));
const profile=runComparison('taxi-profile',datasets[7]);for(const name of new Set(profile.rows.map(r=>r[0])))close(profile.rows.filter(r=>r[0]===name).reduce((s,r)=>s+r[3],0),100);
const stride=runComparison('count-stride',datasets[8]);assert.equal(stride.rows[0][1],20);assert.equal(stride.rows[1][1],20);assert.ok(stride.rows[1][5]>0);assert.equal(stride.rows[2][3],2);
for(const r of stride.rows){assert.equal(r[1],r[2]+r[4]);assert.equal(stride.rows[0][1],r[2]+r[3]);}
const noEvents=runComparison('count-band',{rows:[[1,0,-10,0,'car'],[1,100,-9,0,'car']],meta:{}},{line:15});assert.equal(noEvents.rows[0][5],null);
console.log(`PASS: 15 experiments, ${variants} parameter variants, all CLI parity, no mutation, independent aggregation/metric checks, null and event-match edge cases.`);

