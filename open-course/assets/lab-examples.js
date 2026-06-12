window.LAB_EXAMPLES = [
  {
    id: 'ch1-quality', chapter: 1, level: '入门', duration: '8分钟',
    title: '交通数据质量诊断', summary: '识别缺失、越界与重复记录。',
    goal: '建立“先检查数据、再选择模型”的分析习惯。',
    challenge: '修改速度上限和缺失值，观察质量得分变化。',
    concepts: ['数据质量', '缺失值', '异常值'],
    code: `import numpy as np

# 列依次为：速度、流量、占有率
data = np.array([
    [62, 820, 0.18], [58, 910, 0.22], [np.nan, 870, 0.20],
    [135, 760, 0.17], [42, 1250, 0.39], [42, 1250, 0.39],
    [35, 1410, 1.18], [51, 980, 0.27]
], dtype=float)

speed_limit = 120
missing = np.isnan(data).sum()
speed_error = np.sum(data[:, 0] > speed_limit)
occupancy_error = np.sum(data[:, 2] > 1)
duplicates = len(data) - len(np.unique(np.nan_to_num(data), axis=0))
total_cells = data.size
completeness = 100 * (1 - missing / total_cells)
validity = 100 * (1 - (speed_error + occupancy_error) / len(data))
uniqueness = 100 * (1 - duplicates / len(data))

print(f"缺失单元格: {missing}，重复记录: {duplicates}")
result = {
    "chart": "bar",
    "labels": ["完整性", "有效性", "唯一性"],
    "series": [{"name": "质量得分", "values": [completeness, validity, uniqueness]}],
    "metrics": {"缺失": int(missing), "越界": int(speed_error + occupancy_error), "重复": int(duplicates)}
}`
  },
  {
    id: 'ch1-method', chapter: 1, level: '入门', duration: '10分钟',
    title: '为交通问题选择方法', summary: '按解释、预测、空间和实时需求评分。',
    goal: '理解问题目标如何决定分析方法。',
    challenge: '修改 weights，让“解释”或“实时性”成为首要目标。',
    concepts: ['问题定义', '方法选择', '多准则评分'],
    code: `import numpy as np

methods = ["统计回归", "随机森林", "时序模型", "空间分析", "深度学习"]
# 每行依次表示：可解释、预测、空间、实时能力
scores = np.array([
    [5, 3, 1, 4], [3, 5, 2, 4], [3, 5, 1, 4],
    [4, 2, 5, 2], [2, 5, 3, 3]
], dtype=float)

# 场景：解释事故风险因素，同时保留一定预测能力
weights = np.array([0.45, 0.30, 0.15, 0.10])
total = scores @ weights
best = int(np.argmax(total))

print(f"推荐方法：{methods[best]}")
result = {
    "chart": "bar", "labels": methods,
    "series": [{"name": "匹配度", "values": total.tolist()}],
    "metrics": {"推荐": methods[best], "得分": round(float(total[best]), 2), "候选": len(methods)}
}`
  },
  {
    id: 'ch1-baseline', chapter: 1, level: '入门', duration: '10分钟',
    title: '复杂模型前先做基线', summary: '比较昨日同期与历史均值预测。',
    goal: '学会用简单基线判断复杂模型是否真的有增益。',
    challenge: '改变周末需求，观察哪种基线更稳健。',
    concepts: ['基线模型', 'MAE', '模型增益'],
    code: `import numpy as np

# 前7天为历史，后7天为测试周
history = np.array([102, 118, 121, 125, 132, 86, 79], dtype=float)
actual = np.array([108, 120, 124, 129, 138, 92, 82], dtype=float)
historical_mean = np.repeat(history.mean(), 7)
yesterday_pattern = history.copy()

mae_mean = np.mean(np.abs(actual - historical_mean))
mae_pattern = np.mean(np.abs(actual - yesterday_pattern))
print(f"历史均值 MAE={mae_mean:.1f}，同期模式 MAE={mae_pattern:.1f}")
result = {
    "chart": "series", "x": list(range(1, 8)),
    "series": [
        {"name": "真实需求", "values": actual.tolist()},
        {"name": "同期基线", "values": yesterday_pattern.tolist()},
        {"name": "均值基线", "values": historical_mean.tolist()}
    ],
    "metrics": {"同期MAE": round(float(mae_pattern), 1), "均值MAE": round(float(mae_mean), 1), "更优": "同期模式"}
}`
  },
  {
    id: 'ch1-leakage', chapter: 1, level: '进阶', duration: '12分钟',
    title: '识别目标信息泄漏', summary: '比较合法特征与事故后特征。',
    goal: '判断一个高精度模型是否偷看了未来信息。',
    challenge: '增大 leaked_feature 的噪声，观察虚假优势如何减弱。',
    concepts: ['信息泄漏', '时间顺序', '可信评价'],
    code: `import numpy as np

rng = np.random.default_rng(7)
n = 80
traffic = rng.normal(1000, 180, n)
rain = rng.integers(0, 2, n)
risk = 0.012 * traffic + 3.5 * rain + rng.normal(0, 2.0, n)
legal = np.column_stack([np.ones(n), traffic, rain])

# 事故发生后才产生的拥堵指标，不应作为事故预测特征
leaked_feature = risk + rng.normal(0, 0.6, n)
leaked = np.column_stack([legal, leaked_feature])
split = 60

def test_mae(x):
    beta = np.linalg.lstsq(x[:split], risk[:split], rcond=None)[0]
    prediction = x[split:] @ beta
    return float(np.mean(np.abs(risk[split:] - prediction)))

legal_mae = test_mae(legal)
leaked_mae = test_mae(leaked)
print("泄漏模型看似更准，但部署时无法获得事故后的信息。")
result = {
    "chart": "bar", "labels": ["合法特征", "泄漏特征"],
    "series": [{"name": "测试MAE", "values": [legal_mae, leaked_mae]}],
    "metrics": {"合法MAE": round(legal_mae, 2), "泄漏MAE": round(leaked_mae, 2), "结论": "拒绝泄漏"}
}`
  },
  {
    id: 'ch2-cleaning', chapter: 2, level: '入门', duration: '10分钟',
    title: '速度异常值清洗', summary: '用IQR规则识别并截尾异常速度。',
    goal: '区分设备异常与真实交通突变。',
    challenge: '将 multiplier 从1.5改为1.0或2.5。',
    concepts: ['IQR', '异常值', '截尾处理'],
    code: `import numpy as np

speed = np.array([62, 61, 59, 57, 55, 12, 54, 56, 58, 142, 60, 63], dtype=float)
multiplier = 1.5
q1, q3 = np.percentile(speed, [25, 75])
iqr = q3 - q1
lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
cleaned = np.clip(speed, lower, upper)
outliers = int(np.sum((speed < lower) | (speed > upper)))

print(f"识别出 {outliers} 个异常值，合理范围 {lower:.1f}~{upper:.1f}")
result = {
    "chart": "series", "x": list(range(len(speed))),
    "series": [{"name": "原始速度", "values": speed.tolist()}, {"name": "清洗结果", "values": cleaned.tolist()}],
    "metrics": {"异常数": outliers, "下界": round(float(lower), 1), "上界": round(float(upper), 1)}
}`
  },
  {
    id: 'ch2-aggregation', chapter: 2, level: '入门', duration: '8分钟',
    title: '交通流时间聚合', summary: '把5分钟流量聚合为15分钟流量。',
    goal: '理解求和、均值和时间粒度的交通含义。',
    challenge: '把 group_size 改为2或6，比较峰值变化。',
    concepts: ['重采样', '时间粒度', '流量聚合'],
    code: `import numpy as np

flow_5min = np.array([42, 48, 51, 58, 62, 67, 71, 76, 73, 69, 64, 58], dtype=float)
group_size = 3
usable = len(flow_5min) // group_size * group_size
flow_grouped = flow_5min[:usable].reshape(-1, group_size).sum(axis=1)
labels = [f"第{i+1}段" for i in range(len(flow_grouped))]

print(f"由 {len(flow_5min)} 个5分钟记录得到 {len(flow_grouped)} 个聚合记录")
result = {
    "chart": "bar", "labels": labels,
    "series": [{"name": "聚合交通量", "values": flow_grouped.tolist()}],
    "metrics": {"粒度": f"{group_size*5}分钟", "峰值": int(flow_grouped.max()), "总量": int(flow_grouped.sum())}
}`
  },
  {
    id: 'ch2-scaling', chapter: 2, level: '入门', duration: '10分钟',
    title: '不同量纲的标准化', summary: '把速度与流量放到可比较尺度。',
    goal: '理解标准化为何能改善距离与优化计算。',
    challenge: '加入一个极端流量值，观察Z-score的变化。',
    concepts: ['Z-score', '量纲', '特征处理'],
    code: `import numpy as np

speed = np.array([62, 58, 51, 44, 38, 35, 42, 55], dtype=float)
flow = np.array([520, 680, 910, 1220, 1450, 1510, 1280, 840], dtype=float)

def zscore(values):
    return (values - values.mean()) / values.std()

speed_z = zscore(speed)
flow_z = zscore(flow)
correlation = float(np.corrcoef(speed_z, flow_z)[0, 1])
print(f"标准化后相关系数仍为 {correlation:.3f}")
result = {
    "chart": "series", "x": list(range(1, 9)),
    "series": [{"name": "标准化速度", "values": speed_z.tolist()}, {"name": "标准化流量", "values": flow_z.tolist()}],
    "metrics": {"速度均值": round(float(speed_z.mean()), 2), "流量标准差": round(float(flow_z.std()), 2), "相关": round(correlation, 3)}
}`
  },
  {
    id: 'ch2-od', chapter: 2, level: '进阶', duration: '12分钟',
    title: '构建城市OD矩阵', summary: '把出行记录汇总为区域联系强度。',
    goal: '理解起点、终点与出行量的矩阵表达。',
    challenge: '修改 trips，找出新的最强跨区联系。',
    concepts: ['OD矩阵', '分组聚合', '热力图'],
    code: `import numpy as np

zones = ["中心区", "北区", "东区", "南区"]
trips = [
    (0, 1, 120), (0, 2, 180), (0, 3, 95), (1, 0, 140),
    (1, 2, 70), (2, 0, 210), (2, 3, 85), (3, 0, 115),
    (3, 1, 60), (2, 1, 92)
]
matrix = np.zeros((len(zones), len(zones)))
for origin, destination, count in trips:
    matrix[origin, destination] += count

masked = matrix.copy()
np.fill_diagonal(masked, -1)
origin, destination = np.unravel_index(np.argmax(masked), masked.shape)
print(f"最强联系：{zones[origin]} → {zones[destination]}")
result = {
    "chart": "heatmap", "matrix": matrix.tolist(), "rowLabels": zones, "colLabels": zones,
    "metrics": {"总出行": int(matrix.sum()), "最强OD": f"{zones[origin]}→{zones[destination]}", "流量": int(matrix[origin, destination])}
}`
  },
  {
    id: 'regression', chapter: 3, level: '进阶', duration: '15分钟',
    title: '梯度下降拟合交通需求', summary: '手工更新参数并观察损失收敛。',
    goal: '连接导数、梯度、学习率与回归模型。',
    challenge: '修改 learning_rate 和 steps，寻找稳定又快速的组合。',
    concepts: ['梯度下降', '学习率', 'MAE'],
    code: `import numpy as np

hours = np.array([6, 7, 8, 9, 10, 16, 17, 18, 19, 20], dtype=float)
demand = np.array([72, 145, 286, 230, 168, 210, 355, 430, 318, 226], dtype=float)
learning_rate = 0.08
steps = 120
x = (hours - hours.mean()) / hours.std()
y = (demand - demand.mean()) / demand.std()
w, b = 0.0, 0.0
losses = []
for step in range(steps):
    prediction = w * x + b
    error = prediction - y
    losses.append(float(np.mean(error ** 2)))
    w -= learning_rate * float(2 * np.mean(error * x))
    b -= learning_rate * float(2 * np.mean(error))
fitted = (w * x + b) * demand.std() + demand.mean()
mae = float(np.mean(np.abs(demand - fitted)))
print(f"训练 {steps} 步，最终损失 {losses[-1]:.4f}")
result = {
    "chart": "regression", "x": hours.tolist(), "y": demand.tolist(), "prediction": fitted.tolist(),
    "metrics": {"MAE": round(mae, 1), "斜率": round(w, 3), "最终损失": round(losses[-1], 4)}
}`
  },
  {
    id: 'ch3-bayes', chapter: 3, level: '进阶', duration: '12分钟',
    title: '贝叶斯更新事故风险', summary: '由先验风险和天气证据计算后验。',
    goal: '理解条件概率如何更新交通安全判断。',
    challenge: '修改雨天似然，观察后验风险是否敏感。',
    concepts: ['贝叶斯公式', '先验', '后验'],
    code: `import numpy as np

prior_accident = 0.08
p_rain_given_accident = 0.55
p_rain_given_safe = 0.18

p_rain = p_rain_given_accident * prior_accident + p_rain_given_safe * (1 - prior_accident)
posterior = p_rain_given_accident * prior_accident / p_rain
lift = posterior / prior_accident

print(f"观察到降雨后，事故风险从 {prior_accident:.1%} 更新到 {posterior:.1%}")
result = {
    "chart": "bar", "labels": ["先验风险", "雨天后验"],
    "series": [{"name": "事故概率(%)", "values": [prior_accident*100, posterior*100]}],
    "metrics": {"先验": f"{prior_accident:.1%}", "后验": f"{posterior:.1%}", "风险倍数": round(float(lift), 2)}
}`
  },
  {
    id: 'ch3-poisson', chapter: 3, level: '进阶', duration: '12分钟',
    title: '模拟小时事故次数分布', summary: '观察泊松分布的均值与方差。',
    goal: '把概率分布与交通计数变量联系起来。',
    challenge: '修改 lam，观察零事故比例和分布位置。',
    concepts: ['泊松分布', '计数数据', '随机模拟'],
    code: `import numpy as np

rng = np.random.default_rng(12)
lam = 2.4
counts = rng.poisson(lam, 500)
bins = np.arange(0, 9)
frequency = np.array([(counts == value).sum() for value in bins])
zero_ratio = float(np.mean(counts == 0))

print(f"样本均值={counts.mean():.2f}，方差={counts.var():.2f}")
result = {
    "chart": "bar", "labels": [str(v) for v in bins],
    "series": [{"name": "出现次数", "values": frequency.tolist()}],
    "metrics": {"均值": round(float(counts.mean()), 2), "方差": round(float(counts.var()), 2), "零值比例": f"{zero_ratio:.1%}"}
}`
  },
  {
    id: 'ch3-pca', chapter: 3, level: '挑战', duration: '18分钟',
    title: 'PCA压缩交通状态特征', summary: '将速度、流量、占有率压缩到二维。',
    goal: '理解特征值、特征向量与降维表示。',
    challenge: '改变 congestion_threshold，检查状态分组。',
    concepts: ['特征值', 'PCA', '矩阵分解'],
    code: `import numpy as np

rng = np.random.default_rng(4)
n = 50
flow = rng.normal(1000, 240, n)
occupancy = np.clip(0.12 + flow / 5000 + rng.normal(0, 0.035, n), 0, 1)
speed = np.clip(92 - flow / 24 - occupancy * 35 + rng.normal(0, 4, n), 12, 100)
x = np.column_stack([speed, flow, occupancy])
x = (x - x.mean(axis=0)) / x.std(axis=0)
covariance = np.cov(x, rowvar=False)
values, vectors = np.linalg.eigh(covariance)
order = np.argsort(values)[::-1]
projected = x @ vectors[:, order[:2]]
explained = values[order[:2]].sum() / values.sum()
congestion_threshold = 45
labels = (speed < congestion_threshold).astype(int)

result = {
    "chart": "clusters", "x": projected[:,0].tolist(), "y": projected[:,1].tolist(), "labels": labels.tolist(),
    "metrics": {"解释方差": f"{explained:.1%}", "原始维度": 3, "压缩维度": 2}
}`
  },
  {
    id: 'ch4-linear', chapter: 4, level: '进阶', duration: '15分钟',
    title: '旅行时间多元回归', summary: '估计距离和高峰时段对旅行时间的影响。',
    goal: '解释回归系数的统计含义与交通含义。',
    challenge: '提高 peak_effect，观察高峰虚拟变量系数。',
    concepts: ['线性回归', '虚拟变量', '参数解释'],
    code: `import numpy as np

rng = np.random.default_rng(16)
n = 50
distance = rng.uniform(2, 22, n)
peak = rng.integers(0, 2, n)
peak_effect = 9.0
travel_time = 5 + 2.15 * distance + peak_effect * peak + rng.normal(0, 3, n)
x = np.column_stack([np.ones(n), distance, peak])
beta = np.linalg.lstsq(x, travel_time, rcond=None)[0]
prediction = x @ beta
mae = float(np.mean(np.abs(travel_time - prediction)))

result = {
    "chart": "regression", "x": distance.tolist(), "y": travel_time.tolist(), "prediction": prediction.tolist(),
    "metrics": {"距离系数": round(float(beta[1]), 2), "高峰增量": round(float(beta[2]), 2), "MAE": round(mae, 2)}
}`
  },
  {
    id: 'ch4-logistic', chapter: 4, level: '进阶', duration: '15分钟',
    title: '公共交通选择概率', summary: '调整阈值并比较准确率、精确率和召回率。',
    goal: '理解逻辑概率和分类阈值的权衡。',
    challenge: '将 threshold 改为0.35或0.70。',
    concepts: ['逻辑回归', '分类阈值', '召回率'],
    code: `import numpy as np

distance = np.linspace(1, 20, 20)
accessibility = np.array([0.9,0.8,0.9,0.7,0.8,0.6,0.7,0.5,0.6,0.5,0.4,0.5,0.3,0.4,0.3,0.2,0.3,0.2,0.1,0.2])
logit = 1.8 - 0.08 * distance + 2.2 * accessibility
probability = 1 / (1 + np.exp(-logit))
actual = np.array([1,1,1,1,1,1,1,1,1,1,0,1,0,0,0,0,0,0,0,0])
threshold = 0.55
predicted = (probability >= threshold).astype(int)
tp = np.sum((predicted == 1) & (actual == 1))
fp = np.sum((predicted == 1) & (actual == 0))
fn = np.sum((predicted == 0) & (actual == 1))
accuracy = np.mean(predicted == actual)
precision = tp / max(tp + fp, 1)
recall = tp / max(tp + fn, 1)

result = {
    "chart": "series", "x": distance.tolist(),
    "series": [{"name": "公交选择概率", "values": probability.tolist()}, {"name": "真实选择", "values": actual.tolist()}],
    "metrics": {"准确率": f"{accuracy:.1%}", "精确率": f"{precision:.1%}", "召回率": f"{recall:.1%}"}
}`
  },
  {
    id: 'ch4-count', chapter: 4, level: '挑战', duration: '16分钟',
    title: '诊断事故计数过度离散', summary: '比较观测计数与泊松期望。',
    goal: '用方差均值比判断是否需要负二项模型。',
    challenge: '修改 cluster_noise，观察离散比。',
    concepts: ['泊松回归', '负二项', '过度离散'],
    code: `import numpy as np

rng = np.random.default_rng(21)
n = 300
base_rate = 1.8
cluster_noise = 1.0
random_rate = base_rate * np.exp(rng.normal(0, cluster_noise, n))
counts = rng.poisson(random_rate)
mean_count = float(counts.mean())
variance = float(counts.var())
dispersion = variance / mean_count
bins = np.arange(0, 9)
observed = np.array([(counts == value).sum() for value in bins])
poisson_sample = rng.poisson(mean_count, n)
expected = np.array([(poisson_sample == value).sum() for value in bins])

result = {
    "chart": "bar", "labels": [str(v) for v in bins],
    "series": [{"name": "观测", "values": observed.tolist()}, {"name": "泊松参照", "values": expected.tolist()}],
    "metrics": {"均值": round(mean_count, 2), "方差": round(variance, 2), "离散比": round(dispersion, 2)}
}`
  },
  {
    id: 'ch4-zero', chapter: 4, level: '挑战', duration: '16分钟',
    title: '识别零膨胀计数', summary: '模拟结构性零值与普通计数过程。',
    goal: '区分“不会发生”和“暂未发生”两类零值。',
    challenge: '修改 structural_zero_prob，观察零值比例。',
    concepts: ['零膨胀', '结构性零', '计数过程'],
    code: `import numpy as np

rng = np.random.default_rng(30)
n = 400
structural_zero_prob = 0.38
is_structural_zero = rng.random(n) < structural_zero_prob
counts = rng.poisson(2.1, n)
counts[is_structural_zero] = 0
bins = np.arange(0, 9)
frequency = np.array([(counts == value).sum() for value in bins])
zero_ratio = float(np.mean(counts == 0))
poisson_zero = float(np.exp(-counts.mean()))

result = {
    "chart": "bar", "labels": [str(v) for v in bins],
    "series": [{"name": "路段数量", "values": frequency.tolist()}],
    "metrics": {"实际零值": f"{zero_ratio:.1%}", "泊松零值": f"{poisson_zero:.1%}", "结构零参数": f"{structural_zero_prob:.0%}"}
}`
  },
  {
    id: 'ch5-distance', chapter: 5, level: '入门', duration: '10分钟',
    title: '欧氏距离与路网距离', summary: '比较直线距离和受道路约束的距离。',
    goal: '理解交通空间分析不能总使用直线距离。',
    challenge: '修改 detour_factor 表示河流、立交或单行道影响。',
    concepts: ['欧氏距离', '网络距离', '绕行系数'],
    code: `import numpy as np

origins = np.array([[0,0], [1,2], [2,1], [4,3]], dtype=float)
destinations = np.array([[3,4], [5,3], [6,5], [8,6]], dtype=float)
detour_factor = np.array([1.10, 1.35, 1.65, 1.20])
euclidean = np.sqrt(((destinations - origins) ** 2).sum(axis=1))
network = euclidean * detour_factor

result = {
    "chart": "bar", "labels": ["出行1", "出行2", "出行3", "出行4"],
    "series": [{"name": "直线距离", "values": euclidean.tolist()}, {"name": "路网距离", "values": network.tolist()}],
    "metrics": {"平均绕行": round(float(detour_factor.mean()), 2), "最大差值": round(float(np.max(network-euclidean)), 2), "单位": "km"}
}`
  },
  {
    id: 'ch5-mapmatch', chapter: 5, level: '进阶', duration: '16分钟',
    title: 'GPS点到道路匹配', summary: '把带噪轨迹投影到候选道路。',
    goal: '理解最近道路匹配及其误差。',
    challenge: '增大 noise，观察匹配距离。',
    concepts: ['地图匹配', '点线投影', 'GPS误差'],
    code: `import numpy as np

rng = np.random.default_rng(9)
x = np.linspace(0.5, 9.5, 14)
road_y = 0.48 * x + 1.0
noise = 0.55
gps_y = road_y + rng.normal(0, noise, len(x))

# 直线 y=ax+b 上的正交投影
a, b = 0.48, 1.0
matched_x = (x + a * (gps_y - b)) / (1 + a*a)
matched_y = a * matched_x + b
distance = np.sqrt((x-matched_x)**2 + (gps_y-matched_y)**2)
reference_x = np.linspace(0, 10, 30)
reference_y = a * reference_x + b

result = {
    "chart": "clusters", "x": x.tolist(), "y": gps_y.tolist(), "labels": [0]*len(x),
    "centers": np.column_stack([matched_x, matched_y]).tolist(),
    "reference": {"x": reference_x.tolist(), "y": reference_y.tolist()},
    "metrics": {"平均误差": round(float(distance.mean()), 2), "最大误差": round(float(distance.max()), 2), "GPS点": len(x)}
}`
  },
  {
    id: 'clusters', chapter: 5, level: '进阶', duration: '16分钟',
    title: 'K-means识别事故热点', summary: '改变热点数量并观察空间分组。',
    goal: '理解空间聚类参数如何改变热点范围。',
    challenge: '将 k 改为2、3或4，比较紧凑度。',
    concepts: ['空间聚类', '热点', '紧凑度'],
    code: `import numpy as np

points = np.array([
    [1.0,1.2],[1.3,1.0],[0.8,0.9],[1.5,1.4],[1.1,1.6],
    [4.6,4.8],[5.1,5.2],[4.8,5.5],[5.4,4.7],[5.6,5.3],
    [8.2,2.0],[8.6,2.4],[7.8,2.6],[8.9,1.8],[8.1,3.0],
    [3.0,2.8],[6.5,3.8],[2.2,5.7]
], dtype=float)
k = 3
iterations = 12
centers = points[np.linspace(0, len(points)-1, k, dtype=int)].copy()
for _ in range(iterations):
    distance = ((points[:,None,:]-centers[None,:,:])**2).sum(axis=2)
    labels = distance.argmin(axis=1)
    centers = np.array([points[labels==g].mean(axis=0) if np.any(labels==g) else centers[g] for g in range(k)])
compactness = float(np.mean(np.min(distance, axis=1)))
result = {
    "chart": "clusters", "x": points[:,0].tolist(), "y": points[:,1].tolist(), "labels": labels.tolist(), "centers": centers.tolist(),
    "metrics": {"热点数量": k, "事故点": len(points), "紧凑度": round(compactness, 2)}
}`
  },
  {
    id: 'ch5-moran', chapter: 5, level: '挑战', duration: '18分钟',
    title: '计算全局Moran’s I', summary: '判断相邻区域事故率是否空间集聚。',
    goal: '连接空间权重矩阵与空间自相关。',
    challenge: '打乱 grid 中的值，观察Moran’s I下降。',
    concepts: ['空间权重', 'Moran’s I', '空间集聚'],
    code: `import numpy as np

grid = np.array([
    [8, 9, 3, 2], [7, 8, 3, 2],
    [2, 3, 7, 8], [1, 2, 8, 9]
], dtype=float)
rows, cols = grid.shape
x = grid.ravel()
mean = x.mean()
numerator = 0.0
weight_sum = 0.0
for r in range(rows):
    for c in range(cols):
        i = r * cols + c
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            rr, cc = r+dr, c+dc
            if 0 <= rr < rows and 0 <= cc < cols:
                j = rr * cols + cc
                numerator += (x[i]-mean)*(x[j]-mean)
                weight_sum += 1
denominator = np.sum((x-mean)**2)
moran = len(x) / weight_sum * numerator / denominator
result = {
    "chart": "heatmap", "matrix": grid.tolist(),
    "rowLabels": ["北1","北2","南1","南2"], "colLabels": ["西1","西2","东1","东2"],
    "metrics": {"Moran I": round(float(moran), 3), "均值": round(float(mean), 2), "判断": "正向集聚" if moran > 0 else "离散"}
}`
  },
  {
    id: 'timeseries', chapter: 6, level: '入门', duration: '10分钟',
    title: '滑动平均观察需求趋势', summary: '改变窗口宽度并比较平滑程度。',
    goal: '区分短时波动和长期趋势。',
    challenge: '将 window 改为3、5或7。',
    concepts: ['移动平均', '趋势', '窗口'],
    code: `import numpy as np

demand = np.array([22,15,11,9,13,36,96,218,348,226,158,172,188,181,170,186,246,382,438,325,218,148,91,48], dtype=float)
window = 5
kernel = np.ones(window) / window
smoothed = np.convolve(demand, kernel, mode="same")
residual = demand - smoothed
result = {
    "chart": "series", "x": list(range(24)),
    "series": [{"name": "原始需求", "values": demand.tolist()}, {"name": "平滑趋势", "values": smoothed.tolist()}],
    "metrics": {"窗口": window, "峰值时刻": f"{int(np.argmax(demand))}:00", "残差均值": round(float(np.mean(np.abs(residual))), 1)}
}`
  },
  {
    id: 'ch6-acf', chapter: 6, level: '进阶', duration: '14分钟',
    title: '识别交通流自相关', summary: '计算不同滞后步长的相关系数。',
    goal: '判断历史多远的信息仍有预测价值。',
    challenge: '修改 period，观察周期峰值移动。',
    concepts: ['自相关', '滞后', '周期性'],
    code: `import numpy as np

period = 6
t = np.arange(72)
series = 100 + 25*np.sin(2*np.pi*t/period) + 8*np.sin(2*np.pi*t/24)
lags = np.arange(1, 19)
acf = []
for lag in lags:
    acf.append(float(np.corrcoef(series[:-lag], series[lag:])[0,1]))
best_lag = int(lags[np.argmax(acf)])
result = {
    "chart": "bar", "labels": [str(v) for v in lags],
    "series": [{"name": "自相关", "values": acf}],
    "metrics": {"最强滞后": best_lag, "相关系数": round(max(acf), 3), "周期参数": period}
}`
  },
  {
    id: 'ch6-ar', chapter: 6, level: '进阶', duration: '16分钟',
    title: 'AR模型短时预测', summary: '估计一阶自回归参数并递推未来。',
    goal: '理解当前状态如何依赖上一时刻。',
    challenge: '改变 train_size，观察预测稳定性。',
    concepts: ['AR(1)', '递推预测', '时间划分'],
    code: `import numpy as np

rng = np.random.default_rng(5)
values = [100.0]
for _ in range(35):
    values.append(18 + 0.84 * values[-1] + rng.normal(0, 5))
values = np.array(values)
train_size = 30
x = np.column_stack([np.ones(train_size-1), values[:train_size-1]])
y = values[1:train_size]
beta = np.linalg.lstsq(x, y, rcond=None)[0]
forecast = []
current = values[train_size-1]
for _ in range(len(values)-train_size):
    current = beta[0] + beta[1] * current
    forecast.append(current)
actual = values[train_size:]
mae = float(np.mean(np.abs(actual-np.array(forecast))))
result = {
    "chart": "series", "x": list(range(train_size, len(values))),
    "series": [{"name": "真实值", "values": actual.tolist()}, {"name": "AR预测", "values": forecast}],
    "metrics": {"AR系数": round(float(beta[1]), 3), "MAE": round(mae, 2), "预测步数": len(forecast)}
}`
  },
  {
    id: 'ch6-seasonal', chapter: 6, level: '进阶', duration: '14分钟',
    title: '历史同期季节基线', summary: '用上周同日预测本周需求。',
    goal: '建立交通时序预测必须超越的周期基线。',
    challenge: '增大 event_effect，观察事件日误差。',
    concepts: ['季节基线', '周期', '事件扰动'],
    code: `import numpy as np

last_week = np.array([118,125,129,132,140,92,84], dtype=float)
event_effect = 22
this_week = np.array([121,128,131,136,143,94,87], dtype=float)
this_week[3] += event_effect
forecast = last_week.copy()
error = np.abs(this_week-forecast)
result = {
    "chart": "series", "x": list(range(1,8)),
    "series": [{"name": "本周真实", "values": this_week.tolist()}, {"name": "上周同期", "values": forecast.tolist()}],
    "metrics": {"MAE": round(float(error.mean()), 1), "最大误差日": int(np.argmax(error)+1), "事件增量": event_effect}
}`
  },
  {
    id: 'ch7-impute', chapter: 7, level: '进阶', duration: '15分钟',
    title: '空间加权补全检测器数据', summary: '利用相邻检测器修复缺失速度。',
    goal: '理解时空数据不能只按单列均值补全。',
    challenge: '修改 weights，比较上游和下游影响。',
    concepts: ['缺失补全', '邻接权重', '检测器矩阵'],
    code: `import numpy as np

speed = np.array([
    [70,68,65,61,58,55], [67,65,-1,58,54,51],
    [64,62,59,55,51,48], [61,59,56,52,48,45]
], dtype=float)
weights = np.array([0.6, 0.4])
missing_row, missing_col = 1, 2
neighbors = np.array([speed[0,missing_col], speed[2,missing_col]])
imputed = float(neighbors @ weights / weights.sum())
speed[missing_row, missing_col] = imputed
result = {
    "chart": "heatmap", "matrix": speed.tolist(),
    "rowLabels": ["路段A","路段B","路段C","路段D"], "colLabels": ["t1","t2","t3","t4","t5","t6"],
    "metrics": {"补全速度": round(imputed, 1), "上游权重": weights[0], "下游权重": weights[1]}
}`
  },
  {
    id: 'ch7-lag', chapter: 7, level: '进阶', duration: '15分钟',
    title: '寻找拥堵传播时滞', summary: '比较上下游速度在不同滞后下的相关。',
    goal: '估计拥堵从上游传到下游需要多久。',
    challenge: '修改 true_lag，检查算法能否找回传播时滞。',
    concepts: ['时滞相关', '拥堵传播', '上下游'],
    code: `import numpy as np

t = np.arange(40)
upstream = 70 - 35*np.exp(-((t-17)/4)**2)
true_lag = 3
downstream = np.roll(upstream, true_lag)
downstream[:true_lag] = upstream[0]
lags = np.arange(0, 9)
correlations = []
for lag in lags:
    if lag == 0:
        correlations.append(float(np.corrcoef(upstream, downstream)[0,1]))
    else:
        correlations.append(float(np.corrcoef(upstream[:-lag], downstream[lag:])[0,1]))
best = int(lags[np.argmax(correlations)])
result = {
    "chart": "bar", "labels": [str(v) for v in lags],
    "series": [{"name": "滞后相关", "values": correlations}],
    "metrics": {"识别时滞": best, "真实时滞": true_lag, "最高相关": round(max(correlations), 3)}
}`
  },
  {
    id: 'ch7-propagation', chapter: 7, level: '挑战', duration: '18分钟',
    title: '绘制拥堵传播时空图', summary: '观察低速状态沿道路走廊移动。',
    goal: '从时空矩阵中识别拥堵形成和消散。',
    challenge: '修改 propagation_speed，改变传播方向和速度。',
    concepts: ['时空矩阵', '传播方向', '速度热图'],
    code: `import numpy as np

segments = 6
times = 14
propagation_speed = 1.0
matrix = np.full((segments, times), 72.0)
for road in range(segments):
    center = 4 + road * propagation_speed
    for time in range(times):
        matrix[road,time] -= 42*np.exp(-((time-center)/2.2)**2)
matrix = np.clip(matrix, 18, 75)
minimum = np.unravel_index(np.argmin(matrix), matrix.shape)
result = {
    "chart": "heatmap", "matrix": matrix.tolist(),
    "rowLabels": [f"路段{i+1}" for i in range(segments)], "colLabels": [str(i) for i in range(times)],
    "metrics": {"最低速度": round(float(matrix.min()), 1), "最严重路段": int(minimum[0]+1), "传播速度": propagation_speed}
}`
  },
  {
    id: 'ch7-adjacency', chapter: 7, level: '挑战', duration: '18分钟',
    title: '比较邻接矩阵假设', summary: '比较拓扑邻接与相关性邻接预测。',
    goal: '理解图模型结果取决于空间关系定义。',
    challenge: '修改 topology_weight，观察两种假设的误差。',
    concepts: ['邻接矩阵', '图结构', '模型比较'],
    code: `import numpy as np

actual = np.array([62,58,51,43,36,32,35,41,49,56,61,64], dtype=float)
upstream = np.array([65,61,55,47,39,34,33,37,45,53,59,63], dtype=float)
similar_road = np.array([60,57,52,45,38,34,37,43,50,55,60,62], dtype=float)
topology_weight = 0.75
topology_prediction = topology_weight*upstream + (1-topology_weight)*actual.mean()
correlation_prediction = 0.82*similar_road + 0.18*actual.mean()
mae_topology = float(np.mean(np.abs(actual-topology_prediction)))
mae_correlation = float(np.mean(np.abs(actual-correlation_prediction)))
result = {
    "chart": "series", "x": list(range(12)),
    "series": [{"name": "真实速度", "values": actual.tolist()}, {"name": "拓扑邻接", "values": topology_prediction.tolist()}, {"name": "相关邻接", "values": correlation_prediction.tolist()}],
    "metrics": {"拓扑MAE": round(mae_topology, 2), "相关MAE": round(mae_correlation, 2), "更优": "拓扑" if mae_topology < mae_correlation else "相关"}
}`
  },
  {
    id: 'ch8-iou', chapter: 8, level: '入门', duration: '12分钟',
    title: '计算目标检测IoU', summary: '评价预测框与真实框的重叠程度。',
    goal: '理解检测正确不只是类别正确，还要定位准确。',
    challenge: '修改 predicted_boxes，观察IoU变化。',
    concepts: ['边界框', 'IoU', '定位误差'],
    code: `import numpy as np

ground_truth = np.array([20, 20, 80, 70], dtype=float)
predicted_boxes = np.array([
    [22,22,78,68], [10,15,72,65], [35,28,92,80], [0,0,40,35]
], dtype=float)

def iou(a, b):
    x1, y1 = max(a[0],b[0]), max(a[1],b[1])
    x2, y2 = min(a[2],b[2]), min(a[3],b[3])
    intersection = max(0,x2-x1)*max(0,y2-y1)
    area_a = (a[2]-a[0])*(a[3]-a[1])
    area_b = (b[2]-b[0])*(b[3]-b[1])
    return intersection/(area_a+area_b-intersection)

values = [iou(ground_truth, box) for box in predicted_boxes]
result = {
    "chart": "bar", "labels": ["预测框1","预测框2","预测框3","预测框4"],
    "series": [{"name": "IoU", "values": values}],
    "metrics": {"最高IoU": round(max(values), 3), "合格框": sum(v>=0.5 for v in values), "阈值": 0.5}
}`
  },
  {
    id: 'ch8-nms', chapter: 8, level: '进阶', duration: '15分钟',
    title: '非极大值抑制去重', summary: '调整NMS阈值，控制重复检测框。',
    goal: '理解检测框去重与漏检之间的平衡。',
    challenge: '修改 selected_threshold，观察保留框数量。',
    concepts: ['NMS', '重复检测', '阈值'],
    code: `import numpy as np

scores = np.array([0.95,0.88,0.81,0.72,0.61])
# 简化后的框间最大重叠关系
overlap = np.array([
    [0,0.76,0.18,0.05,0.02], [0.76,0,0.22,0.08,0.03],
    [0.18,0.22,0,0.68,0.12], [0.05,0.08,0.68,0,0.16],
    [0.02,0.03,0.12,0.16,0]
])

def kept_count(threshold):
    order = list(np.argsort(scores)[::-1])
    kept = []
    while order:
        current = order.pop(0)
        kept.append(current)
        order = [item for item in order if overlap[current,item] <= threshold]
    return len(kept)

thresholds = np.array([0.2,0.3,0.4,0.5,0.6,0.7,0.8])
counts = [kept_count(value) for value in thresholds]
selected_threshold = 0.5
result = {
    "chart": "bar", "labels": [str(v) for v in thresholds],
    "series": [{"name": "保留框数", "values": counts}],
    "metrics": {"选择阈值": selected_threshold, "保留框": kept_count(selected_threshold), "原始框": len(scores)}
}`
  },
  {
    id: 'ch8-threshold', chapter: 8, level: '进阶', duration: '16分钟',
    title: '置信度阈值与PR权衡', summary: '比较不同阈值下的精确率和召回率。',
    goal: '为车辆检测选择符合业务目标的阈值。',
    challenge: '增加低分真阳性，观察召回率曲线。',
    concepts: ['置信度', '精确率', '召回率'],
    code: `import numpy as np

scores = np.array([0.96,0.91,0.86,0.82,0.74,0.68,0.61,0.54,0.47,0.39,0.31,0.22])
labels = np.array([1,1,0,1,1,0,1,1,0,1,0,1])
thresholds = np.array([0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9])
precision, recall = [], []
positives = labels.sum()
for threshold in thresholds:
    prediction = scores >= threshold
    tp = np.sum(prediction & (labels==1))
    fp = np.sum(prediction & (labels==0))
    precision.append(float(tp/max(tp+fp,1)))
    recall.append(float(tp/max(positives,1)))
balance = np.array(precision)+np.array(recall)
best = int(np.argmax(balance))
result = {
    "chart": "series", "x": thresholds.tolist(),
    "series": [{"name": "精确率", "values": precision}, {"name": "召回率", "values": recall}],
    "metrics": {"建议阈值": thresholds[best], "精确率": f"{precision[best]:.1%}", "召回率": f"{recall[best]:.1%}"}
}`
  },
  {
    id: 'ch8-tracking', chapter: 8, level: '挑战', duration: '18分钟',
    title: '车辆跟踪与过线计数', summary: '根据轨迹方向判断车辆是否穿越计数线。',
    goal: '把逐帧检测结果转化为交通流量指标。',
    challenge: '修改 line_y 或轨迹，观察漏计和重复计数。',
    concepts: ['目标跟踪', '计数线', '轨迹方向'],
    code: `import numpy as np

frames = np.arange(12)
vehicle_a = np.array([10,15,21,28,35,43,52,61,70,78,86,92], dtype=float)
vehicle_b = np.array([92,87,80,74,67,59,51,44,36,29,22,16], dtype=float)
line_y = 55

def crossing_count(track):
    count = 0
    for previous, current in zip(track[:-1], track[1:]):
        if (previous < line_y <= current) or (previous > line_y >= current):
            count += 1
    return count

count_a = crossing_count(vehicle_a)
count_b = crossing_count(vehicle_b)
line = np.repeat(line_y, len(frames))
result = {
    "chart": "series", "x": frames.tolist(),
    "series": [{"name": "车辆A", "values": vehicle_a.tolist()}, {"name": "车辆B", "values": vehicle_b.tolist()}, {"name": "计数线", "values": line.tolist()}],
    "metrics": {"总计数": count_a+count_b, "车辆A": count_a, "车辆B": count_b}
}`
  }
];
