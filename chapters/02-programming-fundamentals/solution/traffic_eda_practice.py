"""
第二章 编程实践基础 — 交通数据探索性分析（参考实现）

功能：读取、清洗、变换、聚合与可视化交通流量数据。
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
plt.rcParams["figure.dpi"] = 150

# ── 小时列名映射 ─────────────────────────────────────────
HOUR_COLUMNS = {
    "_12_00_1_00_am": 0, "_1_00_2_00am": 1, "_2_00_3_00am": 2,
    "_3_00_4_00am": 3, "_4_00_5_00am": 4,
    "_5_00_6_00am": 5, "_6_00_7_00am": 6, "_7_00_8_00am": 7,
    "_8_00_9_00am": 8, "_9_00_10_00am": 9, "_10_00_11_00am": 10,
    "_11_00_12_00pm": 11, "_12_00_1_00pm": 12, "_1_00_2_00pm": 13,
    "_2_00_3_00pm": 14, "_3_00_4_00pm": 15, "_4_00_5_00pm": 16,
    "_5_00_6_00pm": 17, "_6_00_7_00pm": 18, "_7_00_8_00pm": 19,
    "_8_00_9_00pm": 20, "_9_00_10_00pm": 21, "_10_00_11_00pm": 22,
    "_11_00_12_00am": 23,
}

# 可读的小时列名（用于重命名）
HOUR_READABLE = {col: f"hour_{h:02d}" for col, h in HOUR_COLUMNS.items()}


# ══════════════════════════════════════════════════════════
# 1. 数据读取与清洗
# ══════════════════════════════════════════════════════════

def load_and_clean(csv_path: str) -> pd.DataFrame:
    """读取交通流量数据并进行基础清洗。"""
    df = pd.read_csv(csv_path)
    print(f"  原始数据: {df.shape[0]} 行, {df.shape[1]} 列")

    # 解析日期
    df["date"] = pd.to_datetime(df["date"], format="ISO8601")

    # 重命名小时列为可读格式
    hour_cols = [c for c in df.columns if c in HOUR_READABLE]
    df.rename(columns=HOUR_READABLE, inplace=True)

    # 检查缺失值
    hour_col_names = [f"hour_{h:02d}" for h in range(24)]
    missing_per_col = df[hour_col_names].isnull().sum()
    total_missing = missing_per_col.sum()
    print(f"  小时流量列缺失值总数: {total_missing}")

    # 区分缺失值与零值
    zero_counts = (df[hour_col_names] == 0).sum().sum()
    print(f"  小时流量列零值总数: {zero_counts}")
    print(f"  注意: 零值可能是真实零流量（如凌晨），缺失值可能是检测器故障")

    # 将 0 值保留为 0，不做填充（区分于缺失值）
    # 如果确认某些 0 值应为缺失，可在此处理：
    # df[hour_col_names] = df[hour_col_names].replace(0, np.nan)

    # 添加日期特征
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek  # 0=周一, 6=周日
    df["is_weekend"] = df["day_of_week"].isin([5, 6])

    return df


# ══════════════════════════════════════════════════════════
# 2. 宽表转长表
# ══════════════════════════════════════════════════════════

def wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """将宽表转换为长表。"""
    hour_col_names = [f"hour_{h:02d}" for h in range(24)]
    id_vars = ["id", "segmentid", "roadway_name", "from", "to",
               "direction", "date", "year", "month", "day_of_week", "is_weekend"]

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=hour_col_names,
        var_name="hour_col",
        value_name="volume",
    )

    # 提取小时数字
    df_long["hour"] = df_long["hour_col"].str.extract(r"hour_(\d+)").astype(int)
    df_long.drop(columns=["hour_col"], inplace=True)

    # 转换 volume 为数值
    df_long["volume"] = pd.to_numeric(df_long["volume"], errors="coerce")

    print(f"  长表维度: {df_long.shape}")
    print(f"  缺失值: {df_long['volume'].isnull().sum()}")
    return df_long


# ══════════════════════════════════════════════════════════
# 3. 分组聚合分析
# ══════════════════════════════════════════════════════════

def groupby_analysis(df_long: pd.DataFrame) -> None:
    """分组聚合分析。"""
    print("\n── 分组聚合分析 ──────────────────────────────────")

    # 1. 各路段日均流量
    daily_segment = df_long.groupby(["segmentid", "date"])["volume"].sum().reset_index()
    segment_avg = daily_segment.groupby("segmentid")["volume"].mean().sort_values(ascending=False)
    print("\n[各路段日均流量 Top 10]")
    print(segment_avg.head(10).to_string())

    # 2. 24 小时平均流量曲线
    hourly_profile = df_long.groupby("hour")["volume"].mean()
    print("\n[24 小时平均流量]")
    print(hourly_profile.to_string())

    # 3. 早晚高峰流量比
    morning_peak = df_long[df_long["hour"].between(7, 9)]["volume"].mean()
    evening_peak = df_long[df_long["hour"].between(17, 19)]["volume"].mean()
    daily_mean = df_long["volume"].mean()
    print(f"\n[早晚高峰流量比]")
    print(f"  早高峰(7-9时)均值: {morning_peak:.1f}")
    print(f"  晚高峰(17-19时)均值: {evening_peak:.1f}")
    print(f"  全天均值: {daily_mean:.1f}")
    print(f"  早高峰/全天: {morning_peak / daily_mean:.2f}")
    print(f"  晚高峰/全天: {evening_peak / daily_mean:.2f}")

    # 4. 工作日 vs 周末
    weekday_weekend = df_long.groupby(["is_weekend", "hour"])["volume"].mean().unstack(level=0)
    weekday_weekend.columns = ["工作日", "周末"]
    print("\n[工作日 vs 周末 小时流量对比]")
    print(weekday_weekend.to_string())


# ══════════════════════════════════════════════════════════
# 4. 时间序列重采样
# ══════════════════════════════════════════════════════════

def time_series_analysis() -> None:
    """时间序列重采样分析（使用 Chicago CTA 数据）。"""
    print("\n── 时间序列分析（Chicago CTA）─────────────────────")

    cta = pd.read_csv(
        str(CTA_PATH),
        parse_dates=["service_date"],
        index_col="service_date",
    )
    cta["total_rides"] = pd.to_numeric(cta["total_rides"], errors="coerce")
    print(f"  CTA 数据: {cta.shape[0]} 天")

    # 周均客流
    weekly = cta["total_rides"].resample("W").mean()
    print(f"\n[周均客流] 共 {len(weekly)} 周")
    print(weekly.head(5).to_string())

    # 月度客流总和
    monthly = cta["total_rides"].resample("ME").sum()
    print(f"\n[月度客流] 共 {len(monthly)} 月")
    print(monthly.head(5).to_string())

    # 7 日滚动平均（center=False 避免数据泄漏）
    cta["rolling_7d"] = cta["total_rides"].rolling(window=7, center=False).mean()
    print(f"\n[7 日滚动平均]（前 10 条含 NaN）")
    print(cta[["total_rides", "rolling_7d"]].head(10).to_string())

    # 可视化
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

    # 日客流 + 7 日均线
    axes[0].plot(cta.index, cta["total_rides"], alpha=0.3, label="日客流")
    axes[0].plot(cta.index, cta["rolling_7d"], linewidth=1.5, color="red", label="7 日均线")
    axes[0].set_title("芝加哥 CTA 日客流与 7 日滚动平均")
    axes[0].set_ylabel("客流量")
    axes[0].legend()

    # 周均客流
    axes[1].plot(weekly.index, weekly.values, linewidth=1.2, color="green")
    axes[1].set_title("周均客流")
    axes[1].set_ylabel("客流量")

    # 月度客流
    axes[2].bar(monthly.index, monthly.values, width=20, color="steelblue", alpha=0.7)
    axes[2].set_title("月度客流总和")
    axes[2].set_ylabel("客流量")

    plt.tight_layout()
    save_path = OUTPUT_DIR / "cta_time_series.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"\n  图表已保存: {save_path}")


# ══════════════════════════════════════════════════════════
# 5. 交通流量可视化
# ══════════════════════════════════════════════════════════

def visualize_traffic_flow(df_long: pd.DataFrame) -> None:
    """可视化交通流量数据。"""

    # ── 图 1: 某路段 24 小时流量折线图 ────────────────────
    top_segment = df_long["segmentid"].value_counts().index[0]
    segment_data = df_long[df_long["segmentid"] == top_segment]
    hourly = segment_data.groupby("hour")["volume"].mean()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly.index, hourly.values, "o-", linewidth=2, markersize=6)
    ax.set_title(f"路段 {top_segment} 24 小时平均流量")
    ax.set_xlabel("小时")
    ax.set_ylabel("平均流量")
    ax.set_xticks(range(0, 24))

    # 标注早晚高峰
    am_peak_hour = hourly.loc[6:9].idxmax()
    pm_peak_hour = hourly.loc[16:19].idxmax()
    ax.annotate(
        f"早高峰 {am_peak_hour}:00",
        xy=(am_peak_hour, hourly[am_peak_hour]),
        xytext=(am_peak_hour - 3, hourly[am_peak_hour] * 1.1),
        arrowprops=dict(arrowstyle="->", color="red"),
        fontsize=10, color="red",
    )
    ax.annotate(
        f"晚高峰 {pm_peak_hour}:00",
        xy=(pm_peak_hour, hourly[pm_peak_hour]),
        xytext=(pm_peak_hour + 1, hourly[pm_peak_hour] * 1.1),
        arrowprops=dict(arrowstyle="->", color="orange"),
        fontsize=10, color="orange",
    )
    ax.axvspan(7, 9, alpha=0.1, color="red", label="早高峰时段")
    ax.axvspan(17, 19, alpha=0.1, color="orange", label="晚高峰时段")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    save_path = OUTPUT_DIR / "segment_24h_profile.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")

    # ── 图 2: Top 20 路段 24 小时流量热力图 ──────────────
    top20_segments = df_long["segmentid"].value_counts().head(20).index
    heat_data = (
        df_long[df_long["segmentid"].isin(top20_segments)]
        .groupby(["segmentid", "hour"])["volume"]
        .mean()
        .unstack()
    )

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(
        heat_data,
        cmap="YlOrRd",
        ax=ax,
        linewidths=0.5,
        cbar_kws={"label": "平均流量"},
    )
    ax.set_title("Top 20 路段 24 小时平均流量热力图")
    ax.set_xlabel("小时")
    ax.set_ylabel("路段 ID")
    plt.tight_layout()
    save_path = OUTPUT_DIR / "traffic_flow_heatmap.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")

    # ── 图 3: 工作日 vs 周端箱线图 ──────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    df_long["weekday_label"] = df_long["is_weekend"].map({False: "工作日", True: "周末"})
    # 按天聚合后再画箱线图
    daily_by_type = (
        df_long.groupby(["segmentid", "date", "weekday_label"])["volume"]
        .sum()
        .reset_index()
    )
    sns.boxplot(data=daily_by_type, x="weekday_label", y="volume", ax=ax)
    ax.set_title("工作日 vs 周末 日总流量分布")
    ax.set_xlabel("")
    ax.set_ylabel("日总流量")
    plt.tight_layout()
    save_path = OUTPUT_DIR / "weekday_vs_weekend_boxplot.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")


# ══════════════════════════════════════════════════════════
# 6. 事故数据可视化
# ══════════════════════════════════════════════════════════

def visualize_crash_data() -> None:
    """可视化事故面板数据。"""
    crash = pd.read_csv(str(CRASH_PATH))
    print(f"  事故面板数据: {crash.shape[0]} 行")

    # ── 图 4: 各行政区事故数量箱线图 ────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=crash, x="borough", y="crashes", ax=ax, palette="Set2")
    ax.set_title("纽约各行政区月度事故数量分布")
    ax.set_xlabel("行政区")
    ax.set_ylabel("月度事故数量")
    plt.tight_layout()
    save_path = OUTPUT_DIR / "nyc_crash_borough_boxplot.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")

    # ── 图 5: 各行政区受伤人数小提琴图 ──────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.violinplot(data=crash, x="borough", y="persons_injured", ax=ax,
                   palette="Set3", inner="box")
    ax.set_title("纽约各行政区月度受伤人数分布")
    ax.set_xlabel("行政区")
    ax.set_ylabel("月度受伤人数")
    plt.tight_layout()
    save_path = OUTPUT_DIR / "nyc_crash_borough_violin.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")

    # ── 图 6: 事故数量月度趋势折线图 ────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for borough in crash["borough"].unique():
        borough_data = crash[crash["borough"] == borough]
        ax.plot(borough_data["month"], borough_data["crashes"],
                marker="o", label=borough, linewidth=1.5)
    ax.set_title("纽约各行政区事故数量月度趋势")
    ax.set_xlabel("月份")
    ax.set_ylabel("事故数量")
    ax.set_xticks(range(1, 13))
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    save_path = OUTPUT_DIR / "nyc_crash_monthly_trend.png"
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  图表已保存: {save_path}")


# ══════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════

def main() -> None:
    """主函数：读取 → 清洗 → 变换 → 聚合 → 可视化。"""
    print("=" * 60)
    print("第二章 交通数据探索性分析 — 参考实现")
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

    # 5. 交通流量可视化
    print("\n[5] 交通流量可视化...")
    visualize_traffic_flow(df_long)

    # 6. 事故数据可视化
    print("\n[6] 事故数据可视化...")
    visualize_crash_data()

    print("\n完成！所有图表保存在:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
