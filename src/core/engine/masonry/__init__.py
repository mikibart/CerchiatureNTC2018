# src/core/engine/masonry - Moduli calcolo muratura NTC 2018
"""
Moduli separati per il calcolo muratura secondo NTC 2018 § 8.7.1.5

Struttura:
- validation.py: Validazione input geometrici e meccanici
- geometry.py: Calcolo maschi murari e geometria
- resistance.py: Calcoli resistenza V_t1, V_t2, V_t3
- stiffness.py: Calcolo rigidezza laterale
- calculator.py: Orchestratore principale (MasonryCalculator)
"""

from .validation import MasonryValidator, ValidationResult
from .geometry import MasonryGeometry, MaschiMurari
from .resistance import MasonryResistance, ResistanceResult
from .stiffness import MasonryStiffness, StiffnessResult
from .calculator import MasonryCalculator

__all__ = [
    'MasonryValidator',
    'ValidationResult',
    'MasonryGeometry',
    'MaschiMurari',
    'MasonryResistance',
    'ResistanceResult',
    'MasonryStiffness',
    'StiffnessResult',
    'MasonryCalculator'
]
