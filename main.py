"""
SIH26082 – Main entry point: generates data then runs full pipeline.
Run: python main.py
"""
import os, sys

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_generator import generate_full_dataset
from kmeans_pipeline import run_pipeline

DATA_PATH = os.path.join(os.path.dirname(__file__), "data",
                         "delhi_ncr_aqi_meteo_2021_2024.csv")

if __name__ == "__main__":
    # Step 1: generate synthetic CAAQMS data (only if not already present)
    if not os.path.exists(DATA_PATH):
        print("Generating synthetic Delhi NCR dataset …\n")
        generate_full_dataset(output_dir=os.path.join(os.path.dirname(__file__), "data"))
    else:
        print(f"Dataset already exists at {DATA_PATH}\n")

    # Step 2: run full ML + validation pipeline
    df, agg, results, summary = run_pipeline()
    print("\nOpen 'dashboard/index.html' in your browser to view the interactive dashboard.")
