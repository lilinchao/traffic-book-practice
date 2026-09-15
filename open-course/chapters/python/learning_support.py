"""I/O and display helpers. Model fitting stays visible in the chapter notebooks."""
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd


def locate_root():
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p/'chapters/data').is_dir() and (p/'projects/data').is_dir():
            return p
    raise FileNotFoundError('Run inside the extracted course kit (chapters and projects together).')


def metrics(actual, predicted):
    a, p = np.asarray(actual, float), np.asarray(predicted, float)
    if a.shape != p.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(p).all():
        raise ValueError('Expected matching nonempty finite arrays')
    d = p-a
    return dict(n=int(a.size), MAE=float(np.mean(abs(d))), RMSE=float(np.sqrt(np.mean(d*d))), bias=float(np.mean(d)))


def csv_file(path, columns, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f); writer.writerow(columns); writer.writerows(rows)
    return path


def primary(root, chapter, files, config, outputs):
    key = f'ch{chapter:02}'
    protocol = json.loads((root/'chapters/data/project-protocols.json').read_text(encoding='utf-8'))[key]
    versions = {}
    for p in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'statsmodels', 'matplotlib']:
        try:
            versions[p] = importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:
            pass
    result = dict(schema='traffic-primary-v1', chapter=chapter, protocol=protocol['id'],
                  inputs={p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},
                  config=config, outputs=outputs, versions=versions)
    path = root/'outputs'/key/f'{key}_primary.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    print('Primary submission:', path)
    return result


def prediction_rows(ids, predictions):
    return [[str(ident), name, float(value)] for name, values in predictions.items() for ident, value in zip(ids, values)]


def predictions_table(ids, predictions):
    return dict(columns=['id', 'model', 'prediction'], rows=prediction_rows(ids, predictions))


def metric_table(actual, predictions):
    return pd.DataFrame([{'model': name, **metrics(actual, p)} for name, p in predictions.items()])


def report(root, chapter, title, evidence, questions):
    """Export measured evidence without writing an invented student's interpretation."""
    output = root/'outputs'/f'ch{chapter:02}'/'engineering_report.md'
    rows = ['# '+title, '', '这是本次运行的证据记录，待学生补充工程解释；不是已通过验收的报告。', '']
    for name, value in evidence.items():
        rows += ['## '+name, '', str(value), '']
    for q in questions:
        rows += ['## '+q, '', '待填写：请引用本次具体结果、配置和失败样例。', '']
    rows += ['## 复现与责任', '', '附工作本修改、协议、输入哈希及原始输出。不得将提供方标注或预先生成的参考结果冒充本组人工调查。', '']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(rows), encoding='utf-8')
    return output


def save_plot(root, chapter, name):
    import matplotlib.pyplot as plt
    path = root/'outputs'/f'ch{chapter:02}'/(name+'.svg')
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(path); plt.show(); plt.close()
    print(path)


def lag_design(matrix, p):
    matrix = np.asarray(matrix, float)
    if not isinstance(p, int) or p < 1 or p >= len(matrix):
        raise ValueError('Invalid lag')
    return np.array([matrix[t-p:t][::-1].reshape(-1) for t in range(p, len(matrix))]), matrix[p:]


def fit_lag(matrix, p, multi=True):
    """Small lag helper; notebook exposes X, y and the fitted coefficients."""
    from sklearn.linear_model import LinearRegression
    x, y = lag_design(matrix, p)
    if multi:
        model = LinearRegression().fit(x, y)
        return model, lambda past: model.predict(past[-p:][::-1].reshape(1, -1))[0]
    n = matrix.shape[1]
    models = [LinearRegression().fit(x[:, j::n], y[:, j]) for j in range(n)]
    return models, lambda past: np.array([m.predict(past[-p:, j][::-1].reshape(1, -1))[0] for j, m in enumerate(models)])
