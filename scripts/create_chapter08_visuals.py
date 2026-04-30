"""Generate all figures and result tables for Chapter 08: Traffic Image/Video Analysis.

All visuals use synthetic data generated with numpy / matplotlib — no real images needed.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets/chapter-08"
RESULTS_DIR = ROOT / "data/results/chapter-08"

PRIMARY = "#176b5b"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def laplacian_variance(img: np.ndarray) -> float:
    """Compute variance of the Laplacian — a common blur metric."""
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=float)
    from scipy.signal import convolve2d
    lap = convolve2d(img, kernel, mode="same", boundary="symm")
    return float(np.var(lap))


def make_synthetic_traffic_scene(seed: int = 42) -> np.ndarray:
    """Return a (200, 300, 3) uint8 synthetic top-down traffic scene.

    Gray road with lane markings; coloured rectangles as vehicles.
    """
    rng = np.random.RandomState(seed)
    scene = np.full((200, 300, 3), 90, dtype=np.uint8)  # dark grey background

    # road surface — lighter grey band
    scene[40:160, :, :] = 130

    # lane dashes
    for x in range(0, 300, 30):
        scene[95:105, x : x + 18, :] = 210

    # vehicles (coloured rectangles)
    vehicle_specs = [
        (50, 30, 80, 50, [200, 50, 50]),   # red car
        (60, 160, 100, 50, [50, 50, 200]),  # blue car
        (40, 100, 50, 50, [200, 180, 50]),  # yellow bus
        (55, 220, 130, 50, [50, 180, 50]),  # green truck
    ]
    for h, x, y, w, colour in vehicle_specs:
        y1, y2 = y, min(y + h, 200)
        x1, x2 = x, min(x + w, 300)
        # add slight random jitter so augmentations look different
        dy = rng.randint(-3, 4)
        dx = rng.randint(-3, 4)
        y1 = np.clip(y1 + dy, 0, 200)
        y2 = np.clip(y2 + dy, 0, 200)
        x1 = np.clip(x1 + dx, 0, 300)
        x2 = np.clip(x2 + dx, 0, 300)
        scene[y1:y2, x1:x2] = colour

    return scene


# ---------------------------------------------------------------------------
# Figure 1: Blur detection
# ---------------------------------------------------------------------------

def fig_blur_detection() -> None:
    rng = np.random.RandomState(0)
    base = make_synthetic_traffic_scene(seed=7)
    base_gray = np.mean(base, axis=2) / 255.0

    sharp = base_gray + rng.normal(0, 0.005, base_gray.shape)
    sharp = np.clip(sharp, 0, 1)
    blurry = gaussian_filter(sharp, sigma=3.0)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, img, label in [
        (axes[0], sharp, "Sharp"),
        (axes[1], blurry, "Blurry"),
    ]:
        ax.imshow(img, cmap="gray", vmin=0, vmax=1)
        var = laplacian_variance(img)
        ax.set_title(f"{label}\nLaplacian variance = {var:.4f}", fontsize=14)
        ax.axis("off")
    fig.suptitle("Blur Detection via Laplacian Variance", fontsize=16, fontweight="bold")
    savefig("01_blur_detection.png")


# ---------------------------------------------------------------------------
# Figure 2: Augmentation examples
# ---------------------------------------------------------------------------

def fig_augmentation_examples() -> None:
    rng = np.random.RandomState(5)
    original = make_synthetic_traffic_scene(seed=42).astype(np.float64) / 255.0

    def hflip(img):
        return img[:, ::-1, :]

    def brightness(img, factor=1.4):
        return np.clip(img * factor, 0, 1)

    def gauss_noise(img, sigma=0.07):
        return np.clip(img + rng.normal(0, sigma, img.shape), 0, 1)

    def random_crop(img, margin=30):
        h, w = img.shape[:2]
        top = rng.randint(0, margin)
        left = rng.randint(0, margin)
        return img[top : h - margin + top, left : w - margin + left, :]

    def motion_blur(img, kernel_size=15):
        kernel = np.zeros((kernel_size, kernel_size))
        kernel[kernel_size // 2, :] = 1.0 / kernel_size
        from scipy.signal import convolve2d
        out = np.zeros_like(img)
        for c in range(3):
            out[:, :, c] = convolve2d(img[:, :, c], kernel, mode="same", boundary="symm")
        return np.clip(out, 0, 1)

    augmentations = [
        ("Original", original),
        ("Horizontal Flip", hflip(original)),
        ("Brightness +40%", brightness(original)),
        ("Gaussian Noise", gauss_noise(original)),
        ("Random Crop", random_crop(original)),
        ("Motion Blur", motion_blur(original)),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for ax, (title, img) in zip(axes.ravel(), augmentations):
        ax.imshow(img)
        ax.set_title(title, fontsize=13)
        ax.axis("off")
    fig.suptitle("Common Image Augmentations for Traffic Scenes", fontsize=16, fontweight="bold")
    savefig("02_augmentation_examples.png")


# ---------------------------------------------------------------------------
# Figure 3: IoU diagram
# ---------------------------------------------------------------------------

def fig_iou_diagram() -> None:
    fig, ax = plt.subplots(figsize=(8, 8))

    # ground-truth box
    gt = mpatches.Rectangle((2, 2), 5, 4, linewidth=2,
                             edgecolor="#176b5b", facecolor="#176b5b",
                             alpha=0.25, label="Ground Truth")
    # prediction box
    pr = mpatches.Rectangle((4, 3), 5, 4, linewidth=2,
                             edgecolor="#b7802f", facecolor="#b7802f",
                             alpha=0.25, label="Prediction")
    # intersection
    inter = mpatches.Rectangle((4, 3), 3, 3, linewidth=0,
                                facecolor="#d62728", alpha=0.35, label="Intersection")

    ax.add_patch(gt)
    ax.add_patch(pr)
    ax.add_patch(inter)

    # annotate
    ax.text(3.5, 1.5, "GT", fontsize=16, color="#176b5b", fontweight="bold", ha="center")
    ax.text(7.5, 1.5, "Pred", fontsize=16, color="#b7802f", fontweight="bold", ha="center")

    inter_area = 3 * 3
    union_area = 5 * 4 + 5 * 4 - inter_area
    iou = inter_area / union_area
    ax.text(5.5, 4.5, f"IoU = {iou:.2f}", fontsize=18, fontweight="bold",
            ha="center", va="center", color="#d62728",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#d62728", alpha=0.9))

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=12, framealpha=0.9)
    ax.set_title("Intersection over Union (IoU) Calculation", fontsize=16, fontweight="bold")
    ax.axis("off")
    savefig("03_iou_diagram.png")


# ---------------------------------------------------------------------------
# Figure 4: NMS process
# ---------------------------------------------------------------------------

def fig_nms_process() -> None:
    rng = np.random.RandomState(12)
    # generate overlapping detection boxes around a few objects
    centres = [(100, 80), (250, 120), (400, 90)]
    all_boxes = []  # (x1, y1, x2, y2, score)
    for cx, cy in centres:
        for _ in range(rng.randint(3, 7)):
            dx, dy = rng.normal(0, 12, size=2)
            w = rng.uniform(50, 80)
            h = rng.uniform(40, 70)
            score = rng.uniform(0.4, 0.98)
            all_boxes.append((cx + dx - w / 2, cy + dy - h / 2,
                              cx + dx + w / 2, cy + dy + h / 2, score))

    def nms(boxes, iou_thresh=0.3):
        boxes_sorted = sorted(boxes, key=lambda b: b[4], reverse=True)
        keep = []
        while boxes_sorted:
            best = boxes_sorted.pop(0)
            keep.append(best)
            boxes_sorted = [b for b in boxes_sorted if _iou(best, b) < iou_thresh]
        return keep

    def _iou(a, b):
        xi1 = max(a[0], b[0])
        yi1 = max(a[1], b[1])
        xi2 = min(a[2], b[2])
        yi2 = min(a[3], b[3])
        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        return inter / (area_a + area_b - inter + 1e-9)

    kept = nms(all_boxes)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    for ax, boxes, title in [
        (axes[0], all_boxes, f"Before NMS ({len(all_boxes)} boxes)"),
        (axes[1], kept, f"After NMS ({len(kept)} boxes)"),
    ]:
        # background
        scene = np.full((200, 500, 3), 160, dtype=np.uint8)
        ax.imshow(scene)
        for x1, y1, x2, y2, s in boxes:
            rect = mpatches.Rectangle((x1, y1), x2 - x1, y2 - y1,
                                       linewidth=1.5, edgecolor=PRIMARY,
                                       facecolor="none")
            ax.add_patch(rect)
            ax.text(x1, y1 - 3, f"{s:.2f}", fontsize=8, color="white",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor=PRIMARY, alpha=0.7))
        ax.set_title(title, fontsize=14)
        ax.axis("off")
    fig.suptitle("Non-Maximum Suppression (NMS)", fontsize=16, fontweight="bold")
    savefig("04_nms_process.png")


# ---------------------------------------------------------------------------
# Figure 5: Precision-Recall curve
# ---------------------------------------------------------------------------

def fig_precision_recall_curve() -> None:
    rng = np.random.RandomState(99)

    def make_pr_curve(n_pos=100, n_neg=300, quality=0.8, label=""):
        scores = np.concatenate([
            rng.beta(5 * quality, 2, size=n_pos),
            rng.beta(2, 5 * quality, size=n_neg),
        ])
        labels = np.concatenate([np.ones(n_pos), np.zeros(n_neg)])
        order = np.argsort(-scores)
        labels_sorted = labels[order]
        tp_cum = np.cumsum(labels_sorted)
        fp_cum = np.cumsum(1 - labels_sorted)
        precision = tp_cum / (tp_cum + fp_cum)
        recall = tp_cum / n_pos
        return recall, precision

    recall_v, prec_v = make_pr_curve(quality=0.85, label="Vehicle")
    recall_p, prec_p = make_pr_curve(n_pos=50, n_neg=200, quality=0.7, label="Pedestrian")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(recall_v, prec_v, color=PRIMARY, linewidth=2, label="Vehicle")
    ax.plot(recall_p, prec_p, color="#b7802f", linewidth=2, label="Pedestrian")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=12)
    ax.set_title("Precision-Recall Curves", fontsize=16, fontweight="bold")
    savefig("05_precision_recall_curve.png")


# ---------------------------------------------------------------------------
# Figure 6: AP 11-point interpolation
# ---------------------------------------------------------------------------

def fig_ap_interpolation() -> None:
    recall_pts = np.linspace(0, 1, 11)
    # plausible interpolated precision values
    interp_prec = np.array([1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.68, 0.60, 0.50, 0.35, 0.20])
    # raw (noisier) precision at those recall points
    raw_prec = interp_prec * np.array([1.0, 0.92, 0.97, 0.88, 0.82, 0.78, 0.62, 0.65, 0.45, 0.38, 0.15])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(recall_pts, raw_prec, "o--", color="#999999", linewidth=1.2,
            markersize=6, label="Raw precision", zorder=2)
    ax.step(recall_pts, interp_prec, where="post", color=PRIMARY,
            linewidth=2.5, label="11-point interpolation", zorder=3)
    ax.scatter(recall_pts, interp_prec, color=PRIMARY, s=60, zorder=4)

    ap = np.mean(interp_prec)
    ax.text(0.35, 0.95, f"AP = {ap:.3f}", fontsize=16, fontweight="bold",
            transform=ax.transAxes, color=PRIMARY,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=PRIMARY))

    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=12, loc="lower left")
    ax.set_title("11-Point Interpolation AP Calculation", fontsize=16, fontweight="bold")
    savefig("06_ap_interpolation.png")


# ---------------------------------------------------------------------------
# Figure 7: Per-class AP bar chart
# ---------------------------------------------------------------------------

def fig_per_class_ap() -> None:
    classes = ["Car", "Bus", "Truck", "Pedestrian", "Cyclist", "Motorcycle"]
    aps = [0.82, 0.74, 0.69, 0.61, 0.55, 0.48]
    df = pd.DataFrame({"Class": classes, "AP": aps})

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df, x="Class", y="AP", color=PRIMARY, ax=ax)
    for i, (c, v) in enumerate(zip(classes, aps)):
        ax.text(i, v + 0.015, f"{v:.2f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Average Precision (AP)")
    ax.set_title("Per-Class Average Precision", fontsize=16, fontweight="bold")
    savefig("07_per_class_ap.png")


# ---------------------------------------------------------------------------
# Figure 8: Counting line logic
# ---------------------------------------------------------------------------

def fig_counting_line_logic() -> None:
    rng = np.random.RandomState(33)
    scene = make_synthetic_traffic_scene(seed=33)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(scene)

    # counting line (vertical dashed line)
    lx = 180
    ax.axvline(lx, color="#d62728", linewidth=3, linestyle="--", label="Counting line")
    ax.text(lx + 5, 30, "Counting\nLine", fontsize=11, color="#d62728", fontweight="bold")

    # vehicle trajectories crossing the line
    trajectories = [
        ([60, 120, lx, 240, 280], [55, 58, 60, 62, 65], "Vehicle A"),
        ([40, 100, lx, 220, 270], [130, 128, 125, 122, 120], "Vehicle B"),
        ([lx - 60, lx, lx + 80], [90, 95, 100], "Vehicle C"),
        ([lx + 20, lx, lx - 70], [145, 140, 135], "Vehicle D"),
    ]
    colours = [PRIMARY, "#b7802f", "#4c72b0", "#c44e52"]
    for (xs, ys, label), col in zip(trajectories, colours):
        ax.plot(xs, ys, "-o", color=col, linewidth=2, markersize=5, label=label)
        # direction arrow at mid-point
        mid = len(xs) // 2
        dx = xs[mid + 1] - xs[mid]
        dy = ys[mid + 1] - ys[mid]
        ax.annotate("", xy=(xs[mid] + dx * 0.6, ys[mid] + dy * 0.6),
                     xytext=(xs[mid], ys[mid]),
                     arrowprops=dict(arrowstyle="->", color=col, lw=2))

    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.set_title("Vehicle Counting with a Virtual Counting Line", fontsize=16, fontweight="bold")
    ax.axis("off")
    savefig("08_counting_line_logic.png")


# ---------------------------------------------------------------------------
# Figure 9: Tracking ID switch
# ---------------------------------------------------------------------------

def fig_tracking_id_switch() -> None:
    frames = np.arange(1, 21)

    # vehicle A: tracked as ID 1, then ID switches to 3 at frame 12
    id_a = [1] * 11 + [3] * 9
    # vehicle B: tracked consistently as ID 2
    id_b = [2] * 20
    # vehicle C: appears at frame 5, tracked as 4, switches to 2 at frame 15
    id_c = [np.nan] * 4 + [4] * 10 + [2] * 6

    fig, ax = plt.subplots(figsize=(14, 5))

    ax.plot(frames, id_a, "-o", color=PRIMARY, linewidth=2, markersize=5, label="Vehicle A")
    ax.plot(frames, id_b, "-s", color="#b7802f", linewidth=2, markersize=5, label="Vehicle B")
    valid_c = ~np.isnan(id_c)
    ax.plot(np.array(frames)[valid_c], np.array(id_c)[valid_c], "-^",
            color="#c44e52", linewidth=2, markersize=5, label="Vehicle C")

    # highlight ID switch
    ax.axvspan(11.5, 12.5, color="#d62728", alpha=0.15)
    ax.annotate("ID Switch", xy=(12, 3), xytext=(14, 4.5),
                fontsize=13, fontweight="bold", color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=2))

    ax.set_xlabel("Frame")
    ax.set_ylabel("Track ID")
    ax.set_yticks([1, 2, 3, 4])
    ax.legend(loc="upper left", fontsize=11)
    ax.set_title("Tracking ID Switch Event", fontsize=16, fontweight="bold")
    savefig("09_tracking_id_switch.png")


# ---------------------------------------------------------------------------
# Figure 10: Tracking quality metrics
# ---------------------------------------------------------------------------

def fig_tracking_quality_metrics() -> None:
    quality = np.linspace(0.3, 1.0, 15)

    # MOTA improves with quality (starts negative, crosses zero, approaches 1)
    mota = -0.3 + 1.2 * quality - 0.1 * quality ** 2
    mota = np.clip(mota, -0.3, 0.98)

    # IDF1 also improves but more gradually
    idf1 = 0.2 + 0.7 * quality + 0.05 * quality ** 2
    idf1 = np.clip(idf1, 0.0, 0.98)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(quality, mota, "-o", color=PRIMARY, linewidth=2.5, markersize=6, label="MOTA")
    ax.plot(quality, idf1, "-s", color="#b7802f", linewidth=2.5, markersize=6, label="IDF1")
    ax.axhline(0, color="grey", linestyle=":", linewidth=1)
    ax.set_xlabel("Tracking Quality Level")
    ax.set_ylabel("Metric Score")
    ax.set_xlim(0.3, 1.0)
    ax.set_ylim(-0.35, 1.05)
    ax.legend(fontsize=13)
    ax.set_title("MOTA and IDF1 vs Tracking Quality", fontsize=16, fontweight="bold")
    savefig("10_tracking_quality_metrics.png")


# ---------------------------------------------------------------------------
# CSV tables
# ---------------------------------------------------------------------------

def csv_detection_evaluation() -> None:
    classes = ["Car", "Bus", "Truck", "Pedestrian", "Cyclist", "Motorcycle"]
    precision = [0.85, 0.78, 0.72, 0.65, 0.60, 0.52]
    recall =    [0.80, 0.70, 0.66, 0.58, 0.50, 0.45]
    ap =        [0.82, 0.74, 0.69, 0.61, 0.55, 0.48]
    f1 = [2 * p * r / (p + r) for p, r in zip(precision, recall)]

    df = pd.DataFrame({
        "class": classes,
        "precision": precision,
        "recall": recall,
        "ap": ap,
        "f1": f1,
    })
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / "detection_evaluation.csv", index=False)


def csv_tracking_evaluation() -> None:
    quality_levels = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    mota_vals = []
    motp_vals = []
    idf1_vals = []
    for q in quality_levels:
        m = -0.3 + 1.2 * q - 0.1 * q ** 2
        mota_vals.append(round(np.clip(m, -0.3, 0.98), 3))
        motp_vals.append(round(0.5 + 0.45 * q, 3))
        id = 0.2 + 0.7 * q + 0.05 * q ** 2
        idf1_vals.append(round(np.clip(id, 0.0, 0.98), 3))

    df = pd.DataFrame({
        "quality_level": quality_levels,
        "MOTA": mota_vals,
        "MOTP": motp_vals,
        "IDF1": idf1_vals,
    })
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / "tracking_evaluation.csv", index=False)


def csv_counting_accuracy() -> None:
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    true_count = 120
    # estimated count is exact at 0.5, degrades at extremes
    estimated = [145, 135, 125, 120, 115, 105, 85]
    mae = [abs(e - true_count) for e in estimated]

    df = pd.DataFrame({
        "confidence_threshold": thresholds,
        "true_count": true_count,
        "estimated_count": estimated,
        "absolute_error": mae,
    })
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / "counting_accuracy.csv", index=False)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating Chapter 08 visuals ...")

    fig_blur_detection()
    print("  01_blur_detection.png")

    fig_augmentation_examples()
    print("  02_augmentation_examples.png")

    fig_iou_diagram()
    print("  03_iou_diagram.png")

    fig_nms_process()
    print("  04_nms_process.png")

    fig_precision_recall_curve()
    print("  05_precision_recall_curve.png")

    fig_ap_interpolation()
    print("  06_ap_interpolation.png")

    fig_per_class_ap()
    print("  07_per_class_ap.png")

    fig_counting_line_logic()
    print("  08_counting_line_logic.png")

    fig_tracking_id_switch()
    print("  09_tracking_id_switch.png")

    fig_tracking_quality_metrics()
    print("  10_tracking_quality_metrics.png")

    csv_detection_evaluation()
    print("  detection_evaluation.csv")

    csv_tracking_evaluation()
    print("  tracking_evaluation.csv")

    csv_counting_accuracy()
    print("  counting_accuracy.csv")

    n_fig = len(list(OUT_DIR.glob("*.png")))
    n_csv = len(list(RESULTS_DIR.glob("*.csv")))
    print(f"\nDone: {n_fig} figures in {OUT_DIR}, {n_csv} CSV tables in {RESULTS_DIR}")


if __name__ == "__main__":
    main()
