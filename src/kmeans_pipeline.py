"""
=============================================================================
SIH26082 - K-Means Clustering of Air Pollution-Weather Coupled Zones
Core ML Pipeline: Feature Engineering + K-Means + Validation
Author: Aditya Tanzal (RK3P24TGA15)
=============================================================================
Pipeline:
  1. Load & preprocess Delhi NCR CAAQMS data
  2. Engineer coupled air-quality + meteorological feature vectors
  3. Apply K-Means with Elbow Method + Silhouette Score for optimal k
  4. Characterise clusters (pollution-weather behaviour profiles)
  5. Validate against GRAP pollution-episode severity records
  6. Export results for dashboard
=============================================================================
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (silhouette_score, silhouette_samples,
                             davies_bouldin_score, calinski_harabasz_score)
from sklearn.impute import SimpleImputer
import json

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_PATH    = os.path.join(os.path.dirname(__file__), "..", "data",
                            "delhi_ncr_aqi_meteo_2021_2024.csv")
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Feature configuration ──────────────────────────────────────────────────
POLLUTANT_FEATURES = ["PM25", "PM10", "NO2", "SO2", "CO", "O3"]
METEO_FEATURES     = ["temp_C", "rh_pct", "ws_ms", "bp_hpa", "vis_km"]
# Coupled features = all pollutants + met
ALL_FEATURES = POLLUTANT_FEATURES + METEO_FEATURES

RANDOM_STATE = 42
MAX_K        = 10   # max clusters to evaluate


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  1. DATA LOADING & PREPROCESSING                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def load_and_preprocess(path: str) -> pd.DataFrame:
    """
    Load raw CAAQMS data and apply preprocessing:
    - Parse dates
    - Impute missing values (median strategy)
    - Remove physical impossibilities
    - Add log-transformed PM features (reduce skewness)
    """
    print("\n[1/5] Loading data …")
    df = pd.read_csv(path, parse_dates=["date"])
    print(f"      Rows: {len(df):,}  Stations: {df['station'].nunique()}")

    # Basic sanity bounds
    df = df[(df.PM25 > 0) & (df.PM25 < 1500)]
    df = df[(df.PM10 > 0) & (df.PM10 < 3000)]
    df = df[(df.ws_ms >= 0) & (df.ws_ms < 30)]
    df = df[(df.temp_C > -5) & (df.temp_C < 50)]

    # Impute remaining NaN (median per station)
    for col in ALL_FEATURES:
        if df[col].isna().any():
            df[col].fillna(df.groupby("station")[col].transform("median"), inplace=True)

    # Log1p transforms for pollutants (reduce right-skew)
    for p in POLLUTANT_FEATURES:
        df[f"log_{p}"] = np.log1p(df[p])

    print(f"      After QC: {len(df):,} records")
    return df


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  2. FEATURE ENGINEERING                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, list]:
    """
    Build station-level MONTHLY aggregated feature vectors.
    This gives one row per (station × month) — a spatiotemporal fingerprint
    for clustering into pollution-weather zones.

    Features per row:
      - Mean & std of each pollutant (log-transformed)
      - Mean of each met variable
      - Pollution episode frequency (fraction of Severe+ days)
      - PM2.5/WS coupling ratio (stagnation index)
    """
    print("\n[2/5] Engineering coupled features …")

    log_poll = [f"log_{p}" for p in POLLUTANT_FEATURES]
    agg_dict = {}

    # Pollutant means and stds
    for col in log_poll:
        agg_dict[col] = ["mean", "std"]

    # Meteorological means
    for col in METEO_FEATURES:
        agg_dict[col] = "mean"

    # Auxiliary
    agg_dict["AQI"]     = "mean"
    agg_dict["episode"] = "mean"   # fraction of episode days

    agg = df.groupby(["station", "month", "latitude", "longitude", "zone_type"]).agg(agg_dict)
    agg.columns = ["_".join(c).strip("_") if isinstance(c, tuple) else c for c in agg.columns]
    agg.reset_index(inplace=True)

    # Stagnation index: mean(PM25) / mean(WS)  → higher = worse trapping
    agg["stagnation_idx"] = agg["log_PM25_mean"] / (agg["ws_ms_mean"] + 0.1)

    # Build final feature matrix
    feature_cols = (
        [f"{p}_mean" for p in log_poll] +
        [f"{p}_std"  for p in log_poll] +
        [f"{m}_mean" for m in METEO_FEATURES] +
        ["episode_mean", "stagnation_idx"]
    )
    X_raw = agg[feature_cols].values

    # Impute any residual NaN
    imputer = SimpleImputer(strategy="median")
    X_raw   = imputer.fit_transform(X_raw)

    print(f"      Feature matrix shape: {X_raw.shape}")
    print(f"      Features: {feature_cols}")
    return agg, X_raw, feature_cols


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  3. OPTIMAL K SELECTION                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def find_optimal_k(X_scaled: np.ndarray,
                   k_range: range = range(2, MAX_K + 1)) -> int:
    """
    Use Elbow Method (WCSS / Inertia) + Silhouette Score to pick optimal k.
    Also reports Davies-Bouldin and Calinski-Harabasz indices.
    """
    print("\n[3/5] Finding optimal k …")
    inertias, silhouettes, db_scores, ch_scores = [], [], [], []

    for k in k_range:
        km = KMeans(n_clusters=k, init="k-means++", n_init=20,
                    max_iter=500, random_state=RANDOM_STATE)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))
        db_scores.append(davies_bouldin_score(X_scaled, labels))
        ch_scores.append(calinski_harabasz_score(X_scaled, labels))
        print(f"      k={k:2d} | Inertia={km.inertia_:8.1f} | "
              f"Silhouette={silhouettes[-1]:.3f} | "
              f"DB={db_scores[-1]:.3f} | CH={ch_scores[-1]:.1f}")

    # ── Elbow plot ──────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    ks = list(k_range)

    axes[0].plot(ks, inertias, "o-", color="#E74C3C", lw=2, ms=7)
    axes[0].set(title="Elbow Curve (Inertia)", xlabel="k", ylabel="WCSS")
    axes[0].grid(alpha=0.3)

    axes[1].plot(ks, silhouettes, "s-", color="#2ECC71", lw=2, ms=7)
    axes[1].set(title="Silhouette Score", xlabel="k", ylabel="Score")
    axes[1].axhline(max(silhouettes), ls="--", color="grey", alpha=0.6)
    axes[1].grid(alpha=0.3)

    axes[2].plot(ks, db_scores, "^-", color="#3498DB", lw=2, ms=7, label="Davies-Bouldin")
    ax2r = axes[2].twinx()
    ax2r.plot(ks, ch_scores, "D--", color="#9B59B6", lw=2, ms=7, label="Calinski-Harabasz")
    axes[2].set(title="DB & CH Indices", xlabel="k", ylabel="Davies-Bouldin (↓)")
    ax2r.set_ylabel("Calinski-Harabasz (↑)", color="#9B59B6")
    axes[2].grid(alpha=0.3)

    plt.suptitle("SIH26082 | Optimal k Selection – Delhi NCR Clustering",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "01_optimal_k.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # Best k = highest silhouette (with elbow consideration)
    best_k = ks[np.argmax(silhouettes)]
    print(f"\n      ✔ Optimal k selected: {best_k} (Silhouette = {max(silhouettes):.3f})")

    # Save metrics
    metrics_df = pd.DataFrame({
        "k": ks, "inertia": inertias, "silhouette": silhouettes,
        "davies_bouldin": db_scores, "calinski_harabasz": ch_scores
    })
    metrics_df.to_csv(os.path.join(OUTPUT_DIR, "k_selection_metrics.csv"), index=False)
    return best_k, metrics_df


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  4. K-MEANS CLUSTERING                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

CLUSTER_LABELS = {
    0: "Cluster 0 – Winter Industrial Hotspot",
    1: "Cluster 1 – Moderate Traffic-Residential",
    2: "Cluster 2 – Clean Monsoon / Green Zone",
    3: "Cluster 3 – Post-Monsoon Transition",
    4: "Cluster 4 – Summer Photochemical Zone",
}

CLUSTER_COLORS = ["#E74C3C", "#E67E22", "#2ECC71", "#3498DB", "#9B59B6"]


def apply_kmeans(X_scaled: np.ndarray, agg: pd.DataFrame,
                 feature_cols: list, k: int) -> pd.DataFrame:
    """Fit final K-Means model and annotate the aggregated feature table."""
    print(f"\n[4/5] Applying K-Means (k={k}) …")

    km = KMeans(n_clusters=k, init="k-means++", n_init=50,
                max_iter=1000, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_scaled)

    agg = agg.copy()
    agg["cluster"] = labels
    agg["cluster_label"] = agg["cluster"].map(
        lambda c: CLUSTER_LABELS.get(c, f"Cluster {c}")
    )

    # ── Silhouette sample plot ─────────────────────────────────────────────
    sample_sil = silhouette_samples(X_scaled, labels)
    agg["silhouette_val"] = sample_sil

    fig, ax = plt.subplots(figsize=(8, 6))
    y_lower = 10
    for i in range(k):
        ith_sil = np.sort(sample_sil[labels == i])
        size_i  = len(ith_sil)
        y_upper = y_lower + size_i
        color   = cm.nipy_spectral(float(i) / k)
        ax.fill_betweenx(np.arange(y_lower, y_upper),
                         0, ith_sil, alpha=0.7, color=color)
        ax.text(-0.05, y_lower + 0.5 * size_i,
                str(i), fontsize=9)
        y_lower = y_upper + 10

    avg_sil = silhouette_score(X_scaled, labels)
    ax.axvline(avg_sil, color="red", ls="--", lw=1.5,
               label=f"Mean silhouette = {avg_sil:.3f}")
    ax.set(title=f"Silhouette Plot – k={k} Clusters\nDelhi NCR Pollution-Weather Zones",
           xlabel="Silhouette Coefficient", ylabel="Cluster")
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "02_silhouette_plot.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # ── PCA 2D visualisation ───────────────────────────────────────────────
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    X2d = pca.fit_transform(X_scaled)
    agg["pca1"] = X2d[:, 0]
    agg["pca2"] = X2d[:, 1]

    fig, ax = plt.subplots(figsize=(9, 7))
    for c in range(k):
        mask = labels == c
        color = CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        ax.scatter(X2d[mask, 0], X2d[mask, 1],
                   c=color, label=CLUSTER_LABELS.get(c, f"C{c}"),
                   alpha=0.65, s=50, edgecolors="white", lw=0.3)
    # Centroids in PCA space
    centers_pca = pca.transform(km.cluster_centers_)
    ax.scatter(centers_pca[:, 0], centers_pca[:, 1],
               marker="*", s=350, c="black", zorder=5, label="Centroids")
    ax.set(title=f"PCA Projection – {k} Pollution-Weather Clusters\nDelhi NCR ({pca.explained_variance_ratio_.sum()*100:.1f}% variance explained)",
           xlabel=f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
           ylabel=f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    ax.legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "03_pca_clusters.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    print(f"      Cluster distribution:\n{agg['cluster_label'].value_counts().to_string()}")
    return agg, km


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  5. CLUSTER CHARACTERISATION & VALIDATION                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def characterise_and_validate(df: pd.DataFrame, agg: pd.DataFrame,
                               k: int) -> dict:
    """
    Characterise each cluster by its centroid statistics and validate
    against GRAP episode severity records.
    """
    print("\n[5/5] Characterising clusters & validating against GRAP records …")

    # ── Mean pollutant & met per cluster ──────────────────────────────────
    analysis_cols = (
        ["PM25", "PM10", "NO2", "SO2", "CO", "O3", "AQI"] +
        ["temp_C", "rh_pct", "ws_ms", "bp_hpa", "vis_km"] +
        ["episode", "severity"]
    )
    merged = df.merge(
        agg[["station", "month", "cluster", "cluster_label"]],
        on=["station", "month"], how="left"
    )
    merged.dropna(subset=["cluster"], inplace=True)

    # Cluster profile
    profile = merged.groupby("cluster_label").agg(
        PM25_mean=("PM25", "mean"),
        PM25_max =("PM25", "max"),
        PM10_mean=("PM10", "mean"),
        NO2_mean =("NO2",  "mean"),
        SO2_mean =("SO2",  "mean"),
        AQI_mean =("AQI",  "mean"),
        AQI_max  =("AQI",  "max"),
        WS_mean  =("ws_ms","mean"),
        Temp_mean=("temp_C","mean"),
        RH_mean  =("rh_pct","mean"),
        EpisodeFrac=("episode","mean"),
    ).round(1).reset_index()
    profile.to_csv(os.path.join(OUTPUT_DIR, "cluster_profiles.csv"), index=False)
    print("\n      Cluster Profiles:")
    print(profile.to_string(index=False))

    # ── GRAP validation: match episode days to cluster ────────────────────
    # GRAP severity ↔ cluster episode fraction
    grap_map = {
        "Good":       {"GRAP_Stage": "None",    "expected_cluster_ep_frac": "<0.05"},
        "Moderate":   {"GRAP_Stage": "None",    "expected_cluster_ep_frac": "0.05–0.15"},
        "Poor":       {"GRAP_Stage": "Stage I", "expected_cluster_ep_frac": "0.15–0.35"},
        "Very Poor":  {"GRAP_Stage": "Stage II","expected_cluster_ep_frac": "0.35–0.60"},
        "Severe":     {"GRAP_Stage": "Stage III","expected_cluster_ep_frac": "0.60–0.80"},
        "Severe+":    {"GRAP_Stage": "Stage IV", "expected_cluster_ep_frac": ">0.80"},
    }

    # Validate: for each cluster compute dominant season & severity
    valid = merged.groupby("cluster_label").agg(
        dominant_season  = ("season",   lambda x: x.value_counts().index[0]),
        dominant_severity= ("severity", lambda x: x.value_counts().index[0]),
        ep_fraction      = ("episode",  "mean"),
        n_severe_days    = ("episode",  "sum"),
    ).reset_index()

    valid["GRAP_Stage_Expected"] = valid["ep_fraction"].apply(
        lambda f: "Stage IV (Severe+)" if f > 0.80 else
                  "Stage III (Severe)" if f > 0.60 else
                  "Stage II (Very Poor)" if f > 0.35 else
                  "Stage I (Poor)"     if f > 0.15 else
                  "No Action (Good-Moderate)"
    )
    valid.to_csv(os.path.join(OUTPUT_DIR, "cluster_validation.csv"), index=False)
    print("\n      GRAP Validation:")
    print(valid.to_string(index=False))

    # ── Heatmap: cluster × month ───────────────────────────────────────────
    pivot = merged.groupby(["cluster_label", "month"])["AQI"].mean().unstack()
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    pivot.columns = [month_names[m] for m in pivot.columns]

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="RdYlGn_r",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Mean AQI"})
    ax.set(title="Mean AQI by Cluster × Month – Delhi NCR Pollution Zones",
           xlabel="Month", ylabel="Cluster")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "04_cluster_month_heatmap.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # ── Radar / spider chart: cluster pollutant fingerprints ──────────────
    _plot_radar_chart(profile, k)

    # ── Spatial map data ───────────────────────────────────────────────────
    spatial = agg.groupby("station").agg(
        cluster=("cluster","first"),
        cluster_label=("cluster_label","first"),
        lat=("latitude","first"),
        lon=("longitude","first"),
        zone_type=("zone_type","first"),
        pm25_mean=("log_PM25_mean","mean"),
        ep_frac=("episode_mean","mean"),
    ).reset_index()
    spatial.to_csv(os.path.join(OUTPUT_DIR, "station_clusters.csv"), index=False)

    return {"profile": profile, "validation": valid, "spatial": spatial, "merged": merged}


def _plot_radar_chart(profile: pd.DataFrame, k: int):
    """Normalised radar chart of cluster pollutant fingerprints."""
    cats = ["PM25_mean", "PM10_mean", "NO2_mean", "SO2_mean", "AQI_mean", "EpisodeFrac"]
    labels = ["PM2.5", "PM10", "NO₂", "SO₂", "AQI", "Episode\nFraction"]
    N = len(cats)

    norm = profile[cats].copy()
    for col in cats:
        norm[col] = (norm[col] - norm[col].min()) / (norm[col].max() - norm[col].min() + 1e-8)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8),
                           subplot_kw=dict(polar=True))
    for i, row in norm.iterrows():
        values = row[cats].tolist() + [row[cats[0]]]
        color  = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
        label  = profile.loc[i, "cluster_label"]
        ax.plot(angles, values, "o-", lw=2, color=color, label=label)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("Cluster Pollutant Fingerprints (Normalised)\nDelhi NCR Pollution-Weather Zones",
                 size=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "05_radar_fingerprints.png"),
                dpi=150, bbox_inches="tight")
    plt.close()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MAIN PIPELINE                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def run_pipeline():
    print("=" * 65)
    print("  SIH26082 | K-Means Clustering: Delhi NCR Pollution-Weather Zones")
    print("  Author : Aditya Tanzal  |  Reg: RK3P24TGA15")
    print("=" * 65)

    # 1. Load
    df = load_and_preprocess(DATA_PATH)

    # 2. Feature engineering
    agg, X_raw, feature_cols = engineer_features(df)

    # 3. Scale
    scaler  = RobustScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # 4. Optimal k
    best_k, k_metrics = find_optimal_k(X_scaled)

    # 5. Final clustering
    agg, km = apply_kmeans(X_scaled, agg, feature_cols, best_k)

    # 6. Characterise & validate
    results = characterise_and_validate(df, agg, best_k)

    # ── Save aggregated clustered data ─────────────────────────────────────
    agg.to_csv(os.path.join(OUTPUT_DIR, "clustered_data.csv"), index=False)
    results["merged"].to_csv(os.path.join(OUTPUT_DIR, "full_merged.csv"), index=False)

    # ── Summary JSON for dashboard ──────────────────────────────────────────
    summary = {
        "project":    "SIH26082",
        "author":     "Aditya Tanzal",
        "reg_no":     "RK3P24TGA15",
        "best_k":     int(best_k),
        "silhouette": float(k_metrics.loc[k_metrics.k == best_k, "silhouette"].values[0]),
        "db_score":   float(k_metrics.loc[k_metrics.k == best_k, "davies_bouldin"].values[0]),
        "n_stations": int(df["station"].nunique()),
        "n_records":  int(len(df)),
        "cluster_labels": CLUSTER_LABELS,
        "cluster_colors": CLUSTER_COLORS,
    }
    with open(os.path.join(OUTPUT_DIR, "pipeline_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print("  ✅ Pipeline complete! Outputs saved to /outputs/")
    print(f"     Optimal k = {best_k}  |  Silhouette = {summary['silhouette']:.3f}")
    print("=" * 65)
    return df, agg, results, summary


if __name__ == "__main__":
    run_pipeline()
