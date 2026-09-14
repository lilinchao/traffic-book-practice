# 第1章 绪论：开放课堂

按《交通数据挖掘理论与应用》最新清洁合稿第一章制作。建议本科生两学时、约90分钟。PPT和网页讲义共42页，保留教材1.1至1.6的主线。

## 使用

- 在线入口：https://lilinchao.github.io/traffic-book-practice/open-course/chapter-01/
- 本地使用：解压离线网页包后打开 `index.html`，数据与脚本已打包，不需要安装软件或启动服务器。
- 顶部“课堂投影”逐页讲授，左右方向键或翻页按钮操作。互动内容较长时可纵向滚动。
- `chapter-01.pptx` 是可编辑PowerPoint版本。每页备注包含教师提示、资料依据和对应网页链接。
- 本地包中的下载链接依赖所含文件；离线包自身不重复包含另一个离线包。
- 视频仅提供官方播放入口，没有下载或重传第三方视频。播放依赖网络和平台可用性。每段视频均有观看问题与无法播放时的文字说明。
- 测验选择只保存在本机浏览器，没有账号、分析追踪或后台上传。

## 课堂安排

| 环节 | 建议时间 | 重点活动 |
| --- | --- | --- |
| 导览 | 5分钟 | 交通现象与学习目标 |
| 1.1 概述 | 15分钟 | 无事故拥堵、官方视频、任务配对 |
| 1.2 分析基础 | 20分钟 | 暴露量、时间泄漏、I-94真实数据 |
| 1.3 数据类型 | 20分钟 | 夜间流量、天气、出租车偏差、逐帧计数 |
| 1.4 公开数据集 | 10分钟 | 无人机视频、数据适配与许可 |
| 1.5 常用方法 | 10分钟 | 历史均值基线、预测与因果区别 |
| 1.6 学习与练习 | 10分钟 | 小组研究方案、课堂测验、总结 |

第三个视频是拓展讨论，可留到课后。12个交互模块不要求每个都在90分钟内完整展开，可选择性演示后供学生自行探索。

## 案例与数据

13个案例情境包括：无事故拥堵、路口任务配对、流量与状态、事故数量与暴露量、预测信息可获得性、I-94日变化、夜间流量、天气关联、出租车样本偏差、时间聚合、夜间影像、通行计数、简单预测基线。

真实数据：

1. **UCI Metro Interstate Traffic Volume**。John Hogue，2019，DOI [10.24432/C5X60B](https://doi.org/10.24432/C5X60B)，[数据页](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume)。I-94西向ATR301单检测点，原始48,204行，按本地时间标签合并为40,575个小时，合并7,629条重复天气记录。交通量在同小时无冲突。天气保留标签集合，不同天气组可以重叠。未补齐时间缺口。2018年覆盖截至9月30日，不能当作全年。温度从K转换为摄氏度只用于阅读。CC BY 4.0，课件对数据进行了上述处理。
2. **NYC TLC绿出租车2024年1月**。[官方记录页](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)。原始56,551行，仅按上车时间保留当月56,549行，未按车费、里程或乘客人数清洗。按上车行政区、日类型和钟点汇总，不公开单趟轨迹。数据仅反映该出租车样本，记录准确性及用途限制遵循官方条款。

原始下载哈希与处理摘要保存在 `data/metro.json` 和 `data/taxi.json` 的 `meta` 部分。整理时间2026-09-14。

教学示例：事故率输入值、环道移动减速波动画、三帧跨线计数坐标、任务和数据匹配练习。均不伪装成真实观测、完整交通仿真或检测模型输出。

## 复现

`practice/reproduce.py` 会从官方地址下载两组原始数据，输出清洁样本、出租车汇总和两种基线MAE。Python 3.10及以上，需要pandas和pyarrow。运行命令及依赖见脚本开头。

训练集固定为2017年，测试集为2018年1至9月的6,533个有效小时。全局均值MAE为1723.8辆/小时，星期几与小时均值MAE为259.2辆/小时。图表显示值按需要四舍五入，网页计算使用未取整值。结果不是跨数据集方法排名。

## 许可和素材

- 原创程序代码：MIT。原创教学文字：CC BY-SA 4.0。署名为“交通数据挖掘理论与应用开放课程（lilinchao）”。
- UCI样本遵循CC BY 4.0，须保留John Hogue及数据集引用，并标明处理方式。
- NYC数据遵循其原始开放数据条款。不将其改称本项目自有或MIT数据。
- Vanderbilt、RWTH、BDD100K的论文和视频保留各自版权，只链接官方来源。highD按官方条款申请，本课程不分发原始数据。
- 封面 `cover.png` 为内置图像生成工具制作的概念插画，不代表实际地点。项目内允许随课件使用，必须保留“概念插画”的说明。

封面提示词：

> Use case: illustration-story. Create a sophisticated editorial illustration for an open university course on traffic data mining. Wide 16:9 landscape. Bird's-eye oblique view of a plausible urban intersection at blue hour transitioning into night, a few small cars, a bus, crosswalks, warm headlights, dark teal buildings, thin warm road markings. Crisp understated architectural painting with fine grain, rich midnight teal and muted amber, not cartoonish, not a map of any actual city. Concentrate the illuminated junction and buildings on the right half, left third mostly deep dark teal quiet negative space for editable slide title added later. No words, labels, letters, numbers, charts, graphs, bounding boxes, interface, logos or watermark. Scene is a conceptual illustration, not a documentary photograph. Intended as one full-bleed slide cover and web hero.

## 视频清单

1. [Vanderbilt环道交通实验](https://www.youtube.com/watch?v=bcx-v7og8Zc)：观察减速传播，讨论封闭环道的边界。
2. [RWTH highD官方演示](https://www.youtube.com/watch?v=L_buu-lqJVo)：观察车辆身份和轨迹，讨论位置、时间与速度。
3. [Vanderbilt Quantum Potential](https://www.youtube.com/watch?v=SnROMkdXYJc)：讨论开放道路控制实验与评价。

所有视频均可从网页进入对应机构发布页。网页不承诺所有校园网络均能播放外部平台。
