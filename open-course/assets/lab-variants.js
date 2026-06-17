(function () {
  const labs = window.LAB_EXAMPLES || [];
  const byId = new Map(labs.map((lab) => [lab.id, lab]));

  function set(id, patch) {
    const lab = byId.get(id);
    if (!lab) return;
    Object.assign(lab, patch);
    lab.realData = true;
    lab.concepts = Array.from(new Set([...(patch.concepts || lab.concepts || []), '真实数据']));
  }

  set('relational-join', {
    level: '真实数据',
    title: 'MTA GTFS线路与班次连接查询',
    summary: '使用 MTA 纽约地铁 GTFS 静态数据中的 routes 与 trips 表，统计工作日各线路班次数。',
    goal: '理解 GTFS 中线路表和班次表如何通过 route_id 连接。',
    challenge: '把 route_ids 换成其他线路，观察工作日班次规模和排序是否改变。',
    dataSource: 'MTA NYCT Subway GTFS Static',
    sourceUrl: 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip',
    sampleNote: '在线样本取自 routes.txt 与 trips.txt 的线路分组结果；完整 ZIP 可离线下载复现。',
    concepts: ['GTFS', '连接查询', '分组统计'],
    code: `import numpy as np

# 数据源：MTA NYCT Subway GTFS Static，gtfs_subway.zip
# 样本含义：从 trips.txt 按 route_id 汇总 Weekday service 的班次数。
route_ids = np.array(["1", "2", "3", "A", "C", "E"])
route_names = ["Broadway-7 Av Local", "7 Av Express", "7 Av Express",
               "8 Av Express", "8 Av Local", "8 Av Local"]
weekday_trips = np.array([462, 324, 302, 379, 222, 410], dtype=float)
sort_order = np.array([20, 21, 22, 1, 2, 3])

# 模拟 routes 表与 trips 聚合结果的连接：这里用 route_id 对齐。
service_index = weekday_trips / weekday_trips.max() * 100
best = int(np.argmax(weekday_trips))

result = {
    "chart": "bar",
    "labels": route_ids.tolist(),
    "series": [{"name": "工作日班次数指数", "values": service_index.round(1).tolist()}],
    "metrics": {
        "最高线路": route_ids[best],
        "班次数": int(weekday_trips[best]),
        "样本线路": len(route_ids)
    }
}`
  });

  set('od-heatmap', {
    level: '真实数据',
    title: 'NYC黄色出租车早高峰OD热力图',
    summary: '使用 NYC TLC 2023 黄色出租车记录，汇总 2023-01-03 08:00-09:00 的高频出租车区 OD。',
    goal: '理解出租车上车区和下车区如何构成 OD 矩阵。',
    challenge: '删去同区出行或加入更多 zone，观察最强 OD 是否变化。',
    dataSource: 'NYC TLC Yellow Taxi Trip Records 2023',
    sourceUrl: 'https://data.cityofnewyork.us/resource/4b4i-vvec',
    sampleNote: '在线样本为 NYC Open Data API 聚合后的前 20 个高频 OD；完整数据可从 TLC Trip Record Data 下载。',
    concepts: ['OD矩阵', '出租车区', '热力图'],
    code: `import numpy as np

# 数据源：NYC TLC Yellow Taxi Trip Records 2023
# 查询窗口：2023-01-03 08:00-09:00，按 PULocationID/DOLocationID 聚合。
zones = ["237", "236", "161", "186", "162", "234", "141", "140"]
records = [
    ("237", "236", 50), ("237", "161", 35), ("236", "161", 34),
    ("236", "237", 32), ("236", "236", 29), ("237", "237", 27),
    ("186", "161", 27), ("237", "162", 26), ("186", "234", 25),
    ("141", "236", 24), ("236", "162", 22), ("236", "140", 21),
    ("142", "161", 21), ("238", "236", 20), ("140", "236", 19),
    ("141", "161", 19), ("236", "163", 18), ("170", "161", 16),
    ("229", "164", 15)
]
index = {zone: i for i, zone in enumerate(zones)}
matrix = np.zeros((len(zones), len(zones)))
for origin, destination, count in records:
    if origin in index and destination in index:
        matrix[index[origin], index[destination]] += count

masked = matrix.copy()
np.fill_diagonal(masked, -1)
origin, destination = np.unravel_index(np.argmax(masked), masked.shape)

result = {
    "chart": "heatmap",
    "matrix": matrix.tolist(),
    "rowLabels": zones,
    "colLabels": zones,
    "metrics": {
        "样本出行": int(matrix.sum()),
        "最强OD": f"{zones[origin]}->{zones[destination]}",
        "流量": int(matrix[origin, destination])
    }
}`
  });

  set('bayes-accident-risk', {
    level: '真实数据',
    title: 'NYC事故样本的贝叶斯受伤风险更新',
    summary: '使用 NYC 交通事故 2023 年 1 月样本，根据夜间和驾驶员注意力不集中两个证据更新受伤概率。',
    goal: '把贝叶斯公式落到真实事故字段：受伤人数、事故时间和主要致因。',
    challenge: '把夜间定义从 18-06 改为 20-05，观察后验概率是否改变。',
    dataSource: 'NYC Motor Vehicle Collisions - Crashes',
    sourceUrl: 'https://data.cityofnewyork.us/resource/h9gi-nx95',
    sampleNote: '在线样本使用 2023-01 的 2000 条事故记录聚合比例；完整接口可按日期继续拉取。',
    concepts: ['条件概率', '贝叶斯公式', '事故风险'],
    code: `import numpy as np

# 数据源：NYC Motor Vehicle Collisions - Crashes
# 聚合窗口：2023-01，样本 2000 条。
evidence = ["先验", "夜间后", "夜间+注意力不集中"]
prior = 0.3835  # P(有人受伤)
p_night_injured = 0.4537
p_night_safe = 0.3966
p_distracted_injured = 0.2503
p_distracted_safe = 0.2303

p_night = p_night_injured * prior + p_night_safe * (1 - prior)
posterior_night = p_night_injured * prior / p_night
p_distracted = p_distracted_injured * posterior_night + p_distracted_safe * (1 - posterior_night)
posterior_both = p_distracted_injured * posterior_night / p_distracted
values = np.array([prior, posterior_night, posterior_both]) * 100

result = {
    "chart": "bar",
    "labels": evidence,
    "series": [{"name": "受伤概率(%)", "values": values.round(2).tolist()}],
    "metrics": {
        "样本数": 2000,
        "先验": f"{prior:.1%}",
        "后验": f"{posterior_both:.1%}"
    }
}`
  });

  set('regression', {
    level: '真实数据',
    title: 'UCI共享单车小时需求梯度下降',
    summary: '使用 UCI Bike Sharing 第一天小时记录，用小时变量拟合租车需求的简单基线。',
    goal: '把损失函数、梯度下降和 MAE 连接到真实共享单车需求数据。',
    challenge: '修改 learning_rate 或 steps，观察拟合线和 MAE 是否稳定。',
    dataSource: 'UCI Bike Sharing Dataset',
    sourceUrl: 'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset',
    sampleNote: '在线样本取 hour.csv 的 2011-01-01 24 小时记录；离线脚本使用完整数据。',
    concepts: ['梯度下降', '共享单车', 'MAE'],
    code: `import numpy as np

# 数据源：UCI Bike Sharing Dataset, hour.csv 前 24 小时。
hour = np.arange(24, dtype=float)
cnt = np.array([16,40,32,13,1,1,2,3,8,14,36,56,
                84,94,106,110,93,67,35,37,36,34,28,39], dtype=float)

x = (hour - hour.mean()) / hour.std()
w, b = 0.0, cnt.mean()
learning_rate = 0.08
steps = 240
for _ in range(steps):
    error = (w * x + b) - cnt
    w -= learning_rate * float(2 * np.mean(error * x))
    b -= learning_rate * float(2 * np.mean(error))

prediction = w * x + b
mae = float(np.mean(np.abs(cnt - prediction)))

result = {
    "chart": "regression",
    "x": hour.tolist(),
    "y": cnt.tolist(),
    "prediction": prediction.round(1).tolist(),
    "metrics": {
        "MAE": round(mae, 2),
        "梯度步数": steps,
        "样本小时": len(hour)
    }
}`
  });

  set('overfit-generalization', {
    level: '真实数据',
    title: 'UCI共享单车多项式过拟合观察',
    summary: '用同一天奇偶小时切分训练和测试，比较不同多项式阶数的泛化误差。',
    goal: '看到模型复杂度提高后，训练误差下降但测试误差可能变差。',
    challenge: '把 degree 增加到 11 或 13，观察测试 RMSE 是否恶化。',
    dataSource: 'UCI Bike Sharing Dataset',
    sourceUrl: 'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset',
    sampleNote: '在线样本取 hour.csv 的 2011-01-01 24 小时需求记录。',
    concepts: ['训练测试划分', '过拟合', 'RMSE'],
    code: `import numpy as np

hour = np.arange(24, dtype=float)
cnt = np.array([16,40,32,13,1,1,2,3,8,14,36,56,
                84,94,106,110,93,67,35,37,36,34,28,39], dtype=float)
train = np.arange(0, 24, 2)
test = np.arange(1, 24, 2)
degrees = np.array([1, 3, 5, 9], dtype=int)
train_rmse, test_rmse = [], []

for degree in degrees:
    coef = np.polyfit(hour[train], cnt[train], degree)
    train_pred = np.polyval(coef, hour[train])
    test_pred = np.polyval(coef, hour[test])
    train_rmse.append(float(np.mean((cnt[train] - train_pred) ** 2) ** 0.5))
    test_rmse.append(float(np.mean((cnt[test] - test_pred) ** 2) ** 0.5))

best = int(np.argmin(test_rmse))
result = {
    "chart": "bar",
    "labels": [f"{d}阶" for d in degrees],
    "series": [
        {"name": "训练RMSE", "values": np.round(train_rmse, 2).tolist()},
        {"name": "测试RMSE", "values": np.round(test_rmse, 2).tolist()}
    ],
    "metrics": {
        "最佳阶数": int(degrees[best]),
        "测试RMSE": round(test_rmse[best], 2),
        "样本数": len(hour)
    }
}`
  });

  set('count-regression', {
    level: '真实数据',
    title: 'NYC各区受伤事故计数基线',
    summary: '使用 NYC 事故 2023 年 1 月分区样本，把事故总数作为暴露量估计受伤事故期望。',
    goal: '理解计数模型为什么要区分暴露量和事件次数。',
    challenge: '把全局受伤率改成各区历史率，比较预测是否更接近观测值。',
    dataSource: 'NYC Motor Vehicle Collisions - Crashes',
    sourceUrl: 'https://data.cityofnewyork.us/resource/h9gi-nx95',
    sampleNote: '在线样本为 2023-01 分区聚合：total crashes 与 injured crashes。',
    concepts: ['计数数据', '暴露量', '泊松基线'],
    code: `import numpy as np

# 2023-01 NYC crash records, borough IS NOT NULL.
boroughs = ["BROOKLYN", "QUEENS", "MANHATTAN", "BRONX", "STATEN ISLAND"]
total_crashes = np.array([1697, 1357, 857, 846, 201], dtype=float)
injured_crashes = np.array([663, 531, 295, 303, 70], dtype=float)

global_rate = injured_crashes.sum() / total_crashes.sum()
expected = total_crashes * global_rate
residual = injured_crashes - expected

result = {
    "chart": "bar",
    "labels": ["BK", "QN", "MN", "BX", "SI"],
    "series": [
        {"name": "观测受伤事故", "values": injured_crashes.tolist()},
        {"name": "泊松期望", "values": expected.round(1).tolist()}
    ],
    "metrics": {
        "全局受伤率": f"{global_rate:.1%}",
        "最大残差区": boroughs[int(np.argmax(np.abs(residual)))],
        "样本事故": int(total_crashes.sum())
    }
}`
  });

  set('network-distance', {
    level: '真实数据',
    title: 'MTA 1号线站点直线距离与线路距离',
    summary: '使用 MTA GTFS stops.txt 的真实站点坐标，比较直线距离和沿 1 号线站序累计距离。',
    goal: '理解交通网络上的距离通常大于两点直线距离。',
    challenge: '改用更远的站点对，观察线路距离与直线距离差异是否扩大。',
    dataSource: 'MTA NYCT Subway GTFS Static',
    sourceUrl: 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip',
    sampleNote: '在线样本取 1 号线北段站点坐标；完整 stops.txt 可离线复现。',
    concepts: ['GTFS站点', '网络距离', 'Haversine'],
    code: `import numpy as np

# 数据源：MTA GTFS stops.txt，1号线北段站点坐标。
names = ["242 St", "238 St", "231 St", "225 St", "215 St", "207 St",
         "Dyckman", "191 St", "181 St", "168 St", "157 St", "145 St"]
lat = np.array([40.889248,40.884667,40.878856,40.874561,40.869444,40.864621,
                40.860531,40.855225,40.849505,40.840556,40.834041,40.826551])
lon = np.array([-73.898583,-73.900870,-73.904834,-73.909831,-73.915279,-73.918822,
                -73.925536,-73.929412,-73.933596,-73.940133,-73.944890,-73.950360])

def haversine(i, j):
    r = 6371.0
    lat1, lat2 = np.radians(lat[i]), np.radians(lat[j])
    dlat = np.radians(lat[j] - lat[i])
    dlon = np.radians(lon[j] - lon[i])
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))

segment = np.array([haversine(i, i + 1) for i in range(len(names) - 1)])
cum = np.concatenate([[0], np.cumsum(segment)])
pairs = [(0, 3), (0, 6), (2, 9), (5, 11)]
straight = np.array([haversine(i, j) for i, j in pairs])
network = np.array([cum[j] - cum[i] for i, j in pairs])
labels = [f"{names[i]}-{names[j]}" for i, j in pairs]
detour = network / straight

result = {
    "chart": "bar",
    "labels": labels,
    "series": [
        {"name": "直线距离km", "values": straight.round(2).tolist()},
        {"name": "线路距离km", "values": network.round(2).tolist()}
    ],
    "metrics": {
        "最大绕行": labels[int(np.argmax(detour))],
        "平均绕行": round(float(detour.mean()), 2),
        "站点数": len(names)
    }
}`
  });

  set('map-matching', {
    level: '真实数据',
    title: 'GeoLife GPS点投影到候选道路',
    summary: '使用 GeoLife 文档样例中的 GPS 点，演示把经纬度点投影到候选中心线。',
    goal: '理解地图匹配的核心是把有噪声的 GPS 点约束到道路几何上。',
    challenge: '增大 GPS 点的横向偏移，观察平均匹配误差如何变化。',
    dataSource: 'Microsoft GeoLife GPS Trajectories',
    sourceUrl: 'https://www.microsoft.com/en-us/download/details.aspx?id=52367',
    sampleNote: '在线样本取 GeoLife PLT 文档样例首段；完整数据需按 Microsoft 页面下载。',
    concepts: ['GPS轨迹', '地图匹配', '点线投影'],
    code: `import numpy as np

# GeoLife PLT 样例：Data/010/Trajectory/20070804033032.plt 的前三个点。
lat = np.array([39.921712, 39.921705, 39.921695])
lon = np.array([116.472343, 116.472343, 116.472345])

# 转成近似米制坐标，便于投影。
lat0 = lat.mean()
x = (lon - lon.mean()) * 111000 * np.cos(np.radians(lat0))
y = (lat - lat.mean()) * 111000

# 候选道路中心线：用首尾点构成一条局部线段。
a = np.array([x[0], y[0]])
b = np.array([x[-1], y[-1]])
v = b - a
t = ((np.column_stack([x, y]) - a) @ v) / (v @ v)
t = np.clip(t, 0, 1)
matched = a + t[:, None] * v
distance = np.sqrt(((np.column_stack([x, y]) - matched) ** 2).sum(axis=1))
reference_x = np.linspace(a[0], b[0], 10)
reference_y = np.linspace(a[1], b[1], 10)

result = {
    "chart": "clusters",
    "x": x.round(3).tolist(),
    "y": y.round(3).tolist(),
    "labels": [0, 0, 0],
    "centers": matched.round(3).tolist(),
    "reference": {"x": reference_x.round(3).tolist(), "y": reference_y.round(3).tolist()},
    "metrics": {
        "平均误差m": round(float(distance.mean()), 3),
        "最大误差m": round(float(distance.max()), 3),
        "GPS点": len(lat)
    }
}`
  });

  set('clusters', {
    level: '真实数据',
    title: 'NYC交通事故坐标DBSCAN热点识别',
    summary: '使用 NYC 事故开放数据的真实经纬度点，运行一个小型 DBSCAN 热点识别。',
    goal: '理解 eps 和 min_points 如何影响事故热点与噪声点划分。',
    challenge: '把 eps_km 从 4 改为 2，观察热点数量和噪声点变化。',
    dataSource: 'NYC Motor Vehicle Collisions - Crashes',
    sourceUrl: 'https://data.cityofnewyork.us/resource/h9gi-nx95',
    sampleNote: '在线样本取 2023-01-01 前 20 条带坐标事故记录。',
    concepts: ['DBSCAN', '事故坐标', '热点识别'],
    code: `import numpy as np

lat = np.array([40.710514,40.845870,40.708237,40.693660,40.745068,
                40.823853,40.815320,40.820625,40.814762,40.651337,
                40.876747,40.648228,40.679730,40.708300,40.651863,
                40.814010,40.761982,40.633130,40.704810,40.769737])
lon = np.array([-73.956140,-73.890730,-73.943370,-73.931540,-73.936356,
                -73.807686,-73.886650,-73.890300,-73.813630,-73.889595,
                -73.901245,-74.084500,-73.937400,-73.789200,-73.865360,
                -73.944660,-73.878960,-74.075356,-73.939320,-73.912440])

lat0 = lat.mean()
x = (lon - lon.mean()) * 111 * np.cos(np.radians(lat0))
y = (lat - lat.mean()) * 111
points = np.column_stack([x, y])
eps_km = 4.0
min_points = 3
labels = np.full(len(points), -1, dtype=int)
visited = np.zeros(len(points), dtype=bool)

def neighbors(i):
    d = np.sqrt(((points - points[i]) ** 2).sum(axis=1))
    return np.where(d <= eps_km)[0].tolist()

cluster_id = 0
for i in range(len(points)):
    if visited[i]:
        continue
    visited[i] = True
    seed = neighbors(i)
    if len(seed) < min_points:
        continue
    labels[i] = cluster_id
    k = 0
    while k < len(seed):
        j = seed[k]
        if not visited[j]:
            visited[j] = True
            expanded = neighbors(j)
            if len(expanded) >= min_points:
                seed.extend([n for n in expanded if n not in seed])
        if labels[j] == -1:
            labels[j] = cluster_id
        k += 1
    cluster_id += 1

centers = []
for group in range(cluster_id):
    centers.append(points[labels == group].mean(axis=0).round(3).tolist())

result = {
    "chart": "clusters",
    "x": x.round(3).tolist(),
    "y": y.round(3).tolist(),
    "labels": labels.tolist(),
    "centers": centers,
    "metrics": {
        "热点数": cluster_id,
        "噪声点": int(np.sum(labels == -1)),
        "事故点": len(points)
    }
}`
  });

  set('timeseries', {
    level: '真实数据',
    title: 'Metro I-94小时交通量短时预测',
    summary: '使用 UCI Metro Interstate Traffic Volume 的连续小时流量，比较上一小时基线和三小时均值预测。',
    goal: '先建立简单、可解释的时间序列基线，再讨论复杂模型是否值得使用。',
    challenge: '把窗口长度从 3 改为 5，观察 MAE 是否下降。',
    dataSource: 'UCI Metro Interstate Traffic Volume',
    sourceUrl: 'https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume',
    sampleNote: '在线样本取 CSV 开头 19 个小时记录；离线项目使用完整压缩 CSV。',
    concepts: ['时间序列', '基线模型', 'MAE'],
    code: `import numpy as np

# Metro I-94 traffic_volume, 2012-10-02 09:00 起连续小时样本。
volume = np.array([5545,4516,4767,5026,4918,5181,5584,6015,5791,
                   4770,3539,2784,2361,1529,963,506,321,273,367], dtype=float)
time = np.arange(len(volume))
window = 3
actual = volume[window:]
last_hour = volume[window - 1:-1]
rolling = np.array([volume[i - window:i].mean() for i in range(window, len(volume))])
mae_last = float(np.mean(np.abs(actual - last_hour)))
mae_roll = float(np.mean(np.abs(actual - rolling)))

result = {
    "chart": "series",
    "x": time[window:].tolist(),
    "series": [
        {"name": "真实流量", "values": actual.tolist()},
        {"name": "上一小时", "values": last_hour.tolist()},
        {"name": "三小时均值", "values": rolling.round(1).tolist()}
    ],
    "metrics": {
        "上一小时MAE": round(mae_last, 1),
        "均值MAE": round(mae_roll, 1),
        "窗口": window
    }
}`
  });

  set('st-matrix', {
    level: '真实数据',
    title: 'PeMS-SF检测器时空矩阵切片',
    summary: '使用 UCI PeMS-SF 训练文件开头的归一化检测器读数，组成检测器 × 时间矩阵。',
    goal: '理解时空数据最小单元是“位置-时间”观测值。',
    challenge: '把矩阵乘以 1000 改成 100，观察指标尺度变化但空间结构不变。',
    dataSource: 'UCI PeMS-SF',
    sourceUrl: 'https://archive.ics.uci.edu/dataset/204/pems+sf',
    sampleNote: '在线样本取 PEMS_train 第一条记录的前 5 个检测器、前 10 个时间片。',
    concepts: ['时空矩阵', '检测器', 'PeMS'],
    code: `import numpy as np

# UCI PeMS-SF PEMS_train 第一条记录切片，原值为归一化读数。
matrix = np.array([
    [0.0154,0.0085,0.0099,0.0108,0.0100,0.0111,0.0099,0.0081,0.0099,0.0088],
    [0.0054,0.0051,0.0056,0.0045,0.0037,0.0027,0.0046,0.0028,0.0042,0.0040],
    [0.0164,0.0127,0.0172,0.0126,0.0185,0.0077,0.0119,0.0086,0.0091,0.0124],
    [0.0079,0.0062,0.0068,0.0072,0.0048,0.0046,0.0046,0.0046,0.0045,0.0057],
    [0.0059,0.0051,0.0053,0.0058,0.0063,0.0046,0.0063,0.0047,0.0052,0.0044]
], dtype=float) * 1000
rows = ["400000", "400001", "400009", "400010", "400015"]
cols = [f"t{i}" for i in range(1, 11)]
low = np.unravel_index(np.argmin(matrix), matrix.shape)
high = np.unravel_index(np.argmax(matrix), matrix.shape)

result = {
    "chart": "heatmap",
    "matrix": matrix.round(2).tolist(),
    "rowLabels": rows,
    "colLabels": cols,
    "metrics": {
        "最低点": f"{rows[low[0]]}-{cols[low[1]]}",
        "最高值": round(float(matrix[high]), 2),
        "检测器数": len(rows)
    }
}`
  });

  set('iou-nms', {
    level: '真实数据',
    title: 'KITTI车辆框IoU与重复检测',
    summary: '使用 KITTI 目标检测标注风格的车辆框，计算候选框 IoU 并演示 NMS 保留逻辑。',
    goal: '理解目标检测评价同时关注位置重叠、置信度和重复框去除。',
    challenge: '把 nms_threshold 从 0.5 改为 0.3，观察保留框数量是否变化。',
    dataSource: 'KITTI Object Detection Benchmark',
    sourceUrl: 'https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=2d',
    sampleNote: '在线样本使用 KITTI label_2 风格车辆框坐标；完整图像和标签需按 KITTI 条款下载。',
    concepts: ['目标检测', 'IoU', 'NMS'],
    code: `import numpy as np

# KITTI label_2 风格车辆框：[x1, y1, x2, y2]
truth = np.array([712.40, 143.00, 810.73, 307.92], dtype=float)
boxes = np.array([
    [710.0, 140.0, 812.0, 309.0],
    [699.0, 150.0, 800.0, 300.0],
    [730.0, 160.0, 840.0, 315.0],
    [600.0, 150.0, 690.0, 295.0]
], dtype=float)
scores = np.array([0.93, 0.82, 0.66, 0.41])

def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)

ious = np.array([iou(truth, box) for box in boxes])
nms_threshold = 0.5
order = scores.argsort()[::-1]
kept = []
for idx in order:
    if all(iou(boxes[idx], boxes[j]) < nms_threshold for j in kept):
        kept.append(int(idx))

result = {
    "chart": "bar",
    "labels": [f"框{i+1}" for i in range(len(boxes))],
    "series": [{"name": "对真值IoU", "values": ious.round(3).tolist()}],
    "metrics": {
        "最高IoU": round(float(ious.max()), 3),
        "NMS保留": len(kept),
        "阈值": nms_threshold
    }
}`
  });
})();
