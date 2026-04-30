"""
第 5 章实践：交通空间与位置数据分析 —— 完整解答
==================================================

本文件包含完整的空间分析流程：
1. 加载 NYC 碰撞数据，创建 GeoDataFrame
2. 坐标系检查与变换（EPSG:4326 → EPSG:32618）
3. 行政区级空间权重矩阵（Queen 邻接、K 近邻）
4. 全局与局部 Moran's I 空间自相关检验
5. DBSCAN 聚类识别事故热点
6. KDE 核密度估计检测事故黑点
7. 空间回归（OLS → 残差 Moran's I → SLM/SEM）

数据：
- 纽约市碰撞事故样本：../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv
- 区级月度面板：../../data/processed/nyc_crash_borough_month_panel_2023.csv
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from shapely.geometry import Point, Polygon, MultiPolygon

# 空间分析包
from libpysal.weights import Queen, KNN, DistanceBand
from esda.moran import Moran, Moran_Local
from sklearn.cluster import DBSCAN
from sklearn.neighbors import KernelDensity
import statsmodels.api as sm

# 尝试导入 spreg（空间回归），如不可用则提供降级提示
try:
    from spreg import OLS as SpregOLS, GM_Lag, GM_Error
    HAS_SPREG = True
except ImportError:
    HAS_SPREG = False
    print("警告：spreg 未安装，空间回归部分将使用 statsmodels OLS 替代。")
    print("安装方式：pip install spreg")

plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# ============================================================
# 第 1 步：加载数据
# ============================================================

def load_crash_data(filepath: str) -> pd.DataFrame:
    """读取 NYC 碰撞事故 CSV 数据。"""
    df = pd.read_csv(filepath)
    print(f"[1] 原始数据行数: {len(df)}")
    print(f"    字段: {list(df.columns)}")
    print(f"    各行政区记录数:\n{df['borough'].value_counts()}")
    return df


def load_panel_data(filepath: str) -> pd.DataFrame:
    """读取区级月度面板数据。"""
    df = pd.read_csv(filepath)
    print(f"[1] 面板数据行数: {len(df)}")
    print(f"    行政区: {df['borough'].unique().tolist()}")
    print(f"    月份范围: {sorted(df['month'].unique())}")
    return df


# ============================================================
# 第 2 步：创建点级 GeoDataFrame
# ============================================================

def create_point_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """从含经纬度的 DataFrame 创建点级 GeoDataFrame。"""
    # 去除缺失经纬度的记录
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()
    # 转换为数值类型
    df_clean["latitude"] = pd.to_numeric(df_clean["latitude"], errors="coerce")
    df_clean["longitude"] = pd.to_numeric(df_clean["longitude"], errors="coerce")
    df_clean = df_clean.dropna(subset=["latitude", "longitude"])
    # 排除坐标为 0 的记录
    df_clean = df_clean[(df_clean["latitude"] != 0) & (df_clean["longitude"] != 0)]

    print(f"[2] 有效坐标记录数: {len(df_clean)} / {len(df)}")

    gdf = gpd.GeoDataFrame(
        df_clean,
        geometry=gpd.points_from_xy(df_clean["longitude"], df_clean["latitude"]),
        crs="EPSG:4326",
    )
    return gdf


# ============================================================
# 第 3 步：坐标系检查与变换
# ============================================================

def check_and_transform_crs(gdf: gpd.GeoDataFrame, target_epsg: int = 32618) -> gpd.GeoDataFrame:
    """检查 CRS 并转换到目标投影坐标系（UTM Zone 18N）。"""
    print(f"[3] 当前 CRS: {gdf.crs}")
    print(f"    目标 CRS: EPSG:{target_epsg}")

    # 打印变换前坐标（WGS84，单位为度）
    print(f"    变换前（度）前 3 行:")
    for idx in range(min(3, len(gdf))):
        print(f"      {gdf.geometry.iloc(idx).x:.6f}, {gdf.geometry.iloc(idx).y:.6f}" if idx < len(gdf) else "")

    gdf_proj = gdf.to_crs(epsg=target_epsg)

    # 打印变换后坐标（UTM，单位为米）
    print(f"    变换后（米）前 3 行:")
    for idx in range(min(3, len(gdf_proj))):
        print(f"      {gdf_proj.geometry.iloc[idx].x:.1f}, {gdf_proj.geometry.iloc[idx].y:.1f}")

    return gdf_proj


# ============================================================
# 第 4 步：行政区级 GeoDataFrame
# ============================================================

# 纽约市五个行政区的大致质心坐标（WGS84）
BOROUGH_CENTROIDS = {
    "MANHATTAN": (-73.9712, 40.7831),
    "BRONX": (-73.8648, 40.8448),
    "BROOKLYN": (-73.9442, 40.6782),
    "QUEENS": (-73.7949, 40.7282),
    "STATEN ISLAND": (-74.1502, 40.5795),
}

# 行政区邻接关系（Queen 邻接）
BOROUGH_NEIGHBORS = {
    "MANHATTAN": ["BRONX", "BROOKLYN", "QUEENS"],
    "BRONX": ["MANHATTAN"],
    "BROOKLYN": ["MANHATTAN", "QUEENS", "STATEN ISLAND"],
    "QUEENS": ["MANHATTAN", "BROOKLYN"],
    "STATEN ISLAND": ["BROOKLYN"],
}

# 纽约市五个行政区的简化多边形坐标（WGS84，近似边界）
BOROUGH_POLYGONS = {
    "MANHATTAN": [(-74.02, 40.70), (-74.02, 40.88), (-73.97, 40.88),
                  (-73.93, 40.80), (-73.97, 40.70)],
    "BRONX": [(-73.93, 40.80), (-73.93, 40.92), (-73.80, 40.92),
              (-73.77, 40.87), (-73.83, 40.80)],
    "BROOKLYN": [(-74.04, 40.57), (-74.04, 40.74), (-73.96, 40.74),
                 (-73.86, 40.70), (-73.86, 40.57)],
    "QUEENS": [(-73.96, 40.54), (-73.96, 40.74), (-73.86, 40.70),
               (-73.70, 40.73), (-73.70, 40.54)],
    "STATEN ISLAND": [(-74.25, 40.50), (-74.25, 40.65), (-74.08, 40.65),
                      (-74.08, 40.50)],
}


def create_borough_gdf(panel_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """创建行政区级 GeoDataFrame，包含年度汇总的碰撞数据。"""
    # 按行政区汇总年度数据
    borough_annual = panel_df.groupby("borough").agg(
        total_crashes=("crashes", "sum"),
        total_injured=("persons_injured", "sum"),
        total_killed=("persons_killed", "sum"),
    ).reset_index()

    # 构建多边形几何
    polygons = []
    for borough in borough_annual["borough"]:
        coords = BOROUGH_POLYGONS.get(borough)
        if coords:
            polygons.append(Polygon(coords))
        else:
            # 如果没有预定义多边形，使用质心缓冲
            centroid = BOROUGH_CENTROIDS.get(borough, (-73.9, 40.7))
            polygons.append(Point(centroid).buffer(0.01))

    gdf = gpd.GeoDataFrame(
        borough_annual,
        geometry=polygons,
        crs="EPSG:4326",
    )

    # 计算碰撞率（每平方公里）
    gdf_proj = gdf.to_crs(epsg=32618)
    gdf["area_km2"] = gdf_proj.geometry.area / 1e6
    gdf["crash_rate"] = gdf["total_crashes"] / gdf["area_km2"]

    print(f"[4] 行政区级 GeoDataFrame:")
    print(gdf[["borough", "total_crashes", "total_killed", "area_km2", "crash_rate"]].to_string(index=False))

    return gdf


# ============================================================
# 第 5 步：空间权重矩阵
# ============================================================

def build_spatial_weights(borough_gdf: gpd.GeoDataFrame):
    """构建 Queen 邻接权重矩阵和 K 近邻权重矩阵。"""
    # --- Queen 邻接权重 ---
    # 由于只有 5 个行政区且使用简化多边形，部分多边形可能不相邻
    # 使用手动定义的邻接关系构建权重矩阵
    boroughs = borough_gdf["borough"].tolist()
    n = len(boroughs)
    neighbors = {i: [] for i in range(n)}
    weights_dict = {i: [] for i in range(n)}

    for i, b in enumerate(boroughs):
        for nb in BOROUGH_NEIGHBORS.get(b, []):
            if nb in boroughs:
                j = boroughs.index(nb)
                neighbors[i].append(j)
                weights_dict[i].append(1.0)

    from libpysal.weights import W
    w_queen = W(neighbors, weights_dict)
    w_queen.transform = "r"  # 行标准化

    print(f"[5] Queen 邻接权重矩阵:")
    print(f"    行政区: {boroughs}")
    print(f"    邻接关系: { {boroughs[i]: [boroughs[j] for j in neighbors[i]] for i in range(n)} }")
    print(f"    非零元素比例: {w_queen.pct_nonzero:.1f}%")
    print(f"    平均连接数: {w_queen.mean_neighbors:.1f}")

    # --- K 近邻权重 ---
    # 使用质心坐标构建 KNN 权重
    centroids = np.array([BOROUGH_CENTROIDS[b] for b in boroughs])
    centroid_gdf = gpd.GeoDataFrame(
        {"borough": boroughs},
        geometry=gpd.points_from_xy(centroids[:, 0], centroids[:, 1]),
        crs="EPSG:4326",
    )
    w_knn = KNN.from_dataframe(centroid_gdf, k=3)
    w_knn.transform = "r"

    print(f"\n[5] K 近邻权重矩阵 (K=3):")
    print(f"    非零元素比例: {w_knn.pct_nonzero:.1f}%")
    print(f"    平均连接数: {w_knn.mean_neighbors:.1f}")

    return w_queen, w_knn


# ============================================================
# 第 6 步：全局 Moran's I
# ============================================================

def global_morans_i(borough_gdf: gpd.GeoDataFrame, w):
    """计算全局 Moran's I 并绘制 Moran 散点图。"""
    y = borough_gdf["crash_rate"].values
    moran = Moran(y, w)

    print(f"[6] 全局 Moran's I 检验:")
    print(f"    Moran's I = {moran.I:.4f}")
    print(f"    期望值 E[I] = {moran.EI:.4f}")
    print(f"    z 统计量 = {moran.z_sim:.4f}")
    print(f"    p 值 = {moran.p_sim:.4f}")

    if moran.p_sim < 0.05:
        if moran.I > 0:
            print(f"    结论: 碰撞率存在显著空间正相关（高值与高值聚集、低值与低值聚集）")
        else:
            print(f"    结论: 碰撞率存在显著空间负相关（高值与低值交替分布）")
    else:
        print(f"    结论: 碰撞率在空间上呈随机分布，未检测到显著空间自相关")

    # Moran 散点图
    fig, ax = plt.subplots(figsize=(8, 6))
    wy = w.sparse.dot(y)  # 空间滞后
    ax.scatter(y, wy, c="steelblue", s=80, edgecolors="k", zorder=3)
    # 拟合线
    b, a = np.polyfit(y, wy, 1)
    x_line = np.linspace(y.min(), y.max(), 100)
    ax.plot(x_line, a + b * x_line, "r--", linewidth=1.5, label=f"斜率 = {b:.4f}")
    # 参考线
    ax.axhline(y.mean(), color="gray", linestyle=":", linewidth=0.8)
    ax.axvline(y.mean(), color="gray", linestyle=":", linewidth=0.8)
    # 标注行政区
    for i, borough in enumerate(borough_gdf["borough"]):
        ax.annotate(borough, (y[i], wy[i]), fontsize=8, ha="left", xytext=(5, 5),
                     textcoords="offset points")
    # 象限标注
    ax.text(0.95, 0.95, "HH", transform=ax.transAxes, fontsize=12, ha="right", va="top", color="red")
    ax.text(0.05, 0.05, "LL", transform=ax.transAxes, fontsize=12, ha="left", va="bottom", color="blue")
    ax.text(0.05, 0.95, "HL", transform=ax.transAxes, fontsize=12, ha="left", va="top", color="orange")
    ax.text(0.95, 0.05, "LH", transform=ax.transAxes, fontsize=12, ha="right", va="bottom", color="green")

    ax.set_xlabel("碰撞率")
    ax.set_ylabel("空间滞后碰撞率")
    ax.set_title("Moran 散点图 — 行政区碰撞率")
    ax.legend()
    plt.tight_layout()
    plt.savefig("morans_scatter.png", dpi=150)
    plt.show()
    print("    Moran 散点图已保存为 morans_scatter.png")

    return moran


# ============================================================
# 第 7 步：局部 Moran's I（LISA）
# ============================================================

def local_morans_i(borough_gdf: gpd.GeoDataFrame, w):
    """计算局部 Moran's I（LISA）并绘制聚类图。"""
    y = borough_gdf["crash_rate"].values
    lisa = Moran_Local(y, w, permutations=999)

    # 添加 LISA 结果到 GeoDataFrame
    borough_gdf = borough_gdf.copy()
    borough_gdf["lisa_I"] = lisa.Is
    borough_gdf["lisa_p"] = lisa.p_sim
    borough_gdf["lisa_q"] = lisa.q  # 象限: 1=HH, 2=LH, 3=LL, 4=HL

    # 标记显著区域
    sig = lisa.p_sim < 0.05
    borough_gdf["lisa_sig"] = sig

    # 聚类标签
    labels = {1: "HH（热点）", 2: "LH", 3: "LL（冷点）", 4: "HL"}
    borough_gdf["lisa_label"] = "不显著"
    for i in range(len(borough_gdf)):
        if sig[i]:
            borough_gdf.loc[borough_gdf.index[i], "lisa_label"] = labels.get(lisa.q[i], "?")

    print(f"[7] 局部 Moran's I（LISA）:")
    for _, row in borough_gdf.iterrows():
        sig_str = "*" if row["lisa_sig"] else ""
        print(f"    {row['borough']}: I={row['lisa_I']:.4f}, "
              f"p={row['lisa_p']:.4f}{sig_str}, "
              f"象限={row['lisa_q']}, {row['lisa_label']}")

    # LISA 聚类图
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = {"HH（热点）": "red", "LL（冷点）": "blue", "HL": "orange",
              "LH": "lightgreen", "不显著": "#eeeeee"}
    borough_gdf["color"] = borough_gdf["lisa_label"].map(colors)
    borough_gdf.plot(ax=ax, color=borough_gdf["color"], edgecolor="black", linewidth=1)
    # 标注
    for _, row in borough_gdf.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(f"{row['borough']}\n{row['lisa_label']}",
                    (centroid.x, centroid.y), fontsize=8, ha="center",
                    fontweight="bold")
    # 图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, edgecolor="black", label=l)
                       for l, c in colors.items() if l in borough_gdf["lisa_label"].values]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=9)
    ax.set_title("LISA 聚类图 — 行政区碰撞率")
    plt.tight_layout()
    plt.savefig("lisa_cluster.png", dpi=150)
    plt.show()
    print("    LISA 聚类图已保存为 lisa_cluster.png")

    return lisa, borough_gdf


# ============================================================
# 第 8 步：DBSCAN 聚类
# ============================================================

def dbscan_clustering(gdf_proj: gpd.GeoDataFrame, eps: int = 500, min_samples: int = 15):
    """使用 DBSCAN 对碰撞点位进行聚类，识别事故热点。"""
    # 提取投影后的坐标
    coords = np.column_stack([gdf_proj.geometry.x, gdf_proj.geometry.y])

    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    labels = db.labels_

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    print(f"[8] DBSCAN 聚类结果 (eps={eps}m, min_samples={min_samples}):")
    print(f"    聚类数: {n_clusters}")
    print(f"    噪声点数: {n_noise} ({100*n_noise/len(labels):.1f}%)")
    for c in range(n_clusters):
        count = list(labels).count(c)
        print(f"    聚类 {c}: {count} 个点")

    # 添加标签到 GeoDataFrame
    gdf_result = gdf_proj.copy()
    gdf_result["cluster"] = labels

    # 可视化
    fig, ax = plt.subplots(figsize=(12, 9))
    # 噪声点
    noise = gdf_result[gdf_result["cluster"] == -1]
    noise.plot(ax=ax, color="lightgray", markersize=2, alpha=0.3, label="噪声点")
    # 聚类点
    for c in range(n_clusters):
        cluster_pts = gdf_result[gdf_result["cluster"] == c]
        cluster_pts.plot(ax=ax, markersize=4, alpha=0.6,
                         label=f"聚类 {c} ({len(cluster_pts)} 点)")

    ax.set_title(f"DBSCAN 事故热点聚类 (eps={eps}m, min_samples={min_samples})")
    ax.set_xlabel("东移 (m)")
    ax.set_ylabel("北移 (m)")
    ax.legend(fontsize=8, markerscale=2)
    plt.tight_layout()
    plt.savefig("dbscan_clusters.png", dpi=150)
    plt.show()
    print("    DBSCAN 聚类图已保存为 dbscan_clusters.png")

    return gdf_result, db


# ============================================================
# 第 9 步：核密度估计（KDE）
# ============================================================

def kernel_density_estimation(gdf_proj: gpd.GeoDataFrame, bandwidth: int = 500):
    """对碰撞点位进行核密度估计，检测事故黑点。"""
    coords = np.column_stack([gdf_proj.geometry.x, gdf_proj.geometry.y])

    kde = KernelDensity(bandwidth=bandwidth, metric="euclidean").fit(coords)

    # 在网格上评估密度
    xmin, ymin, xmax, ymax = coords[:, 0].min(), coords[:, 1].min(), \
                              coords[:, 0].max(), coords[:, 1].max()
    # 扩展边界
    margin = (xmax - xmin) * 0.05
    xmin -= margin
    xmax += margin
    ymin -= margin
    ymax += margin

    # 网格分辨率
    n_grid = 200
    xx = np.linspace(xmin, xmax, n_grid)
    yy = np.linspace(ymin, ymax, n_grid)
    XX, YY = np.meshgrid(xx, yy)
    grid_coords = np.column_stack([XX.ravel(), YY.ravel()])

    # 计算密度
    log_density = kde.score_samples(grid_coords)
    density = np.exp(log_density).reshape(XX.shape)

    # 黑点阈值：密度 95% 分位数
    threshold = np.percentile(density, 95)

    print(f"[9] 核密度估计 (bandwidth={bandwidth}m):")
    print(f"    密度范围: [{density.min():.6f}, {density.max():.6f}]")
    print(f"    黑点阈值 (95% 分位数): {threshold:.6f}")
    blackspot_pct = 100 * np.sum(density >= threshold) / density.size
    print(f"    黑点区域占比: {blackspot_pct:.1f}%")

    # 可视化
    fig, ax = plt.subplots(figsize=(12, 9))
    im = ax.pcolormesh(XX, YY, density, cmap="YlOrRd", shading="auto")
    # 黑点等高线
    ax.contour(XX, YY, density, levels=[threshold], colors="blue", linewidths=2, linestyles="--")
    # 事故点
    ax.scatter(coords[:, 0], coords[:, 1], s=1, c="black", alpha=0.1)
    plt.colorbar(im, ax=ax, label="碰撞密度")
    ax.set_title(f"碰撞核密度估计与黑点检测 (带宽={bandwidth}m)")
    ax.set_xlabel("东移 (m)")
    ax.set_ylabel("北移 (m)")

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="blue", linestyle="--", linewidth=2, label="黑点边界 (95% 分位数)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="black",
               markersize=4, label="碰撞点", alpha=0.5),
    ]
    ax.legend(handles=legend_elements, loc="upper right")
    plt.tight_layout()
    plt.savefig("kde_blackspot.png", dpi=150)
    plt.show()
    print("    KDE 黑点图已保存为 kde_blackspot.png")

    return kde, density, threshold


# ============================================================
# 第 10 步：空间回归
# ============================================================

def spatial_regression(borough_gdf: gpd.GeoDataFrame, w, panel_df: pd.DataFrame):
    """空间回归分析：OLS → 残差 Moran's I → SLM/SEM。

    由于仅有 5 个行政区，本步骤主要展示分析流程。
    实际研究中应使用更细的空间单元（如网格、交通小区）以获得足够的观测数。
    """
    print(f"[10] 空间回归分析")
    print(f"     注意: 仅有 {len(borough_gdf)} 个行政区，自由度非常有限。")
    print(f"     以下展示完整分析流程，实际研究中建议使用网格或交通小区等更细的空间单元。")

    # 准备回归数据
    y = borough_gdf["crash_rate"].values
    # 使用伤亡比例作为自变量（简单示例）
    borough_gdf["kill_rate"] = borough_gdf["total_killed"] / borough_gdf["total_crashes"]
    X = sm.add_constant(borough_gdf[["kill_rate"]].values)

    # --- OLS 基线模型 ---
    ols_model = sm.OLS(y, X).fit()
    print(f"\n    OLS 回归结果:")
    print(f"    R² = {ols_model.rsquared:.4f}")
    print(f"    调整 R² = {ols_model.rsquared_adj:.4f}")
    print(f"    AIC = {ols_model.aic:.2f}")
    for i, name in enumerate(["const", "kill_rate"]):
        print(f"    {name}: coef={ols_model.params[i]:.4f}, "
              f"p={ols_model.pvalues[i]:.4f}")

    # --- 残差 Moran's I ---
    resid = ols_model.resid
    moran_resid = Moran(resid, w)
    print(f"\n    残差 Moran's I = {moran_resid.I:.4f}, p = {moran_resid.p_sim:.4f}")
    if moran_resid.p_sim < 0.05:
        print(f"    残差存在显著空间自相关 → 需要空间模型")
    else:
        print(f"    残差空间自相关不显著 → OLS 可能已足够")

    # --- SLM / SEM（需要 spreg 包）---
    if HAS_SPREG:
        try:
            # 空间滞后模型 (SLM)
            w_sparse = w.sparse
            slm = GM_Lag(y, X[:, 1:], w=w_sparse, name_y=["crash_rate"],
                         name_x=["kill_rate"], name_w="Queen")
            print(f"\n    SLM 空间滞后模型:")
            print(f"    ρ (空间自回归系数) = {slm.rho:.4f}")
            print(f"    AIC = {slm.aic:.2f}")

            # 空间误差模型 (SEM)
            sem = GM_Error(y, X[:, 1:], w=w_sparse, name_y=["crash_rate"],
                           name_x=["kill_rate"], name_w="Queen")
            print(f"\n    SEM 空间误差模型:")
            print(f"    λ (空间误差系数) = {sem.lam:.4f}")
            print(f"    AIC = {sem.aic:.2f}")

            # 模型比较
            print(f"\n    模型比较:")
            print(f"    {'模型':<8} {'AIC':>10}")
            print(f"    {'OLS':<8} {ols_model.aic:>10.2f}")
            print(f"    {'SLM':<8} {slm.aic:>10.2f}")
            print(f"    {'SEM':<8} {sem.aic:>10.2f}")

            if slm.aic < ols_model.aic and slm.aic < sem.aic:
                print(f"    → SLM 拟合最优")
            elif sem.aic < ols_model.aic:
                print(f"    → SEM 拟合最优")
            else:
                print(f"    → OLS 拟合最优（空间效应可能不显著）")

        except Exception as e:
            print(f"    空间回归模型拟合失败: {e}")
            print(f"    原因可能是观测数过少 (N={len(borough_gdf)})，建议使用更细的空间单元。")
    else:
        print(f"\n    spreg 未安装，跳过 SLM/SEM。")

    print(f"\n    模型选择建议:")
    print(f"    - 若残差 Moran's I 显著 → 需要空间模型")
    print(f"    - 若关注溢出效应 → 优先选择 SLM")
    print(f"    - 若关注遗漏变量 → 优先选择 SEM")
    print(f"    - 实际研究中建议使用 LM-Lag / LM-Error 检验辅助选择")

    return ols_model


# ============================================================
# 第 11 步：综合可视化
# ============================================================

def plot_comprehensive_overview(gdf: gpd.GeoDataFrame, gdf_proj: gpd.GeoDataFrame,
                                borough_gdf: gpd.GeoDataFrame):
    """绘制综合概览图。"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # (a) 事故点分布
    ax = axes[0, 0]
    gdf.plot(ax=ax, column="borough", markersize=2, legend=True, categorical=True,
             legend_kwds={"fontsize": 8, "title": "行政区"})
    ax.set_title("(a) 碰撞事故点分布")

    # (b) 行政区碰撞率分级统计图
    ax = axes[0, 1]
    borough_gdf.plot(ax=ax, column="crash_rate", legend=True, cmap="YlOrRd",
                     edgecolor="black", linewidth=1,
                     legend_kwds={"label": "碰撞率（次/km²）", "shrink": 0.8})
    for _, row in borough_gdf.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(f"{row['borough']}\n{row['crash_rate']:.0f}",
                    (centroid.x, centroid.y), fontsize=7, ha="center")
    ax.set_title("(b) 行政区碰撞率")

    # (c) 投影后的事故点
    ax = axes[1, 0]
    gdf_proj.plot(ax=ax, column="borough", markersize=2, legend=True, categorical=True,
                  legend_kwds={"fontsize": 8, "title": "行政区"})
    ax.set_title("(c) 投影后事故点 (EPSG:32618)")
    ax.set_xlabel("东移 (m)")
    ax.set_ylabel("北移 (m)")

    # (d) 行政区伤亡统计
    ax = axes[1, 1]
    borough_gdf.plot(ax=ax, column="total_killed", legend=True, cmap="Reds",
                     edgecolor="black", linewidth=1,
                     legend_kwds={"label": "死亡人数", "shrink": 0.8})
    for _, row in borough_gdf.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(f"{row['borough']}\n{row['total_killed']}",
                    (centroid.x, centroid.y), fontsize=7, ha="center")
    ax.set_title("(d) 行政区死亡人数")

    plt.suptitle("第 5 章实践 — 交通空间与位置数据分析综合概览", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig("spatial_overview.png", dpi=150)
    plt.show()
    print("[11] 综合概览图已保存为 spatial_overview.png")


# ============================================================
# 主程序
# ============================================================

def main():
    """执行完整的空间分析流程。"""
    print("=" * 70)
    print("第 5 章实践：交通空间与位置数据分析")
    print("=" * 70)

    # 数据路径
    crash_path = "../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv"
    panel_path = "../../data/processed/nyc_crash_borough_month_panel_2023.csv"

    # ---- 第 1 步：加载数据 ----
    crash_df = load_crash_data(crash_path)
    panel_df = load_panel_data(panel_path)

    # ---- 第 2 步：创建点级 GeoDataFrame ----
    crash_gdf = create_point_gdf(crash_df)
    print()

    # ---- 第 3 步：坐标系变换 ----
    crash_gdf_proj = check_and_transform_crs(crash_gdf)
    print()

    # ---- 第 4 步：行政区级 GeoDataFrame ----
    borough_gdf = create_borough_gdf(panel_df)
    print()

    # ---- 第 5 步：空间权重矩阵 ----
    w_queen, w_knn = build_spatial_weights(borough_gdf)
    print()

    # ---- 第 6 步：全局 Moran's I ----
    moran = global_morans_i(borough_gdf, w_queen)
    print()

    # ---- 第 7 步：局部 Moran's I ----
    lisa, borough_gdf_lisa = local_morans_i(borough_gdf, w_queen)
    print()

    # ---- 第 8 步：DBSCAN 聚类 ----
    gdf_dbscan, db = dbscan_clustering(crash_gdf_proj, eps=500, min_samples=15)
    print()

    # ---- 第 9 步：KDE 黑点检测 ----
    kde, density, threshold = kernel_density_estimation(crash_gdf_proj, bandwidth=500)
    print()

    # ---- 第 10 步：空间回归 ----
    ols_model = spatial_regression(borough_gdf_lisa, w_queen, panel_df)
    print()

    # ---- 第 11 步：综合可视化 ----
    plot_comprehensive_overview(crash_gdf, crash_gdf_proj, borough_gdf_lisa)

    print("=" * 70)
    print("分析完成！输出文件：")
    print("  - morans_scatter.png    Moran 散点图")
    print("  - lisa_cluster.png      LISA 聚类图")
    print("  - dbscan_clusters.png   DBSCAN 聚类图")
    print("  - kde_blackspot.png     KDE 黑点检测图")
    print("  - spatial_overview.png  综合概览图")
    print("=" * 70)


if __name__ == "__main__":
    main()
