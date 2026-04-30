"""Generate Chapter 05 figures and result tables.

Traffic Spatial and Location Data Analysis
===========================================
Uses the NYC crash borough-month panel (2023) to illustrate spatial
analysis methods: spatial weights, Moran's I, LISA, DBSCAN, KDE,
and spatial regression (OLS / SLM / SEM).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/nyc_crash_borough_month_panel_2023.csv"
OUT_DIR = ROOT / "assets/chapter-05"
RESULTS_DIR = ROOT / "data/results/chapter-05"

# ── styling ──────────────────────────────────────────────────────────────
PRIMARY = "#176b5b"
SECONDARY = "#b7802f"
FIG_KW = dict(dpi=160, bbox_inches="tight")

# ── NYC borough metadata ────────────────────────────────────────────────
BOROUGHS = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]

# Approximate centroids (lon, lat) used for simulation & mapping
BOROUGH_CENTROIDS = {
    "Bronx":          (-73.8648, 40.8448),
    "Brooklyn":       (-73.9442, 40.6782),
    "Manhattan":      (-73.9712, 40.7831),
    "Queens":         (-73.7949, 40.7282),
    "Staten Island":  (-74.1502, 40.5795),
}

# Queen contiguity (manually defined for 5 NYC boroughs)
ADJACENCY = {
    "Bronx":          ["Manhattan"],
    "Brooklyn":       ["Manhattan", "Queens", "Staten Island"],
    "Manhattan":      ["Bronx", "Brooklyn"],
    "Queens":         ["Brooklyn"],
    "Staten Island":  ["Brooklyn"],
}


def savefig(name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, **FIG_KW)
    plt.close()


# ── helpers ──────────────────────────────────────────────────────────────

def _normalise_borough(series: pd.Series) -> pd.Series:
    """Convert 'BRONX' style names to title-case."""
    return series.str.strip().str.title().str.replace("Staten Island", "Staten Island", regex=False)


def build_weights_matrix(boroughs: list[str], adjacency: dict) -> np.ndarray:
    """Row-standardised spatial weight matrix W (n x n)."""
    n = len(boroughs)
    idx = {b: i for i, b in enumerate(boroughs)}
    W = np.zeros((n, n))
    for b, neighbours in adjacency.items():
        for nb in neighbours:
            W[idx[b], idx[nb]] = 1.0
    # row-standardise
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    W = W / row_sums
    return W


def global_morans_i(y: np.ndarray, W: np.ndarray) -> dict:
    """Compute Global Moran's I, z-score, and one-sided p-value."""
    n = len(y)
    y_bar = y.mean()
    z = y - y_bar
    S0 = W.sum()
    numerator = n * float(z @ W @ z)
    denominator = float(z @ z) * S0
    I = numerator / denominator if denominator != 0 else 0.0
    # Expected value under randomisation
    EI = -1.0 / (n - 1)
    # Variance (normal approximation)
    s1 = 0.5 * ((W + W.T) ** 2).sum()
    s2 = ((W.sum(axis=1) + W.sum(axis=0)) ** 2).sum()
    var_I = (n ** 2 * s1 - n * s2 + 3 * S0 ** 2) / (
        (n ** 2 - 1) * S0 ** 2
    ) - EI ** 2
    z_score = (I - EI) / np.sqrt(var_I) if var_I > 0 else 0.0
    from scipy.stats import norm
    p_value = 1.0 - norm.cdf(abs(z_score))  # two-tailed
    p_value = 2 * p_value  # two-sided
    return {"I": I, "EI": EI, "z_score": z_score, "p_value": p_value, "n": n}


def local_morans_i(y: np.ndarray, W: np.ndarray) -> np.ndarray:
    """Compute Local Indicators of Spatial Association (LISA)."""
    n = len(y)
    y_bar = y.mean()
    z = y - y_bar
    m2 = (z @ z) / n
    lisa = np.zeros(n)
    for i in range(n):
        lisa[i] = z[i] * float(W[i] @ z) / m2
    return lisa


def lisa_cluster_labels(y: np.ndarray, W: np.ndarray) -> list[str]:
    """Classify each observation into HH, LL, HL, LH or Not Significant."""
    y_bar = y.mean()
    z = y - y_bar
    lag = W @ z
    labels = []
    for i in range(len(y)):
        if z[i] > 0 and lag[i] > 0:
            labels.append("High-High")
        elif z[i] < 0 and lag[i] < 0:
            labels.append("Low-Low")
        elif z[i] > 0 and lag[i] < 0:
            labels.append("High-Low")
        elif z[i] < 0 and lag[i] > 0:
            labels.append("Low-High")
        else:
            labels.append("Not Significant")
    return labels


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titleweight"] = "bold"

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(DATA_PATH)
    df["borough"] = _normalise_borough(df["borough"])
    df["crashes"] = pd.to_numeric(df["crashes"], errors="coerce")
    df["persons_injured"] = pd.to_numeric(df["persons_injured"], errors="coerce")
    df["persons_killed"] = pd.to_numeric(df["persons_killed"], errors="coerce")
    df["month"] = pd.to_numeric(df["month"], errors="coerce")

    # ── 1. Borough crash bar chart ──────────────────────────────────────
    total_by_borough = (
        df.groupby("borough", as_index=False)
        .agg(total_crashes=("crashes", "sum"))
        .sort_values("total_crashes", ascending=False)
    )
    ax = sns.barplot(
        data=total_by_borough, x="borough", y="total_crashes", color=PRIMARY
    )
    ax.set_title("Total Traffic Crashes by NYC Borough (2023)")
    ax.set_xlabel("")
    ax.set_ylabel("Total crashes")
    plt.xticks(rotation=30, ha="right")
    savefig("01_borough_crash_bar.png")

    # ── 2. Crash rate choropleth-style grouped bar ─────────────────────
    crash_rate = df.pivot_table(
        index="borough", columns="month", values="crashes", aggfunc="sum"
    )
    crash_rate_long = crash_rate.reset_index().melt(
        id_vars="borough", var_name="month", value_name="crashes"
    )
    ax = sns.barplot(
        data=crash_rate_long,
        x="borough",
        y="crashes",
        hue="month",
        palette="YlGnBu",
    )
    ax.set_title("Monthly Crash Counts by Borough (Choropleth-Style View)")
    ax.set_xlabel("")
    ax.set_ylabel("Crashes")
    plt.xticks(rotation=30, ha="right")
    ax.legend(title="Month", ncol=4, fontsize="small", title_fontsize="small")
    savefig("02_crash_rate_choropleth.png")

    # ── Build spatial weights ───────────────────────────────────────────
    W = build_weights_matrix(BOROUGHS, ADJACENCY)

    # ── Spatial variable: total crashes per borough (annual) ────────────
    annual = (
        df.groupby("borough", as_index=False)
        .agg(
            total_crashes=("crashes", "sum"),
            total_injured=("persons_injured", "sum"),
            total_killed=("persons_killed", "sum"),
        )
    )
    # Align to BOROUGHS order
    annual = annual.set_index("borough").reindex(BOROUGHS).reset_index()
    y = annual["total_crashes"].values.astype(float)

    # ── 3. Moran's I scatter plot ───────────────────────────────────────
    mi = global_morans_i(y, W)
    y_bar = y.mean()
    z_y = y - y_bar
    spatial_lag = W @ z_y

    fig, ax = plt.subplots()
    ax.scatter(z_y, spatial_lag, color=PRIMARY, s=120, zorder=3)
    # Regression line through origin
    m = np.polyfit(z_y, spatial_lag, 1)
    x_line = np.linspace(z_y.min() - 100, z_y.max() + 100, 100)
    ax.plot(x_line, m[0] * x_line + m[1], color="#101817", linewidth=1.5)
    ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)
    ax.axvline(0, color="grey", linestyle="--", linewidth=0.8)
    for i, boro in enumerate(BOROUGHS):
        ax.annotate(boro, (z_y[i], spatial_lag[i]),
                    textcoords="offset points", xytext=(6, 6), fontsize=9)
    ax.set_title(f"Moran's I Scatter Plot  (I = {mi['I']:.4f}, p = {mi['p_value']:.4f})")
    ax.set_xlabel("Standardised crash count")
    ax.set_ylabel("Spatial lag of standardised crash count")
    savefig("03_morans_i_scatter.png")

    # ── Save Moran's I results ──────────────────────────────────────────
    mi_df = pd.DataFrame([mi])
    mi_df.to_csv(RESULTS_DIR / "morans_i_results.csv", index=False)

    # ── 4. LISA cluster bar chart ───────────────────────────────────────
    lisa_vals = local_morans_i(y, W)
    lisa_labels = lisa_cluster_labels(y, W)
    lisa_df = pd.DataFrame({
        "borough": BOROUGHS,
        "lisa_value": lisa_vals,
        "cluster_type": lisa_labels,
    })
    lisa_counts = lisa_df["cluster_type"].value_counts().reset_index()
    lisa_counts.columns = ["cluster_type", "count"]

    palette_lisa = {
        "High-High": "#d6604d",
        "Low-Low": "#2166ac",
        "High-Low": "#f4a582",
        "Low-High": "#92c5de",
        "Not Significant": "#cccccc",
    }
    ax = sns.barplot(
        data=lisa_counts,
        x="cluster_type",
        y="count",
        palette=palette_lisa,
    )
    ax.set_title("LISA Cluster Types Across NYC Boroughs")
    ax.set_xlabel("Cluster type")
    ax.set_ylabel("Number of boroughs")
    savefig("04_lisa_cluster.png")

    lisa_df.to_csv(RESULTS_DIR / "lisa_clusters.csv", index=False)

    # ── 5. Spatial weights heatmap ──────────────────────────────────────
    W_df = pd.DataFrame(W, index=BOROUGHS, columns=BOROUGHS)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(W_df, annot=True, fmt=".3f", cmap="YlGnBu", ax=ax, cbar_kws={"label": "Weight"})
    ax.set_title("Row-Standardised Spatial Weight Matrix (Queen Contiguity)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    savefig("05_spatial_weights_heatmap.png")

    # ── 6. DBSCAN on simulated crash points ─────────────────────────────
    from sklearn.cluster import DBSCAN

    rng = np.random.default_rng(42)
    n_per_borough = {
        "Bronx": 300,
        "Brooklyn": 600,
        "Manhattan": 500,
        "Queens": 450,
        "Staten Island": 150,
    }
    pts_lon, pts_lat, pts_borough = [], [], []
    for boro, n_pts in n_per_borough.items():
        cx, cy = BOROUGH_CENTROIDS[boro]
        pts_lon.append(rng.normal(cx, 0.015, n_pts))
        pts_lat.append(rng.normal(cy, 0.012, n_pts))
        pts_borough.extend([boro] * n_pts)

    pts_lon = np.concatenate(pts_lon)
    pts_lat = np.concatenate(pts_lat)
    coords = np.column_stack([pts_lon, pts_lat])

    db = DBSCAN(eps=0.02, min_samples=15).fit(coords)
    labels_db = db.labels_
    n_clusters = len(set(labels_db)) - (1 if -1 in labels_db else 0)
    n_noise = (labels_db == -1).sum()

    fig, ax = plt.subplots(figsize=(10, 8))
    unique_labels = set(labels_db)
    colors = sns.color_palette("husl", n_clusters)
    for k, col in zip(sorted(unique_labels), colors if -1 not in unique_labels else [(0.6, 0.6, 0.6)] + colors):
        if k == -1:
            col = (0.75, 0.75, 0.75)
            size = 8
            label = "Noise"
        else:
            size = 20
            label = f"Cluster {k}"
        mask = labels_db == k
        ax.scatter(coords[mask, 0], coords[mask, 1], s=size, c=[col], label=label, alpha=0.7)
    ax.set_title(f"DBSCAN Clustering of Simulated Crash Points ({n_clusters} clusters)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(markerscale=2, fontsize="small")
    savefig("06_dbscan_simulation.png")

    db_summary = []
    for k in sorted(unique_labels):
        mask = labels_db == k
        boro_mode = pd.Series(np.array(pts_borough)[mask]).mode().iloc[0] if mask.sum() > 0 else "N/A"
        db_summary.append({
            "cluster": k if k != -1 else "Noise",
            "n_points": int(mask.sum()),
            "dominant_borough": boro_mode,
            "mean_lon": float(coords[mask, 0].mean()),
            "mean_lat": float(coords[mask, 1].mean()),
        })
    pd.DataFrame(db_summary).to_csv(RESULTS_DIR / "dbscan_clusters.csv", index=False)

    # ── 7. KDE density contour ──────────────────────────────────────────
    from scipy.stats import gaussian_kde

    kde = gaussian_kde(coords.T, bw_method=0.15)
    xmin, xmax = coords[:, 0].min() - 0.02, coords[:, 0].max() + 0.02
    ymin, ymax = coords[:, 1].min() - 0.02, coords[:, 1].max() + 0.02
    xx, yy = np.meshgrid(np.linspace(xmin, xmax, 200), np.linspace(ymin, ymax, 200))
    zz = kde(np.column_stack([xx.ravel(), yy.ravel()]).T).reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(10, 8))
    cf = ax.contourf(xx, yy, zz, levels=15, cmap="YlGnBu", alpha=0.85)
    ax.contour(xx, yy, zz, levels=15, colors="#101817", linewidths=0.4, alpha=0.4)
    plt.colorbar(cf, ax=ax, label="Density")
    ax.set_title("KDE Density Contour of Simulated Crash Points")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    savefig("07_kde_density.png")

    # ── Spatial regression ──────────────────────────────────────────────
    # Use borough-month panel for more observations (5 boroughs x 12 months = 60)
    panel = df.copy()
    panel = panel[panel["borough"].isin(BOROUGHS)].reset_index(drop=True)
    panel = panel.sort_values(["borough", "month"])

    # Dependent variable: log(crashes + 1)
    panel["log_crashes"] = np.log1p(panel["crashes"])
    # Independent variables
    panel["log_injured"] = np.log1p(panel["persons_injured"])
    panel["month_factor"] = panel["month"].astype(float)

    # Build W for 5 boroughs (repeated for each month)
    n_boroughs = len(BOROUGHS)
    n_months = 12
    n_obs = n_boroughs * n_months

    # Expanded block-diagonal W (each month block uses same W)
    W_block = np.kron(np.eye(n_months), W)

    # OLS regression
    X_vars = ["log_injured", "month_factor"]
    X = sm.add_constant(panel[X_vars].values.astype(float))
    y_reg = panel["log_crashes"].values.astype(float)

    ols_model = sm.OLS(y_reg, X).fit()

    # ── Try spreg for spatial lag and spatial error models ──────────────
    spreg_available = False
    try:
        from spreg import OLS as SpregOLS, GM_Lag, GM_Error
        spreg_available = True
    except ImportError:
        pass

    if spreg_available:
        try:
            from libpysal.weights import W as pysal_W

            # Build PySAL weight object from block-diagonal structure
            # For spreg, we need the full 60x60 weights
            neighbours_dict = {}
            for i in range(n_obs):
                neighbours_dict[i] = [j for j in range(n_obs) if W_block[i, j] > 0]
            pysal_w = pysal_W(neighbours_dict)
            pysal_w.transform = "r"

            spreg_ols = SpregOLS(y_reg, X, w=pysal_w, name_x=["const"] + X_vars)
            slm = GM_Lag(y_reg, X, w=pysal_w, name_x=["const"] + X_vars)
            sem = GM_Error(y_reg, X, w=pysal_w, name_x=["const"] + X_vars)

            ols_aic = float(spreg_ols.aic)
            ols_bic = None  # spreg OLS doesn't expose BIC directly
            slm_aic = float(slm.aic)
            sem_aic = float(sem.aic)

            # Build coefficient comparison
            var_names = ["const", "log_injured", "month_factor"]
            coef_dict = {"variable": var_names}
            coef_dict["OLS"] = spreg_ols.betas.ravel()[: len(var_names)]
            coef_dict["SLM"] = np.append(slm.betas.ravel()[: len(var_names) - 1], [np.nan])[:len(var_names)]
            coef_dict["SEM"] = np.append(sem.betas.ravel()[: len(var_names) - 1], [np.nan])[:len(var_names)]

            # R-squared
            ols_r2 = float(spreg_ols.r2) if hasattr(spreg_ols, "r2") else ols_model.rsquared
            slm_r2 = float(slm.r2) if hasattr(slm, "r2") else np.nan
            sem_r2 = float(sem.r2) if hasattr(sem, "r2") else np.nan

            # Residuals for Moran's I
            ols_resid = spreg_ols.u.ravel()
            slm_resid = slm.u.ravel()
            sem_resid = sem.u.ravel()

        except Exception:
            spreg_available = False

    if not spreg_available:
        # Fallback: use statsmodels OLS and conceptual comparison
        coef_dict = {"variable": ["const", "log_injured", "month_factor"]}
        coef_dict["OLS"] = ols_model.params

        # Conceptual SLM: add spatially lagged dependent variable
        Wy = W_block @ y_reg
        X_slm = np.column_stack([X, Wy])
        slm_model = sm.OLS(y_reg, X_slm).fit()
        coef_dict["SLM"] = np.append(slm_model.params[:3], [np.nan])[:3]

        # Conceptual SEM: add spatially lagged error
        ols_resid_raw = ols_model.resid
        We = W_block @ ols_resid_raw
        X_sem = np.column_stack([X, We])
        sem_model = sm.OLS(y_reg, X_sem).fit()
        coef_dict["SEM"] = np.append(sem_model.params[:3], [np.nan])[:3]

        ols_aic = ols_model.aic
        slm_aic = slm_model.aic
        sem_aic = sem_model.aic

        ols_r2 = ols_model.rsquared
        slm_r2 = slm_model.rsquared
        sem_r2 = sem_model.rsquared

        ols_resid = ols_model.resid
        slm_resid = slm_model.resid
        sem_resid = sem_model.resid

    # ── 8. OLS vs SLM vs SEM coefficient comparison ────────────────────
    coef_df = pd.DataFrame(coef_dict)
    coef_long = coef_df.melt(id_vars="variable", var_name="model", value_name="coefficient")
    # Drop const for cleaner visualisation
    coef_long_no_const = coef_long[coef_long["variable"] != "const"]

    ax = sns.barplot(
        data=coef_long_no_const,
        x="variable",
        y="coefficient",
        hue="model",
        palette=[PRIMARY, SECONDARY, "#6a3d9a"],
    )
    ax.axhline(0, color="#101817", linewidth=0.8)
    ax.set_title("OLS vs Spatial Lag vs Spatial Error: Coefficient Comparison")
    ax.set_xlabel("")
    ax.set_ylabel("Coefficient estimate")
    ax.legend(title="Model")
    savefig("08_ols_vs_spatial.png")

    # ── 9. Residual Moran's I diagnostic ────────────────────────────────
    resid_mi = {}
    for name, resid in [("OLS", ols_resid), ("SLM", slm_resid), ("SEM", sem_resid)]:
        r = global_morans_i(resid, W_block)
        resid_mi[name] = r["I"]

    resid_df = pd.DataFrame(
        {"model": list(resid_mi.keys()), "residual_morans_i": list(resid_mi.values())}
    )
    ax = sns.barplot(data=resid_df, x="model", y="residual_morans_i",
                     palette=[PRIMARY, SECONDARY, "#6a3d9a"])
    ax.axhline(0, color="#101817", linewidth=0.8, linestyle="--")
    ax.set_title("Residual Spatial Autocorrelation (Moran's I) by Model")
    ax.set_xlabel("Model")
    ax.set_ylabel("Moran's I of residuals")
    savefig("09_residual_morans_i.png")

    # ── 10. AIC/BIC comparison ──────────────────────────────────────────
    comparison = pd.DataFrame({
        "model": ["OLS", "SLM", "SEM"],
        "AIC": [ols_aic, slm_aic, sem_aic],
        "R_squared": [ols_r2, slm_r2, sem_r2],
    })
    # Add BIC if available
    if spreg_available:
        comparison["BIC"] = [np.nan, np.nan, np.nan]
    else:
        comparison["BIC"] = [ols_model.bic, slm_model.bic, sem_model.bic]

    comparison.to_csv(RESULTS_DIR / "spatial_regression_comparison.csv", index=False)

    comp_long = comparison.melt(id_vars="model", value_vars=["AIC", "BIC"])
    comp_long = comp_long.dropna(subset=["value"])
    ax = sns.barplot(
        data=comp_long,
        x="variable",
        y="value",
        hue="model",
        palette=[PRIMARY, SECONDARY, "#6a3d9a"],
    )
    ax.set_title("Spatial Model Comparison: AIC and BIC")
    ax.set_xlabel("")
    ax.set_ylabel("Information criterion")
    ax.legend(title="Model")
    savefig("10_spatial_model_comparison.png")

    # ── Summary ─────────────────────────────────────────────────────────
    figures = sorted(OUT_DIR.glob("*.png"))
    tables = sorted(RESULTS_DIR.glob("*.csv"))
    print(f"Created {len(figures)} figures in {OUT_DIR}")
    print(f"Created {len(tables)} result tables in {RESULTS_DIR}")
    for f in figures:
        print(f"  {f.name}")
    for t in tables:
        print(f"  {t.name}")


if __name__ == "__main__":
    main()
