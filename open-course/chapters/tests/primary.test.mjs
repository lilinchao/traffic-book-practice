import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {PROJECTS} from '../catalog.js';
import {validatePrimary,crossingEvents} from '../primary-validation.mjs';
const ROOT=new URL('../../',import.meta.url),bytes=p=>fs.readFileSync(new URL(p,ROOT)),read=p=>JSON.parse(bytes(p));
const digest=p=>createHash('sha256').update(bytes(p)).digest('hex');
const index=read('chapters/data/learning-notebooks.json');let cells=0;
for(const p of PROJECTS){const n=index[p.id],book=read(n.path);assert.equal(digest(n.path),n.sha256);assert.equal(book.metadata.course_protocol,p.protocol.id);assert.equal(n.code_cells,book.cells.filter(c=>c.cell_type==='code').length);assert.equal(p.tasks.length,4);assert.ok(p.protocol.required.length>0);cells+=n.code_cells;}
assert.equal(cells,51);
for(const ch of [4,5,6,7,8]){const key=`ch0${ch}`,ref=read(`chapters/data/primary/${key}.json`);assert.equal(ref.protocol,PROJECTS[ch-1].protocol.id);for(const [path,sha] of Object.entries(ref.inputs))assert.equal(digest(path),sha);}
assert.equal(read('chapters/data/primary/ch06.json').truth.length,2169);
assert.equal(read('chapters/data/primary/ch07.json').truth.length,672);
const ref={protocol:'test-only',inputs:{},truth:[['a',2],['b',4]],models:['unit-test-model']};
const bundle={schema:'traffic-primary-v1',chapter:4,protocol:'test-only',inputs:{},config:{},outputs:{predictions:{columns:['id','model','prediction'],rows:[['a','unit-test-model',1],['b','unit-test-model',5]]}}};
assert.equal(validatePrimary(4,bundle,ref).rows[0][2],1);
for(const change of [b=>b.protocol='old',b=>b.outputs.predictions.rows.pop(),b=>b.outputs.predictions.rows.push(['a','unit-test-model',1]),b=>b.outputs.predictions.rows[0][2]=1e308,b=>b.outputs.predictions.rows[0][2]=null]){const bad=structuredClone(bundle);change(bad);assert.throws(()=>validatePrimary(4,bad,ref));}
assert.deepEqual(crossingEvents([[1,0,14,0],[1,1,15,0],[1,2,16,0]]),[[1,2,'+x']]);
const video=read('chapters/data/video/results.json');for(const run of Object.values(video.runs)){assert.equal(run.frames.length,350);assert.equal(run.metrics.reference_events,run.metrics.event_TP+run.metrics.event_FN);assert.equal(run.metrics.predicted_events,run.metrics.event_TP+run.metrics.event_FP);}
console.log('PASS: eight protocols, 51 code cells, notebook hashes, five input inventories, primary validator negative tests and video event accounting.');
