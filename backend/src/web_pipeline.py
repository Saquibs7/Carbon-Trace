"""Web-facing data pipeline mirroring the notebook logic.

This module:
- Uses OWID CO₂ dataset to compute real emission intensity (kg CO₂ / MWh)
- Localizes to selected industrial economies
- Generates synthetic factory-level data
- Injects data quality issues
- Cleans and validates the dataset
- Performs basic EDA and saves plots
- Returns paths + headline metrics for the web layer.
"""

from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# bring audit functionality into the web pipeline
from .runner import run_audit, write_summary_csv, plot_emissions
import matplotlib
matplotlib.use("Agg")  # non-GUI backend

import matplotlib.pyplot as plt

COUNTRIES = ["India", "China", "Germany", "United States", "Japan"]
SECTORS = ["Steel", "Textile", "Electronics"]

SECTOR_MULTIPLIER: Dict[str, float] = {
    "Steel": 1.15,
    "Textile": 1.0,
    "Electronics": 0.85,
}


def seasonal_factor(month: int, sector: str) -> float:
    if sector == "Steel":
        return 1 + 0.15 * np.sin((month - 3) / 12 * 2 * np.pi)
    if sector == "Textile":
        return 1 + 0.20 * np.sin((month - 10) / 12 * 2 * np.pi)
    if sector == "Electronics":
        return 1 + 0.18 * np.sin((month - 8) / 12 * 2 * np.pi)
    return 1.0


def compute_intensity(owid_path: Path) -> pd.DataFrame:
    """Compute country-level emission intensity (kg CO₂ / MWh) from OWID dataset."""
    df = pd.read_csv(owid_path)
    df = df[df["country"].isin(COUNTRIES)]
    df = df[df["year"] >= 2018]

    intensity_df = df.groupby("country")["co2_per_unit_energy"].mean().reset_index()
    intensity_df["co2_per_mwh"] = intensity_df["co2_per_unit_energy"] * 1000
    return intensity_df


def generate_factories(n_factories: int = 50) -> pd.DataFrame:
    data: List[List[str]] = []

    for i in range(n_factories):
        factory_id = f"FAC_{str(i + 1).zfill(3)}"
        sector = random.choice(SECTORS)
        country = random.choice(COUNTRIES)
        data.append([factory_id, sector, country])

    return pd.DataFrame(data, columns=["factory_id", "sector", "country"])


def generate_monthly_factory_data(
    intensity_df: pd.DataFrame, n_factories: int = 50
) -> pd.DataFrame:
    """Generate monthly factory-level data anchored to OWID intensity."""
    factory_df = generate_factories(n_factories)

    rows: List[List[Any]] = []

    for _, row in factory_df.iterrows():
        base_intensity = intensity_df[
            intensity_df["country"] == row["country"]
        ]["co2_per_mwh"].values[0]

        for month in range(1, 13):
            season_adj = seasonal_factor(month, row["sector"])

            if row["sector"] == "Steel":
                production = np.random.normal(1500, 300)
            elif row["sector"] == "Textile":
                production = np.random.normal(600, 120)
            else:
                production = np.random.normal(250, 60)

            production = max(production * season_adj, 10)

            energy_used = production * np.random.uniform(2.5, 4.5)

            emission = energy_used * base_intensity
            emission *= SECTOR_MULTIPLIER[row["sector"]]

            rows.append(
                [
                    row["factory_id"],
                    row["sector"],
                    row["country"],
                    month,
                    production,
                    energy_used,
                    emission,
                ]
            )

    columns = [
        "factory_id",
        "sector",
        "country",
        "month",
        "production_tons",
        "energy_used_mwh",
        "co2_emissions_kg",
    ]

    return pd.DataFrame(rows, columns=columns)


def inject_dirty_data(df: pd.DataFrame) -> pd.DataFrame:
    """Inject missing values, duplicates, and outliers."""
    dirty = df.copy()

    # Missing values
    dirty.loc[dirty.sample(frac=0.05, random_state=42).index, "energy_used_mwh"] = np.nan

    # Duplicates
    dirty = pd.concat([dirty, dirty.sample(15, random_state=43)], ignore_index=True)

    # Outliers
    outlier_idx = dirty.sample(5, random_state=44).index
    dirty.loc[outlier_idx, "energy_used_mwh"] *= 3

    return dirty


def clean_data(df: pd.DataFrame, intensity_df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataset and recompute emissions."""
    cleaned = df.drop_duplicates().copy()

    cleaned["energy_used_mwh"] = cleaned.groupby("sector")["energy_used_mwh"].transform(
        lambda x: x.fillna(x.mean())
    )

    country_intensity = intensity_df.set_index("country")["co2_per_mwh"]
    sector_mult_series = pd.Series(SECTOR_MULTIPLIER)

    cleaned["co2_emissions_kg"] = (
        cleaned["energy_used_mwh"]
        * cleaned["country"].map(country_intensity)
        * cleaned["sector"].map(sector_mult_series)
    )

    cleaned["emission_per_mwh"] = (
        cleaned["co2_emissions_kg"] / cleaned["energy_used_mwh"]
    )
    cleaned["energy_per_ton"] = (
        cleaned["energy_used_mwh"] / cleaned["production_tons"]
    )

    # track deviation from base country intensity (used later for reporting)
    country_intensity = intensity_df.set_index("country")["co2_per_mwh"]
    cleaned["intensity_diff"] = (
        cleaned["emission_per_mwh"] - cleaned["country"].map(country_intensity)
    )

    assert (cleaned["production_tons"] > 0).all()
    assert (cleaned["energy_used_mwh"] > 0).all()
    assert (cleaned["co2_emissions_kg"] > 0).all()

    return cleaned

def run_web_pipeline(
    owid_csv_path: str,
    output_root: str,
    production_csv: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """End-to-end pipeline used by the web app.

    This copies most of the notebook logic but also runs the closure-based
    audit and produces the summary file/chart that the command‑line tool
    generates. If ``production_csv`` is provided the pipeline skips
    synthetic generation and uses the provided file directly (this is how you
    can avoid any randomness and feed near‑real factory data).

    Parameters
    ----------
    owid_csv_path:
        Path to uploaded OWID CO₂ dataset CSV.
    output_root:
        Directory where cleaned CSV and plots will be written.
    production_csv:
        Optional path to a user-supplied monthly production dataset. The file
        should contain the same columns produced by ``generate_monthly_factory_data``
        (factory_id, sector, month, production_tons, energy_used_mwh, etc.).
        When given, the pipeline uses it verbatim instead of synthesising new
        numbers, which satisfies the "near to accurate data" requirement.
    seed:
        Optional integer seed; seeding improves reproducibility for demos and
        automated tests. Use ``None`` to allow genuinely random variation.
    """
    # allow consumer to control randomness; default to no seed for realism
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    intensity_df = compute_intensity(Path(owid_csv_path))

    if production_csv is not None and Path(production_csv).exists():
        # user-supplied data takes precedence
        raw_factory_df = pd.read_csv(production_csv)
    else:
        raw_factory_df = generate_monthly_factory_data(intensity_df)

    dirty_df = inject_dirty_data(raw_factory_df)
    cleaned_df = clean_data(dirty_df, intensity_df)

    # Run EDA before renaming columns so plots can still use `production_tons
    mean_deviation = cleaned_df["intensity_diff"].abs().mean()

    # The auditing engine expects `monthly_production_tons`, so duplicate/rename
    cleaned_for_audit = cleaned_df.rename(
        columns={"production_tons": "monthly_production_tons"}
    )

    cleaned_path = output_dir / "cleaned_factory_emissions_2026.csv"
    cleaned_for_audit.to_csv(cleaned_path, index=False)

    # ----- run the closure audit using the cleaned dataset -----
    project_root = Path(__file__).resolve().parents[1]
    factories, _ = run_audit(
        input_csv=str(cleaned_path),
        config_path=str(project_root / "config" / "sectors.json"),
    )

    # write the same outputs as command-line runner
    audit_summary_path = output_dir / "audit_summary_2026.csv"
    write_summary_csv(factories, str(audit_summary_path))

    emissions_chart_path = output_dir / "emissions_chart.png"
    plot_emissions(factories, str(emissions_chart_path))

    # copy files into static assets so templates can display them easily
    static_root = project_root / "web" / "static" / "outputs" / output_dir.name
    if static_root.exists():
        shutil.rmtree(static_root)
    shutil.copytree(output_dir, static_root)

    # gather aggregate + alert/violator info (mirrors CLI output)
    total_factories = len(factories)
    total_emissions_all = sum(f.total_emissions for f in factories.values())
    total_alerts = sum(f.alerts_count for f in factories.values())

    violators = [
        {"factory_id": f.factory_id, "total": f.total_emissions, "alerts": f.alerts_count}
        for f in factories.values()
        if f.alerts_count > 0
    ]

    return {
        "cleaned_csv": str(cleaned_path),
        "summary": {
            "rows_raw": int(len(raw_factory_df)),
            "rows_dirty": int(len(dirty_df)),
            "rows_cleaned": int(len(cleaned_df)),
            "countries": COUNTRIES,
            "sectors": SECTORS,
            "mean_intensity_deviation": float(mean_deviation),
            "total_factories": int(total_factories),
            "total_emissions_all": float(total_emissions_all),
            "total_alerts": int(total_alerts),
        },
        "audit_summary_csv": str(audit_summary_path),
        "emissions_chart": str(Path("outputs") / output_dir.name / emissions_chart_path.name),
        "violators": violators,
    }

