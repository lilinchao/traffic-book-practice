"""
Chapter 06 — Traffic Time Series Analysis: figure & table generation
====================================================================

Reads synthetic 5-minute traffic flow data (3 detectors, 4 weeks) and
produces 12 PNG figures + 4 CSV result tables for the textbook.

Figures  -> assets/chapter-06/
Tables   -> data/results/chapter-06/
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf, pacf, adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/synthetic_traffic_flow_5min.csv"
OUT_DIR = ROOT / "assets/chapter-06"
RESULTS_DIR = ROOT / "data/results/chapter-06"

PRIMARY = "#176b5b"
SECONDARY = "#b7802f"

# Time-period definitions (hour boundaries)
TIME_PERIODS = {
    "Early morning": (0, 6),
    "Morning peak": (7, 9),
    "Midday": (10, 16),
    "Evening peak": (17, 19),
    "Night": (20, 23),
}


def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def load_data() -> pd.DataFrame:
    """Load and prepare the 5-minute traffic flow CSV."""
    df = pd.read_csv(DATA_PATH)
    # The generator uses "datetime"; accept "timestamp" as well
    ts_col = "datetime" if "datetime" in df.columns else "timestamp"
    df[ts_col] = pd.to_datetime(df[ts_col])
    df = df.rename(columns={ts_col: "timestamp"})
    df = df.sort_values(["detector_id", "timestamp"]).reset_index(drop=True)
    return df


def _pick_detector(df: pd.DataFrame, det: str | None = None) -> pd.DataFrame:
    """Return data for one detector (first one if *det* is None)."""
    if det is None:
        det = df["detector_id"].iloc[0]
    return df.loc[df["detector_id"] == det].copy()


# ===================================================================
# Figure 1 — 7-day flow time series for first detector
# ===================================================================
def fig_01_7day_flow(df: pd.DataFrame) -> None:
    sub = _pick_detector(df)
    start = sub["timestamp"].min()
    end = start + pd.Timedelta(days=7)
    week = sub[(sub["timestamp"] >= start) & (sub["timestamp"] < end)]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(week["timestamp"], week["flow"], color=PRIMARY, linewidth=0.8)
    ax.set_title("7-Day Traffic Flow Time Series (Detector 1)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flow (vehicles / 5 min)")
    # Shade weekends
    for d in pd.date_range(start.date(), end.date(), freq="D"):
        if d.weekday() >= 5:
            ax.axvspan(d, d + pd.Timedelta(days=1), color="#f5e6ab", alpha=0.35)
    savefig("01_7day_flow_timeseries.png")


# ===================================================================
# Figure 2 — Average daily profile: weekday vs weekend
# ===================================================================
def fig_02_daily_profile(df: pd.DataFrame) -> None:
    sub = _pick_detector(df)
    sub["hour_minute"] = sub["timestamp"].dt.hour + sub["timestamp"].dt.minute / 60
    sub["is_weekend"] = sub["timestamp"].dt.weekday >= 5

    profile = (
        sub.groupby(["is_weekend", "hour_minute"])["flow"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    for weekend, label, color in [(False, "Weekday", PRIMARY), (True, "Weekend", SECONDARY)]:
        part = profile[profile["is_weekend"] == weekend]
        ax.plot(part["hour_minute"], part["flow"], label=label, color=color, linewidth=2)

    ax.set_title("Average Daily Flow Profile: Weekday vs Weekend")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Mean flow (vehicles / 5 min)")
    ax.set_xticks(range(0, 25, 2))
    ax.legend()
    savefig("02_daily_profile_weekday_weekend.png")


# ===================================================================
# Figure 3 — Heatmap of flow (hour x day-of-week)
# ===================================================================
def fig_03_heatmap(df: pd.DataFrame) -> None:
    sub = _pick_detector(df)
    sub["hour"] = sub["timestamp"].dt.hour
    sub["dow"] = sub["timestamp"].dt.dayofweek  # 0=Mon .. 6=Sun

    pivot = sub.pivot_table(index="hour", columns="dow", values="flow", aggfunc="mean")
    pivot.columns = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot, cmap="YlGnBu", annot=False, ax=ax)
    ax.set_title("Mean Flow by Hour and Day of Week")
    ax.set_xlabel("")
    ax.set_ylabel("Hour of day")
    savefig("03_flow_heatmap.png")


# ===================================================================
# Figure 4 — ACF and PACF
# ===================================================================
def fig_04_acf_pacf(df: pd.DataFrame) -> None:
    sub = _pick_detector(df)
    series = sub.set_index("timestamp")["flow"]

    nlags = 72  # 6 hours at 5-min resolution
    acf_vals = acf(series, nlags=nlags, fft=True)
    pacf_vals = pacf(series, nlags=nlags)

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    lags = np.arange(nlags + 1)

    # ACF
    axes[0].bar(lags, acf_vals, color=PRIMARY, width=0.8)
    ci = 1.96 / np.sqrt(len(series))
    axes[0].axhline(ci, color="grey", ls="--", lw=0.8)
    axes[0].axhline(-ci, color="grey", ls="--", lw=0.8)
    axes[0].set_title("Autocorrelation Function (ACF)")
    axes[0].set_ylabel("ACF")

    # PACF
    axes[1].bar(lags, pacf_vals, color=SECONDARY, width=0.8)
    axes[1].axhline(ci, color="grey", ls="--", lw=0.8)
    axes[1].axhline(-ci, color="grey", ls="--", lw=0.8)
    axes[1].set_title("Partial Autocorrelation Function (PACF)")
    axes[1].set_xlabel("Lag (5-min intervals)")
    axes[1].set_ylabel("PACF")
    savefig("04_acf_pacf.png")


# ===================================================================
# Figure 5 — ADF before / after differencing
# ===================================================================
def fig_05_adf(df: pd.DataFrame) -> dict:
    sub = _pick_detector(df)
    series = sub.set_index("timestamp")["flow"]

    adf_orig = adfuller(series.dropna(), autolag="AIC")
    diff1 = series.diff().dropna()
    adf_diff = adfuller(diff1, autolag="AIC")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(series.index[:288 * 3], series.values[:288 * 3], color=PRIMARY, linewidth=0.7)
    axes[0].set_title(f"Original Series\nADF p = {adf_orig[1]:.4f}")
    axes[0].set_ylabel("Flow")
    axes[0].set_xlabel("")

    axes[1].plot(diff1.index[:288 * 3], diff1.values[:288 * 3], color=SECONDARY, linewidth=0.7)
    axes[1].set_title(f"First Difference\nADF p = {adf_diff[1]:.4f}")
    axes[1].set_ylabel("Diff(flow)")
    axes[1].set_xlabel("")

    fig.suptitle("Stationarity Check: Original vs Differenced Series", fontsize=16, fontweight="bold")
    savefig("05_adf_before_after.png")

    return {
        "adf_stat_original": adf_orig[0],
        "adf_pvalue_original": adf_orig[1],
        "adf_stat_diff1": adf_diff[0],
        "adf_pvalue_diff1": adf_diff[1],
    }


# ===================================================================
# ARIMA helpers
# ===================================================================
def _train_test_split(df: pd.DataFrame):
    """First 3 weeks train, last week test, for the first detector."""
    sub = _pick_detector(df)
    sub = sub.set_index("timestamp")["flow"].asfreq("5min")
    sub = sub.ffill()

    n_total = len(sub)
    n_train = int(n_total * 3 / 4)  # ~3 weeks
    train = sub.iloc[:n_train]
    test = sub.iloc[n_train:]
    return train, test


def _baseline_forecast(train: pd.Series, test_index: pd.DatetimeIndex) -> np.ndarray:
    """Historical same-hour mean as baseline."""
    train_df = train.to_frame("flow")
    train_df["hour"] = train_df.index.hour
    train_df["minute"] = train_df.index.minute
    hourly_mean = train_df.groupby(["hour", "minute"])["flow"].mean()
    preds = []
    for ts in test_index:
        key = (ts.hour, ts.minute)
        preds.append(hourly_mean.get(key, train.mean()))
    return np.array(preds)


def _arima_forecast(train: pd.Series, test: pd.Series, order=(1, 1, 1)):
    """Fit ARIMA on training data, produce multi-step forecasts (static, not rolling)."""
    model = ARIMA(train, order=order)
    fitted = model.fit()
    n_test = len(test)
    forecast = fitted.forecast(steps=n_test)
    return np.array(forecast), fitted


def _arima_rolling_last3(train: pd.Series, test: pd.Series, order=(1, 1, 1)):
    """Rolling one-step forecast for the last 1 day of the test set."""
    n_last = min(288, len(test))  # 1 day at 5-min (288 steps)
    test_last = test.iloc[-n_last:]
    history = pd.concat([train, test.iloc[: len(test) - n_last]])

    predictions: list[float] = []
    for t in range(n_last):
        model = ARIMA(history, order=order)
        fitted = model.fit()
        yhat = fitted.forecast(steps=1).iloc[0]
        predictions.append(yhat)
        history = pd.concat([history, test_last.iloc[t:t + 1]])
    return np.array(predictions), fitted, test_last


# ===================================================================
# Figure 6 — ARIMA residual diagnostics
# ===================================================================
def fig_06_arima_diagnostics(train: pd.Series, order=(1, 1, 1)) -> dict:
    model = ARIMA(train, order=order)
    fitted = model.fit()
    resid = fitted.resid.dropna()

    # Ljung-Box test on residuals
    lb = acorr_ljungbox(resid, lags=[24], return_df=True)
    lb_stat = lb["lb_stat"].iloc[0]
    lb_pval = lb["lb_pvalue"].iloc[0]

    # Residual ACF
    nlags = 48
    acf_resid = acf(resid, nlags=nlags, fft=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Residual ACF bar plot
    axes[0].bar(range(nlags + 1), acf_resid, color=PRIMARY, width=0.8)
    ci = 1.96 / np.sqrt(len(resid))
    axes[0].axhline(ci, color="grey", ls="--", lw=0.8)
    axes[0].axhline(-ci, color="grey", ls="--", lw=0.8)
    axes[0].set_title("Residual ACF")
    axes[0].set_xlabel("Lag")
    axes[0].set_ylabel("ACF")

    # Residual histogram
    axes[1].hist(resid, bins=50, color=PRIMARY, edgecolor="white", density=True)
    axes[1].set_title(f"Residual Distribution\nLjung-Box(24) p = {lb_pval:.4f}")
    axes[1].set_xlabel("Residual")
    axes[1].set_ylabel("Density")

    fig.suptitle("ARIMA Residual Diagnostics", fontsize=16, fontweight="bold")
    savefig("06_arima_residual_diagnostics.png")

    return {
        "arima_order": str(order),
        "lb_stat": lb_stat,
        "lb_pvalue": lb_pval,
    }


# ===================================================================
# Figure 7 — ARIMA rolling forecast vs actual (last 3 days)
# ===================================================================
def fig_07_arima_rolling(train: pd.Series, test: pd.Series) -> np.ndarray | None:
    try:
        preds, fitted, test_last = _arima_rolling_last3(train, test)
    except Exception:
        # If ARIMA fails, plot a placeholder
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.text(0.5, 0.5, "ARIMA rolling forecast failed",
                ha="center", va="center", fontsize=18)
        savefig("07_arima_rolling_forecast.png")
        return None

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(test_last.index, test_last.values, label="Actual", color="#101817", linewidth=0.7)
    ax.plot(test_last.index, preds, label="ARIMA forecast", color=SECONDARY, linewidth=0.7, alpha=0.85)
    ax.set_title("ARIMA Rolling One-step Forecast vs Actual (Last 1 Day)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flow (vehicles / 5 min)")
    ax.legend()
    savefig("07_arima_rolling_forecast.png")
    return preds


# ===================================================================
# Figure 8 — LSTM (or placeholder) forecast
# ===================================================================
def fig_08_lstm(train: pd.Series, test: pd.Series) -> np.ndarray | None:
    """Try a simple PyTorch LSTM; fall back to placeholder if unavailable."""
    lstm_preds: np.ndarray | None = None

    try:
        import torch
        import torch.nn as nn

        # ----- prepare sequences -----
        WINDOW = 12  # use past 1 hour (12 x 5 min)
        train_vals = train.values.astype(np.float32)
        test_vals = test.values.astype(np.float32)

        # Normalise using training stats
        mu, sigma = train_vals.mean(), train_vals.std()
        train_norm = (train_vals - mu) / sigma
        test_norm = (test_vals - mu) / sigma

        # Combine end of train + test for sliding windows into test
        combined = np.concatenate([train_norm[-WINDOW:], test_norm])

        X_test_list, y_test_list = [], []
        for i in range(len(test)):
            X_test_list.append(combined[i:i + WINDOW])
            y_test_list.append(combined[i + WINDOW])

        X_test_t = torch.tensor(np.array(X_test_list), dtype=torch.float32).unsqueeze(-1)
        y_test_t = torch.tensor(np.array(y_test_list), dtype=torch.float32)

        # Build training sequences
        X_tr_list, y_tr_list = [], []
        for i in range(len(train_norm) - WINDOW):
            X_tr_list.append(train_norm[i:i + WINDOW])
            y_tr_list.append(train_norm[i + WINDOW])
        X_tr_t = torch.tensor(np.array(X_tr_list), dtype=torch.float32).unsqueeze(-1)
        y_tr_t = torch.tensor(np.array(y_tr_list), dtype=torch.float32)

        # ----- model -----
        class SimpleLSTM(nn.Module):
            def __init__(self, hidden=32):
                super().__init__()
                self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, batch_first=True)
                self.fc = nn.Linear(hidden, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :]).squeeze(-1)

        torch.manual_seed(42)
        model_lstm = SimpleLSTM()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model_lstm.parameters(), lr=1e-3)

        # Train
        model_lstm.train()
        for epoch in range(10):
            perm = torch.randperm(len(X_tr_t))
            for start in range(0, len(X_tr_t), 512):
                idx = perm[start:start + 512]
                optimizer.zero_grad()
                loss = criterion(model_lstm(X_tr_t[idx]), y_tr_t[idx])
                loss.backward()
                optimizer.step()

        # Predict
        model_lstm.eval()
        with torch.no_grad():
            pred_norm = model_lstm(X_test_t).numpy()
        lstm_preds = pred_norm * sigma + mu

    except ImportError:
        pass  # PyTorch not available

    fig, ax = plt.subplots(figsize=(14, 5))
    if lstm_preds is not None:
        ax.plot(test.index, test.values, label="Actual", color="#101817", linewidth=0.7)
        ax.plot(test.index, lstm_preds, label="LSTM prediction", color="#c0392b", linewidth=0.7, alpha=0.85)
        ax.legend()
    else:
        ax.text(0.5, 0.5, "LSTM requires PyTorch",
                ha="center", va="center", fontsize=20, transform=ax.transAxes)
    ax.set_title("LSTM Prediction vs Actual (Test Set)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flow (vehicles / 5 min)")
    savefig("08_lstm_forecast.png")

    return lstm_preds


# ===================================================================
# Metrics
# ===================================================================
def _mae(y, yhat):
    return np.mean(np.abs(y - yhat))


def _rmse(y, yhat):
    return np.sqrt(np.mean((y - yhat) ** 2))


def _mape(y, yhat):
    mask = y != 0
    return np.mean(np.abs((y[mask] - yhat[mask]) / y[mask])) * 100 if mask.any() else np.nan


# ===================================================================
# Figure 9 — Model comparison bar chart
# ===================================================================
def fig_09_model_comparison(
    actual: np.ndarray,
    baseline_pred: np.ndarray,
    arima_pred: np.ndarray | None,
    lstm_pred: np.ndarray | None,
) -> pd.DataFrame:
    records = []
    for name, pred in [("Baseline", baseline_pred),
                       ("ARIMA", arima_pred),
                       ("LSTM", lstm_pred)]:
        if pred is None:
            records.append({"model": name, "MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan})
            continue
        records.append({
            "model": name,
            "MAE": _mae(actual, pred),
            "RMSE": _rmse(actual, pred),
            "MAPE": _mape(actual, pred),
        })
    comp = pd.DataFrame(records)
    comp.to_csv(RESULTS_DIR / "model_comparison.csv", index=False)

    # Bar chart
    metrics = ["MAE", "RMSE", "MAPE"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = [PRIMARY, SECONDARY, "#c0392b"]
    for i, m in enumerate(metrics):
        bars = axes[i].bar(comp["model"], comp[m], color=colors[:len(comp)], edgecolor="white")
        axes[i].set_title(m)
        axes[i].set_ylabel(m)
        for bar, val in zip(bars, comp[m]):
            if not np.isnan(val):
                axes[i].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                             f"{val:.2f}", ha="center", va="bottom", fontsize=11)

    fig.suptitle("Model Comparison", fontsize=16, fontweight="bold")
    savefig("09_model_comparison.png")
    return comp


# ===================================================================
# Figure 10 — Peak / off-peak error breakdown
# ===================================================================
def fig_10_peak_offpeak(
    test: pd.Series,
    baseline_pred: np.ndarray,
    arima_pred: np.ndarray | None,
    lstm_pred: np.ndarray | None,
) -> pd.DataFrame:
    hours = test.index.hour
    rows = []
    for period, (h0, h1) in TIME_PERIODS.items():
        mask = (hours >= h0) & (hours <= h1)
        actual_p = test.values[mask]
        for name, pred in [("Baseline", baseline_pred),
                           ("ARIMA", arima_pred),
                           ("LSTM", lstm_pred)]:
            if pred is None:
                rows.append({"period": period, "model": name, "MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan})
                continue
            pred_p = pred[mask]
            rows.append({
                "period": period,
                "model": name,
                "MAE": _mae(actual_p, pred_p),
                "RMSE": _rmse(actual_p, pred_p),
                "MAPE": _mape(actual_p, pred_p),
            })
    df_err = pd.DataFrame(rows)
    df_err.to_csv(RESULTS_DIR / "peak_offpeak_errors.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    palette = {"Baseline": PRIMARY, "ARIMA": SECONDARY, "LSTM": "#c0392b"}
    sns.barplot(data=df_err, x="period", y="MAE", hue="model", palette=palette, ax=ax)
    ax.set_title("MAE by Time Period and Model")
    ax.set_xlabel("")
    ax.set_ylabel("MAE (vehicles / 5 min)")
    ax.legend(title="Model")
    plt.xticks(rotation=25)
    savefig("10_peak_offpeak_errors.png")
    return df_err


# ===================================================================
# DTW helpers
# ===================================================================
def _dtw_distance(s1: np.ndarray, s2: np.ndarray) -> float:
    """Simple DTW distance between two 1-D sequences."""
    n, m = len(s1), len(s2)
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(s1[i - 1] - s2[j - 1])
            dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])
    return dtw[n, m]


# ===================================================================
# Figure 11 — DTW distance heatmap
# ===================================================================
def fig_11_dtw_matrix(df: pd.DataFrame) -> pd.DataFrame:
    detectors = sorted(df["detector_id"].unique())
    # Compute average daily curve for each detector
    daily_curves: dict[str, np.ndarray] = {}
    for det in detectors:
        sub = df[df["detector_id"] == det].copy()
        sub["time_of_day"] = sub["timestamp"].dt.hour + sub["timestamp"].dt.minute / 60
        curve = sub.groupby("time_of_day")["flow"].mean().values
        daily_curves[det] = curve

    # Down-sample to hourly for DTW (speed up)
    def _hourly_avg(arr: np.ndarray) -> np.ndarray:
        # arr has 288 values (one per 5 min), average in groups of 12
        return arr[: len(arr) - len(arr) % 12].reshape(-1, 12).mean(axis=1)

    n = len(detectors)
    dist_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                dist_mat[i, j] = 0.0
            elif i < j:
                d = _dtw_distance(_hourly_avg(daily_curves[detectors[i]]),
                                  _hourly_avg(daily_curves[detectors[j]]))
                dist_mat[i, j] = d
                dist_mat[j, i] = d

    fig, ax = plt.subplots(figsize=(7, 6))
    labels = [d.replace("detector_", "D") for d in detectors]
    sns.heatmap(dist_mat, annot=True, fmt=".1f", cmap="YlGnBu",
                xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_title("DTW Distance Matrix Between Detectors")
    savefig("11_dtw_distance_matrix.png")

    # Build cluster summary
    cluster_rows = []
    for i, det in enumerate(detectors):
        row = {"detector_id": det}
        for j, det2 in enumerate(detectors):
            row[f"dist_{det2}"] = dist_mat[i, j]
        # Simple assignment: cluster by nearest centroid (just 2 clusters for 3 detectors)
        row["cluster"] = int(i)  # placeholder — with 3 detectors assign each to own
        cluster_rows.append(row)
    dtw_summary = pd.DataFrame(cluster_rows)
    return dtw_summary, dist_mat


# ===================================================================
# Figure 12 — Overlaid daily curves by DTW cluster
# ===================================================================
def fig_12_dtw_daily(df: pd.DataFrame, dtw_summary: pd.DataFrame, dist_mat: np.ndarray) -> None:
    detectors = sorted(df["detector_id"].unique())

    # Simple clustering: pair the two closest detectors, leave the third alone
    n = len(detectors)
    min_dist, best_i, best_j = np.inf, 0, 1
    for i in range(n):
        for j in range(i + 1, n):
            if dist_mat[i, j] < min_dist:
                min_dist, best_i, best_j = dist_mat[i, j], i, j

    # Assign cluster labels
    cluster_map = {}
    for idx, det in enumerate(detectors):
        if idx == best_i or idx == best_j:
            cluster_map[det] = 0
        else:
            cluster_map[det] = 1
    # If all in same cluster (n<=2), everyone cluster 0
    if n <= 2:
        cluster_map = {d: 0 for d in detectors}

    # Update dtw_summary
    dtw_summary["cluster"] = dtw_summary["detector_id"].map(cluster_map)
    dtw_summary.to_csv(RESULTS_DIR / "dtw_cluster_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 5))
    palette = [PRIMARY, SECONDARY, "#c0392b"]
    for det in detectors:
        sub = df[df["detector_id"] == det].copy()
        sub["time_of_day"] = sub["timestamp"].dt.hour + sub["timestamp"].dt.minute / 60
        daily = sub.groupby("time_of_day")["flow"].mean()
        c = cluster_map[det]
        label = f"{det.replace('detector_', 'D')} (cluster {c})"
        ax.plot(daily.index, daily.values, label=label, color=palette[c % len(palette)], linewidth=2)

    ax.set_title("Daily Flow Curves by DTW Cluster")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Mean flow (vehicles / 5 min)")
    ax.set_xticks(range(0, 25, 2))
    ax.legend()
    savefig("12_dtw_daily_patterns.png")


# ===================================================================
# Main
# ===================================================================
def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data ...")
    df = load_data()
    print(f"  Records: {len(df)}  Detectors: {df['detector_id'].unique().tolist()}")
    print(f"  Range: {df['timestamp'].min()} ~ {df['timestamp'].max()}")

    # ------ Figures 1-4 ------
    print("[1/12] 7-day flow time series ...")
    fig_01_7day_flow(df)

    print("[2/12] Daily profile weekday vs weekend ...")
    fig_02_daily_profile(df)

    print("[3/12] Flow heatmap ...")
    fig_03_heatmap(df)

    print("[4/12] ACF / PACF ...")
    fig_04_acf_pacf(df)

    # ------ ADF ------
    print("[5/12] ADF before / after ...")
    adf_info = fig_05_adf(df)

    # ------ Train / test split ------
    print("Splitting train (3 wk) / test (1 wk) ...")
    train, test = _train_test_split(df)

    # ------ ARIMA residual diagnostics ------
    print("[6/12] ARIMA residual diagnostics ...")
    arima_diag = fig_06_arima_diagnostics(train, order=(1, 1, 1))

    # ------ ARIMA rolling forecast (last 3 days) ------
    print("[7/12] ARIMA rolling forecast ...")
    arima_rolling_preds = fig_07_arima_rolling(train, test)

    # ------ Full ARIMA forecast for test set (for metrics) ------
    print("Computing full ARIMA test-set forecasts ...")
    try:
        arima_test_preds, _ = _arima_forecast(train, test, order=(1, 1, 1))
    except Exception:
        arima_test_preds = None

    # ------ LSTM ------
    print("[8/12] LSTM forecast ...")
    lstm_preds = fig_08_lstm(train, test)

    # ------ Baseline ------
    print("Computing baseline (historical same-hour mean) ...")
    baseline_preds = _baseline_forecast(train, test.index)

    # ------ Model comparison ------
    print("[9/12] Model comparison ...")
    comp = fig_09_model_comparison(test.values, baseline_preds, arima_test_preds, lstm_preds)

    # ------ Peak / off-peak errors ------
    print("[10/12] Peak / off-peak errors ...")
    fig_10_peak_offpeak(test, baseline_preds, arima_test_preds, lstm_preds)

    # ------ DTW ------
    print("[11/12] DTW distance matrix ...")
    dtw_summary, dist_mat = fig_11_dtw_matrix(df)

    print("[12/12] DTW daily patterns ...")
    fig_12_dtw_daily(df, dtw_summary, dist_mat)

    # ------ Save diagnostics CSV ------
    diag = {
        "adf_statistic": adf_info["adf_stat_original"],
        "adf_pvalue": adf_info["adf_pvalue_original"],
        "adf_statistic_diff1": adf_info["adf_stat_diff1"],
        "adf_pvalue_diff1": adf_info["adf_pvalue_diff1"],
        "arima_order": arima_diag["arima_order"],
        "ljung_box_stat": arima_diag["lb_stat"],
        "ljung_box_pvalue": arima_diag["lb_pvalue"],
    }
    pd.DataFrame([diag]).to_csv(RESULTS_DIR / "arima_diagnostics.csv", index=False)

    # ------ Summary ------
    n_fig = len(list(OUT_DIR.glob("*.png")))
    n_csv = len(list(RESULTS_DIR.glob("*.csv")))
    print(f"\nDone!  {n_fig} figures in {OUT_DIR}  |  {n_csv} CSVs in {RESULTS_DIR}")


if __name__ == "__main__":
    main()
