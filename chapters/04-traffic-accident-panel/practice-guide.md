# 第 4 章实践讲义：交通事故面板数据分析

本讲义面向学生上机实践使用，不作为书籍正文。请配合 Notebook 一起完成：

`notebooks/chapter-04/traffic_accident_panel_analysis.ipynb`

## 1. 实践目标

完成本实践后，你应该能够：

- 解释什么是事件级交通事故数据。
- 将事故记录聚合为 `borough-month` 面板数据。
- 用图表比较不同地区和月份的事故变化。
- 构造简单的事故风险指标。
- 使用逻辑回归分析二分类交通安全问题。
- 使用泊松回归和负二项回归分析事故次数。
- 使用零膨胀模型理解稀有事故结果中的大量零值。
- 说明模型结果能解释什么、不能解释什么。

## 2. 数据背景

本实践使用 NYC Motor Vehicle Collisions Crashes 开放数据。

数据源：

https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

本仓库提供两份本地数据：

| 文件 | 说明 |
| --- | --- |
| `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv` | 事故事件级样本，每行是一条事故记录 |
| `data/processed/nyc_crash_borough_month_panel_2023.csv` | 2023 年行政区-月份面板数据 |

原始样本适合做字段理解、缺失值检查、事故原因分析。面板数据适合做趋势分析和回归建模。

## 3. 分析问题

本案例围绕四个问题展开：

1. 纽约不同 borough 的事故数量是否有明显差异？
2. 事故数量和受伤率是否存在月度变化？
3. 事故次数这类计数数据应该如何建模？
4. 死亡人数这类稀有结果为什么适合考虑零膨胀模型？

这些问题不是因果识别问题。我们不会声称某个 borough 或某个月“导致”事故增加，而是学习如何用数据描述、比较和建模交通安全现象。

## 4. 环境准备

在仓库根目录安装依赖：

```bash
pip install -r requirements.txt
```

打开 Notebook：

```bash
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

如果需要重新执行全部单元并保存输出：

```bash
bash scripts/execute_chapter04_notebook.sh
```

## 5. 实践流程

### 5.1 读取事故记录

先读取原始事故样本：

```python
crashes = pd.read_csv(RAW_PATH, parse_dates=["crash_date"])
crashes.head()
```

重点观察：

- `crash_date` 和 `crash_time`：事故发生时间。
- `borough`：事故所在行政区。
- `latitude` 和 `longitude`：事故位置。
- `number_of_persons_injured`：受伤人数。
- `number_of_persons_killed`：死亡人数。
- `contributing_factor_vehicle_1`：主要事故因素。

原始数据是一条事故一行，属于事件级数据。事件级数据粒度细，但通常会有缺失值、异常值和字段不统一的问题。

### 5.2 检查数据质量

重点检查几个字段的缺失率：

```python
important_cols = [
    "crash_date",
    "borough",
    "latitude",
    "longitude",
    "number_of_persons_injured",
    "number_of_persons_killed",
    "contributing_factor_vehicle_1",
]

crashes[important_cols].isna().mean().sort_values(ascending=False)
```

思考：

- 如果 `borough` 缺失，能不能用经纬度补全？
- 如果事故原因缺失，是否应该把它当成 `Unspecified`？
- 如果经纬度为 0 或缺失，地图分析会受到什么影响？

### 5.3 理解事故原因

使用 `contributing_factor_vehicle_1` 统计常见事故原因：

```python
top_factors = (
    crashes["contributing_factor_vehicle_1"]
    .fillna("Unspecified")
    .value_counts()
    .head(12)
)
```

这一步的目的不是建立模型，而是理解数据中有哪些主要现象。交通事故数据常见原因包括注意力不集中、未让行、跟车过近、倒车不当等。

### 5.4 构造面板数据

面板数据有两个基本维度：

- 个体维度：这里是 `borough`
- 时间维度：这里是 `month`

本实践使用的面板数据已经聚合好：

```python
panel = pd.read_csv(PANEL_PATH)
```

每一行代表“某个 borough 在某个月”的事故统计。

你需要检查它是否是平衡面板：

```python
panel.groupby("borough")["month"].nunique()
```

如果每个 borough 都有 12 个月，说明这是一个平衡面板。平衡面板便于教学和建模，但真实项目中经常会遇到缺失月份。

## 6. 可视化解读

可视化预览页：

`chapters/04-traffic-accident-panel/visuals.html`

### 6.1 月度事故趋势

图表：

`assets/chapter-04/01_monthly_crash_trends.png`

解读重点：

- Brooklyn 和 Queens 的事故数量通常较高。
- Staten Island 的事故数量明显较低。
- 直接比较事故数量时，需要注意地区面积、人口、道路长度和交通量差异。

### 6.2 事故热力图

图表：

`assets/chapter-04/02_crash_heatmap.png`

热力图适合快速定位高值区域。横轴是月份，纵轴是 borough，颜色越深表示事故数量越高。

### 6.3 受伤率趋势

图表：

`assets/chapter-04/03_injury_rate_trends.png`

受伤率定义为：

```text
persons_injured / crashes * 100
```

它表示每 100 起事故对应的受伤人数。这个指标可以弱化事故总量差异，但仍然不是完整的风险指标，因为它没有控制交通暴露量。

### 6.4 伤亡结构

图表：

`assets/chapter-04/04_injury_structure.png`

比较行人、骑行者和机动车使用者的受伤人数。这个图可以帮助我们讨论不同交通参与者的安全风险。

## 7. 模型案例

### 7.1 逻辑回归

逻辑回归用于二分类问题。本实践构造：

```text
high_injury_rate = injury_rate_per_100_crashes 是否高于样本中位数
```

模型问题：

```text
某个 borough-month 是否属于高受伤率月份？
```

示例模型：

```python
logit_model = smf.logit(
    "high_injury_rate ~ crashes + summer + C(borough)",
    data=model_df,
).fit()
```

解释方式：

- 系数为正：变量增加时，高受伤率月份的 log-odds 增加。
- `np.exp(coef)` 是 odds ratio。
- odds ratio 大于 1 表示高受伤率的优势比增加。
- odds ratio 小于 1 表示高受伤率的优势比降低。

注意：逻辑回归结果是相关性解释，不是因果解释。

### 7.2 泊松回归

泊松回归用于计数型因变量。本实践用它建模：

```text
crashes
```

模型问题：

```text
某个 borough-month 的事故次数如何随月份和 borough 变化？
```

示例模型：

```python
poisson_model = smf.poisson(
    "crashes ~ month_centered + C(borough)",
    data=model_df,
).fit()
```

解释方式：

- 泊松回归默认使用 log link。
- `np.exp(coef)` 可以解释为 incidence rate ratio。
- 如果 IRR 为 1.10，表示对应变量增加时，期望事故次数约增加 10%。

关键假设：

```text
条件均值 = 条件方差
```

如果方差明显大于均值，就可能存在过度离散。

### 7.3 负二项回归

负二项回归适合处理过度离散的计数数据。

在本案例中，可以比较泊松回归和负二项回归的 AIC：

```python
model_comparison = pd.DataFrame({
    "model": ["Poisson", "Negative Binomial"],
    "aic": [poisson_model.aic, negative_binomial_model.aic],
})
```

如果负二项模型的 AIC 更低，说明它在当前数据上可能更合适。

解释重点：

- 泊松模型假设较强。
- 负二项模型允许方差大于均值。
- 交通事故次数通常受很多未观测因素影响，容易过度离散。

### 7.4 零膨胀模型

零膨胀模型适合大量零值的计数因变量。本实践用：

```text
persons_killed
```

某些 borough-month 死亡人数为 0。这个 0 可能来自两种机制：

1. 结构性零值：该观察单位几乎不会出现死亡事故。
2. 抽样零值：有风险，但这个月没有发生。

零膨胀模型把这两种机制拆开：

- 零膨胀部分：解释是否属于结构性零值状态。
- 计数部分：解释非结构性零值下的事件次数。

示例模型：

```python
zip_model = ZeroInflatedPoisson(
    endog=model_df["persons_killed"],
    exog=zip_exog,
    exog_infl=zip_infl,
    exposure=model_df["crashes"],
).fit()
```

这里使用 `crashes` 作为 exposure，含义是事故总数越多，死亡人数的暴露机会也越多。

## 8. 结果解释边界

这份实践数据适合教学，但解释时要保持克制：

- 不能直接说某个 borough 更危险，因为没有控制人口、道路里程、交通量和出行方式结构。
- 不能直接说某个月导致事故增加，因为没有控制天气、节假日、施工、执法等因素。
- 样本数据和聚合数据的来源不同，适合教学演示，不适合直接发表结论。
- 模型结果主要用于理解方法，而不是给出政策建议。

更严谨的分析需要加入：

- 人口或车辆保有量
- 道路长度和道路等级
- 交通流量或出行量
- 天气数据
- 节假日和重大事件
- 空间邻近关系

## 9. 学生任务

### 基础任务

1. 读取原始事故样本。
2. 统计每个 borough 的事故数量。
3. 统计最常见的 10 类事故原因。
4. 读取面板数据并检查是否平衡。
5. 绘制月度事故趋势图。

### 进阶任务

1. 构造 `injury_rate_per_100_crashes`。
2. 找出受伤率最高的 5 个 borough-month。
3. 构造 `high_injury_rate` 并拟合逻辑回归。
4. 拟合泊松回归并解释一个 IRR。
5. 比较泊松回归和负二项回归的 AIC。

### 挑战任务

1. 用 `persons_killed` 拟合零膨胀泊松模型。
2. 比较 `crashes` 作为 exposure 前后的模型差异。
3. 自己选择一个外部变量，例如天气或人口，设计一个扩展研究问题。
4. 写一段 300 字以内的结果解读，必须包含“可以说明什么”和“不能说明什么”。

## 10. 提交要求

建议提交以下内容：

- 执行完成的 Notebook。
- 至少 3 张图表。
- 一个模型结果表。
- 300-500 字分析说明。
- 一段局限性说明。

分析说明建议包含：

1. 你分析了什么问题？
2. 你使用了哪些数据字段？
3. 你发现了什么模式？
4. 模型结果如何解释？
5. 这个分析还有哪些不足？

## 11. 延伸方向

如果想继续扩展，可以尝试：

- 将纽约事故数据扩展到多年。
- 合并 NYC Traffic Volume Counts，加入交通流量。
- 合并天气数据，分析雨雪天气下的事故变化。
- 使用经纬度做空间聚类。
- 将 borough 换成 ZIP code 或道路路段，构造更细粒度面板。
