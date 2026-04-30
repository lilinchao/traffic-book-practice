"""
第 1 章参考实现：环境检查、数据类型识别与命令行交互
运行方式：
  python solution/hello_ai.py
  python solution/hello_ai.py --quiz
  python solution/hello_ai.py --check
"""

import argparse
import platform
import sys


# ── 环境检查 ──────────────────────────────────────────


def check_package(package_name: str) -> str:
    """检查单个包是否已安装，返回版本号或 '未安装'。"""
    try:
        module = __import__(package_name)
        return getattr(module, "__version__", "已安装")
    except ImportError:
        return "未安装"


def run_env_check() -> None:
    """打印 Python 环境信息和关键包状态。"""
    print("=" * 55)
    print("  交通数据挖掘：理论与应用 — 第 1 章实践")
    print("=" * 55)
    print()
    print(f"Python 版本 : {sys.version}")
    print(f"操作系统     : {platform.system()} {platform.release()}")
    print(f"Python 路径  : {sys.executable}")
    print()

    packages = ["numpy", "pandas", "matplotlib", "seaborn", "sklearn", "jupyter"]
    print("关键包检查：")
    missing = []
    for pkg in packages:
        version = check_package(pkg)
        if version == "未安装":
            missing.append(pkg)
            print(f"  {pkg:>12s} : {'---':>20s}  [缺失]")
        else:
            print(f"  {pkg:>12s} : {version:>20s}  [OK]")

    print()
    if missing:
        print(f"提示：以下包未安装，可运行：pip install {' '.join(missing)}")
    else:
        print("所有关键包均已安装，环境准备就绪！")


# ── 数据类型识别 ──────────────────────────────────────


DATA_TYPE_INFO = {
    "面板数据": "多个个体在多个时间点的重复观测，如多路段每日事故数。",
    "时间序列": "单个个体随时间变化的观测序列，如单检测器每小时车流量。",
    "空间数据": "带有空间位置信息的数据，如各监测站的空气质量指标。",
    "时空数据": "同时包含空间和时间维度，如出租车 GPS 轨迹。",
    "图像数据": "以图像形式采集的数据，如路口监控截图。",
}

QUIZ_QUESTIONS = [
    {
        "description": (
            "5 个空气质量监测站，记录了 30 天的每日 PM2.5 浓度。\n"
            "每行包含：站点ID、日期、PM2.5浓度、温度、湿度。"
        ),
        "answer": "面板数据",
        "hint": "多个站点 + 多个时间点 = ?",
    },
    {
        "description": (
            "某高速公路检测器，记录了 24 小时内每 5 分钟的交通流量。\n"
            "每行包含：时间戳、流量（辆/5分钟）。"
        ),
        "answer": "时间序列",
        "hint": "单个检测器 + 时间顺序排列 = ?",
    },
    {
        "description": (
            "深圳市 500 辆出租车的 GPS 轨迹数据。\n"
            "每行包含：出租车ID、时间戳、经度、纬度、速度。"
        ),
        "answer": "时空数据",
        "hint": "既有经纬度又有时间戳 = ?",
    },
    {
        "description": (
            "某城市 200 个路口的监控摄像头拍摄的照片。\n"
            "每行包含：摄像头ID、拍摄时间、图像文件路径。"
        ),
        "answer": "图像数据",
        "hint": "核心数据是照片 = ?",
    },
    {
        "description": (
            "深圳市各行政区的人口密度和平均通勤距离。\n"
            "每行包含：行政区名称、经度、纬度、人口密度、平均通勤距离。"
        ),
        "answer": "空间数据",
        "hint": "有位置信息但没有时间变化 = ?",
    },
]


def run_quiz() -> None:
    """运行数据类型识别小测验。"""
    print("=" * 55)
    print("  交通数据类型识别测验")
    print("  可选答案：面板数据 / 时间序列 / 空间数据 / 时空数据 / 图像数据")
    print("=" * 55)
    print()

    correct = 0
    for i, q in enumerate(QUIZ_QUESTIONS, 1):
        print(f"第 {i} 题：")
        print(f"  {q['description']}")
        print()

        for attempt in range(2):
            answer = input("  你的答案：").strip()
            if answer == q["answer"]:
                print("  正确！\n")
                correct += 1
                break
            elif attempt == 0:
                print(f"  不对，再想想。提示：{q['hint']}")
            else:
                print(f"  正确答案是：{q['answer']}")
                print(f"  说明：{DATA_TYPE_INFO[q['answer']]}")
                print()

    total = len(QUIZ_QUESTIONS)
    print("-" * 55)
    print(f"测验结束：{correct}/{total} 正确")
    if correct == total:
        print("太棒了！你已经掌握了交通数据类型的识别。")
    elif correct >= total * 0.6:
        print("不错！建议回顾 practice-guide.md 第 3 节加深理解。")
    else:
        print("建议仔细阅读 practice-guide.md 第 3 节后再试一次。")


# ── 主程序 ────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="第 1 章实践脚本：环境检查与数据类型识别"
    )
    parser.add_argument(
        "--quiz",
        action="store_true",
        help="运行数据类型识别测验",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅运行环境检查（默认同时运行欢迎信息）",
    )
    args = parser.parse_args()

    if args.quiz:
        run_quiz()
    elif args.check:
        run_env_check()
    else:
        run_env_check()
        print()
        print("提示：运行 --quiz 可以测试你对交通数据类型的理解。")
        print("      运行 --check 仅查看环境检查结果。")


if __name__ == "__main__":
    main()
