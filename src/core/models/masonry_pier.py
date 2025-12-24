"""
Modello Maschio Murario
Rappresenta un maschio murario per la verifica strutturale
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class PierSituation(Enum):
    """Situazione del maschio"""
    EXISTING = 0   # Di fatto
    DESIGN = 1     # Di progetto


@dataclass
class MasonryPier:
    """
    Maschio murario per verifica resistenza
    """
    id: int = 0

    # Geometria
    origin_x: float = 0.0      # cm - Coordinata X origine
    origin_y: float = 0.0      # cm - Coordinata Y origine
    length: float = 100.0      # cm - Lunghezza
    height: float = 300.0      # cm - Altezza

    # Proprietà meccaniche
    sigma_resistance: float = 0.0  # N/mm² - Tensione di resistenza

    # Curva di capacità
    capacity_curve_id: int = 0

    # Situazione
    situation: PierSituation = PierSituation.EXISTING

    @classmethod
    def from_acca(cls, maschio_data: dict) -> 'MasonryPier':
        """
        Crea maschio da dati ACCA iEM
        """
        return cls(
            id=maschio_data.get('Id', 0),
            origin_x=maschio_data.get('PtOrgX', 0),
            origin_y=maschio_data.get('PtOrgY', 0),
            length=maschio_data.get('Lunghezza', 100) * 100,  # m -> cm
            height=maschio_data.get('Altezza', 3) * 100,       # m -> cm
            sigma_resistance=maschio_data.get('SgmForRsst', 0),
            capacity_curve_id=maschio_data.get('CrvCpct', 0),
            situation=PierSituation(maschio_data.get('Situazione', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'origin_x': self.origin_x,
            'origin_y': self.origin_y,
            'length': self.length,
            'height': self.height,
            'sigma_resistance': self.sigma_resistance,
            'capacity_curve_id': self.capacity_curve_id,
            'situation': self.situation.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasonryPier':
        """Deserializza da dizionario"""
        return cls(
            id=data.get('id', 0),
            origin_x=data.get('origin_x', 0),
            origin_y=data.get('origin_y', 0),
            length=data.get('length', 100),
            height=data.get('height', 300),
            sigma_resistance=data.get('sigma_resistance', 0),
            capacity_curve_id=data.get('capacity_curve_id', 0),
            situation=PierSituation(data.get('situation', 0))
        )


@dataclass
class CapacityCurvePoint:
    """Punto della curva di capacità"""
    force: float = 0.0        # N - Forza
    displacement: float = 0.0  # mm - Spostamento


@dataclass
class CapacityCurve:
    """
    Curva di capacità (pushover) per maschio murario
    """
    id: int = 0
    points: List[CapacityCurvePoint] = field(default_factory=list)

    @classmethod
    def from_acca(cls, curve_data: List[dict]) -> 'CapacityCurve':
        """
        Crea curva da dati ACCA iEM
        """
        if not curve_data:
            return cls()

        curve_id = curve_data[0].get('IDCurva', 0)
        points = [
            CapacityCurvePoint(
                force=p.get('Frz', 0),
                displacement=p.get('Sp', 0)
            )
            for p in curve_data
        ]
        return cls(id=curve_id, points=points)

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'points': [
                {'force': p.force, 'displacement': p.displacement}
                for p in self.points
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapacityCurve':
        """Deserializza da dizionario"""
        points = [
            CapacityCurvePoint(
                force=p.get('force', 0),
                displacement=p.get('displacement', 0)
            )
            for p in data.get('points', [])
        ]
        return cls(id=data.get('id', 0), points=points)

    @property
    def max_force(self) -> float:
        """Forza massima della curva"""
        if not self.points:
            return 0.0
        return max(p.force for p in self.points)

    @property
    def max_displacement(self) -> float:
        """Spostamento massimo della curva"""
        if not self.points:
            return 0.0
        return max(p.displacement for p in self.points)

    @property
    def ultimate_displacement(self) -> float:
        """Spostamento ultimo (all'80% della forza massima post-picco)"""
        if not self.points:
            return 0.0

        # Trova il punto di forza massima
        f_max = self.max_force
        threshold = 0.8 * f_max

        # Cerca il punto in cui la forza scende sotto l'80% dopo il picco
        found_peak = False
        for p in self.points:
            if p.force >= f_max * 0.99:  # Tolleranza per il picco
                found_peak = True
            elif found_peak and p.force <= threshold:
                return p.displacement

        return self.max_displacement


@dataclass
class MasonryPierCollection:
    """
    Collezione di maschi murari con curve di capacità
    """
    piers: List[MasonryPier] = field(default_factory=list)
    capacity_curves: Dict[int, CapacityCurve] = field(default_factory=dict)

    def add_pier(self, pier: MasonryPier):
        """Aggiunge un maschio"""
        self.piers.append(pier)

    def add_capacity_curve(self, curve: CapacityCurve):
        """Aggiunge una curva di capacità"""
        self.capacity_curves[curve.id] = curve

    def get_pier_curve(self, pier: MasonryPier) -> Optional[CapacityCurve]:
        """Ottiene la curva di capacità di un maschio"""
        return self.capacity_curves.get(pier.capacity_curve_id)

    def get_existing_piers(self) -> List[MasonryPier]:
        """Restituisce i maschi di fatto"""
        return [p for p in self.piers if p.situation == PierSituation.EXISTING]

    def get_design_piers(self) -> List[MasonryPier]:
        """Restituisce i maschi di progetto"""
        return [p for p in self.piers if p.situation == PierSituation.DESIGN]

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'piers': [p.to_dict() for p in self.piers],
            'capacity_curves': {
                str(k): v.to_dict() for k, v in self.capacity_curves.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasonryPierCollection':
        """Deserializza da dizionario"""
        collection = cls()

        for pier_data in data.get('piers', []):
            collection.piers.append(MasonryPier.from_dict(pier_data))

        for curve_id, curve_data in data.get('capacity_curves', {}).items():
            curve = CapacityCurve.from_dict(curve_data)
            collection.capacity_curves[int(curve_id)] = curve

        return collection
