"""
Chapter 07 — Traffic Spatiotemporal Data Analysis

Generates all figures and result tables for the chapter using the synthetic
network speed data produced by scripts/generate_synthetic_network.py.

Figures  -> assets/chapter-07/
CSVs     -> data/results/chapter-07/

Usage:
    python scripts/create_chapter07_visuals.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import sparse
from scipy.spatial.distance import squareform
from statsmodels.tsa.api import VAR

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed"
SPEED_PATH = DATA_DIR / "synthetic_network_speed.csv"
ADJ_PATH = DATA_DIR / "synthetic_network_adjacency.npz"
NODES_PATH = DATA_DIR / "synthetic_network_nodes.csv"

OUT_DIR = ROOT / "assets/chapter-07"
RESULTS_DIR = ROOT / "data/results/chapter-07"

PRIMARY = "#176b5b"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def load_data():
    """Load speed panel, adjacency matrix, and node metadata."""
    speed = pd.read_csv(SPEED_PATH, parse_dates=["timestamp"])
    adj = sparse.load_npz(ADJ_PATH).toarray().astype(float)
    nodes = pd.read_csv(NODES_PATH)
    return speed, adj, nodes


def build_edge_list(adj: np.ndarray):
    """Return list of (i, j) edges from an adjacency matrix."""
    rows, cols = np.where(np.triu(adj) > 0)
    return list(zip(rows.tolist(), cols.tolist()))


def region_color_map(nodes: pd.DataFrame):
    """Return dict node_id -> colour based on region."""
    palette = {"center": "#176b5b", "middle": "#b7802f", "outer": "#7b7b7b"}
    return {row["node_id"]: palette[row["region"]] for _, row in nodes.iterrows()}


# ---------------------------------------------------------------------------
# DTW implementation (simple, no window constraint)
# ---------------------------------------------------------------------------
def dtw_distance(x: np.ndarray, y: np.ndarray) -> float:
    """Compute the DTW distance between two 1-D sequences."""
    n, m = len(x), len(y)
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (x[i - 1] - y[j - 1]) ** 2
            dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])
    return np.sqrt(dtw[n, m])


# ---------------------------------------------------------------------------
# Forecasting metrics
# ---------------------------------------------------------------------------
def mae(y_true, y_pred):
    return np.nanmean(np.abs(y_true - y_pred))


def rmse(y_true, y_pred):
    return np.sqrt(np.nanmean((y_true - y_pred) ** 2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    speed_df, adj, nodes = load_data()
    node_ids = nodes["node_id"].tolist()
    node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    n_nodes = len(node_ids)

    # Pivot to wide form: rows = timestamp, cols = node_id
    speed_wide = speed_df.pivot(index="timestamp", columns="node_id", values="speed")
    speed_wide = speed_wide[node_ids]  # ensure consistent ordering
    speed_wide.sort_index(inplace=True)

    # Fill missing values with linear interpolation then forward/back fill
    speed_wide = speed_wide.interpolate(method="linear").ffill().bfill()

    # =======================================================================
    # Figure 1 — Network topology
    # =======================================================================
    print("[1/12] Network topology ...")
    G = nx.Graph()
    for _, row in nodes.iterrows():
        G.add_node(row["node_id"], pos=(row["x"], row["y"]), region=row["region"])
    for i, j in build_edge_list(adj):
        G.add_edge(node_ids[i], node_ids[j])

    pos = nx.get_node_attributes(G, "pos")
    color_map = region_color_map(nodes)
    node_colors = [color_map[n] for n in G.nodes()]
    fig, ax = plt.subplots(figsize=(8, 8))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5, width=1.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=500, edgecolors="k")
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_color="white")
    # Legend
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#176b5b", markersize=12, label="center"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#b7802f", markersize=12, label="middle"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#7b7b7b", markersize=12, label="outer"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", title="Region")
    ax.set_title("Network Topology — Nodes Colored by Region")
    ax.axis("off")
    savefig("01_network_topology.png")

    # =======================================================================
    # Figure 2 — Adjacency matrix heatmap
    # =======================================================================
    print("[2/12] Adjacency heatmap ...")
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(adj, ax=ax, cmap="YlGnBu", cbar_kws={"label": "Connection"},
                xticklabels=node_ids, yticklabels=node_ids, linewidths=0.5, linecolor="white")
    ax.set_title("Adjacency Matrix Heatmap")
    ax.set_xlabel("Node")
    ax.set_ylabel("Node")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    savefig("02_adjacency_heatmap.png")

    # =======================================================================
    # Figure 3 — Speed heatmap (one day)
    # =======================================================================
    print("[3/12] Speed heatmap ...")
    first_day = speed_wide.index[0].normalize()
    one_day = speed_wide.loc[speed_wide.index.normalize() == first_day]
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.heatmap(one_day.T, ax=ax, cmap="RdYlGn", cbar_kws={"label": "Speed (km/h)"},
                xticklabels=48, yticklabels=1, linewidths=0)
    ax.set_title(f"Speed Heatmap — {first_day.strftime('%Y-%m-%d')} (Node x Time)")
    ax.set_xlabel("Time of day")
    ax.set_ylabel("Node")
    # Relabel x-axis with hours
    n_ticks = 12
    tick_positions = np.linspace(0, len(one_day) - 1, n_ticks, dtype=int)
    tick_labels = [one_day.index[i].strftime("%H:%M") for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")
    savefig("03_speed_heatmap.png")

    # =======================================================================
    # Figure 4 — Time-lagged cross-correlation
    # =======================================================================
    print("[4/12] Time-lagged cross-correlation ...")
    max_lag = 12  # 12 * 5 min = 60 min
    selected_pairs = [(0, 1), (0, 5), (0, 10), (1, 2), (5, 10), (3, 7)]
    corr_records = []
    lag_matrix = np.zeros((len(selected_pairs), max_lag + 1))

    for p_idx, (ni, nj) in enumerate(selected_pairs):
        xi = speed_wide[node_ids[ni]].values
        xj = speed_wide[node_ids[nj]].values
        xi = (xi - xi.mean()) / (xi.std() + 1e-9)
        xj = (xj - xj.mean()) / (xj.std() + 1e-9)
        for lag in range(max_lag + 1):
            if lag == 0:
                c = np.corrcoef(xi, xj)[0, 1]
            else:
                c = np.corrcoef(xi[lag:], xj[:-lag])[0, 1]
            lag_matrix[p_idx, lag] = c
            corr_records.append({
                "node_i": node_ids[ni],
                "node_j": node_ids[nj],
                "lag_steps": lag,
                "lag_minutes": lag * 5,
                "correlation": round(c, 4),
            })

    corr_df = pd.DataFrame(corr_records)
    # Save top correlations
    top_corr = corr_df.sort_values("correlation", key=abs, ascending=False).head(30)
    top_corr.to_csv(RESULTS_DIR / "time_lagged_correlation.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    pair_labels = [f"{node_ids[ni]}-{node_ids[nj]}" for ni, nj in selected_pairs]
    for p_idx, label in enumerate(pair_labels):
        ax.plot(range(max_lag + 1), lag_matrix[p_idx], marker="o", label=label)
    ax.set_title("Time-lagged Cross-correlation Between Node Pairs")
    ax.set_xlabel("Lag (5-min steps)")
    ax.set_ylabel("Correlation")
    ax.legend(title="Node pair", fontsize=8)
    savefig("04_time_lagged_cross_correlation.png")

    # =======================================================================
    # Figure 5 — Daily speed by region
    # =======================================================================
    print("[5/12] Daily speed by region ...")
    speed_long = speed_df.copy()
    speed_long["hour"] = speed_long["timestamp"].dt.hour
    speed_long["minute"] = speed_long["timestamp"].dt.minute
    speed_long["time_of_day"] = speed_long["hour"] + speed_long["minute"] / 60.0
    speed_long = speed_long.merge(nodes[["node_id", "region"]], on="node_id")

    daily_by_region = (
        speed_long.groupby(["region", "time_of_day"], as_index=False)
        .agg(avg_speed=("speed", "mean"))
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    region_palette = {"center": "#176b5b", "middle": "#b7802f", "outer": "#7b7b7b"}
    for region in ["center", "middle", "outer"]:
        subset = daily_by_region[daily_by_region["region"] == region]
        ax.plot(subset["time_of_day"], subset["avg_speed"], label=region,
                color=region_palette[region], linewidth=2)
    ax.set_title("Average Daily Speed by Region")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Speed (km/h)")
    ax.set_xticks(range(0, 25, 2))
    ax.legend(title="Region")
    savefig("05_daily_speed_by_region.png")

    # =======================================================================
    # Figure 6 — DTW clustering
    # =======================================================================
    print("[6/12] DTW clustering ...")
    # Build daily average curves per node (use first weekday)
    first_weekday = None
    for d in sorted(speed_wide.index.normalize().unique()):
        if d.weekday() < 5:
            first_weekday = d
            break
    day_mask = speed_wide.index.normalize() == first_weekday
    daily_curves = speed_wide.loc[day_mask].values.T  # shape (n_nodes, n_steps)

    # Compute DTW distance matrix
    dtw_mat = np.zeros((n_nodes, n_nodes))
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            d = dtw_distance(daily_curves[i], daily_curves[j])
            dtw_mat[i, j] = d
            dtw_mat[j, i] = d

    # Agglomerative clustering into 3 clusters
    from scipy.cluster.hierarchy import fcluster, linkage
    condensed = squareform(dtw_mat)
    Z = linkage(condensed, method="average")
    cluster_labels = fcluster(Z, t=3, criterion="maxclust")  # 1-indexed

    dtw_cluster_df = pd.DataFrame({
        "node_id": node_ids,
        "cluster": cluster_labels,
        "region": nodes["region"].values,
    })
    dtw_cluster_df.to_csv(RESULTS_DIR / "dtw_clusters.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    # DTW distance heatmap
    sns.heatmap(dtw_mat, ax=axes[0], cmap="YlOrRd", xticklabels=node_ids, yticklabels=node_ids,
                cbar_kws={"label": "DTW distance"}, linewidths=0.3, linecolor="white")
    axes[0].set_title("DTW Distance Matrix")
    axes[0].set_xlabel("Node")
    axes[0].set_ylabel("Node")
    axes[0].tick_params(axis="x", rotation=45)
    # Cluster assignments
    cluster_palette = {1: "#176b5b", 2: "#b7802f", 3: "#7b7b7b"}
    node_cluster_colors = [cluster_palette[c] for c in cluster_labels]
    axes[1].bar(range(n_nodes), [1] * n_nodes, color=node_cluster_colors)
    axes[1].set_xticks(range(n_nodes))
    axes[1].set_xticklabels(node_ids, rotation=45, ha="right")
    axes[1].set_yticks([])
    axes[1].set_title("DTW Cluster Assignments")
    axes[1].set_xlabel("Node")
    legend_patches = [Patch(facecolor=cluster_palette[k], label=f"Cluster {k}") for k in sorted(cluster_palette)]
    axes[1].legend(handles=legend_patches, loc="upper right")
    savefig("06_dtw_clustering.png")

    # =======================================================================
    # Train / test split — first 3 weeks train, last week test
    # =======================================================================
    timestamps = speed_wide.index.sort_values()
    n_total = len(timestamps)
    steps_per_week = n_total // 4
    split_idx = 3 * steps_per_week
    train_ts = timestamps[:split_idx]
    test_ts = timestamps[split_idx:]

    train_df = speed_wide.loc[train_ts]
    test_df = speed_wide.loc[test_ts]

    # =======================================================================
    # Figure 7 — VAR forecast
    # =======================================================================
    print("[7/12] VAR forecast ...")
    # Select a subset of nodes for VAR (to keep it tractable)
    var_nodes = ["N00", "N01", "N05", "N10"]
    train_var = train_df[var_nodes].copy()

    # Deseason: subtract hourly mean from training set
    hourly_mean = train_var.groupby(train_var.index.hour).transform("mean")
    train_var_deseas = train_var - hourly_mean

    model_var = VAR(train_var_deseas.values)
    lag_order = model_var.select_order(maxlags=20).aic
    var_result = model_var.fit(lag_order)

    # Forecast: rolling 1-step-ahead on test set
    # We need to feed the last `lag_order` observations from the end of training
    # then step through test
    forecast_steps = min(len(test_df), 288)  # one day
    # For multi-step evaluation we'll do direct forecast
    var_forecast = var_result.forecast(train_var_deseas.values[-lag_order:], steps=forecast_steps)

    # Re-add seasonality
    test_subset = test_df[var_nodes].iloc[:forecast_steps]
    test_hours = test_subset.index.hour
    for col_idx, col in enumerate(var_nodes):
        hour_means = hourly_mean[col].groupby(hourly_mean.index.hour).mean()
        var_forecast[:, col_idx] += test_hours.map(hour_means).values

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True)
    time_axis = test_subset.index
    for idx, (col, ax) in enumerate(zip(var_nodes, axes.flatten())):
        ax.plot(time_axis, test_subset[col].values, label="Actual", color="k", linewidth=1.2)
        ax.plot(time_axis, var_forecast[:, idx], label="VAR", color=PRIMARY, linewidth=1.2)
        ax.set_title(f"Node {col}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Speed (km/h)")
        ax.legend(fontsize=8)
    fig.suptitle("VAR Forecast vs Actual (1-day horizon)", fontweight="bold")
    savefig("07_var_forecast.png")

    # =======================================================================
    # Figure 8 — XGBoost forecast
    # =======================================================================
    print("[8/12] XGBoost forecast ...")
    from xgboost import XGBRegressor

    # Build feature matrix for all nodes (with timestamp for time-ordered split)
    def build_features(df_wide: pd.DataFrame, adj_matrix: np.ndarray):
        """Construct feature dataframe from wide speed matrix."""
        records = []
        lag_steps_list = [1, 2, 3, 6, 12]  # 5, 10, 15, 30, 60 min
        for nid in node_ids:
            series = df_wide[nid].copy()
            node_idx = node_id_to_idx[nid]
            neighbors = np.where(adj_matrix[node_idx] > 0)[0]
            neighbor_ids = [node_ids[ni] for ni in neighbors]

            feat = pd.DataFrame(index=series.index)
            feat["timestamp"] = series.index
            feat["node_id"] = nid
            feat["speed"] = series.values

            # Own lags
            for lag in lag_steps_list:
                feat[f"lag_{lag}"] = series.shift(lag).values

            # Neighbor average lag
            if len(neighbor_ids) > 0:
                neighbor_avg = df_wide[neighbor_ids].mean(axis=1)
                for lag in [1, 3, 6]:
                    feat[f"nbr_lag_{lag}"] = neighbor_avg.shift(lag).values
            else:
                for lag in [1, 3, 6]:
                    feat[f"nbr_lag_{lag}"] = np.nan

            # Temporal features
            feat["hour"] = series.index.hour
            feat["day_of_week"] = series.index.dayofweek

            # Region encoding
            region = nodes.loc[nodes["node_id"] == nid, "region"].values[0]
            feat["region_center"] = int(region == "center")
            feat["region_middle"] = int(region == "middle")
            feat["region_outer"] = int(region == "outer")

            records.append(feat)

        all_feat = pd.concat(records, ignore_index=True)
        all_feat.dropna(inplace=True)
        all_feat.sort_values("timestamp", inplace=True)
        all_feat.reset_index(drop=True, inplace=True)
        return all_feat

    all_features = build_features(speed_wide, adj)
    feature_cols = [c for c in all_features.columns if c not in ("timestamp", "node_id", "speed")]

    # Split: use timestamp-based split
    split_ts = test_ts[0]
    train_feat = all_features[all_features["timestamp"] < split_ts]
    test_feat = all_features[all_features["timestamp"] >= split_ts]

    X_train = train_feat[feature_cols].values
    y_train = train_feat["speed"].values
    X_test = test_feat[feature_cols].values
    y_test = test_feat["speed"].values
    test_node_ids_arr = test_feat["node_id"].values
    test_timestamps_arr = test_feat["timestamp"].values

    xgb_model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)

    # Plot for selected nodes
    xgb_plot_nodes = ["N00", "N05", "N10"]
    fig, axes = plt.subplots(len(xgb_plot_nodes), 1, figsize=(14, 10), sharex=True)
    for ax, nid in zip(axes, xgb_plot_nodes):
        mask = test_node_ids_arr == nid
        if mask.sum() == 0:
            continue
        ts = test_timestamps_arr[mask]
        actual = y_test[mask]
        pred = xgb_pred[mask]
        # Plot first day
        one_day_mask = ts < ts[0] + pd.Timedelta(days=1)
        ax.plot(ts[one_day_mask], actual[one_day_mask], label="Actual", color="k", linewidth=1.2)
        ax.plot(ts[one_day_mask], pred[one_day_mask], label="XGBoost", color=PRIMARY, linewidth=1.2)
        ax.set_title(f"Node {nid}")
        ax.set_ylabel("Speed (km/h)")
        ax.legend(fontsize=8)
    axes[-1].set_xlabel("Time")
    fig.suptitle("XGBoost Forecast vs Actual (1-day sample)", fontweight="bold")
    savefig("08_xgboost_forecast.png")

    # =======================================================================
    # Compute errors for all models
    # =======================================================================
    # Historical mean baseline
    train_mean = train_df.mean()

    # Historical mean errors (per node)
    hist_mean_errors = {}
    for nid in node_ids:
        actual = test_df[nid].values
        pred = np.full_like(actual, train_mean[nid])
        hist_mean_errors[nid] = {"mae": mae(actual, pred), "rmse": rmse(actual, pred)}

    # XGBoost errors (per node)
    xgb_errors = {}
    for nid in node_ids:
        mask = test_node_ids_arr == nid
        if mask.sum() == 0:
            continue
        actual = y_test[mask]
        pred = xgb_pred[mask]
        xgb_errors[nid] = {"mae": mae(actual, pred), "rmse": rmse(actual, pred)}

    # Full VAR for all nodes
    print("[9/12] Model comparison ...")
    avg_hist_mae = np.mean([v["mae"] for v in hist_mean_errors.values()])
    avg_hist_rmse = np.mean([v["rmse"] for v in hist_mean_errors.values()])
    avg_xgb_mae = np.mean([v["mae"] for v in xgb_errors.values()])
    avg_xgb_rmse = np.mean([v["rmse"] for v in xgb_errors.values()])

    # Full VAR for all nodes (may be slow, use maxlags=5)
    train_var_all = train_df.copy()
    hourly_mean_all = train_var_all.groupby(train_var_all.index.hour).transform("mean")
    train_var_all_deseas = train_var_all - hourly_mean_all

    model_var_all = VAR(train_var_all_deseas.values)
    try:
        var_lag = min(model_var_all.select_order(maxlags=10).aic, 10)
    except Exception:
        var_lag = 5
    var_result_all = model_var_all.fit(var_lag)

    # 1-step-ahead forecast for test period
    n_test = len(test_df)
    var_all_forecast = np.zeros((n_test, n_nodes))
    history = train_var_all_deseas.values.copy()
    for t in range(n_test):
        fc = var_result_all.forecast(history[-var_lag:], steps=1)
        var_all_forecast[t] = fc[0]
        # Append actual deseas observation for next step
        actual_deseas = test_df.iloc[t].values - hourly_mean_all.iloc[t % len(hourly_mean_all)].values
        history = np.vstack([history, actual_deseas])

    # Re-add seasonality
    for col_idx in range(n_nodes):
        hour_means = hourly_mean_all.iloc[:, col_idx].groupby(hourly_mean_all.index.hour).mean()
        for t in range(n_test):
            h = test_df.index[t].hour
            var_all_forecast[t, col_idx] += hour_means.get(h, 0)

    # Per-node VAR errors
    var_all_errors = {}
    for col_idx, nid in enumerate(node_ids):
        actual = test_df[nid].values
        pred = var_all_forecast[:, col_idx]
        var_all_errors[nid] = {"mae": mae(actual, pred), "rmse": rmse(actual, pred)}

    avg_var_mae = np.mean([v["mae"] for v in var_all_errors.values()])
    avg_var_rmse = np.mean([v["rmse"] for v in var_all_errors.values()])

    # =======================================================================
    # Figure 9 — Model comparison bar chart
    # =======================================================================
    comparison_df = pd.DataFrame({
        "model": ["historical_mean", "VAR", "XGBoost"],
        "MAE": [avg_hist_mae, avg_var_mae, avg_xgb_mae],
        "RMSE": [avg_hist_rmse, avg_var_rmse, avg_xgb_rmse],
    })
    comparison_df.to_csv(RESULTS_DIR / "model_comparison.csv", index=False)

    comp_long = comparison_df.melt(id_vars="model", value_vars=["MAE", "RMSE"], var_name="metric", value_name="error")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=comp_long, x="metric", y="error", hue="model", ax=ax, palette="Set2")
    ax.set_title("Model Comparison: MAE and RMSE")
    ax.set_xlabel("")
    ax.set_ylabel("Error (km/h)")
    ax.legend(title="Model")
    savefig("09_model_comparison.png")

    # =======================================================================
    # Figure 10 — Error spatial distribution (MAE by node, colored by region)
    # =======================================================================
    print("[10/12] Error spatial distribution ...")
    error_records = []
    for nid in node_ids:
        region = nodes.loc[nodes["node_id"] == nid, "region"].values[0]
        error_records.append({
            "node_id": nid,
            "region": region,
            "XGBoost_MAE": xgb_errors.get(nid, {}).get("mae", np.nan),
            "VAR_MAE": var_all_errors.get(nid, {}).get("mae", np.nan),
            "HistMean_MAE": hist_mean_errors.get(nid, {}).get("mae", np.nan),
        })
    error_df = pd.DataFrame(error_records)

    fig, ax = plt.subplots(figsize=(14, 6))
    error_melt = error_df.melt(id_vars=["node_id", "region"],
                               value_vars=["HistMean_MAE", "VAR_MAE", "XGBoost_MAE"],
                               var_name="model", value_name="MAE")
    sns.barplot(data=error_melt, x="node_id", y="MAE", hue="model", ax=ax, palette="Set2")
    # Color x-tick labels by region
    region_colors = {"center": "#176b5b", "middle": "#b7802f", "outer": "#7b7b7b"}
    for label in ax.get_xticklabels():
        nid = label.get_text()
        reg = nodes.loc[nodes["node_id"] == nid, "region"].values[0]
        label.set_color(region_colors[reg])
    ax.set_title("MAE by Node (colored tick labels = region)")
    ax.set_xlabel("Node (center=green, middle=orange, outer=gray)")
    ax.set_ylabel("MAE (km/h)")
    ax.legend(title="Model")
    savefig("10_error_spatial_distribution.png")

    # =======================================================================
    # Figure 11 — Multi-horizon errors
    # =======================================================================
    print("[11/12] Multi-horizon errors ...")
    horizons = [1, 3, 6, 12]  # in 5-min steps
    horizon_labels = ["5 min", "15 min", "30 min", "60 min"]
    multi_horizon = {"model": [], "horizon": [], "MAE": [], "RMSE": []}

    for h, h_label in zip(horizons, horizon_labels):
        # Historical mean: same regardless of horizon
        hmae_list = [hist_mean_errors[nid]["mae"] for nid in node_ids]
        hrmse_list = [hist_mean_errors[nid]["rmse"] for nid in node_ids]
        multi_horizon["model"].append("historical_mean")
        multi_horizon["horizon"].append(h_label)
        multi_horizon["MAE"].append(np.mean(hmae_list))
        multi_horizon["RMSE"].append(np.mean(hrmse_list))

        # VAR: multi-step forecast
        var_multi_fc = var_result_all.forecast(train_var_all_deseas.values[-var_lag:], steps=h)
        # Evaluate at step h-1 (the h-th step ahead)
        actual_h = test_df.iloc[h - 1].values
        # Re-add seasonality
        hour_h = test_df.index[h - 1].hour
        for col_idx in range(n_nodes):
            hour_means = hourly_mean_all.iloc[:, col_idx].groupby(hourly_mean_all.index.hour).mean()
            var_multi_fc[-1, col_idx] += hour_means.get(hour_h, 0)
        pred_h = var_multi_fc[-1]
        multi_horizon["model"].append("VAR")
        multi_horizon["horizon"].append(h_label)
        multi_horizon["MAE"].append(mae(actual_h, pred_h))
        multi_horizon["RMSE"].append(rmse(actual_h, pred_h))

        # XGBoost: use lag features that correspond to horizon h
        # For simplicity, evaluate XGBoost on test samples where we can construct h-step ahead target
        # Shift target by h steps
        xgb_h_errors_mae = []
        xgb_h_errors_rmse = []
        for nid in node_ids:
            mask = test_node_ids_arr == nid
            if mask.sum() < h:
                continue
            actual = y_test[mask][h - 1:]
            pred = xgb_pred[mask][:-h] if h > 1 else xgb_pred[mask]
            # Align lengths
            min_len = min(len(actual), len(pred))
            if min_len == 0:
                continue
            actual = actual[:min_len]
            pred = pred[:min_len]
            xgb_h_errors_mae.append(mae(actual, pred))
            xgb_h_errors_rmse.append(rmse(actual, pred))
        multi_horizon["model"].append("XGBoost")
        multi_horizon["horizon"].append(h_label)
        multi_horizon["MAE"].append(np.mean(xgb_h_errors_mae) if xgb_h_errors_mae else np.nan)
        multi_horizon["RMSE"].append(np.mean(xgb_h_errors_rmse) if xgb_h_errors_rmse else np.nan)

    mh_df = pd.DataFrame(multi_horizon)

    fig, ax = plt.subplots(figsize=(10, 6))
    for model_name in ["historical_mean", "VAR", "XGBoost"]:
        subset = mh_df[mh_df["model"] == model_name]
        ax.plot(subset["horizon"], subset["MAE"], marker="o", label=model_name, linewidth=2)
    ax.set_title("Error vs Prediction Horizon")
    ax.set_xlabel("Prediction horizon")
    ax.set_ylabel("MAE (km/h)")
    ax.legend(title="Model")
    savefig("11_multi_horizon_errors.png")

    # =======================================================================
    # Figure 12 — Center vs edge errors (grouped bar)
    # =======================================================================
    print("[12/12] Center vs middle vs outer errors ...")
    regional_err_records = []
    for nid in node_ids:
        region = nodes.loc[nodes["node_id"] == nid, "region"].values[0]
        for model_name, err_dict in [("historical_mean", hist_mean_errors),
                                      ("VAR", var_all_errors),
                                      ("XGBoost", xgb_errors)]:
            if nid in err_dict:
                regional_err_records.append({
                    "region": region,
                    "model": model_name,
                    "MAE": err_dict[nid]["mae"],
                    "RMSE": err_dict[nid]["rmse"],
                })

    regional_errors_df = pd.DataFrame(regional_err_records)
    regional_summary = regional_errors_df.groupby(["region", "model"], as_index=False).agg(
        MAE=("MAE", "mean"), RMSE=("RMSE", "mean")
    )
    regional_summary.to_csv(RESULTS_DIR / "regional_errors.csv", index=False)

    # Also add multi-horizon per-region data
    for h, h_label in zip(horizons, horizon_labels):
        for region in ["center", "middle", "outer"]:
            region_nodes = nodes[nodes["region"] == region]["node_id"].tolist()
            for model_name in ["historical_mean", "VAR", "XGBoost"]:
                mh_subset = mh_df[(mh_df["model"] == model_name) & (mh_df["horizon"] == h_label)]
                if len(mh_subset) > 0:
                    regional_err_records.append({
                        "region": region,
                        "model": model_name,
                        "horizon": h_label,
                        "MAE": mh_subset["MAE"].values[0],
                        "RMSE": mh_subset["RMSE"].values[0],
                    })
    # Rewrite with full data
    regional_errors_full = pd.DataFrame(regional_err_records)
    regional_errors_full.to_csv(RESULTS_DIR / "regional_errors.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=regional_summary, x="region", y="MAE", hue="model", ax=ax,
                order=["center", "middle", "outer"], palette="Set2")
    ax.set_title("Prediction Error by Region")
    ax.set_xlabel("Region")
    ax.set_ylabel("MAE (km/h)")
    ax.legend(title="Model")
    savefig("12_center_vs_edge_errors.png")

    # =======================================================================
    # Summary
    # =======================================================================
    n_figures = len(list(OUT_DIR.glob("*.png")))
    n_csvs = len(list(RESULTS_DIR.glob("*.csv")))
    print("\n" + "=" * 60)
    print(f"Chapter 07 visual generation complete")
    print(f"  Figures : {n_figures}  -> {OUT_DIR}")
    print(f"  CSVs    : {n_csvs}  -> {RESULTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
