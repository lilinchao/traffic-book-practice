import {writeFile} from 'node:fs/promises';
import {CASES} from './catalog.js';
import {caseToMarkdown} from './case-reader.js';
const book=['# 交通数据挖掘：完整教学案例册','','16个案例统一采用研究背景与意义、问题分析与定义、解决思路与方法、结果评价与分析四个环节。数字为课程固定真实数据快照的复算结果；无独立真值的内容不报告准确率，尚未实施的设计明确作为待验证方案。','','本册与网页使用相同内容源。先复现固定参数，再做敏感性分析；不要将调整后的结果与本文基准口径混用。各数据源许可见DATA_SOURCES.md；SinD包含禁止商业使用等自定义条款。','',...CASES.flatMap(c=>['---','',caseToMarkdown(c)])].join('\n');
await writeFile(new URL('CASEBOOK.md',import.meta.url),book,'utf8');
console.log(`Built ${CASES.length} full case studies from shared page content and evidence.`);
