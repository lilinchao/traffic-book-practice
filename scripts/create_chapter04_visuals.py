from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.discrete.count_model import ZeroInflatedPoisson


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/stats19_collision_casualty_tabular_2023_sample.csv"
OUT_DIR = ROOT / "assets/chapter-04"
RESULTS_DIR = ROOT / "data/results/chapter-04"


def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close()


def exponentiated_table(model, label: str) -> pd.DataFrame:
    conf = model.conf_int()
    table = pd.DataFrame(
        {
            "term": model.params.index,
            "coef": model.params.values,
            label: np.exp(model.params.values),
            "ci_low": np.exp(conf[0].values),
            "ci_high": np.exp(conf[1].values),
            "p_value": model.pvalues.values,
        }
    )
    return table


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    df = pd.read_csv(DATA_PATH)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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
    logit_table = exponentiated_table(logit_model, "odds_ratio")
    logit_table.to_csv(RESULTS_DIR / "logistic_regression_odds_ratios.csv", index=False)
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
    poisson_table = exponentiated_table(poisson_model, "incidence_rate_ratio")
    poisson_table.to_csv(RESULTS_DIR / "poisson_incidence_rate_ratios.csv", index=False)
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

    negative_binomial_model = smf.glm(
        count_formula,
        data=df,
        family=sm.families.NegativeBinomial(),
    ).fit()
    comparison = pd.DataFrame(
        {
            "model": ["Poisson", "Negative Binomial"],
            "aic": [poisson_model.aic, negative_binomial_model.aic],
            "bic": [poisson_model.bic, negative_binomial_model.bic],
            "dispersion": [poisson_model.pearson_chi2 / poisson_model.df_resid, np.nan],
        }
    )
    comparison.to_csv(RESULTS_DIR / "count_model_comparison.csv", index=False)

    comparison_plot = comparison.melt(id_vars="model", value_vars=["aic", "bic"])
    ax = sns.barplot(data=comparison_plot, x="variable", y="value", hue="model")
    ax.set_title("Count Model Comparison: AIC and BIC")
    ax.set_xlabel("")
    ax.set_ylabel("Information criterion")
    plt.legend(title="")
    savefig("07_count_model_comparison.png")

    irr = poisson_table[poisson_table["term"] != "Intercept"].copy()
    irr = irr.sort_values("incidence_rate_ratio")
    ax = irr.set_index("term")["incidence_rate_ratio"].plot(kind="barh", color="#b7802f")
    ax.axvline(1, color="#101817", linestyle="--", linewidth=1)
    ax.set_title("Poisson Regression Incidence Rate Ratios")
    ax.set_xlabel("Incidence rate ratio for casualty count")
    savefig("08_poisson_incidence_rate_ratios.png")

    scenario_grid = pd.DataFrame(
        [
            {
                "scenario": "Urban daylight, 30 mph",
                "speed_limit": 30,
                "rural": 0,
                "darkness": 0,
                "adverse_weather": 0,
                "wet_or_icy": 0,
                "junction_present": 1,
                "weekend": 0,
                "number_of_vehicles": 2,
            },
            {
                "scenario": "Urban darkness, 30 mph",
                "speed_limit": 30,
                "rural": 0,
                "darkness": 1,
                "adverse_weather": 0,
                "wet_or_icy": 0,
                "junction_present": 1,
                "weekend": 0,
                "number_of_vehicles": 2,
            },
            {
                "scenario": "Rural daylight, 60 mph",
                "speed_limit": 60,
                "rural": 1,
                "darkness": 0,
                "adverse_weather": 0,
                "wet_or_icy": 0,
                "junction_present": 0,
                "weekend": 0,
                "number_of_vehicles": 2,
            },
            {
                "scenario": "Rural darkness, wet, 60 mph",
                "speed_limit": 60,
                "rural": 1,
                "darkness": 1,
                "adverse_weather": 1,
                "wet_or_icy": 1,
                "junction_present": 0,
                "weekend": 1,
                "number_of_vehicles": 2,
            },
        ]
    )
    scenario_grid["predicted_severe_probability"] = logit_model.predict(scenario_grid)
    scenario_grid["predicted_casualties_poisson"] = poisson_model.predict(scenario_grid)
    scenario_grid["predicted_casualties_negative_binomial"] = negative_binomial_model.predict(
        scenario_grid
    )
    scenario_grid.to_csv(RESULTS_DIR / "scenario_predictions.csv", index=False)

    scenario_long = scenario_grid.melt(
        id_vars="scenario",
        value_vars=["predicted_severe_probability"],
        var_name="metric",
        value_name="value",
    )
    ax = sns.barplot(data=scenario_long, y="scenario", x="value", color="#176b5b")
    ax.set_title("Scenario Predictions: Severe/Fatal Collision Probability")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("")
    savefig("09_scenario_severe_probability.png")

    casualty_scenarios = scenario_grid.melt(
        id_vars="scenario",
        value_vars=["predicted_casualties_poisson", "predicted_casualties_negative_binomial"],
        var_name="model",
        value_name="predicted_casualties",
    )
    ax = sns.barplot(data=casualty_scenarios, y="scenario", x="predicted_casualties", hue="model")
    ax.set_title("Scenario Predictions: Expected Casualty Count")
    ax.set_xlabel("Predicted casualties")
    ax.set_ylabel("")
    plt.legend(title="")
    savefig("10_scenario_predicted_casualties.png")

    predictors = [
        "speed_limit",
        "rural",
        "darkness",
        "adverse_weather",
        "wet_or_icy",
        "junction_present",
        "weekend",
        "number_of_vehicles",
    ]
    zip_exog = sm.add_constant(df[predictors].astype(float))
    zip_infl = sm.add_constant(df[["rural", "darkness", "junction_present"]].astype(float))
    zip_model = ZeroInflatedPoisson(
        endog=df["vulnerable_casualties"],
        exog=zip_exog,
        exog_infl=zip_infl,
    ).fit(disp=False, maxiter=200)
    zip_params = pd.DataFrame(
        {
            "term": zip_model.params.index,
            "coef": zip_model.params.values,
            "exp_coef": np.exp(zip_model.params.values),
            "p_value": zip_model.pvalues.values,
        }
    )
    zip_params["component"] = np.where(zip_params["term"].str.startswith("inflate_"), "zero_inflation", "count")
    zip_params.to_csv(RESULTS_DIR / "zero_inflated_poisson_results.csv", index=False)

    zip_count = zip_params[
        (zip_params["component"] == "count") & (zip_params["term"] != "const")
    ].copy()
    zip_count = zip_count.sort_values("exp_coef")
    ax = zip_count.set_index("term")["exp_coef"].plot(kind="barh", color="#176b5b")
    ax.axvline(1, color="#101817", linestyle="--", linewidth=1)
    ax.set_title("Zero-inflated Poisson Count Component")
    ax.set_xlabel("Exponentiated coefficient")
    savefig("11_zip_count_component.png")

    zip_sample = df.sample(2500, random_state=8).copy()
    sample_exog = sm.add_constant(zip_sample[predictors].astype(float), has_constant="add")
    sample_infl = sm.add_constant(
        zip_sample[["rural", "darkness", "junction_present"]].astype(float),
        has_constant="add",
    )
    zip_sample["predicted_vulnerable_casualties"] = zip_model.predict(
        exog=sample_exog,
        exog_infl=sample_infl,
    )
    ax = sns.scatterplot(
        data=zip_sample,
        x="vulnerable_casualties",
        y="predicted_vulnerable_casualties",
        alpha=0.45,
        color="#176b5b",
    )
    ax.set_title("Zero-inflated Poisson: Observed vs Predicted Vulnerable Casualties")
    ax.set_xlabel("Observed vulnerable casualties")
    ax.set_ylabel("Predicted vulnerable casualties")
    savefig("12_zip_observed_vs_predicted.png")

    print(f"Created {len(list(OUT_DIR.glob('*.png')))} figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
