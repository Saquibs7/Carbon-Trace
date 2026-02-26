"""Test closure state persistence and independence."""

from src.closures import make_emission_auditor
from src.models import Factory

def test_closure_accumulation():
    """Factory A accumulates correctly over months."""
    auditor = make_emission_auditor("Steel", 100000)
    
    # 3 months of identical data
    for month in range(1, 4):
        result = auditor(1000, 4000)
        expected_monthly = 1000*2.5 + 4000*0.6  # 2500 + 2400 = 4900
    
    assert abs(result["monthly_emissions_kg"] - 4900) < 1, "Monthly calc wrong"
    assert result["total_emissions_kg"] ≈ 14700, "Should accumulate 3×4900"
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
    print(f"✅ Independence: A={factory_a.total_emissions}, B={factory_b.total_emissions}")

def test_alert_trigger():
    """Alert when cap exceeded."""
    auditor = make_emission_auditor("Textile", 5000)
    auditor(2000, 5000)  # ~3600 kg
    result = auditor(1500, 4000)  # ~2880 → total >5000?
    
    assert result["status"] == "ALERT"
    print("✅ Alert trigger: PASS")

if __name__ == "__main__":
    test_closure_accumulation()
    test_factory_independence()
    test_alert_trigger()
    print("🎉 All tests PASSED!")
