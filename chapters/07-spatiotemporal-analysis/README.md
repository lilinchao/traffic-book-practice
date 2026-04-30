# 07 交通时空数据分析

本章围绕城市路网速度数据，演示时空数据的基本概念、组织方式、相关性分析与预处理方法，以及从经典统计到图神经网络的时空预测模型体系。

## Dataset

- 合成路网速度数据: `../../data/processed/synthetic_network_speed.csv`
- 合成路网邻接矩阵: `../../data/processed/synthetic_network_adjacency.npz`
- 合成路网节点坐标: `../../data/processed/synthetic_network_nodes.csv`
- 数据生成脚本: `../../scripts/generate_synthetic_network.py`
- 模型结果表: `../../data/results/chapter-07/`

## Practice Goals

- 理解时空数据的基本概念：观测对象与分析对象、空间粒度与时间粒度、边界效应
- 掌握时空数据的组织方式：长表、节点-时间矩阵、张量、图结构与邻接矩阵
- 分析时空相关性：时间自相关、空间自相关、时空耦合相关性
- 实践时空数据预处理：时间对齐、空间匹配、缺失值处理
- 实现时空插值（ST-KNN）、时空聚类（DTW+K-means）、时空关联分析（时滞互相关）
- 构建时空预测模型：历史平均基线、VAR、XGBoost 特征工程、STGCN/DCRNN 图神经网络
- 完成城市路网速度预测综合案例，进行模型比较与误差分析

## Generate Data

```bash
python3 scripts/generate_synthetic_network.py
```

## Run Practice

```bash
pip install -r requirements.txt
python chapters/07-spatiotemporal-analysis/starter/spatiotemporal_practice.py
python chapters/07-spatiotemporal-analysis/solution/spatiotemporal_practice.py
```

## File Structure

```
07-spatiotemporal-analysis/
├── README.md           # 本章说明（本文件）
├── exercises.md        # 练习题
├── practice-guide.md   # 实践讲义
├── starter/
│   └── spatiotemporal_practice.py   # 起始代码
└── solution/
    └── spatiotemporal_practice.py   # 参考实现
```

## Key Concepts

| 概念 | 说明 |
| --- | --- |
| 观测对象 vs 分析对象 | 检测器位置固定（观测对象），路网路段是分析对象 |
| 时间粒度 | 5 分钟/15 分钟/1 小时等聚合间隔 |
| 空间粒度 | 路段/交叉口/小区/TAZ 等空间单元 |
| 边界效应 | 路网边缘节点缺少邻居信息，影响分析结果 |
| 长表 | 每行一条记录：节点ID、时间戳、速度值 |
| 节点-时间矩阵 | 行为节点、列为时间步的速度矩阵 |
| 张量 | 节点 x 时间 x 特征的三维组织方式 |
| 图结构 | 节点集合 + 边集合 + 邻接矩阵 |
| 时滞互相关 | 检测拥堵在空间上的传播方向与时间延迟 |
| DTW 聚类 | 基于动态时间规整的相似性度量，用于路段模式分组 |
