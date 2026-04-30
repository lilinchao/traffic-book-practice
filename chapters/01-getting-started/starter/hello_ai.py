"""
第 1 章入门脚本：环境检查与欢迎信息
运行方式：python starter/hello_ai.py
"""

import sys
import platform


def check_package(package_name: str) -> str:
    """检查单个包是否已安装，返回版本号或缺失提示。"""
    try:
        module = __import__(package_name)
        version = getattr(module, "__version__", "已安装（无版本号）")
        return version
    except ImportError:
        return "未安装"


def main():
    # 欢迎信息
    print("=" * 50)
    print("  交通数据挖掘：理论与应用 — 第 1 章实践")
    print("=" * 50)
    print()

    # Python 环境信息
    print(f"Python 版本：{sys.version}")
    print(f"操作系统：{platform.system()} {platform.release()}")
    print(f"Python 路径：{sys.executable}")
    print()

    # 关键包检查
    packages = ["numpy", "pandas", "matplotlib", "seaborn", "sklearn", "jupyter"]
    print("关键包检查：")
    for pkg in packages:
        version = check_package(pkg)
        status = "OK" if version != "未安装" else "缺失"
        print(f"  {pkg:>12s} : {version:>20s}  [{status}]")
    print()

    # 缺失包提示
    missing = [pkg for pkg in packages if check_package(pkg) == "未安装"]
    if missing:
        print(f"提示：以下包未安装，可运行：pip install {' '.join(missing)}")
    else:
        print("所有关键包均已安装，环境准备就绪！")
    print()
    print("下一步：阅读 practice-guide.md，了解交通数据类型和分析框架。")


if __name__ == "__main__":
    main()
