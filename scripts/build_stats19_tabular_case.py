from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
COLLISION_PATH = ROOT / "data/raw/stats19_collision_2023.csv"
CASUALTY_PATH = ROOT / "data/raw/stats19_casualty_2023.csv"
OUT_PATH = ROOT / "data/processed/stats19_collision_casualty_tabular_2023_sample.csv"


ROAD_TYPE = {
    1: "Roundabout",
    2: "One way street",
    3: "Dual carriageway",
    6: "Single carriageway",
    7: "Slip road",
    9: "Unknown",
    12: "One way street or slip road",
}

LIGHT_CONDITIONS = {
    1: "Daylight",
    4: "Darkness - lights lit",
    5: "Darkness - lights unlit",
    6: "Darkness - no lighting",
    7: "Darkness - lighting unknown",
}

WEATHER_CONDITIONS = {
    1: "Fine no high winds",
    2: "Raining no high winds",
    3: "Snowing no high winds",
    4: "Fine + high winds",
    5: "Raining + high winds",
    6: "Snowing + high winds",
    7: "Fog or mist",
    8: "Other",
    9: "Unknown",
}

ROAD_SURFACE = {
    1: "Dry",
    2: "Wet or damp",
    3: "Snow",
    4: "Frost or ice",
    5: "Flood over 3cm",
    6: "Oil or diesel",
    7: "Mud",
    9: "Unknown",
}


def main() -> None:
    collisions = pd.read_csv(COLLISION_PATH, low_memory=False)
    casualties = pd.read_csv(CASUALTY_PATH, low_memory=False)

    vulnerable_counts = (
        casualties.assign(
            vulnerable_casualty=casualties["casualty_type"].isin([0, 1]).astype(int)
        )
        .groupby("collision_index", as_index=False)["vulnerable_casualty"]
        .sum()
        .rename(columns={"vulnerable_casualty": "vulnerable_casualties"})
    )

    cols = [
        "collision_index",
        "collision_severity",
        "number_of_vehicles",
        "number_of_casualties",
        "day_of_week",
        "time",
        "road_type",
        "speed_limit",
        "junction_detail",
        "light_conditions",
        "weather_conditions",
        "road_surface_conditions",
        "urban_or_rural_area",
        "did_police_officer_attend_scene_of_accident",
        "longitude",
        "latitude",
    ]
    df = collisions[cols].merge(vulnerable_counts, on="collision_index", how="left")
    df["vulnerable_casualties"] = df["vulnerable_casualties"].fillna(0).astype(int)

    df = df[(df["speed_limit"] > 0) & (df["speed_limit"] <= 70)]
    df = df[df["collision_severity"].isin([1, 2, 3])]
    df = df[df["urban_or_rural_area"].isin([1, 2])]

    df["severe_or_fatal"] = df["collision_severity"].isin([1, 2]).astype(int)
    df["fatal"] = (df["collision_severity"] == 1).astype(int)
    df["rural"] = (df["urban_or_rural_area"] == 2).astype(int)
    df["darkness"] = df["light_conditions"].isin([4, 5, 6, 7]).astype(int)
    df["adverse_weather"] = df["weather_conditions"].isin([2, 3, 5, 6, 7, 8]).astype(int)
    df["wet_or_icy"] = df["road_surface_conditions"].isin([2, 3, 4, 5]).astype(int)
    df["junction_present"] = (~df["junction_detail"].isin([0, -1])).astype(int)
    df["weekend"] = df["day_of_week"].isin([1, 7]).astype(int)

    df["road_type_label"] = df["road_type"].map(ROAD_TYPE).fillna("Other")
    df["light_label"] = df["light_conditions"].map(LIGHT_CONDITIONS).fillna("Other")
    df["weather_label"] = df["weather_conditions"].map(WEATHER_CONDITIONS).fillna("Other")
    df["surface_label"] = df["road_surface_conditions"].map(ROAD_SURFACE).fillna("Other")
    df["area_label"] = df["urban_or_rural_area"].map({1: "Urban", 2: "Rural"})

    keep = [
        "collision_index",
        "severe_or_fatal",
        "fatal",
        "number_of_casualties",
        "vulnerable_casualties",
        "number_of_vehicles",
        "speed_limit",
        "rural",
        "darkness",
        "adverse_weather",
        "wet_or_icy",
        "junction_present",
        "weekend",
        "road_type_label",
        "light_label",
        "weather_label",
        "surface_label",
        "area_label",
        "longitude",
        "latitude",
    ]

    sample = (
        df[keep]
        .sample(n=min(25000, len(df)), random_state=42)
        .sort_values("collision_index")
        .reset_index(drop=True)
    )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(sample):,} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
