"""
Modello Progetto
Contenitore principale di tutti i dati
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ProjectInfo:
    """Informazioni progetto"""
    name: str = ""
    location: str = ""
    client: str = ""
    engineer: str = "Arch. Michelangelo Bartolotta"
    date: datetime = field(default_factory=datetime.now)

@dataclass
class Project:
    """Progetto completo"""
    info: ProjectInfo = field(default_factory=ProjectInfo)
    wall: Optional['Wall'] = None
    openings: List['Opening'] = field(default_factory=list)
    materials: Dict = field(default_factory=dict)
    loads: Dict = field(default_factory=dict)
    results: Optional[Dict] = None
    version: str = "1.0"
