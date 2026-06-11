"""Chapter 4: Poisson and negative-binomial models for hourly trip counts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error

from common import DATA_DIR, download_and_extract_zip, ensure_dirs


BIKE_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"


def main() -> None:
    ensure_dirs()
    folder = download_and_extract_zip(BIKE_URL, DATA_DIR / "bike_sharing")
    data = pd.read_csv(folder / "hour.csv")
    data["date"] = pd.to_datetime(data["dteday"])
    train = data[data["date"] < "2012-10-01"].copy()
    test = data[data["date"] >= "2012-10-01"].copy()
    formula = "cnt ~ temp + hum + windspeed + C(hr) + C(workingday) + C(weathersit)"
    poisson = smf.glm(formula, train, family=sm.families.Poisson()).fit()
    dispersion = poisson.pearson_chi2 / poisson.df_resid
    fitted = poisson.fittedvalues.to_numpy()
    observed = train["cnt"].to_numpy()
    alpha = np.maximum(0.01, np.mean(((observed - fitted) ** 2 - observed) / fitted**2))
    negative_binomial = smf.glm(
        formula, train, family=sm.families.NegativeBinomial(alpha=alpha)
    ).fit()
    for name, model in [("Poisson", poisson), ("Negative binomial", negative_binomial)]:
        prediction = np.maximum(0, model.predict(test))
        print(f"{name} MAE: {mean_absolute_error(test['cnt'], prediction):.2f}")
    print(f"Poisson dispersion statistic: {dispersion:.2f}")
    print(f"Estimated negative-binomial alpha: {alpha:.3f}")
    print("Incidence-rate ratios for numeric variables:")
    print(np.exp(negative_binomial.params[["temp", "hum", "windspeed"]]).round(3))


if __name__ == "__main__":
    main()
