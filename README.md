# SIH26082 — K-Means Clustering of Air Pollution–Weather Coupled Zones for Delhi NCR Forecasting

**Author:** Aditya Tanzal  
**Registration Number:** RK3P24TGA15  
**Problem ID:** SIH26082  

---

## Project Structure

```
bbhupii project/
├── main.py                              ← Run this to generate data + execute full pipeline
├── SIH26082_SOTA_Report_Aditya_Tanzal.docx   ← Completed SOTA Report
├── SOTA_Project_new.docx               ← Original template
│
├── src/
│   ├── data_generator.py               ← Synthetic CAAQMS data generation (18 stations, 2021-2024)
│   ├── kmeans_pipeline.py              ← Full ML pipeline: features → K-Means → validation
│   └── generate_sota_report.py         ← Generates the filled SOTA DOCX report
│
├── data/
│   └── delhi_ncr_aqi_meteo_2021_2024.csv   ← Generated after running main.py
│
├── outputs/                            ← Generated after running main.py
│   ├── 01_optimal_k.png                ← Elbow + Silhouette + DB/CH charts
│   ├── 02_silhouette_plot.png          ← Silhouette sample analysis
│   ├── 03_pca_clusters.png             ← PCA 2D cluster projection
│   ├── 04_cluster_month_heatmap.png    ← Cluster × Month AQI heatmap
│   ├── 05_radar_fingerprints.png       ← Radar/spider pollutant fingerprint chart
│   ├── cluster_profiles.csv            ← Cluster centroid statistics
│   ├── cluster_validation.csv          ← GRAP episode validation
│   ├── station_clusters.csv            ← Station → Cluster spatial assignments
│   ├── clustered_data.csv              ← Aggregated clustered feature table
│   ├── full_merged.csv                 ← Daily records with cluster labels
│   ├── k_selection_metrics.csv         ← Silhouette/DB/CH per k=2..10
│   └── pipeline_summary.json           ← Summary stats for dashboard
│
└── dashboard/
    ├── index.html                      ← Open in browser for interactive dashboard
    ├── style.css                       ← Dark glassmorphism design
    └── app.js                          ← Animated counters, SVG map, feature bars
```

---

## How to Run

### Step 1: Install dependencies
```bash
pip install scikit-learn pandas numpy matplotlib seaborn python-docx openpyxl
```

### Step 2: Run the full pipeline
```bash
python main.py
```
This will:
1. Generate the synthetic Delhi NCR dataset (18 stations × 4 years)
2. Run feature engineering and K-Means clustering
3. Produce 5 analysis charts in `/outputs/`
4. Export cluster validation against GRAP records

### Step 3: View the dashboard
Open `dashboard/index.html` in any browser.

### Step 4: Regenerate the SOTA Report
```bash
python src/generate_sota_report.py
```

---

## Key Results

| Metric              | Value    | Interpretation          |
|---------------------|----------|-------------------------|
| Optimal k           | 2        | Elbow + Silhouette      |
| Silhouette Score    | 0.702    | Strong Structure        |
| Davies-Bouldin      | 0.355    | Excellent Separation    |
| Calinski-Harabász   | 513.4    | Dense, Compact Clusters |
| Records             | 26,261   | 18 stations × 4 years   |
| Features            | 19       | Coupled AQ + Met        |

## Clusters Found

| Cluster | Name                        | GRAP Stage        | Ep. Fraction |
|---------|-----------------------------|-------------------|--------------|
| 0       | Broad NCR — All-Season Zone | Stage II (Very Poor) | 53.2%    |
| 1       | Winter Severe Hotspot       | Stage IV (Severe+)| 100.0%       |

---

## Technologies Used
- **Python 3.13** · scikit-learn · pandas · numpy · matplotlib · seaborn
- **ML Algorithms:** K-Means++ · PCA · RobustScaler
- **Validation:** Silhouette, Davies-Bouldin, Calinski-Harabász, GRAP match
- **Dashboard:** HTML5 · CSS3 (Glassmorphism) · Vanilla JS · Canvas API · SVG
- **Data Sources:** CPCB CAAQMS (synthetic simulation) · IMD Meteorology · GRAP records
