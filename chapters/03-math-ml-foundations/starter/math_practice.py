"""
第三章 数理理论基础 —— 实践练习起始代码

请完成每个函数中标记了 TODO 的部分。
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
    # TODO: 实现速度序列生成
    # 提示：使用 sin 函数模拟早晚高峰的下降，叠加高斯噪声
    rng = np.random.default_rng(seed)
    speed = np.zeros(n_points)
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
    # TODO: 实现前向差分
    dy = np.array([])
    return dy


def central_diff(y: np.ndarray, h: float = 1.0) -> np.ndarray:
    """
    中心差分计算数值导数。

    参数：
        y: 输入序列，形状 (n,)
        h: 时间步长

    返回：
        dy: 中心差分结果，形状 (n-2,)
    """
    # TODO: 实现中心差分
    dy = np.array([])
    return dy


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
    # TODO: 用中心差分计算变化率，找出绝对值最大的 top_k 个时刻
    indices = np.array([])
    rates = np.array([])
    return indices, rates


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
    # TODO: 用 numpy 生成泊松随机数
    rng = np.random.default_rng(seed)
    data = np.array([])
    return data


def generate_nb_data(r: float = 5.0, p: float = 0.5, size: int = 1000, seed: int = 42) -> np.ndarray:
    """
    生成负二项分布的事故计数数据。

    参数：
        r: 负二项分布的成功次数参数
        p: 负二项分布的成功概率参数
        size: 样本量
        seed: 随机种子

    返回：
        data: 形状 (size,) 的计数数组
    """
    # TODO: 用 numpy 生成负二项随机数
    rng = np.random.default_rng(seed)
    data = np.array([])
    return data


def fit_poisson(data: np.ndarray) -> float:
    """
    用极大似然估计拟合泊松分布。

    参数：
        data: 计数数据

    返回：
        lam_hat: 估计的 lambda 值
    """
    # TODO: 泊松分布 MLE，lambda_hat = sample_mean
    lam_hat = 0.0
    return lam_hat


def fit_negative_binomial(data: np.ndarray):
    """
    用极大似然估计拟合负二项分布。

    参数：
        data: 计数数据

    返回：
        n_hat: 估计的形状参数 n
        p_hat: 估计的成功概率参数 p
    """
    # TODO: 用 scipy.stats.nbinom.fit 或矩估计拟合
    n_hat = 0.0
    p_hat = 0.0
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
    # TODO: 拟合两种分布并比较
    result = {}
    return result


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
    # TODO: 生成速度矩阵
    rng = np.random.default_rng(seed)
    V = np.zeros((n_hours, n_detectors))
    return V


def compute_row_means(V: np.ndarray) -> np.ndarray:
    """
    计算速度矩阵的行均值（每小时全网平均速度）。

    参数：
        V: 速度矩阵，形状 (T, D)

    返回：
        row_means: 形状 (T,) 的时间平均速度
    """
    # TODO: 计算行均值
    row_means = np.array([])
    return row_means


def compute_col_means(V: np.ndarray) -> np.ndarray:
    """
    计算速度矩阵的列均值（每个检测器的日平均速度）。

    参数：
        V: 速度矩阵，形状 (T, D)

    返回：
        col_means: 形状 (D,) 的检测器平均速度
    """
    # TODO: 计算列均值
    col_means = np.array([])
    return col_means


def svd_low_rank_approx(V: np.ndarray, k: int) -> np.ndarray:
    """
    用 SVD 低秩近似重建速度矩阵。

    参数：
        V: 速度矩阵，形状 (T, D)
        k: 保留的奇异值个数

    返回：
        V_k: 低秩近似矩阵，形状 (T, D)
    """
    # TODO: 实现 SVD 低秩近似
    V_k = np.zeros_like(V)
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
    # TODO: 计算 Frobenius 范数相对误差
    error = 0.0
    return error


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
    # TODO: 生成 y = X @ true_w + true_b + noise
    rng = np.random.default_rng(seed)
    X = np.zeros((n_samples, n_features))
    y = np.zeros(n_samples)
    true_w = np.zeros(n_features)
    true_b = 0.0
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
    # TODO: 计算 MSE
    loss = 0.0
    return loss


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
    # TODO: 实现梯度下降
    n, p = X.shape
    w = np.zeros(p)
    b = 0.0
    losses = []
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
    # TODO: 用 numpy.linalg.lstsq 求解析解
    w = np.array([])
    b = 0.0
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
    # TODO: 实现时间序列划分（不能随机打乱！）
    X_train = np.array([])
    X_test = np.array([])
    y_train = np.array([])
    y_test = np.array([])
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
    # TODO: 实现随机划分
    X_train = np.array([])
    X_test = np.array([])
    y_train = np.array([])
    y_test = np.array([])
    return X_train, X_test, y_train, y_test


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算 MAE。"""
    # TODO
    return 0.0


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算 RMSE。"""
    # TODO
    return 0.0


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-8) -> float:
    """
    计算 MAPE。

    参数：
        epsilon: 防止除以零的小量

    返回：
        mape: 百分比值
    """
    # TODO
    return 0.0


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    综合计算所有评价指标。

    返回：
        metrics: {"MAE": ..., "RMSE": ..., "MAPE": ...}
    """
    # TODO
    metrics = {}
    return metrics


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

    # --- 2. 概率分布 ---
    print("\n--- 2. 概率分布与交通事故计数 ---")
    poisson_data = generate_poisson_data(lam=5.0)
    nb_data = generate_nb_data(r=5.0, p=0.5)
    lam_hat = fit_poisson(poisson_data)
    n_hat, p_hat = fit_negative_binomial(nb_data)
    print(f"泊松拟合 lambda_hat: {lam_hat:.4f}")
    print(f"负二项拟合 n_hat: {n_hat:.4f}, p_hat: {p_hat:.4f}")
    result = compare_distributions(nb_data)
    print(f"分布比较结果: {result}")

    # --- 3. 矩阵运算 ---
    print("\n--- 3. 矩阵运算与速度矩阵 ---")
    V = generate_speed_matrix()
    row_means = compute_row_means(V)
    col_means = compute_col_means(V)
    print(f"速度矩阵形状: {V.shape}")
    print(f"每小时平均速度范围: [{row_means.min():.1f}, {row_means.max():.1f}] km/h")
    print(f"各检测器平均速度范围: [{col_means.min():.1f}, {col_means.max():.1f}] km/h")
    for k in [1, 2, 3]:
        V_k = svd_low_rank_approx(V, k)
        err = reconstruction_error(V, V_k)
        print(f"k={k} 重建误差: {err:.4f}")

    # --- 4. 梯度下降 ---
    print("\n--- 4. 梯度下降与线性回归 ---")
    X, y, true_w, true_b = generate_regression_data()
    for lr in [0.001, 0.01, 0.1]:
        w, b, losses = gradient_descent(X, y, lr=lr, n_epochs=200)
        print(f"lr={lr}: 最终损失={losses[-1]:.4f}, w={w}, b={b:.4f}")
    w_ana, b_ana = analytical_solution(X, y)
    print(f"解析解: w={w_ana}, b={b_ana:.4f}")

    # --- 5. 数据划分与评价指标 ---
    print("\n--- 5. 时间序列划分与评价指标 ---")
    X_ts, y_ts, _, _ = generate_regression_data(n_samples=365)
    X_train, X_test, y_train, y_test = time_series_split(X_ts, y_ts)
    print(f"时间划分: 训练 {X_train.shape[0]}, 测试 {X_test.shape[0]}")
    w, b, _ = gradient_descent(X_train, y_train, lr=0.01, n_epochs=200)
    y_pred = X_test @ w + b
    metrics = evaluate_predictions(y_test, y_pred)
    print(f"评价指标: {metrics}")

    print("\n" + "=" * 60)
    print("所有练习完成！")


if __name__ == "__main__":
    main()
