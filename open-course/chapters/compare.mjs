import {readFile} from 'node:fs/promises';
import {EXPERIMENTS,runComparison} from './comparisons.mjs';
import {toCSV} from './engine.mjs';

const [id,...args]=process.argv.slice(2);
const experiment=EXPERIMENTS.find(e=>e.id===id);
try {
 if(!experiment)throw Error('请选择实验ID：\n'+EXPERIMENTS.map(e=>`${e.id}  ${e.title}`).join('\n'));
 const config={};
 for(const arg of args){const match=/^--([a-z]+)=(.+)$/.exec(arg);if(!match||!experiment.controls.some(c=>c.key===match[1]))throw Error('未知参数：'+arg);config[match[1]]=match[2];}
 const paths={2:'../projects/data/audit.json',3:'data/ch03.json',4:'data/ch04.json',5:'../projects/data/crashes.json',6:'../projects/data/forecast.json',7:'../projects/data/taxi.json',8:'../projects/data/sind.json'};
 const data=JSON.parse(await readFile(new URL(paths[experiment.chapter],import.meta.url),'utf8'));
 const result=runComparison(id,data,config);
 process.stdout.write(toCSV(result.columns,result.rows)+'\n');
 process.stderr.write(JSON.stringify(result,null,2)+'\n');
} catch(e){process.stderr.write(e.message+'\n');process.exitCode=1;}
