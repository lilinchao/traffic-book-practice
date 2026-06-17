(() => {
  let labExamplesValue = window.LAB_EXAMPLES;
  let variantsLoaded = false;

  Object.defineProperty(window, 'LAB_EXAMPLES', {
    configurable: true,
    get() {
      return labExamplesValue;
    },
    set(value) {
      labExamplesValue = value;
      if (!Array.isArray(value) || variantsLoaded) return;
      variantsLoaded = true;
      const request = new XMLHttpRequest();
      request.open('GET', 'assets/lab-variants.js?v=2', false);
      request.send(null);
      if (request.status >= 200 && request.status < 400) {
        (0, eval)(request.responseText);
      }
    }
  });
})();

const menuButton = document.querySelector('.menu-button');
const sidebar = document.querySelector('.sidebar');

menuButton.addEventListener('click', () => {
  const open = sidebar.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
});

document.querySelectorAll('.sidebar a').forEach((link) => {
  link.addEventListener('click', () => sidebar.classList.remove('open'));
});

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall back for browsers that block clipboard access on local pages.
    }
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  textarea.remove();
}

document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copyTarget);
    await copyText(target.innerText);
    const original = button.textContent;
    button.textContent = '已复制';
    setTimeout(() => { button.textContent = original; }, 1400);
  });
});

const sections = [...document.querySelectorAll('main [id]')];
const navLinks = [...document.querySelectorAll('.sidebar a')];
const observer = new IntersectionObserver((entries) => {
  const visible = entries
    .filter((entry) => entry.isIntersecting)
    .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  navLinks.forEach((link) => link.classList.toggle('active', link.hash === `#${visible.target.id}`));
}, { rootMargin: '-18% 0px -68% 0px', threshold: [0, 0.2, 0.5] });
sections.forEach((section) => observer.observe(section));

const demandSeries = {
  weekday: {
    values: [28, 18, 12, 9, 14, 38, 106, 230, 352, 205, 144, 160, 182, 175, 166, 178, 242, 390, 446, 312, 208, 142, 92, 54, 34],
    insight: '早晚高峰形成两个清晰峰值。'
  },
  weekend: {
    values: [34, 24, 17, 12, 10, 18, 34, 62, 104, 162, 214, 258, 292, 310, 304, 286, 265, 244, 218, 184, 148, 112, 80, 55, 38],
    insight: '周末需求向午后集中，峰值更加平缓。'
  }
};

const chartLine = document.getElementById('chart-line');
const chartArea = document.getElementById('chart-area');
const chartPoints = document.getElementById('chart-points');
const chartInsight = document.getElementById('chart-insight');
const chartTooltip = document.getElementById('chart-tooltip');
const chartWrap = document.querySelector('.chart-wrap');
const chartWidth = 560;
const chartHeight = 230;
const chartLeft = 54;
const chartTop = 40;
const maxDemand = 480;

function pointFor(value, index, count) {
  return {
    x: chartLeft + (index / (count - 1)) * chartWidth,
    y: chartTop + chartHeight - (value / maxDemand) * chartHeight
  };
}

function drawDemandChart(seriesName) {
  const series = demandSeries[seriesName];
  const points = series.values.map((value, index) => pointFor(value, index, series.values.length));
  const line = points.map((point, index) => `${index ? 'L' : 'M'}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ');
  chartLine.setAttribute('d', line);
  chartArea.setAttribute('d', `${line} L${points.at(-1).x},270 L${points[0].x},270 Z`);
  chartPoints.replaceChildren();

  points.forEach((point, index) => {
    if (index % 2 && index !== series.values.length - 1) return;
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('class', 'chart-point');
    circle.setAttribute('cx', point.x);
    circle.setAttribute('cy', point.y);
    circle.setAttribute('r', 3.5);
    circle.setAttribute('tabindex', '0');
    circle.setAttribute('aria-label', `${index}时，需求指数 ${series.values[index]}`);
    const showTooltip = () => {
      const svgRect = document.getElementById('demand-chart').getBoundingClientRect();
      const wrapRect = chartWrap.getBoundingClientRect();
      chartTooltip.innerHTML = `<strong>${index}:00</strong><br>需求指数 ${series.values[index]}`;
      chartTooltip.hidden = false;
      chartTooltip.style.left = `${svgRect.left - wrapRect.left + point.x / 640 * svgRect.width}px`;
      chartTooltip.style.top = `${svgRect.top - wrapRect.top + point.y / 310 * svgRect.height}px`;
      circle.classList.add('active');
    };
    const hideTooltip = () => {
      chartTooltip.hidden = true;
      circle.classList.remove('active');
    };
    circle.addEventListener('mouseenter', showTooltip);
    circle.addEventListener('focus', showTooltip);
    circle.addEventListener('mouseleave', hideTooltip);
    circle.addEventListener('blur', hideTooltip);
    chartPoints.appendChild(circle);
  });

  chartInsight.textContent = series.insight;
}

document.querySelectorAll('.chart-toggle').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.chart-toggle').forEach((item) => {
      const active = item === button;
      item.classList.toggle('active', active);
      item.setAttribute('aria-pressed', String(active));
    });
    drawDemandChart(button.dataset.series);
  });
});

const matrix = document.getElementById('matrix-visual');
const matrixValues = [2,3,4,5,5,4,3,2,2,3,4,6,7,6,4,3,2,2,3,4,5,7,8,7,5,3,2,3,3,4,6,8,9,8,6,4,3,3,4,5,7,9,9,8,7,5,4,4,5,6,7,8,8,7,6,5];
matrixValues.forEach((value) => {
  const cell = document.createElement('i');
  cell.style.setProperty('--o', (0.12 + value / 11).toFixed(2));
  matrix.appendChild(cell);
});

drawDemandChart('weekday');
