"""Chapter 7: lagged multi-sensor prediction with the UCI PeMS-SF data."""

from __future__ import annotations

import re

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from common import DATA_DIR, download_and_extract_zip, ensure_dirs


PEMS_URL = "https://archive.ics.uci.edu/static/public/204/pems+sf.zip"


def parse_pems(path, max_days):
    days = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.strip("[]")
        rows = []
        for row in line.split(";"):
            values = np.fromstring(re.sub(r"\s+", " ", row.strip()), sep=" ")
            if values.size:
                rows.append(values)
        if rows:
            days.append(np.vstack(rows))
        if len(days) >= max_days:
            break
    return days


def make_examples(days, sensor_count=40, lags=6):
    x, y = [], []
    for day in days:
        # UCI stores each day as sensors x 10-minute timestamps.
        matrix = day[:sensor_count, :].T
        for t in range(lags, len(matrix)):
            x.append(matrix[t - lags : t].reshape(-1))
            y.append(matrix[t])
    return np.asarray(x), np.asarray(y)


def main() -> None:
    ensure_dirs()
    folder = download_and_extract_zip(PEMS_URL, DATA_DIR / "pems_sf")
    train_days = parse_pems(folder / "PEMS_train", max_days=80)
    test_days = parse_pems(folder / "PEMS_test", max_days=20)
    x_train, y_train = make_examples(train_days)
    x_test, y_test = make_examples(test_days)
    baseline_scores = []
    model_scores = []
    for sensor in [0, 5, 10]:
        historical = x_test[:, -y_test.shape[1] + sensor]
        model = HistGradientBoostingRegressor(
            max_iter=100, max_depth=6, learning_rate=0.08, random_state=42
        ).fit(x_train, y_train[:, sensor])
        prediction = model.predict(x_test)
        baseline_scores.append(mean_absolute_error(y_test[:, sensor], historical))
        model_scores.append(mean_absolute_error(y_test[:, sensor], prediction))
    print(f"Last-value baseline mean MAE: {np.mean(baseline_scores):.4f}")
    print(f"Multi-sensor lag model mean MAE: {np.mean(model_scores):.4f}")


if __name__ == "__main__":
    main()
