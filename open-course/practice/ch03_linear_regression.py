"""Chapter 3: connect derivatives, loss, and gradient descent to traffic demand."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from common import DATA_DIR, OUTPUT_DIR, download_and_extract_zip, ensure_dirs


BIKE_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"


def gradient_descent(x: np.ndarray, y: np.ndarray, steps: int = 1500, lr: float = 0.03):
    weights = np.zeros(x.shape[1])
    losses = []
    for _ in range(steps):
        error = x @ weights - y
        losses.append(float(np.mean(error**2)))
        gradient = 2 * x.T @ error / len(y)
        weights -= lr * gradient
    return weights, losses


def main() -> None:
    ensure_dirs()
    folder = download_and_extract_zip(BIKE_URL, DATA_DIR / "bike_sharing")
    data = pd.read_csv(folder / "hour.csv")
    features = ["temp", "atemp", "hum", "windspeed", "hr", "workingday"]
    x = data[features].astype(float)
    y = data["cnt"].to_numpy(dtype=float)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)
    x_train_design = np.column_stack([np.ones(len(x_train_scaled)), x_train_scaled])
    x_test_design = np.column_stack([np.ones(len(x_test_scaled)), x_test_scaled])
    weights, losses = gradient_descent(x_train_design, y_train)
    prediction = np.maximum(0, x_test_design @ weights)
    print(f"MAE: {mean_absolute_error(y_test, prediction):.2f}")
    print(f"RMSE: {mean_squared_error(y_test, prediction) ** 0.5:.2f}")
    print(dict(zip(["intercept", *features], weights.round(3))))
    plt.plot(losses)
    plt.xlabel("Iteration")
    plt.ylabel("Mean squared error")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ch03_gradient_descent_loss.png", dpi=180)


if __name__ == "__main__":
    main()

