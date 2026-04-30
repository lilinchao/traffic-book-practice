"""
生成合成交通流量数据
==================

生成 3 个检测器、4 周（28 天）的 5 分钟间隔交通流量数据。
数据特征：
  - 双峰日模式（早高峰 7-9 点，晚高峰 17-19 点）
  - 工作日与周末差异
  - 检测器间流量差异
  - 高斯噪声
  - 少量缺失值

输出：data/processed/synthetic_traffic_flow_5min.csv
"""

import numpy as np
import pandas as pd
import os

# ============================================================
# 配置
# ============================================================
SEED = 42
N_DAYS = 28                         # 4 周
INTERVAL = "5min"                    # 5 分钟间隔
POINTS_PER_DAY = 288                 # 24h * 12 (每 5 分钟一个点)
DETECTORS = {
    "detector_01": {"base_flow": 60, "peak_am": 80, "peak_pm": 70, "noise_std": 8},
    "detector_02": {"base_flow": 45, "peak_am": 55, "peak_pm": 50, "noise_std": 6},
    "detector_03": {"base_flow": 30, "peak_am": 40, "peak_pm": 35, "noise_std": 5},
}
MISSING_FRAC = 0.005                 # 约 0.5% 缺失率
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "synthetic_traffic_flow_5min.csv",
)


def daily_pattern(t_minutes, base_flow, peak_am, peak_pm):
    """生成一天的流量模式。

    使用两个高斯峰模拟早晚高峰：
      - 早高峰：均值 = 8*60 = 480 分钟（8:00），标准差 = 60 分钟
      - 晚高峰：均值 = 17.5*60 = 1050 分钟（17:30），标准差 = 60 分钟

    Args:
        t_minutes: 一天内的分钟数数组 (0, 5, 10, ..., 1435)
        base_flow: 基础流量
        peak_am: 早高峰增量
        peak_pm: 晚高峰增量

    Returns:
        流量数组
    """
    # 早高峰：center=480min (8:00), sigma=60min
    am_peak = peak_am * np.exp(-0.5 * ((t_minutes - 480) / 60) ** 2)
    # 晚高峰：center=1050min (17:30), sigma=60min
    pm_peak = peak_pm * np.exp(-0.5 * ((t_minutes - 1050) / 60) ** 2)
    # 夜间低流量：0-5 点和 22-24 点流量降低
    night_low = -base_flow * 0.7 * (
        np.exp(-0.5 * ((t_minutes - 150) / 120) ** 2)  # 凌晨低谷 ~2:30
    )

    flow = base_flow + am_peak + pm_peak + night_low
    return np.maximum(flow, 0)  # 流量不能为负


def generate_detector_data(detector_id, params, start_date, n_days, rng):
    """生成单个检测器的流量数据。

    Args:
        detector_id: 检测器编号
        params: 检测器参数字典
        start_date: 起始日期
        n_days: 天数
        rng: 随机数生成器

    Returns:
        DataFrame with columns: datetime, detector_id, flow
    """
    # 生成完整时间索引
    datetimes = pd.date_range(
        start=start_date,
        periods=n_days * POINTS_PER_DAY,
        freq=INTERVAL,
    )

    t_minutes = np.arange(POINTS_PER_DAY) * 5  # 每天的分钟序列

    records = []
    for i, dt in enumerate(datetimes):
        day_of_week = dt.weekday()  # 0=周一, 6=周日
        is_weekend = day_of_week >= 5

        # 基础日模式
        day_t = t_minutes[i % POINTS_PER_DAY]
        flow = daily_pattern(day_t, params["base_flow"], params["peak_am"], params["peak_pm"])

        # 周末：流量降低，高峰不明显
        if is_weekend:
            # 整体降低 30%
            flow *= 0.7
            # 高峰降低更多（周末没有通勤高峰）
            # 重新计算带周末特征的模式
            flow = daily_pattern(day_t, params["base_flow"] * 0.7,
                                 params["peak_am"] * 0.3,
                                 params["peak_pm"] * 0.4)
            flow = np.maximum(flow, 0)

        # 加高斯噪声
        noise = rng.normal(0, params["noise_std"])
        flow = max(0, int(np.round(flow + noise)))

        records.append({
            "datetime": dt,
            "detector_id": detector_id,
            "flow": flow,
        })

    return pd.DataFrame(records)


def inject_missing(df, missing_frac, rng):
    """随机注入缺失值。

    随机删除少量记录以模拟传感器故障。
    """
    n_missing = int(len(df) * missing_frac)
    if n_missing == 0:
        return df

    missing_idx = rng.choice(len(df), size=n_missing, replace=False)
    return df.drop(index=df.index[missing_idx]).reset_index(drop=True)


def main():
    print("生成合成交通流量数据...")
    rng = np.random.default_rng(SEED)

    # 起始日期：2024-01-01（周一）
    start_date = pd.Timestamp("2024-01-01")

    all_frames = []
    for det_id, params in DETECTORS.items():
        print(f"  生成 {det_id}...")
        det_df = generate_detector_data(det_id, params, start_date, N_DAYS, rng)
        all_frames.append(det_df)

    df = pd.concat(all_frames, ignore_index=True)

    # 注入缺失值
    print(f"  注入缺失值（约 {MISSING_FRAC*100:.1f}%）...")
    df = inject_missing(df, MISSING_FRAC, rng)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # 保存
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"  已保存: {OUTPUT_PATH}")
    print(f"  总记录数: {len(df)}")
    print(f"  检测器: {df['detector_id'].unique().tolist()}")
    print(f"  时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")

    # 验证
    for det in df["detector_id"].unique():
        sub = df[df["detector_id"] == det]
        full_range = pd.date_range(sub["datetime"].min(), sub["datetime"].max(), freq="5min")
        n_missing = len(full_range) - len(sub)
        print(f"  {det}: 记录数={len(sub)}, 缺失={n_missing}, "
              f"均值流量={sub['flow'].mean():.1f}, 标准差={sub['flow'].std():.1f}")


if __name__ == "__main__":
    main()
