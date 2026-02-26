"""Factory models wrapping auditor closures."""

from typing import List, Dict, Any
from .closures import make_emission_auditor

class Factory:
    def __init__(self, factory_id: str, sector: str, carbon_cap_kg: float):
        self.factory_id = factory_id
        self.sector = sector
        # PRIVATE: Each factory gets its own closure
        self._auditor = make_emission_auditor(sector, carbon_cap_kg)
        self.history: List[Dict[str, Any]] = []
    
    def record_month(self, 
                     month: int,
                     monthly_production_tons: float,
                     energy_used_mwh: float,
                     energy_source_type: str | None = None,
                     raw_material_weight_tons: float | None = None) -> Dict[str, Any]:
        """Record one month's production data."""
        result = self._auditor(
            monthly_production_tons,
            energy_used_mwh,
            energy_source_type,
            raw_material_weight_tons,
        )
        
        # Enrich with metadata
        result.update({
            "factory_id": self.factory_id,
            "sector": self.sector,
            "month": month,
        })
        
        self.history.append(result)
        return result
    
    @property
    def total_emissions(self) -> float:
        """Read-only total emissions."""
        return self.history[-1]["total_emissions_kg"] if self.history else 0.0
    
    @property
    def alerts_count(self) -> int:
        """Count of months over cap."""
        return sum(1 for r in self.history if r["status"] == "ALERT")
