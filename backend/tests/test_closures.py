"""Test closure state persistence and independence."""

from src.closures import make_emission_auditor
from src.models import Factory
from src.web_pipeline import run_web_pipeline
from pathlib import Path
import pandas as pd

def test_closure_accumulation():
    """Factory A accumulates correctly over months."""
    auditor = make_emission_auditor("Steel", 100000)
    
    # 3 months of identical data
    for month in range(1, 4):
        result = auditor(1000, 4000)
        expected_monthly = 1000*2.5 + 4000*0.6  # 2500 + 2400 = 4900
    
    assert abs(result["monthly_emissions_kg"] - 4900) < 1, "Monthly calc wrong"
    # after three identical months the total should be roughly three times
    assert abs(result["total_emissions_kg"] - 14700) < 1, "Should accumulate 3×4900"
    print("✅ Accumulation: PASS")

def test_factory_independence():
    """Factory A ≠ Factory B despite same sector."""
    factory_a = Factory("A", "Steel", 100000)
    factory_b = Factory("B", "Steel", 100000)
    
    # Same inputs, different totals due to separate closures
    factory_a.record_month(1, 1000, 4000)
    factory_b.record_month(1, 1000, 4000)
    
    factory_a.record_month(2, 1200, 4500)
    factory_b.record_month(2, 800, 3500)  # Different month 2
    
    assert factory_a.total_emissions != factory_b.total_emissions
    assert factory_a.alerts_count == 0
    assert factory_b.alerts_count == 0
    print(f"✅ Independence: A={factory_a.total_emissions}, B={factory_b.total_emissions}")

def test_alert_trigger():
    """Alert when cap exceeded."""
    auditor = make_emission_auditor("Textile", 5000)
    auditor(2000, 5000)  # ~3600 kg
    result = auditor(1500, 4000)  # ~2880 → total >5000?
    
    assert result["status"] == "ALERT"
    assert "cap" in result["alert"].lower()
    print("✅ Alert trigger: PASS")


# additional sanity check for the web pipeline

def test_web_pipeline(tmp_path):
    """Pipeline should run end‑to‑end and produce expected keys/files."""
    # create a tiny OWID-like file
    owid = tmp_path / "owid.csv"
    owid.write_text("country,year,co2_per_unit_energy\nIndia,2020,0.7\nChina,2020,0.8\n")

    outdir = tmp_path / "out"
    res = run_web_pipeline(str(owid), str(outdir), seed=123)

    # expect cleaned csv, audit summary and chart paths
    assert "cleaned_csv" in res
    assert "audit_summary_csv" in res
    assert Path(res["audit_summary_csv"]).exists()
    assert Path(res["emissions_chart"]).exists()
    assert isinstance(res.get("violators"), list)

    # verify the cleaned file contains intensity_diff and the returned
    # mean_intensity_deviation matches the column
    df = pd.read_csv(res["cleaned_csv"])
    assert "intensity_diff" in df.columns
    # mean deviation should equal the absolute mean of the column
    expected_mean = float(df["intensity_diff"].abs().mean())
    assert abs(res["summary"]["mean_intensity_deviation"] - expected_mean) < 1e-6

    print("✅ Web pipeline smoke test passed")


if __name__ == "__main__":
    test_closure_accumulation()
    test_factory_independence()
    test_alert_trigger()
    # run quick pipeline check using a temporary directory
    import tempfile, pathlib
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    test_web_pipeline(tmpdir)
    print("🎉 All tests PASSED!")
