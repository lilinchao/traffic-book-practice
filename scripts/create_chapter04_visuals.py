from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.discrete.count_model import ZeroInflatedPoisson


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv"
PANEL_PATH = ROOT / "data/processed/nyc_crash_borough_month_panel_2023.csv"
OUT_DIR = ROOT / "assets/chapter-04"


def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    crashes = pd.read_csv(RAW_PATH, parse_dates=["crash_date"])
    panel = pd.read_csv(PANEL_PATH)
    numeric_cols = [
        "month",
        "crashes",
        "persons_injured",
        "persons_killed",
        "pedestrians_injured",
        "cyclists_injured",
        "motorists_injured",
    ]
    panel[numeric_cols] = panel[numeric_cols].apply(pd.to_numeric)
    panel["injury_rate_per_100_crashes"] = panel["persons_injured"] / panel["crashes"] * 100
    return crashes, panel


def add_model_columns(panel: pd.DataFrame) -> pd.DataFrame:
    model_df = panel.copy()
    model_df["month_centered"] = model_df["month"] - model_df["month"].mean()
    model_df["summer"] = model_df["month"].isin([6, 7, 8]).astype(int)

    poisson_model = smf.poisson(
        "crashes ~ month_centered + C(borough)",
        data=model_df,
    ).fit(disp=False, maxiter=200)
    model_df["poisson_predicted_crashes"] = poisson_model.predict(model_df)

    zip_exog = sm.add_constant(model_df[["month_centered", "summer"]].astype(float))
    zip_infl = zip_exog[["const", "summer"]]
    zip_model = ZeroInflatedPoisson(
        endog=model_df["persons_killed"],
        exog=zip_exog,
        exog_infl=zip_infl,
        exposure=model_df["crashes"],
    ).fit(disp=False, maxiter=300)
    model_df["zip_predicted_deaths"] = zip_model.predict(
        exog=zip_exog,
        exog_infl=zip_infl,
        exposure=model_df["crashes"],
    )
    return model_df


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    crashes, panel = load_data()
    model_df = add_model_columns(panel)

    ax = sns.lineplot(data=panel, x="month", y="crashes", hue="borough", marker="o")
    ax.set_title("Monthly Crash Counts by NYC Borough, 2023")
    ax.set_xlabel("Month")
    ax.set_ylabel("Crashes")
    ax.set_xticks(range(1, 13))
    plt.legend(title="Borough", bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig("01_monthly_crash_trends.png")

    crash_wide = panel.pivot(index="borough", columns="month", values="crashes")
    ax = sns.heatmap(crash_wide, annot=True, fmt=".0f", cmap="YlGnBu")
    ax.set_title("Crash Count Heatmap by Borough and Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Borough")
    savefig("02_crash_heatmap.png")

    ax = sns.lineplot(
        data=panel,
        x="month",
        y="injury_rate_per_100_crashes",
        hue="borough",
        marker="o",
    )
    ax.set_title("Injury Rate per 100 Crashes by Borough")
    ax.set_xlabel("Month")
    ax.set_ylabel("Injured Persons per 100 Crashes")
    ax.set_xticks(range(1, 13))
    plt.legend(title="Borough", bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig("03_injury_rate_trends.png")

    injury_summary = pd.Series(
        {
            "Pedestrians": crashes["number_of_pedestrians_injured"].sum(),
            "Cyclists": crashes["number_of_cyclist_injured"].sum(),
            "Motorists": crashes["number_of_motorist_injured"].sum(),
        }
    )
    ax = injury_summary.plot(kind="bar", color=["#b7802f", "#176b5b", "#101817"])
    ax.set_title("Injuries by Road User Type in Raw Crash Sample")
    ax.set_xlabel("")
    ax.set_ylabel("Injured Persons")
    plt.xticks(rotation=0)
    savefig("04_injury_structure.png")

    ax = sns.scatterplot(
        data=model_df,
        x="crashes",
        y="poisson_predicted_crashes",
        hue="borough",
        s=120,
    )
    limit = max(model_df["crashes"].max(), model_df["poisson_predicted_crashes"].max())
    ax.plot([0, limit], [0, limit], color="#101817", linestyle="--", linewidth=1)
    ax.set_title("Poisson Regression: Observed vs Predicted Crashes")
    ax.set_xlabel("Observed Crashes")
    ax.set_ylabel("Predicted Crashes")
    plt.legend(title="Borough", bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig("05_poisson_observed_vs_predicted.png")

    death_counts = model_df["persons_killed"].value_counts().sort_index()
    ax = death_counts.plot(kind="bar", color="#176b5b")
    ax.set_title("Distribution of Monthly Death Counts")
    ax.set_xlabel("Deaths in Borough-Month")
    ax.set_ylabel("Number of Borough-Month Observations")
    plt.xticks(rotation=0)
    savefig("06_death_zero_distribution.png")

    print(f"Created {len(list(OUT_DIR.glob('*.png')))} figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
