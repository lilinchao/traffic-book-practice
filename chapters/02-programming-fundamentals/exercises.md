# Exercises

## 基础

1. **创建交通数据库**：使用 SQLite 创建 `traffic.db`，包含 `road_segment`（路段信息）、`detector`（检测器信息）和 `traffic_flow`（交通流量）三张表，并从 `data/raw/nyc_traffic_volume_counts_sample.csv` 导入数据。

2. **基本 SQL 查询**：编写 SQL 语句完成以下操作：
   - 查询某条路段（如 segmentid = 15540）的所有流量记录
   - 查询 2015 年之后的流量记录（按日期筛选）
   - 统计每个路段的记录条数

3. **Pandas 数据读取与清洗**：读取 `data/raw/nyc_traffic_volume_counts_sample.csv`，完成以下操作：
   - 将日期列解析为 `datetime` 类型
   - 将小时流量列（如 `_12_00_1_00_am`）重命名为更可读的格式（如 `hour_00`）
   - 检查并处理缺失值，区分真正的缺失值与零流量

4. **基础可视化**：使用 Matplotlib 绘制某路段一天的 24 小时流量曲线图，标注早晚高峰。

## 进阶

1. **多表连接与聚合查询**：在 SQLite 中完成以下操作：
   - 使用 JOIN 连接 `road_segment` 和 `traffic_flow` 表，查询每条路段名称对应的平均流量
   - 使用 GROUP BY + HAVING 筛选出平均早高峰流量（7:00-9:00）超过 100 的路段
   - 使用子查询找出流量最大的前 5 天

2. **数据变换与分组聚合**：对交通流量数据完成以下操作：
   - 将宽表（每小时一列）转换为长表（`timestamp` + `volume`）
   - 按路段分组，计算每条路段的日均流量、早晚高峰流量比
   - 按星期分组，比较工作日与周末的流量分布差异

3. **时间序列重采样**：读取 `data/raw/chicago_cta_daily_boarding_sample.csv`，完成：
   - 将 `service_date` 设为索引
   - 按周重采样，计算周均客流
   - 按月重采样，计算月度客流总和
   - 使用滚动窗口（7 日）计算移动平均，平滑日客流曲线

4. **多图可视化**：使用 Seaborn 绘制以下图表：
   - 各行政区事故数量箱线图（基于 `data/processed/nyc_crash_borough_month_panel_2023.csv`）
   - 24 小时流量热力图（行 = 路段，列 = 小时）
   - 工作日与周末客流对比的 violin plot

## 挑战

1. **完整数据库 CRUD 应用**：编写一个 Python 类 `TrafficDB`，封装以下功能：
   - `__init__`：连接数据库，若不存在则建表并导入数据
   - `insert_flow`：插入单条流量记录
   - `update_flow`：更新指定记录的流量值
   - `delete_flow`：删除指定日期的记录
   - `query_by_segment`：按路段查询，支持日期范围与时间段筛选
   - `aggregate_report`：生成路段级聚合报告（日均流量、峰值时段、变异系数）
   - 使用事务确保操作的原子性
   - 使用参数化查询防止 SQL 注入

2. **交通流量 EDA 完整流程**：对 `nyc_traffic_volume_counts_sample.csv` 完成端到端探索性分析：
   - 数据质量评估：缺失率、异常值检测（IQR / Z-score）、重复记录检查
   - 时间特征工程：提取小时、星期、月份、是否节假日等特征
   - 时空模式发现：不同路段的流量模式聚类（使用简单 K-Means）
   - 可视化报告：生成包含至少 6 张图的综合分析报告
   - 将分析结论写入 Markdown 文件

3. **时间序列数据泄漏检验**：构建一个交通流量预测的特征矩阵，要求：
   - 使用 `chicago_cta_daily_boarding_sample.csv`，以 7 天历史客流预测下一天客流
   - 构造滑动窗口特征（lag_1, lag_7, rolling_mean_7, rolling_std_7）
   - 严格按时间顺序划分训练集/测试集（禁止随机划分）
   - 检验特征中是否存在未来信息泄漏（如滚动统计使用了未来数据）
   - 对比正确划分与随机划分的模型表现差异，说明数据泄漏的影响

4. **空间可视化实践**：基于 `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`，完成：
   - 提取经纬度，去除缺失坐标
   - 使用 GeoPandas 将事故点映射为地理散点图
   - 按行政区绘制事故密度等值线/热力图
   - 保存为 GeoJSON 格式供后续章节使用
