# 第1章：从交通问题走向可验证的实践

2026-09-15交通任务衔接版。保留教材1.1至1.6的结构和42页网页讲义，以五类交通任务连接当前八章主项目。书稿未修改；基础PPT保留原版，**不包含本轮新增衔接和视频核验**，不能将其数值与新版网页混为同一实验。

## 使用

- [在线课堂](https://lilinchao.github.io/traffic-book-practice/open-course/chapter-01/)；首页选择交通任务，或按小节讲授。
- 建议90分钟主线：导览5分钟、概述15分钟、分析基础20分钟、数据类型20分钟、数据选择10分钟、方法与评价10分钟、方案与路径10分钟。共享单车、安全、出租车和行人分支择一深入，其他留到课后。
- 网页共17个交互模块、15个问题情境。不是要求一堂课完成全部活动。
- 顶部“课堂投影”逐页展示；方向键、PageUp/PageDown与按钮翻页，输入草稿时不截获方向键。
- 解压离线包后打开index.html，不需要启动服务器。课程讲义、数据筛选、研究方案、模型误差重算和事件结果讨论可离线使用；**真实视频、外部机构视频和后续章节完整项目需要网络**。
- 原版可编辑PPT仍保留下载，但新增内容请以本次HTML课堂为准。

## 五类交通任务

| 交通任务 | 第一章动手做什么 | 后续章节及成果 |
| --- | --- | --- |
| 早高峰监测与预测 | 区分流量和拥堵、审查小时记录、比较预测时效与分时误差 | 第2章整编；第3章20/60/90日抽样与区间；第6章1/3/6小时预测及适用性报告 |
| 共享单车高峰服务 | 核查标签泄漏与天气信息，比较早晚高峰估计误差 | 第4章OLS、泊松、NB2；服务量估计与站点数据缺口 |
| 道路事故候选地点排查 | 比较事故数量与暴露量，审查474条不能落图记录 | 第5章固定网格、KDE、DBSCAN；至少3处候选范围与现场核查清单 |
| 出租车分区与夜间运营 | 区分服务记录与潜在需求，识别地区及钟点差异 | 第7章AR/VAR预测与独立KMeans日型；分区运营研判 |
| 夜间步行交通调查 | 从重复框到通过事件，揭示15次对15次背后的误计与漏计 | 第8章YOLOX、卡尔曼与匈牙利关联；逐事件、分方向核验 |

这些场景来自不同地区和数据集，不拼接成一个虚构城市或已经实施的工程。SinD天津地面轨迹与MOT17夜间影像是独立协议，位置单位和参考证据不同。

## 研究方案与章节路径

[本课研究方案](https://lilinchao.github.io/traffic-book-practice/open-course/chapter-01/#plan)按任务分别保存六项内容：对象与范围、问题与用途、指标与字段、至少两种真实来源的适配与许可、方法与评价、证据缺口与结论边界。导出的Markdown包含相关主协议与交付清单，作为第1章项目的问题定义书草稿，不冒充已完成实验。

第1章工作本仍以原有四类基础来源演示；自行车与MOT17是第4/8章的扩展来源，方案中应单独记录其许可、字段和覆盖，不改变原四类示例或拼接总体。

[八章实践路径](https://lilinchao.github.io/traffic-book-practice/open-course/chapter-01/#pathways)直接使用chapters/project-protocols.js与catalog.js生成的当前任务、算法、统计总体和交付物。每条路径都可进入项目概览、代码/工作本和交通研究案例。完整Python拟合在Jupyter执行，网页显示与重算实际冻结结果，不声称在浏览器重新训练模型。

## 与第6章相同的预测口径

- 2017年训练，2018年上半年验证，7至9月使用1/3/6小时共同的2169个目标时刻。
- 历史星期小时均值MAE为218.686383辆/小时，上周同期为264.055786辆/小时，均在全日共同目标上计算。基线沿用章节冻结文件的3位小数预测；生成脚本同时与原始训练均值核对舍入误差。
- 可切换全日、07-09时、16-18时、00-05时，选看ARIMA/SARIMA的三种提前量，并导出同一批逐小时观测与预测。
- 周期基线在三个提前量下不变，因为日历与上周值在所有起点已经可用；不是滑块失效。ARIMA/SARIMA使用不同起点的过滤状态。
- 旧版PPT和practice/reproduce.py包含2018年1至9月6533小时的入门比较（全局均值和历史星期小时均值）。它们仅作基础数据复现材料，不参与新版2169目标对照，也不与第6章2190小时补充接口混排。

## 真实视频的证据边界

MOT17-04为35秒、1050帧的真实夜间街道序列。课件点击后加载约12.6MB的H.264播放副本，并标出画面y=300像素的计数线。副本未改变尺寸、帧序和30Hz时间对应关系；模型推理仍使用官方原文件。

0.35阈值：参考15次、预测15次，但逐事件核验为13次正确、2次误计、2次漏计。0.60阈值：10次正确、1次误计、5次漏计。参考事件来自提供方人工框与ID按相同计数规则导出，不是本课另行标注。当前页面只展示裸视频、计数线和结果；具体目标框、身份及逐事件证据通过第8章入口核查。

结果是公开序列上的教学复核，不是独立场景泛化成绩；不推断行人身份、地理方向、通行能力或小时设计流量。[完整来源、模型、计数规则与许可](https://lilinchao.github.io/traffic-book-practice/open-course/chapters/VIDEO_LESSON.md)。

原有Vanderbilt环道与开放道路实验、RWTH highD研究视频保留为拓展，只在同意后连接YouTube；不下载或重传这些视频，校园网络无法播放时可使用文字备用讲解。

## 真实数据与许可

1. **UCI Metro Interstate Traffic Volume**。John Hogue，2019，DOI [10.24432/C5X60B](https://doi.org/10.24432/C5X60B)，CC BY 4.0。48,204行按同一本地小时标签整理为40,575小时，交通量无同小时冲突；天气保留标签集合，不补缺测，不重建UTC/夏令时时间轴。2018年仅到9月30日。
2. **NYC TLC绿出租车2024年1月**。[官方来源](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)。56,551原始行中保留56,549条当月上车记录，仅发布地区、日期类型与钟点汇总，不能代表所有出行或未满足需求，遵循原始开放数据条款。
3. **UCI Bike Sharing Dataset**与**NYC道路事故记录**。使用第4、5章同源统计和真实模型结果，保留[章节数据来源清单](https://lilinchao.github.io/traffic-book-practice/open-course/chapters/DATA_SOURCES.md)中的数据许可、覆盖与处理方式，不改称课程自有数据。
4. **MOT17-04**影像、标注及衍生事件摘要采用CC BY-NC-SA 3.0，署名Milan、Leal-Taixe、Reid、Roth、Schindler及MOTChallenge贡献者。非商业、署名与相同方式共享要求不能由课程代码MIT许可覆盖。OpenCV Zoo YOLOX为Apache-2.0，课堂包不包含模型权重。
5. 原创程序代码MIT，原创教学文字CC BY-SA 4.0；第三方数据、论文、视频与衍生摘要按各自条款处理，见LICENSE.txt。highD按官方条款申请，本课不分发其原始数据。
6. 封面cover.png沿用原AI生成蓝调夜色路口概念插画，不代表实际地点或实证资料。

## 隐私与复现

课堂测验沿用traffic-ch1-quiz-v1；研究方案另用traffic-ch1-project-brief-v1，本机存储，不上传、不评分。按任务分别保留草稿；清除当前草稿不清除其他任务或主项目笔记。存储不可用时提示及时导出。外部视频、资料与GitHub Pages仍有正常网络请求。

基础数据下载和清洗见practice/reproduce.py。新版证据快照data/project-bridge.js包含输入文件SHA-256、当前八章协议、2169目标预测、共享单车分时误差和夜间事件摘要。在完整仓库中运行：

```bash
node open-course/chapter-01/build-project-bridge.mjs
node --test open-course/chapter-01/tests/classroom.test.mjs
```

生成脚本只读取仓库内公开来源与结果，不读取学生作业、个人笔记或本机核查记录。离线包无需生成即可使用；重新生成需要完整仓库的chapters和projects数据。

## 原封面提示词（沿用）

> Use case: illustration-story. Create a sophisticated editorial illustration for an open university course on traffic data mining. Wide 16:9 landscape. Bird's-eye oblique view of a plausible urban intersection at blue hour transitioning into night, a few small cars, a bus, crosswalks, warm headlights, dark teal buildings, thin warm road markings. Crisp understated architectural painting with fine grain, rich midnight teal and muted amber, not cartoonish, not a map of any actual city. Concentrate the illuminated junction and buildings on the right half, left third mostly deep dark teal quiet negative space for editable slide title added later. No words, labels, letters, numbers, charts, graphs, bounding boxes, interface, logos or watermark. Scene is a conceptual illustration, not a documentary photograph. Intended as one full-bleed slide cover and web hero.
