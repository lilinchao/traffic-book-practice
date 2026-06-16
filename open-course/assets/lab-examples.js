const py = (value) => JSON.stringify(value);

const rows = [
  ['data-types', 1, '1.3', '概念交互', '8分钟', '同一交通问题的数据类型选择', 'bar', '数据类型,任务匹配,开放数据'],
  ['open-data-readiness', 1, '1.4', '数据准备', '8分钟', '开源交通数据可用性评价', 'bar', '开放数据,可用性,字段完整性'],
  ['method-selector', 1, '1.5', '方法判断', '10分钟', '交通数据挖掘方法选择器', 'bar', '方法选择,解释性,预测能力'],
  ['relational-join', 2, '2.1', '工具基础', '10分钟', '公交线路与班次的关系型查询', 'bar', '关系型数据,连接查询,分组聚合'],
  ['clean-resample', 2, '2.2', '工具基础', '12分钟', '检测器速度清洗与时间聚合', 'series', '缺失值,异常值,重采样'],
  ['od-heatmap', 2, '2.3', '工具基础', '10分钟', 'OD矩阵热力图表达', 'heatmap', 'OD矩阵,热力图,可视化'],
  ['speed-flow-derivative', 3, '3.1', '核心代码', '10分钟', '速度-密度曲线的边际变化', 'series', '导数,边际变化,基本图'],
  ['bayes-accident-risk', 3, '3.2', '核心代码', '10分钟', '贝叶斯更新事故风险', 'bar', '条件概率,贝叶斯公式,风险更新'],
  ['pca-traffic-state', 3, '3.3', '核心代码', '12分钟', 'PCA压缩交通状态特征', 'clusters', '矩阵分解,PCA,降维'],
  ['regression', 3, '3.4', '核心代码', '15分钟', '梯度下降拟合交通需求', 'regression', '损失函数,梯度下降,模型评价'],
  ['overfit-generalization', 3, '3.5', '模型意识', '12分钟', '训练误差与测试误差的分离', 'bar', '训练测试划分,过拟合,泛化'],
  ['table-preprocess', 4, '4.2', '核心代码', '12分钟', '表格型交通数据预处理清单', 'bar', '数据清洗,异常值,建模前检查'],
  ['travel-time-linear', 4, '4.3', '核心代码', '14分钟', '旅行时间影响因素线性回归', 'regression', '线性回归,虚拟变量,参数解释'],
  ['mode-choice-logit', 4, '4.4', '核心代码', '14分钟', '公共交通选择概率', 'bar', '逻辑回归,概率解释,方式选择'],
  ['count-regression', 4, '4.5', '核心代码', '14分钟', '道路事故次数的泊松预测', 'bar', '计数数据,泊松模型,暴露量'],
  ['zero-inflation', 4, '4.6', '核心代码', '12分钟', '大量零值下的出行次数解释', 'bar', '零膨胀,结构性零值,计数模型'],
  ['network-distance', 5, '5.1', '空间分析', '10分钟', '欧氏距离与路网距离差异', 'bar', '欧氏距离,路网距离,交通约束'],
  ['map-matching', 5, '5.3', '空间分析', '14分钟', 'GPS点到道路中心线匹配', 'clusters', '地图匹配,点线投影,GPS误差'],
  ['buffer-coverage', 5, '5.4', '空间分析', '12分钟', '公交站缓冲区服务覆盖', 'bar', '缓冲区,服务覆盖,供需匹配'],
  ['grid-aggregation', 5, '5.5', '空间分析', '12分钟', '事故点位网格化聚合', 'heatmap', '空间聚合,网格化,指标构建'],
  ['clusters', 5, '5.6', '空间分析', '15分钟', 'DBSCAN识别事故热点', 'clusters', 'DBSCAN,热点识别,噪声点'],
  ['moran-hotspot', 5, '5.7', '空间分析', '15分钟', '全局Moran I空间自相关', 'heatmap', '空间权重,Moran I,空间集聚'],
  ['time-cleaning', 6, '6.2', '时序分析', '12分钟', '时序缺失补全与平滑', 'series', '时间索引,缺失补全,移动平均'],
  ['seasonal-acf', 6, '6.3', '时序分析', '12分钟', '交通流量周期性与自相关', 'bar', '周期性,自相关,滞后'],
  ['timeseries', 6, '6.5', '时序分析', '15分钟', '季节基线与AR残差短时预测', 'series', '季节基线,AR残差,预测评价'],
  ['lstm-window', 6, '6.7', '时序分析', '12分钟', 'LSTM训练样本窗口构造', 'bar', 'LSTM,滑动窗口,监督样本'],
  ['dtw-pattern', 6, '6.8', '时序分析', '14分钟', 'DTW识别相似交通状态', 'bar', 'DTW,相似性度量,模式识别'],
  ['st-matrix', 7, '7.1', '时空分析', '10分钟', '检测器-时间速度矩阵', 'heatmap', '时空矩阵,检测器,速度热力图'],
  ['lag-correlation', 7, '7.2', '时空分析', '12分钟', '上下游拥堵传播时滞', 'bar', '时滞相关,拥堵传播,上下游关系'],
  ['st-forecast', 7, '7.5', '时空分析', '14分钟', '时空特征预测路段速度', 'series', '历史同期,邻接路段,时空预测'],
  ['iou-nms', 8, '8.4', '影像分析', '12分钟', '目标检测IoU与去重', 'bar', '边界框,IoU,NMS'],
  ['segmentation-mask', 8, '8.5', '影像分析', '12分钟', '道路区域语义分割指标', 'heatmap', '语义分割,掩膜,像素IoU'],
  ['tracking-count', 8, '8.6', '影像分析', '14分钟', '车辆轨迹与过线计数', 'series', '目标跟踪,计数线,交通参数提取']
];

const challenges = {
  bar: '调整输入指标，观察排序、阈值或推荐结果是否改变。',
  series: '修改峰值、窗口或基线，比较误差指标变化。',
  heatmap: '提高一个空间单元的数值，观察热点位置是否移动。',
  regression: '修改一个观测值，观察斜率、截距和MAE的变化。',
  clusters: '改变点位或阈值，观察分组结果和中心位置变化。'
};

function hash(text) {
  return [...text].reduce((total, char) => (total * 31 + char.charCodeAt(0)) % 9973, 17);
}

function seq(seed, count, low, high) {
  return Array.from({length: count}, (_, index) => {
    const value = (seed * (index + 5) + index * index * 13 + 29) % (high - low + 1);
    return low + value;
  });
}

function barCode(title, seed) {
  const labels = ['数据准备', '特征构建', '模型计算', '结果解释', '复核改进'];
  const values = seq(seed, 5, 42, 96);
  const baseline = values.map((value, index) => Math.max(25, value - 6 - (index % 3) * 3));
  return `import numpy as np

# ${title}
labels = ${py(labels)}
values = np.array(${py(values)}, dtype=float)
baseline = np.array(${py(baseline)}, dtype=float)
gain = values - baseline
best = int(np.argmax(values))

result = {
    "chart": "bar",
    "labels": labels,
    "series": [
        {"name": "实验值", "values": values.tolist()},
        {"name": "基线值", "values": baseline.tolist()}
    ],
    "metrics": {"最高项": labels[best], "最高值": round(float(values[best]), 2), "平均提升": round(float(gain.mean()), 2)}
}`;
}

function seriesCode(title, seed) {
  const x = Array.from({length: 12}, (_, index) => index + 1);
  const observed = seq(seed, 12, 35, 150).map((value, index) => Math.round(value + 28 * Math.sin(index / 1.7)));
  const baseline = observed.map((value, index, array) => {
    const left = array[Math.max(0, index - 1)];
    const right = array[Math.min(array.length - 1, index + 1)];
    return Math.round((left + value + right) / 3);
  });
  return `import numpy as np

# ${title}
x = ${py(x)}
observed = np.array(${py(observed)}, dtype=float)
baseline = np.array(${py(baseline)}, dtype=float)
error = np.abs(observed - baseline)
peak = int(np.argmax(observed))

result = {
    "chart": "series",
    "x": x,
    "series": [
        {"name": "观测值", "values": observed.tolist()},
        {"name": "基线或平滑值", "values": baseline.tolist()}
    ],
    "metrics": {"峰值位置": x[peak], "峰值": round(float(observed[peak]), 2), "MAE": round(float(error.mean()), 2)}
}`;
}

function heatmapCode(title, seed) {
  const labels = ['北1', '北2', '南1', '南2'];
  const base = seq(seed, 16, 3, 35);
  const matrix = [0, 1, 2, 3].map((row) => base.slice(row * 4, row * 4 + 4));
  matrix[2][2] += 18;
  return `import numpy as np

# ${title}
labels = ${py(labels)}
matrix = np.array(${py(matrix)}, dtype=float)
position = np.unravel_index(np.argmax(matrix), matrix.shape)

result = {
    "chart": "heatmap",
    "matrix": matrix.tolist(),
    "rowLabels": labels,
    "colLabels": labels,
    "metrics": {"热点单元": f"{labels[position[0]]}-{labels[position[1]]}", "最高值": round(float(matrix[position]), 2), "均值": round(float(matrix.mean()), 2)}
}`;
}

function regressionCode(title, seed) {
  const x = Array.from({length: 10}, (_, index) => index + 2);
  const slope = 2.5 + (seed % 7) / 2;
  const y = x.map((value, index) => Math.round(8 + slope * value + ((index % 4) - 1.5) * 4));
  return `import numpy as np

# ${title}
x = np.array(${py(x)}, dtype=float)
y = np.array(${py(y)}, dtype=float)
design = np.column_stack([np.ones(len(x)), x])
beta = np.linalg.lstsq(design, y, rcond=None)[0]
prediction = design @ beta
mae = float(np.mean(np.abs(y - prediction)))

result = {
    "chart": "regression",
    "x": x.tolist(),
    "y": y.tolist(),
    "prediction": prediction.tolist(),
    "metrics": {"截距": round(float(beta[0]), 2), "斜率": round(float(beta[1]), 2), "MAE": round(mae, 2)}
}`;
}

function clusterCode(title, seed) {
  const offset = (seed % 5) / 10;
  const points = [
    [1, 1.2], [1.3, 0.9], [0.8, 1.5], [4.7, 4.8], [5.2, 5.1],
    [4.9, 5.6], [8.2, 2.0], [8.7, 2.4], [7.9, 2.7], [3.0, 2.8], [6.4, 3.8]
  ].map(([x, y]) => [Number((x + offset).toFixed(2)), Number((y - offset).toFixed(2))]);
  return `import numpy as np

# ${title}
points = np.array(${py(points)}, dtype=float)
centers = np.array([[1.0, 1.2], [5.0, 5.2], [8.3, 2.3]], dtype=float)
distance = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
labels = distance.argmin(axis=1)
centers = np.array([points[labels == group].mean(axis=0) for group in range(3)])
compactness = float(np.mean(np.min(distance, axis=1)))

result = {
    "chart": "clusters",
    "x": points[:, 0].tolist(),
    "y": points[:, 1].tolist(),
    "labels": labels.tolist(),
    "centers": centers.tolist(),
    "metrics": {"分组数": 3, "样本数": len(points), "紧凑度": round(compactness, 2)}
}`;
}

function buildCode(type, title, seed) {
  if (type === 'bar') return barCode(title, seed);
  if (type === 'series') return seriesCode(title, seed);
  if (type === 'heatmap') return heatmapCode(title, seed);
  if (type === 'regression') return regressionCode(title, seed);
  if (type === 'clusters') return clusterCode(title, seed);
  throw new Error(`Unknown lab chart type: ${type}`);
}

window.LAB_EXAMPLES = rows.map(([id, chapter, section, level, duration, title, type, conceptText]) => {
  const seed = hash(`${id}-${title}`);
  return {
    id,
    chapter,
    section,
    level,
    duration,
    title,
    summary: `围绕“${title}”构建一个可运行的交通数据小实验。`,
    goal: `把教材 ${section} 小节的方法转化为数据、指标和图表三个步骤。`,
    challenge: challenges[type],
    concepts: conceptText.split(','),
    code: buildCode(type, title, seed)
  };
});
