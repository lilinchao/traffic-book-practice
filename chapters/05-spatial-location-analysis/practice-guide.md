# 第 5 章实践讲义：交通空间与位置数据分析

本讲义面向学生上机实践使用，不作为书籍正文。案例使用纽约市交通事故数据和华盛顿特区共享单车站点数据，目标是掌握空间数据的基本操作、空间自相关检验、空间聚类与热点检测、核密度估计以及空间回归建模。

## 1. 实践目标

完成本实践后，你应该能够：

- 从表格数据创建 GeoDataFrame，理解点、线、面三种空间数据类型。
- 检查和转换坐标参考系统（CRS），理解地图投影对距离和面积计算的影响。
- 构建 Queen 邻接权重矩阵与 K 近邻权重矩阵。
- 使用全局 Moran's I 和局部 Moran's I（LISA）检验事故率的空间自相关。
- 使用 DBSCAN 对碰撞点进行聚类，识别事故热点。
- 使用核密度估计（KDE）检测事故黑点。
- 建立 OLS 基线模型，诊断残差空间自相关，并拟合空间滞后模型（SLM）与空间误差模型（SEM）。

## 2. 数据集

本实践使用以下数据：

### 2.1 纽约市交通事故数据

| 文件 | 说明 |
| --- | --- |
| `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv` | 2023 年碰撞事故原始样本（5000 条） |
| `data/processed/nyc_crash_borough_month_panel_2023.csv` | 按行政区和月份汇总的面板数据 |

原始样本包含经纬度（`latitude`、`longitude`）、行政区（`borough`）、伤亡人数等字段，适合点级空间分析。

面板数据按 5 个行政区和 12 个月汇总，适合区级空间回归建模。

### 2.2 华盛顿特区共享单车站点数据

| 文件 | 说明 |
| --- | --- |
| `data/raw/capital_bikeshare_station_information.json` | 站点位置与容量信息 |
| `data/raw/capital_bikeshare_station_status.json` | 站点实时状态（可用车辆数、空桩数） |

共享单车站点数据作为辅助练习材料，用于空间点模式分析的补充练习。

### 2.3 行政区面状几何

纽约市 5 个行政区（曼哈顿、布鲁克林、皇后区、布朗克斯、史泰登岛）的面状边界可从 `geopandas` 内置数据集或 NYC Open Data 获取。本实践在代码中使用简化的行政区坐标字典构建面状几何。

## 3. 空间数据基本概念

### 3.1 空间数据类型

| 类型 | 说明 | 交通示例 |
| --- | --- | --- |
| 点（Point） | 零维，表示位置 | 事故发生点、共享单车站点 |
| 线（Line） | 一维，表示路径 | 道路段、公交线路 |
| 面（Polygon） | 二维，表示区域 | 行政区、交通小区、分析单元 |

### 3.2 空间效应

- **空间依赖性（Spatial Dependence）**：近邻区域的观测值相关，即"距离相近的事物更相似"（Tobler 地理学第一定律）。交通事故在空间上可能呈现聚集特征。
- **空间异质性（Spatial Heterogeneity）**：不同空间位置的关系或过程存在差异。例如，城市核心区与郊区的事故影响因子可能不同。
- **尺度效应与 MAUP**：分析结果随空间单元大小和边界划分而变化，即可面元问题（Modifiable Areal Unit Problem）。

## 4. 空间预处理

### 4.1 创建 GeoDataFrame

从 CSV 读取含经纬度的数据，使用 `geopandas.points_from_xy()` 创建点几何：

```python
import pandas as pd
import geopandas as gpd

df = pd.read_csv("../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv")
df = df.dropna(subset=["latitude", "longitude"])
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
    crs="EPSG:4326",
)
```

### 4.2 坐标系统检查与变换

- **EPSG:4326**（WGS84）是地理坐标系，单位为度，不能直接计算距离和面积。
- **EPSG:32618**（UTM Zone 18N）是投影坐标系，单位为米，适合纽约市区域分析。

变换操作：

```python
gdf_projected = gdf.to_crs(epsg=32618)
```

变换后坐标从 (经度, 纬度) 变为 (东移, 北移)，单位为米，可直接计算距离。

### 4.3 空间连接与空间聚合

- **空间连接（Spatial Join）**：将点事件与面状区域关联，例如把碰撞点分配到所属行政区。
- **空间聚合（Spatial Aggregation）**：按空间单元汇总统计量，例如统计每个行政区的事故总数和伤亡总人数。

## 5. 空间权重矩阵

空间权重矩阵 W 是空间自相关和空间回归的基础。

### 5.1 Queen 邻接权重

Queen 邻接定义相邻区域为共享边界或共享顶点的区域（类似国际象棋中皇后的走法）：

```python
from libpysal.weights import Queen

w_queen = Queen.from_dataframe(borough_gdf)
w_queen.transform = "r"  # 行标准化
```

### 5.2 K 近邻权重

K 近邻权重定义每个区域与其最近的 K 个区域相邻：

```python
from libpysal.weights import KNN

w_knn = KNN.from_dataframe(borough_gdf, k=5)
w_knn.transform = "r"
```

### 5.3 距离权重

基于距离衰减的权重矩阵，设定距离阈值或使用反距离函数：

```python
from libpysal.weights import DistanceBand

w_dist = DistanceBand.from_dataframe(borough_gdf, threshold=5000, binary=True)
```

## 6. 空间自相关

### 6.1 全局 Moran's I

全局 Moran's I 衡量整体空间自相关程度，取值范围为 [-1, 1]：

- I > 0：空间正相关（相似值聚集）
- I ≈ 0：空间随机
- I < 0：空间负相关（相异值聚集）

```python
from esda.moran import Moran

moran = Moran(borough_gdf["crash_rate"], w_queen)
print(f"Moran's I = {moran.I:.4f}, p = {moran.p_sim:.4f}")
```

### 6.2 Moran 散点图

Moran 散点图的四个象限：

| 象限 | 含义 |
| --- | --- |
| 右上（HH） | 高值被高值包围（热点） |
| 左下（LL） | 低值被低值包围（冷点） |
| 左上（HL） | 高值被低值包围（空间异常） |
| 右下（LH） | 低值被高值包围（空间异常） |

### 6.3 局部 Moran's I（LISA）

局部 Moran's I 识别每个空间单元的局部聚集模式：

```python
from esda.moran import Moran_Local

lisa = Moran_Local(borough_gdf["crash_rate"], w_queen)
```

LISA 显著性检验使用随机置换方法，将结果分为 HH、LL、HL、LH 四类聚集区，绘制 LISA 聚类图。

## 7. DBSCAN 空间聚类

DBSCAN（Density-Based Spatial Clustering of Applications with Noise）是一种基于密度的聚类方法，适合识别事故热点：

- **eps**：邻域半径（米），决定两个点是否为邻居。
- **min_samples**：核心点的最小邻居数，决定聚类的最小密度。

```python
from sklearn.cluster import DBSCAN

coords = gdf_projected[["longitude_proj", "latitude_proj"]].values
db = DBSCAN(eps=500, min_samples=15).fit(coords)
labels = db.labels_
```

DBSCAN 的优点：不需要预设聚类数、能发现任意形状的簇、可标识噪声点。

## 8. 核密度估计（KDE）

核密度估计用于生成空间密度的连续表面，识别事故黑点：

```python
from sklearn.neighbors import KernelDensity
import numpy as np

coords = gdf_projected[["longitude_proj", "latitude_proj"]].values
kde = KernelDensity(bandwidth=500, metric="euclidean").fit(coords)
```

- **带宽（bandwidth）** 是 KDE 的关键参数：带宽过小会导致密度面过于碎片化，带宽过大会过度平滑。
- 黑点定义为密度值超过全局 95% 分位数的区域。

## 9. 空间回归

### 9.1 OLS 基线模型

首先建立普通最小二乘回归作为基线：

```python
import statsmodels.api as sm

X = sm.add_constant(borough_gdf[["pop_density", "road_length"]])
y = borough_gdf["crash_rate"]
ols_model = sm.OLS(y, X).fit()
```

### 9.2 残差空间自相关诊断

如果 OLS 残差存在空间自相关，说明模型遗漏了空间效应：

```python
residual_moran = Moran(ols_model.resid, w_queen)
print(f"残差 Moran's I = {residual_moran.I:.4f}, p = {residual_moran.p_sim:.4f}")
```

### 9.3 空间滞后模型（SLM）

SLM 在回归中引入因变量的空间滞后项 W_y：

```
y = ρ W y + X β + ε
```

ρ 为空间自回归系数。若 ρ 显著为正，说明相邻区域的事故率对本区域有正向溢出效应。

### 9.4 空间误差模型（SEM）

SEM 在回归中引入误差项的空间依赖：

```
y = X β + u
u = λ W u + ξ
```

λ 为空间误差系数。若 λ 显著，说明遗漏的空间变量通过误差项产生了空间相关性。

### 9.5 模型选择

| 判断标准 | 选择建议 |
| --- | --- |
| 残差 Moran's I 仍显著 | 需要空间模型 |
| LM-Lag 显著、LM-Error 不显著 | 优先选择 SLM |
| LM-Error 显著、LM-Lag 不显著 | 优先选择 SEM |
| 两者均显著 | 比较稳健形式，选择更显著的 |
| 关注溢出效应 | 选择 SLM |
| 关注遗漏变量 | 选择 SEM |

## 10. 实践步骤概览

1. 加载 NYC 碰撞数据，创建点级 GeoDataFrame。
2. 检查并转换 CRS（EPSG:4326 → EPSG:32618）。
3. 空间聚合：按行政区汇总碰撞数与伤亡人数。
4. 构建行政区面状 GeoDataFrame 与空间权重矩阵。
5. 全局 Moran's I 检验与 Moran 散点图。
6. 局部 Moran's I（LISA）与聚类图。
7. DBSCAN 聚类识别事故热点。
8. KDE 检测事故黑点。
9. OLS 基线回归与残差 Moran's I 诊断。
10. SLM / SEM 空间回归建模与比较。

## 11. 学生任务

详见 `exercises.md`，分为基础（4 题）、进阶（4 题）、挑战（3 题）三个层次。

## 12. 延伸方向

- **地理加权回归（GWR）**：允许回归系数随空间位置变化，捕捉空间异质性。
- **MAUP 问题**：尝试不同空间单元划分（如网格、交通小区），比较分析结果。
- **时空扩展**：结合时间维度，构建时空权重矩阵与时空自相关分析。
- **共享单车数据**：使用 Capital Bikeshare 站点数据练习最近邻分析与空间点模式分析。
