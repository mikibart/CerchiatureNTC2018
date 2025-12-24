"""
Modello Muro
Rappresenta la parete da verificare con supporto geometria variabile
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class KnowledgeLevel(Enum):
    """Livelli di conoscenza NTC 2018"""
    LC1 = "LC1"  # Conoscenza limitata - FC = 1.35
    LC2 = "LC2"  # Conoscenza adeguata - FC = 1.20
    LC3 = "LC3"  # Conoscenza accurata - FC = 1.00


@dataclass
class WallGeometry:
    """Geometria del muro con supporto altezza variabile"""
    length: float  # cm - Base del muro
    height_left: float  # cm - Altezza lato sinistro
    height_right: float  # cm - Altezza lato destro
    thickness_existing: float  # cm - Spessore di fatto
    thickness_design: float  # cm - Spessore di progetto

    @property
    def height(self) -> float:
        """Altezza media del muro"""
        return (self.height_left + self.height_right) / 2

    @property
    def is_variable_height(self) -> bool:
        """Verifica se il muro ha altezza variabile"""
        return abs(self.height_left - self.height_right) > 0.1

    @property
    def area_existing(self) -> float:
        """Area sezione di fatto in cm²"""
        return self.length * self.thickness_existing

    @property
    def area_design(self) -> float:
        """Area sezione di progetto in cm²"""
        return self.length * self.thickness_design


@dataclass
class WallMaterials:
    """Materiali associati al muro"""
    masonry_existing_id: int = 0  # ID materiale muratura di fatto
    masonry_design_id: int = 0    # ID materiale muratura di progetto
    concrete_id: int = 0          # ID materiale C.A.
    steel_profiles_id: int = 0    # ID materiale acciaio profilati
    steel_rebars_id: int = 0      # ID materiale acciaio armatura
    infill_id: int = 0            # ID materiale chiusura/tamponamento


@dataclass
class Wall:
    """
    Muro completo con geometria e materiali
    Supporta formato ACCA iEM
    """
    geometry: WallGeometry = None
    materials: WallMaterials = None
    knowledge_level: KnowledgeLevel = KnowledgeLevel.LC1

    # Setti murari (per muri composti)
    wall_segments: list = field(default_factory=list)

    def __post_init__(self):
        if self.geometry is None:
            self.geometry = WallGeometry(
                length=500.0,
                height_left=300.0,
                height_right=300.0,
                thickness_existing=30.0,
                thickness_design=30.0
            )
        if self.materials is None:
            self.materials = WallMaterials()

    @classmethod
    def from_simple(cls, length: float, height: float, thickness: float,
                    material_type: str = "blocchi", knowledge_level: str = "LC1"):
        """Crea muro da parametri semplici (retrocompatibilità)"""
        geometry = WallGeometry(
            length=length,
            height_left=height,
            height_right=height,
            thickness_existing=thickness,
            thickness_design=thickness
        )
        kl = KnowledgeLevel(knowledge_level) if isinstance(knowledge_level, str) else knowledge_level
        return cls(geometry=geometry, knowledge_level=kl)

    @classmethod
    def from_acca(cls, setti_muri: list, dati_muro: dict):
        """
        Crea muro da dati ACCA iEM

        Args:
            setti_muri: Lista di setti murari dal database ACCA
            dati_muro: Dati generali del muro dal database ACCA
        """
        # Calcola dimensioni totali dai setti
        if setti_muri:
            total_base = sum(s.get('Base', 0) for s in setti_muri)
            max_height_left = max(s.get('AltezzaSx', 300) for s in setti_muri)
            max_height_right = max(s.get('AltezzaDx', 300) for s in setti_muri)
        else:
            total_base = 500
            max_height_left = 300
            max_height_right = 300

        geometry = WallGeometry(
            length=total_base,
            height_left=max_height_left,
            height_right=max_height_right,
            thickness_existing=dati_muro.get('MUSpessoreDifatto', 30),
            thickness_design=dati_muro.get('MUSpessoreDiProgetto', 30)
        )

        materials = WallMaterials(
            masonry_existing_id=dati_muro.get('MaterialeDiFatto', 0),
            masonry_design_id=dati_muro.get('MaterialeDiProgetto', 0),
            concrete_id=dati_muro.get('MaterialeCA', 0),
            steel_profiles_id=dati_muro.get('MaterialeACProfilati', 0),
            steel_rebars_id=dati_muro.get('MaterialeACTondini', 0),
            infill_id=dati_muro.get('MaterialeChiusura', 0)
        )

        wall = cls(geometry=geometry, materials=materials)
        wall.wall_segments = setti_muri
        return wall

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'geometry': {
                'length': self.geometry.length,
                'height_left': self.geometry.height_left,
                'height_right': self.geometry.height_right,
                'thickness_existing': self.geometry.thickness_existing,
                'thickness_design': self.geometry.thickness_design
            },
            'materials': {
                'masonry_existing_id': self.materials.masonry_existing_id,
                'masonry_design_id': self.materials.masonry_design_id,
                'concrete_id': self.materials.concrete_id,
                'steel_profiles_id': self.materials.steel_profiles_id,
                'steel_rebars_id': self.materials.steel_rebars_id,
                'infill_id': self.materials.infill_id
            },
            'knowledge_level': self.knowledge_level.value,
            'wall_segments': self.wall_segments
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Wall':
        """Deserializza da dizionario"""
        geom_data = data.get('geometry', {})
        geometry = WallGeometry(
            length=geom_data.get('length', 500),
            height_left=geom_data.get('height_left', geom_data.get('height', 300)),
            height_right=geom_data.get('height_right', geom_data.get('height', 300)),
            thickness_existing=geom_data.get('thickness_existing', geom_data.get('thickness', 30)),
            thickness_design=geom_data.get('thickness_design', geom_data.get('thickness', 30))
        )

        mat_data = data.get('materials', {})
        materials = WallMaterials(
            masonry_existing_id=mat_data.get('masonry_existing_id', 0),
            masonry_design_id=mat_data.get('masonry_design_id', 0),
            concrete_id=mat_data.get('concrete_id', 0),
            steel_profiles_id=mat_data.get('steel_profiles_id', 0),
            steel_rebars_id=mat_data.get('steel_rebars_id', 0),
            infill_id=mat_data.get('infill_id', 0)
        )

        kl_str = data.get('knowledge_level', 'LC1')
        knowledge_level = KnowledgeLevel(kl_str) if kl_str in ['LC1', 'LC2', 'LC3'] else KnowledgeLevel.LC1

        wall = cls(geometry=geometry, materials=materials, knowledge_level=knowledge_level)
        wall.wall_segments = data.get('wall_segments', [])
        return wall

    # Proprietà di retrocompatibilità
    @property
    def length(self) -> float:
        return self.geometry.length

    @property
    def height(self) -> float:
        return self.geometry.height

    @property
    def thickness(self) -> float:
        return self.geometry.thickness_existing

    @property
    def area(self) -> float:
        return self.geometry.area_existing
