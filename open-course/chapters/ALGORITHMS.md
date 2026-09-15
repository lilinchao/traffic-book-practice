# 第4—8章：真实数据上的章节算法

本轮在10篇交通工程案例中增加算法推导、输入与符号、实际计算结果、可切换图形及交通含义。网页切换的是已执行Python的输出，不是浏览器在线重训。原16案例结构、基础对照实验和学生笔记保持不变。

| 章节 | 本轮已执行 | 数据与交通对象 |
| --- | --- | --- |
| 4 | OLS、泊松GLM、验证选择离散参数的NB2 | UCI共享单车系统小时租借量 |
| 5 | 高斯KDE、6组DBSCAN、两类等量遮盖敏感性 | NYC2024年1月事故位置与候选排查范围 |
| 6 | ARIMA(2,0,0)、SARIMA(2,0,0)(1,0,0)24、残差检验 | I-94西向单断面1/3/6小时交通量预测 |
| 7 | 单区域AR、多区域VAR、12组时空画像KMeans与ARI | TLC绿出租车分区域小时运营量、典型服务日 |
| 8 | 常速度卡尔曼、带门限匈牙利关联、逐事件计数 | SinD匿名地面点重关联和交叉口通行调查 |

不要求一篇案例使用本章所有算法。没有真实输入或明确交通任务支持时，不强行加入图神经网络、插值定位、视觉检测或实例分割。

## 复现

下载完整章节材料包并解压，在包含`chapters/`和`projects/`的目录执行。Python建议3.12，使用独立虚拟环境；下列版本对应本轮实际计算环境，完整版本号另记在每份JSON中。

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r chapters/python/algorithm-requirements.txt
python chapters/python/case_algorithms.py --chapter all
python chapters/python/test_case_algorithms.py
node chapters/build-algorithm-evidence.mjs
node chapters/build-casebook.mjs
node chapters/tests/algorithms.test.mjs
```

仅复现一章可将`all`改为`4`至`8`。默认更新`chapters/data/algorithms/chN.json`；也可用`--output`写入另一目录保留发布结果，随后自行比较。生成网页汇总的Node脚本读取默认位置。数值优化在不同平台/线性代数库下可能有细微差别，尤其是聚类局部解；不要只按文件字节相同判断算法复现成功。

只阅读结果无需Python依赖。`build-algorithm-evidence.mjs`从五份完整JSON生成轻量网页模块，`case-algorithm-ui.js`把相同表格与解读写入网页和Markdown；不在脚本中另填一套展示数字。完整JSON保留逐条预测、密度、DBSCAN标签、日型成员与中心、轨迹重关联及事件列表。

## 训练与评价边界

- 第4章：2011年训练、2012上半年验证、下半年测试4376小时；预处理只拟合训练集，排除标签组成项。NB2的alpha为验证选择而非联合极大似然估计。本轮精简编码且无正则惩罚，不与旧岭回归协议混用。
- 第5章：7068个已知有效点、2069个固定评价位置；KDE为归一化概率密度。人为遮盖20%不表示真实缺失率；未知474条记录不补造位置。局部距离近似不替代正式工程投影检验。
- 第6章：训练2017年；2018上半年报告验证，7—9月共同2169个目标。缺测保留NaN，利用起点过滤状态而非平滑状态。参数固定，起点随h变化。已公开教学测试期不是全新独立部署检验；p值下溢为0不表示数学概率为零。
- 第7章：四区域预测按1—21日/22—24日/25—31日划分；验证选择p，滚动一步预测不重训。全月聚类独立用于探索，不将其作为留出预测特征。VAR使用跨区域时间关系，不包含路网拓扑；单月验证不证明全年泛化。
- 第8章：算法只接收时间与匿名位置，原ID仅用于事后核查。提供方平滑地面轨迹不是检测输出，也非独立人工真值；不报告YOLO成绩、MOTA或IDF1。总事件数一致不是计数100%正确。

## 方法来源与许可

回归和状态空间模型采用statsmodels；KDE、DBSCAN、KMeans使用scikit-learn；VAR以同一最小二乘定义在scikit-learn中实现。匈牙利求解使用SciPy，卡尔曼与计数实现为本课程原创教学代码，借鉴SORT的运动预测与关联思想，未复制完整SORT程序，不声称复现其边界框基准。

参考：[statsmodels GLM](https://www.statsmodels.org/stable/glm.html)、[SARIMAX](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)、[VAR](https://www.statsmodels.org/stable/vector_ar.html)、[scikit-learn DBSCAN](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html)、[SORT作者仓库](https://github.com/abewley/sort)。每篇案例另列对应方法说明。

数据来源和处理链见`DATA_SOURCES.md`。代码开源不覆盖第三方数据许可；SinD含禁止商业使用条款，须保留原许可与引用。派生JSON同样受原数据条件约束。
