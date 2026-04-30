"""
第 7 章参考实现：交通时空数据分析

完整实现包括：
- 数据组织：长表 → 节点-时间矩阵 → 张量 → 图结构
- 邻接矩阵构建：拓扑、距离高斯核
- 时滞互相关分析
- DTW + K-means 路段聚类
- VAR 基线预测
- XGBoost 时空特征工程预测
- 模型比较与分区域分步长误差分析

运行前请先生成数据：
    python scripts/generate_synthetic_network.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial.distance import cdist

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]  # Book/
DATA_DIR = ROOT / "data" / "processed"
SPEED_PATH = DATA_DIR / "synthetic_network_speed.csv"
ADJ_PATH = DATA_DIR / "synthetic_network_adjacency.npz"
NODES_PATH = DATA_DIR / "synthetic_network_nodes.csv"
RESULT_DIR = ROOT / "data" / "results" / "chapter-07"

plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ===========================================================================
# A. 数据加载
# ===========================================================================
def load_speed_data(path: Path = SPEED_PATH) -> pd.DataFrame:
    """加载速度长表数据。"""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"  速度数据: {df.shape[0]} 行, {df.shape[1]} 列")
    print(f"  节点数: {df['node_id'].nunique()}, 时间范围: "
          f"{df['timestamp'].min()} ~ {df['timestamp'].max()}")
    return df


def load_adjacency(path: Path = ADJ_PATH) -> np.ndarray:
    """加载邻接矩阵。"""
    adj = sparse.load_npz(path).toarray().astype(np.float64)
    print(f"  邻接矩阵: {adj.shape}, 边数: {int(adj.sum() / 2)}")
    return adj


def load_nodes(path: Path = NODES_PATH) -> pd.DataFrame:
    """加载节点坐标信息。"""
    nodes = pd.read_csv(path)
    print(f"  节点信息: {nodes.shape[0]} 个节点, 列: {list(nodes.columns)}")
    return nodes


# ===========================================================================
# B. 数据组织
# ===========================================================================
def long_to_matrix(speed_long: pd.DataFrame) -> pd.DataFrame:
    """将速度长表转换为节点-时间矩阵（行为节点，列为时间步）。"""
    matrix = speed_long.pivot(index="node_id", columns="timestamp", values="speed")
    matrix.sort_index(axis=0, inplace=True)
    matrix.sort_index(axis=1, inplace=True)
    return matrix


def matrix_to_tensor(
    speed_matrix: pd.DataFrame, feature_cols: Optional[list[str]] = None
) -> np.ndarray:
    """将节点-时间矩阵扩展为张量 (nodes, timesteps, features)。

    当只有速度一个特征时，feature_dim=1。
    """
    values = speed_matrix.values  # (nodes, timesteps)
    tensor = values[:, :, np.newaxis]  # (nodes, timesteps, 1)
    return tensor


def build_edge_list(adj: np.ndarray) -> list[tuple[int, int]]:
    """从邻接矩阵提取边列表。"""
    rows, cols = np.where(np.triu(adj, k=1) > 0)
    return list(zip(rows.tolist(), cols.tolist()))


# ===========================================================================
# C. 邻接矩阵构建
# ===========================================================================
def build_distance_adjacency(
    nodes: pd.DataFrame, sigma: float = 2.0, threshold: float = 0.1
) -> np.ndarray:
    """构建基于距离的高斯核邻接矩阵。

    A[i][j] = exp(-d(i,j)^2 / sigma^2)，若 A[i][j] < threshold 则置 0。
    """
    coords = nodes[["x", "y"]].values
    dist_matrix = cdist(coords, coords, metric="euclidean")
    adj = np.exp(-(dist_matrix ** 2) / (sigma ** 2))
    np.fill_diagonal(adj, 0)
    adj[adj < threshold] = 0
    return adj


def build_correlation_adjacency(speed_matrix: pd.DataFrame, threshold: float = 0.3) -> np.ndarray:
    """构建基于速度相关性的邻接矩阵。"""
    corr = speed_matrix.T.corr().abs().values
    np.fill_diagonal(corr, 0)
    adj = (corr >= threshold).astype(np.float64)
    return adj


# ===========================================================================
# D. 时空相关性分析
# ===========================================================================
def compute_acf(speed_series: np.ndarray, nlags: int = 288) -> np.ndarray:
    """计算自相关函数。"""
    n = len(speed_series)
    mean = speed_series.mean()
    var = ((speed_series - mean) ** 2).sum() / n
    acf_vals = np.zeros(nlags + 1)
    for lag in range(nlags + 1):
        if lag >= n:
            break
        acf_vals[lag] = np.sum(
            (speed_series[: n - lag] - mean) * (speed_series[lag:] - mean)
        ) / (n * var)
    return acf_vals


def time_lagged_cross_correlation(
    x: np.ndarray, y: np.ndarray, max_lag: int = 36
) -> tuple[np.ndarray, np.ndarray]:
    """计算两个序列的时滞互相关。

    返回：
        lags: 滞后值数组 (-max_lag, ..., max_lag)
        ccs: 对应的互相关系数
    """
    lags = np.arange(-max_lag, max_lag + 1)
    ccs = np.zeros(len(lags))
    n = len(x)
    for idx, lag in enumerate(lags):
        if lag >= 0:
            cc = np.corrcoef(x[: n - lag], y[lag:])[0, 1]
        else:
            cc = np.corrcoef(x[-lag:], y[: n + lag])[0, 1]
        ccs[idx] = cc
    return lags, ccs


def compute_morans_i(values: np.ndarray, adj: np.ndarray) -> float:
    """计算 Moran's I 空间自相关指数。"""
    n = len(values)
    w = adj.copy()
    w_sum = w.sum()
    mean_val = values.mean()
    num = 0.0
    for i in range(n):
        for j in range(n):
            num += w[i, j] * (values[i] - mean_val) * (values[j] - mean_val)
    den = np.sum((values - mean_val) ** 2)
    if den == 0 or w_sum == 0:
        return 0.0
    return (n / w_sum) * (num / den)


# ===========================================================================
# E. DTW + K-means 聚类
# ===========================================================================
def compute_dtw_distance_matrix(
    speed_matrix: pd.DataFrame, sample_rate: int = 12
) -> np.ndarray:
    """计算 DTW 距离矩阵。

    参数：
        speed_matrix: 节点-时间矩阵
        sample_rate: 降采样率（12 表示每小时取一个点）

    返回：
        N x N 的 DTW 距离矩阵
    """
    try:
        from tslearn.metrics import dtw as tslearn_dtw
        use_tslearn = True
    except ImportError:
        use_tslearn = False

    series_list = []
    for node_id in speed_matrix.index:
        s = speed_matrix.loc[node_id].values[::sample_rate]
        series_list.append(s)

    n = len(series_list)
    dtw_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if use_tslearn:
                d = tslearn_dtw(series_list[i], series_list[j])
            else:
                # 简易 DTW 实现
                d = _simple_dtw(series_list[i], series_list[j])
            dtw_matrix[i, j] = d
            dtw_matrix[j, i] = d
    return dtw_matrix


def _simple_dtw(s1: np.ndarray, s2: np.ndarray) -> float:
    """简易 DTW 实现（无需额外依赖）。"""
    n, m = len(s1), len(s2)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (s1[i - 1] - s2[j - 1]) ** 2
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j], dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1]
            )
    return np.sqrt(dtw_matrix[n, m])


def cluster_nodes_dtw(
    speed_matrix: pd.DataFrame, n_clusters: int = 3, sample_rate: int = 12
) -> np.ndarray:
    """使用 DTW 距离 + K-means 对路段进行聚类。"""
    from sklearn.cluster import KMeans

    dtw_dist = compute_dtw_distance_matrix(speed_matrix, sample_rate=sample_rate)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(dtw_dist)
    return labels


# ===========================================================================
# F. 预测模型
# ===========================================================================
# F1. 历史平均基线
def historical_average_predict(
    train_matrix: pd.DataFrame, test_timestamps: pd.DatetimeIndex
) -> np.ndarray:
    """历史平均预测：按小时和星期取均值。"""
    train_t = train_matrix.T.copy()
    train_t.index = pd.DatetimeIndex(train_t.index)
    train_t["hour"] = train_t.index.hour
    train_t["weekday"] = train_t.index.weekday

    node_cols = [c for c in train_t.columns if c not in ("hour", "weekday")]
    hist_mean = train_t.groupby(["hour", "weekday"])[node_cols].mean()

    preds = []
    for ts in test_timestamps:
        key = (ts.hour, ts.weekday())
        if key in hist_mean.index:
            preds.append(hist_mean.loc[key].values)
        else:
            preds.append(train_matrix.mean(axis=1).values)
    return np.array(preds)  # (len(test_timestamps), num_nodes)


# F2. VAR 模型
def var_predict(
    train_matrix: pd.DataFrame, steps: int = 12, maxlags: int = 12
) -> np.ndarray:
    """VAR 模型预测。

    参数：
        train_matrix: 节点-时间矩阵 (nodes, timesteps)
        steps: 预测步数
        maxlags: 最大滞后阶数

    返回：
        预测值数组 (steps, num_nodes)
    """
    from statsmodels.tsa.api import VAR

    data = train_matrix.T.copy()  # (timesteps, nodes)
    data.index = pd.DatetimeIndex(data.index)
    # 使用数值型列
    model = VAR(data.values)
    results = model.fit(maxlags=maxlags, ic="aic")
    lag_order = results.k_ar
    forecast = results.forecast(data.values[-lag_order:], steps=steps)
    return forecast  # (steps, num_nodes)


# F3. XGBoost 特征工程
def build_xgboost_features(
    speed_matrix: pd.DataFrame, adj: np.ndarray, lags: list[int] | None = None
) -> pd.DataFrame:
    """构建 XGBoost 时空特征。

    特征包括：
    - 历史速度滞后
    - 邻居速度滞后均值
    - 时间特征（小时、星期、是否周末）
    - 空间特征（度中心性、邻居均值）
    - 历史同时段统计
    """
    if lags is None:
        lags = [1, 2, 3, 6, 12]

    timestamps = speed_matrix.columns
    node_ids = speed_matrix.index.tolist()
    n_nodes = len(node_ids)
    deg_centrality = adj.sum(axis=1) / (n_nodes - 1)

    rows = []
    for t_idx in range(max(lags) + 288, len(timestamps)):
        ts = timestamps[t_idx]
        hour = ts.hour
        weekday = ts.weekday()

        for n_idx, node_id in enumerate(node_ids):
            target = speed_matrix.iloc[n_idx, t_idx]
            if np.isnan(target):
                continue

            feat: dict = {
                "node_id": node_id,
                "node_idx": n_idx,
                "timestamp": ts,
                "target": target,
            }

            # 历史速度滞后
            for lag in lags:
                feat[f"speed_lag_{lag}"] = speed_matrix.iloc[n_idx, t_idx - lag]

            # 邻居速度滞后均值
            neighbors = np.where(adj[n_idx] > 0)[0]
            for lag in lags[:3]:
                if len(neighbors) > 0:
                    feat[f"neighbor_mean_lag_{lag}"] = speed_matrix.iloc[
                        neighbors, t_idx - lag
                    ].mean()
                else:
                    feat[f"neighbor_mean_lag_{lag}"] = speed_matrix.iloc[
                        :, t_idx - lag
                    ].mean()

            # 时间特征
            feat["hour"] = hour
            feat["weekday"] = weekday
            feat["is_weekend"] = int(weekday >= 5)

            # 空间特征
            feat["degree_centrality"] = deg_centrality[n_idx]
            if len(neighbors) > 0:
                feat["neighbor_current_mean"] = speed_matrix.iloc[
                    neighbors, t_idx - 1
                ].mean()
            else:
                feat["neighbor_current_mean"] = speed_matrix.iloc[:, t_idx - 1].mean()

            # 历史同时段统计
            same_hour_mask = pd.DatetimeIndex(timestamps[:t_idx]).hour == hour
            if same_hour_mask.sum() > 0:
                hist_vals = speed_matrix.iloc[n_idx, :t_idx].values[same_hour_mask]
                feat["hist_hour_mean"] = np.nanmean(hist_vals)
                feat["hist_hour_std"] = np.nanstd(hist_vals) if len(hist_vals) > 1 else 0
            else:
                feat["hist_hour_mean"] = speed_matrix.iloc[n_idx].mean()
                feat["hist_hour_std"] = speed_matrix.iloc[n_idx].std()

            rows.append(feat)

    return pd.DataFrame(rows)


def xgboost_predict(
    speed_matrix: pd.DataFrame, adj: np.ndarray, test_steps: int = 288
) -> tuple[np.ndarray, np.ndarray]:
    """XGBoost 时空预测。

    参数：
        speed_matrix: 节点-时间矩阵
        adj: 邻接矩阵
        test_steps: 测试集时间步数（默认一天 = 288 个 5 分钟）

    返回：
        (y_true, y_pred) 两个数组，形状均为 (n_samples,)
    """
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    print("  构建特征...")
    feature_df = build_xgboost_features(speed_matrix, adj)
    feature_cols = [
        c for c in feature_df.columns if c not in ("node_id", "timestamp", "target")
    ]

    # 划分训练/测试集
    timestamps = feature_df["timestamp"].sort_values().unique()
    split_ts = timestamps[-test_steps]
    train_df = feature_df[feature_df["timestamp"] < split_ts]
    test_df = feature_df[feature_df["timestamp"] >= split_ts]

    X_train = train_df[feature_cols].values
    y_train = train_df["target"].values
    X_test = test_df[feature_cols].values
    y_test = test_df["target"].values

    print(f"  训练集: {X_train.shape[0]} 样本, 测试集: {X_test.shape[0]} 样本")

    model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train, verbose=False)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"  XGBoost MAE: {mae:.2f}, RMSE: {rmse:.2f}")

    return y_test, y_pred, test_df


# ===========================================================================
# G. 模型比较与误差分析
# ===========================================================================
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """计算 MAE, RMSE, MAPE。"""
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else 0
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def evaluate_by_region(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    node_indices: np.ndarray,
    nodes: pd.DataFrame,
    adj: np.ndarray,
) -> pd.DataFrame:
    """按空间区域（中心/边缘）计算误差。"""
    n_nodes = len(nodes)
    deg = adj.sum(axis=1)
    median_deg = np.median(deg)
    is_center = deg >= median_deg

    results = []
    for label, mask_arr in [("中心节点", is_center), ("边缘节点", ~is_center)]:
        idx = np.where(mask_arr)[0]
        sample_mask = np.isin(node_indices, idx)
        if sample_mask.sum() > 0:
            metrics = compute_metrics(y_true[sample_mask], y_pred[sample_mask])
            metrics["区域"] = label
            metrics["节点数"] = len(idx)
            results.append(metrics)
    return pd.DataFrame(results)


def evaluate_by_horizon(
    speed_matrix: pd.DataFrame, adj: np.ndarray, horizons: list[int] | None = None
) -> pd.DataFrame:
    """按预测步长计算历史平均和 VAR 的误差。"""
    if horizons is None:
        horizons = [1, 3, 6, 12]

    timestamps = speed_matrix.columns
    n_total = len(timestamps)
    n_test = min(288, n_total // 5)
    train_matrix = speed_matrix.iloc[:, : n_total - n_test]
    test_matrix = speed_matrix.iloc[:, n_total - n_test :]

    results = []
    for h in horizons:
        # VAR
        var_forecast = var_predict(train_matrix, steps=h)
        var_true = test_matrix.values[:, :h].T  # (h, nodes)
        var_pred = var_forecast[:h]
        m_var = compute_metrics(var_true.flatten(), var_pred.flatten())
        m_var["步长"] = h
        m_var["模型"] = "VAR"
        results.append(m_var)

        # 历史平均
        test_ts = pd.DatetimeIndex(test_matrix.columns[:h])
        ha_pred = historical_average_predict(train_matrix, test_ts)
        ha_true = test_matrix.values[:, :h].T
        m_ha = compute_metrics(ha_true.flatten(), ha_pred.flatten())
        m_ha["步长"] = h
        m_ha["模型"] = "历史平均"
        results.append(m_ha)

    return pd.DataFrame(results)


# ===========================================================================
# H. 可视化
# ===========================================================================
def plot_network_topology(
    nodes: pd.DataFrame, adj: np.ndarray, labels: np.ndarray | None = None, save_path: Path | None = None
) -> None:
    """绘制路网拓扑图。"""
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    edges = build_edge_list(adj)

    for i, j in edges:
        x_vals = [nodes.iloc[i]["x"], nodes.iloc[j]["x"]]
        y_vals = [nodes.iloc[i]["y"], nodes.iloc[j]["y"]]
        ax.plot(x_vals, y_vals, "k-", linewidth=0.8, alpha=0.5)

    if labels is not None:
        scatter = ax.scatter(
            nodes["x"], nodes["y"], c=labels, cmap="Set1", s=120, zorder=5, edgecolors="black"
        )
        plt.colorbar(scatter, ax=ax, label="聚类标签")
    else:
        ax.scatter(nodes["x"], nodes["y"], c="steelblue", s=120, zorder=5, edgecolors="black")

    for _, row in nodes.iterrows():
        ax.annotate(
            str(row["node_id"]),
            (row["x"], row["y"]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=9,
        )

    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.set_title("路网拓扑图")
    ax.set_aspect("equal")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_speed_heatmap(
    speed_matrix: pd.DataFrame, save_path: Path | None = None
) -> None:
    """绘制速度时空热力图。"""
    fig, ax = plt.subplots(figsize=(14, 5))
    data = speed_matrix.values[:10, :288 * 3]  # 前10节点、前3天
    im = ax.imshow(data, aspect="auto", cmap="RdYlGn", vmin=20, vmax=80)
    ax.set_xlabel("时间步（5 分钟间隔）")
    ax.set_ylabel("节点")
    ax.set_yticks(range(min(10, len(speed_matrix.index))))
    ax.set_yticklabels(speed_matrix.index[:10])
    ax.set_title("速度时空热力图（前 10 节点，前 3 天）")
    plt.colorbar(im, ax=ax, label="速度 (km/h)")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_timeseries_with_peak(
    speed_matrix: pd.DataFrame, node_id: str, days: int = 7, save_path: Path | None = None
) -> None:
    """绘制时间序列并标注高峰时段。"""
    series = speed_matrix.loc[node_id]
    n_points = min(days * 288, len(series))
    series = series.iloc[:n_points]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(series.index, series.values, linewidth=0.6, color="steelblue")

    # 标注早晚高峰
    for ts in series.index:
        if 7 <= ts.hour < 9:
            ax.axvspan(
                ts.replace(hour=7, minute=0), ts.replace(hour=9, minute=0),
                alpha=0.1, color="red"
            )
        if 17 <= ts.hour < 19:
            ax.axvspan(
                ts.replace(hour=17, minute=0), ts.replace(hour=19, minute=0),
                alpha=0.1, color="orange"
            )

    ax.set_xlabel("时间")
    ax.set_ylabel("速度 (km/h)")
    ax.set_title(f"节点 {node_id} 速度时间序列（{days} 天）")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_acf(acf_vals: np.ndarray, title: str = "自相关函数", save_path: Path | None = None) -> None:
    """绘制 ACF 图。"""
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.bar(range(len(acf_vals)), acf_vals, width=0.8, color="steelblue")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_xlabel("滞后（5 分钟间隔）")
    ax.set_ylabel("自相关系数")
    ax.set_title(title)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_time_lagged_cc(
    lags: np.ndarray, ccs: np.ndarray, node_a: str, node_b: str, save_path: Path | None = None
) -> None:
    """绘制时滞互相关图。"""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(lags, ccs, width=0.8, color="coral")
    best_idx = np.argmax(np.abs(ccs))
    ax.axvline(x=lags[best_idx], color="red", linestyle="--", label=f"最佳滞后={lags[best_idx]}")
    ax.set_xlabel("滞后（5 分钟间隔）")
    ax.set_ylabel("互相关系数")
    ax.set_title(f"时滞互相关: {node_a} vs {node_b}")
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_cluster_patterns(
    speed_matrix: pd.DataFrame, labels: np.ndarray, save_path: Path | None = None
) -> None:
    """绘制各聚类的平均速度模式。"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    n_days = 3
    n_points = n_days * 288
    unique_labels = sorted(set(labels))
    colors = ["steelblue", "coral", "seagreen"]

    for ax_idx, lbl in enumerate(unique_labels):
        if ax_idx >= len(axes):
            break
        mask = labels == lbl
        cluster_data = speed_matrix.values[mask, :n_points]
        mean_pattern = cluster_data.mean(axis=0)
        std_pattern = cluster_data.std(axis=0)
        time_axis = range(n_points)
        axes[ax_idx].plot(time_axis, mean_pattern, color=colors[ax_idx % len(colors)], linewidth=0.8)
        axes[ax_idx].fill_between(
            time_axis,
            mean_pattern - std_pattern,
            mean_pattern + std_pattern,
            alpha=0.2,
            color=colors[ax_idx % len(colors)],
        )
        axes[ax_idx].set_title(f"聚类 {lbl}（{mask.sum()} 个节点）")
        axes[ax_idx].set_xlabel("时间步")
        if ax_idx == 0:
            axes[ax_idx].set_ylabel("速度 (km/h)")

    plt.suptitle("DTW 聚类速度模式")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


def plot_model_comparison(
    comparison_df: pd.DataFrame, save_path: Path | None = None
) -> None:
    """绘制模型比较柱状图。"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    metrics = ["MAE", "RMSE", "MAPE"]
    for ax, metric in zip(axes, metrics):
        if metric in comparison_df.columns:
            pivot = comparison_df.pivot(index="步长", columns="模型", values=metric)
            pivot.plot(kind="bar", ax=ax, rot=0)
            ax.set_title(metric)
            ax.set_ylabel(metric)
            ax.set_xlabel("预测步长")
            ax.legend(title="模型")
    plt.suptitle("模型预测误差比较")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  保存: {save_path}")
    plt.close(fig)


# ===========================================================================
# 主函数
# ===========================================================================
def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("第 7 章 交通时空数据分析 - 参考实现")
    print("=" * 60)

    # ---- A. 数据加载 ----
    print("\n[A] 加载数据")
    speed_long = load_speed_data()
    adj = load_adjacency()
    nodes = load_nodes()

    # ---- B. 数据组织 ----
    print("\n[B] 数据组织")
    speed_matrix = long_to_matrix(speed_long)
    print(f"  节点-时间矩阵: {speed_matrix.shape}")
    print(f"  缺失比例: {speed_matrix.isna().mean().mean():.4f}")

    tensor = matrix_to_tensor(speed_matrix)
    print(f"  张量: {tensor.shape}")

    edges = build_edge_list(adj)
    print(f"  边列表: {len(edges)} 条边")

    # ---- C. 邻接矩阵 ----
    print("\n[C] 邻接矩阵构建")
    dist_adj = build_distance_adjacency(nodes, sigma=2.0, threshold=0.1)
    print(f"  距离邻接矩阵非零元素: {np.count_nonzero(dist_adj)}")

    corr_adj = build_correlation_adjacency(speed_matrix, threshold=0.3)
    print(f"  相关性邻接矩阵非零元素: {np.count_nonzero(corr_adj)}")
    print(f"  拓扑邻接矩阵非零元素: {np.count_nonzero(adj)}")

    # ---- D. 时空相关性 ----
    print("\n[D] 时空相关性分析")
    first_node = speed_matrix.index[0]
    acf_vals = compute_acf(speed_matrix.loc[first_node].values, nlags=288)
    plot_acf(acf_vals, title=f"节点 {first_node} 自相关函数",
             save_path=RESULT_DIR / "acf_node0.png")

    # 时滞互相关：取第一对相邻节点
    edges_list = build_edge_list(adj)
    if edges_list:
        i, j = edges_list[0]
        node_a, node_b = speed_matrix.index[i], speed_matrix.index[j]
        lags, ccs = time_lagged_cross_correlation(
            speed_matrix.iloc[i].values, speed_matrix.iloc[j].values, max_lag=36
        )
        best_lag = lags[np.argmax(np.abs(ccs))]
        best_cc = ccs[np.argmax(np.abs(ccs))]
        print(f"  节点 {node_a} vs {node_b}: 最佳滞后={best_lag}, 互相关={best_cc:.3f}")
        plot_time_lagged_cc(lags, ccs, node_a, node_b,
                            save_path=RESULT_DIR / "time_lagged_cc.png")

    # Moran's I
    mean_speeds = speed_matrix.mean(axis=1).values
    moran_i = compute_morans_i(mean_speeds, adj)
    print(f"  Moran's I（时间平均速度）: {moran_i:.4f}")

    # ---- E. DTW 聚类 ----
    print("\n[E] DTW + K-means 聚类")
    labels = cluster_nodes_dtw(speed_matrix, n_clusters=3, sample_rate=12)
    print(f"  聚类结果: {dict(zip(*np.unique(labels, return_counts=True)))}")

    plot_network_topology(nodes, adj, labels=labels,
                         save_path=RESULT_DIR / "network_clustered.png")
    plot_cluster_patterns(speed_matrix, labels,
                         save_path=RESULT_DIR / "cluster_patterns.png")

    # ---- F. 预测模型 ----
    print("\n[F] 预测模型")

    # 数据划分
    n_total = speed_matrix.shape[1]
    n_test = min(288, n_total // 5)  # 最后一天做测试
    train_matrix = speed_matrix.iloc[:, : n_total - n_test]
    test_matrix = speed_matrix.iloc[:, n_total - n_test :]
    print(f"  训练集: {train_matrix.shape[1]} 步, 测试集: {test_matrix.shape[1]} 步")

    # F1. 历史平均
    print("\n  [F1] 历史平均")
    test_ts = pd.DatetimeIndex(test_matrix.columns)
    ha_pred = historical_average_predict(train_matrix, test_ts)
    ha_true = test_matrix.values.T
    ha_metrics = compute_metrics(ha_true.flatten(), ha_pred.flatten())
    print(f"  历史平均 MAE: {ha_metrics['MAE']:.2f}, RMSE: {ha_metrics['RMSE']:.2f}, "
          f"MAPE: {ha_metrics['MAPE']:.2f}%")

    # F2. VAR
    print("\n  [F2] VAR 模型")
    var_forecast = var_predict(train_matrix, steps=n_test)
    var_metrics = compute_metrics(test_matrix.values.T.flatten(), var_forecast.flatten())
    print(f"  VAR MAE: {var_metrics['MAE']:.2f}, RMSE: {var_metrics['RMSE']:.2f}, "
          f"MAPE: {var_metrics['MAPE']:.2f}%")

    # F3. XGBoost
    print("\n  [F3] XGBoost")
    y_true_xgb, y_pred_xgb, test_df_xgb = xgboost_predict(speed_matrix, adj, test_steps=n_test)

    # ---- G. 模型比较 ----
    print("\n[G] 模型比较与误差分析")

    # 汇总表
    model_comparison = pd.DataFrame([
        {"模型": "历史平均", **ha_metrics},
        {"模型": "VAR", **var_metrics},
        {"模型": "XGBoost", **compute_metrics(y_true_xgb, y_pred_xgb)},
    ])
    model_comparison.to_csv(RESULT_DIR / "model_comparison.csv", index=False)
    print("\n  整体模型比较:")
    print(model_comparison.to_string(index=False))

    # 分区域误差
    print("\n  XGBoost 分区域误差:")
    node_idx_arr = test_df_xgb["node_idx"].values.astype(int)
    region_result = evaluate_by_region(y_true_xgb, y_pred_xgb, node_idx_arr, nodes, adj)
    region_result.to_csv(RESULT_DIR / "region_error.csv", index=False)
    print(region_result.to_string(index=False))

    # 分步长误差
    print("\n  分步长误差分析:")
    horizon_result = evaluate_by_horizon(speed_matrix, adj)
    horizon_result.to_csv(RESULT_DIR / "horizon_error.csv", index=False)
    print(horizon_result.to_string(index=False))
    plot_model_comparison(horizon_result, save_path=RESULT_DIR / "model_comparison.png")

    # ---- H. 可视化 ----
    print("\n[H] 生成可视化图表")
    plot_network_topology(nodes, adj, save_path=RESULT_DIR / "network_topology.png")
    plot_speed_heatmap(speed_matrix, save_path=RESULT_DIR / "speed_heatmap.png")
    plot_timeseries_with_peak(speed_matrix, speed_matrix.index[0], days=7,
                              save_path=RESULT_DIR / "speed_timeseries.png")

    # 邻接矩阵热力图
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, matrix, title in [
        (axes[0], adj, "拓扑邻接矩阵"),
        (axes[1], dist_adj, "距离邻接矩阵"),
        (axes[2], corr_adj, "相关性邻接矩阵"),
    ]:
        im = ax.imshow(matrix, cmap="Blues", vmin=0)
        ax.set_title(title)
        ax.set_xlabel("节点")
        ax.set_ylabel("节点")
        plt.colorbar(im, ax=ax, fraction=0.046)
    plt.suptitle("邻接矩阵对比")
    plt.tight_layout()
    fig.savefig(RESULT_DIR / "adjacency_comparison.png", dpi=150)
    print(f"  保存: {RESULT_DIR / 'adjacency_comparison.png'}")
    plt.close(fig)

    print("\n" + "=" * 60)
    print("所有结果已保存到:", RESULT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
