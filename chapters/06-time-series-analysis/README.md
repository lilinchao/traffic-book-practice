# 06 交通时序数据分析

本章使用合成交通流量数据与 NYC 交通流量样本数据，演示时序数据预处理、统计特征分析、平稳性检验、ARIMA 建模、LSTM 建模、DTW 模式相似性比较以及短期预测全流程。

## Dataset

- 合成 5 分钟交通流量数据：`../../data/processed/synthetic_traffic_flow_5min.csv`
- NYC 交通流量样本：`../../data/raw/nyc_traffic_volume_counts_sample.csv`
- Chicago CTA 日均客流样本：`../../data/raw/chicago_cta_daily_boarding_sample.csv`

## Practice Files

| 文件 | 说明 |
| --- | --- |
| `starter/timeseries_practice.py` | 起始代码：数据加载、基础可视化、ACF/PACF 框架 |
| `solution/timeseries_practice.py` | 完整方案：预处理、ADF 检验、ARIMA、LSTM、模型对比、DTW |
| `exercises.md` | 习题：基础 4 题、进阶 4 题、挑战 3 题 |
| `practice-guide.md` | 实践讲义：覆盖全流程操作指引 |

## Practice Goals

- 加载并预处理交通流量时序数据（时间解析、缺失值处理、重采样）
- 分析趋势、日/周周期性，绘制 ACF/PACF 图
- 使用 ADF 检验判断时序平稳性
- ARIMA 建模：阶数选择、拟合、残差诊断、滚动预测
- LSTM 建模：滑动窗口构建、时间顺序划分、训练与预测
- 基线对比：历史均值 vs ARIMA vs LSTM
- DTW 比较不同检测器的日流量模式相似性
- 按时段（高峰/平峰）和预测步长进行误差分析

## Generate Synthetic Data

```bash
python3 scripts/generate_synthetic_flow.py
```

输出：`data/processed/synthetic_traffic_flow_5min.csv`

## Run Practice

```bash
pip install -r requirements.txt

# 起始代码
python chapters/06-time-series-analysis/starter/timeseries_practice.py

# 完整方案
python chapters/06-time-series-analysis/solution/timeseries_practice.py
```
