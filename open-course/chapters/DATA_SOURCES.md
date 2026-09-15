# 数据来源、处理与许可

本轮数据准备日期为2026-09-14。页面样例、案例数字和基线结果均来自分发的真实数据快照，不使用手工生成数组冒充实测数据。完整文件哈希见资料包`MANIFEST.json`；原始下载哈希和处理元数据见相应JSON文件。

## UCI I-94交通量：第1、2、3、6章

- 官方：[Metro Interstate Traffic Volume](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume)
- 下载：[原始ZIP](https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip)
- John Hogue (2019)，DOI:10.24432/C5X60B，CC BY 4.0。
- 原始ZIP SHA-256：`b99aeabcbd6cc86f642da3a79d90883425798f58abd3b3302da2fa19dda73768`。
- 原始48,204行，40,575个不同小时，7,629重复行。第2章`ch02_raw.csv`是原始压缩CSV的解压内容，保留天气字段；不是重新合成的数据。
- `ch02_cleaning.py`核查同一小时交通量冲突后合并。该文件没有冲突小时；其他文件若冲突则停止，不能任意取第一行。
- 不恢复夏令时，不将缺测填0，保留数据范围和原始行权重。`projects/python/prepare_data.py`给出完整准备过程。
- 第3章按2017年日期组织07、08、09时交通量，只有三小时均观测到的日期进入样本。358个完整日期、7个排除日期；`peak_mean`为三个小时流量均值，单位辆/小时。日级Bootstrap用来讨论抽样不确定性，不消除选择偏差或相邻日期相关性。
- 第6章训练2017年，验证2018年1至6月，练习测试7至9月。模型在每个预测跨度内使用共同有效样本；1小时接口有2,190条。滚动起点信息可用性、基线与特征说明见`projects/DATA_SOURCES.md`和准备代码。

## UCI Bike Sharing：第4章

- 官方：[Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)
- 下载：[原始ZIP](https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip)
- Hadi Fanaee-T (2013)，DOI:10.24432/C5W894，CC BY 4.0。
- 使用ZIP内真实`hour.csv`，实际读取17,379行。官网页面元信息可能显示不同记录数量，以本次读取文件与哈希为准。原始压缩包SHA-256见`chapters/data/ch04.json`的`meta.sha256`。
- 2011年8,645行训练；2012年1至6月4,358行验证；2012年7至12月4,376行练习测试。
- 特征为温度、体感温度、湿度、风速与季节/月/时/假日/星期/工作日/天气类别。温度等按原始UCI定义归一化，见`BIKE_README.txt`。类别编码使用OneHotEncoder；数值标准化只在训练集拟合。
- `cnt`是目标。`casual`和`registered`之和等于`cnt`，两者从特征文件中排除。原`instant`重命名为`id`，用于对齐，不输入模型。日期只用于切分。
- 训练均值、岭回归与泊松回归均从同一训练集拟合。岭回归alpha候选1、10、100；泊松回归alpha候选0.001、0.1、1；各自只用验证RMSE选参数，不在练习测试标签上选择。岭回归负预测截为0，处理规则对验证与测试相同。
- 给定实测天气的条件回归不等于天气未知时的提前预测。跨年需求变化可能造成系统性偏差。
- `ch04_solution.csv`是公开自测标签。`ch04.json`也包含公开标签和基线预测；不能将浏览器自测宣称为隐藏测试。

## NYC事故：第5章

- 官方：[Motor Vehicle Collisions - Crashes](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95)。遵循NYC Open Data原始条款。
- 完整查询2024年1月，并用独立count查询核对7,542条记录。7,068条通过坐标检查，474条排除。
- 使用近似米制网格，原点经度-74.3、纬度40.45，东西距离按纬度40.73换算。网格不是道路边界，也不是正式风险估计。没有暴露量分母。
- 查询、下载哈希与字段选择见`projects/DATA_SOURCES.md`、`projects/data/crashes.json`和准备代码。不分发姓名或车牌。

## NYC TLC：第7章

- 官方：[Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)。遵循NYC TLC原始条款。
- 原始2024年1月绿出租车文件56,551行；按上车时间保留当月56,549行，排除2条非当月记录。
- 课程只分发日期—行政区—小时聚合，不分发个人轨迹。行政区保留Manhattan、Brooklyn、Queens、Bronx、Staten Island、EWR和Unknown。
- 平日为周一至周五，不剔除节假日；当月23个平日、8个周末日。夜间22至05时。日均分母来自所选完整日历日期，而不是只统计有记录的日期。
- 不能从上车量直接推断所有需求或未满足需求。详细来源与哈希见公共项目数据说明。

## SinD天津轨迹：第8章

- 官方：[SOTIF-AVLab/SinD](https://github.com/SOTIF-AVLab/SinD)，固定提交`930e4dea78d924c6e9a58ff8e378331f93bba8ec`。
- `Data/Tianjin/8_2_1/Veh_smoothed_tracks.csv`原始129,273行。课程保留前120秒11,531点、77条轨迹，xy保留4位小数。
- 此数据是提供方已平滑的地面轨迹，不是课程检测器结果。未包含独立行人文件、原视频或人工计数真值。
- 原始CSV SHA-256：`c377452a22ad0d57e2ebc9a8bccf050ef50c32c10ce35d7984a12edc24e532b5`，与Git LFS对象核对。
- 原许可带有禁止商业使用等自定义条款，**不是标准CC0**。分发副本保留`projects/data/SIND-LICENSE.txt`。课程MIT代码许可不改变这些限制。
- 计数规则按轨迹ID与方向去重，长断点重置连接。事件时间为首次在另一侧被观测到的采样时间。没有独立人工真值时只报告规则敏感性，不报告完整系统准确率。

## 案例与参考页面

### 完整案例的结果证据

2026-09-15工程案例版不更换原始快照，扩展为30张结果或材料核查表。新增计算包括：7地区服务规模与夜间占比；调查区间相对半宽；共享单车07—09、16—18时及其他时段的冻结预测误差与未抵消低估量占比；I-94同样本的重点时段误差；皇后区平日与周末分时日均；SinD按30秒窗口的分方向事件数。每一项都从下列带哈希文件生成，不手工编造交通观测。

低估量占比定义为Σmax(实测−估计,0)/Σ实测，不是缺车率；道路高峰窗口为预设钟点而非拥堵标签；30秒窗不表示信号周期。新区间指标、分时统计及方向计数由`tests/cases.test.mjs`独立核对。研究区域、单位、工程用途与缺少的数据在每篇全文中给出。

16篇完整案例使用`case-studies.js`中的课程原创分析和`data/case-evidence.js`中的固定结果表。后者由`build-case-evidence.mjs`计算或汇总，记录10个实际输入文件的SHA-256。网页与案例册不手工编造数值；统计口径在每篇结果部分列出。案例场景属于教学分析，不是管理部门已经实施的项目或治理成效报告。

日画像聚类实际运行现有`projects/python/extensions.py --project taxi`，使用scikit-learn 1.9.1、random_state=42、n_init=10，对31日×168维日内占比矩阵比较K=2/3/4/5。`case-cluster-comparison.csv`保存样本内轮廓系数，`case-day-clusters-4.csv`保存K=4日期分组，`case-cluster-centers-4.csv`保存对应中心向量。这些是从同一TLC真实快照计算的派生数据，不是新的交通观测；许可沿用TLC原始条款。没有实施的跨种子、跨月份稳定性检验不作数值结论。

第三章案例的主结果表统一采用1000次重采样，并解释旧500次示例与它之间的计算差异。第六章基线案例使用1小时任务全部2190个目标时刻，多跨度案例则先取三个任务共有的2169个目标时刻；两种口径不混用。第八章仍只评价给定平滑轨迹的规则敏感性，无独立真值的评价层不填准确率。

网页、单篇下载和完整`CASEBOOK.md`由同一份内容与证据生成。修改源数据、聚类输出或案例文字后，应依次重建证据与案例册，再运行案例一致性测试并更新资料包。

16个案例为本课程结合上述数据编写的中文解读，不是搬运Kaggle文章。页面组织参考[House Prices项目](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques/overview)的任务、数据、代码、评价与提交结构；未使用其房价数据、图片、Logo或参赛者成绩。
