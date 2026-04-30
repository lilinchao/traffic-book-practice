"""
第三章 数理理论基础 —— 实践练习参考实现

运行方式：python math_practice.py
"""

import numpy as np
from scipy import stats


# ============================================================
# 1. 数值微分与交通速度变化率
# ============================================================

def generate_speed_series(n_points: int = 288, seed: int = 42) -> np.ndarray:
    """
    生成模拟的 24 小时交通速度时间序列。

    参数：
        n_points: 时间点数（默认 288，对应 5 分钟间隔）
        seed: 随机种子

    返回：
        speed: 形状 (n_points,) 的速度数组 (km/h)

    模式设计：
        - 凌晨：自由流速度约 100 km/h
        - 早高峰 (7:00-9:00)：速度下降至约 40 km/h
        - 中午：恢复至约 80 km/h
        - 晚高峰 (17:00-19:00)：速度下降至约 50 km/h
        - 夜间：恢复至自由流
    """
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 24, n_points)  # 时间轴（小时）

    # 基础自由流速度
    base_speed = 100.0

    # 早高峰下降：7-9 点，用高斯形下降
    morning_dip = 60.0 * np.exp(-0.5 * ((t - 8.0) / 0.8) ** 2)

    # 晚高峰下降：17-19 点
    evening_dip = 50.0 * np.exp(-0.5 * ((t - 18.0) / 1.0) ** 2)

    # 叠加噪声
    noise = rng.normal(0, 3.0, n_points)

    speed = base_speed - morning_dip - evening_dip + noise
    # 确保速度不为负
    speed = np.clip(speed, 10.0, None)

    return speed


def forward_diff(y: np.ndarray, h: float = 1.0) -> np.ndarray:
    """
    前向差分计算数值导数。

    参数：
        y: 输入序列，形状 (n,)
        h: 时间步长

    返回：
        dy: 前向差分结果，形状 (n-1,)
    """
    return (y[1:] - y[:-1]) / h


def central_diff(y: np.ndarray, h: float = 1.0) -> np.ndarray:
    """
    中心差分计算数值导数。

    参数：
        y: 输入序列，形状 (n,)
        h: 时间步长

    返回：
        dy: 中心差分结果，形状 (n-2,)
    """
    return (y[2:] - y[:-2]) / (2 * h)


def find_extreme_changes(speed: np.ndarray, h: float = 1.0, top_k: int = 3):
    """
    找出速度变化率最大的时刻。

    参数：
        speed: 速度序列
        h: 时间步长
        top_k: 返回前 k 个极值

    返回：
        indices: 变化率绝对值最大的时刻索引
        rates: 对应的变化率值
    """
    rates = central_diff(speed, h)
    abs_rates = np.abs(rates)
    # 中心差分的结果索引偏移了 1，对应原始序列的 1..n-2
    top_indices_in_diff = np.argsort(abs_rates)[-top_k:][::-1]
    # 映射回原始序列索引（中心差分第 i 个元素对应原始序列第 i+1 个）
    original_indices = top_indices_in_diff + 1
    return original_indices, rates[top_indices_in_diff]


# ============================================================
# 2. 概率分布与交通事故计数
# ============================================================

def generate_poisson_data(lam: float = 5.0, size: int = 1000, seed: int = 42) -> np.ndarray:
    """
    生成泊松分布的事故计数数据。

    参数：
        lam: 泊松分布参数 lambda
        size: 样本量
        seed: 随机种子

    返回：
        data: 形状 (size,) 的计数数组
    """
    rng = np.random.default_rng(seed)
    return rng.poisson(lam, size=size)


def generate_nb_data(r: float = 5.0, p: float = 0.5, size: int = 1000, seed: int = 42) -> np.ndarray:
    """
    生成负二项分布的事故计数数据。

    scipy 和 numpy 的负二项分布参数约定：
    nbinom(n, p) 表示成功 n 次前失败次数的分布。

    参数：
        r: 负二项分布的成功次数参数
        p: 负二项分布的成功概率参数
        size: 样本量
        seed: 随机种子

    返回：
        data: 形状 (size,) 的计数数组
    """
    rng = np.random.default_rng(seed)
    return rng.negative_binomial(r, p, size=size)


def fit_poisson(data: np.ndarray) -> float:
    """
    用极大似然估计拟合泊松分布。

    参数：
        data: 计数数据

    返回：
        lam_hat: 估计的 lambda 值
    """
    return float(np.mean(data))


def fit_negative_binomial(data: np.ndarray):
    """
    用极大似然估计拟合负二项分布。

    使用矩估计法：
    mu = mean(data)
    var = var(data)
    n = mu^2 / (var - mu)   (当 var > mu)
    p = n / (n + mu)

    参数：
        data: 计数数据

    返回：
        n_hat: 估计的形状参数 n
        p_hat: 估计的成功概率参数 p
    """
    mu = np.mean(data)
    var = np.var(data, ddof=1)
    if var <= mu:
        # 没有过度离散，退化为泊松
        n_hat = 1e6  # 很大的 n 近似泊松
        p_hat = n_hat / (n_hat + mu)
    else:
        n_hat = mu ** 2 / (var - mu)
        p_hat = n_hat / (n_hat + mu)
    return n_hat, p_hat


def compare_distributions(data: np.ndarray) -> dict:
    """
    对同一组数据分别拟合泊松和负二项分布，比较拟合效果。

    参数：
        data: 计数数据

    返回：
        result: 字典，包含：
            - poisson_lambda: 泊松估计
            - nb_n, nb_p: 负二项估计
            - poisson_chi2_stat: 泊松卡方统计量
            - nb_chi2_stat: 负二项卡方统计量
            - overdispersion: 过度离散统计量 (variance / mean - 1)
    """
    mu = np.mean(data)
    var = np.var(data, ddof=1)

    # 泊松拟合
    lam_hat = fit_poisson(data)

    # 负二项拟合
    n_hat, p_hat = fit_negative_binomial(data)

    # 计算卡方拟合优度
    max_val = int(data.max()) + 1
    observed = np.bincount(data.astype(int), minlength=max_val).astype(float)

    # 合并尾部使期望频数 >= 5（卡方检验要求）
    def chi2_stat(prob_func, observed_full):
        """计算卡方统计量，合并尾部。"""
        expected = np.array([prob_func(k) * len(data) for k in range(len(observed_full))])
        # 合并尾部
        obs_merged, exp_merged = [], []
        running_obs, running_exp = 0.0, 0.0
        for o, e in zip(observed_full, expected):
            running_obs += o
            running_exp += e
            if running_exp >= 5.0:
                obs_merged.append(running_obs)
                exp_merged.append(running_exp)
                running_obs, running_exp = 0.0, 0.0
        # 把剩余的合并到最后一个桶
        if running_obs > 0 or running_exp > 0:
            if len(obs_merged) > 0:
                obs_merged[-1] += running_obs
                exp_merged[-1] += running_exp
            else:
                obs_merged.append(running_obs)
                exp_merged.append(running_exp)
        obs_arr = np.array(obs_merged)
        exp_arr = np.array(exp_merged)
        # 避免除以零
        mask = exp_arr > 0
        chi2 = np.sum((obs_arr[mask] - exp_arr[mask]) ** 2 / exp_arr[mask])
        return chi2

    poisson_dist = stats.poisson(lam_hat)
    poisson_chi2 = chi2_stat(poisson_dist.pmf, observed)

    nb_dist = stats.nbinom(n_hat, p_hat)
    nb_chi2 = chi2_stat(nb_dist.pmf, observed)

    overdispersion = var / mu - 1.0

    return {
        "poisson_lambda": lam_hat,
        "nb_n": n_hat,
        "nb_p": p_hat,
        "poisson_chi2_stat": poisson_chi2,
        "nb_chi2_stat": nb_chi2,
        "overdispersion": overdispersion,
    }


# ============================================================
# 3. 矩阵运算与速度矩阵
# ============================================================

def generate_speed_matrix(n_hours: int = 24, n_detectors: int = 10, seed: int = 42) -> np.ndarray:
    """
    生成模拟的速度矩阵 V（时间 x 检测器）。

    参数：
        n_hours: 小时数（行数）
        n_detectors: 检测器数（列数）
        seed: 随机种子

    返回：
        V: 形状 (n_hours, n_detectors) 的速度矩阵

    模式设计：
        - 行模式：早晚高峰速度下降
        - 列模式：不同检测器有不同的基础速度
        - 叠加噪声
    """
    rng = np.random.default_rng(seed)
    hours = np.arange(n_hours)

    # 行模式：每个小时有一个速度折扣因子（高峰期速度低）
    # 早高峰 7-9 点，晚高峰 17-19 点
    time_pattern = np.ones(n_hours)
    time_pattern -= 0.5 * np.exp(-0.5 * ((hours - 8) / 1.0) ** 2)
    time_pattern -= 0.4 * np.exp(-0.5 * ((hours - 18) / 1.0) ** 2)

    # 列模式：每个检测器有不同的基础速度
    base_speeds = rng.uniform(70, 110, n_detectors)

    # 构造矩阵：V[t, d] = base_speeds[d] * time_pattern[t] + noise
    V = base_speeds[np.newaxis, :] * time_pattern[:, np.newaxis]
    V += rng.normal(0, 3.0, (n_hours, n_detectors))

    # 确保速度合理
    V = np.clip(V, 15.0, None)

    return V


def compute_row_means(V: np.ndarray) -> np.ndarray:
    """
    计算速度矩阵的行均值（每小时全网平均速度）。

    参数：
        V: 速度矩阵，形状 (T, D)

    返回：
        row_means: 形状 (T,) 的时间平均速度
    """
    return V.mean(axis=1)


def compute_col_means(V: np.ndarray) -> np.ndarray:
    """
    计算速度矩阵的列均值（每个检测器的日平均速度）。

    参数：
        V: 速度矩阵，形状 (T, D)

    返回：
        col_means: 形状 (D,) 的检测器平均速度
    """
    return V.mean(axis=0)


def svd_low_rank_approx(V: np.ndarray, k: int) -> np.ndarray:
    """
    用 SVD 低秩近似重建速度矩阵。

    参数：
        V: 速度矩阵，形状 (T, D)
        k: 保留的奇异值个数

    返回：
        V_k: 低秩近似矩阵，形状 (T, D)
    """
    U, S, Vt = np.linalg.svd(V, full_matrices=False)
    # 只保留前 k 个奇异值
    S_k = np.zeros_like(S)
    S_k[:k] = S[:k]
    V_k = U @ np.diag(S_k) @ Vt
    return V_k


def reconstruction_error(V: np.ndarray, V_k: np.ndarray) -> float:
    """
    计算低秩近似的 Frobenius 范数重建误差。

    参数：
        V: 原始矩阵
        V_k: 近似矩阵

    返回：
        error: ||V - V_k||_F / ||V||_F
    """
    numerator = np.linalg.norm(V - V_k, 'fro')
    denominator = np.linalg.norm(V, 'fro')
    if denominator == 0:
        return 0.0
    return numerator / denominator


# ============================================================
# 4. 梯度下降与线性回归
# ============================================================

def generate_regression_data(n_samples: int = 200, n_features: int = 1, seed: int = 42):
    """
    生成模拟的线性回归交通数据。

    参数：
        n_samples: 样本数
        n_features: 特征数
        seed: 随机种子

    返回：
        X: 形状 (n_samples, n_features) 的特征矩阵
        y: 形状 (n_samples,) 的目标值
        true_w: 真实权重
        true_b: 真实偏置
    """
    rng = np.random.default_rng(seed)
    true_w = rng.uniform(2.0, 8.0, n_features)
    true_b = rng.uniform(10.0, 30.0)
    X = rng.uniform(0, 10, (n_samples, n_features))
    noise = rng.normal(0, 5.0, n_samples)
    y = X @ true_w + true_b + noise
    return X, y, true_w, true_b


def mse_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    计算均方误差损失。

    参数：
        y_true: 真实值
        y_pred: 预测值

    返回：
        loss: MSE 值
    """
    return float(np.mean((y_true - y_pred) ** 2))


def gradient_descent(X: np.ndarray, y: np.ndarray,
                     lr: float = 0.01, n_epochs: int = 200):
    """
    批量梯度下降求解线性回归。

    参数：
        X: 特征矩阵，形状 (n, p)
        y: 目标值，形状 (n,)
        lr: 学习率
        n_epochs: 迭代轮数

    返回：
        w: 学习到的权重，形状 (p,)
        b: 学习到的偏置
        losses: 每轮损失列表
    """
    n, p = X.shape
    w = np.zeros(p)
    b = 0.0
    losses = []

    for epoch in range(n_epochs):
        # 前向传播
        y_pred = X @ w + b

        # 计算损失
        loss = mse_loss(y, y_pred)
        losses.append(loss)

        # 计算梯度
        error = y_pred - y
        grad_w = (2.0 / n) * (X.T @ error)
        grad_b = (2.0 / n) * np.sum(error)

        # 更新参数
        w = w - lr * grad_w
        b = b - lr * grad_b

    return w, b, losses


def analytical_solution(X: np.ndarray, y: np.ndarray):
    """
    用正规方程求解线性回归的解析解。

    参数：
        X: 特征矩阵，形状 (n, p)
        y: 目标值，形状 (n,)

    返回：
        w: 解析解权重
        b: 解析解偏置
    """
    n = X.shape[0]
    # 在 X 前面加一列 1 来求解偏置
    X_aug = np.column_stack([np.ones(n), X])
    # lstsq 返回 (x, residuals, rank, sv)
    params, _, _, _ = np.linalg.lstsq(X_aug, y, rcond=None)
    b = params[0]
    w = params[1:]
    return w, b


# ============================================================
# 5. 时间序列划分与评价指标
# ============================================================

def time_series_split(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.8):
    """
    按时间顺序划分训练集和测试集。

    参数：
        X: 特征矩阵，形状 (n, p)，按时间顺序排列
        y: 目标值，形状 (n,)
        train_ratio: 训练集比例

    返回：
        X_train, X_test, y_train, y_test
    """
    n = X.shape[0]
    split_idx = int(n * train_ratio)
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    return X_train, X_test, y_train, y_test


def random_split(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.8, seed: int = 42):
    """
    随机打乱后划分训练集和测试集（用于对比，展示数据泄露问题）。

    参数：
        X: 特征矩阵
        y: 目标值
        train_ratio: 训练集比例
        seed: 随机种子

    返回：
        X_train, X_test, y_train, y_test
    """
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    indices = rng.permutation(n)
    split_idx = int(n * train_ratio)
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算 MAE。"""
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算 RMSE。"""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-8) -> float:
    """
    计算 MAPE。

    参数：
        epsilon: 防止除以零的小量

    返回：
        mape: 百分比值
    """
    return float(np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + epsilon))) * 100)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    综合计算所有评价指标。

    返回：
        metrics: {"MAE": ..., "RMSE": ..., "MAPE": ...}
    """
    return {
        "MAE": compute_mae(y_true, y_pred),
        "RMSE": compute_rmse(y_true, y_pred),
        "MAPE": compute_mape(y_true, y_pred),
    }


# ============================================================
# 主函数：运行所有练习
# ============================================================

def main():
    print("=" * 60)
    print("第三章 数理理论基础 —— 实践练习")
    print("=" * 60)

    # --- 1. 数值微分 ---
    print("\n--- 1. 数值微分与交通速度变化率 ---")
    speed = generate_speed_series()
    fd = forward_diff(speed, h=1.0)
    cd = central_diff(speed, h=1.0)
    print(f"速度序列长度: {len(speed)}")
    print(f"前向差分长度: {len(fd)}")
    print(f"中心差分长度: {len(cd)}")
    indices, rates = find_extreme_changes(speed)
    print(f"变化率最大的时刻索引: {indices}")
    print(f"对应变化率: {rates}")
    # 交通解读
    n_points = len(speed)
    hours_at_indices = indices * 24.0 / n_points
    print(f"对应时刻（约）: {hours_at_indices.round(1)} 点")
    print("解读: 变化率最大的时刻对应拥堵开始或消散的转折点")

    # --- 2. 概率分布 ---
    print("\n--- 2. 概率分布与交通事故计数 ---")
    poisson_data = generate_poisson_data(lam=5.0)
    nb_data = generate_nb_data(r=5.0, p=0.5)
    lam_hat = fit_poisson(poisson_data)
    n_hat, p_hat = fit_negative_binomial(nb_data)
    print(f"泊松数据拟合 lambda_hat: {lam_hat:.4f} (真实值: 5.0)")
    print(f"负二项数据拟合 n_hat: {n_hat:.4f}, p_hat: {p_hat:.4f}")
    print(f"负二项数据均值: {np.mean(nb_data):.2f}, 方差: {np.var(nb_data, ddof=1):.2f}")
    result = compare_distributions(nb_data)
    print(f"分布比较结果:")
    for k, v in result.items():
        print(f"  {k}: {v:.4f}")
    print("解读: 负二项数据的过度离散统计量 > 0，说明泊松拟合不足，负二项更适合")

    # --- 3. 矩阵运算 ---
    print("\n--- 3. 矩阵运算与速度矩阵 ---")
    V = generate_speed_matrix()
    row_means = compute_row_means(V)
    col_means = compute_col_means(V)
    print(f"速度矩阵形状: {V.shape}")
    print(f"矩阵秩: {np.linalg.matrix_rank(V)}")
    print(f"每小时平均速度范围: [{row_means.min():.1f}, {row_means.max():.1f}] km/h")
    print(f"各检测器平均速度范围: [{col_means.min():.1f}, {col_means.max():.1f}] km/h")

    U, S, Vt = np.linalg.svd(V, full_matrices=False)
    print(f"奇异值: {S[:5].round(2)} ...")
    for k in [1, 2, 3, 5]:
        V_k = svd_low_rank_approx(V, k)
        err = reconstruction_error(V, V_k)
        print(f"  k={k} 重建误差: {err:.4f}, 累计方差解释比: {np.sum(S[:k]**2)/np.sum(S**2):.4f}")
    print("解读: k=1 捕获主模式（早晚高峰），k=2-3 补充细节，k 增大收益递减")

    # --- 4. 梯度下降 ---
    print("\n--- 4. 梯度下降与线性回归 ---")
    X, y, true_w, true_b = generate_regression_data()
    print(f"真实参数: w={true_w}, b={true_b:.4f}")
    for lr in [0.001, 0.01, 0.1]:
        w, b, losses = gradient_descent(X, y, lr=lr, n_epochs=200)
        print(f"lr={lr:>5}: 最终损失={losses[-1]:.4f}, w={np.round(w, 4)}, b={b:.4f}")
    w_ana, b_ana = analytical_solution(X, y)
    print(f"解析解:   w={np.round(w_ana, 4)}, b={b_ana:.4f}")
    print("解读: lr=0.001 收敛慢，lr=0.01 收敛适中，lr=0.1 可能震荡或发散")

    # --- 5. 数据划分与评价指标 ---
    print("\n--- 5. 时间序列划分与评价指标 ---")
    X_ts, y_ts, _, _ = generate_regression_data(n_samples=365)

    # 时间序列划分
    X_train, X_test, y_train, y_test = time_series_split(X_ts, y_ts)
    print(f"时间划分: 训练 {X_train.shape[0]} 天, 测试 {X_test.shape[0]} 天")
    w, b, _ = gradient_descent(X_train, y_train, lr=0.01, n_epochs=500)
    y_pred = X_test @ w + b
    metrics = evaluate_predictions(y_test, y_pred)
    print(f"时间划分指标: {metrics}")

    # 随机划分（对比）
    X_train_r, X_test_r, y_train_r, y_test_r = random_split(X_ts, y_ts)
    w_r, b_r, _ = gradient_descent(X_train_r, y_train_r, lr=0.01, n_epochs=500)
    y_pred_r = X_test_r @ w_r + b_r
    metrics_r = evaluate_predictions(y_test_r, y_pred_r)
    print(f"随机划分指标: {metrics_r}")
    print("解读: 随机划分可能导致数据泄露，测试误差通常偏低")

    # 指标在不同流量水平下的行为
    print("\n--- 指标行为分析 ---")
    y_true_demo = np.array([5.0, 8.0, 10.0, 50.0, 80.0, 100.0])
    y_pred_demo = np.array([10.0, 12.0, 13.0, 55.0, 85.0, 105.0])
    for yt, yp in zip(y_true_demo, y_pred_demo):
        abs_err = abs(yt - yp)
        pct_err = abs(yt - yp) / abs(yt) * 100
        print(f"  真实={yt:>5.0f}, 预测={yp:>5.0f}, "
              f"绝对误差={abs_err:.0f}, 百分比误差={pct_err:.1f}%")
    print("解读: 低流量时同样的绝对偏差导致更大的百分比误差，MAPE 在低流量时不稳定")

    print("\n" + "=" * 60)
    print("所有练习完成！")


if __name__ == "__main__":
    main()
