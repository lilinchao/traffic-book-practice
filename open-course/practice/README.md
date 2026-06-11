# 《交通数据挖掘理论与应用》实践代码

本目录为第3至第8章案例提供可复现代码。脚本首次运行时自动下载允许直接获取的数据；需要接受数据使用条款的数据则由读者手动下载。

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
