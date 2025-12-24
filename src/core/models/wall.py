"""
Modello Muro
Rappresenta la parete da verificare
"""

from dataclasses import dataclass

@dataclass
class Wall:
    """Geometria e proprietà del muro"""
    length: float  # cm
    height: float  # cm
    thickness: float  # cm
    material_type: str = "blocchi"
    knowledge_level: str = "LC1"
    
    @property
    def area(self) -> float:
        """Area della sezione in cm²"""
        return self.length * self.thickness
