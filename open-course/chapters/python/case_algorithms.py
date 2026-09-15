"""Reproduce chapter 4-8 case algorithms on the distributed real snapshots.

Run from open-course: python chapters/python/case_algorithms.py --chapter all
No data download, test-set tuning, or browser training is performed.
"""
import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from sklearn.cluster import DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.neighbors import KernelDensity
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'chapters/data/algorithms'


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def metrics(y, prediction):
    error = np.asarray(prediction) - np.asarray(y)
    return [len(error), float(np.mean(np.abs(error))),
            float(np.sqrt(np.mean(error ** 2))), float(np.mean(error))]


def table(title, columns, rows, note=''):
    return dict(title=title, columns=columns, rows=rows, note=note)


def result(chapter, inputs, protocol, cases, details):
    import statsmodels
    return dict(chapter=chapter, edition='2026-09-15-algorithms',
                versions=dict(numpy=np.__version__, scipy=scipy.__version__,
                              sklearn=sklearn.__version__, statsmodels=statsmodels.__version__),
                inputs={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs},
                protocol=protocol, cases=cases, details=details)


def regression():
    import statsmodels.api as sm
    inputs = ['chapters/data/ch04_' + p + '.csv' for p in ['train', 'validation', 'test', 'solution']]
    train, valid, test, truth = [pd.read_csv(ROOT / p) for p in inputs]
    assert test.id.is_unique and truth.id.is_unique and set(test.id) == set(truth.id)
    numeric = ['temp', 'atemp', 'hum', 'windspeed']
    categorical = ['mnth', 'hr', 'holiday', 'weekday', 'weathersit']
    # Drop redundant season/workingday encodings; fit reference levels on training only.
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False), categorical)])
    x = sm.add_constant(transform.fit_transform(train), has_constant='add')
    xv = sm.add_constant(transform.transform(valid), has_constant='add')
    xt = sm.add_constant(transform.transform(test), has_constant='add')
    y = train.cnt.to_numpy(dtype=float)
    assert np.linalg.matrix_rank(x) == x.shape[1]
    models = {'OLS': sm.OLS(y, x).fit(), 'Poisson': sm.GLM(y, x, family=sm.families.Poisson()).fit(maxiter=200)}
    candidates = []
    for alpha in [0.05, 0.2, 0.5, 1.0]:
        model = sm.GLM(y, x, family=sm.families.NegativeBinomial(alpha=alpha)).fit(maxiter=200)
        assert model.converged
        score = metrics(valid.cnt, model.predict(xv))
        candidates.append((alpha, model, score))
    chosen = min(candidates, key=lambda c: (c[2][2], c[0]))
    models['NB2'] = chosen[1]
    assert models['Poisson'].converged
    # Test labels are consulted only after the dispersion choice is frozen.
    actual = truth.set_index('id').loc[test.id, 'cnt'].to_numpy(dtype=float)
    predictions = {name: np.maximum(0, model.predict(xt)) for name, model in models.items()}
    summary = [[name, *metrics(actual, pred)] for name, pred in predictions.items()]
    columns = ['模型', '共同小时数', 'MAE（次/小时）', 'RMSE（次/小时）', '偏差（次/小时）']
    periods = []
    for label, mask in [('07—09时', test.hr.isin([7, 8, 9])), ('16—18时', test.hr.isin([16, 17, 18]))]:
        for name, pred in predictions.items():
            periods.append([label, name, *metrics(actual[mask], pred[mask])])
    coef_names = ['intercept', *transform.get_feature_names_out()]
    coefficients = [[name, float(models['Poisson'].params[i]), float(np.exp(models['Poisson'].params[i]))]
                    for i, name in enumerate(coef_names) if name.startswith('numeric')]
    protocol = ('2011训练、2012上半年验证、下半年4376小时测试。统一使用温度、体感温度、湿度、风速及月份、小时、节假日、星期、天气类别；'
                '不使用casual/registered。独热编码删除首类别，预处理只拟合训练集。OLS非负截断；NB2离散参数仅从验证RMSE选择，未报告未经验证的系数因果效应。')
    common = table('多元线性与计数回归：实际重新拟合', columns, summary,
                   '本轮统一精简编码并取消正则惩罚，与旧版岭回归/正则泊松不是相同模型；两套结果分别标示，不作无条件替换。')
    return result(4, inputs, protocol, {
        'bike-leakage': dict(tables=[common, table('泊松模型的连续变量系数', ['标准化变量', '系数β', 'exp(β)'], coefficients,
                                                'exp(β)为其他变量固定时增加一个训练期标准差对应的条件均值比；相关特征会影响解释，不是政策因果效应。')]),
        'poisson-ridge': dict(tables=[table('NB2离散参数验证选择', ['alpha', '验证小时数', '验证MAE', '验证RMSE', '验证偏差'],
                                          [[a, *m] for a, _, m in candidates], f'选定alpha={chosen[0]}；Var(Y|X)=mu+alpha*mu²。alpha是验证选择的超参数，不是联合极大似然估计。'),
                                     common, table('重点时段模型适用性', ['时段', *columns], periods)])},
        dict(selected_alpha=chosen[0], feature_names=coef_names, train_n=len(train), validation_n=len(valid),
             test_rows=[[int(row.id), row.dteday, int(row.hr), float(actual[i]), *[float(predictions[n][i]) for n in models]]
                        for i, row in enumerate(test.itertuples())], prediction_names=list(models)))


def spatial():
    path = 'projects/data/crashes.json'
    records = [r for r in read_json(path)['rows'] if r[7]]
    xy = np.array([[(r[4] + 74.3) * 111320 * np.cos(np.deg2rad(40.73)), (r[3] - 40.45) * 111320] for r in records])
    cells = sorted({tuple(map(int, row)) for row in np.floor(xy / 500)})
    probe = (np.array(cells) + 0.5) * 500
    def density(points, bandwidth):
        return np.exp(KernelDensity(bandwidth=bandwidth, kernel='gaussian').fit(points).score_samples(probe)) * 1e6
    surfaces = {h: density(xy, h) for h in [250, 500, 1000]}
    top = lambda scores: np.argsort(-scores, kind='stable')[:20]
    density_summary = [[h, len(probe), float(v.max()), len(set(top(v)) & set(top(surfaces[500])))] for h, v in surfaces.items()]
    db_rows, memberships = [], {}
    for eps in [150, 350, 700]:
        for minimum in [5, 15]:
            labels = DBSCAN(eps=eps, min_samples=minimum).fit_predict(xy)
            sizes = np.bincount(labels[labels >= 0])
            db_rows.append([eps, minimum, len(sizes), int((labels < 0).sum()), int(sizes.max(initial=0))])
            memberships[f'{eps}-{minimum}'] = labels.tolist()
    rng = np.random.default_rng(42)
    removed_n = int(len(xy) * 0.2)
    masks = {'完整有效点集': np.arange(len(xy)),
             '随机遮盖20%': np.sort(rng.permutation(len(xy))[removed_n:]),
             '东侧集中遮盖20%': np.argsort(xy[:, 0], kind='stable')[:-removed_n]}
    missing_rows, missing_surfaces = [], {}
    for name, keep in masks.items():
        score = density(xy[keep], 500)
        missing_surfaces[name] = score.tolist()
        overlap = len(set(top(score)) & set(top(surfaces[500])))
        missing_rows.append([name, len(keep), len(xy)-len(keep), overlap, float(spearmanr(score, surfaces[500]).statistic)])
    protocol = ('7068个已有有效事故坐标；固定局部米制投影与2069个有记录的500米网格中心作为评价点。'
                'KDE采用高斯核、带宽250/500/1000米，输出概率密度/km²，不是风险。DBSCAN比较6组eps/min_samples。'
                '遮盖实验只隐藏已有坐标，不推测474条真实排除记录的位置；固定探测点防止评价范围随缺失变化。')
    return result(5, [path], protocol, {
        'grid-size': dict(tables=[table('KDE带宽对照', ['带宽（米）', '固定评价点数', '最大密度（1/km²）', '与500米前20点重合数'], density_summary),
                                  table('DBSCAN密度连通分组', ['eps（米）', 'min_samples', '簇数', '噪声点数', '最大簇点数'], db_rows,
                                        'min_samples包含点自身。簇是密度连通组，不能直接命名为危险路段，最大簇也可能由邻近点链式连接形成。')]),
        'no-coordinates': dict(tables=[table('已知坐标遮盖：KDE空间敏感性', ['情境', '保留坐标数', '人为遮盖数', '前20点重合数', '密度排名Spearman相关'], missing_rows,
                                            '20%为明确标记的压力测试参数，不是实测缺失率。仅比较已有有效点集的变化，不恢复原本未知坐标，不把插值用于编造事故位置。')])},
        dict(collision_ids=[r[0] for r in records], xy_m=xy.tolist(), cells=cells,
             kde={str(h): v.tolist() for h, v in surfaces.items()}, masked_kde=missing_surfaces, dbscan=memberships))


def state_forecasts(filtered, targets, horizons):
    """Use filtered (never smoothed) state at t-h; no observations after that origin."""
    ssm = filtered.model.ssm
    transition, design = ssm['transition'], ssm['design']
    intercept = np.asarray(ssm['state_intercept'])
    if intercept.ndim == 1:
        intercept = intercept[:, None]
    obs_intercept = float(np.asarray(ssm['obs_intercept']).ravel()[0])
    output = {}
    for h in horizons:
        state = filtered.filtered_state[:, np.asarray(targets) - h].copy()
        for step in range(h):
            c = intercept if intercept.shape[1] == 1 else intercept[:, np.asarray(targets)-h+step]
            state = transition @ state + c
        output[h] = np.maximum(0, (design @ state).ravel() + obs_intercept)
    return output


def temporal():
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.stats.diagnostic import acorr_ljungbox
    paths = ['projects/data/audit.json', 'projects/data/forecast.json']
    records = read_json(paths[0])['rows']
    source = pd.Series({pd.Timestamp(r[0]): r[1] for r in records}, dtype=float)
    index = pd.date_range('2017-01-01', '2018-09-30T23:00', freq='h')
    series = source.reindex(index) / 1000
    train = series.loc[:'2017-12-31T23:00']
    validation_positions = np.flatnonzero((index >= '2018-01-01') & (index < '2018-07-01') & series.notna())
    definitions = [('ARIMA(2,0,0)', (2, 0, 0), (0, 0, 0, 0)),
                   ('SARIMA(2,0,0)(1,0,0)24', (2, 0, 0), (1, 0, 0, 24))]
    all_results, rows, validations, fits = {}, [], [], {}
    frozen = read_json(paths[1])['horizons']
    common = sorted(set.intersection(*[set(r[0] for r in frozen[str(h)]['rows']) for h in [1, 3, 6]]))
    targets = index.get_indexer(pd.to_datetime(common))
    assert (targets >= 6).all() and series.iloc[targets].notna().all()
    for name, order, seasonal in definitions:
        with warnings.catch_warnings(record=True) as seen:
            fitted = SARIMAX(train, order=order, seasonal_order=seasonal, trend='c').fit(disp=False, maxiter=150)
        if not fitted.mle_retvals['converged']:
            raise RuntimeError(name + ' did not converge')
        filtered = SARIMAX(series, order=order, seasonal_order=seasonal, trend='c').filter(fitted.params)
        predictions = state_forecasts(filtered, targets, [1, 3, 6])
        # Independently check one direct dynamic statsmodels forecast per horizon.
        for h in [1, 3, 6]:
            t = int(targets[20])
            check = filtered.get_prediction(start=t-h+1, end=t, dynamic=True).predicted_mean.iloc[-1]
            assert np.isclose(predictions[h][20], max(0, check), atol=1e-8)
            predictions[h] *= 1000
            rows.append([name, h, *metrics(series.iloc[targets].to_numpy()*1000, predictions[h])])
        vpred = state_forecasts(filtered, validation_positions, [1])[1]*1000
        validations.append([name, *metrics(series.iloc[validation_positions].to_numpy()*1000, vpred)])
        standardized = fitted.filter_results.standardized_forecasts_error[0]
        # Keep a genuinely contiguous training residual segment for diagnostics.
        blocks = pd.Series(standardized, index=train.index).where(train.notna()).iloc[72:]
        longest = max((g.dropna() for _, g in blocks.groupby(blocks.isna().cumsum())), key=len)
        pvalue = float(acorr_ljungbox(longest, lags=[24], model_df=3 if seasonal[0] else 2).lb_pvalue.iloc[0])
        fits[name] = dict(params={str(k): float(v) for k, v in fitted.params.items()},
                          aic=float(fitted.aic), converged=True, warnings=[str(w.message) for w in seen],
                          residual_n=len(longest), ljung_box_lag24_p=pvalue)
        all_results[name] = {str(h): predictions[h].tolist() for h in predictions}
    for method, col in [('上周同期', 4), ('训练期星期小时均值', 5)]:
        for h in [1, 3, 6]:
            mapping = {r[0]: r for r in frozen[str(h)]['rows']}
            pred = np.array([mapping[t][col] for t in common])
            rows.append([method, h, *metrics(series.iloc[targets].to_numpy()*1000, pred)])
    protocol = ('2017年拟合固定ARIMA(2,0,0)及SARIMA(2,0,0)(1,0,0)24；2018上半年报告验证，7—9月在1/3/6小时共同2169个目标评价。'
                '缺测保留NaN，由状态空间模型跳过观测更新；用起点t-h的过滤状态递推，不用平滑状态或未来实测。数值缩放1000后拟合并还原单位。'
                '本轮是在已公开教学测试期复算，不构成从未参与开发的独立部署验证。')
    columns = ['方法', '提前小时', '共同小时数', 'MAE（辆/小时）', 'RMSE（辆/小时）', '偏差（辆/小时）']
    return result(6, paths, protocol, {
        'simple-baseline': dict(tables=[table('ARIMA类模型与周期基线：1小时', columns, [r for r in rows if r[1] == 1]),
                                        table('训练残差诊断', ['模型', 'AIC', '连续残差长度', 'Ljung–Box(24) p值'],
                                              [[n, v['aic'], v['residual_n'], v['ljung_box_lag24_p']] for n, v in fits.items()],
                                              '检验仅针对最长连续训练残差片段，已扣除AR参数自由度。小p值提示剩余自相关，不等于预测完全无效。')]),
        'forecast-origin': dict(tables=[table('同一参数模型的滚动多提前量预测', columns, rows),
                                        table('训练后固定模型的验证期1小时表现', ['方法', *columns[2:]], validations)])},
        dict(targets=common, actual=(series.iloc[targets].to_numpy()*1000).tolist(), predictions=all_results,
             fits=fits, train_hours=len(train), train_missing=int(train.isna().sum()),
             origin_rule='Filtered state at target-h; target observations never included.'))


def autoregression(matrix, order, multivariate):
    xs, ys = [], []
    for t in range(order, len(matrix)):
        xs.append(matrix[t-order:t][::-1].reshape(-1))
        ys.append(matrix[t])
    x, y = np.array(xs), np.array(ys)
    if multivariate:
        model = LinearRegression().fit(x, y)
        return lambda history: model.predict(history[-order:][::-1].reshape(1, -1))[0]
    models = [LinearRegression().fit(x[:, j::matrix.shape[1]], y[:, j]) for j in range(matrix.shape[1])]
    return lambda history: np.array([m.predict(history[-order:, j][::-1].reshape(1, -1))[0] for j, m in enumerate(models)])


def spatiotemporal():
    path = 'projects/data/taxi.json'
    data = read_json(path)['rows']
    names = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx']
    matrix = np.zeros((31*24, len(names)))
    boroughs = sorted({r[1] for r in data})
    profiles = np.zeros((31, len(boroughs)*24))
    for d, b, h, count in data:
        day = int(d[-2:])-1
        profiles[day, boroughs.index(b)*24+h] += count
        if b in names:
            matrix[day*24+h, names.index(b)] += count
    training = matrix[:21*24]
    valid_idx, test_idx = np.arange(21*24, 24*24), np.arange(24*24, 31*24)
    predictions, selection, selected = {}, [], {}
    for name, multi in [('单区域AR', False), ('多区域VAR', True)]:
        trials = []
        for p in [1, 3, 24]:
            predict = autoregression(training, p, multi)
            val = np.maximum(0, np.array([predict(matrix[:t]) for t in valid_idx]))
            score = metrics(matrix[valid_idx].ravel(), val.ravel())
            selection.append([name, p, *score])
            trials.append((score[2], p, predict))
        _, order, predictor = min(trials, key=lambda row: (row[0], row[1]))
        selected[name] = order
        predictions[name] = np.maximum(0, np.array([predictor(matrix[:t]) for t in test_idx]))
    calendar = np.array([training[t%168::168].mean(axis=0) for t in test_idx])
    predictions['历史同期均值'] = calendar
    predictions['上一小时'] = matrix[test_idx-1]
    summary = [[name, *metrics(matrix[test_idx].ravel(), pred.ravel())] for name, pred in predictions.items()]
    nodes = [[b, name, *metrics(matrix[test_idx, j], pred[:, j])] for j, b in enumerate(names) for name, pred in predictions.items()]
    proportions = profiles/profiles.sum(axis=1, keepdims=True)
    cluster_rows, members, centers = [], {}, {}
    for k in [2, 3, 4, 5]:
        baseline = None
        for seed in [42, 7, 19]:
            model = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(proportions)
            if baseline is None:
                baseline = model.labels_
            cluster_rows.append([k, seed, float(silhouette_score(proportions, model.labels_)), float(adjusted_rand_score(baseline, model.labels_)), int(np.bincount(model.labels_).min())])
            members[f'{k}-{seed}'] = model.labels_.tolist()
            centers[f'{k}-{seed}'] = model.cluster_centers_.tolist()
    protocol = ('TLC 2024年1月真实聚合。预测预先选Manhattan/Brooklyn/Queens/Bronx四区域，排除低频Staten Island及非行政区EWR/Unknown；'
                '1—21日训练，22—24日选AR/VAR滞后1/3/24，25—31日672个区域小时共同评价。逐时使用已到达历史，不重训。'
                '聚类独立使用全月7类地区×24小时日内占比，比较K=2/3/4/5和三个种子，不能将全月聚类用于上述留出预测。')
    columns = ['方法', '区域小时数', 'MAE（条/小时）', 'RMSE（条/小时）', '偏差（条/小时）']
    return result(7, [path], protocol, {
        'weekday-denominator': dict(tables=[table('分时运营量：单区域与多区域预测', columns, summary),
                                            table('各区域的共同时间评价', ['区域', *columns], nodes),
                                            table('滞后阶数的验证选择', ['方法', '滞后p', *columns[1:]], selection)]),
        'similar-days': dict(tables=[table('时空画像KMeans与跨种子稳定性', ['K', '种子', '样本内轮廓系数', '相对种子42的ARI', '最小簇日期数'], cluster_rows,
                                          'ARI比较成员配对，不受簇编号互换影响；跨种子稳定不等于跨月份稳定，也不是预测准确率。')])},
        dict(nodes=names, selected_lags=selected, test_hour_indices=test_idx.tolist(), actual=matrix[test_idx].tolist(),
             predictions={k: v.tolist() for k, v in predictions.items()}, full_matrix=matrix.tolist(),
             profile_totals=profiles.sum(axis=1).tolist(), profile_boroughs=boroughs, profile_shares=proportions.tolist(), memberships=members, centers=centers))


def associate(frames, mode, gate=5.0, max_age=1.5):
    """Inputs contain only (time, Nx2 positions); source IDs never enter association."""
    tracks, assignments, serial = {}, [], 0
    h = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=float)
    for time, positions in frames:
        tracks = {k: v for k, v in tracks.items() if time-v['observed'] <= max_age}
        ids = sorted(tracks)
        for track in tracks.values():
            dt = time-track['time']
            f = np.eye(4); f[0, 2] = dt; f[1, 3] = dt
            if mode == 'kalman':
                g = np.array([[dt*dt/2, 0], [0, dt*dt/2], [dt, 0], [0, dt]])
                track['x'] = f @ track['x']
                track['p'] = f @ track['p'] @ f.T + 4.0*g@g.T
            track['time'] = time
        cost = cdist(np.array([tracks[k]['x'][:2] for k in ids]), positions) if ids and len(positions) else np.empty((len(ids), len(positions)))
        matches = []
        if cost.size:
            # Augmented dummies allow unmatched tracks/detections instead of invalid forced pairs.
            n, m = cost.shape
            augmented = np.full((n+m, n+m), 1e6)
            augmented[:n, :m] = np.where(cost <= gate, cost, 1e6)
            augmented[np.arange(n), m+np.arange(n)] = gate+1
            augmented[n+np.arange(m), np.arange(m)] = gate+1
            augmented[n:, m:] = 0
            rr, cc = linear_sum_assignment(augmented)
            matches = [(i, j) for i, j in zip(rr, cc) if i < n and j < m and cost[i, j] <= gate]
        assigned = {}
        for i, j in matches:
            ident = ids[i]; track = tracks[ident]
            if mode == 'kalman':
                gain = track['p'] @ h.T @ np.linalg.inv(h @ track['p'] @ h.T + np.eye(2)*0.25)
                track['x'] += gain @ (positions[j] - h @ track['x'])
                ikh = np.eye(4)-gain@h
                track['p'] = ikh @ track['p'] @ ikh.T + gain @ (np.eye(2)*0.25) @ gain.T
            else:
                track['x'][:2] = positions[j]
            track['observed'] = time; assigned[j] = ident
        for j, point in enumerate(positions):
            if j not in assigned:
                serial += 1; assigned[j] = serial
                tracks[serial] = dict(x=np.array([*point, 0, 0], dtype=float), p=np.diag([0.25, 0.25, 100., 100.]), time=time, observed=time)
        assignments.append([assigned[j] for j in range(len(positions))])
    return assignments


def count_events(rows):
    previous, counted, events = {}, set(), []
    for ident, time, x, y in sorted(rows, key=lambda r: (r[1], str(r[0]))):
        side = -1 if x < 14.7 else 1 if x > 15.3 else 0
        last = previous.get(ident)
        if last and time-last[0] > 1.5:
            last = None
        if last and side and last[1] and side != last[1] and (ident, side) not in counted:
            counted.add((ident, side)); events.append([ident, time, '+x' if side > 0 else '-x'])
        previous[ident] = (time, side or (last[1] if last else 0))
    return events


def tracking():
    path = 'projects/data/sind.json'
    raw = read_json(path)['rows']
    times = sorted({r[1] for r in raw})
    by_time = {t: [] for t in times}
    for row in raw:
        by_time[row[1]].append(row)
    summary, counter, detail = [], [], {}
    for stride in [1, 5, 10]:
        kept = times[::stride]
        rng = np.random.default_rng(42)
        ordered = [[by_time[t][i] for i in rng.permutation(len(by_time[t]))] for t in kept]
        frames = [(t/1000, np.array([[r[2], r[3]] for r in rows])) for t, rows in zip(kept, ordered)]
        reference = [[r[0], r[1]/1000, r[2], r[3]] for rows in ordered for r in rows]
        reference_events = count_events(reference)
        for mode in ['position', 'kalman']:
            labels = associate(frames, mode)
            last_track, last_source, correct, total, switches = {}, {}, 0, 0, 0
            predicted, audit = [], []
            for source_rows, assigned in zip(ordered, labels):
                for row, ident in zip(source_rows, assigned):
                    source, time = str(row[0]), row[1]/1000
                    if ident in last_track and time-last_track[ident][1] <= 1.5:
                        total += 1; correct += last_track[ident][0] == source
                    if source in last_source and time-last_source[source][1] <= 1.5 and last_source[source][0] != ident:
                        switches += 1
                    last_track[ident] = (source, time); last_source[source] = (ident, time)
                    predicted.append([ident, time, row[2], row[3]])
                    audit.append([source, ident, time, row[2], row[3]])
            events = count_events(predicted)
            summary.append([stride, mode, len(audit), len({r[1] for r in audit}), total, correct, correct/total if total else None, switches])
            counter.append([stride, mode, len(reference_events), len(events), sum(e[2]=='+x' for e in events), sum(e[2]=='-x' for e in events), len(events)-len(reference_events)])
            detail[f'{stride}-{mode}'] = dict(assignments=audit, events=events, reference_events=reference_events)
    protocol = ('SinD天津120秒平滑坐标，逐帧打乱顺序并隐藏源ID；算法只读时间和x/y，不读源ID或未来坐标。'
                '比较位置保持+匈牙利与常速度卡尔曼+匈牙利，门限5米，最长保留1.5秒；量测协方差0.25I，过程加速度方差4。'
                '这是SORT关联思想的地面点简化实现，不是完整SORT、YOLO或DeepSORT；源ID仅用于重关联核查，并非独立人工视频真值。')
    tables = [table('跨帧身份重关联的实证结果', ['采样步长', '关联方法', '坐标点数', '生成轨迹数', '可核对关联对', '源ID一致对', '一致比例', '源轨迹ID变化次数'], summary,
                    '一致比例按新轨迹相邻观测对核查源ID。ID变化次数为相邻源观测间新ID改变的自定义审计量，不冒称标准MOTA/IDF1。'),
              table('重关联误差向通行计数的传递', ['采样步长', '关联方法', '同采样源ID事件', '新ID事件', '+x事件', '−x事件', '事件总数差'], counter,
                    '计数在测得位置而非滤波位置上执行，只改变身份关联，隔离关联影响。相同总数仍可能对应不同车辆，不能称为计数准确率。')]
    return result(8, [path], protocol, {'crossing-rule': dict(tables=[tables[1], tables[0]]),
                                      'trajectory-not-video': dict(tables=tables)}, detail)


FUNCTIONS = {'4': regression, '5': spatial, '6': temporal, '7': spatiotemporal, '8': tracking}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapter', choices=['all', *FUNCTIONS], default='all')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for chapter in FUNCTIONS if args.chapter == 'all' else [args.chapter]:
        print('Running chapter', chapter, flush=True)
        with threadpool_limits(limits=1):
            out = FUNCTIONS[chapter]()
        (args.output / f'ch{chapter}.json').write_text(json.dumps(out, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
        print('Completed', chapter, [(k, len(v['tables'])) for k, v in out['cases'].items()], flush=True)


if __name__ == '__main__':
    main()
