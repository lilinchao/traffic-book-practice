# 05 交通空间与位置数据分析

本章使用纽约市交通事故数据与华盛顿特区共享单车站点数据，演示空间数据的基本概念、空间预处理、空间权重矩阵与空间自相关、空间聚类与热点检测、空间插值、空间点模式分析以及空间回归等方法。

## Dataset

- 原始碰撞记录：`../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`
- 区级月度面板：`../../data/processed/nyc_crash_borough_month_panel_2023.csv`
- 共享单车站点信息：`../../data/raw/capital_bikeshare_station_information.json`
- 共享单车站点状态：`../../data/raw/capital_bikeshare_station_status.json`
- 实践讲义：`practice-guide.md`
- 练习题：`exercises.md`

## Practice Goals

- 理解空间数据的基本类型（点、线、面）与空间效应
- 掌握坐标系统检查、地图投影与坐标变换
- 构建 Queen 邻接与 K 近邻空间权重矩阵
- 使用全局与局部 Moran's I 检验事故率的空间自相关
- 使用 DBSCAN 识别事故热点聚集
- 使用 KDE 检测事故黑点
- 建立 OLS 基线模型，通过残差 Moran's I 判断空间依赖，并拟合 SLM/SEM

## Refresh Data

```bash
bash scripts/download_case_data.sh
```

## Run Practice

```bash
pip install -r requirements.txt
python starter/spatial_analysis_practice.py   # 起始模板
python solution/spatial_analysis_practice.py  # 完整解答
```

## Spatial Packages

本实践额外依赖以下空间分析包：

- `geopandas` — 空间数据结构与操作
- `libpysal` — 空间权重矩阵构建
- `esda` — 空间自相关统计量
- `pointpats` — 空间点模式分析

安装方式：

```bash
pip install geopandas libpysal esda pointpats
```
