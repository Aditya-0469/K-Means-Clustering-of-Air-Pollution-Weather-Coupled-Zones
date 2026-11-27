"""
=============================================================================
SIH26082 - K-Means Clustering of Air Pollution-Weather Coupled Zones
Data Generator: Synthetic Delhi NCR Monitoring Station Data
Author : Aditya Tanzal (RK3P24TGA15)
=============================================================================
This module generates realistic synthetic data for Delhi NCR CAAQMS stations
mimicking CPCB data structure (PM2.5, PM10, NO2, SO2, CO, O3, AQI +
meteorological parameters: Temp, RH, WS, WD, BP, Visibility).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

# ── Seed for reproducibility ───────────────────────────────────────────────
np.random.seed(42)

# ── Delhi NCR monitoring stations (real CAAQMS locations) ──────────────────
STATIONS = {
    # (Name, Lat, Lon, Zone-Type)
    "Anand_Vihar":         (28.6469, 77.3152, "Traffic-Industrial"),
    "RK_Puram":            (28.5640, 77.1855, "Residential"),
    "Punjabi_Bagh":        (28.6745, 77.1296, "Residential-Traffic"),
    "Dwarka_Sector8":      (28.5795, 77.0601, "Residential"),
    "Nehru_Nagar":         (28.5669, 77.2536, "Industrial"),
    "Okhla_Phase2":        (28.5305, 77.2729, "Industrial"),
    "Noida_Sector62":      (28.6254, 77.3650, "IT-Residential"),
    "Noida_Sector125":     (28.5386, 77.3252, "Mixed"),
    "Ghaziabad_Loni":      (28.7464, 77.2862, "Industrial"),
    "Ghaziabad_Vasundhra": (28.6615, 77.3612, "Residential"),
    "Faridabad_Sector16":  (28.4089, 77.3178, "Industrial"),
    "Faridabad_NIT":       (28.3837, 77.3090, "Residential"),
    "Gurugram_Sector51":   (28.4595, 77.0266, "IT-Commercial"),
    "Gurugram_Manesar":    (28.3590, 76.9399, "Industrial"),
    "Sonepat_Town":        (28.9931, 77.0151, "Mixed"),
    "Bahadurgarh":         (28.6942, 76.9211, "Industrial"),
    "Ballabhgarh":         (28.3407, 77.3176, "Residential"),
    "Greater_Noida":       (28.4744, 77.5040, "Mixed"),
}

# ── Seasonal profiles (realistic Delhi NCR patterns) ──────────────────────
# Months 1-12: relative PM2.5 scaling factor
SEASONAL_PM25 = {
     1: 3.5,  2: 3.0,  3: 2.0,  4: 1.5,  5: 1.3,  6: 1.0,
     7: 0.8,  8: 0.8,  9: 1.0, 10: 1.8, 11: 3.2, 12: 3.8
}

# Zone-type emission multipliers
ZONE_MULT = {
    "Traffic-Industrial": {"PM25": 1.6, "PM10": 1.7, "NO2": 1.8, "SO2": 1.4, "CO": 1.7, "O3": 0.8},
    "Residential":        {"PM25": 1.0, "PM10": 1.0, "NO2": 0.9, "SO2": 0.8, "CO": 1.1, "O3": 1.0},
    "Residential-Traffic":{"PM25": 1.3, "PM10": 1.3, "NO2": 1.4, "SO2": 1.0, "CO": 1.3, "O3": 0.9},
    "Industrial":         {"PM25": 1.7, "PM10": 2.0, "NO2": 1.5, "SO2": 2.0, "CO": 1.5, "O3": 0.7},
    "IT-Residential":     {"PM25": 0.9, "PM10": 0.9, "NO2": 0.9, "SO2": 0.7, "CO": 0.9, "O3": 1.1},
    "IT-Commercial":      {"PM25": 1.0, "PM10": 1.0, "NO2": 1.1, "SO2": 0.8, "CO": 1.0, "O3": 1.0},
    "Mixed":              {"PM25": 1.2, "PM10": 1.2, "NO2": 1.1, "SO2": 1.0, "CO": 1.1, "O3": 0.9},
}


def aqi_from_pm25(pm25: float) -> float:
    """Compute AQI from PM2.5 using India NAQI breakpoints."""
    breakpoints = [
        (0, 30,    0,  50),
        (31, 60,   51, 100),
        (61, 90,  101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, 500, 401, 500),
    ]
    for (c_lo, c_hi, i_lo, i_hi) in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return i_lo + (pm25 - c_lo) / (c_hi - c_lo) * (i_hi - i_lo)
    return 500.0


def generate_station_data(station_name: str, lat: float, lon: float,
                          zone_type: str,
                          start: str = "2021-01-01",
                          end: str = "2024-12-31") -> pd.DataFrame:
    """
    Generate daily time series for one monitoring station.
    Returns a DataFrame with pollutant + meteorological features.
    """
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)
    mult = ZONE_MULT[zone_type]

    records = []
    for i, d in enumerate(dates):
        month = d.month
        season_scale = SEASONAL_PM25[month]

        # ── Meteorological variables ──────────────────────────────────────
        # Temperature °C: hot summers, cold winters
        if month in [12, 1, 2]:
            temp = np.random.normal(12, 5)
        elif month in [3, 4]:
            temp = np.random.normal(28, 6)
        elif month in [5, 6]:
            temp = np.random.normal(40, 4)
        elif month in [7, 8, 9]:
            temp = np.random.normal(33, 3)
        else:
            temp = np.random.normal(25, 5)

        # Relative Humidity %
        if month in [7, 8, 9]:
            rh = np.random.normal(80, 10)
        elif month in [12, 1, 2]:
            rh = np.random.normal(75, 12)
        else:
            rh = np.random.normal(45, 15)
        rh = np.clip(rh, 10, 100)

        # Wind speed m/s (low in winter → pollution trapping)
        if month in [12, 1, 2]:
            ws = np.random.exponential(1.5)
        elif month in [6, 7, 8]:
            ws = np.random.exponential(3.5)
        else:
            ws = np.random.exponential(2.0)
        ws = np.clip(ws, 0.1, 15)

        # Wind direction degrees
        wd = np.random.uniform(0, 360)

        # Barometric pressure hPa
        bp = np.random.normal(1012 - 0.5 * (temp - 15), 3)

        # Visibility km (drops in high pollution / fog)
        if month in [12, 1] and ws < 1.5:
            vis = np.random.uniform(0.3, 3.0)
        else:
            vis = np.random.uniform(4, 15)

        # ── Pollutant concentrations ──────────────────────────────────────
        # PM2.5 µg/m³
        base_pm25 = 60 * season_scale * mult["PM25"]
        noise = np.random.normal(0, 15)
        wind_corr = max(0, (3.0 - ws)) * 12  # stagnation amplifies
        pm25 = max(5, base_pm25 + noise + wind_corr)

        # PM10 µg/m³ (higher in dry/dusty periods)
        pm10 = pm25 * np.random.uniform(1.5, 2.5) * mult["PM10"] / mult["PM25"]
        pm10 = max(10, pm10)

        # NO2 µg/m³
        no2 = 30 * season_scale * mult["NO2"] + np.random.normal(0, 8)
        no2 = max(5, no2)

        # SO2 µg/m³
        so2 = 12 * season_scale * mult["SO2"] + np.random.normal(0, 4)
        so2 = max(2, so2)

        # CO mg/m³
        co = 1.2 * season_scale * mult["CO"] + np.random.normal(0, 0.4)
        co = max(0.1, co)

        # O3 µg/m³ (photochemical, peaks summer afternoons)
        o3_summer = 1.5 if month in [4, 5, 6] else 0.6
        o3 = 40 * o3_summer * mult["O3"] + np.random.normal(0, 10)
        o3 = max(5, o3)

        # AQI (based on PM2.5 as dominant pollutant)
        aqi = aqi_from_pm25(pm25)

        # Pollution episode flag (AQI > 300 == Severe)
        episode = 1 if aqi > 300 else 0
        episode_severity = (
            "Severe+" if aqi > 400 else
            "Severe"  if aqi > 300 else
            "Very Poor" if aqi > 200 else
            "Poor"    if aqi > 100 else
            "Moderate" if aqi > 50  else "Good"
        )

        records.append({
            "date":       d,
            "station":    station_name,
            "latitude":   lat,
            "longitude":  lon,
            "zone_type":  zone_type,
            "month":      month,
            "season":     ("Winter" if month in [12,1,2] else
                           "Spring" if month in [3,4,5] else
                           "Monsoon" if month in [6,7,8,9] else "Post-Monsoon"),
            # Meteorological
            "temp_C":    round(temp, 1),
            "rh_pct":    round(rh, 1),
            "ws_ms":     round(ws, 2),
            "wd_deg":    round(wd, 1),
            "bp_hpa":    round(bp, 1),
            "vis_km":    round(vis, 2),
            # Pollutants
            "PM25":      round(pm25, 1),
            "PM10":      round(pm10, 1),
            "NO2":       round(no2, 1),
            "SO2":       round(so2, 1),
            "CO":        round(co, 2),
            "O3":        round(o3, 1),
            "AQI":       round(aqi, 0),
            "episode":   episode,
            "severity":  episode_severity,
        })

    return pd.DataFrame(records)


def generate_full_dataset(output_dir: str = "../data") -> pd.DataFrame:
    """Generate and save the complete Delhi NCR dataset."""
    os.makedirs(output_dir, exist_ok=True)
    all_dfs = []
    for station_name, (lat, lon, zone_type) in STATIONS.items():
        print(f"  Generating: {station_name} [{zone_type}]")
        df = generate_station_data(station_name, lat, lon, zone_type)
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df.sort_values(["date", "station"], inplace=True)
    full_df.reset_index(drop=True, inplace=True)

    path = os.path.join(output_dir, "delhi_ncr_aqi_meteo_2021_2024.csv")
    full_df.to_csv(path, index=False)
    print(f"\n[OK] Dataset saved -> {path}")
    print(f"   Shape: {full_df.shape}  |  Stations: {full_df['station'].nunique()}")
    return full_df


if __name__ == "__main__":
    print("=" * 60)
    print("SIH26082 | Delhi NCR Synthetic Dataset Generator")
    print("=" * 60)

    df = generate_full_dataset(output_dir="../data")
    print("\nSample records:")
    print(df.head(5).to_string())
