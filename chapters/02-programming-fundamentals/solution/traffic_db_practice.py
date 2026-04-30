"""
第二章 编程实践基础 — 交通数据库操作（参考实现）

功能：使用 SQLite 创建交通数据库，实现建表、数据导入、CRUD、聚合查询与多表连接。
数据源：data/raw/nyc_traffic_volume_counts_sample.csv
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional

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

# ── SQL 建表语句 ─────────────────────────────────────────
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS road_segment (
    segment_id   INTEGER PRIMARY KEY,
    roadway_name TEXT,
    from_street  TEXT,
    to_street    TEXT,
    direction    TEXT
);

CREATE TABLE IF NOT EXISTS detector (
    detector_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id   INTEGER,
    install_date TEXT,
    status       TEXT DEFAULT 'active',
    FOREIGN KEY (segment_id) REFERENCES road_segment(segment_id)
);

CREATE TABLE IF NOT EXISTS traffic_flow (
    flow_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER,
    date       TEXT,
    hour       INTEGER,
    volume     INTEGER,
    FOREIGN KEY (segment_id) REFERENCES road_segment(segment_id)
);
"""


# ══════════════════════════════════════════════════════════
# 1. 数据库创建与建表
# ══════════════════════════════════════════════════════════

def create_database(db_path: str) -> sqlite3.Connection:
    """创建数据库连接并建表。"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript(CREATE_TABLES_SQL)
    conn.commit()
    print(f"  数据库已创建: {db_path}")
    return conn


# ══════════════════════════════════════════════════════════
# 2. 数据导入
# ══════════════════════════════════════════════════════════

def import_data(conn: sqlite3.Connection, csv_path: str) -> None:
    """从 CSV 导入数据到数据库。"""
    df = pd.read_csv(csv_path)
    print(f"  读取 CSV: {df.shape[0]} 行, {df.shape[1]} 列")

    # ── 2a. 提取路段信息并插入 road_segment ───────────────
    segments = (
        df[["segmentid", "roadway_name", "from", "to", "direction"]]
        .drop_duplicates(subset=["segmentid"])
        .rename(columns={
            "segmentid": "segment_id",
            "from": "from_street",
            "to": "to_street",
        })
    )
    segments.to_sql("road_segment", conn, if_exists="append", index=False)
    print(f"  插入路段: {len(segments)} 条")

    # ── 2b. 宽表转长表 ───────────────────────────────────
    hour_cols = list(HOUR_COLUMNS.keys())
    df_long = df.melt(
        id_vars=["id", "segmentid", "roadway_name", "from", "to", "direction", "date"],
        value_vars=hour_cols,
        var_name="hour_col",
        value_name="volume",
    )
    df_long["hour"] = df_long["hour_col"].map(HOUR_COLUMNS)
    df_long["date"] = pd.to_datetime(df_long["date"], format="ISO8601").dt.strftime("%Y-%m-%d")

    # 保留需要的列
    flow_data = df_long[["segmentid", "date", "hour", "volume"]].rename(
        columns={"segmentid": "segment_id"}
    )
    # volume 转整数，NaN 保持为 None
    flow_data["volume"] = pd.to_numeric(flow_data["volume"], errors="coerce").astype("Int64")

    flow_data.to_sql("traffic_flow", conn, if_exists="append", index=False)
    print(f"  插入流量记录: {len(flow_data)} 条")

    # ── 2c. 为每个路段创建虚拟检测器 ─────────────────────
    cursor = conn.cursor()
    for seg_id in segments["segment_id"]:
        cursor.execute(
            "INSERT INTO detector (segment_id, install_date, status) VALUES (?, ?, ?)",
            (int(seg_id), "2010-01-01", "active"),
        )
    conn.commit()
    print(f"  插入检测器: {len(segments)} 条")


# ══════════════════════════════════════════════════════════
# 3. CRUD 操作
# ══════════════════════════════════════════════════════════

def insert_flow(conn: sqlite3.Connection, segment_id: int,
                date: str, hour: int, volume: int) -> int:
    """插入单条流量记录（参数化查询防止 SQL 注入）。"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO traffic_flow (segment_id, date, hour, volume) VALUES (?, ?, ?, ?)",
        (segment_id, date, hour, volume),
    )
    conn.commit()
    return cursor.lastrowid


def update_flow(conn: sqlite3.Connection, flow_id: int, new_volume: int) -> None:
    """更新指定流量记录的 volume 值。"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE traffic_flow SET volume = ? WHERE flow_id = ?",
        (new_volume, flow_id),
    )
    conn.commit()
    print(f"  已更新 flow_id={flow_id}, volume={new_volume}")


def delete_flow(conn: sqlite3.Connection, date: str) -> int:
    """删除指定日期的所有流量记录，返回删除条数。"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM traffic_flow WHERE date = ?", (date,))
    conn.commit()
    deleted = cursor.rowcount
    print(f"  已删除 date={date} 的 {deleted} 条记录")
    return deleted


def query_by_segment(conn: sqlite3.Connection, segment_id: int,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     hour_range: Optional[tuple] = None) -> pd.DataFrame:
    """按路段查询流量，支持日期范围与时间段筛选。"""
    sql = "SELECT * FROM traffic_flow WHERE segment_id = ?"
    params: list = [segment_id]

    if date_from:
        sql += " AND date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND date <= ?"
        params.append(date_to)
    if hour_range:
        sql += " AND hour BETWEEN ? AND ?"
        params.extend(hour_range)

    sql += " ORDER BY date, hour"
    return pd.read_sql_query(sql, conn, params=params)


# ══════════════════════════════════════════════════════════
# 4. 基本查询
# ══════════════════════════════════════════════════════════

def basic_queries(conn: sqlite3.Connection) -> None:
    """执行基本查询并打印结果。"""
    print("\n── 基本查询 ────────────────────────────────────────")

    # 查询 1: segment_id = 15540 的流量记录（前 10 条）
    print("\n[查询1] segment_id=15540 的流量记录（前 10 条）:")
    result = pd.read_sql_query(
        "SELECT date, hour, volume FROM traffic_flow "
        "WHERE segment_id = 15540 ORDER BY date, hour LIMIT 10",
        conn,
    )
    print(result.to_string(index=False))

    # 查询 2: 2015 年之后的流量记录数
    print("\n[查询2] 2015 年之后的流量记录数:")
    result = pd.read_sql_query(
        "SELECT COUNT(*) AS cnt FROM traffic_flow WHERE date > '2015-12-31'",
        conn,
    )
    print(f"  {result.iloc[0, 0]} 条")

    # 查询 3: 每个路段的记录条数（前 10）
    print("\n[查询3] 各路段记录条数（前 10）:")
    result = pd.read_sql_query(
        "SELECT segment_id, COUNT(*) AS record_count "
        "FROM traffic_flow GROUP BY segment_id "
        "ORDER BY record_count DESC LIMIT 10",
        conn,
    )
    print(result.to_string(index=False))


# ══════════════════════════════════════════════════════════
# 5. 多表连接与聚合查询
# ══════════════════════════════════════════════════════════

def advanced_queries(conn: sqlite3.Connection) -> None:
    """执行多表连接与聚合查询。"""
    print("\n── 进阶查询 ────────────────────────────────────────")

    # 查询 4: 路段名称与平均流量
    print("\n[查询4] 各路段平均流量（前 10）:")
    result = pd.read_sql_query(
        "SELECT rs.roadway_name, ROUND(AVG(tf.volume), 1) AS avg_volume "
        "FROM traffic_flow tf "
        "JOIN road_segment rs ON tf.segment_id = rs.segment_id "
        "GROUP BY rs.roadway_name "
        "ORDER BY avg_volume DESC LIMIT 10",
        conn,
    )
    print(result.to_string(index=False))

    # 查询 5: 早高峰平均流量 > 100 的路段
    print("\n[查询5] 早高峰（7-9时）平均流量 > 100 的路段:")
    result = pd.read_sql_query(
        "SELECT rs.roadway_name, ROUND(AVG(tf.volume), 1) AS avg_am_peak "
        "FROM traffic_flow tf "
        "JOIN road_segment rs ON tf.segment_id = rs.segment_id "
        "WHERE tf.hour BETWEEN 7 AND 9 "
        "GROUP BY rs.roadway_name "
        "HAVING avg_am_peak > 100 "
        "ORDER BY avg_am_peak DESC",
        conn,
    )
    print(result.to_string(index=False))

    # 查询 6: 流量最高的 5 天
    print("\n[查询6] 日总流量最高的 5 天:")
    result = pd.read_sql_query(
        "SELECT date, SUM(volume) AS daily_total "
        "FROM traffic_flow "
        "GROUP BY date ORDER BY daily_total DESC LIMIT 5",
        conn,
    )
    print(result.to_string(index=False))

    # 查询 7: 检测器 + 路段连接查询
    print("\n[查询7] 检测器与路段信息（前 5 条）:")
    result = pd.read_sql_query(
        "SELECT d.detector_id, d.status, rs.roadway_name, rs.direction "
        "FROM detector d "
        "JOIN road_segment rs ON d.segment_id = rs.segment_id "
        "LIMIT 5",
        conn,
    )
    print(result.to_string(index=False))


# ══════════════════════════════════════════════════════════
# 6. 聚合报告
# ══════════════════════════════════════════════════════════

def aggregate_report(conn: sqlite3.Connection) -> pd.DataFrame:
    """生成路段级聚合报告：日均流量、峰值时段、变异系数。"""
    result = pd.read_sql_query(
        "SELECT tf.segment_id, rs.roadway_name, "
        "  ROUND(AVG(tf.volume), 1) AS avg_daily_volume, "
        "  (SELECT hour FROM traffic_flow tf2 "
        "   WHERE tf2.segment_id = tf.segment_id "
        "   GROUP BY hour ORDER BY AVG(volume) DESC LIMIT 1) AS peak_hour, "
        "  ROUND(CAST(STDDEV(tf.volume) AS REAL) / NULLIF(AVG(tf.volume), 0), 3) AS cv "
        "FROM traffic_flow tf "
        "JOIN road_segment rs ON tf.segment_id = rs.segment_id "
        "GROUP BY tf.segment_id "
        "ORDER BY avg_daily_volume DESC",
        conn,
    )
    return result


# ══════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════

def main() -> None:
    """主函数：创建数据库 → 导入数据 → CRUD → 查询 → 报告。"""
    print("=" * 60)
    print("第二章 交通数据库操作 — 参考实现")
    print("=" * 60)

    # 清除旧数据库（仅用于演示，确保可重复运行）
    if DB_PATH.exists():
        DB_PATH.unlink()

    # 1. 创建数据库
    print("\n[1] 创建数据库...")
    conn = create_database(str(DB_PATH))

    # 2. 导入数据
    print("\n[2] 导入数据...")
    import_data(conn, str(DATA_PATH))

    # 3. CRUD 演示
    print("\n[3] CRUD 操作演示...")
    new_id = insert_flow(conn, segment_id=15540, date="2024-01-01", hour=8, volume=999)
    print(f"  插入记录 flow_id={new_id}")
    update_flow(conn, flow_id=new_id, new_volume=888)
    delete_flow(conn, date="2024-01-01")

    # 4. 基本查询
    print("\n[4] 基本查询...")
    basic_queries(conn)

    # 5. 进阶查询
    print("\n[5] 多表连接与聚合查询...")
    advanced_queries(conn)

    # 6. 聚合报告
    print("\n[6] 路段级聚合报告...")
    report = aggregate_report(conn)
    print(report.head(10).to_string(index=False))

    # 关闭连接
    conn.close()
    print("\n完成！数据库保存在:", DB_PATH)


if __name__ == "__main__":
    main()
