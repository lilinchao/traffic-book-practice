"""
生成合成城市路网速度数据

生成一个小型路网（15 个节点、约 20 条边）的 5 分钟间隔速度数据，
持续 4 周，包含早晚高峰模式、周末效应和随机噪声。

输出文件：
- data/processed/synthetic_network_speed.csv     速度长表
- data/processed/synthetic_network_adjacency.npz  邻接矩阵（稀疏格式）
- data/processed/synthetic_network_nodes.csv     节点信息

用法：
    python scripts/generate_synthetic_network.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# 路网拓扑定义
# ---------------------------------------------------------------------------
# 15 个节点的坐标 (x, y)，模拟一个小型城市路网
# 节点 0-4 为中心区域，5-9 为中间环，10-14 为外围
NODE_COORDS = np.array([
    # 中心区域 (0-4)
    [5.0, 5.0],   # 0: 中心交叉口
    [4.0, 5.0],   # 1
    [6.0, 5.0],   # 2
    [5.0, 4.0],   # 3
    [5.0, 6.0],   # 4
    # 中间环 (5-9)
    [3.0, 5.0],   # 5
    [7.0, 5.0],   # 6
    [5.0, 3.0],   # 7
    [5.0, 7.0],   # 8
    [4.0, 4.0],   # 9
    # 外围 (10-14)
    [2.0, 5.0],   # 10
    [8.0, 5.0],   # 11
    [5.0, 2.0],   # 12
    [5.0, 8.0],   # 13
    [3.0, 3.0],   # 14
])

# 区域标签：center / middle / outer
REGION_LABELS = (
    ["center"] * 5 + ["middle"] * 5 + ["outer"] * 5
)

# 边列表（无向）
EDGES = [
    # 中心内部连接
    (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 9), (2, 4),
    # 中心到中间环
    (1, 5), (2, 6), (3, 7), (4, 8),
    (3, 9), (1, 9),
    # 中间环内部
    (5, 9), (9, 7),
    (5, 8),
    # 中间环到外围
    (5, 10), (6, 11), (7, 12), (8, 13),
    (9, 14),
    # 外围连接
    (10, 14), (12, 14),
]

NUM_NODES = len(NODE_COORDS)

# ---------------------------------------------------------------------------
# 速度生成参数
# ---------------------------------------------------------------------------
SPEED_BASE = {
    "center": 45.0,   # 中心区基础速度较低（拥堵）
    "middle": 55.0,   # 中间环
    "outer": 65.0,    # 外围速度较高
}

# 高峰降幅（占基础速度的比例）
PEAK_DROP = {
    "center": 0.40,   # 中心区高峰降幅大
    "middle": 0.25,
    "outer": 0.10,
}

# 时间参数
N_WEEKS = 4
INTERVAL_MIN = 5
STEPS_PER_DAY = 24 * 60 // INTERVAL_MIN  # 288
TOTAL_STEPS = N_WEEKS * 7 * STEPS_PER_DAY

# 随机种子
RNG_SEED = 42


# ---------------------------------------------------------------------------
# 速度生成函数
# ---------------------------------------------------------------------------
def generate_daily_pattern(
    hour: int, minute: int, weekday: int, region: str
) -> float:
    """生成给定时刻的基础速度（不含随机噪声）。

    包含：
    - 早高峰 (7:00-9:00) 和晚高峰 (17:00-19:00) 降幅
    - 周末速度较高、高峰不明显
    - 夜间速度较高
    """
    base = SPEED_BASE[region]
    drop = PEAK_DROP[region]
    is_weekend = weekday >= 5

    # 昼夜基线调整
    if hour < 5 or hour >= 22:
        # 深夜速度高
        night_factor = 1.15
    elif hour < 7 or hour >= 21:
        # 过渡时段
        night_factor = 1.05
    else:
        night_factor = 1.0

    # 高峰降幅
    peak_factor = 1.0
    if not is_weekend:
        # 早高峰
        if 7 <= hour < 9:
            # 在 8:00 达到最高降幅
            progress = (hour - 7) + minute / 60.0
            peak_factor = 1.0 - drop * np.sin(np.pi * progress / 2.0)
        # 晚高峰
        elif 17 <= hour < 19:
            progress = (hour - 17) + minute / 60.0
            peak_factor = 1.0 - drop * np.sin(np.pi * progress / 2.0)
        # 高峰前后过渡
        elif 9 <= hour < 10:
            peak_factor = 1.0 - drop * 0.3 * (10 - hour - minute / 60.0)
        elif 16 <= hour < 17:
            peak_factor = 1.0 - drop * 0.3 * (hour - 16 + minute / 60.0)
    else:
        # 周末：中午时段小高峰
        if 11 <= hour < 14:
            peak_factor = 1.0 - drop * 0.3

    speed = base * night_factor * peak_factor
    return speed


def generate_speed_data() -> pd.DataFrame:
    """生成全部时空速度数据。"""
    rng = np.random.default_rng(RNG_SEED)

    # 构建时间索引
    start = pd.Timestamp("2024-01-01 00:00")
    timestamps = pd.date_range(start=start, periods=TOTAL_STEPS, freq=f"{INTERVAL_MIN}min")

    rows = []
    for node_idx in range(NUM_NODES):
        region = REGION_LABELS[node_idx]
        node_id = f"N{node_idx:02d}"

        # 每个节点的随机基础偏移
        base_offset = rng.normal(0, 3.0)
        # 生成自相关噪声（AR(1) 过程）
        noise = np.zeros(TOTAL_STEPS)
        noise[0] = rng.normal(0, 2.0)
        for t in range(1, TOTAL_STEPS):
            noise[t] = 0.7 * noise[t - 1] + rng.normal(0, 1.5)

        for t_idx, ts in enumerate(timestamps):
            hour = ts.hour
            minute = ts.minute
            weekday = ts.weekday()

            base_speed = generate_daily_pattern(hour, minute, weekday, region)
            speed = base_speed + base_offset + noise[t_idx]
            # 加入少量缺失值（约 1%）
            if rng.random() < 0.01:
                speed = np.nan
            else:
                speed = np.clip(speed, 15.0, 90.0)

            rows.append({
                "node_id": node_id,
                "timestamp": ts,
                "speed": round(speed, 1),
            })

    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# 邻接矩阵构建
# ---------------------------------------------------------------------------
def build_adjacency_matrix() -> np.ndarray:
    """根据边列表构建邻接矩阵。"""
    adj = np.zeros((NUM_NODES, NUM_NODES), dtype=np.float64)
    for i, j in EDGES:
        adj[i, j] = 1.0
        adj[j, i] = 1.0
    return adj


# ---------------------------------------------------------------------------
# 节点信息
# ---------------------------------------------------------------------------
def build_nodes_dataframe() -> pd.DataFrame:
    """构建节点信息 DataFrame。"""
    df = pd.DataFrame({
        "node_id": [f"N{i:02d}" for i in range(NUM_NODES)],
        "x": NODE_COORDS[:, 0],
        "y": NODE_COORDS[:, 1],
        "region": REGION_LABELS,
    })
    return df


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("生成合成路网速度数据")
    print("=" * 60)

    # 1. 速度数据
    print("\n[1] 生成速度数据...")
    speed_df = generate_speed_data()
    speed_path = OUT_DIR / "synthetic_network_speed.csv"
    speed_df.to_csv(speed_path, index=False)
    print(f"  保存: {speed_path}")
    print(f"  行数: {len(speed_df):,}, 节点数: {speed_df['node_id'].nunique()}")
    print(f"  时间范围: {speed_df['timestamp'].min()} ~ {speed_df['timestamp'].max()}")
    print(f"  缺失值: {speed_df['speed'].isna().sum()} ({speed_df['speed'].isna().mean():.2%})")

    # 2. 邻接矩阵
    print("\n[2] 构建邻接矩阵...")
    adj = build_adjacency_matrix()
    adj_path = OUT_DIR / "synthetic_network_adjacency.npz"
    sparse.save_npz(adj_path, sparse.csr_matrix(adj))
    print(f"  保存: {adj_path}")
    print(f"  节点数: {adj.shape[0]}, 边数: {int(adj.sum() / 2)}")

    # 3. 节点信息
    print("\n[3] 构建节点信息...")
    nodes_df = build_nodes_dataframe()
    nodes_path = OUT_DIR / "synthetic_network_nodes.csv"
    nodes_df.to_csv(nodes_path, index=False)
    print(f"  保存: {nodes_path}")

    print("\n" + "=" * 60)
    print("数据生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
