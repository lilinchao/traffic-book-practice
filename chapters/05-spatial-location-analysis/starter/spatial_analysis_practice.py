"""
第 5 章实践：交通空间与位置数据分析 —— 起始模板
==================================================

本文件提供基本的代码框架和部分 TODO 标记。
学生需要根据 practice-guide.md 的指引，补充完成各步骤。

数据：
- 纽约市碰撞事故样本：../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv
- 区级月度面板：../../data/processed/nyc_crash_borough_month_panel_2023.csv
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# 第 1 步：加载数据
# ============================================================

def load_crash_data(filepath: str) -> pd.DataFrame:
    """读取 NYC 碰撞事故 CSV 数据。"""
    df = pd.read_csv(filepath)
    print(f"原始数据行数: {len(df)}")
    print(f"字段: {list(df.columns)}")
    return df


def load_panel_data(filepath: str) -> pd.DataFrame:
    """读取区级月度面板数据。"""
    df = pd.read_csv(filepath)
    print(f"面板数据行数: {len(df)}")
    return df


# ============================================================
# 第 2 步：创建 GeoDataFrame
# ============================================================

def create_point_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """从含经纬度的 DataFrame 创建点级 GeoDataFrame。

    TODO:
    - 去除 latitude 或 longitude 为空的记录
    - 使用 gpd.points_from_xy() 创建点几何
    - 设定 CRS 为 EPSG:4326
    """
    # TODO: 去除缺失经纬度的记录
    # df = df.dropna(subset=["latitude", "longitude"])

    # TODO: 创建 GeoDataFrame
    # gdf = gpd.GeoDataFrame(
    #     df,
    #     geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
    #     crs="EPSG:4326",
    # )
    # return gdf
    raise NotImplementedError("请完成 create_point_gdf 函数")


# ============================================================
# 第 3 步：坐标系检查与变换
# ============================================================

def check_and_transform_crs(gdf: gpd.GeoDataFrame, target_epsg: int = 32618) -> gpd.GeoDataFrame:
    """检查 CRS 并转换到目标投影坐标系。

    TODO:
    - 打印当前 CRS 信息
    - 使用 to_crs() 转换到目标 EPSG
    - 打印转换前后前 5 行坐标对比
    """
    # TODO: 实现
    raise NotImplementedError("请完成 check_and_transform_crs 函数")


# ============================================================
# 第 4 步：简单空间可视化
# ============================================================

def plot_crash_points(gdf: gpd.GeoDataFrame, title: str = "NYC 碰撞事故点分布"):
    """绘制碰撞事故点的基本散点图。

    TODO:
    - 使用 gdf.plot() 绘制点图
    - 按行政区着色
    - 添加标题和图例
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    # TODO: 实现
    # gdf.plot(ax=ax, column="borough", markersize=2, legend=True, categorical=True)
    ax.set_title(title)
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    plt.tight_layout()
    plt.savefig("crash_points.png", dpi=150)
    plt.show()
    print("基础点图已保存为 crash_points.png")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    # 数据路径
    crash_path = "../../data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv"
    panel_path = "../../data/processed/nyc_crash_borough_month_panel_2023.csv"

    # 加载数据
    crash_df = load_crash_data(crash_path)
    panel_df = load_panel_data(panel_path)

    # 创建 GeoDataFrame
    crash_gdf = create_point_gdf(crash_df)

    # 坐标系变换
    crash_gdf_proj = check_and_transform_crs(crash_gdf)

    # 基础可视化
    plot_crash_points(crash_gdf)
