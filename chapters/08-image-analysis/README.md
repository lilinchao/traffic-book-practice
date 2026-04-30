# 08 交通影像数据分析

本章围绕交通场景中的图像与视频数据，从数据预处理、图像分类、目标检测、目标跟踪、语义分割到视频交通参数提取，构建完整的交通影像分析实践链路。

## 推荐公开数据集

由于影像数据体积较大，本仓库不内嵌原始图像。请自行下载以下数据集用于实验：

| 数据集 | 说明 | 下载地址 |
| --- | --- | --- |
| BDD100K | 10 万帧多样化驾驶场景图像，含目标检测与语义分割标注 | https://bdd-data.berkeley.edu/ |
| UA-DETRAC | 路口监控视频车辆检测与跟踪数据集 | https://detrac-db.rire.ri.cmu.edu/ |
| COCO | 通用目标检测与分割基准 | https://cocodataset.org/ |
| MOT Challenge | 多目标跟踪评测数据集 | https://motchallenge.net/ |
| Cityscapes | 城市街景语义分割 | https://www.cityscapes-dataset.com/ |

## 文件结构

```
08-image-analysis/
├── README.md
├── exercises.md            # 习题：基础(4)、进阶(4)、挑战(3)
├── practice-guide.md       # 实践讲义
├── starter/
│   └── image_analysis_practice.py   # 起始代码
└── solution/
    └── image_analysis_practice.py   # 完整参考实现
```

## 实践目标

- 掌握图像加载与质量控制（模糊检测）
- 掌握交通场景数据增强方法
- 从零实现 IoU、NMS、检测评价（Precision/Recall/AP/mAP）
- 掌握计数线逻辑实现流量统计
- 计算跟踪评价指标 MOTA、IDF1
- 理解相机标定与速度估计的基本概念
- 讨论真实部署中的挑战

## 运行代码

起始代码与完整参考实现均使用合成数据运行，无需下载真实数据集即可验证逻辑正确性。

```bash
pip install numpy opencv-python
python starter/image_analysis_practice.py
python solution/image_analysis_practice.py
```

如需使用真实数据，请先下载上述推荐数据集并修改代码中的路径。
