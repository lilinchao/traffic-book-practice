# 02 编程实践基础

本章实践目标：掌握数据库操作、Python 数据处理与可视化三大基础技能，为后续章节的建模与分析打下工程基础。

## Goals

- 使用 SQLite 存储与查询交通数据（建表、CRUD、聚合、多表连接）
- 用 Pandas 完成交通流量数据的读取、清洗、变换与聚合
- 用 Matplotlib / Seaborn 绘制时间序列图、箱线图、热力图等常见交通可视化图表
- 识别并避免时间序列分析中的常见陷阱（时间解析、缺失值与零值区分、数据泄漏）

## Files

- `exercises.md`: 分级练习（基础 / 进阶 / 挑战）
- `practice-guide.md`: 实践指南与关键要点
- `starter/traffic_db_practice.py`: 数据库操作起始代码
- `starter/traffic_eda_practice.py`: 数据处理与可视化起始代码
- `solution/traffic_db_practice.py`: 数据库操作参考实现
- `solution/traffic_eda_practice.py`: 数据处理与可视化参考实现

## Setup

```bash
cd /home/szu-ciic/桌面/Book
pip install -r requirements.txt
```

## Practice

1. 阅读 `practice-guide.md` 了解整体工作流程。
2. 从 `starter/` 开始，按照 `exercises.md` 中的任务逐步完成。
3. 完成后与 `solution/` 中的参考实现对比。

## Datasets

本章使用以下数据集（已在 `data/` 目录中）：

| 文件 | 用途 |
| --- | --- |
| `data/raw/nyc_traffic_volume_counts_sample.csv` | 路段小时交通流量数据，用于数据库建表与 EDA |
| `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv` | NYC 交通事故记录，用于多表连接与聚合查询 |
| `data/processed/nyc_crash_borough_month_panel_2023.csv` | NYC 按行政区-月度汇总的面板数据，用于分组统计与可视化 |
| `data/raw/chicago_cta_daily_boarding_sample.csv` | 芝加哥公交日客流数据，用于时间序列处理与可视化 |

## Validation

```bash
python chapters/02-programming-fundamentals/solution/traffic_db_practice.py
python chapters/02-programming-fundamentals/solution/traffic_eda_practice.py
```
