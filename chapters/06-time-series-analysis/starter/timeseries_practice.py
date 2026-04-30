"""
第 6 章 交通时序数据分析 - 起始代码
=====================================

本文件提供数据加载、基础可视化和 ACF/PACF 的框架代码。
学生需要补充标有 TODO 的部分，完成完整实践。

运行前请确保已生成合成数据：
    python scripts/generate_synthetic_flow.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 0. 配置
# ============================================================
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
DATA_PATH = "../../data/processed/synthetic_traffic_flow_5min.csv"


# ============================================================
# 1. 数据加载
# ============================================================
def load_data(path=DATA_PATH):
    """加载合成交通流量数据。

    TODO: 读取 CSV，将 datetime 列解析为 pd.Timestamp 并设为索引。
    返回按索引排序的 DataFrame。
    """
    # --- 你的代码 ---
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


# ============================================================
# 2. 基础可视化
# ============================================================
def plot_weekly_flow(df, detector="detector_01"):
    """绘制指定检测器前 7 天的交通流量时序图。

    TODO: 筛选检测器数据，取前 7 天，绘制流量曲线。
    在图中标注早高峰和晚高峰的大致时段。
    """
    sub = df[df["detector_id"] == detector]
    start = sub.index.min()
    end = start + pd.Timedelta(days=7)
    week_data = sub[sub.index < end]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(week_data.index, week_data["flow"], linewidth=0.8)
    ax.set_xlabel("时间")
    ax.set_ylabel("流量（辆/5分钟）")
    ax.set_title(f"{detector} 前 7 天交通流量")

    # TODO: 标注高峰时段（添加阴影区域或垂直线）
    # ax.axvspan(...)

    plt.tight_layout()
    plt.savefig("weekly_flow.png", dpi=150)
    plt.show()
    print("[提示] 请在图中标注早高峰 (7:00-9:00) 和晚高峰 (17:00-19:00)")


def plot_resample_comparison(df, detector="detector_01"):
    """对比不同重采样粒度的流量曲线。

    TODO: 将 5 分钟数据重采样为 1 小时和 1 天，
    绘制三条曲线进行比较。
    """
    sub = df[df["detector_id"] == detector]["flow"]

    # --- 你的代码 ---
    hourly = sub.resample("1h").sum()
    daily = sub.resample("1D").sum()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

    axes[0].plot(sub.index, sub.values, linewidth=0.3)
    axes[0].set_title("5 分钟粒度")
    axes[0].set_ylabel("流量")

    axes[1].plot(hourly.index, hourly.values, linewidth=0.8)
    axes[1].set_title("1 小时粒度")
    axes[1].set_ylabel("流量")

    axes[2].plot(daily.index, daily.values, marker="o", markersize=4)
    axes[2].set_title("1 天粒度")
    axes[2].set_ylabel("流量")
    axes[2].set_xlabel("日期")

    plt.suptitle(f"{detector} 不同粒度流量对比", fontsize=14)
    plt.tight_layout()
    plt.savefig("resample_comparison.png", dpi=150)
    plt.show()


# ============================================================
# 3. ACF / PACF
# ============================================================
def plot_acf_pacf(df, detector="detector_01", lags=288):
    """绘制 ACF 和 PACF 图。

    TODO: 使用 statsmodels 的 plot_acf / plot_pacf 绘制。
    在 ACF 图中标注日周期 (滞后 288) 的位置。
    """
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

    series = df[df["detector_id"] == detector]["flow"]

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    # --- 你的代码 ---
    plot_acf(series, lags=lags, ax=axes[0])
    plot_pacf(series, lags=lags, ax=axes[1])

    axes[0].axvline(x=288, color="red", linestyle="--", label="1 天周期 (lag=288)")
    axes[0].legend()
    axes[0].set_title("自相关函数 (ACF)")
    axes[1].set_title("偏自相关函数 (PACF)")

    plt.suptitle(f"{detector} ACF / PACF", fontsize=14)
    plt.tight_layout()
    plt.savefig("acf_pacf.png", dpi=150)
    plt.show()
    print("[提示] ACF 在 lag=288, 576 等处的峰值反映了日周期性")


# ============================================================
# 4. 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("第 6 章 交通时序数据分析 - 起始代码")
    print("=" * 60)

    # 加载数据
    df = load_data()
    print(f"数据形状: {df.shape}")
    print(f"检测器: {df['detector_id'].unique()}")
    print(f"时间范围: {df.index.min()} ~ {df.index.max()}")
    print()

    # 基础可视化
    print("--- 绘制 7 天流量图 ---")
    plot_weekly_flow(df)

    print("--- 重采样对比 ---")
    plot_resample_comparison(df)

    print("--- ACF / PACF ---")
    plot_acf_pacf(df)

    print("\n[下一步] 请完成 exercises.md 中的基础任务 1-4")
    print("  - 补充高峰时段标注")
    print("  - 实现 ADF 检验")
    print("  - 对差分序列做 ADF 检验")
