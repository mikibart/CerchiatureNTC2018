"""
Modello Rinforzo
Cerchiatura in acciaio o C.A.
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SteelReinforcement:
    """Rinforzo in acciaio"""
    intervention_type: str  # frame, lintel, arch
    steel_grade: str = "S235"
    profiles: Dict[str, List[str]] = None  # position -> profiles
    
@dataclass
class ConcreteReinforcement:
    """Rinforzo in C.A."""
    intervention_type: str
    concrete_class: str = "C25/30"
    width: float = 30.0
    height: float = 30.0
    rebar_diameter: int = 16
    rebar_count: int = 4
