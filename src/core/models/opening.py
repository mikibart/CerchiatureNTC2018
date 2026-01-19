"""
Modello Apertura
Rappresenta un'apertura nel muro
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Opening:
    """Apertura con eventuale rinforzo"""
    width: float  # cm
    height: float  # cm
    x: float  # posizione da sinistra
    y: float  # posizione dal basso
    opening_type: str = "rectangular"
    is_existing: bool = False
    reinforcement: Optional['Reinforcement'] = None
