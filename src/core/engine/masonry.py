"""
Calcoli Muratura secondo NTC 2018
=================================

NOTA: Questo file è mantenuto per retrocompatibilità.
La logica di calcolo è stata modularizzata in:

    src/core/engine/masonry/
    ├── validation.py   - Validazione input
    ├── geometry.py     - Calcolo maschi murari
    ├── resistance.py   - Calcoli V_t1, V_t2, V_t3
    ├── stiffness.py    - Calcolo rigidezza
    └── calculator.py   - Orchestratore principale

Per nuovi sviluppi, importare direttamente:
    from src.core.engine.masonry import MasonryCalculator

Arch. Michelangelo Bartolotta
Versione: 2.0.0 - Refactoring modulare
"""

# Re-export per retrocompatibilità
from src.core.engine.masonry.calculator import MasonryCalculator
from src.core.engine.masonry.validation import MasonryValidator, ValidationResult
from src.core.engine.masonry.geometry import MasonryGeometry, MaschiMurari, Maschio
from src.core.engine.masonry.resistance import MasonryResistance, ResistanceResult
from src.core.engine.masonry.stiffness import MasonryStiffness, StiffnessResult

__all__ = [
    'MasonryCalculator',
    'MasonryValidator',
    'ValidationResult',
    'MasonryGeometry',
    'MaschiMurari',
    'Maschio',
    'MasonryResistance',
    'ResistanceResult',
    'MasonryStiffness',
    'StiffnessResult'
]
