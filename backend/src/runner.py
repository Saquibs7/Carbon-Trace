"""Main Carbon-Trace auditing engine."""

import csv
import json
from typing import Dict, List, Any
from pathlib import Path
import matplotlib.pyplot as plt

from .models import Factory

def load_config(config_path: str) -> Dict[str, Any]:
    """Load sector caps and multipliers."""
    with open(config_path) as f:
        return json.load(f)

def run_audit(input_csv: str, config_path: str) -> tuple[Dict[str, Factory], List[Dict[str, Any]]]:
    """Process all monthly data through factories."""
    config = load_config(config_path)
    factories: Dict[str, Factory] = {}
    all_records: List[Dict[str, Any]] = []
    
    with open(input_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = row["factory_id"]
            month = int(row["month"])
            
            if fid not in factories:
                sector = row["sector"]
                cap = config["caps_by_sector"].get(sector, 1_000_000.0)
                factories[fid] = Factory(fid, sector, cap)
            
            factory = factories[fid]
            result = factory.record_month(
                month,
                float(row["monthly_production_tons"]),
                float(row["energy_used_mwh"]),
                row.get("energy_source_type"),
                float(row.get("raw_material_weight_tons", 0)),
            )
            all_records.append(result)
    
    return factories, all_records

def write_summary_csv(factories: Dict[str, Factory], output_path: str) -> None:
    """Write year-to-date totals per factory."""
    fieldnames = [
        "factory_id", "sector", "total_emissions_kg",
        "max_monthly_emissions_kg", "alerts_count"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for factory in factories.values():
            if factory.history:
                total = factory.total_emissions
                max_monthly = max(r["monthly_emissions_kg"] for r in factory.history)
                alerts = factory.alerts_count
            else:
                total = max_monthly = alerts = 0
            
            writer.writerow({
                "factory_id": factory.factory_id,
                "sector": factory.sector,
                "total_emissions_kg": f"{total:.2f}",
                "max_monthly_emissions_kg": f"{max_monthly:.2f}",
                "alerts_count": alerts,
            })
    
    print(f"✅ Summary written: {output_path}")

def plot_emissions(
    factories: Dict[str, Factory],
    output_path: str,
    figsize: tuple[float, float] = (8, 5),
) -> None:
    """Cumulative emissions line chart (top 12 factories by emissions).

    The default figure size has been reduced for web display; callers can
    override with a different ``figsize`` if needed (e.g. larger for
    command‑line reports).
    """
    plt.figure(figsize=figsize)
    
    # Sort factories by total emissions, take top 12
    sorted_factories = sorted(
        factories.items(), 
        key=lambda x: x[1].total_emissions, 
        reverse=True
    )[:12]
    
    for fid, factory in sorted_factories:
        monthly = sorted(factory.history, key=lambda r: r["month"])
        months = [r["month"] for r in monthly]
        cumulative = [r["total_emissions_kg"] / 1000 for r in monthly]  # to metric tons
        
        plt.plot(
            months, cumulative, 
            marker='o', linewidth=2, markersize=4,
            label=f"{fid} ({factory.sector})",
        )
    
    plt.xlabel("Month (2026)", fontsize=12)
    plt.ylabel("Cumulative Emissions (metric tons CO₂)", fontsize=12)
    plt.title("Carbon-Trace: Cumulative Emissions by Factory", fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Chart saved: {output_path}")
