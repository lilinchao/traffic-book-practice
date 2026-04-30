"""
第 8 章完整参考实现：交通影像数据分析
=====================================

本文件包含图像预处理、数据增强、IoU/NMS、检测评价（Precision/Recall/AP/mAP）、
计数线逻辑、跟踪评价（MOTA/IDF1）的完整实现。

运行方式：
    python image_analysis_practice.py

依赖：
    pip install numpy opencv-python

注意：本代码使用合成数据运行，无需下载真实数据集。
推荐真实数据集：BDD100K、UA-DETRAC、COCO、MOT Challenge、Cityscapes。
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional


# ============================================================
# 第一部分：图像加载与质量控制
# ============================================================

def compute_blur_score(img_gray: np.ndarray) -> float:
    """计算图像的拉普拉斯方差作为模糊度指标。

    原理：清晰图像边缘丰富，拉普拉斯变换响应大，方差高；
          模糊图像边缘少，响应小，方差低。

    参数：
        img_gray: 灰度图像，形状 (H, W)，dtype uint8 或 float64

    返回：
        拉普拉斯方差，值越小表示越模糊
    """
    if img_gray.dtype != np.float64:
        img_gray = img_gray.astype(np.float64)
    laplacian = cv2.Laplacian(img_gray, cv2.CV_64F)
    return float(laplacian.var())


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
    blur_score = compute_blur_score(img_gray)
    brightness = float(img_gray.mean())
    is_blurry = blur_score < blur_threshold
    is_too_dark = brightness < brightness_range[0]
    is_too_bright = brightness > brightness_range[1]
    is_valid = not is_blurry and not is_too_dark and not is_too_bright

    return {
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "brightness": brightness,
        "is_too_dark": is_too_dark,
        "is_too_bright": is_too_bright,
        "is_valid": is_valid,
    }


def filter_blurry_images(img_list: List[np.ndarray], threshold: float = 50.0) -> List[np.ndarray]:
    """从图像列表中过滤掉模糊图像。

    参数：
        img_list: 灰度图像列表
        threshold: 模糊度阈值

    返回：
        清晰图像列表
    """
    result = []
    for img in img_list:
        gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        score = compute_blur_score(gray)
        if score >= threshold:
            result.append(img)
    return result


# ============================================================
# 第二部分：数据增强
# ============================================================

def horizontal_flip(img: np.ndarray, bboxes: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """对图像和边界框执行水平翻转。

    参数：
        img: 图像，形状 (H, W, C) 或 (H, W)
        bboxes: 边界框数组，形状 (N, 4)，格式 [x1, y1, x2, y2]；可为 None

    返回：
        (flipped_img, flipped_bboxes)
    """
    flipped_img = img[:, ::-1].copy()
    h, w = img.shape[:2]

    if bboxes is not None and len(bboxes) > 0:
        flipped_bboxes = bboxes.copy()
        flipped_bboxes[:, 0] = w - bboxes[:, 2]  # x1_new = W - x2_old
        flipped_bboxes[:, 2] = w - bboxes[:, 0]  # x2_new = W - x1_old
        return flipped_img, flipped_bboxes
    return flipped_img, bboxes


def adjust_brightness(img: np.ndarray, factor: float) -> np.ndarray:
    """调整图像亮度。

    参数：
        img: 图像，dtype uint8
        factor: 亮度因子，>1 变亮，<1 变暗

    返回：
        调整后的图像，dtype uint8
    """
    result = img.astype(np.float64) * factor
    result = np.clip(result, 0, 255).astype(np.uint8)
    return result


def adjust_contrast(img: np.ndarray, factor: float) -> np.ndarray:
    """调整图像对比度。

    参数：
        img: 图像，dtype uint8
        factor: 对比度因子，>1 增加对比度，<1 降低对比度

    返回：
        调整后的图像，dtype uint8
    """
    mean_val = img.mean()
    result = mean_val + factor * (img.astype(np.float64) - mean_val)
    result = np.clip(result, 0, 255).astype(np.uint8)
    return result


def add_gaussian_noise(img: np.ndarray, mean: float = 0, std: float = 25) -> np.ndarray:
    """给图像添加高斯噪声。

    参数：
        img: 图像，dtype uint8
        mean: 噪声均值
        std: 噪声标准差

    返回：
        添加噪声后的图像，dtype uint8
    """
    noise = np.random.normal(mean, std, img.shape)
    result = img.astype(np.float64) + noise
    result = np.clip(result, 0, 255).astype(np.uint8)
    return result


def add_motion_blur(img: np.ndarray, kernel_size: int = 15, angle: float = 0) -> np.ndarray:
    """给图像添加运动模糊效果。

    参数：
        img: 图像，dtype uint8
        kernel_size: 运动模糊核大小
        angle: 运动方向角度（度）

    返回：
        添加运动模糊后的图像，dtype uint8
    """
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[kernel_size // 2, :] = 1.0
    kernel = kernel / kernel_size
    M = cv2.getRotationMatrix2D((kernel_size / 2, kernel_size / 2), angle, 1)
    kernel = cv2.warpAffine(kernel, M, (kernel_size, kernel_size))
    result = cv2.filter2D(img, -1, kernel)
    return result


def random_crop(img: np.ndarray, bboxes: Optional[np.ndarray] = None,
                crop_ratio: float = 0.8) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """随机裁剪图像，同步调整边界框。

    参数：
        img: 图像，形状 (H, W, C)
        bboxes: 边界框数组，格式 [x1, y1, x2, y2]；可为 None
        crop_ratio: 裁剪区域占原图比例

    返回：
        (cropped_img, cropped_bboxes)，裁剪后边界框中无效框（面积 <= 0）被剔除
    """
    h, w = img.shape[:2]
    new_h, new_w = int(h * crop_ratio), int(w * crop_ratio)
    y_offset = np.random.randint(0, h - new_h + 1)
    x_offset = np.random.randint(0, w - new_w + 1)

    cropped_img = img[y_offset:y_offset + new_h, x_offset:x_offset + new_w].copy()

    if bboxes is not None and len(bboxes) > 0:
        cropped_bboxes = bboxes.copy()
        cropped_bboxes[:, 0] = np.maximum(bboxes[:, 0] - x_offset, 0)
        cropped_bboxes[:, 1] = np.maximum(bboxes[:, 1] - y_offset, 0)
        cropped_bboxes[:, 2] = np.minimum(bboxes[:, 2] - x_offset, new_w)
        cropped_bboxes[:, 3] = np.minimum(bboxes[:, 3] - y_offset, new_h)
        # 剔除无效框（宽或高 <= 0）
        valid = (cropped_bboxes[:, 2] > cropped_bboxes[:, 0]) & \
                (cropped_bboxes[:, 3] > cropped_bboxes[:, 1])
        cropped_bboxes = cropped_bboxes[valid]
        return cropped_img, cropped_bboxes
    return cropped_img, bboxes


class TrafficAugmentation:
    """交通场景数据增强流水线。

    使用方法：
        aug = TrafficAugmentation(brightness_range=(0.7, 1.3), noise_std=15)
        augmented_img, augmented_bboxes = aug(img, bboxes)
    """

    def __init__(self, brightness_range: Tuple[float, float] = (0.7, 1.3),
                 contrast_range: Tuple[float, float] = (0.8, 1.2),
                 noise_std: float = 15,
                 flip_prob: float = 0.5,
                 crop_prob: float = 0.3,
                 motion_blur_prob: float = 0.2):
        self.brightness_range = brightness_range
        self.contrast_range = contrast_range
        self.noise_std = noise_std
        self.flip_prob = flip_prob
        self.crop_prob = crop_prob
        self.motion_blur_prob = motion_blur_prob

    def __call__(self, img: np.ndarray, bboxes: Optional[np.ndarray] = None
                 ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """执行数据增强流水线。"""
        result_img = img.copy()
        result_bboxes = bboxes.copy() if bboxes is not None else None

        # 亮度调整
        factor = np.random.uniform(*self.brightness_range)
        result_img = adjust_brightness(result_img, factor)

        # 对比度调整
        factor = np.random.uniform(*self.contrast_range)
        result_img = adjust_contrast(result_img, factor)

        # 高斯噪声
        if self.noise_std > 0:
            result_img = add_gaussian_noise(result_img, std=self.noise_std)

        # 水平翻转
        if np.random.random() < self.flip_prob:
            result_img, result_bboxes = horizontal_flip(result_img, result_bboxes)

        # 随机裁剪
        if np.random.random() < self.crop_prob:
            result_img, result_bboxes = random_crop(result_img, result_bboxes, crop_ratio=0.85)

        # 运动模糊
        if np.random.random() < self.motion_blur_prob:
            angle = np.random.uniform(0, 180)
            result_img = add_motion_blur(result_img, kernel_size=11, angle=angle)

        return result_img, result_bboxes


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
    # 计算交集区域
    inter_x1 = max(box_a[0], box_b[0])
    inter_y1 = max(box_a[1], box_b[1])
    inter_x2 = min(box_a[2], box_b[2])
    inter_y2 = min(box_a[3], box_b[3])

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    # 计算各框面积
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

    # 并集面积
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def compute_iou_matrix(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """计算两组边界框之间的 IoU 矩阵。

    参数：
        boxes_a: 形状 (M, 4)
        boxes_b: 形状 (N, 4)

    返回：
        IoU 矩阵，形状 (M, N)
    """
    M, N = len(boxes_a), len(boxes_b)
    iou_matrix = np.zeros((M, N), dtype=np.float64)
    for i in range(M):
        for j in range(N):
            iou_matrix[i, j] = compute_iou(boxes_a[i], boxes_b[j])
    return iou_matrix


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.5) -> np.ndarray:
    """非极大值抑制。

    算法步骤：
    1. 按置信度从高到低排序所有检测框
    2. 取置信度最高的框 A，加入输出列表
    3. 计算剩余框与 A 的 IoU，剔除 IoU > 阈值的框
    4. 重复步骤 2-3 直到所有框被处理

    参数：
        boxes: 形状 (N, 4)，格式 [x1, y1, x2, y2]
        scores: 形状 (N,)，置信度分数
        iou_threshold: IoU 阈值

    返回：
        保留的框索引数组
    """
    if len(boxes) == 0:
        return np.array([], dtype=np.int64)

    # 按置信度降序排序
    order = scores.argsort()[::-1]
    keep = []

    while len(order) > 0:
        # 取当前置信度最高的框
        i = order[0]
        keep.append(i)

        if len(order) == 1:
            break

        # 计算剩余框与当前框的 IoU
        remaining = order[1:]
        ious = np.array([compute_iou(boxes[i], boxes[j]) for j in remaining])

        # 保留 IoU <= 阈值的框
        mask = ious <= iou_threshold
        order = remaining[mask]

    return np.array(keep, dtype=np.int64)


# ============================================================
# 第四部分：检测评价：Precision、Recall、AP、mAP
# ============================================================

def match_detections(gt_boxes: np.ndarray, pred_boxes: np.ndarray,
                     pred_scores: np.ndarray, iou_threshold: float = 0.5
                     ) -> Tuple[List[bool], List[bool]]:
    """将预测框与真实框匹配，确定 TP 和 FP。

    参数：
        gt_boxes: 真实框，形状 (G, 4)
        pred_boxes: 预测框，形状 (P, 4)
        pred_scores: 预测置信度，形状 (P,)
        iou_threshold: IoU 阈值

    返回：
        (is_tp, is_fp)，长度均为 P 的列表，标记每个预测是否为 TP 或 FP
    """
    # 按置信度降序排列预测
    order = pred_scores.argsort()[::-1]
    pred_boxes_sorted = pred_boxes[order]

    G = len(gt_boxes)
    P = len(pred_boxes)
    gt_matched = np.zeros(G, dtype=bool)
    is_tp = [False] * P
    is_fp = [False] * P

    for p_idx in range(P):
        orig_idx = order[p_idx]
        best_iou = 0.0
        best_gt_idx = -1

        for g_idx in range(G):
            if gt_matched[g_idx]:
                continue
            iou = compute_iou(pred_boxes_sorted[p_idx], gt_boxes[g_idx])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = g_idx

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            is_tp[orig_idx] = True
            gt_matched[best_gt_idx] = True
        else:
            is_fp[orig_idx] = True

    return is_tp, is_fp


def compute_precision_recall(tp_count: int, fp_count: int, fn_count: int) -> Tuple[float, float]:
    """计算 Precision 和 Recall。

    参数：
        tp_count: 真正例数量
        fp_count: 假正例数量
        fn_count: 假反例数量

    返回：
        (precision, recall)
    """
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    return precision, recall


def compute_ap(precisions: np.ndarray, recalls: np.ndarray) -> float:
    """计算平均精度（AP），使用全点插值法。

    全点插值法：对每个 Recall 值 r，取 r' >= r 范围内的最大 Precision，
    然后计算插值后 Precision-Recall 曲线下面积。

    参数：
        precisions: 累积 Precision 数组（已按 Recall 排序）
        recalls: 累积 Recall 数组（单调递增）

    返回：
        AP 值
    """
    # 在 Recall 首尾添加哨兵点
    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([1.0], precisions, [0.0]))

    # 从右向左计算包络线（确保 Precision 单调递减）
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    # 计算 PR 曲线下面积
    indices = np.where(mrec[1:] != mrec[:-1])[0]
    ap = np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1])

    return float(ap)


def compute_ap_from_detections(gt_boxes: np.ndarray, pred_boxes: np.ndarray,
                                pred_scores: np.ndarray, iou_threshold: float = 0.5) -> float:
    """从检测结果直接计算 AP。

    参数：
        gt_boxes: 真实框，形状 (G, 4)
        pred_boxes: 预测框，形状 (P, 4)
        pred_scores: 预测置信度，形状 (P,)
        iou_threshold: IoU 阈值

    返回：
        AP 值
    """
    is_tp, is_fp = match_detections(gt_boxes, pred_boxes, pred_scores, iou_threshold)

    # 按置信度降序排列
    order = pred_scores.argsort()[::-1]
    tp_ordered = np.array([is_tp[i] for i in order], dtype=np.float64)
    fp_ordered = np.array([is_fp[i] for i in order], dtype=np.float64)

    # 累积 TP 和 FP
    tp_cumsum = np.cumsum(tp_ordered)
    fp_cumsum = np.cumsum(fp_ordered)

    precisions = tp_cumsum / (tp_cumsum + fp_cumsum)
    recalls = tp_cumsum / len(gt_boxes) if len(gt_boxes) > 0 else tp_cumsum * 0

    ap = compute_ap(precisions, recalls)
    return ap


def compute_map(all_gt: Dict[str, np.ndarray], all_pred: Dict[str, Tuple[np.ndarray, np.ndarray]],
                iou_threshold: float = 0.5) -> Tuple[float, Dict[str, float]]:
    """计算 mAP（所有类别 AP 的均值）。

    参数：
        all_gt: 字典 {类别名: 真实框数组 (G, 4)}
        all_pred: 字典 {类别名: (预测框数组 (P, 4), 预测分数数组 (P,))}
        iou_threshold: IoU 阈值

    返回：
        (mAP, {类别名: AP})
    """
    ap_dict = {}
    for cls_name in all_gt:
        gt_boxes = all_gt[cls_name]
        if cls_name in all_pred:
            pred_boxes, pred_scores = all_pred[cls_name]
        else:
            pred_boxes = np.zeros((0, 4))
            pred_scores = np.zeros(0)

        if len(gt_boxes) == 0 and len(pred_boxes) == 0:
            ap_dict[cls_name] = 1.0
        elif len(gt_boxes) == 0:
            ap_dict[cls_name] = 0.0
        else:
            ap_dict[cls_name] = compute_ap_from_detections(
                gt_boxes, pred_boxes, pred_scores, iou_threshold)

    mAP = float(np.mean(list(ap_dict.values()))) if ap_dict else 0.0
    return mAP, ap_dict


# ============================================================
# 第五部分：计数线逻辑与流量统计
# ============================================================

def check_line_crossing(prev_pos: Tuple[float, float], curr_pos: Tuple[float, float],
                        line_y: float) -> Optional[str]:
    """判断目标是否穿越水平计数线。

    参数：
        prev_pos: 前一帧中心坐标 (x, y)
        curr_pos: 当前帧中心坐标 (x, y)
        line_y: 计数线的 y 坐标

    返回：
        'down' — 从上往下穿越
        'up' — 从下往上穿越
        None — 未穿越
    """
    prev_y, curr_y = prev_pos[1], curr_pos[1]
    if prev_y < line_y and curr_y >= line_y:
        return 'down'
    elif prev_y >= line_y and curr_y < line_y:
        return 'up'
    return None


def count_crossings(track_positions: Dict[int, List[Tuple[float, float]]],
                    line_y: float, cooldown_frames: int = 5,
                    min_cross_distance: float = 5.0) -> Dict[str, int]:
    """统计穿越计数线的目标数量。

    参数：
        track_positions: {track_id: [(x_t, y_t), ...]}，目标中心坐标时间序列
        line_y: 计数线的 y 坐标
        cooldown_frames: 穿越后需要等待多少帧才能再次计数，避免计数线附近来回移动导致误计
        min_cross_distance: 最小穿越距离（像素），小于此距离的穿越被忽略

    返回：
        {'down': 穿越数, 'up': 穿越数, 'total': 总穿越数}
    """
    down_count = 0
    up_count = 0

    for track_id, positions in track_positions.items():
        if len(positions) < 2:
            continue
        cooldown = 0
        for i in range(1, len(positions)):
            if cooldown > 0:
                cooldown -= 1
                continue
            direction = check_line_crossing(positions[i - 1], positions[i], line_y)
            if direction is not None:
                dist = abs(positions[i][1] - positions[i - 1][1])
                if dist < min_cross_distance:
                    continue
                if direction == 'down':
                    down_count += 1
                else:
                    up_count += 1
                cooldown = cooldown_frames

    return {'down': down_count, 'up': up_count, 'total': down_count + up_count}


# ============================================================
# 第六部分：跟踪评价：MOTA 与 IDF1
# ============================================================

def compute_mota(num_gt: int, num_fn: int, num_fp: int, num_idsw: int) -> float:
    """计算 MOTA（Multiple Object Tracking Accuracy）。

    MOTA = 1 - (FN + FP + IDSW) / GT

    参数：
        num_gt: 真实目标出现总次数
        num_fn: 漏检总数
        num_fp: 误检总数
        num_idsw: ID 切换总数

    返回：
        MOTA 值，范围 (-inf, 1]
    """
    if num_gt == 0:
        return 1.0
    return 1.0 - (num_fn + num_fp + num_idsw) / num_gt


def compute_idf1(idtp: int, idfp: int, idfn: int) -> float:
    """计算 IDF1（ID F1 Score）。

    IDF1 = 2 * IDTP / (2 * IDTP + IDFP + IDFN)

    参数：
        idtp: ID 真正例数
        idfp: ID 假正例数
        idfn: ID 假反例数

    返回：
        IDF1 值，范围 [0, 1]
    """
    denominator = 2 * idtp + idfp + idfn
    if denominator == 0:
        return 1.0
    return 2.0 * idtp / denominator


def compute_tracking_id_matches(gt_tracks: Dict[int, List[Tuple[int, int, int, int]]],
                                 pred_tracks: Dict[int, List[Tuple[int, int, int, int]]]
                                 ) -> Tuple[int, int, int]:
    """计算跟踪 ID 匹配统计（简化版）。

    对每个真实 track，找到与之 IoU 最大的预测 track，统计 IDTP/IDFP/IDFN。
    此为简化实现，完整实现需基于 MOT 评测工具。

    参数：
        gt_tracks: {gt_id: [(frame, x1, y1, x2, y2), ...]}
        pred_tracks: {pred_id: [(frame, x1, y1, x2, y2), ...]}

    返回：
        (idtp, idfp, idfn)
    """
    # 构建 frame -> gt_boxes 和 frame -> pred_boxes 映射
    frame_gt: Dict[int, Dict[int, np.ndarray]] = {}
    for gt_id, frames in gt_tracks.items():
        for frame, x1, y1, x2, y2 in frames:
            if frame not in frame_gt:
                frame_gt[frame] = {}
            frame_gt[frame][gt_id] = np.array([x1, y1, x2, y2], dtype=np.float64)

    frame_pred: Dict[int, Dict[int, np.ndarray]] = {}
    for pred_id, frames in pred_tracks.items():
        for frame, x1, y1, x2, y2 in frames:
            if frame not in frame_pred:
                frame_pred[frame] = {}
            frame_pred[frame][pred_id] = np.array([x1, y1, x2, y2], dtype=np.float64)

    # 对每个真实 track 找到最佳匹配的预测 track
    # 简化：统计每帧中 ID 匹配情况
    idtp = 0
    total_pred = 0
    total_gt = 0

    all_frames = set(frame_gt.keys()) | set(frame_pred.keys())
    for frame in all_frames:
        gt_dict = frame_gt.get(frame, {})
        pred_dict = frame_pred.get(frame, {})
        total_gt += len(gt_dict)
        total_pred += len(pred_dict)

        # 对每个真实框找最佳匹配预测框
        matched_preds = set()
        for gt_id, gt_box in gt_dict.items():
            best_iou = 0.0
            best_pred_id = -1
            for pred_id, pred_box in pred_dict.items():
                if pred_id in matched_preds:
                    continue
                iou = compute_iou(gt_box, pred_box)
                if iou > best_iou and iou >= 0.5:
                    best_iou = iou
                    best_pred_id = pred_id
            if best_pred_id >= 0:
                idtp += 1
                matched_preds.add(best_pred_id)

    idfp = total_pred - idtp
    idfn = total_gt - idtp
    return idtp, idfp, idfn


# ============================================================
# 第七部分：速度估计概念（相机标定）
# ============================================================

def pixel_to_world(dx_pixel: float, dy_pixel: float,
                   pixels_per_meter: float = 20.0, fps: float = 25.0) -> float:
    """将像素位移换算为真实速度（简化模型）。

    注意：此函数使用简化的匀值像素-距离换算，实际应用中需要：
    1. 相机标定获取内参矩阵和畸变系数
    2. 逆透视映射（IPM）将透视图像转换为鸟瞰图
    3. 考虑不同深度的像素-距离换算比例差异

    参数：
        dx_pixel: x 方向像素位移
        dy_pixel: y 方向像素位移
        pixels_per_meter: 每米对应的像素数（简化为常数）
        fps: 视频帧率

    返回：
        速度，单位 km/h
    """
    displacement_pixel = np.sqrt(dx_pixel ** 2 + dy_pixel ** 2)
    displacement_meter = displacement_pixel / pixels_per_meter
    speed_mps = displacement_meter * fps  # 米/秒
    speed_kmph = speed_mps * 3.6  # 转换为 km/h
    return speed_kmph


# ============================================================
# 第八部分：综合案例 — 路口视频车辆检测与流量统计管线
# ============================================================

def simulate_video_pipeline(
    n_frames: int = 50,
    n_vehicles: int = 8,
    frame_size: Tuple[int, int] = (640, 480),
    line_y: int = 240,
    iou_threshold: float = 0.5,
    nms_threshold: float = 0.5,
    time_window_sec: int = 300,
    fps: float = 25.0,
) -> Dict:
    """模拟从视频到交通流量统计的完整管线（使用合成数据）。

    管线步骤：
    1. 模拟视频帧中的车辆位置
    2. 模拟检测结果（含误检和漏检）
    3. 对检测结果执行 NMS
    4. 使用卡尔曼滤波 + 匈牙利匹配的简化跟踪
    5. 计数线穿越判定
    6. 按时间窗汇总流量

    参数：
        n_frames: 帧数
        n_vehicles: 真实车辆数
        frame_size: (W, H)
        line_y: 计数线 y 坐标
        iou_threshold: 检测匹配 IoU 阈值
        nms_threshold: NMS IoU 阈值
        time_window_sec: 流量汇总时间窗（秒）
        fps: 帧率

    返回：
        字典，包含 flow_summary, tracking_metrics, detection_metrics
    """
    rng = np.random.RandomState(42)
    W, H = frame_size

    # --- 1. 模拟车辆轨迹 ---
    tracks = {}  # vehicle_id -> list of (x, y, w, h)
    for vid in range(n_vehicles):
        x = rng.uniform(50, W - 50)
        y = rng.uniform(50, H - 50)
        vx = rng.uniform(-3, 3)
        vy = rng.uniform(1, 5)  # 大部分向下移动
        positions = []
        for f in range(n_frames):
            x_f = x + vx * f + rng.normal(0, 0.5)
            y_f = y + vy * f + rng.normal(0, 0.5)
            w_f = rng.uniform(30, 60)
            h_f = rng.uniform(25, 50)
            if 0 <= x_f <= W and 0 <= y_f <= H:
                positions.append((x_f, y_f, w_f, h_f))
        if len(positions) >= 2:
            tracks[vid] = positions

    # --- 2. 模拟检测结果 ---
    det_tp = 0
    det_fp = 0
    det_fn = 0
    all_detections = []  # list of (frame, x1, y1, x2, y2, score, is_tp)

    for f in range(n_frames):
        frame_dets = []
        for vid, pos_list in tracks.items():
            if f < len(pos_list):
                x, y, w, h = pos_list[f]
                # 漏检概率 10%
                if rng.random() < 0.1:
                    det_fn += 1
                    continue
                # 加入位置噪声
                x1 = x - w / 2 + rng.normal(0, 3)
                y1 = y - h / 2 + rng.normal(0, 3)
                x2 = x + w / 2 + rng.normal(0, 3)
                y2 = y + h / 2 + rng.normal(0, 3)
                score = rng.uniform(0.6, 0.99)
                frame_dets.append((f, x1, y1, x2, y2, score, True))
                det_tp += 1

        # 添加误检
        n_fp = rng.poisson(0.5)
        for _ in range(n_fp):
            fx = rng.uniform(0, W - 50)
            fy = rng.uniform(0, H - 50)
            fw = rng.uniform(20, 50)
            fh = rng.uniform(20, 40)
            fs = rng.uniform(0.3, 0.7)
            frame_dets.append((f, fx, fy, fx + fw, fy + fh, fs, False))
            det_fp += 1

        all_detections.extend(frame_dets)

    # --- 3. NMS（按帧处理）---
    nms_detections = []
    for f in range(n_frames):
        frame_dets = [(d[1], d[2], d[3], d[4], d[5], d[6])
                      for d in all_detections if d[0] == f]
        if not frame_dets:
            continue
        boxes = np.array([[d[0], d[1], d[2], d[3]] for d in frame_dets])
        scores = np.array([d[4] for d in frame_dets])
        keep = nms(boxes, scores, nms_threshold)
        for idx in keep:
            d = frame_dets[idx]
            nms_detections.append((f, d[0], d[1], d[2], d[3], d[4], d[5]))

    # --- 4. 简化跟踪（基于最近邻匹配）---
    tracked = {}  # track_id -> list of (frame, cx, cy)
    next_id = 0
    active = {}  # track_id -> (cx, cy, last_frame)
    max_gap = 3  # 最大允许帧间隔

    for f in range(n_frames):
        frame_centers = []
        for d in nms_detections:
            if d[0] != f:
                continue
            cx = (d[1] + d[3]) / 2
            cy = (d[2] + d[4]) / 2
            frame_centers.append((cx, cy))

        matched_tracks = set()
        matched_dets = set()
        # 对每个活跃轨迹找最近的检测
        assignments = []
        for tid, (tcx, tcy, last_f) in active.items():
            if f - last_f > max_gap:
                continue
            best_dist = float('inf')
            best_di = -1
            for di, (dcx, dcy) in enumerate(frame_centers):
                if di in matched_dets:
                    continue
                dist = np.sqrt((tcx - dcx) ** 2 + (tcy - dcy) ** 2)
                if dist < best_dist and dist < 50:
                    best_dist = dist
                    best_di = di
            if best_di >= 0:
                assignments.append((tid, best_di))
                matched_tracks.add(tid)
                matched_dets.add(best_di)

        for tid, di in assignments:
            cx, cy = frame_centers[di]
            tracked[tid].append((f, cx, cy))
            active[tid] = (cx, cy, f)

        # 未匹配的检测 → 新轨迹
        for di, (cx, cy) in enumerate(frame_centers):
            if di not in matched_dets:
                tracked[next_id] = [(f, cx, cy)]
                active[next_id] = (cx, cy, f)
                next_id += 1

    # 清理过期的活跃轨迹
    active = {tid: v for tid, v in active.items()
              if f - v[2] <= max_gap}

    # --- 5. 计数线穿越 ---
    track_positions = {}
    for tid, traj in tracked.items():
        track_positions[tid] = [(x, y) for _, x, y in traj]

    flow = count_crossings(track_positions, line_y)

    # --- 6. 按时间窗汇总流量 ---
    frames_per_window = int(time_window_sec * fps)
    n_windows = max(1, n_frames // frames_per_window)
    flow_by_window = {"down": [0] * n_windows, "up": [0] * n_windows}

    for tid, traj in tracked.items():
        for i in range(1, len(traj)):
            prev_f, prev_x, prev_y = traj[i - 1]
            curr_f, curr_x, curr_y = traj[i]
            direction = check_line_crossing((prev_x, prev_y), (curr_x, curr_y), line_y)
            if direction is not None:
                win = min(prev_f // frames_per_window, n_windows - 1)
                if direction == 'down':
                    flow_by_window["down"][win] += 1
                else:
                    flow_by_window["up"][win] += 1

    # --- 计算跟踪指标 ---
    total_gt = sum(len(pos) for pos in tracks.values())
    num_fn_est = int(total_gt * 0.1)
    num_fp_est = det_fp
    num_idsw = sum(1 for tid in tracked if len(tracked[tid]) > 1 and
                   any(abs(traj[i][2] - traj[i-1][2]) > 30
                       for i in range(1, len(traj))))
    mota = compute_mota(total_gt, num_fn_est, num_fp_est, num_idsw)

    return {
        "flow_summary": flow,
        "flow_by_window": flow_by_window,
        "detection_metrics": {
            "TP": det_tp, "FP": det_fp, "FN": det_fn,
            "precision": det_tp / max(det_tp + det_fp, 1),
            "recall": det_tp / max(det_tp + det_fn, 1),
        },
        "tracking_metrics": {
            "MOTA": mota,
            "n_tracks": len(tracked),
            "n_id_switches": num_idsw,
        },
    }


# ============================================================
# 主函数：使用合成数据验证
# ============================================================

def main():
    print("=" * 60)
    print("第 8 章：交通影像数据分析 — 完整参考实现")
    print("=" * 60)

    np.random.seed(42)

    # ========================================
    # 第一部分：图像质量控制
    # ========================================
    print("\n" + "=" * 40)
    print("[第一部分] 图像加载与质量控制")
    print("=" * 40)

    # 生成合成灰度图像
    sharp_img = np.random.randint(50, 200, size=(480, 640), dtype=np.uint8)
    blurry_img = cv2.GaussianBlur(sharp_img, (31, 31), 10)

    sharp_score = compute_blur_score(sharp_img)
    blurry_score = compute_blur_score(blurry_img)
    print(f"  清晰图像拉普拉斯方差: {sharp_score:.2f}")
    print(f"  模糊图像拉普拉斯方差: {blurry_score:.2f}")

    quality = check_image_quality(sharp_img)
    print(f"  清晰图像质量检查: blur_score={quality['blur_score']:.2f}, "
          f"is_blurry={quality['is_blurry']}, brightness={quality['brightness']:.2f}, "
          f"is_valid={quality['is_valid']}")

    quality_blur = check_image_quality(blurry_img, blur_threshold=100.0)
    print(f"  模糊图像质量检查: blur_score={quality_blur['blur_score']:.2f}, "
          f"is_blurry={quality_blur['is_blurry']}, is_valid={quality_blur['is_valid']}")

    # 批量模糊过滤
    img_list = [sharp_img, blurry_img, sharp_img, blurry_img]
    filtered = filter_blurry_images(img_list, threshold=50.0)
    print(f"  批量过滤: {len(img_list)} 张 -> {len(filtered)} 张清晰图像")

    # ========================================
    # 第二部分：数据增强
    # ========================================
    print("\n" + "=" * 40)
    print("[第二部分] 数据增强")
    print("=" * 40)

    color_img = np.random.randint(0, 255, size=(480, 640, 3), dtype=np.uint8)
    bboxes = np.array([[100, 200, 300, 400], [50, 60, 150, 160]], dtype=np.float64)

    # 水平翻转
    flipped_img, flipped_bboxes = horizontal_flip(color_img, bboxes)
    print(f"  水平翻转: 图像形状={flipped_img.shape}")
    print(f"    原始框: {bboxes.tolist()}")
    print(f"    翻转框: {flipped_bboxes.tolist()}")

    # 亮度调整
    bright_img = adjust_brightness(color_img, 1.5)
    dark_img = adjust_brightness(color_img, 0.5)
    print(f"  亮度调整: 原始均值={color_img.mean():.2f}, "
          f"变亮后={bright_img.mean():.2f}, 变暗后={dark_img.mean():.2f}")

    # 对比度调整
    high_contrast = adjust_contrast(color_img, 1.5)
    print(f"  对比度调整: 原始标准差={color_img.std():.2f}, "
          f"增强后={high_contrast.std():.2f}")

    # 高斯噪声
    noisy_img = add_gaussian_noise(color_img, std=20)
    print(f"  高斯噪声: 噪声标准差=20, 差异标准差={np.std(noisy_img.astype(float) - color_img.astype(float)):.2f}")

    # 运动模糊
    motion_blur_img = add_motion_blur(color_img, kernel_size=15, angle=30)
    print(f"  运动模糊: 核大小=15, 角度=30°")

    # 随机裁剪
    cropped_img, cropped_bboxes = random_crop(color_img, bboxes, crop_ratio=0.8)
    print(f"  随机裁剪: 原始尺寸={color_img.shape[:2]}, 裁剪后={cropped_img.shape[:2]}")
    print(f"    裁剪后有效框: {cropped_bboxes.tolist() if cropped_bboxes is not None else 'None'}")

    # 数据增强流水线
    aug = TrafficAugmentation(brightness_range=(0.7, 1.3), noise_std=10)
    aug_img, aug_bboxes = aug(color_img, bboxes)
    print(f"  增强流水线: 输出形状={aug_img.shape}")
    print(f"    增强后边界框: {aug_bboxes.tolist() if aug_bboxes is not None else 'None'}")

    # ========================================
    # 第三部分：IoU 与 NMS
    # ========================================
    print("\n" + "=" * 40)
    print("[第三部分] IoU 与 NMS")
    print("=" * 40)

    # IoU 测试
    test_cases = [
        ("完全重叠", [10, 10, 60, 60], [10, 10, 60, 60]),
        ("部分重叠", [10, 10, 60, 60], [30, 30, 80, 80]),
        ("完全不重叠", [10, 10, 60, 60], [100, 100, 150, 150]),
        ("包含关系", [10, 10, 100, 100], [30, 30, 60, 60]),
    ]
    for name, a, b in test_cases:
        iou = compute_iou(np.array(a), np.array(b))
        print(f"  {name}: IoU = {iou:.4f}")

    # 部分重叠 IoU 手算验证
    # 交集 = (60-30)*(60-30) = 900, 并集 = 50*50 + 50*50 - 900 = 4100
    # IoU = 900/4100 ≈ 0.2195
    print(f"  部分重叠手算验证: 交集=900, 并集=4100, IoU={900/4100:.4f}")

    # IoU 矩阵
    boxes_a = np.array([[10, 10, 60, 60], [100, 100, 150, 150]], dtype=np.float64)
    boxes_b = np.array([[30, 30, 80, 80], [10, 10, 60, 60]], dtype=np.float64)
    iou_mat = compute_iou_matrix(boxes_a, boxes_b)
    print(f"\n  IoU 矩阵:\n{iou_mat}")

    # NMS 测试
    nms_boxes = np.array([
        [10, 10, 60, 60],    # A
        [12, 12, 58, 58],    # B (与 A 重叠大)
        [15, 14, 65, 64],    # C (与 A 重叠中等)
        [100, 100, 150, 150], # D (独立)
        [105, 105, 155, 155], # E (与 D 重叠大)
    ], dtype=np.float64)
    nms_scores = np.array([0.95, 0.85, 0.70, 0.90, 0.60])
    keep = nms(nms_boxes, nms_scores, iou_threshold=0.5)
    print(f"\n  NMS 输入: 5 个框")
    print(f"    置信度: {nms_scores.tolist()}")
    print(f"    保留索引: {keep.tolist()}")
    print(f"    保留框置信度: {nms_scores[keep].tolist()}")

    # NMS 过程详解
    print("\n  NMS 逐步过程 (IoU 阈值=0.5):")
    print("    1. 排序: A(0.95) > D(0.90) > B(0.85) > C(0.70) > E(0.60)")
    print("    2. 选 A(0.95): IoU(A,B)={:.4f} > 0.5 -> 剔除 B; IoU(A,C)={:.4f} -> 判断; IoU(A,D)={:.4f} -> 保留 D; IoU(A,E)={:.4f} -> 保留 E".format(
        compute_iou(nms_boxes[0], nms_boxes[1]),
        compute_iou(nms_boxes[0], nms_boxes[2]),
        compute_iou(nms_boxes[0], nms_boxes[3]),
        compute_iou(nms_boxes[0], nms_boxes[4]),
    ))
    iou_ac = compute_iou(nms_boxes[0], nms_boxes[2])
    print(f"    IoU(A,C)={iou_ac:.4f} {'> 0.5 -> 剔除 C' if iou_ac > 0.5 else '<= 0.5 -> 保留 C'}")
    print("    3. 选 D(0.90): IoU(D,E)={:.4f} -> 判断".format(
        compute_iou(nms_boxes[3], nms_boxes[4])))
    iou_de = compute_iou(nms_boxes[3], nms_boxes[4])
    print(f"    IoU(D,E)={iou_de:.4f} {'> 0.5 -> 剔除 E' if iou_de > 0.5 else '<= 0.5 -> 保留 E'}")

    # ========================================
    # 第四部分：检测评价
    # ========================================
    print("\n" + "=" * 40)
    print("[第四部分] 检测评价：Precision、Recall、AP、mAP")
    print("=" * 40)

    # Precision/Recall 基本计算
    p, r = compute_precision_recall(5, 3, 2)
    print(f"  TP=5, FP=3, FN=2 -> Precision={p:.4f}, Recall={r:.4f}")

    # 使用合成数据计算 AP
    # 场景：6 个真实目标，10 个预测（按置信度降序）
    # 检测结果序列：TP, TP, FP, TP, FP, TP, FP, FP, TP, FP
    gt_boxes = np.array([
        [10, 10, 50, 50], [100, 10, 150, 50], [200, 10, 250, 50],
        [300, 10, 350, 50], [400, 10, 450, 50], [500, 10, 550, 50],
    ], dtype=np.float64)

    # 模拟检测结果：6 个真目标 + 4 个假检测
    pred_boxes = np.array([
        [10, 10, 50, 50],    # TP (匹配 gt[0])
        [100, 10, 150, 50],  # TP (匹配 gt[1])
        [60, 60, 90, 90],    # FP (无匹配)
        [200, 10, 250, 50],  # TP (匹配 gt[2])
        [70, 70, 100, 100],  # FP
        [300, 10, 350, 50],  # TP (匹配 gt[3])
        [80, 80, 110, 110],  # FP
        [90, 90, 120, 120],  # FP
        [400, 10, 450, 50],  # TP (匹配 gt[4])
        [95, 95, 125, 125],  # FP
    ], dtype=np.float64)

    pred_scores = np.array([0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60, 0.55, 0.50, 0.40])

    ap = compute_ap_from_detections(gt_boxes, pred_boxes, pred_scores, iou_threshold=0.5)
    print(f"\n  单类别 AP (合成数据): {ap:.4f}")

    # 展示匹配详情
    is_tp, is_fp = match_detections(gt_boxes, pred_boxes, pred_scores, iou_threshold=0.5)
    print(f"  匹配详情 (按原始索引):")
    for i in range(len(pred_scores)):
        status = "TP" if is_tp[i] else "FP"
        print(f"    预测 {i}: score={pred_scores[i]:.2f}, {status}")

    # 累积 Precision/Recall
    order = pred_scores.argsort()[::-1]
    tp_arr = np.array([is_tp[i] for i in order], dtype=np.float64)
    fp_arr = np.array([is_fp[i] for i in order], dtype=np.float64)
    tp_cum = np.cumsum(tp_arr)
    fp_cum = np.cumsum(fp_arr)
    precs = tp_cum / (tp_cum + fp_cum)
    recs = tp_cum / len(gt_boxes)
    print(f"\n  累积 Precision-Recall:")
    for k in range(len(order)):
        print(f"    top-{k+1}: Precision={precs[k]:.4f}, Recall={recs[k]:.4f}")

    # mAP 计算
    all_gt = {
        "车辆": np.array([[10, 10, 60, 60], [100, 100, 160, 160]], dtype=np.float64),
        "行人": np.array([[200, 200, 230, 280]], dtype=np.float64),
        "自行车": np.array([[300, 300, 340, 370]], dtype=np.float64),
    }
    all_pred = {
        "车辆": (np.array([[10, 10, 60, 60], [100, 100, 160, 160]], dtype=np.float64),
                 np.array([0.9, 0.8])),
        "行人": (np.array([[200, 200, 230, 280]], dtype=np.float64),
                 np.array([0.7])),
        "自行车": (np.array([[300, 300, 340, 370]], dtype=np.float64),
                 np.array([0.6])),
    }

    mAP, ap_dict = compute_map(all_gt, all_pred, iou_threshold=0.5)
    print(f"\n  mAP@0.5 (合成数据):")
    for cls_name, cls_ap in ap_dict.items():
        print(f"    {cls_name}: AP = {cls_ap:.4f}")
    print(f"    mAP = {mAP:.4f}")

    # ========================================
    # 第五部分：计数线逻辑
    # ========================================
    print("\n" + "=" * 40)
    print("[第五部分] 计数线逻辑与流量统计")
    print("=" * 40)

    line_y = 300.0

    # 单目标穿越测试
    cases = [
        ("从上往下穿越", (100, 290), (100, 310)),
        ("从下往上穿越", (100, 310), (100, 290)),
        ("未穿越", (100, 280), (100, 290)),
    ]
    for name, prev, curr in cases:
        direction = check_line_crossing(prev, curr, line_y)
        print(f"  {name}: {prev} -> {curr}, 结果 = {direction}")

    # 多目标流量统计
    track_positions = {
        1: [(100, 200), (100, 250), (100, 290), (100, 310), (100, 350)],  # 穿越下行
        2: [(200, 400), (200, 350), (200, 310), (200, 290), (200, 250)],  # 穿越上行
        3: [(150, 200), (150, 250), (150, 280)],  # 未穿越
        4: [(300, 290), (300, 310), (300, 330)],  # 穿越下行
    }

    counts = count_crossings(track_positions, line_y)
    print(f"\n  计数线 y={line_y}, 流量统计:")
    print(f"    下行: {counts['down']}")
    print(f"    上行: {counts['up']}")
    print(f"    总计: {counts['total']}")

    # ========================================
    # 第六部分：跟踪评价
    # ========================================
    print("\n" + "=" * 40)
    print("[第六部分] 跟踪评价：MOTA 与 IDF1")
    print("=" * 40)

    # MOTA 计算
    num_gt, num_fn, num_fp, num_idsw = 20, 5, 3, 2
    mota = compute_mota(num_gt, num_fn, num_fp, num_idsw)
    print(f"  MOTA 计算:")
    print(f"    GT={num_gt}, FN={num_fn}, FP={num_fp}, IDSW={num_idsw}")
    print(f"    MOTA = 1 - ({num_fn}+{num_fp}+{num_idsw})/{num_gt} = {mota:.4f}")

    # IDF1 计算
    idtp, idfp, idfn = 45, 8, 10
    idf1 = compute_idf1(idtp, idfp, idfn)
    print(f"\n  IDF1 计算:")
    print(f"    IDTP={idtp}, IDFP={idfp}, IDFN={idfn}")
    print(f"    IDF1 = 2*{idtp}/(2*{idtp}+{idfp}+{idfn}) = {idf1:.4f}")

    # 使用合成跟踪数据计算
    gt_tracks = {
        1: [(1, 10, 10, 60, 60), (2, 12, 12, 62, 62), (3, 14, 14, 64, 64)],
        2: [(1, 100, 100, 150, 150), (2, 102, 102, 152, 152), (3, 104, 104, 154, 154)],
    }
    pred_tracks = {
        1: [(1, 10, 10, 60, 60), (2, 12, 12, 62, 62), (3, 14, 14, 64, 64)],
        2: [(1, 100, 100, 150, 150), (2, 102, 102, 152, 152), (3, 104, 104, 154, 154)],
    }

    idtp_calc, idfp_calc, idfn_calc = compute_tracking_id_matches(gt_tracks, pred_tracks)
    idf1_calc = compute_idf1(idtp_calc, idfp_calc, idfn_calc)
    print(f"\n  合成跟踪数据 IDF1:")
    print(f"    IDTP={idtp_calc}, IDFP={idfp_calc}, IDFN={idfn_calc}")
    print(f"    IDF1 = {idf1_calc:.4f}")

    # ========================================
    # 第七部分：速度估计
    # ========================================
    print("\n" + "=" * 40)
    print("[第七部分] 相机标定与速度估计（简化模型）")
    print("=" * 40)

    # 模拟：目标在连续帧之间移动 10 像素
    speed = pixel_to_world(dx_pixel=10, dy_pixel=0, pixels_per_meter=20.0, fps=25.0)
    print(f"  水平位移 10 像素, pixels_per_meter=20, fps=25:")
    print(f"    速度 = {speed:.2f} km/h")

    speed_diag = pixel_to_world(dx_pixel=8, dy_pixel=6, pixels_per_meter=20.0, fps=25.0)
    print(f"  对角位移 (8,6) 像素, pixels_per_meter=20, fps=25:")
    print(f"    速度 = {speed_diag:.2f} km/h")

    print(f"\n  注意: 此为简化模型，实际应用需要:")
    print(f"    1. 相机标定 (内参矩阵 + 畸变系数)")
    print(f"    2. 逆透视映射 (IPM) 消除透视畸变")
    print(f"    3. 考虑不同深度的像素-距离换算差异")
    print(f"    4. 使用 cv2.findHomography 或 cv2.getPerspectiveTransform")

    # ========================================
    # 第八部分：综合案例
    # ========================================
    print("\n" + "=" * 40)
    print("[第八部分] 综合案例：路口视频车辆检测与流量统计")
    print("=" * 40)

    result = simulate_video_pipeline(
        n_frames=50, n_vehicles=8, frame_size=(640, 480),
        line_y=240, time_window_sec=300, fps=25.0,
    )

    dm = result["detection_metrics"]
    print(f"  检测效果: TP={dm['TP']}, FP={dm['FP']}, FN={dm['FN']}")
    print(f"    Precision={dm['precision']:.3f}, Recall={dm['recall']:.3f}")

    tm = result["tracking_metrics"]
    print(f"  跟踪效果: MOTA={tm['MOTA']:.3f}, 轨迹数={tm['n_tracks']}, ID切换={tm['n_id_switches']}")

    fs = result["flow_summary"]
    print(f"  流量统计: 下行={fs['down']}, 上行={fs['up']}, 总计={fs['total']}")

    fbw = result["flow_by_window"]
    print(f"  按时间窗汇总 (5 分钟):")
    for i, (d, u) in enumerate(zip(fbw["down"], fbw["up"])):
        print(f"    窗口 {i+1}: 下行={d}, 上行={u}, 总计={d+u}")

    print(f"\n  管线流程: 视频帧 -> 检测 -> NMS -> 跟踪 -> 计数线穿越 -> 流量汇总")
    print(f"  实际部署需额外考虑: ROI 设置、车道映射、相机标定、异常场景")

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 60)
    print("完整参考实现运行完毕")
    print("=" * 60)
    print("\n推荐进一步实践:")
    print("  1. 下载 BDD100K 或 UA-DETRAC 数据集，替换合成数据")
    print("  2. 使用真实标注计算 mAP@0.5 和 mAP@0.5:0.95")
    print("  3. 在 MOT Challenge 上评测 MOTA 和 IDF1")
    print("  4. 使用真实视频运行 simulate_video_pipeline 的完整流程")
    print("  5. 讨论夜间、雨天、遮挡等部署挑战")


if __name__ == "__main__":
    main()
