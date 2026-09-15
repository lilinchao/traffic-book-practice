import {writeFile} from 'node:fs/promises';
import {PROJECTS} from './catalog.js';
const sections=p=>[['协议版本',p.protocol.id],['必做方法',p.protocol.required.join('；')],['选做方法',p.protocol.optional.join('；')],['交通对象与单位',p.protocol.unit],['样本范围',p.protocol.population],['划分与信息边界',p.protocol.split],['主比较口径',p.protocol.comparison]];
const table=rows=>['| 要素 | 规定 |','| --- | --- |',...rows.map(r=>'| '+r.join(' | ')+' |')].join('\n');
let book=['# 八章实践任务书','','保留单一论文式案例结构，不另拆学生任务版与参考全文。以下任务、工作本与主实验协议采用同一版本。',''];
for(const p of PROJECTS){
 const q=p.protocol;
 book.push('## 第'+p.chapter+'章 '+p.title,'',table(sections(p)),'','### 工程交付物','',...p.deliverables.map(t=>'- '+t),'',...p.tasks.flatMap(([h,s,d])=>['### '+h,'',s,'','阶段成果：'+d,'']),'### 验收要求','',...p.acceptance.map(t=>'- '+t),'');
 const report=['# '+p.title+'：工程分析报告','','协议版本：'+q.id,'数据来源：'+p.source.url,'',table(sections(p)),'','## 研究范围与工程用途','','明确对象、位置、时间范围、使用单位和分析结果将支持什么判断。','',...p.tasks.flatMap(([h,s,d])=>['## '+h,'',s,'','需提供：'+d,'','我的证据与解释：','']),'## 交付文件清单','',...p.deliverables.map(t=>'- [ ] '+t),'','## 对照、失败样本与不确定性','','列出实际运行配置、原始输出文件、失败时段/点位/事件，区分得到的结果和需要补充验证的判断。','','## 复现记录','','记录协议、输入SHA-256、依赖版本、代码修改、参数选择依据与运行方式。公开自测不代替教师审阅。','','## 使用边界与许可','',''+p.source.license,'',...p.boundaries.map(t=>'- '+t),''];
 await writeFile(new URL(p.id+'_report.md',import.meta.url),report.join('\n'));
}
await writeFile(new URL('PROJECT_BRIEFS.md',import.meta.url),book.join('\n'));
await writeFile(new URL('data/project-protocols.json',import.meta.url),JSON.stringify(Object.fromEntries(PROJECTS.map(p=>[p.id,p.protocol])),null,2));
console.log('Generated eight task briefs, report templates and machine-readable primary protocols.');
