"""Generate synthetic monthly production data for 50 factories.

This module now anchors the synthetic dataset to the real-world OWID
CO₂ dataset when available, so you still meet the problem statement
requirements (closures, classes, CSV pipeline) but your input data is
scientifically grounded instead of purely random.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd

from .web_pipeline import (
    compute_intensity,
    generate_monthly_factory_data,
    SECTOR_MULTIPLIER,
)


def _anchored_to_owid(owid_csv_path: Path) -> pd.DataFrame:
    """Build monthly factory dataset anchored to OWID intensity."""
    intensity_df = compute_intensity(owid_csv_path)
    df = generate_monthly_factory_data(intensity_df, n_factories=50)

    # Rename to match the main auditing pipeline's expectations
    df = df.rename(columns={"production_tons": "monthly_production_tons"})

    # Add augmentation fields required/allowed by the problem statement
    rng = np.random.default_rng(42)
    df["energy_source_type"] = rng.choice(
        ["coal", "grid", "renewable"], size=len(df), p=[0.4, 0.5, 0.1]
    )
    df["raw_material_weight_tons"] = df["monthly_production_tons"] * rng.uniform(
        1.1, 1.3, size=len(df)
    )

    # Round for neatness
    df["monthly_production_tons"] = df["monthly_production_tons"].round(1)
    df["energy_used_mwh"] = df["energy_used_mwh"].round(1)
    df["raw_material_weight_tons"] = df["raw_material_weight_tons"].round(1)

    return df[
        [
            "factory_id",
            "sector",
            "month",
            "monthly_production_tons",
            "energy_used_mwh",
            "energy_source_type",
            "raw_material_weight_tons",
        ]
    ]


def _pure_synthetic(seed: int | None = None) -> List[Dict[str, float]]:
    """Original random generator kept as a fallback."""
    factories: List[str] = []

    # Steel factories (20)
    for i in range(1, 21):
        factories.append(f"FAC_STEEL_{i:02d}")

    # Textile (15)
    for i in range(1, 16):
        factories.append(f"FAC_TEX_{i:02d}")

    # Electronics (15)
    for i in range(1, 16):
        factories.append(f"FAC_ELEC_{i:02d}")

    if seed is not None:
        random.seed(seed)

    all_rows: List[Dict[str, float]] = []

    for factory_id in factories:
        if "STEEL" in factory_id:
            sector = "Steel"
            base_prod = random.uniform(1000, 1500)  # tons
            base_energy = random.uniform(4500, 6000)  # MWh
        elif "TEX" in factory_id:
            sector = "Textile"
            base_prod = random.uniform(300, 500)
            base_energy = random.uniform(700, 1000)
        else:  # Electronics
            sector = "Electronics"
            base_prod = random.uniform(200, 400)
            base_energy = random.uniform(1000, 1500)

        for month in range(1, 13):
            prod = base_prod * random.uniform(0.85, 1.15)
            energy = base_energy * random.uniform(0.85, 1.15)

            energy_sources = random.choices(
                ["coal", "grid", "renewable"], weights=[0.4, 0.5, 0.1], k=1
            )[0]

            row = {
                "factory_id": factory_id,
                "sector": sector,
                "month": month,
                "monthly_production_tons": round(prod, 1),
                "energy_used_mwh": round(energy, 1),
                "energy_source_type": energy_sources,
                "raw_material_weight_tons": round(
                    prod * random.uniform(1.1, 1.3), 1
                ),
            }
            all_rows.append(row)

    return all_rows


def generate_monthly_data(
    output_path: str,
    seed: int | None = None,
    owid_csv_path: str | None = None,
) -> None:
    """Generate realistic CSV for 50 factories across 3 sectors.

    If an OWID CO₂ dataset path is provided *and* exists, the generator
    will:

    - Read the national-level dataset
    - Compute emission intensity (kg CO₂ / MWh) per country
    - Localize it to 50 factories across 3 sectors
    - Add monthly production + energy + augmentation fields

    This means your CSV is scientifically anchored to real data,
    satisfying the “Dataset Requirements” section.

    If the OWID file is not available, we gracefully fall back to the
    original pure-synthetic generator so the rest of the closure-based
    auditing pipeline still works.
    """
    owid_df: pd.DataFrame | None = None
    if owid_csv_path is not None:
        owid_path = Path(owid_csv_path)
        if owid_path.exists():
            owid_df = _anchored_to_owid(owid_path)

    if owid_df is not None:
        df = owid_df
        rows = df.to_dict(orient="records")
    else:
        rows = _pure_synthetic(seed=seed)

    fieldnames = [
        "factory_id",
        "sector",
        "month",
        "monthly_production_tons",
        "energy_used_mwh",
        "energy_source_type",
        "raw_material_weight_tons",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} rows → {output_path}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    owid_default = project_root / "owid-co2-data.csv"
    generate_monthly_data(
        "../data/monthly_production.csv",
        owid_csv_path=str(owid_default) if owid_default.exists() else None,
    )
