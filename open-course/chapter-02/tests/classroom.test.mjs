import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const dir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const ctx={window:{}};vm.createContext(ctx);
for(const name of ['core.js','lesson.js','data/observations.js'])vm.runInContext(fs.readFileSync(path.join(dir,name),'utf8'),ctx);
const C=ctx.window.ClassroomCore,D=ctx.window.OBSERVATIONS,L=ctx.window.LESSON,M=C.organize(D.rows);
test('real source hashes and unchanged chapter protocols',()=>{
  for(const [name,sha] of Object.entries(D.hashes))assert.equal(createHash('sha256').update(fs.readFileSync(path.join(dir,'..',name))).digest('hex'),sha,name);
  assert.equal(D.protocol,D.protocols.ch02.id);
  assert.equal(D.protocols.ch06.id,'ch06-forecast-v1');
  assert.match(D.protocols.ch06.population,/2169/);
});
test('full traffic population, conflicts and same-hour weather weights',()=>{
  assert.equal(D.rows.length,48204);assert.equal(M.hours.length,40575);assert.equal(M.conflicts.length,0);
  assert.equal(M.hours.reduce((s,r)=>s+r.count,0),48204);
  assert.equal(M.hours.filter(r=>r.volume===0).length,2);
  const a=C.audit(M,2017);assert.equal(a.expected,8760);assert.equal(a.missing,47);assert.equal(a.unique,8713);assert.equal(a.extra,1892);
  assert.equal(C.audit(M,2016).expected,8784);
  assert.equal(C.audit(M,2018).missing,19);assert.equal(C.audit(M,2018,true).expected,8760);
  const u=C.hourlyProfile(M,2017),w=C.hourlyProfile(M,2017,true);
  assert.equal(u.reduce((s,r)=>s+r.n,0),8713);assert.equal(w.reduce((s,r)=>s+r.n,0),10605);
  assert.ok(u.some((r,i)=>Math.abs(r.value-w[i].value)>1));
});
test('complete dates match the third chapter and zero is not missing',()=>{
  assert.equal(C.peakDays(M).length,358);
  assert.equal(C.peakDays(M,2017,false).length,364);
  const zero=M.hours.find(r=>r.volume===0);assert.equal(C.daySlots(M,zero.time.slice(0,10)).find(r=>r.hour===zero.hour).value,0);
  const gap=C.peakDays(M,2017,false).find(r=>r.n<3);assert.ok(gap);assert.ok(C.daySlots(M,gap.date).some(r=>r.value===null));
  assert.equal(C.mean([]),null);assert.equal(C.mean([0,2]),1);
});
test('bundled SQLite wrapper preserves original engine bytes',()=>{
  const vendor={window:{}};vm.createContext(vendor);
  vm.runInContext(fs.readFileSync(path.join(dir,'vendor/sqlite.js'),'utf8'),vendor);
  const manifest=JSON.parse(fs.readFileSync(path.join(dir,'vendor/manifest.json'),'utf8'));
  assert.equal(manifest.version,'1.14.2');
  assert.equal(createHash('sha256').update(vendor.window.SQL_ENGINE_SOURCE).digest('hex'),manifest.engineSHA256);
});
test('conflicting copy detected without changing source',()=>{
  const extra=Array.from(D.rows[0]);extra[8]+=100;
  assert.equal(C.organize([...D.rows,extra]).conflicts.length,1);
  assert.equal(C.organize(D.rows).conflicts.length,0);
});
test('transport-specific extension units and coverage',()=>{
  assert.equal(D.crashTotal,7542);assert.equal(D.crashes.length,7068);
  assert.equal(new Set(D.tracks.map(r=>r[0])).size,3);assert.equal(D.tracks.length,1325);
  assert.ok(D.tracks.every(r=>r[1]>=0&&r[1]<=120));
  assert.ok(D.crashes.every(r=>r[1]<-73&&r[2]>40));
});
test('unique routes, four textbook sections and complete lesson text',()=>{
  assert.equal(new Set(L.pages.map(p=>p.id)).size,L.pages.length);
  assert.equal(L.sections.length,4);
  for(const p of L.pages){assert.ok(p.body.length>=2);assert.ok(p.lead&&p.question&&p.takeaway);assert.ok(L.sections.some(s=>s[0]===p.section));}
  assert.ok(L.pages.some(p=>p.lab==='sql'));assert.ok(L.pages.some(p=>p.lab==='python'));
});
test('CSV handles commas, quotes, labels and missing distinctly',()=>{
  assert.equal(C.csv(['a','b'],[['x,y','a"b'],[0,null]]),'"a","b"\r\n"x,y","a""b"\r\n"0",""');
});
