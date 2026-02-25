"""Carbon-Trace: Secure emission auditor closures."""

def make_emission_auditor(sector: str, carbon_cap_kg: float) -> callable:
    """
    Factory function that returns a closure for one factory's emissions.
    
    Private state:
    - total_emissions: accumulates across monthly calls
    - emission factors: sector-specific, hidden
    
    Returns auditor callable with clean interface.
    """
    # PRIVATE: Sector-specific emission factors (kg CO2)
    emission_factors = {
        "Steel": {"production_per_ton": 2.5, "energy_per_mwh": 0.6},
        "Textile": {"production_per_ton": 1.2, "energy_per_mwh": 0.4},
        "Electronics": {"production_per_ton": 1.8, "energy_per_mwh": 0.5},
    }
    
    if sector not in emission_factors:
        raise ValueError(f"Unknown sector: {sector}")
    
    factors = emission_factors[sector]
    
    # PRIVATE STATE: persists across calls
    total_emissions = 0.0
    
    def auditor(monthly_production_tons: float,
                energy_used_mwh: float,
                energy_source_type: str | None = None,
                raw_material_weight_tons: float | None = None) -> dict:
        nonlocal total_emissions
        
        # Core calculation
        emissions_production = monthly_production_tons * factors["production_per_ton"]
        emissions_energy = energy_used_mwh * factors["energy_per_mwh"]
        monthly_emissions = emissions_production + emissions_energy
        
        # Energy source multiplier (optional enhancement)
        if energy_source_type == "coal":
            monthly_emissions *= 1.2
        elif energy_source_type == "renewable":
            monthly_emissions *= 0.7
        elif energy_source_type == "grid":
            pass  # baseline
        
        # Accumulate
        total_emissions += monthly_emissions
        
        # Carbon cap check
        status = "OK"
        alert = None
        if total_emissions > carbon_cap_kg:
            status = "ALERT"
            alert = (
                f"🚨 Carbon cap exceeded! "
                f"Total: {total_emissions:.0f} kg CO₂ "
                f"(cap: {carbon_cap_kg:.0f} kg)"
            )
        
        return {
            "monthly_emissions_kg": round(monthly_emissions, 2),
            "total_emissions_kg": round(total_emissions, 2),
            "status": status,
            "alert": alert,
        }
    
    return auditor
