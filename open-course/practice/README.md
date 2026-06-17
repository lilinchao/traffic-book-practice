# 《交通数据挖掘理论与应用》实践代码

本目录为第3至第8章案例提供可复现代码。脚本首次运行时自动下载允许直接获取的数据；需要接受数据使用条款的数据则由读者手动下载。

## 在线真实数据核心实验

网页中的在线实验使用小样本真实数据，适合课堂即时演示；完整数据下载、批量清洗和模型训练放在本目录的离线脚本中。

| 章节 | 在线实验 | 数据来源 |
|---|---|---|
| 第2章 | MTA GTFS线路与班次连接查询 | MTA NYCT Subway GTFS Static |
| 第2章 | NYC黄色出租车早高峰OD热力图 | NYC TLC Yellow Taxi Trip Records |
| 第3章 | NYC事故样本的贝叶斯受伤风险更新 | NYC Motor Vehicle Collisions |
| 第3章 | UCI共享单车小时需求梯度下降 | UCI Bike Sharing |
| 第3章 | UCI共享单车多项式过拟合观察 | UCI Bike Sharing |
| 第4章 | NYC各区受伤事故计数基线 | NYC Motor Vehicle Collisions |
| 第5章 | MTA 1号线站点直线距离与线路距离 | MTA NYCT Subway GTFS Static |
| 第5章 | GeoLife GPS点投影到候选道路 | Microsoft GeoLife |
| 第5章 | NYC交通事故坐标DBSCAN热点识别 | NYC Motor Vehicle Collisions |
| 第6章 | Metro I-94小时交通量短时预测 | UCI Metro Interstate Traffic Volume |
| 第7章 | PeMS-SF检测器时空矩阵切片 | UCI PeMS-SF |
| 第8章 | KITTI车辆框IoU与重复检测 | KITTI Object Detection |

## 数据与章节对应

| 章节 | 实践主题 | 数据来源 | 运行方式 |
|---|---|---|---|
| 第3章 | 损失函数、梯度下降与线性回归 | UCI Bike Sharing | `python ch03_linear_regression.py` |
| 第4章 | 泊松与负二项计数回归 | UCI Bike Sharing | `python ch04_count_regression.py` |
| 第5章 | 事故点位KDE与DBSCAN热点 | NYC Open Data | `python ch05_spatial_hotspots.py` |
| 第6章 | 周期基线与SARIMA预测 | UCI Bike Sharing | `python ch06_time_series.py` |
| 第7章 | 多检测器时空滞后预测 | UCI PeMS-SF | `python ch07_spatiotemporal.py` |
| 第8章 | YOLO检测、跟踪与过线计数 | UA-DETRAC | `python ch08_vehicle_counting.py VIDEO_PATH` |

## 数据来源

- UCI Bike Sharing: https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset
- NYC Motor Vehicle Collisions - Crashes: https://data.cityofnewyork.us/d/h9gi-nx95
- UCI PeMS-SF: https://archive.ics.uci.edu/dataset/204/pems+sf
- UA-DETRAC: https://detrac-db.rit.albany.edu/

UCI 数据页面标注为 CC BY 4.0。NYC 数据通过官方开放数据 API 按限定年份和行数读取。UA-DETRAC 需要读者按照其网站条款下载视频，本项目不重新分发视频文件。

## 环境

建议使用 Python 3.11 或 3.12。第3至第7章安装基础依赖：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

第8章需要 PyTorch、OpenCV 和 Ultralytics，安装包较大，应单独安装：

```powershell
python -m pip install -r requirements-vision.txt
```

运行结果保存在 `outputs`，下载的数据保存在 `data`。这两个目录不应打包进书稿附件，发布时只提供代码和数据下载说明。
