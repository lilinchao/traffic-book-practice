from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


RAW_PATH = Path("data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv")
OUT_PATH = Path("data/processed/nyc_crash_borough_month_panel_from_sample_2023.csv")


def to_int(value: str) -> int:
    if not value:
        return 0
    return int(float(value))


def month_from_date(value: str) -> str:
    return value[:7]


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "crashes": 0,
            "persons_injured": 0,
            "persons_killed": 0,
            "pedestrians_injured": 0,
            "cyclists_injured": 0,
            "motorists_injured": 0,
            "driver_inattention_crashes": 0,
            "failure_to_yield_crashes": 0,
        }
    )

    with RAW_PATH.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            borough = (row.get("borough") or "UNKNOWN").strip() or "UNKNOWN"
            month = month_from_date(row["crash_date"])
            key = (borough, month)
            values = panel[key]
            values["crashes"] += 1
            values["persons_injured"] += to_int(row.get("number_of_persons_injured", "0"))
            values["persons_killed"] += to_int(row.get("number_of_persons_killed", "0"))
            values["pedestrians_injured"] += to_int(row.get("number_of_pedestrians_injured", "0"))
            values["cyclists_injured"] += to_int(row.get("number_of_cyclist_injured", "0"))
            values["motorists_injured"] += to_int(row.get("number_of_motorist_injured", "0"))

            factor = (row.get("contributing_factor_vehicle_1") or "").lower()
            if "driver inattention" in factor:
                values["driver_inattention_crashes"] += 1
            if "failure to yield" in factor:
                values["failure_to_yield_crashes"] += 1

    fieldnames = [
        "borough",
        "month",
        "crashes",
        "persons_injured",
        "persons_killed",
        "pedestrians_injured",
        "cyclists_injured",
        "motorists_injured",
        "driver_inattention_crashes",
        "failure_to_yield_crashes",
    ]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for (borough, month), values in sorted(panel.items()):
            writer.writerow({"borough": borough, "month": month, **values})


if __name__ == "__main__":
    main()
