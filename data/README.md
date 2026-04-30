# Case Data

本目录包含交通分析各章的教学数据集。

`raw/` 中的原始数据通过脚本下载，不纳入 git 追踪。正式使用前请核对各数据源的许可证、引用要求和再分发规则。

## 下载原始数据

```bash
bash scripts/download_case_data.sh
```

## 生成合成数据

部分章节使用合成数据，无需下载：

```bash
python scripts/generate_synthetic_flow.py       # 第 6 章：5 分钟交通流量
python scripts/generate_synthetic_network.py     # 第 7 章：路网速度时空数据
```

## 文件说明

| 文件 | 章节 | 来源 | 用途 |
| --- | --- | --- | --- |
| `raw/stats19_collision_2023.csv` | 4 | UK DfT STATS19 | 碰撞事故表 |
| `raw/stats19_casualty_2023.csv` | 4 | UK DfT STATS19 | 伤亡人员表 |
| `processed/stats19_collision_casualty_tabular_2023_sample.csv` | 4 | STATS19 衍生 | 逻辑回归/泊松/零膨胀建模 |
| `results/chapter-04/*.csv` | 4 | STATS19 模型输出 | 模型系数、比较与情景预测 |
| `raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv` | 4/5 | NYC Open Data | 事故记录与空间分析 |
| `processed/nyc_crash_borough_month_panel_2023.csv` | 4 | NYC Open Data | 行政区-月份面板数据 |
| `raw/nyc_traffic_volume_counts_sample.csv` | 4/6 | NYC Open Data | 交通流量面板数据 |
| `raw/chicago_cta_daily_boarding_sample.csv` | 6 | Chicago Data Portal | 日客流时序分析 |
| `raw/capital_bikeshare_station_information.json` | 5 | Capital Bikeshare GBFS | 站点位置与空间分析 |
| `raw/capital_bikeshare_station_status.json` | 5 | Capital Bikeshare GBFS | 站点状态分析 |
| `processed/synthetic_traffic_flow_5min.csv` | 6 | 合成数据 | 5 分钟交通流量时序预测 |
| `processed/synthetic_network_speed_5min/` | 7 | 合成数据 | 路网速度时空预测 |

## 数据源链接

- NYC Traffic Volume Counts: https://data.cityofnewyork.us/Transportation/Traffic-Volume-Counts/btm5-ppia
- NYC Motor Vehicle Collisions Crashes: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
- UK DfT STATS19 Road Safety Data: https://data.dft.gov.uk/road-accidents-safety-data/
- Chicago CTA Daily Boarding Totals: https://data.cityofchicago.org/Transportation/CTA-Ridership-Daily-Boarding-Totals/6iiy-9s97
- Capital Bikeshare GBFS: https://capitalbikeshare.com/system-data
