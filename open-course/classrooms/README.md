# 第3至8章交互课堂

在线入口：<https://lilinchao.github.io/traffic-book-practice/open-course/classrooms/>

各章保留独立入口`chapter-03/`至`chapter-08/`，每章附PPT、教学页、真实数据实验、课堂讨论、记录导出和既有Python完整项目及案例链接。教材小节对应来自《交通数据挖掘理论与应用》符号释义与教学逻辑修订清洁合稿的已核验提取稿，本轮不修改书稿。

## 教学组织

- 第3章：早高峰抽样调查，微积分、概率、矩阵、优化和建模评价相互联系。
- 第4章：共享单车高峰服务量估计，OLS、Poisson、NB2、分类与零膨胀的适用范围。
- 第5章：事故空间排查，质量审计、距离、网格、KDE、DBSCAN与道路现场核查。
- 第6章：断面小时交通量预测，时间协议、周期性、ARIMA/SARIMA、多提前量评价与DTW。
- 第7章：出租车分区分时运营，地区矩阵、AR/VAR、日型聚类和稳定性。
- 第8章：影像交通调查，分类/检测/分割/跟踪、匿名关联、通行事件与独立影像核验。

讲授内容比主实验范围更宽。PCA、逻辑回归、零膨胀、空间回归、LSTM和图神经网络等页面为方法解释与适用性讨论，不声称已完成这些模型训练。

## 实际计算与冻结结果

真实观测直接计算：日差分、常数最小二乘梯度下降、日期分布、条件比例、日级Bootstrap、坐标覆盖、网格与排序、全部7068点到2069固定位置的高斯KDE、2017小时曲线、成对滞后相关、24小时DTW、出租车分母/占比、SinD跨线事件。

冻结预测评价：第4章OLS/Poisson/NB2，第6章周期基线及ARIMA/SARIMA，第7章AR/VAR等。网页按选择的时段或地区重新计算误差，不重新拟合。第6章使用算法主协议2169共同目标，不混入旧版2190小时任务。

已有算法结果浏览：DBSCAN的六套成员标签、KMeans的12套日型成员和稳定性结果、SinD位置保持与卡尔曼匿名关联。显示既有Python真实运行输出，不把切换结果称为训练。完整重算代码在`../chapters/python/case_algorithms.py`及本章工作本。

数学演示：NB2方差曲线使用指定均值10/50/100/200/500和可调α，明确标记为公式演示，不作为实测数据。

第6章滞后相关按确切小时标签配对，并各自计算Pearson相关，不冒充所有软件默认ACF。DTW使用绝对代价与有限错位带，未按路径长度归一化。第5章地图为局部距离散点图，没有道路底图或风险暴露量。

## 代码与运行

每章代码页可编辑并实际执行JavaScript。输入为该章数据副本，公共函数`runLab(id,data,config)`与参数实验一致。代码运行在可终止的Worker中，限时20秒，文字输出限制100000字符，可恢复默认、停止、重试和下载代码。下载的代码片段需在网页编辑器运行或自行提供`data`与`runLab`，不是可单独双击的程序。完整Python实践使用既有Jupyter工作本。

静态网站不含云端计算、账号或收作业服务。默认课堂代码不上传数据。自行编写的代码仍具有浏览器允许的网络能力，因此只运行可信代码，不粘贴密钥或个人资料。输入内容显示前进行HTML转义。本机记录按章节隔离，只保存最近50次手动记录；存储失败会提示并允许立即导出，清空需确认。

页面使用ES模块，需HTTP访问。仓库根目录可用`python -m http.server 8000`后打开`http://localhost:8000/open-course/classrooms/`。不依赖外部CDN或在线Python运行时，所有数值输入来自同站固定快照；本版本未提供可直接双击的单文件离线HTML。第8章视频使用已发布H.264副本，点击播放，不自动下载完整影片。

## 数据与许可

输入文件SHA-256及教材提取稿校验在`manifest.json`。源数据的固定获取时间和处理范围保留在各输入元数据；课程使用历史快照，不宣称反映当前交通状况。

- [UCI I-94 / John Hogue (2019)](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume)，CC BY 4.0。单向断面小时资料，不恢复夏令时。原始行无空单元格不代表时间索引无缺口。
- [UCI Bike Sharing / Hadi Fanaee-T (2013)](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)，CC BY 4.0。课程实际hour.csv分割总计17379小时，使用文件计数，不采用网页摘要中的17389。casual和registered不作为特征。
- [NYC事故](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95)及[TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)，遵守各源原始条款。事故计数不等于单位暴露风险，上车记录不等于全部出行需求。
- [SinD](https://github.com/SOTIF-AVLab/SinD)，固定课程提交和120秒天津平滑轨迹，遵守[自定义非商业条款](../projects/data/SIND-LICENSE.txt)。源ID审计不代替影像独立真值。
- [MOT17-04](https://motchallenge.net/data/MOT17/)，夜间步行街行人序列，CC BY-NC-SA 3.0。原始影像、转码与模型来源见[影像来源说明](../chapters/data/video/sources.json)与[许可](../chapters/data/video/LICENSE.md)。YOLOX模型为Apache-2.0。影像协议独立于SinD。

课程原创代码MIT、原创讲解CC BY-SA 4.0，详见课程总许可。第三方数据、影像及其衍生材料不由课程MIT或CC BY-SA许可重新授权。

## 核验

`node --test classrooms/tests/classrooms.test.mjs`检查真实数据计算、冻结预测样本、KDE数值一致性、参数边界和教材章节覆盖。浏览器检查另覆盖所有教学页、代码真实执行、停止恢复、记录导出、窄屏和投影键盘操作。
