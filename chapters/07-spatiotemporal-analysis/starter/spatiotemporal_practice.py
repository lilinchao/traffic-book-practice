"""
第 7 章 起始代码：交通时空数据分析

本脚本提供数据加载和基础可视化的框架代码。
学生需要根据实践讲义补全缺失部分（标记为 TODO）。

运行前请先生成数据：
    python scripts/generate_synthetic_network.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]  # Book/
DATA_DIR = ROOT / "data" / "processed"
SPEED_PATH = DATA_DIR / "synthetic_network_speed.csv"
ADJ_PATH = DATA_DIR / "synthetic_network_adjacency.npz"
NODES_PATH = DATA_DIR / "synthetic_network_nodes.csv"
RESULT_DIR = ROOT / "data" / "results" / "chapter-07"


# ---------------------------------------------------------------------------
# 1. 数据加载
# ---------------------------------------------------------------------------
def load_speed_data(path: Path) -> pd.DataFrame:
    """加载速度长表数据。"""
    # TODO: 读取 CSV 文件并返回 DataFrame
    # 提示：pd.read_csv(path)
    raise NotImplementedError


def load_adjacency(path: Path) -> np.ndarray:
    """加载邻接矩阵。"""
    # TODO: 读取 .npz 稀疏矩阵并转为稠密数组
    # 提示：sparse.load_npz(path).toarray()
    raise NotImplementedError


def load_nodes(path: Path) -> pd.DataFrame:
    """加载节点坐标信息。"""
    # TODO: 读取节点 CSV 文件
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 2. 长表 → 节点-时间矩阵
# ---------------------------------------------------------------------------
def long_to_matrix(speed_long: pd.DataFrame) -> pd.DataFrame:
    """将速度长表转换为节点-时间矩阵（行为节点，列为时间步）。

    参数：
        speed_long: 包含 node_id, timestamp, speed 列的长表

    返回：
        节点-时间矩阵 DataFrame
    """
    # TODO: 使用 pivot 转换
    # 提示：speed_long.pivot(index='node_id', columns='timestamp', values='speed')
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 3. 基础统计
# ---------------------------------------------------------------------------
def compute_basic_stats(speed_matrix: pd.DataFrame) -> dict:
    """计算速度矩阵的基本统计量。"""
    # TODO: 计算以下统计量
    # - 矩阵形状
    # - 缺失值比例
    # - 每个节点的速度均值和标准差
    # - 整体速度均值、最小值、最大值
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 4. 基础可视化
# ---------------------------------------------------------------------------
def plot_network_topology(
    nodes: pd.DataFrame, adj: np.ndarray, ax: plt.Axes | None = None
) -> plt.Axes:
    """绘制路网拓扑图。

    参数：
        nodes: 节点信息 DataFrame，包含 node_id, x, y 列
        adj: 邻接矩阵
        ax: matplotlib 轴对象

    返回：
        matplotlib 轴对象
    """
    # TODO: 绘制路网拓扑
    # 1. 用散点图画节点
    # 2. 根据邻接矩阵连线
    # 3. 标注节点 ID
    raise NotImplementedError


def plot_speed_timeseries(
    speed_matrix: pd.DataFrame,
    node_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """绘制单个节点的时间序列。

    参数：
        speed_matrix: 节点-时间矩阵
        node_id: 要绘制的节点 ID
        start_time: 起始时间（可选）
        end_time: 结束时间（可选）
        ax: matplotlib 轴对象

    返回：
        matplotlib 轴对象
    """
    # TODO: 绘制时间序列
    # 提示：speed_matrix.loc[node_id][start_time:end_time].plot()
    raise NotImplementedError


def plot_adjacency_heatmap(adj: np.ndarray, ax: plt.Axes | None = None) -> plt.Axes:
    """绘制邻接矩阵热力图。"""
    # TODO: 使用 imshow 或 seaborn.heatmap 绘制邻接矩阵
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------
def main() -> None:
    """主函数：加载数据，完成基础统计和可视化。"""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("第 7 章 交通时空数据分析 - 起始代码")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1] 加载数据...")
    # TODO: 调用 load_speed_data, load_adjacency, load_nodes

    # 2. 长表 → 矩阵
    print("\n[2] 转换为节点-时间矩阵...")
    # TODO: 调用 long_to_matrix

    # 3. 基础统计
    print("\n[3] 基础统计...")
    # TODO: 调用 compute_basic_stats 并打印结果

    # 4. 可视化
    print("\n[4] 绘制可视化图表...")
    # TODO: 调用绘图函数并保存图表到 RESULT_DIR

    print("\n完成！图表已保存到", RESULT_DIR)


if __name__ == "__main__":
    main()
