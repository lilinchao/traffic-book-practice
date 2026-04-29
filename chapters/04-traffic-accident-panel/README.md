# 04 Traffic Accident Panel Analysis

本章使用纽约交通事故开放数据，演示如何从事件级事故记录构造“行政区-月份”面板数据，并完成描述性分析与回归建模案例。

## Dataset

- Raw sample: `../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`
- Processed panel: `../../data/processed/nyc_crash_borough_month_panel_2023.csv`
- Data dictionary: `../../data/dictionaries/nyc_motor_vehicle_collisions.md`
- Notebook: `../../notebooks/chapter-04/traffic_accident_panel_analysis.ipynb`
- Practice guide: `practice-guide.md`

## Practice Goals

- 读取并检查事故记录数据
- 处理日期、行政区和伤亡数字段
- 构造 borough-month 面板数据
- 分析不同 borough 的事故数量和伤亡变化
- 识别样本中的常见事故原因
- 使用逻辑回归识别高受伤率月份
- 使用泊松回归和负二项回归建模事故次数
- 使用零膨胀泊松模型建模死亡事故计数

## Refresh Data

```bash
bash scripts/download_case_data.sh
```

Run the command from the repository root. The processed panel is downloaded as a grouped result from the NYC Open Data API so it covers all 12 months of 2023.

## Run Notebook

```bash
pip install -r requirements.txt
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

Execute all cells and save outputs:

```bash
bash scripts/execute_chapter04_notebook.sh
```
