"""
第二章 编程实践基础 — 交通数据探索性分析（起始代码）

任务：完成以下 TODO 部分，对交通流量数据进行读取、清洗、变换、聚合与可视化。

数据源：
  - data/raw/nyc_traffic_volume_counts_sample.csv
  - data/processed/nyc_crash_borough_month_panel_2023.csv
  - data/raw/chicago_cta_daily_boarding_sample.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Book/
TRAFFIC_PATH = PROJECT_ROOT / "data" / "raw" / "nyc_traffic_volume_counts_sample.csv"
CRASH_PATH = PROJECT_ROOT / "data" / "processed" / "nyc_crash_borough_month_panel_2023.csv"
CTA_PATH = PROJECT_ROOT / "data" / "raw" / "chicago_cta_daily_boarding_sample.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"

# ── Matplotlib 中文支持 ──────────────────────────────────
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# ── 小时列名映射 ─────────────────────────────────────────
HOUR_COLUMNS = {
    "_12_00_1_00_am": 0, "_1_00_2_00am": 1, "_2_00_3_00am": 2,
    "_3_00_4_00am": 3, "_4_00_5_00am": 4, "_5_00_6_00am": 5,
    "_6_00_7_00am": 6, "_7_00_8_00am": 7, "_8_00_9_00am": 8,
    "_9_00_10_00am": 9, "_10_00_11_00am": 10, "_11_00_12_00pm": 11,
    "_12_00_1_00pm": 12, "_1_00_2_00pm": 13, "_2_00_3_00pm": 14,
    "_3_00_4_00pm": 15, "_4_00_5_00pm": 16, "_5_00_6_00pm": 17,
    "_6_00_7_00pm": 18, "_7_00_8_00pm": 19, "_8_00_9_00pm": 20,
    "_9_00_10_00pm": 21, "_10_00_11_00pm": 22, "_11_00_12_00am": 23,
}


def load_and_clean(csv_path: str) -> pd.DataFrame:
    """读取交通流量数据并进行基础清洗。

    TODO:
      1. 读取 CSV
      2. 将 date 列解析为 datetime
      3. 将小时列重命名为 hour_00, hour_01, ..., hour_23
      4. 检查缺失值，区分缺失值与零流量
      5. 返回清洗后的 DataFrame
    """
    # TODO: 实现数据读取与清洗
    raise NotImplementedError("请完成数据读取与清洗")


def wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """将宽表转换为长表。

    TODO:
      1. 使用 pd.melt 将每小时一列转换为 (hour, volume) 格式
      2. 映射小时列名为 0-23 整数
      3. 返回长表 DataFrame
    """
    # TODO: 实现宽表转长表
    raise NotImplementedError("请完成宽表转长表")


def groupby_analysis(df_long: pd.DataFrame) -> None:
    """分组聚合分析。

    TODO:
      1. 按路段计算日均流量
      2. 按路段 + 小时计算平均小时流量（24 小时流量曲线）
      3. 计算早晚高峰流量比（早高峰 7-9 时 / 全天平均）
    """
    # TODO: 实现分组聚合
    raise NotImplementedError("请完成分组聚合分析")


def time_series_analysis() -> None:
    """时间序列重采样分析（使用 Chicago CTA 数据）。

    TODO:
      1. 读取 CTA 数据，将 service_date 设为索引
      2. 按周重采样计算周均客流
      3. 按月重采样计算月度客流总和
      4. 计算 7 日滚动平均
    """
    # TODO: 实现时间序列分析
    raise NotImplementedError("请完成时间序列分析")


def visualize_traffic_flow(df_long: pd.DataFrame) -> None:
    """可视化交通流量数据。

    TODO:
      1. 绘制某路段 24 小时流量折线图，标注早晚高峰
      2. 绘制 Top 20 路段 24 小时流量热力图
    """
    # TODO: 实现可视化
    raise NotImplementedError("请完成可视化")


def visualize_crash_data() -> None:
    """可视化事故面板数据。

    TODO:
      1. 读取 nyc_crash_borough_month_panel_2023.csv
      2. 绘制各行政区事故数量箱线图
    """
    # TODO: 实现事故数据可视化
    raise NotImplementedError("请完成事故数据可视化")


def main() -> None:
    """主函数：读取 → 清洗 → 变换 → 聚合 → 可视化。"""
    print("=" * 60)
    print("第二章 交通数据探索性分析练习")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 读取与清洗
    print("\n[1] 读取与清洗数据...")
    df = load_and_clean(str(TRAFFIC_PATH))
    print(f"    数据维度: {df.shape}")

    # 2. 宽表转长表
    print("\n[2] 宽表转长表...")
    df_long = wide_to_long(df)
    print(f"    长表维度: {df_long.shape}")

    # 3. 分组聚合
    print("\n[3] 分组聚合分析...")
    groupby_analysis(df_long)

    # 4. 时间序列
    print("\n[4] 时间序列分析...")
    time_series_analysis()

    # 5. 可视化
    print("\n[5] 可视化...")
    visualize_traffic_flow(df_long)
    visualize_crash_data()

    print("\n完成！图表保存在:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
