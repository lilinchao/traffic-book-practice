# 交通数据挖掘理论与应用 — 实践材料

本仓库是教材《交通数据挖掘理论与应用》的开源配套实践材料。

## 章节目录

| 章 | 主题 | 实践状态 |
|---|---|---|
| 01 | 绪论 | 已完成 |
| 02 | 编程实践基础 | 已完成 |
| 03 | 数理理论基础 | 已完成 |
| 04 | 交通表格型数据分析 | 已完成 |
| 05 | 交通空间与位置数据分析 | 已完成 |
| 06 | 交通时序数据分析 | 已完成 |
| 07 | 交通时空数据分析 | 已完成 |
| 08 | 交通影像数据分析 | 已完成 |

## 每章包含

- `README.md` — 学习目标与文件说明
- `practice-guide.md` — 实践讲义（面向学生上机）
- `exercises.md` — 分层练习（基础 / 进阶 / 挑战）
- `starter/` — 起始代码
- `solution/` — 参考实现

## 数据集

交通数据源和字段说明见：

- `datasets.html`
- `DATASETS.md`

小规模教学样本存放在 `data/processed/` 和 `data/results/`。

原始数据需通过脚本下载：

```bash
bash scripts/download_case_data.sh
```

部分章节使用合成数据，由脚本生成：

```bash
python scripts/generate_synthetic_flow.py
python scripts/generate_synthetic_network.py
```

## Notebooks

各章 Notebook 存放在 `notebooks/`。

安装依赖：

```bash
pip install -r requirements.txt
```

## 网站

本仓库支持 GitHub Pages 部署。推送后：

1. `Settings` → `Pages`
2. `Build and deployment` → `Deploy from a branch`
3. 选择 `main` 分支，`/root`
4. 保存

访问地址：

```text
https://<your-github-username>.github.io/<repository-name>/
```

## 本地预览

```bash
python3 -m http.server 8000
```

访问 `http://localhost:8000`

## 许可证

代码采用 MIT License。教学材料采用 CC BY 4.0。
