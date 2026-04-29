# 04 Traffic Tabular Data Analysis

本章使用英国 STATS19 交通事故表格数据，演示如何围绕因变量、自变量和控制变量设计建模案例，并分析自变量对事故严重程度、伤亡人数和弱势交通参与者伤亡数的影响。

## Dataset

- Raw collision table: `../../data/raw/stats19_collision_2023.csv`
- Raw casualty table: `../../data/raw/stats19_casualty_2023.csv`
- Processed teaching sample: `../../data/processed/stats19_collision_casualty_tabular_2023_sample.csv`
- Notebook: `../../notebooks/chapter-04/traffic_accident_panel_analysis.ipynb`
- Practice guide: `practice-guide.md`
- Model result tables: `../../data/results/chapter-04/`

## Practice Goals

- 读取并理解交通事故表格数据
- 区分因变量、自变量和控制变量
- 使用逻辑回归分析严重事故概率
- 使用泊松回归和负二项回归分析伤亡人数
- 使用零膨胀泊松模型分析弱势交通参与者伤亡数
- 讨论相关性模型和严格因果识别之间的边界
- 输出模型结果表、情景预测表和可视化图表

## Refresh Data

```bash
bash scripts/download_case_data.sh
python3 scripts/build_stats19_tabular_case.py
```

## Run Notebook

```bash
pip install -r requirements.txt
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

Execute all cells and save outputs:

```bash
bash scripts/execute_chapter04_notebook.sh
```
