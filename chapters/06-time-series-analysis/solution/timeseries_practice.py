"""
第 6 章 交通时序数据分析 - 完整方案
=====================================

本文件实现完整的交通时序分析流程：
  1. 数据加载与预处理（时间解析、缺失值、重采样、平滑）
  2. 统计分析（趋势、日/周周期性、ACF/PACF）
  3. 平稳性检验（ADF、差分、白噪声检验）
  4. ARIMA 建模（阶数选择、拟合、残差诊断、滚动预测）
  5. LSTM 建模（滑动窗口、时间顺序划分、训练、预测）
  6. 模型对比（基线 vs ARIMA vs LSTM）
  7. DTW 模式相似性
  8. 分时段与多步长误差分析

运行前请确保已生成合成数据：
    python scripts/generate_synthetic_flow.py

依赖：
    pip install pandas numpy matplotlib statsmodels pmdarima scikit-learn torch dtaidistance
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# ============================================================
# 0. 配置
# ============================================================
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

DATA_PATH = "../../data/processed/synthetic_traffic_flow_5min.csv"
DETECTOR = "detector_01"
OUTPUT_DIR = "."


# ============================================================
# 1. 数据加载与预处理
# ============================================================
def load_data(path=DATA_PATH):
    """加载合成交通流量数据并预处理。"""
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def check_missing(df, detector=DETECTOR):
    """检查指定检测器的缺失时间点。"""
    sub = df[df["detector_id"] == detector]
    full_range = pd.date_range(sub.index.min(), sub.index.max(), freq="5min")
    missing = full_range.difference(sub.index)
    print(f"{detector}: 总记录 {len(sub)}, 缺失时间点 {len(missing)}")
    return missing


def fill_missing(df):
    """缺失值处理：前向填充 + 线性插值。"""
    df = df.copy()
    df["flow"] = df.groupby("detector_id")["flow"].transform(
        lambda x: x.ffill().interpolate()
    )
    return df


def detect_outliers_iqr(series, factor=1.5):
    """基于 IQR 检测异常值。"""
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def resample_flow(df, freq="1h"):
    """按检测器重采样流量。"""
    return df.groupby("detector_id").resample(freq)["flow"].sum().reset_index()


def smooth_flow(df, window=12):
    """移动平均平滑。"""
    df = df.copy()
    df["flow_smooth"] = df.groupby("detector_id")["flow"].transform(
        lambda x: x.rolling(window=window, center=True, min_periods=1).mean()
    )
    return df


# ============================================================
# 2. 统计分析
# ============================================================
def plot_weekly_flow(df, detector=DETECTOR):
    """绘制前 7 天交通流量时序图，标注高峰时段。"""
    sub = df[df["detector_id"] == detector]
    start = sub.index.min()
    end = start + pd.Timedelta(days=7)
    week_data = sub[sub.index < end]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(week_data.index, week_data["flow"], linewidth=0.8)

    # 标注高峰时段
    for day in pd.date_range(start.normalize(), end.normalize(), freq="1D")[:-1]:
        ax.axvspan(day + pd.Timedelta(hours=7), day + pd.Timedelta(hours=9),
                   alpha=0.15, color="red", label="早高峰" if day == start.normalize() else "")
        ax.axvspan(day + pd.Timedelta(hours=17), day + pd.Timedelta(hours=19),
                   alpha=0.15, color="orange", label="晚高峰" if day == start.normalize() else "")

    ax.set_xlabel("时间")
    ax.set_ylabel("流量（辆/5分钟）")
    ax.set_title(f"{detector} 前 7 天交通流量（标注高峰时段）")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/weekly_flow.png", dpi=150)
    plt.show()


def plot_resample_comparison(df, detector=DETECTOR):
    """对比不同重采样粒度的流量曲线。"""
    sub = df[df["detector_id"] == detector]["flow"]
    hourly = sub.resample("1h").sum()
    daily = sub.resample("1D").sum()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
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
    plt.savefig(f"{OUTPUT_DIR}/resample_comparison.png", dpi=150)
    plt.show()


def plot_daily_pattern(df, detector=DETECTOR):
    """绘制日均流量模式。"""
    sub = df[df["detector_id"] == detector]
    pattern = sub.groupby([sub.index.hour, sub.index.minute])["flow"].mean()
    time_labels = [f"{h:02d}:{m:02d}" for h, m in pattern.index]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(range(len(pattern)), pattern.values, linewidth=1.5)
    ax.set_xticks(range(0, len(pattern), 12))
    ax.set_xticklabels([time_labels[i] for i in range(0, len(pattern), 12)], rotation=45)
    ax.set_xlabel("时刻")
    ax.set_ylabel("平均流量（辆/5分钟）")
    ax.set_title(f"{detector} 日均流量模式")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/daily_pattern.png", dpi=150)
    plt.show()


def plot_weekly_pattern(df, detector=DETECTOR):
    """绘制周均流量模式。"""
    sub = df[df["detector_id"] == detector].copy()
    sub["weekday"] = sub.index.weekday
    weekly = sub.groupby("weekday")["flow"].mean()
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(7), weekly.values, color=["#4C72B0"] * 5 + ["#DD8452"] * 2)
    ax.set_xticks(range(7))
    ax.set_xticklabels(day_names)
    ax.set_ylabel("平均流量（辆/5分钟）")
    ax.set_title(f"{detector} 周均流量模式（蓝色=工作日，橙色=周末）")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/weekly_pattern.png", dpi=150)
    plt.show()


def plot_acf_pacf(df, detector=DETECTOR, lags=288):
    """绘制 ACF 和 PACF 图。"""
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

    series = df[df["detector_id"] == detector]["flow"]

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    plot_acf(series, lags=lags, ax=axes[0])
    plot_pacf(series, lags=lags, ax=axes[1])

    axes[0].axvline(x=288, color="red", linestyle="--", label="1 天周期 (lag=288)")
    axes[0].legend()
    axes[0].set_title("自相关函数 (ACF)")
    axes[1].set_title("偏自相关函数 (PACF)")

    plt.suptitle(f"{detector} ACF / PACF", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/acf_pacf.png", dpi=150)
    plt.show()


# ============================================================
# 3. 平稳性检验
# ============================================================
def adf_test(series, name="序列"):
    """ADF 检验并打印结果。"""
    from statsmodels.tsa.stattools import adfuller

    result = adfuller(series.dropna(), autolag="AIC")
    print(f"\n--- ADF 检验: {name} ---")
    print(f"  ADF 统计量: {result[0]:.4f}")
    print(f"  p 值: {result[1]:.4f}")
    print(f"  使用滞后: {result[2]}")
    print(f"  观测数: {result[3]}")
    for key, val in result[4].items():
        print(f"  临界值 ({key}): {val:.4f}")
    if result[1] < 0.05:
        print("  结论: 拒绝单位根假设，序列平稳")
    else:
        print("  结论: 不能拒绝单位根假设，序列可能非平稳")
    return result


def white_noise_test(series, lags=[10, 20], name="序列"):
    """Ljung-Box 白噪声检验。"""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    lb = acorr_ljungbox(series.dropna(), lags=lags, return_df=True)
    print(f"\n--- Ljung-Box 白噪声检验: {name} ---")
    print(lb.to_string())
    for lag in lags:
        p = lb.loc[lag, "lb_pvalue"]
        if p < 0.05:
            print(f"  滞后 {lag}: p={p:.4f} < 0.05, 序列非白噪声，存在自相关结构")
        else:
            print(f"  滞后 {lag}: p={p:.4f} >= 0.05, 可能为白噪声")
    return lb


# ============================================================
# 4. ARIMA 建模
# ============================================================
def arima_auto_select(series, seasonal=True, m=24):
    """使用 auto_arima 自动选择阶数。"""
    from pmdarima import auto_arima

    model_sel = auto_arima(
        series,
        seasonal=seasonal,
        m=m,
        d=None,
        D=None,
        stepwise=True,
        suppress_warnings=True,
        trace=True,
        max_p=5,
        max_q=5,
        max_P=3,
        max_Q=3,
    )
    print(f"\n最优阶数: {model_sel.order}")
    print(f"季节阶数: {model_sel.seasonal_order}")
    print(f"AIC: {model_sel.aic():.2f}")
    return model_sel


def fit_sarima(train_series, order, seasonal_order):
    """拟合 SARIMA 模型。"""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    model = SARIMAX(
        train_series,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    result = model.fit(disp=False)
    print(result.summary())
    return result


def residual_diagnostics(result):
    """ARIMA 残差诊断。"""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    resid = result.resid
    print("\n--- 残差诊断 ---")

    # Ljung-Box 检验
    lb = acorr_ljungbox(resid, lags=[10, 20], return_df=True)
    print("残差 Ljung-Box 检验:")
    print(lb.to_string())

    # 残差诊断图
    fig = result.plot_diagnostics(figsize=(12, 8))
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/arima_residual_diagnostics.png", dpi=150)
    plt.show()
    return lb


def arima_rolling_forecast(train_series, test_series, order, seasonal_order, step=1):
    """ARIMA 滚动预测。

    每次 forecast step 步后将真实值加入历史继续预测。
    step 参数控制每隔多少步重新拟合模型（减少计算量）。
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    history = list(train_series)
    predictions = []

    for t in range(len(test_series)):
        if t % step == 0:
            model = SARIMAX(
                history,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            result = model.fit(disp=False)

        yhat = result.forecast(steps=1)[0]
        predictions.append(yhat)
        history.append(test_series.iloc[t])

    return np.array(predictions)


# ============================================================
# 5. LSTM 建模
# ============================================================
def create_sliding_windows(series, window_size=12, horizon=1):
    """将时序数据转为滑动窗口对。

    Args:
        series: pd.Series 或 np.ndarray
        window_size: 输入窗口长度
        horizon: 预测步长

    Returns:
        X: (N, window_size)
        y: (N, horizon)
    """
    values = series.values if hasattr(series, "values") else np.array(series)
    X, y = [], []
    for i in range(len(values) - window_size - horizon + 1):
        X.append(values[i: i + window_size])
        y.append(values[i + window_size: i + window_size + horizon])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def split_time_series(X, y, train_ratio=0.7, val_ratio=0.1):
    """按时间顺序划分训练/验证/测试集。"""
    n = len(X)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    print(f"  训练集: {len(X_train)} 样本")
    print(f"  验证集: {len(X_val)} 样本")
    print(f"  测试集: {len(X_test)} 样本")
    return X_train, y_train, X_val, y_val, X_test, y_test


class TrafficLSTM:
    """基于 PyTorch 的 LSTM 交通流量预测模型。"""

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1,
                 lr=1e-3, epochs=50, batch_size=64, seed=42):
        import torch
        import torch.nn as nn

        self.torch = torch
        self.nn = nn
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.input_size = input_size
        self.output_size = output_size
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed

        # 固定随机种子
        torch.manual_seed(seed)
        np.random.seed(seed)

        # 构建模型
        self.model = self._build_model()
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def _build_model(self):
        import torch.nn as nn

        class _LSTMNet(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, output_size):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                self.fc = nn.Linear(hidden_size, output_size)

            def forward(self, x):
                x = x.unsqueeze(-1)                          # (B, T, 1)
                out, _ = self.lstm(x)                        # (B, T, H)
                out = self.fc(out[:, -1, :])                 # (B, output_size)
                return out

        return _LSTMNet(self.input_size, self.hidden_size,
                        self.num_layers, self.output_size)

    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """训练 LSTM 模型。"""
        from torch.utils.data import TensorDataset, DataLoader

        torch = self.torch

        X_t = torch.FloatTensor(X_train)
        y_t = torch.FloatTensor(y_train)
        ds = TensorDataset(X_t, y_t)
        loader = DataLoader(ds, batch_size=self.batch_size, shuffle=True)

        train_losses = []
        val_losses = []

        for epoch in range(self.epochs):
            self.model.train()
            epoch_loss = 0
            for X_batch, y_batch in loader:
                self.optimizer.zero_grad()
                pred = self.model(X_batch)
                loss = self.criterion(pred, y_batch)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item() * len(X_batch)
            epoch_loss /= len(X_train)
            train_losses.append(epoch_loss)

            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    val_pred = self.model(torch.FloatTensor(X_val))
                    val_loss = self.criterion(val_pred, torch.FloatTensor(y_val)).item()
                    val_losses.append(val_loss)

            if (epoch + 1) % 10 == 0:
                msg = f"Epoch {epoch+1}/{self.epochs}: train_loss={epoch_loss:.4f}"
                if val_losses:
                    msg += f", val_loss={val_losses[-1]:.4f}"
                print(f"  {msg}")

        return train_losses, val_losses

    def predict(self, X):
        """预测。"""
        torch = self.torch
        self.model.eval()
        with torch.no_grad():
            return self.model(torch.FloatTensor(X)).numpy()


# ============================================================
# 6. 模型评估
# ============================================================
def calc_metrics(y_true, y_pred, name="模型"):
    """计算 RMSE、MAE、MAPE。"""
    mask = y_true != 0
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape_val = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else np.nan

    print(f"  {name}: RMSE={rmse:.2f}, MAE={mae:.2f}, MAPE={mape_val:.2f}%")
    return {"name": name, "rmse": rmse, "mae": mae, "mape": mape_val}


def baseline_historical_mean(train_series, test_index):
    """基线模型：历史同期均值。

    对每小时粒度数据，用训练集中同一小时的均值作为预测。
    """
    hourly_mean = train_series.groupby(train_series.index.hour).mean()
    preds = [hourly_mean[h] for h in test_index.hour]
    return np.array(preds)


def compare_models(results_list):
    """生成模型对比表。"""
    df_cmp = pd.DataFrame(results_list)
    print("\n=== 模型对比 ===")
    print(df_cmp.to_string(index=False))
    return df_cmp


# ============================================================
# 7. 分时段误差分析
# ============================================================
def error_by_period(y_true, y_pred, test_index, name="模型"):
    """按高峰/平峰分组计算误差。"""
    peak_hours = [7, 8, 17, 18]  # 早高峰 7-9, 晚高峰 17-19
    is_peak = np.isin(test_index.hour, peak_hours)

    if is_peak.sum() > 0 and (~is_peak).sum() > 0:
        rmse_peak = np.sqrt(mean_squared_error(y_true[is_peak], y_pred[is_peak]))
        rmse_off = np.sqrt(mean_squared_error(y_true[~is_peak], y_pred[~is_peak]))
        print(f"  {name} - 高峰 RMSE: {rmse_peak:.2f}, 平峰 RMSE: {rmse_off:.2f}")
        return {"name": name, "rmse_peak": rmse_peak, "rmse_offpeak": rmse_off}
    else:
        print(f"  {name} - 数据不足，无法分时段分析")
        return {"name": name, "rmse_peak": np.nan, "rmse_offpeak": np.nan}


# ============================================================
# 8. DTW 模式相似性
# ============================================================
def get_daily_pattern(df, detector_id):
    """提取工作日平均日流量曲线。"""
    sub = df[(df["detector_id"] == detector_id) & (df.index.weekday < 5)]
    pattern = sub.groupby([sub.index.hour, sub.index.minute])["flow"].mean()
    return pattern.values


def dtw_comparison(df):
    """使用 DTW 比较不同检测器的日模式相似性。"""
    try:
        from dtaidistance import dtw
        has_dtw = True
    except ImportError:
        print("[警告] dtaidistance 未安装，使用简化 DTW 实现")
        has_dtw = False

    detectors = df["detector_id"].unique()
    patterns = {d: get_daily_pattern(df, d) for d in detectors}

    print("\n=== DTW 模式相似性分析 ===")
    results = []

    for i, d1 in enumerate(detectors):
        for j, d2 in enumerate(detectors):
            if i >= j:
                continue
            p1, p2 = patterns[d1], patterns[d2]

            # 欧氏距离
            eucl = np.linalg.norm(p1 - p2)

            if has_dtw:
                dtw_dist = dtw.distance(p1, p2)
                print(f"  {d1} vs {d2}: DTW={dtw_dist:.2f}, 欧氏={eucl:.2f}, "
                      f"比值={dtw_dist/eucl:.3f}")
                results.append({
                    "pair": f"{d1} vs {d2}",
                    "dtw": dtw_dist,
                    "euclidean": eucl,
                    "ratio": dtw_dist / eucl,
                })
            else:
                # 简化实现：动态规划 DTW
                dtw_dist = _simple_dtw(p1, p2)
                print(f"  {d1} vs {d2}: DTW={dtw_dist:.2f}, 欧氏={eucl:.2f}")
                results.append({
                    "pair": f"{d1} vs {d2}",
                    "dtw": dtw_dist,
                    "euclidean": eucl,
                })

    return pd.DataFrame(results)


def _simple_dtw(s1, s2):
    """简化 DTW 实现（动态规划）。"""
    n, m = len(s1), len(s2)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (s1[i - 1] - s2[j - 1]) ** 2
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j],      # 插入
                dtw_matrix[i, j - 1],      # 删除
                dtw_matrix[i - 1, j - 1],  # 匹配
            )

    return np.sqrt(dtw_matrix[n, m])


# ============================================================
# 9. 多步长预测实验
# ============================================================
def multi_horizon_experiment(series_h, horizons=[1, 3, 6], window_size=12):
    """不同预测步长的 LSTM 实验与可视化。"""
    import torch

    results = []

    for h in horizons:
        print(f"\n--- 预测步长: {h} 小时 ---")
        X, y = create_sliding_windows(series_h, window_size=window_size, horizon=h)
        X_train, y_train, X_val, y_val, X_test, y_test = split_time_series(
            X, y, train_ratio=0.7, val_ratio=0.1
        )

        # 标准化
        x_scaler = StandardScaler()
        y_scaler = StandardScaler()
        X_train_s = x_scaler.fit_transform(X_train)
        X_val_s = x_scaler.transform(X_val)
        X_test_s = x_scaler.transform(X_test)
        y_train_s = y_scaler.fit_transform(y_train)
        y_val_s = y_scaler.transform(y_val)
        y_test_s = y_scaler.transform(y_test)

        # 训练 LSTM
        lstm = TrafficLSTM(
            input_size=1, hidden_size=64, num_layers=2, output_size=h,
            lr=1e-3, epochs=30, batch_size=64,
        )
        lstm.fit(X_train_s, y_train_s, X_val_s, y_val_s)

        # 预测
        y_pred_s = lstm.predict(X_test_s)
        y_pred = y_scaler.inverse_transform(y_pred_s)

        # 计算最后一步的 RMSE（关注最远预测）
        rmse = np.sqrt(mean_squared_error(y_test[:, -1], y_pred[:, -1]))
        results.append({"horizon": h, "rmse_last_step": rmse})
        print(f"  步长 {h}: 最远一步 RMSE={rmse:.2f}")

    # 绘制步长-误差曲线
    df_h = pd.DataFrame(results)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df_h["horizon"], df_h["rmse_last_step"], marker="o", linewidth=2)
    ax.set_xlabel("预测步长（小时）")
    ax.set_ylabel("RMSE")
    ax.set_title("预测步长与误差关系")
    ax.set_xticks(horizons)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/horizon_error_curve.png", dpi=150)
    plt.show()

    return df_h


# ============================================================
# 10. 主程序
# ============================================================
def main():
    print("=" * 60)
    print("第 6 章 交通时序数据分析 - 完整方案")
    print("=" * 60)

    # ----------------------------------------------------------
    # 1. 加载与预处理
    # ----------------------------------------------------------
    print("\n[1] 数据加载与预处理")
    df = load_data()
    print(f"数据形状: {df.shape}")
    print(f"检测器: {df['detector_id'].unique().tolist()}")
    print(f"时间范围: {df.index.min()} ~ {df.index.max()}")

    for det in df["detector_id"].unique():
        check_missing(df, det)

    df = fill_missing(df)

    # 异常值检测
    series_01 = df[df["detector_id"] == DETECTOR]["flow"]
    outliers = detect_outliers_iqr(series_01)
    print(f"\n{DETECTOR} 异常值数量: {outliers.sum()} / {len(series_01)}")

    # 平滑
    df = smooth_flow(df, window=12)

    # 小时粒度数据
    df_hourly = resample_flow(df, freq="1h")
    series_h = df_hourly[df_hourly["detector_id"] == DETECTOR].set_index("datetime")["flow"].sort_index()

    # ----------------------------------------------------------
    # 2. 统计分析
    # ----------------------------------------------------------
    print("\n[2] 统计分析")
    plot_weekly_flow(df)
    plot_resample_comparison(df)
    plot_daily_pattern(df)
    plot_weekly_pattern(df)
    plot_acf_pacf(df)

    # ----------------------------------------------------------
    # 3. 平稳性检验
    # ----------------------------------------------------------
    print("\n[3] 平稳性检验")
    series_5min = df[df["detector_id"] == DETECTOR]["flow"]
    adf_result = adf_test(series_5min, name="原始序列（5 分钟）")
    diff_series = series_5min.diff().dropna()
    adf_result_diff = adf_test(diff_series, name="一阶差分序列")
    white_noise_test(diff_series, name="一阶差分序列")

    # ----------------------------------------------------------
    # 4. ARIMA 建模
    # ----------------------------------------------------------
    print("\n[4] ARIMA 建模")
    n_total = len(series_h)
    n_train = int(n_total * 0.8)
    train_h = series_h.iloc[:n_train]
    test_h = series_h.iloc[n_train:]

    print("自动选择阶数...")
    model_sel = arima_auto_select(train_h, seasonal=True, m=24)

    order = model_sel.order
    seasonal_order = model_sel.seasonal_order

    print("\n拟合 SARIMA 模型...")
    arima_result = fit_sarima(train_h, order, seasonal_order)
    residual_diagnostics(arima_result)

    print("\nARIMA 滚动预测（每 6 步重新拟合）...")
    arima_preds = arima_rolling_forecast(
        train_h, test_h, order, seasonal_order, step=6
    )

    # ----------------------------------------------------------
    # 5. LSTM 建模
    # ----------------------------------------------------------
    print("\n[5] LSTM 建模")
    X, y = create_sliding_windows(series_h, window_size=12, horizon=1)
    X_train, y_train, X_val, y_val, X_test, y_test = split_time_series(
        X, y, train_ratio=0.7, val_ratio=0.1
    )

    # 标准化
    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    X_train_s = x_scaler.fit_transform(X_train)
    X_val_s = x_scaler.transform(X_val)
    X_test_s = x_scaler.transform(X_test)
    y_train_s = y_scaler.fit_transform(y_train)
    y_val_s = y_scaler.transform(y_val)
    y_test_s = y_scaler.transform(y_test)

    # 训练
    print("训练 LSTM...")
    lstm = TrafficLSTM(
        input_size=1, hidden_size=64, num_layers=2, output_size=1,
        lr=1e-3, epochs=50, batch_size=64,
    )
    train_losses, val_losses = lstm.fit(X_train_s, y_train_s, X_val_s, y_val_s)

    # 训练曲线
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_losses, label="训练损失")
    ax.plot(val_losses, label="验证损失")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("MSE Loss")
    ax.set_title("LSTM 训练曲线")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/lstm_training_curve.png", dpi=150)
    plt.show()

    # 预测
    y_pred_lstm_s = lstm.predict(X_test_s)
    y_pred_lstm = y_scaler.inverse_transform(y_pred_lstm_s).flatten()
    y_true_lstm = y_scaler.inverse_transform(y_test_s).flatten()

    # ----------------------------------------------------------
    # 6. 模型对比
    # ----------------------------------------------------------
    print("\n[6] 模型对比")

    # 基线：历史同期均值
    baseline_preds = baseline_historical_mean(train_h, test_h.index)
    arima_preds_trunc = arima_preds  # 已与 test_h 对齐

    # LSTM 需要与对应的时间对齐
    # 测试集的时间索引需要从 series_h 推算
    n_train_val = int(len(X) * 0.8)
    lstm_test_index = series_h.index[n_train_val + 12:]  # 偏移窗口长度
    lstm_test_index = lstm_test_index[:len(y_true_lstm)]

    # 确保长度一致
    min_len = min(len(baseline_preds), len(arima_preds), len(y_true_lstm))
    baseline_trim = baseline_preds[:min_len]
    arima_trim = arima_preds[:min_len]
    lstm_trim = y_pred_lstm[:min_len]
    y_true_trim = test_h.values[:min_len]
    test_idx_trim = test_h.index[:min_len]

    all_metrics = []
    all_metrics.append(calc_metrics(y_true_trim, baseline_trim, name="历史均值基线"))
    all_metrics.append(calc_metrics(y_true_trim, arima_trim, name="ARIMA"))
    all_metrics.append(calc_metrics(y_true_trim, lstm_trim, name="LSTM"))

    df_cmp = compare_models(all_metrics)

    # 对比图
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(test_idx_trim, y_true_trim, label="真实值", linewidth=1.0, alpha=0.8)
    ax.plot(test_idx_trim, baseline_trim, label="基线", linewidth=0.8, alpha=0.6)
    ax.plot(test_idx_trim, arima_trim, label="ARIMA", linewidth=0.8, alpha=0.8)
    ax.plot(test_idx_trim, lstm_trim, label="LSTM", linewidth=0.8, alpha=0.8)
    ax.set_xlabel("时间")
    ax.set_ylabel("流量")
    ax.set_title("模型预测对比")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/model_comparison.png", dpi=150)
    plt.show()

    # ----------------------------------------------------------
    # 7. 分时段误差分析
    # ----------------------------------------------------------
    print("\n[7] 分时段误差分析")
    period_results = []
    period_results.append(error_by_period(y_true_trim, baseline_trim, test_idx_trim, name="基线"))
    period_results.append(error_by_period(y_true_trim, arima_trim, test_idx_trim, name="ARIMA"))
    period_results.append(error_by_period(y_true_trim, lstm_trim, test_idx_trim, name="LSTM"))

    df_period = pd.DataFrame(period_results)
    print("\n=== 分时段 RMSE ===")
    print(df_period.to_string(index=False))

    # ----------------------------------------------------------
    # 8. DTW 模式相似性
    # ----------------------------------------------------------
    print("\n[8] DTW 模式相似性")
    df_dtw = dtw_comparison(df)

    # 绘制不同检测器的日模式对比
    fig, ax = plt.subplots(figsize=(14, 5))
    for det in df["detector_id"].unique():
        pattern = get_daily_pattern(df, det)
        ax.plot(range(len(pattern)), pattern, label=det, linewidth=1.2)
    ax.set_xlabel("5 分钟间隔（0-287）")
    ax.set_ylabel("平均流量")
    ax.set_title("不同检测器工作日日流量模式对比")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/daily_pattern_comparison.png", dpi=150)
    plt.show()

    # ----------------------------------------------------------
    # 9. 多步长实验
    # ----------------------------------------------------------
    print("\n[9] 多步长预测实验")
    df_horizon = multi_horizon_experiment(series_h, horizons=[1, 3, 6])

    # ----------------------------------------------------------
    # 总结
    # ----------------------------------------------------------
    print("\n" + "=" * 60)
    print("分析完成！生成的图表：")
    print("  - weekly_flow.png: 7 天流量图")
    print("  - resample_comparison.png: 重采样对比")
    print("  - daily_pattern.png: 日均流量模式")
    print("  - weekly_pattern.png: 周均流量模式")
    print("  - acf_pacf.png: ACF/PACF 图")
    print("  - arima_residual_diagnostics.png: ARIMA 残差诊断")
    print("  - lstm_training_curve.png: LSTM 训练曲线")
    print("  - model_comparison.png: 模型预测对比")
    print("  - daily_pattern_comparison.png: 检测器日模式对比")
    print("  - horizon_error_curve.png: 步长-误差曲线")
    print("=" * 60)


if __name__ == "__main__":
    main()
