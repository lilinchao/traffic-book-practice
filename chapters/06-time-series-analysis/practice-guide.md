# 第 6 章实践讲义：交通时序数据分析

本讲义面向学生上机实践使用，不作为书籍正文。案例使用合成交通流量数据，目标是学习交通时序数据的预处理、统计分析、建模与预测全流程。

## 1. 实践目标

完成本实践后，你应该能够：

- 加载并预处理交通流量时序数据（时间解析、缺失值处理、重采样、平滑）
- 识别时序中的趋势、日/周周期性，绘制并解读 ACF/PACF 图
- 使用 ADF 检验判断时序平稳性，理解差分对平稳化的作用
- 使用 ARIMA/SARIMA 进行建模、阶数选择、残差诊断和滚动预测
- 构建 LSTM 滑动窗口数据集，按时间顺序划分训练/验证/测试集并训练
- 对比基线模型、ARIMA、LSTM 的预测性能
- 使用 DTW 衡量不同检测器日流量模式的相似性
- 按时段和预测步长分析预测误差

## 2. 数据集

本实践使用合成交通流量数据，由 `scripts/generate_synthetic_flow.py` 生成。

| 文件 | 说明 |
| --- | --- |
| `data/processed/synthetic_traffic_flow_5min.csv` | 合成 5 分钟交通流量数据（4 周） |

数据包含 3 个检测器（detector_01, detector_02, detector_03），每个检测器 4 周的 5 分钟间隔流量记录。

数据列：

| 列名 | 类型 | 说明 |
| --- | --- | --- |
| `datetime` | str | 时间戳，5 分钟间隔 |
| `detector_id` | str | 检测器编号 |
| `flow` | int | 5 分钟内通过的车辆数 |

生成数据：

```bash
python3 scripts/generate_synthetic_flow.py
```

## 3. 数据加载与预处理

### 3.1 加载数据

```python
import pandas as pd

df = pd.read_csv("../../data/processed/synthetic_traffic_flow_5min.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.set_index("datetime").sort_index()
```

### 3.2 时间解析

确认时间索引的频率：

```python
print(f"频率推断: {pd.infer_freq(df.index[:100])}")
print(f"时间范围: {df.index.min()} ~ {df.index.max()}")
print(f"总记录数: {len(df)}")
```

### 3.3 缺失值处理

检查是否存在缺失时间点：

```python
# 按检测器分组检查完整性
for det in df["detector_id"].unique():
    sub = df[df["detector_id"] == det]
    full_range = pd.date_range(sub.index.min(), sub.index.max(), freq="5min")
    missing = full_range.difference(sub.index)
    print(f"{det}: 缺失 {len(missing)} 个时间点")
```

缺失值填充策略：

- 前向填充（`ffill`）：短期缺失，用前一个有效值填充
- 线性插值（`interpolate`）：连续缺失较少时
- 同期均值填充：利用周期性，用前几周同一时刻的均值

```python
# 前向填充 + 线性插值
df["flow"] = df.groupby("detector_id")["flow"].transform(
    lambda x: x.ffill().interpolate()
)
```

### 3.4 重采样

5 分钟数据可以根据需要重采样为更粗粒度：

```python
# 小时粒度
df_hourly = df.groupby("detector_id").resample("1h")["flow"].sum()

# 日粒度
df_daily = df.groupby("detector_id").resample("1D")["flow"].sum()
```

### 3.5 异常值检测与平滑

```python
# 基于 IQR 检测异常值
def detect_outliers_iqr(series, factor=1.5):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)

# 移动平均平滑（窗口 = 12，即 1 小时）
df["flow_smooth"] = df.groupby("detector_id")["flow"].transform(
    lambda x: x.rolling(window=12, center=True, min_periods=1).mean()
)
```

## 4. 统计分析

### 4.1 趋势分析

```python
# 日均流量趋势
daily = df.groupby("detector_id").resample("1D")["flow"].sum().reset_index()
```

观察 4 周内日流量是否有上升趋势或下降趋势。合成数据中趋势较弱，真实数据中可能有明显增长或衰减。

### 4.2 日周期性

交通流量的日周期是最显著的模式：

```python
# 按时刻统计平均流量
hourly_pattern = df.groupby([df.index.hour, df.index.minute])["flow"].mean()
hourly_pattern.index = [f"{h:02d}:{m:02d}" for h, m in hourly_pattern.index]
```

典型交通流量日模式：凌晨 2-4 点最低，早高峰 7-9 点，午间平峰，晚高峰 17-19 点，夜间逐渐降低。

### 4.3 周周期性

```python
# 按星期统计日均流量
df["weekday"] = df.index.weekday
weekly_pattern = df.groupby(["weekday"])["flow"].mean()
```

工作日（周一至周五）流量明显高于周末（周六、周日），且工作日早晚高峰模式相似，周末没有明显高峰。

### 4.4 ACF 与 PACF

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

series = df[df["detector_id"] == "detector_01"]["flow"]

fig, axes = plt.subplots(2, 1, figsize=(12, 8))
plot_acf(series, lags=288, ax=axes[0])   # 288 = 1天的5分钟点数
plot_pacf(series, lags=288, ax=axes[1])
axes[0].axvline(x=288, color="red", linestyle="--", label="1天周期")
axes[0].legend()
plt.tight_layout()
plt.savefig("acf_pacf_5min.png", dpi=150)
plt.show()
```

解读要点：

- ACF 在滞后 288（1 天）、576（2 天）等处出现周期性峰值，说明存在日周期
- PACF 在前几阶迅速衰减，有助于判断 AR 阶数
- 如果 ACF 缓慢衰减，说明序列可能非平稳

## 5. 平稳性检验

### 5.1 ADF 检验

```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(series, autolag="AIC")
print(f"ADF 统计量: {result[0]:.4f}")
print(f"p 值: {result[1]:.4f}")
print(f"使用滞后: {result[2]}")
print(f"观测数: {result[3]}")
for key, val in result[4].items():
    print(f"  临界值 ({key}): {val:.4f}")
```

判断标准：

- p 值 < 0.05：拒绝单位根假设，序列平稳
- p 值 >= 0.05：不能拒绝单位根假设，序列可能非平稳

### 5.2 差分与再检验

```python
diff_series = series.diff().dropna()
result_diff = adfuller(diff_series, autolag="AIC")
print(f"一阶差分后 ADF p 值: {result_diff[1]:.4f}")
```

交通流量序列通常在差分后趋于平稳，此时 ARIMA 中的 d=1。

### 5.3 白噪声检验

```python
from statsmodels.stats.diagnostic import acorr_ljungbox

lb_result = acorr_ljungbox(diff_series, lags=[10], return_df=True)
print(lb_result)
```

如果 p 值很小，说明差分后序列仍非白噪声，存在可建模的自相关结构。

## 6. ARIMA 建模

### 6.1 阶数选择

```python
from pmdarima import auto_arima

# 使用小时粒度数据加速
series_h = df_hourly.loc["detector_01"]

model_sel = auto_arima(
    series_h,
    seasonal=True,
    m=24,               # 日周期：24 小时
    d=None,             # 自动确定差分阶数
    D=None,             # 自动确定季节差分阶数
    stepwise=True,
    suppress_warnings=True,
    trace=True,
)
print(model_sel.summary())
print(f"最优阶数: {model_sel.order}, 季节阶数: {model_sel.seasonal_order}")
```

### 6.2 模型拟合

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

order = model_sel.order
seasonal_order = model_sel.seasonal_order

model = SARIMAX(
    train_series,
    order=order,
    seasonal_order=seasonal_order,
    enforce_stationarity=False,
    enforce_invertibility=False,
)
result = model.fit(disp=False)
print(result.summary())
```

### 6.3 残差诊断

```python
# Ljung-Box 检验
lb = acorr_ljungbox(result.resid, lags=[10, 20], return_df=True)
print("残差 Ljung-Box 检验:")
print(lb)

# 残差 ACF 图
fig = result.plot_diagnostics(figsize=(12, 8))
plt.tight_layout()
plt.savefig("arima_residual_diagnostics.png", dpi=150)
plt.show()
```

好的残差应近似白噪声：ACF 几乎全部在置信区间内，Ljung-Box 检验 p 值较大。

### 6.4 滚动预测

```python
history = list(train_series)
predictions = []

for t in range(len(test_series)):
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
```

注意：滚动预测每次重新拟合模型，计算量较大。实际中可每隔若干步重新拟合。

## 7. LSTM 建模

### 7.1 滑动窗口构建

```python
import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader

def create_sliding_windows(series, window_size=12, horizon=1):
    """将时序数据转为 (X, y) 滑动窗口对。

    Args:
        series: 1-D 数组或 Series
        window_size: 输入窗口长度
        horizon: 预测步长

    Returns:
        X: (N, window_size)
        y: (N, horizon)
    """
    values = series.values if hasattr(series, "values") else np.array(series)
    X, y = [], []
    for i in range(len(values) - window_size - horizon + 1):
        X.append(values[i : i + window_size])
        y.append(values[i + window_size : i + window_size + horizon])
    return np.array(X), np.array(y)
```

### 7.2 数据划分（严格按时间顺序）

```python
n = len(X)
train_end = int(n * 0.7)
val_end = int(n * 0.8)

X_train, y_train = X[:train_end], y[:train_end]
X_val, y_val = X[train_end:val_end], y[train_end:val_end]
X_test, y_test = X[val_end:], y[val_end:]
```

重要：时序数据不能随机划分，必须按时间顺序划分，否则会造成数据泄露。

### 7.3 标准化

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# y 也需要对应标准化
y_scaler = StandardScaler()
y_train_scaled = y_scaler.fit_transform(y_train)
y_val_scaled = y_scaler.transform(y_val)
y_test_scaled = y_scaler.transform(y_test)
```

### 7.4 LSTM 模型

```python
import torch.nn as nn

class TrafficLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # x: (batch, window_size)
        x = x.unsqueeze(-1)  # (batch, window_size, 1)
        out, _ = self.lstm(x)  # (batch, window_size, hidden_size)
        out = out[:, -1, :]    # 取最后时刻
        out = self.fc(out)     # (batch, output_size)
        return out
```

### 7.5 训练

```python
model = TrafficLSTM(input_size=1, hidden_size=64, num_layers=2, output_size=horizon)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

train_ds = TensorDataset(
    torch.FloatTensor(X_train_scaled),
    torch.FloatTensor(y_train_scaled),
)
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)

for epoch in range(50):
    model.train()
    total_loss = 0
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        pred = model(X_batch)
        loss = criterion(pred, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    if (epoch + 1) % 10 == 0:
        model.eval()
        with torch.no_grad():
            val_pred = model(torch.FloatTensor(X_val_scaled))
            val_loss = criterion(val_pred, torch.FloatTensor(y_val_scaled))
        print(f"Epoch {epoch+1}: train_loss={total_loss/len(train_loader):.4f}, val_loss={val_loss:.4f}")
```

### 7.6 预测与反标准化

```python
model.eval()
with torch.no_grad():
    y_pred_scaled = model(torch.FloatTensor(X_test_scaled)).numpy()

y_pred = y_scaler.inverse_transform(y_pred_scaled)
y_true = y_scaler.inverse_transform(y_test_scaled)
```

## 8. 模型对比

### 8.1 基线模型

```python
# 历史同期均值：用训练集中同一时刻的均值作为预测
train_series_h = train_series  # 小时粒度
baseline_pred = train_series_h.groupby(train_series_h.index.hour).mean()
```

### 8.2 误差指标

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

def mape(y_true, y_pred):
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

rmse = np.sqrt(mean_squared_error(y_true, y_pred))
mae = mean_absolute_error(y_true, y_pred)
mape_val = mape(y_true, y_pred)
```

### 8.3 分时段误差分析

```python
# 高峰 / 平峰分组
test_index = test_series.index[len(train_series) + len(val_series):]
peak_hours = [7, 8, 17, 18]  # 早高峰 7-9, 晚高峰 17-19
is_peak = np.isin(test_index.hour, peak_hours)

rmse_peak = np.sqrt(mean_squared_error(y_true[is_peak], y_pred[is_peak]))
rmse_off = np.sqrt(mean_squared_error(y_true[~is_peak], y_pred[~is_peak]))
print(f"高峰 RMSE: {rmse_peak:.2f}, 平峰 RMSE: {rmse_off:.2f}")
```

## 9. DTW 模式相似性

### 9.1 提取日流量模式

```python
# 提取每个检测器的典型日曲线
def get_daily_pattern(df, detector_id):
    sub = df[df["detector_id"] == detector_id]
    # 取所有工作日的平均日曲线
    sub = sub[sub.index.weekday < 5]
    pattern = sub.groupby([sub.index.hour, sub.index.minute])["flow"].mean()
    return pattern.values

p1 = get_daily_pattern(df, "detector_01")
p2 = get_daily_pattern(df, "detector_02")
p3 = get_daily_pattern(df, "detector_03")
```

### 9.2 DTW 距离

```python
from dtaidistance import dtw

dtw_dist_12 = dtw.distance(p1, p2)
dtw_dist_13 = dtw.distance(p1, p3)
eucl_dist_12 = np.linalg.norm(p1 - p2)
eucl_dist_13 = np.linalg.norm(p1 - p3)

print(f"DTW(1,2)={dtw_dist_12:.2f}, 欧氏(1,2)={eucl_dist_12:.2f}")
print(f"DTW(1,3)={dtw_dist_13:.2f}, 欧氏(1,3)={eucl_dist_13:.2f}")
```

### 9.3 DTW 与欧氏距离的差异

DTW 允许时间轴的弹性伸缩，因此：

- 当两条曲线形状相似但存在时间偏移时，DTW 距离小于欧氏距离
- 当曲线完美对齐时，DTW 距离约等于欧氏距离
- 交通场景中，早高峰可能在不同检测器上有 10-30 分钟的偏移，DTW 更能反映模式相似性

## 10. 预测步长与误差

```python
horizons = [1, 3, 6]
results = []

for h in horizons:
    X_h, y_h = create_sliding_windows(series_h, window_size=12, horizon=h)
    # ... 划分、训练、预测 ...
    rmse_h = np.sqrt(mean_squared_error(y_true_h, y_pred_h))
    results.append({"horizon": h, "rmse": rmse_h})

pd.DataFrame(results).plot(x="horizon", y="rmse", marker="o")
plt.xlabel("预测步长（小时）")
plt.ylabel("RMSE")
plt.title("预测步长与误差关系")
plt.savefig("horizon_error_curve.png", dpi=150)
```

一般规律：预测步长越长，误差越大。短期（1-3 步）预测通常可靠，超过 6 步后误差显著增长。

## 11. 学生任务

### 基础任务

1. 读取合成交通流量数据，解析时间索引，绘制 7 天流量图并标注高峰时段。
2. 按 1 小时和 1 天重采样，比较不同粒度下的趋势与波动。
3. 绘制 ACF/PACF 图，标注日周期位置并解释周期性振荡。
4. 做 ADF 检验，对原始序列和一阶差分序列分别检验。

### 进阶任务

1. 使用 auto_arima 选择阶数，手动拟合 SARIMA 模型并比较 AIC。
2. 对 ARIMA 残差做 Ljung-Box 检验和白噪声检验。
3. 构建 LSTM 滑动窗口数据集，按时间顺序划分并训练。
4. 实现滚动预测并比较多步预测误差。

### 挑战任务

1. 三模型对比实验，按高峰/平峰分组分析误差。
2. DTW 比较检测器日模式相似性，与欧氏距离对比。
3. 不同预测步长实验，绘制步长-误差曲线。
