import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {COURSES} from '../later.js';
import {INPUTS,runLab,defaults,controls,codeExample,forecastRows} from '../engine.mjs';
const root=new URL('../../',import.meta.url),data={};
for(const n of Object.keys(COURSES))data[n]=Object.fromEntries(Object.entries(INPUTS[n]).map(([k,p])=>[k,JSON.parse(fs.readFileSync(new URL(p,root),'utf8'))]));
for(const [n,c]of Object.entries(COURSES)){
 test('chapter '+n+' unique pages and real default results',()=>{
  assert.equal(new Set(c.pages.map(p=>p.id)).size,c.pages.length);
  assert.ok(c.pages.some(p=>p.lab==='code'));
  for(const p of c.pages.filter(p=>p.lab&&p.lab!=='code')){
   const r=runLab(p.lab,data[n]);assert.ok(r.rows.length,p.lab);assert.ok(r.columns.length);assert.ok(r.note);assert.ok(r.compute);
   for(const row of r.rows)for(const v of row)if(typeof v==='number')assert.ok(Number.isFinite(v),p.lab);
  }
 });
 test('chapter '+n+' editable default JavaScript executes',()=>{let outputs=[];new Function('data','runLab','print',codeExample(n))(structuredClone(data[n]),runLab,v=>outputs.push(v));assert.equal(outputs.length,3);assert.ok(Array.isArray(outputs[1]));});
}
test('book small-section anchors and content sufficient',()=>{for(const c of Object.values(COURSES)){assert.ok(c.pages.length>=15);for(const p of c.pages){assert.ok(p.question);assert.ok(p.body.length>=2);if(p.formula)assert.ok(p.symbols);}}});
test('KDE matches Python Gaussian values on same probes',()=>{for(const h of [250,500,1000]){const r=runLab('kde',data[5],{bandwidth:h}),expected=data[5].algorithm.details.kde[h];r.map.forEach((row,i)=>assert.ok(Math.abs(row[2]-expected[i])<1e-12));}});
test('regression uses primary three models and 4376 test hours',()=>{const r=runLab('bike-models',data[4]);assert.deepEqual(r.rows.map(r=>r[0]),['OLS','Poisson','NB2']);for(const a of r.rows)assert.equal(a[1],4376);const refs=data[4].algorithm.cases['bike-leakage'].tables[0].rows;for(let i=0;i<3;i++)for(let j=1;j<5;j++)assert.ok(Math.abs(r.rows[i][j]-refs[i][j])<1e-9);});
test('all forecast models use identical 2169 target times',()=>{for(const h of [1,3,6]){const r=runLab('forecast-models',data[6],{horizon:h});for(const a of r.rows)assert.equal(a[1],2169);for(const model of ['ARIMA','SARIMA','week','calendar'])assert.equal(forecastRows(data[6],model,h).length,2169);}});
test('regional predictions use 672 or 168 cells',()=>{assert.ok(runLab('regional-models',data[7]).rows.every(r=>r[1]===672));assert.ok(runLab('regional-models',data[7],{region:'Queens'}).rows.every(r=>r[1]===168));});
test('SinD crossing reference',()=>{const r=runLab('crossing',data[8]);assert.equal(r.rows.length,20);assert.deepEqual(r.chart.series[0].values,[9,11]);});
test('input bounds and invalid categories fail explicitly',()=>{assert.throws(()=>runLab('gradient',data[3],{eta:'NaN'}));assert.throws(()=>runLab('kde',data[5],{bandwidth:0}));assert.throws(()=>runLab('regional-models',data[7],{region:'missing'}));});
test('changing gradient and sample parameters changes actual output',()=>{assert.notDeepEqual(runLab('gradient',data[3],{eta:.1}).rows,runLab('gradient',data[3],{eta:.4}).rows);assert.notDeepEqual(runLab('sample-size',data[3],{seed:42}).rows,runLab('sample-size',data[3],{seed:43}).rows);});
