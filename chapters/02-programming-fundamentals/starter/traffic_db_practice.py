"""
第二章 编程实践基础 — 交通数据库操作（起始代码）

任务：完成以下 TODO 部分，使用 SQLite 创建交通数据库并进行基本查询。

数据源：data/raw/nyc_traffic_volume_counts_sample.csv
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Book/
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "nyc_traffic_volume_counts_sample.csv"
DB_PATH = PROJECT_ROOT / "data" / "results" / "traffic.db"

# ── 小时列名映射 ─────────────────────────────────────────
HOUR_COLUMNS = {
    "_12_00_1_00_am": 0, "_1_00_2_00am": 1, "_2_00_3_00am": 2,
    "_3_00_4_00am": 3, "_4_00_5_00am": 4, "_5_00_6_00am": 5,
    "_6_00_7_00am": 6, "_7_00_8_00am": 7, "_8_00_9_00am": 8,
    "_9_00_10_00am": 9, "_10_00_11_00am": 10, "_11_00_12_00pm": 11,
    "_12_00_1_00pm": 12, "_1_00_2_00pm": 13, "_2_00_3_00pm": 14,
    "_3_00_4_00pm": 15, "_4_00_5_00pm": 16, "_5_00_6_00pm": 17,
    "_6_00_7_00pm": 18, "_7_00_8_00pm": 19, "_8_00_9_00pm": 20,
    "_9_00_10_00pm": 21, "_10_00_11_00pm": 22, "_11_00_12_00am": 23,
}


def create_database(db_path: str) -> sqlite3.Connection:
    """创建数据库并建表。

    TODO: 创建以下三张表：
      - road_segment(segment_id, roadway_name, from_street, to_street, direction)
      - detector(detector_id, segment_id, install_date, status)
      - traffic_flow(flow_id, segment_id, date, hour, volume)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # TODO: 编写 CREATE TABLE 语句
    # cursor.executescript("""...""")
    raise NotImplementedError("请完成建表操作")

    conn.commit()
    return conn


def import_data(conn: sqlite3.Connection, csv_path: str) -> None:
    """从 CSV 导入数据到数据库。

    TODO:
      1. 读取 CSV
      2. 提取不重复路段，插入 road_segment
      3. 将宽表转为长表（使用 pd.melt）
      4. 批量插入 traffic_flow
    """
    df = pd.read_csv(csv_path)

    # TODO: 插入路段数据
    raise NotImplementedError("请完成数据导入")

    # TODO: 宽表转长表并插入流量数据
    raise NotImplementedError("请完成数据导入")


def basic_queries(conn: sqlite3.Connection) -> None:
    """执行基本查询并打印结果。

    TODO: 完成以下查询：
      1. 查询 segment_id = 15540 的所有流量记录
      2. 查询 2015 年之后的流量记录
      3. 统计每个路段的记录条数
    """
    # TODO: 编写 SQL 查询
    raise NotImplementedError("请完成基本查询")


def main() -> None:
    """主函数：创建数据库 → 导入数据 → 执行查询。"""
    print("=" * 60)
    print("第二章 交通数据库操作练习")
    print("=" * 60)

    # 创建数据库
    print("\n[1] 创建数据库...")
    conn = create_database(str(DB_PATH))

    # 导入数据
    print("\n[2] 导入数据...")
    import_data(conn, str(DATA_PATH))

    # 执行查询
    print("\n[3] 执行基本查询...")
    basic_queries(conn)

    # 关闭连接
    conn.close()
    print("\n完成！数据库保存在:", DB_PATH)


if __name__ == "__main__":
    main()
