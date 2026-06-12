const labExamples = {
  regression: {
    title: '梯度下降拟合交通需求',
    code: `import numpy as np

# 小时与对应的共享单车需求指数
hours = np.array([6, 7, 8, 9, 10, 16, 17, 18, 19, 20], dtype=float)
demand = np.array([72, 145, 286, 230, 168, 210, 355, 430, 318, 226], dtype=float)

# 尝试修改这两个参数
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
    "chart": "regression",
    "x": hours.tolist(),
    "y": demand.tolist(),
    "prediction": fitted.tolist(),
    "metrics": {"MAE": round(mae, 1), "斜率": round(w, 3), "最终损失": round(losses[-1], 4)}
}`
  },
  timeseries: {
    title: '滑动平均观察需求趋势',
    code: `import numpy as np

# 连续 24 小时的需求指数
demand = np.array([
    22, 15, 11, 9, 13, 36, 96, 218, 348, 226, 158, 172,
    188, 181, 170, 186, 246, 382, 438, 325, 218, 148, 91, 48
], dtype=float)

# 尝试改为 3、5 或 7
window = 5

kernel = np.ones(window) / window
smoothed = np.convolve(demand, kernel, mode="same")
residual = demand - smoothed

print(f"窗口宽度: {window}")
print(f"原始峰值出现在 {int(np.argmax(demand))} 时")
result = {
    "chart": "series",
    "x": list(range(24)),
    "series": [
        {"name": "原始需求", "values": demand.tolist()},
        {"name": "平滑趋势", "values": smoothed.tolist()}
    ],
    "metrics": {
        "窗口": window,
        "峰值时刻": f"{int(np.argmax(demand))}:00",
        "残差均值": round(float(np.mean(np.abs(residual))), 1)
    }
}`
  },
  clusters: {
    title: 'K-means 识别事故热点',
    code: `import numpy as np

# 模拟的城市事故点坐标，三片区域具有不同密度
points = np.array([
    [1.0, 1.2], [1.3, 1.0], [0.8, 0.9], [1.5, 1.4], [1.1, 1.6],
    [4.6, 4.8], [5.1, 5.2], [4.8, 5.5], [5.4, 4.7], [5.6, 5.3],
    [8.2, 2.0], [8.6, 2.4], [7.8, 2.6], [8.9, 1.8], [8.1, 3.0],
    [3.0, 2.8], [6.5, 3.8], [2.2, 5.7]
], dtype=float)

# 尝试改为 2、3 或 4
k = 3
iterations = 12
centers = points[np.linspace(0, len(points) - 1, k, dtype=int)].copy()

for _ in range(iterations):
    distance = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    labels = distance.argmin(axis=1)
    centers = np.array([
        points[labels == group].mean(axis=0) if np.any(labels == group) else centers[group]
        for group in range(k)
    ])

compactness = float(np.mean(np.min(distance, axis=1)))
print(f"识别出 {k} 个候选热点")
result = {
    "chart": "clusters",
    "x": points[:, 0].tolist(),
    "y": points[:, 1].tolist(),
    "labels": labels.tolist(),
    "centers": centers.tolist(),
    "metrics": {"热点数量": k, "事故点": len(points), "紧凑度": round(compactness, 2)}
}`
  }
};

const labCode = document.getElementById('lab-code');
const labTitle = document.getElementById('lab-example-title');
const labRun = document.getElementById('lab-run');
const labStop = document.getElementById('lab-stop');
const labReset = document.getElementById('lab-reset');
const labStatus = document.getElementById('lab-status');
const labConsole = document.getElementById('lab-console');
const labMetrics = document.getElementById('lab-metrics');
const labChart = document.getElementById('lab-chart');
const labChartEmpty = document.getElementById('lab-chart-empty');
let activeLab = 'regression';
let labWorker = null;
let labRunning = false;

function selectLab(name, resetCode = true) {
  activeLab = name;
  const example = labExamples[name];
  labTitle.textContent = example.title;
  if (resetCode) labCode.value = example.code;
  document.querySelectorAll('.lab-example-tab').forEach((button) => {
    const active = button.dataset.labExample === name;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', String(active));
  });
}

function createWorker() {
  if (labWorker) return labWorker;
  labWorker = new Worker('assets/python-worker.js?v=2');
  labWorker.addEventListener('message', handleWorkerMessage);
  labWorker.addEventListener('error', (event) => finishWithError(event.message || '浏览器 Python 环境加载失败'));
  return labWorker;
}

function setRunning(running) {
  labRunning = running;
  labRun.disabled = running;
  labStop.disabled = !running;
  labCode.readOnly = running;
}

function handleWorkerMessage(event) {
  const message = event.data;
  if (message.type === 'status') {
    labStatus.textContent = message.text;
    return;
  }
  if (message.type === 'result') {
    setRunning(false);
    labStatus.textContent = `完成 · ${message.elapsed} 秒`;
    labConsole.textContent = message.stdout || '代码运行完成，没有 print 输出。';
    renderMetrics(message.result.metrics || {});
    renderLabChart(message.result);
    return;
  }
  if (message.type === 'error') finishWithError(message.error);
}

function finishWithError(error) {
  setRunning(false);
  labStatus.textContent = '运行失败';
  labConsole.textContent = error;
  labConsole.closest('details').open = true;
}

function renderMetrics(metrics) {
  const entries = Object.entries(metrics).slice(0, 4);
  labMetrics.replaceChildren(...entries.map(([label, value]) => {
    const item = document.createElement('div');
    const caption = document.createElement('span');
    const number = document.createElement('strong');
    caption.textContent = label;
    number.textContent = value;
    item.append(caption, number);
    return item;
  }));
}

function svgElement(tag, attributes = {}) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  return element;
}

function scales(xValues, yValues) {
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const padX = (maxX - minX || 1) * 0.08;
  const padY = (maxY - minY || 1) * 0.12;
  return {
    x: (value) => 58 + ((value - minX + padX) / (maxX - minX + padX * 2)) * 552,
    y: (value) => 302 - ((value - minY + padY) / (maxY - minY + padY * 2)) * 252
  };
}

function drawGrid() {
  [50, 113, 176, 239, 302].forEach((y) => labChart.append(svgElement('line', {x1: 58, y1: y, x2: 610, y2: y, class: 'lab-gridline'})));
}

function renderLabChart(result) {
  labChart.replaceChildren();
  labChartEmpty.hidden = true;
  drawGrid();
  if (result.chart === 'regression') renderRegression(result);
  else if (result.chart === 'series') renderSeries(result);
  else if (result.chart === 'clusters') renderClusters(result);
  else throw new Error('result.chart 必须是 regression、series 或 clusters');
}

function renderRegression(result) {
  const scale = scales(result.x, [...result.y, ...result.prediction]);
  const ordered = result.x.map((x, index) => ({x, y: result.prediction[index]})).sort((a, b) => a.x - b.x);
  const path = ordered.map((point, index) => `${index ? 'L' : 'M'}${scale.x(point.x)},${scale.y(point.y)}`).join(' ');
  labChart.append(svgElement('path', {d: path, class: 'lab-result-line'}));
  result.x.forEach((x, index) => labChart.append(svgElement('circle', {cx: scale.x(x), cy: scale.y(result.y[index]), r: 6, class: 'lab-result-point'})));
}

function renderSeries(result) {
  const allValues = result.series.flatMap((series) => series.values);
  const scale = scales(result.x, allValues);
  result.series.forEach((series, seriesIndex) => {
    const path = result.x.map((x, index) => `${index ? 'L' : 'M'}${scale.x(x)},${scale.y(series.values[index])}`).join(' ');
    labChart.append(svgElement('path', {d: path, class: `lab-series-line series-${seriesIndex}`}));
    const legend = svgElement('text', {x: 70 + seriesIndex * 115, y: 28, class: `lab-legend series-${seriesIndex}`});
    legend.textContent = `● ${series.name}`;
    labChart.append(legend);
  });
}

function renderClusters(result) {
  const centerX = result.centers.map((center) => center[0]);
  const centerY = result.centers.map((center) => center[1]);
  const scale = scales([...result.x, ...centerX], [...result.y, ...centerY]);
  result.x.forEach((x, index) => labChart.append(svgElement('circle', {
    cx: scale.x(x), cy: scale.y(result.y[index]), r: 7, class: `lab-cluster-point cluster-${result.labels[index] % 5}`
  })));
  result.centers.forEach((center, index) => {
    const marker = svgElement('text', {x: scale.x(center[0]), y: scale.y(center[1]) + 7, class: `lab-center cluster-${index % 5}`});
    marker.textContent = '×';
    labChart.append(marker);
  });
}

document.querySelectorAll('.lab-example-tab').forEach((button) => {
  button.addEventListener('click', () => selectLab(button.dataset.labExample));
});

document.querySelectorAll('[data-open-lab]').forEach((link) => {
  link.addEventListener('click', () => selectLab(link.dataset.openLab));
});

labReset.addEventListener('click', () => selectLab(activeLab));

labRun.addEventListener('click', () => {
  if (labRunning) return;
  setRunning(true);
  labStatus.textContent = '准备运行...';
  labConsole.textContent = '正在启动浏览器 Python 环境...';
  createWorker().postMessage({type: 'run', code: labCode.value});
});

labStop.addEventListener('click', () => {
  if (!labWorker) return;
  labWorker.terminate();
  labWorker = null;
  setRunning(false);
  labStatus.textContent = '已停止';
  labConsole.textContent = '运行已由用户停止。再次点击运行会重新启动 Python。';
});

selectLab(activeLab);
