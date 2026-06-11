"""Chapter 8: YOLO detection, tracking, and line-crossing vehicle counts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO


VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path, help="UA-DETRAC video or another traffic video")
    parser.add_argument("--output", type=Path, default=Path("outputs/ch08_counted.mp4"))
    parser.add_argument("--line-ratio", type=float, default=0.65)
    args = parser.parse_args()
    model = YOLO("yolov8n.pt")
    capture = cv2.VideoCapture(str(args.video))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    line_y = int(height * args.line_ratio)
    previous_y = {}
    counted_ids = set()
    counts = Counter()
    for result in model.track(source=str(args.video), stream=True, persist=True, verbose=False):
        frame = result.orig_img.copy()
        cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2)
        if result.boxes.id is not None:
            for box, track_id, class_id in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.id.int().cpu().tolist(),
                result.boxes.cls.int().cpu().tolist(),
            ):
                if class_id not in VEHICLE_CLASSES:
                    continue
                x1, y1, x2, y2 = map(int, box)
                center_y = (y1 + y2) // 2
                if previous_y.get(track_id, center_y) < line_y <= center_y and track_id not in counted_ids:
                    counts[VEHICLE_CLASSES[class_id]] += 1
                    counted_ids.add(track_id)
                previous_y[track_id] = center_y
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                cv2.putText(frame, f"{VEHICLE_CLASSES[class_id]} {track_id}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        cv2.putText(frame, str(dict(counts)), (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        writer.write(frame)
    capture.release()
    writer.release()
    print(dict(counts))


if __name__ == "__main__":
    main()

