from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/stats19_collision_casualty_tabular_2023_sample.csv"
OUT_DIR = ROOT / "assets/chapter-04"


def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    df = pd.read_csv(DATA_PATH)

    severity_by_speed = (
        df.groupby("speed_limit", as_index=False)
        .agg(severe_rate=("severe_or_fatal", "mean"), n=("severe_or_fatal", "size"))
    )
    ax = sns.barplot(data=severity_by_speed, x="speed_limit", y="severe_rate", color="#176b5b")
    ax.set_title("Severe or Fatal Collision Rate by Speed Limit")
    ax.set_xlabel("Speed limit")
    ax.set_ylabel("Severe/fatal rate")
    savefig("01_severity_by_speed_limit.png")

    rate_table = df.pivot_table(
        index="area_label",
        columns="darkness",
        values="severe_or_fatal",
        aggfunc="mean",
    ).rename(columns={0: "Daylight", 1: "Darkness"})
    ax = sns.heatmap(rate_table, annot=True, fmt=".1%", cmap="YlGnBu")
    ax.set_title("Severe/Fatal Rate by Area and Lighting")
    ax.set_xlabel("")
    ax.set_ylabel("")
    savefig("02_severity_area_lighting_heatmap.png")

    ax = sns.boxplot(data=df, x="area_label", y="number_of_casualties", color="#d9e0dc")
    ax.set_title("Casualty Count Distribution by Urban/Rural Area")
    ax.set_xlabel("")
    ax.set_ylabel("Number of casualties")
    savefig("03_casualty_count_by_area.png")

    ax = df["vulnerable_casualties"].value_counts().sort_index().plot(kind="bar", color="#176b5b")
    ax.set_title("Zero-heavy Distribution of Vulnerable Road-user Casualties")
    ax.set_xlabel("Vulnerable casualties in collision")
    ax.set_ylabel("Collision count")
    plt.xticks(rotation=0)
    savefig("04_vulnerable_zero_distribution.png")

    formula = (
        "severe_or_fatal ~ speed_limit + rural + darkness + adverse_weather + "
        "wet_or_icy + junction_present + weekend + number_of_vehicles"
    )
    logit_model = smf.logit(formula, data=df).fit(disp=False, maxiter=200)
    odds = np.exp(logit_model.params.drop("Intercept")).sort_values()
    ax = odds.plot(kind="barh", color="#176b5b")
    ax.axvline(1, color="#101817", linestyle="--", linewidth=1)
    ax.set_title("Logistic Regression Odds Ratios")
    ax.set_xlabel("Odds ratio for severe/fatal collision")
    savefig("05_logistic_odds_ratios.png")

    count_formula = (
        "number_of_casualties ~ speed_limit + rural + darkness + adverse_weather + "
        "wet_or_icy + junction_present + weekend + number_of_vehicles"
    )
    poisson_model = smf.glm(count_formula, data=df, family=sm.families.Poisson()).fit()
    sample = df.sample(2500, random_state=7).copy()
    sample["predicted_casualties"] = poisson_model.predict(sample)
    ax = sns.scatterplot(
        data=sample,
        x="number_of_casualties",
        y="predicted_casualties",
        alpha=0.45,
        color="#176b5b",
    )
    ax.set_title("Poisson Regression: Observed vs Predicted Casualties")
    ax.set_xlabel("Observed casualties")
    ax.set_ylabel("Predicted casualties")
    savefig("06_poisson_observed_vs_predicted.png")

    print(f"Created {len(list(OUT_DIR.glob('*.png')))} figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
