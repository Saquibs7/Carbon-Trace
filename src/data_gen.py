"""Generate synthetic monthly production data for 50 factories."""

import csv
import random
from typing import List, Dict

def generate_monthly_data(output_path: str) -> None:
    """Generate realistic CSV for 50 factories across 3 sectors."""
    
    factories = []
    
    # Steel factories (20)
    for i in range(1, 21):
        factories.append(f"FAC_STEEL_{i:02d}")
    
    # Textile (15)
    for i in range(1, 16):
        factories.append(f"FAC_TEX_{i:02d}")
    
    # Electronics (15)
    for i in range(1, 16):
        factories.append(f"FAC_ELEC_{i:02d}")
    
    random.seed(42)  # Reproducible
    
    all_rows = []
    
    for factory_id in factories:
        # Decode sector from ID
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
        
        # Generate 12 months with realistic variation (±15%)
        for month in range(1, 13):
            prod = base_prod * random.uniform(0.85, 1.15)
            energy = base_energy * random.uniform(0.85, 1.15)
            
            energy_sources = random.choices(
                ["coal", "grid", "renewable"], 
                weights=[0.4, 0.5, 0.1], k=1
            )[0]
            
            row = {
                "factory_id": factory_id,
                "sector": sector,
                "month": month,
                "monthly_production_tons": round(prod, 1),
                "energy_used_mwh": round(energy, 1),
                "energy_source_type": energy_sources,
                "raw_material_weight_tons": round(prod * random.uniform(1.1, 1.3), 1),
            }
            all_rows.append(row)
    
    # Write CSV
    fieldnames = [
        "factory_id", "sector", "month", 
        "monthly_production_tons", "energy_used_mwh",
        "energy_source_type", "raw_material_weight_tons"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"✅ Generated {len(all_rows)} rows → {output_path}")

if __name__ == "__main__":
    generate_monthly_data("../data/monthly_production.csv")
