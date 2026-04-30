# 编程实践基础 — 实践指南

本文档为第二章编程实践提供完整的操作指南，涵盖数据库操作、Python 数据处理、数据可视化三大模块，并列出常见陷阱与最佳实践。

---

## 一、SQLite 交通数据库搭建

### 1.1 数据库表结构设计

本章使用 NYC Traffic Volume Counts 数据集（`data/raw/nyc_traffic_volume_counts_sample.csv`），设计如下三张表：

**road_segment（路段表）**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| segment_id | INTEGER PRIMARY KEY | 路段编号 |
| roadway_name | TEXT | 道路名称 |
| from_street | TEXT | 起点街道 |
| to_street | TEXT | 终点街道 |
| direction | TEXT | 行驶方向 |

**detector（检测器表）**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| detector_id | INTEGER PRIMARY KEY AUTOINCREMENT | 检测器编号 |
| segment_id | INTEGER | 所属路段 |
| install_date | TEXT | 安装日期 |
| status | TEXT | 状态（active / inactive） |

**traffic_flow（流量表）**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| flow_id | INTEGER PRIMARY KEY AUTOINCREMENT | 记录编号 |
| segment_id | INTEGER | 路段编号 |
| date | TEXT | 日期 |
| hour | INTEGER | 小时（0-23） |
| volume | INTEGER | 流量 |

### 1.2 创建数据库与建表

```python
import sqlite3
import pandas as pd

DB_PATH = "traffic.db"

def create_database(db_path: str = DB_PATH) -> sqlite3.Connection:
    """创建数据库连接并建表。"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS road_segment (
            segment_id INTEGER PRIMARY KEY,
            roadway_name TEXT,
            from_street TEXT,
            to_street TEXT,
            direction TEXT
        );

        CREATE TABLE IF NOT EXISTS detector (
            detector_id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_id INTEGER,
            install_date TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (segment_id) REFERENCES road_segment(segment_id)
        );

        CREATE TABLE IF NOT EXISTS traffic_flow (
            flow_id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_id INTEGER,
            date TEXT,
            hour INTEGER,
            volume INTEGER,
            FOREIGN KEY (segment_id) REFERENCES road_segment(segment_id)
        );
    """)

    conn.commit()
    return conn
```

### 1.3 从 CSV 导入数据

原始数据为宽表格式（每小时一列），需要先转换为长表再插入：

```python
# 小时列名映射
HOUR_COLUMNS = {
    "_12_00_1_00_am": 0, "_1_00_2_00am": 1, "_2_00_3_00am": 2,
    "_3_00_4_00am": 3, "_4_00_5_00am": 4, "_5_00_6_00am": 5,
    "_6_00_7_00am": 6, "_7_00_8_00am": 7, "_8_00_9_00am": 8,
    "_9_00_10_00am": 9, "_10_00_11_00am": 10, "_11_00_12_00pm": 11,
    "_12_00_1_00pm": 12, "_1_00_2_00pm": 13, "_2_00_3_00pm": 14,
    "_3_00_4_00pm": 15, "_4_00_5_00pm": 16, "_5_00_6_00pm": 17,
    "_6_00_7_00pm": 18, "_7_00_8_00pm": 19, "_8_00_9_00pm": 20,
    "_9_00_10_00pm": 21, "_10_00_11_00pm": 22, "_11_00_12_00am": 23,
}
```

导入步骤：

1. 读取 CSV
2. 提取不重复路段信息插入 `road_segment`
3. 用 `pd.melt()` 将宽表转长表
4. 批量插入 `traffic_flow`

### 1.4 常用 SQL 操作示例

```sql
-- 查询某路段全天流量
SELECT hour, SUM(volume) AS total_volume
FROM traffic_flow
WHERE segment_id = 15540 AND date = '2012-01-09'
GROUP BY hour
ORDER BY hour;

-- 早高峰流量排名
SELECT rs.roadway_name, AVG(tf.volume) AS avg_am_peak
FROM traffic_flow tf
JOIN road_segment rs ON tf.segment_id = rs.segment_id
WHERE tf.hour BETWEEN 7 AND 9
GROUP BY rs.roadway_name
HAVING avg_am_peak > 100
ORDER BY avg_am_peak DESC;

-- 流量最高的 5 天
SELECT date, SUM(volume) AS daily_total
FROM traffic_flow
GROUP BY date
ORDER BY daily_total DESC
LIMIT 5;
```

---

## 二、Python 数据处理工作流

### 2.1 标准流程：读取 → 清洗 → 变换 → 聚合 → 可视化

```
读取 CSV ──> 解析时间 ──> 处理缺失值 ──> 宽表转长表
    │                                          │
    │               列重命名 <─────────────────┘
    │                  │
    v                  v
  类型转换         特征提取（小时/星期/月份）
    │                  │
    └──────┬───────────┘
           v
      分组聚合（groupby / resample）
           │
           v
       可视化输出
```

### 2.2 读取数据

```python
df = pd.read_csv("../../data/raw/nyc_traffic_volume_counts_sample.csv")
```

### 2.3 时间解析

原始数据日期格式为 `2012-01-09T00:00:00.000`，需要正确解析：

```python
df["date"] = pd.to_datetime(df["date"], format="ISO8601").dt.date
# 或更精细地保留时间信息：
df["date"] = pd.to_datetime(df["date"], format="mixed")
```

### 2.4 宽表转长表

```python
hour_cols = list(HOUR_COLUMNS.keys())
df_long = df.melt(
    id_vars=["id", "segmentid", "roadway_name", "from", "to", "direction", "date"],
    value_vars=hour_cols,
    var_name="hour_col",
    value_name="volume",
)
df_long["hour"] = df_long["hour_col"].map(HOUR_COLUMNS)
df_long.drop(columns=["hour_col"], inplace=True)
```

### 2.5 分组聚合

```python
# 按路段计算日均流量
daily_avg = df_long.groupby("segmentid")["volume"].mean()

# 按路段 + 小时计算平均小时流量
hourly_profile = df_long.groupby(["segmentid", "hour"])["volume"].mean().unstack()
```

### 2.6 时间序列重采样

使用 Chicago CTA 数据演示：

```python
cta = pd.read_csv("../../data/raw/chicago_cta_daily_boarding_sample.csv",
                   parse_dates=["service_date"], index_col="service_date")

# 周均客流
weekly = cta["total_rides"].resample("W").mean()

# 月度客流总和
monthly = cta["total_rides"].resample("ME").sum()

# 7 日滚动平均
cta["rolling_7d"] = cta["total_rides"].rolling(window=7, center=False).mean()
```

---

## 三、数据可视化

### 3.1 图表选择指南

| 分析目标 | 推荐图表 | 适用数据 |
| --- | --- | --- |
| 展示流量随时间变化 | 折线图 / 时间序列图 | 时序数据 |
| 比较不同组别分布 | 箱线图 / 小提琴图 | 分组数值数据 |
| 展示二维密度分布 | 热力图 | 路段 x 时段矩阵 |
| 显示空间分布 | 散点图 / 热力图 | 经纬度坐标 |
| 比较分类汇总 | 柱状图 | 分类聚合结果 |

### 3.2 时间序列图

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 4))
cta["total_rides"].plot(ax=ax, alpha=0.3, label="日客流")
cta["rolling_7d"].plot(ax=ax, linewidth=2, label="7 日均线")
ax.set_title("芝加哥 CTA 日客流时间序列")
ax.set_xlabel("日期")
ax.set_ylabel("客流量")
ax.legend()
plt.tight_layout()
plt.savefig("cta_daily_rides.png", dpi=150)
plt.show()
```

### 3.3 箱线图

```python
import seaborn as sns

crash_panel = pd.read_csv("../../data/processed/nyc_crash_borough_month_panel_2023.csv")
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=crash_panel, x="borough", y="crashes", ax=ax)
ax.set_title("纽约各行政区月度事故数量分布")
ax.set_xlabel("行政区")
ax.set_ylabel("事故数量")
plt.tight_layout()
plt.savefig("nyc_crash_borough_boxplot.png", dpi=150)
plt.show()
```

### 3.4 热力图

```python
# 路段 x 小时流量热力图
fig, ax = plt.subplots(figsize=(14, 8))
# 选取记录数前 20 的路段
top_segments = df_long["segmentid"].value_counts().head(20).index
heat_data = df_long[df_long["segmentid"].isin(top_segments)] \
    .groupby(["segmentid", "hour"])["volume"].mean().unstack()
sns.heatmap(heat_data, cmap="YlOrRd", ax=ax, linewidths=0.5)
ax.set_title("Top 20 路段 24 小时平均流量热力图")
ax.set_xlabel("小时")
ax.set_ylabel("路段 ID")
plt.tight_layout()
plt.savefig("traffic_flow_heatmap.png", dpi=150)
plt.show()
```

---

## 四、常见陷阱与最佳实践

### 4.1 时间解析陷阱

| 问题 | 说明 | 解决方案 |
| --- | --- | --- |
| 格式不一致 | 同一列中混合 `2023-01-01` 和 `01/01/2023` | 使用 `format="mixed"` 或 `pd.to_datetime(..., dayfirst=False)` |
| 时区问题 | 不同数据源时区不同 | 统一转为 UTC 或本地时区：`dt.tz_localize().tz_convert()` |
| ISO 8601 带毫秒 | `2012-01-09T00:00:00.000` | `format="ISO8601"` 或 `format="mixed"` |

### 4.2 缺失值 vs 零值

**这是交通数据中最常见的陷阱之一。** 在原始流量数据中：

- **零值**：检测器正常工作，该时段确实无车通过（如凌晨 3 点的郊区道路）
- **缺失值**：检测器故障、通信中断，实际流量未知

错误处理方式：

```python
# 错误：将所有缺失值填充为 0
df.fillna(0)  # 这会把检测器故障伪装成零流量！
```

正确处理方式：

```python
# 区分处理
# 先检查数据来源文档，确认缺失值含义
# 如果确实表示"未采集"，可以：
# 1. 标记缺失
df["volume"] = df["volume"].replace(0, np.nan)  # 如果确认某些 0 值实际为缺失
# 2. 插值
df["volume"] = df["volume"].interpolate(method="time")
# 3. 在聚合时排除
df.groupby("segmentid")["volume"].mean()  # NaN 自动被跳过
```

### 4.3 时间序列数据泄漏

构建预测模型时，**必须严格按时间顺序划分数据**：

```python
# 正确：时间顺序划分
train = df.loc[df["date"] < "2023-07-01"]
test = df.loc[df["date"] >= "2023-07-01"]

# 错误：随机划分（会导致数据泄漏）
from sklearn.model_selection import train_test_split
train, test = train_test_split(df, test_size=0.2, random_state=42)  # 禁止！
```

滚动统计特征中的泄漏风险：

```python
# 错误：center=True 会使用未来数据
df["rolling_mean"] = df["volume"].rolling(window=7, center=True).mean()

# 正确：只使用历史数据
df["rolling_mean"] = df["volume"].rolling(window=7, center=False).mean()
```

### 4.4 其他注意事项

- **SQLite 并发**：SQLite 不支持高并发写入，适合单机教学场景；生产环境请使用 PostgreSQL / MySQL
- **内存管理**：大文件不要一次性 `read_csv`，使用 `chunksize` 参数分块读取
- **中文显示**：Matplotlib 默认不支持中文，需设置字体：

```python
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
```

- **编码问题**：CSV 文件读取时遇到编码错误，尝试 `encoding="utf-8"` 或 `encoding="latin1"`
