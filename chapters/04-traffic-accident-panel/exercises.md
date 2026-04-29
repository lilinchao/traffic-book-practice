# Exercises

## Basic

1. 读取 `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`。
2. 统计每个 borough 的事故数量。
3. 将 `crash_date` 转换为月份。
4. 生成 borough-month 事故数量表。

## Advanced

1. 计算每个 borough 每月的受伤人数。
2. 比较机动车、行人、骑行者三类受伤人数。
3. 找出 `contributing_factor_vehicle_1` 中最常见的 10 类原因。
4. 构造 `high_injury_rate` 二分类变量，并解释它的含义。
5. 拟合泊松回归模型，解释一个发生率比。

## Challenge

1. 构造一个平衡面板，保证每个 borough 都有 12 个月。
2. 计算每个 borough 的月度事故环比变化。
3. 设计一个简单的事故风险指标，并解释它的局限。
4. 比较泊松回归和负二项回归的 AIC，说明为什么负二项模型可能更合适。
5. 用 `persons_killed` 拟合零膨胀模型，并说明零膨胀部分和计数部分分别回答什么问题。
