"""Chapter 5: spatial quality control, KDE, and DBSCAN for NYC crashes."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy.stats import gaussian_kde
from sklearn.cluster import DBSCAN

from common import DATA_DIR, OUTPUT_DIR, ensure_dirs


API = "https://data.cityofnewyork.us/resource/h9gi-nx95.csv"


def load_crashes(limit: int = 30000) -> pd.DataFrame:
    path = DATA_DIR / "nyc_crashes_2024.csv"
    if not path.exists():
        params = {
            "$select": "crash_date,borough,latitude,longitude,number_of_persons_injured",
            "$where": "crash_date between '2024-01-01T00:00:00' and '2024-12-31T23:59:59' AND latitude IS NOT NULL AND longitude IS NOT NULL",
            "$limit": limit,
            "$order": "crash_date",
        }
        response = requests.get(API, params=params, timeout=180)
        response.raise_for_status()
        path.write_bytes(response.content)
    data = pd.read_csv(path)
    for column in ["latitude", "longitude"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.dropna(subset=["latitude", "longitude"]).query(
        "40.45 < latitude < 41.0 and -74.3 < longitude < -73.65"
    )


def main() -> None:
    ensure_dirs()
    data = load_crashes()
    coordinates = data[["latitude", "longitude"]].to_numpy()
    radians = np.radians(coordinates)
    labels = DBSCAN(eps=0.35 / 6371.0088, min_samples=15, metric="haversine").fit_predict(radians)
    data["cluster"] = labels
    largest = data.query("cluster >= 0")["cluster"].value_counts().head(10)
    print("Largest DBSCAN clusters:")
    print(largest)
    sample = data.sample(min(8000, len(data)), random_state=42)
    xy = sample[["longitude", "latitude"]].to_numpy().T
    density = gaussian_kde(xy)(xy)
    order = np.argsort(density)
    plt.scatter(xy[0, order], xy[1, order], c=density[order], s=4, cmap="inferno")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.colorbar(label="Relative KDE density")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ch05_nyc_crash_kde.png", dpi=180)


if __name__ == "__main__":
    main()

