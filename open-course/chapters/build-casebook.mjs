import {writeFile} from 'node:fs/promises';
import {CASES} from './catalog.js';
import {caseToMarkdown} from './case-reader.js';
const book=['# 交通数据挖掘：交通工程研究案例册','','面向交通运输工程专业的16篇论文式教学案例。以出租车服务、道路监测与调查、共享单车运营、事故排查、断面预测和交叉口通行统计为主线。每篇包含摘要与关键词、背景、研究区域与数据、问题与工程指标、方法、结果、工程讨论、结论和参考资料。课程原创，非已发表论文。','','数字为课程固定真实数据快照的复算结果；无独立真值的内容不报告准确率，尚未实施的工程方案明确作为后续研究，不冒充真实部署或治理成效。','','本册与网页使用相同内容源。先复现固定参数，再做敏感性分析；不要将调整后的结果与本文基准口径混用。各数据源许可见DATA_SOURCES.md；SinD包含禁止商业使用等自定义条款。','','## 案例目录','',...CASES.map(c=>'- 第'+c.chapter+'章：'+c.title),'',...CASES.flatMap(c=>['---','',caseToMarkdown(c)])].join('\n');
await writeFile(new URL('CASEBOOK.md',import.meta.url),book,'utf8');
console.log(`Built ${CASES.length} full case studies from shared page content and evidence.`);
