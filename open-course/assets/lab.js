const labExamples = window.LAB_EXAMPLES || [];
const labById = new Map(labExamples.map((example) => [example.id, example]));

const labCode = document.getElementById('lab-code');
const labTitle = document.getElementById('lab-example-title');
const labGoal = document.getElementById('lab-goal');
const labChallenge = document.getElementById('lab-challenge');
const labConcepts = document.getElementById('lab-concepts');
const labFilters = document.getElementById('lab-chapter-filters');
const labCatalog = document.getElementById('lab-catalog');
const labCatalogCount = document.getElementById('lab-catalog-count');
const labRun = document.getElementById('lab-run');
const labStop = document.getElementById('lab-stop');
const labReset = document.getElementById('lab-reset');
const labDownload = document.getElementById('lab-download');
const labStatus = document.getElementById('lab-status');
const labConsole = document.getElementById('lab-console');
const labMetrics = document.getElementById('lab-metrics');
const labChart = document.getElementById('lab-chart');
const labChartEmpty = document.getElementById('lab-chart-empty');

let activeLab = labExamples[0]?.id || '';
let activeChapter = 1;
let labWorker = null;
let labRunning = false;

const chartColors = ['#4965f5', '#ff6b42', '#0b756b', '#9b51e0', '#d1a600'];

function renderChapterFilters() {
  const filters = [
    {value: 0, label: '全部'},
    ...Array.from({length: 8}, (_, index) => ({value: index + 1, label: `第${index + 1}章`}))
  ];
  labFilters.replaceChildren(...filters.map((filter) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'lab-chapter-filter';
    button.classList.toggle('active', filter.value === activeChapter);
    button.textContent = filter.label;
    button.addEventListener('click', () => {
      activeChapter = filter.value;
      if (activeChapter !== 0 && labById.get(activeLab)?.chapter !== activeChapter) {
        const firstInChapter = labExamples.find((example) => example.chapter === activeChapter);
        if (firstInChapter) {
          selectLab(firstInChapter.id);
          return;
        }
      }
      renderChapterFilters();
      renderCatalog();
    });
    return button;
  }));
}

function renderCatalog() {
  const visible = activeChapter === 0
    ? labExamples
    : labExamples.filter((example) => example.chapter === activeChapter);

  labCatalogCount.textContent = activeChapter === 0
    ? `全部章节 · ${visible.length}项实践`
    : `第${activeChapter}章 · ${visible.length}项实践`;

  labCatalog.replaceChildren(...visible.map((example) => {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'lab-catalog-card';
    card.classList.toggle('active', example.id === activeLab);
    card.dataset.labId = example.id;

    const meta = document.createElement('span');
    meta.className = 'lab-card-meta';
    const level = document.createElement('span');
    level.textContent = `第${example.chapter}章 · ${example.level}`;
    const duration = document.createElement('span');
    duration.textContent = example.duration;
    meta.append(level, duration);

    const title = document.createElement('strong');
    title.textContent = example.title;
    const summary = document.createElement('p');
    summary.textContent = example.summary;
    card.append(meta, title, summary);
    card.addEventListener('click', () => selectLab(example.id));
    return card;
  }));
}

function selectLab(id, options = {}) {
  const example = labById.get(id);
  if (!example) return;
  activeLab = id;
  if (options.reveal) activeChapter = example.chapter;
  labTitle.textContent = example.title;
  labGoal.textContent = example.goal;
  labChallenge.textContent = example.challenge;
  labConcepts.replaceChildren(...example.concepts.map((concept) => {
    const tag = document.createElement('span');
    tag.textContent = concept;
    return tag;
  }));
  if (options.resetCode !== false) labCode.value = example.code;
  renderChapterFilters();
  renderCatalog();
}

function createWorker() {
  if (labWorker) return labWorker;
  labWorker = new Worker('assets/python-worker.js?v=3');
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
    try {
      renderMetrics(message.result?.metrics || {});
      renderLabChart(message.result || {});
    } catch (error) {
      finishWithError(`结果可视化失败：${error.message}`);
    }
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
  [50, 113, 176, 239, 302].forEach((y) => {
    labChart.append(svgElement('line', {x1: 58, y1: y, x2: 610, y2: y, class: 'lab-gridline'}));
  });
}

function renderLabChart(result) {
  labChart.replaceChildren();
  labChartEmpty.hidden = true;
  if (result.chart !== 'heatmap') drawGrid();
  if (result.chart === 'regression') renderRegression(result);
  else if (result.chart === 'series') renderSeries(result);
  else if (result.chart === 'clusters') renderClusters(result);
  else if (result.chart === 'bar') renderBar(result);
  else if (result.chart === 'heatmap') renderHeatmap(result);
  else throw new Error('result.chart 必须是 regression、series、clusters、bar 或 heatmap');
}

function renderRegression(result) {
  const scale = scales(result.x, [...result.y, ...result.prediction]);
  const ordered = result.x.map((x, index) => ({x, y: result.prediction[index]})).sort((a, b) => a.x - b.x);
  const path = ordered.map((point, index) => `${index ? 'L' : 'M'}${scale.x(point.x)},${scale.y(point.y)}`).join(' ');
  labChart.append(svgElement('path', {d: path, class: 'lab-result-line'}));
  result.x.forEach((x, index) => {
    labChart.append(svgElement('circle', {cx: scale.x(x), cy: scale.y(result.y[index]), r: 6, class: 'lab-result-point'}));
  });
}

function renderSeries(result) {
  const allValues = result.series.flatMap((series) => series.values);
  const scale = scales(result.x, allValues);
  result.series.forEach((series, seriesIndex) => {
    const path = result.x.map((x, index) => `${index ? 'L' : 'M'}${scale.x(x)},${scale.y(series.values[index])}`).join(' ');
    labChart.append(svgElement('path', {
      d: path,
      class: 'lab-series-line',
      style: `stroke:${chartColors[seriesIndex % chartColors.length]}`
    }));
    const legend = svgElement('text', {
      x: 70 + seriesIndex * 145,
      y: 28,
      class: 'lab-legend',
      style: `fill:${chartColors[seriesIndex % chartColors.length]}`
    });
    legend.textContent = `● ${series.name}`;
    labChart.append(legend);
  });
}

function renderClusters(result) {
  const centers = result.centers || [];
  const referenceX = result.reference?.x || [];
  const referenceY = result.reference?.y || [];
  const allX = [...result.x, ...centers.map((center) => center[0]), ...referenceX];
  const allY = [...result.y, ...centers.map((center) => center[1]), ...referenceY];
  const scale = scales(allX, allY);

  if (referenceX.length) {
    const path = referenceX.map((x, index) => `${index ? 'L' : 'M'}${scale.x(x)},${scale.y(referenceY[index])}`).join(' ');
    labChart.append(svgElement('path', {d: path, class: 'lab-reference-line'}));
  }

  result.x.forEach((x, index) => {
    labChart.append(svgElement('circle', {
      cx: scale.x(x), cy: scale.y(result.y[index]), r: 7,
      class: `lab-cluster-point cluster-${(result.labels?.[index] || 0) % 5}`
    }));
  });
  centers.forEach((center, index) => {
    const marker = svgElement('text', {
      x: scale.x(center[0]), y: scale.y(center[1]) + 7,
      class: `lab-center cluster-${index % 5}`
    });
    marker.textContent = '×';
    labChart.append(marker);
  });
}

function renderBar(result) {
  const series = result.series || [];
  const allValues = series.flatMap((item) => item.values);
  const minValue = Math.min(0, ...allValues);
  const maxValue = Math.max(1, ...allValues);
  const left = 62;
  const top = 54;
  const width = 542;
  const height = 226;
  const groupWidth = width / result.labels.length;
  const barWidth = Math.min(38, groupWidth * 0.72 / Math.max(series.length, 1));
  const valueY = (value) => top + (maxValue - value) / (maxValue - minValue || 1) * height;
  const zeroY = valueY(0);

  series.forEach((item, seriesIndex) => {
    item.values.forEach((value, index) => {
      const x = left + index * groupWidth + groupWidth / 2
        + (seriesIndex - (series.length - 1) / 2) * (barWidth + 3) - barWidth / 2;
      const y = Math.min(valueY(value), zeroY);
      const rect = svgElement('rect', {
        x, y, width: barWidth, height: Math.max(1, Math.abs(zeroY - valueY(value))),
        rx: 3, class: 'lab-bar', style: `fill:${chartColors[seriesIndex % chartColors.length]}`
      });
      labChart.append(rect);
    });

    if (series.length > 1) {
      const legend = svgElement('text', {
        x: 68 + seriesIndex * 145, y: 27, class: 'lab-legend',
        style: `fill:${chartColors[seriesIndex % chartColors.length]}`
      });
      legend.textContent = `■ ${item.name}`;
      labChart.append(legend);
    }
  });

  result.labels.forEach((label, index) => {
    const caption = svgElement('text', {
      x: left + index * groupWidth + groupWidth / 2,
      y: 309,
      class: 'lab-bar-label'
    });
    caption.textContent = String(label).length > 8 ? `${String(label).slice(0, 8)}…` : label;
    labChart.append(caption);
  });
}

function renderHeatmap(result) {
  const matrix = result.matrix || [];
  const rows = matrix.length;
  const columns = matrix[0]?.length || 0;
  if (!rows || !columns) throw new Error('热力图矩阵不能为空');
  const values = matrix.flat();
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const left = 122;
  const top = 42;
  const width = 470;
  const height = 242;
  const cellWidth = width / columns;
  const cellHeight = height / rows;

  matrix.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      const ratio = (value - minValue) / (maxValue - minValue || 1);
      labChart.append(svgElement('rect', {
        x: left + columnIndex * cellWidth,
        y: top + rowIndex * cellHeight,
        width: cellWidth,
        height: cellHeight,
        rx: 2,
        class: 'lab-heat-cell',
        style: `fill:hsl(${226 - ratio * 190} 72% ${93 - ratio * 43}%)`
      }));
    });
  });

  const rowLabels = result.rowLabels || Array.from({length: rows}, (_, index) => index + 1);
  const columnLabels = result.colLabels || Array.from({length: columns}, (_, index) => index + 1);
  rowLabels.forEach((label, index) => {
    const text = svgElement('text', {x: left - 9, y: top + (index + 0.57) * cellHeight, class: 'lab-heat-label', 'text-anchor': 'end'});
    text.textContent = label;
    labChart.append(text);
  });
  columnLabels.forEach((label, index) => {
    const text = svgElement('text', {x: left + (index + 0.5) * cellWidth, y: top - 10, class: 'lab-heat-label', 'text-anchor': 'middle'});
    text.textContent = label;
    labChart.append(text);
  });
}

document.querySelectorAll('[data-open-lab]').forEach((link) => {
  link.addEventListener('click', () => selectLab(link.dataset.openLab, {reveal: true}));
});

labReset.addEventListener('click', () => selectLab(activeLab));

labDownload.addEventListener('click', () => {
  const example = labById.get(activeLab);
  const blob = new Blob([labCode.value], {type: 'text/x-python;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${example?.id || 'traffic-lab'}.py`;
  link.click();
  URL.revokeObjectURL(url);
});

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

if (activeLab) selectLab(activeLab, {reveal: true});
