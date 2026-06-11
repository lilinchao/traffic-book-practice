"""Chapter 6: seasonal baseline and SARIMA for hourly bike demand."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

from common import DATA_DIR, OUTPUT_DIR, download_and_extract_zip, ensure_dirs


BIKE_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"


def report(name: str, actual: pd.Series, prediction: pd.Series) -> None:
    print(f"{name} MAE: {mean_absolute_error(actual, prediction):.2f}")
    print(f"{name} RMSE: {mean_squared_error(actual, prediction) ** 0.5:.2f}")


def main() -> None:
    ensure_dirs()
    folder = download_and_extract_zip(BIKE_URL, DATA_DIR / "bike_sharing")
    raw = pd.read_csv(folder / "hour.csv")
    raw["timestamp"] = pd.to_datetime(raw["dteday"]) + pd.to_timedelta(raw["hr"], unit="h")
    series = raw.set_index("timestamp")["cnt"].asfreq("h").interpolate(limit=2)
    series = series.iloc[-24 * 120 :]
    train, test = series.iloc[:-168], series.iloc[-168:]
    seasonal = series.shift(168).reindex(test.index)
    report("Weekly seasonal baseline", test, seasonal)
    model = SARIMAX(
        train,
        order=(2, 1, 2),
        seasonal_order=(1, 0, 1, 24),
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(method="powell", maxiter=100, disp=False)
    forecast = model.forecast(len(test)).clip(lower=0)
    report("SARIMA", test, forecast)
    ax = test.plot(label="Observed", figsize=(10, 4))
    seasonal.plot(ax=ax, label="Weekly baseline", alpha=0.8)
    forecast.plot(ax=ax, label="SARIMA", alpha=0.8)
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ch06_forecast_comparison.png", dpi=180)


if __name__ == "__main__":
    main()
