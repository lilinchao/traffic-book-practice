"""
第 8 章起始代码：交通影像数据分析
=====================================

本文件提供框架代码和待实现的占位函数。
请根据 practice-guide.md 中的说明，完成每个函数的实现。

运行方式：
    python image_analysis_practice.py

依赖：
    pip install numpy opencv-python

注意：本代码使用合成数据运行，无需下载真实数据集。
"""

import numpy as np


# ============================================================
# 第一部分：图像加载与质量控制
# ============================================================

def compute_blur_score(img_gray: np.ndarray) -> float:
    """计算图像的拉普拉斯方差作为模糊度指标。

    参数：
        img_gray: 灰度图像，形状 (H, W)，dtype uint8 或 float64

    返回：
        拉普拉斯方差，值越小表示越模糊

    提示：
        使用 cv2.Laplacian 计算拉普拉斯变换，然后对结果求方差 .var()
    """
    # TODO: 实现模糊度计算
    raise NotImplementedError


def check_image_quality(img_gray: np.ndarray, blur_threshold: float = 100.0,
                        brightness_range: tuple = (40, 220)) -> dict:
    """检查图像质量，返回模糊度和亮度信息。

    参数：
        img_gray: 灰度图像
        blur_threshold: 模糊度阈值，低于此值标记为模糊
        brightness_range: 亮度合法范围 (min, max)

    返回：
        字典，包含 blur_score, is_blurry, brightness, is_valid
    """
    # TODO: 实现图像质量检查
    raise NotImplementedError


# ============================================================
# 第二部分：数据增强
# ============================================================

def horizontal_flip(img: np.ndarray, bboxes: np.ndarray) -> tuple:
    """对图像和边界框执行水平翻转。

    参数：
        img: 图像，形状 (H, W, C)
        bboxes: 边界框数组，形状 (N, 4)，格式 [x1, y1, x2, y2]

    返回：
        (flipped_img, flipped_bboxes)
    """
    # TODO: 实现水平翻转（图像和边界框同步）
    raise NotImplementedError


def adjust_brightness(img: np.ndarray, factor: float) -> np.ndarray:
    """调整图像亮度。

    参数：
        img: 图像，dtype uint8
        factor: 亮度因子，>1 变亮，<1 变暗

    返回：
        调整后的图像，dtype uint8
    """
    # TODO: 实现亮度调整
    raise NotImplementedError


# ============================================================
# 第三部分：IoU 与 NMS
# ============================================================

def compute_iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    """计算两个边界框的 IoU。

    参数：
        box_a: [x1, y1, x2, y2]
        box_b: [x1, y1, x2, y2]

    返回：
        IoU 值，范围 [0, 1]
    """
    # TODO: 实现 IoU 计算
    raise NotImplementedError


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.5) -> np.ndarray:
    """非极大值抑制。

    参数：
        boxes: 形状 (N, 4)，格式 [x1, y1, x2, y2]
        scores: 形状 (N,)，置信度分数
        iou_threshold: IoU 阈值

    返回：
        保留的框索引数组
    """
    # TODO: 实现 NMS
    raise NotImplementedError


# ============================================================
# 第四部分：检测评价
# ============================================================

def compute_precision_recall(tp_count: int, fp_count: int, fn_count: int) -> tuple:
    """计算 Precision 和 Recall。

    参数：
        tp_count: 真正例数量
        fp_count: 假正例数量
        fn_count: 假反例数量

    返回：
        (precision, recall)
    """
    # TODO: 实现 Precision 和 Recall 计算
    raise NotImplementedError


def compute_ap(precisions: np.ndarray, recalls: np.ndarray) -> float:
    """计算平均精度（AP），使用全点插值法。

    参数：
        precisions: 累积 Precision 数组
        recalls: 累积 Recall 数组

    返回：
        AP 值
    """
    # TODO: 实现 AP 计算
    raise NotImplementedError


# ============================================================
# 主函数：使用合成数据验证
# ============================================================

def main():
    print("=" * 60)
    print("第 8 章：交通影像数据分析 — 起始代码")
    print("=" * 60)

    # --- 第一部分：图像质量控制 ---
    print("\n[第一部分] 图像加载与质量控制")
    # 生成合成灰度图像
    np.random.seed(42)
    sharp_img = np.random.randint(50, 200, size=(480, 640), dtype=np.uint8)
    blurry_img = cv2.GaussianBlur(sharp_img, (31, 31), 10)

    try:
        sharp_score = compute_blur_score(sharp_img)
        blurry_score = compute_blur_score(blurry_img)
        print(f"  清晰图像模糊度: {sharp_score:.2f}")
        print(f"  模糊图像模糊度: {blurry_score:.2f}")
    except NotImplementedError:
        print("  [待实现] compute_blur_score")

    try:
        result = check_image_quality(sharp_img)
        print(f"  质量检查结果: {result}")
    except NotImplementedError:
        print("  [待实现] check_image_quality")

    # --- 第二部分：数据增强 ---
    print("\n[第二部分] 数据增强")
    color_img = np.random.randint(0, 255, size=(480, 640, 3), dtype=np.uint8)
    bboxes = np.array([[100, 200, 300, 400], [50, 60, 150, 160]], dtype=np.float64)

    try:
        flipped_img, flipped_bboxes = horizontal_flip(color_img, bboxes)
        print(f"  翻转后图像形状: {flipped_img.shape}")
        print(f"  翻转后边界框: {flipped_bboxes}")
    except NotImplementedError:
        print("  [待实现] horizontal_flip")

    try:
        bright_img = adjust_brightness(color_img, 1.5)
        print(f"  亮度调整后均值: {bright_img.mean():.2f}")
    except NotImplementedError:
        print("  [待实现] adjust_brightness")

    # --- 第三部分：IoU 与 NMS ---
    print("\n[第三部分] IoU 与 NMS")

    # IoU 测试
    test_cases = [
        ("完全重叠", [10, 10, 60, 60], [10, 10, 60, 60]),
        ("部分重叠", [10, 10, 60, 60], [30, 30, 80, 80]),
        ("完全不重叠", [10, 10, 60, 60], [100, 100, 150, 150]),
    ]
    for name, a, b in test_cases:
        try:
            iou = compute_iou(np.array(a), np.array(b))
            print(f"  {name} IoU = {iou:.4f}")
        except NotImplementedError:
            print(f"  [待实现] compute_iou ({name})")

    # NMS 测试
    nms_boxes = np.array([
        [10, 10, 60, 60],
        [12, 12, 58, 58],
        [15, 14, 65, 64],
        [100, 100, 150, 150],
        [105, 105, 155, 155],
    ], dtype=np.float64)
    nms_scores = np.array([0.95, 0.85, 0.70, 0.90, 0.60])

    try:
        keep = nms(nms_boxes, nms_scores, iou_threshold=0.5)
        print(f"  NMS 保留的框索引: {keep}")
    except NotImplementedError:
        print("  [待实现] nms")

    # --- 第四部分：检测评价 ---
    print("\n[第四部分] 检测评价")

    try:
        p, r = compute_precision_recall(5, 3, 2)
        print(f"  Precision = {p:.4f}, Recall = {r:.4f}")
    except NotImplementedError:
        print("  [待实现] compute_precision_recall")

    try:
        # 11 点插值法示例
        recall_points = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        precision_points = np.array([1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.5, 0.4, 0.3])
        ap = compute_ap(precision_points, recall_points)
        print(f"  AP (示例) = {ap:.4f}")
    except NotImplementedError:
        print("  [待实现] compute_ap")

    print("\n" + "=" * 60)
    print("起始代码运行完毕。请完成上述 TODO 函数。")
    print("=" * 60)


if __name__ == "__main__":
    import cv2
    main()
