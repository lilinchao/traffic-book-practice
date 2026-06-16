const py = (value) => JSON.stringify(value, null, 2);

const sectionRows = [
  ['1.1', 's1-1', '交通数据挖掘概述', 'bar'],
  ['1.2', 's1-2', '交通数据分析基础', 'bar'],
  ['1.3', 's1-3', '交通数据类型', 'bar'],
  ['1.4', 's1-4', '常见开源交通数据集', 'bar'],
  ['1.5', 's1-5', '交通数据挖掘常用方法', 'bar'],
  ['1.6', 's1-6', '本书结构与学习建议', 'series'],
  ['2.1', 's2-1', '数据库基础', 'bar'],
  ['2.2', 's2-2', 'Python数据处理基础', 'series'],
  ['2.3', 's2-3', '数据可视化基础', 'bar'],
  ['2.4', 's2-4', '交通数据分析实践环境', 'bar'],
  ['3.1', 's3-1', '微积分基础', 'series'],
  ['3.2', 's3-2', '概率论基础', 'bar'],
  ['3.3', 's3-3', '线性代数基础', 'clusters'],
  ['3.4', 'regression', '优化方法基础', 'regression'],
  ['3.5', 's3-5', '机器学习建模基础', 'series'],
  ['3.6', 's3-6', '综合案例：数学概念如何支撑交通建模', 'bar'],
  ['4.1', 's4-1', '交通表格型数据概述', 'bar'],
  ['4.2', 's4-2', '交通表格型数据预处理', 'bar'],
  ['4.3', 's4-3', '连续因变量回归分析', 'regression'],
  ['4.4', 's4-4', '分类因变量回归分析', 'series'],
  ['4.5', 's4-5', '计数因变量回归分析', 'bar'],
  ['4.6', 's4-6', '零膨胀数据分析', 'bar'],
  ['4.7', 's4-7', '本章实践：交通表格型数据建模', 'bar'],
  ['4.8', 's4-8', '本章小结与习题', 'bar'],
  ['5.1', 's5-1', '交通位置数据的理论基础', 'bar'],
  ['5.2', 's5-2', '交通位置数据的获取与预处理方法', 'clusters'],
  ['5.3', 's5-3', '地图匹配方法', 'mapmatch'],
  ['5.4', 's5-4', '空间连接、缓冲区与服务覆盖分析', 'bar'],
  ['5.5', 's5-5', '位置数据的空间聚合与指标构建', 'heatmap'],
  ['5.6', 'clusters', '空间点模式与热点识别方法', 'clusters'],
  ['5.7', 's5-7', '空间自相关与统计热点识别', 'heatmap'],
  ['5.8', 's5-8', '空间插值方法', 'heatmap'],
  ['5.9', 's5-9', '空间回归与空间异质性模型', 'bar'],
  ['5.10', 's5-10', '综合实践：交通事故点位数据分析', 'bar'],
  ['5.11', 's5-11', '方法选择与适用边界', 'bar'],
  ['6.1', 's6-1', '交通时序数据概述', 'series'],
  ['6.2', 's6-2', '时序数据预处理', 'series'],
  ['6.3', 's6-3', '时序数据统计分析', 'series'],
  ['6.4', 's6-4', '时序数据检验', 'series'],
  ['6.5', 'timeseries', 'ARIMA模型', 'series'],
  ['6.6', 's6-6', '长短时记忆网络模型', 'bar'],
  ['6.7', 's6-7', '动态时间规整', 'bar'],
  ['6.8', 's6-8', '本章实践：交通流量短时预测', 'series'],
  ['7.1', 's7-1', '交通时空数据的基本认识与组织方式', 'heatmap'],
  ['7.2', 's7-2', '交通时空相关性分析', 'bar'],
  ['7.3', 's7-3', '交通时空数据预处理', 'heatmap'],
  ['7.4', 's7-4', '交通时空分析方法', 'clusters'],
  ['7.5', 's7-5', '交通时空预测方法', 'bar'],
  ['7.6', 's7-6', '综合案例：城市路网交通速度预测', 'heatmap'],
  ['7.7', 's7-7', '本章小结', 'bar'],
  ['7.8', 's7-8', '习题与思考', 'bar'],
  ['8.1', 's8-1', '交通录像数据的基本认识', 'bar'],
  ['8.2', 's8-2', '交通录像数据预处理', 'bar'],
  ['8.3', 's8-3', '图像分类方法', 'heatmap'],
  ['8.4', 's8-4', '交通目标检测方法', 'bar'],
  ['8.5', 's8-5', '图像语义分割方法', 'bar'],
  ['8.6', 's8-6', '视频目标跟踪与交通参数提取', 'series'],
  ['8.7', 's8-7', '综合案例：路口交通视频车辆检测与流量统计', 'bar'],
  ['8.8', 's8-8', '本章小结', 'bar'],
  ['8.9', 's8-9', '习题与思考', 'bar']
];

const conceptMap = {
  bar: ['指标构建', '对比分析', '解释结果'],
  series: ['时间序列', '基线比较', '误差分析'],
  heatmap: ['矩阵表达', '空间聚合', '热点识别'],
  regression: ['回归建模', '参数估计', '模型评价'],
  clusters: ['空间点', '聚类', '中心识别'],
  mapmatch: ['地图匹配', 'GPS误差', '道路投影']
};

const challengeMap = {
  bar: '调整 values 或 baseline，观察指标排序是否改变。',
  series: '修改 observed 中的峰值或谷值，比较误差指标变化。',
  heatmap: '把一个单元格调高，观察热点位置和均值是否变化。',
  regression: '修改 y 中的观测值，观察斜率和 MAE 的变化。',
  clusters: '改变 k 或 points，观察空间分组和紧凑度变化。',
  mapmatch: '增大 noise，观察 GPS 点到道路中心线的匹配误差。'
};

function seedOf(text) {
  return [...text].reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

function numbers(seed, count, low, high) {
  return Array.from({length: count}, (_, index) => {
    const raw = (seed * (index + 3) + index * index * 17 + 23) % (high - low + 1);
    return low + raw;
  });
}

function labMeta(section, id, title, template) {
  const chapter = Number(section.split('.')[0]);
  const seed = seedOf(section + title);
  return {
    id,
    chapter,
    section,
    level: id === 'regression' || id === 'clusters' || id === 'timeseries' ? '进阶' : '小节',
    duration: id === 'regression' || id === 'clusters' || id === 'timeseries' ? '15分钟' : `${8 + seed % 5}分钟`,
    title,
    summary: `围绕“${title}”构造一个可运行的小型交通数据实验。`,
    goal: `把教材 ${section} 小节的方法转化为可计算、可解释的交通数据分析步骤。`,
    challenge: challengeMap[template],
    concepts: conceptMap[template],
    code: templates[template]({section, title, seed})
  };
}

const templates = {
  bar({section, title, seed}) {
    const labels = ['数据准备', '特征构建', '模型计算', '结果解释', '复核改进'];
    const values = numbers(seed, labels.length, 52, 96);
    const baseline = values.map((value, index) => Math.max(25, value - 8 + (index % 3) * 4));
    return `import numpy as np

# ${section} ${title}
labels = ${py(labels)}
values = np.array(${py(values)}, dtype=float)
baseline = np.array(${py(baseline)}, dtype=float)

gain = values - baseline
best = int(np.argmax(values))
print(f"最高项：{labels[best]}，取值：{values[best]:.2f}")

result = {
    "chart": "bar",
    "labels": labels,
    "series": [
        {"name": "实验值", "values": values.tolist()},
        {"name": "基线值", "values": baseline.tolist()}
    ],
    "metrics": {
        "最高项": labels[best],
        "平均值": round(float(values.mean()), 2),
        "平均提升": round(float(gain.mean()), 2),
        "波动范围": round(float(values.max() - values.min()), 2)
    }
}`;
  },

  series({section, title, seed}) {
    const base = numbers(seed, 8, 80, 180);
    const observed = base.map((value, index) => value + (index % 3 === 1 ? 42 : index * 7));
    const baseline = observed.map((value, index) => Math.round(value * (0.92 + (index % 4) * 0.02)));
    return `import numpy as np

# ${section} ${title}
x = np.arange(1, 9)
observed = np.array(${py(observed)}, dtype=float)
baseline = np.array(${py(baseline)}, dtype=float)

error = observed - baseline
peak = int(np.argmax(observed))
mae = float(np.mean(np.abs(error)))
print(f"峰值位置：{int(x[peak])}，平均绝对误差：{mae:.2f}")

result = {
    "chart": "series",
    "x": x.tolist(),
    "series": [
        {"name": "观测值", "values": observed.tolist()},
        {"name": "基线值", "values": baseline.tolist()}
    ],
    "metrics": {
        "峰值位置": int(x[peak]),
        "MAE": round(mae, 2),
        "最大误差": round(float(np.max(np.abs(error))), 2)
    }
}`;
  },

  heatmap({section, title, seed}) {
    const start = seed % 7;
    const matrix = Array.from({length: 4}, (_, r) =>
      Array.from({length: 4}, (_, c) => 3 + start + r * 3 + c * 2 + (r === 2 && c === 2 ? 7 : 0))
    );
    return `import numpy as np

# ${section} ${title}
matrix = np.array(${py(matrix)}, dtype=float)
row_labels = ["北1", "北2", "南1", "南2"]
col_labels = ["西1", "西2", "东1", "东2"]

position = np.unravel_index(np.argmax(matrix), matrix.shape)
print(f"最高单元：{row_labels[position[0]]} × {col_labels[position[1]]}")

result = {
    "chart": "heatmap",
    "matrix": matrix.tolist(),
    "rowLabels": row_labels,
    "colLabels": col_labels,
    "metrics": {
        "最高单元": f"{row_labels[position[0]]}-{col_labels[position[1]]}",
        "最高值": round(float(matrix[position]), 2),
        "均值": round(float(matrix.mean()), 2)
    }
}`;
  },

  regression({section, title}) {
    return `import numpy as np

# ${section} ${title}
x = np.array([6, 7, 8, 9, 10, 16, 17, 18, 19, 20], dtype=float)
y = np.array([72, 145, 286, 230, 168, 210, 355, 430, 318, 226], dtype=float)

design = np.column_stack([np.ones(len(x)), x])
beta = np.linalg.lstsq(design, y, rcond=None)[0]
prediction = design @ beta
mae = float(np.mean(np.abs(y - prediction)))
print(f"小时 每增加 1 个单位，需求 约变化 {beta[1]:.2f}")

result = {
    "chart": "regression",
    "x": x.tolist(),
    "y": y.tolist(),
    "prediction": prediction.tolist(),
    "metrics": {
        "截距": round(float(beta[0]), 2),
        "斜率": round(float(beta[1]), 2),
        "MAE": round(mae, 2)
    }
}`;
  },

  clusters({section, title, seed}) {
    const shift = (seed % 5) / 10;
    const points = [
      [1.0, 1.2], [1.3, 1.0], [0.8, 0.9], [1.5, 1.4],
      [4.6, 4.8], [5.1, 5.2], [4.8, 5.5], [5.4, 4.7],
      [8.2, 2.0], [8.6, 2.4], [7.8, 2.6], [8.9, 1.8],
      [3.0 + shift, 2.8], [6.5, 3.8]
    ];
    return `import numpy as np

# ${section} ${title}
points = np.array(${py(points)}, dtype=float)
k = 3

centers = points[np.linspace(0, len(points) - 1, k, dtype=int)].copy()
for _ in range(12):
    distance = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    labels = distance.argmin(axis=1)
    centers = np.array([
        points[labels == group].mean(axis=0) if np.any(labels == group) else centers[group]
        for group in range(k)
    ])

compactness = float(np.mean(np.min(distance, axis=1)))
print(f"识别出 {k} 个空间分组，紧凑度 {compactness:.2f}")

result = {
    "chart": "clusters",
    "x": points[:, 0].tolist(),
    "y": points[:, 1].tolist(),
    "labels": labels.tolist(),
    "centers": centers.tolist(),
    "metrics": {"分组数": k, "样本数": len(points), "紧凑度": round(compactness, 2)}
}`;
  },

  mapmatch({section, title}) {
    return `import numpy as np

# ${section} ${title}
x = np.linspace(0, 10, 18)
road_slope = 0.42
road_intercept = 1.2
noise = np.array([0.35,-0.22,0.18,0.48,-0.31,0.16,-0.44,0.25,0.12,-0.38,0.28,-0.18,0.41,-0.26,0.19,0.33,-0.21,0.14])

gps_y = road_slope * x + road_intercept + noise
matched_x = (x + road_slope * (gps_y - road_intercept)) / (1 + road_slope ** 2)
matched_y = road_slope * matched_x + road_intercept
distance = np.sqrt((x - matched_x) ** 2 + (gps_y - matched_y) ** 2)
reference_x = np.linspace(0, 10, 30)
reference_y = road_slope * reference_x + road_intercept

result = {
    "chart": "clusters",
    "x": x.tolist(),
    "y": gps_y.tolist(),
    "labels": [0] * len(x),
    "centers": np.column_stack([matched_x, matched_y]).tolist(),
    "reference": {"x": reference_x.tolist(), "y": reference_y.tolist()},
    "metrics": {"平均误差": round(float(distance.mean()), 2), "最大误差": round(float(distance.max()), 2), "GPS点": len(x)}
}`;
  }
};

window.LAB_EXAMPLES = sectionRows.map(([section, id, title, template]) => labMeta(section, id, title, template));
