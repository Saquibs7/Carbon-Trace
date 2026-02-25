#!/usr/bin/env python3
"""Carbon-Trace: Industrial Emission Auditor (SDG 13)."""

import sys
from pathlib import Path
from src.runner import run_audit, write_summary_csv, plot_emissions
from src.data_gen import generate_monthly_data

def main():
    project_root = Path(__file__).parent
    
    # Step 1: Generate data (if missing)
    data_file = project_root / "data" / "monthly_production.csv"
    if not data_file.exists():
        print("📊 Generating synthetic dataset...")
        generate_monthly_data(str(data_file))
    
    # Step 2: Run audit
    print("🔬 Running Carbon-Trace audit...")
    factories, records = run_audit(
        input_csv=str(data_file),
        config_path=str(project_root / "config" / "sectors.json"),
    )
    
    # Print summary stats
    total_factories = len(factories)
    total_emissions_all = sum(f.total_emissions for f in factories.values())
    alerts = sum(f.alerts_count for f in factories.values())
    
    print(f"\n📈 Audit Complete:")
    print(f"   {total_factories} factories audited")
    print(f"   {total_emissions_all:,.0f} kg CO₂ total emissions")
    print(f"   {alerts} alert(s) triggered")
    
    # Step 3: Write outputs
    summary_file = project_root / "data" / "audit_summary_2026.csv"
    write_summary_csv(factories, str(summary_file))
    
    chart_file = project_root / "plot" / "emissions_chart.png"
    plot_emissions(factories, str(chart_file))
    
    print(f"\n✅ Outputs ready:")
    print(f"   📄 {summary_file}")
    print(f"   📊 {chart_file}")
    
    # Show top violators
    violators = [(f.factory_id, f.total_emissions, f.alerts_count) 
                for f in factories.values() if f.alerts_count > 0]
    if violators:
        print("\n🚨 Top violators:")
        for fid, total, alerts in sorted(violators, key=lambda x: x[1], reverse=True)[:3]:
            print(f"   {fid}: {total:,.0f}kg ({alerts} alerts)")

if __name__ == "__main__":
    main()
