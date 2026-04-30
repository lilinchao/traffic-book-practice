# 第 7 章实践讲义：交通时空数据分析

本讲义面向学生上机实践使用，不作为书籍正文。案例使用合成城市路网速度数据，目标是学习交通时空数据的组织、分析与预测方法。

## 1. 实践目标

完成本实践后，你应该能够：

- 区分时空数据中的观测对象与分析对象，理解空间粒度和时间粒度的含义。
- 将长表数据转换为节点-时间矩阵、张量、图结构等不同组织形式。
- 计算时间自相关、空间自相关和时空耦合相关性。
- 实践时间对齐、空间匹配和缺失值处理等预处理步骤。
- 使用时滞互相关分析拥堵的空间传播方向与时间延迟。
- 使用 DTW + K-means 对路段进行速度模式聚类。
- 构建历史平均、VAR、XGBoost 和图神经网络等多类时空预测模型。
- 按空间区域和预测步长进行模型比较与误差分析。

## 2. 数据集

本实践使用合成城市路网速度数据，由 `scripts/generate_synthetic_network.py` 生成。

| 文件 | 说明 |
| --- | --- |
| `data/processed/synthetic_network_speed.csv` | 速度长表：节点ID、时间戳、速度值 |
| `data/processed/synthetic_network_adjacency.npz` | 邻接矩阵（稀疏格式） |
| `data/processed/synthetic_network_nodes.csv` | 节点信息：ID、x坐标、y坐标、区域标签 |

数据特征：

- 路网规模：15 个节点
- 时间范围：4 周，5 分钟间隔
- 速度范围：20-80 km/h，含早晚高峰模式
- 邻接关系：无向图，约 20 条边

## 3. 时空数据基本概念

### 3.1 观测对象与分析对象

- 观测对象：固定检测器（如线圈、卡口）所在的位置，数据采集的物理位置。
- 分析对象：路网中的路段或交叉口，是建模和决策的基本空间单元。
- 两者关系：观测对象可以是分析对象的子集；当检测器覆盖不足时，需要空间插值。

### 3.2 空间粒度与时间粒度

- 空间粒度：路段级 → 交叉口级 → 交通小区(TAZ)级 → 城市级。粒度越细，空间异质性越强，数据需求越大。
- 时间粒度：5 分钟 → 15 分钟 → 1 小时 → 1 天。粒度越细，时间动态越丰富，噪声影响也越大。
- 粒度选择原则：根据分析目的和数据可用性平衡。短时预测宜用细粒度，战略规划可用粗粒度。

### 3.3 边界效应

路网边缘的节点只有部分邻居在研究区域内，导致：

- 空间统计量（如空间自相关）计算不完整。
- 图神经网络消息传递时信息来源不对称。
- 解决思路：扩展研究区域、使用虚拟边界节点、或在分析时标注边界影响。

## 4. 数据组织方式

### 4.1 长表格式

最原始的存储形式，每行一条记录：

| node_id | timestamp | speed |
| --- | --- | --- |
| N01 | 2024-01-01 00:00 | 55.2 |
| N01 | 2024-01-01 00:05 | 53.8 |

优点：灵活，易追加；缺点：查询和矩阵运算效率低。

### 4.2 节点-时间矩阵

行为节点、列为时间步：

```
         t1    t2    t3   ...
N01    55.2  53.8  51.0
N02    48.3  47.1  46.5
...
```

适合时间序列分析和矩阵分解。转换方法：

```python
speed_matrix = speed_long.pivot(index='node_id', columns='timestamp', values='speed')
```

### 4.3 张量

节点 x 时间 x 特征的三维组织方式，适合多变量时空数据：

```
shape = (num_nodes, num_timesteps, num_features)
```

例如 `num_features` 可包含速度、流量、占有率。张量组织方式便于与深度学习模型对接。

### 4.4 图结构与邻接矩阵

图结构 = 节点集合 V + 边集合 E + 邻接矩阵 A。

邻接矩阵 A 是 |V| x |V| 的矩阵，`A[i][j] = 1` 表示节点 i 和 j 相邻。

图结构是图神经网络的基础输入，同时支持空间统计分析。

## 5. 邻接矩阵构建

### 5.1 拓扑邻接矩阵

基于路网连通性，有物理连接则 `A[i][j] = 1`。

```python
# 从边列表构建
import numpy as np
A = np.zeros((num_nodes, num_nodes))
for i, j in edges:
    A[i][j] = 1
    A[j][i] = 1  # 无向图
```

### 5.2 距离邻接矩阵

基于节点间距离构建，常用高斯核加权：

```
A_dist[i][j] = exp(-d(i,j)^2 / sigma^2)
```

其中 `d(i,j)` 是节点间距离，`sigma` 是核宽度参数。距离邻接矩阵是稠密的，可以设阈值截断。

### 5.3 相关性邻接矩阵

基于速度序列的相关系数构建：

```
A_corr[i][j] = |corr(speed_i, speed_j)|
```

相关性邻接矩阵反映功能连接而非物理连接，适合发现远程交通关联。

## 6. 时空相关性分析

### 6.1 时间自相关

使用自相关函数（ACF）衡量时间序列的滞后相关性：

```python
from statsmodels.tsa.stattools import acf
acf_values = acf(speed_series, nlags=288)  # 一天的5分钟间隔数
```

交通速度通常具有日周期性（lag=288 对应 24 小时）和周周期性（lag=2016 对应一周）。

### 6.2 空间自相关

使用 Moran's I 衡量空间相关性：

```
I = (N / W) * sum_i sum_j w_ij (x_i - x_bar)(x_j - x_bar) / sum_i (x_i - x_bar)^2
```

I > 0 表示空间正相关（相邻节点速度相似），I < 0 表示空间负相关。

### 6.3 时滞互相关

检测拥堵传播方向与时间延迟：

```python
from numpy import correlate
def time_lagged_cc(x, y, max_lag):
    ccs = []
    for lag in range(-max_lag, max_lag + 1):
        cc = np.corrcoef(x[:len(x)-abs(lag)], np.roll(y, -lag)[:len(y)-abs(lag)])[0, 1]
        ccs.append((lag, cc))
    return ccs
```

最佳滞后对应的 `lag` 表示信号从 x 传播到 y 的时间，`cc` 表示传播强度。

## 7. DTW + K-means 聚类

### 7.1 动态时间规整（DTW）

DTW 衡量两条时间序列在时间轴弹性对齐后的距离，对速度模式的相位偏移（高峰出现时间不同）具有鲁棒性。

```python
from tslearn.metrics import dtw
distance = dtw(series_a, series_b)
```

### 7.2 K-means 聚类

以 DTW 距离矩阵为输入，对路段进行聚类：

```python
from sklearn.cluster import KMeans
dtw_matrix = compute_dtw_matrix(all_series)  # N x N
kmeans = KMeans(n_clusters=3, random_state=42)
labels = kmeans.fit_predict(dtw_matrix)
```

聚类结果可解释为：高峰明显型、平缓型、夜低昼高型等速度模式。

## 8. 时空预测模型

### 8.1 历史平均基线

取同一时间片历史速度的均值作为预测值：

```python
pred = train_data.groupby(['hour', 'weekday'])['speed'].mean()
```

简单但常作为基线。无法应对非周期性事件（事故、天气）。

### 8.2 VAR 模型

向量自回归模型，捕捉多节点间的线性动态关系：

```
Y_t = c + A_1 * Y_{t-1} + A_2 * Y_{t-2} + ... + A_p * Y_{t-p} + e_t
```

其中 Y_t 是所有节点在时刻 t 的速度向量。

```python
from statsmodels.tsa.api import VAR
model = VAR(train_matrix.T)  # 输入为时间 x 节点
results = model.fit(maxlags=12)
forecast = results.forecast(train_matrix.T.values[-12:], steps=12)
```

VAR 的局限：节点多时参数爆炸，且仅捕捉线性关系。

### 8.3 XGBoost 特征工程

将时空预测转化为监督学习问题，关键在于特征设计：

| 特征类别 | 具体特征 | 说明 |
| --- | --- | --- |
| 时间滞后 | speed(t-1), speed(t-2), ..., speed(t-12) | 目标节点近期速度 |
| 邻居滞后 | neighbor_mean(t-1), neighbor_mean(t-2) | 邻居节点近期速度均值 |
| 时间特征 | hour, weekday, is_weekend | 周期性模式 |
| 空间特征 | degree, betweenness, neighbor_mean | 网络拓扑属性 |
| 历史特征 | hist_mean_same_hour, hist_std_same_hour | 同一时段历史统计 |

```python
import xgboost as xgb
model = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1)
model.fit(X_train, y_train)
pred = model.predict(X_test)
```

XGBoost 的优势：非线性拟合能力强，特征重要性可解释；局限：不显式建模空间结构。

### 8.4 图神经网络（STGCN / DCRNN）

图神经网络显式利用路网拓扑进行信息传递：

- STGCN：图卷积 + 时间卷积的交替堆叠，捕捉空间依赖和时间依赖。
- DCRNN：扩散卷积 + GRU，用图上的随机游走模拟交通扩散过程。

图神经网络需要以下输入：

1. 特征张量：`(batch, num_nodes, num_timesteps, num_features)`
2. 邻接矩阵：`(num_nodes, num_nodes)`
3. 预测目标：下一个时间步的速度

图神经网络的优势：显式利用图结构，适合大规模路网；局限：训练复杂度高，需要较多数据。

## 9. 模型比较与误差分析

### 9.1 评价指标

| 指标 | 公式 | 说明 |
| --- | --- | --- |
| MAE | mean(\|y - y_hat\|) | 平均绝对误差 |
| RMSE | sqrt(mean((y - y_hat)^2)) | 均方根误差 |
| MAPE | mean(\|y - y_hat\| / y) | 平均绝对百分比误差 |

### 9.2 分区域误差分析

将节点按位置分为中心区域和边缘区域，分别计算误差：

- 中心节点：邻居多，信息丰富，预测误差通常更低。
- 边缘节点：邻居少，受边界效应影响，预测误差通常更高。

### 9.3 分步长误差分析

按预测步长（1/3/6/12 步）分别计算误差：

- 短期预测（1-3 步）：各模型差异较小，历史平均即可。
- 中期预测（6 步）：需要时空信息的模型优势显现。
- 长期预测（12 步）：图神经网络通常保持更好的性能。

## 10. 实践流程

1. 生成数据：`python scripts/generate_synthetic_network.py`
2. 数据加载与长表转换：读取 CSV，转换为节点-时间矩阵。
3. 探索性分析：可视化速度时空分布、邻接矩阵热力图。
4. 时空相关性分析：ACF、时滞互相关、Moran's I。
5. 路段聚类：DTW 距离矩阵 + K-means，分析聚类模式。
6. 模型构建与预测：历史平均 → VAR → XGBoost。
7. 模型比较：分区域、分步长计算误差，绘制对比图。
8. （挑战）图神经网络：STGCN 或 DCRNN 预测。

## 11. 学生任务

### 基础任务

1. 运行数据生成脚本，读取数据并了解其结构。
2. 将长表转换为节点-时间矩阵，检查缺失值。
3. 绘制路网拓扑图和节点速度时间序列。
4. 选取两个相邻节点，计算并可视化其时滞互相关。

### 进阶任务

1. 构建 DTW 距离矩阵，进行路段聚类并分析模式。
2. 拟合 VAR 模型，预测未来 1 小时速度。
3. 构建高斯核距离邻接矩阵，与拓扑邻接矩阵对比。
4. 拟合 XGBoost 模型，对比与 VAR 的预测误差。

### 挑战任务

1. 实现完整的模型比较框架：历史平均、VAR、XGBoost，分区域分步长分析。
2. 使用图神经网络（STGCN 或 DCRNN）进行预测。
3. 撰写分析结论，讨论各模型优缺点及适用场景。
