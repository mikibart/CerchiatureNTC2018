"""
Modello Apertura
Rappresenta un'apertura nel muro con cerchiatura
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class OpeningType(Enum):
    """Tipo di apertura"""
    RECTANGULAR = "rectangular"  # Rettangolare standard
    ARCHED = "arched"           # Con arco
    CURVED = "curved"           # Curva


class SituationType(Enum):
    """Situazione dell'apertura"""
    EXISTING = 1   # Di fatto (esistente) - ACCA usa 1
    DESIGN = 2     # Di progetto (nuova) - ACCA usa 2


class FrameType(Enum):
    """Tipo di cerchiatura"""
    LINTEL_ONLY = 0      # Solo piattabanda
    FULL_FRAME = 1       # Telaio completo (piattabanda + piedritti + base)


class ProfileType(Enum):
    """Tipologia profilato"""
    STEEL_PROFILE = 11001  # Profilato in acciaio
    CONCRETE_BEAM = 11002  # Trave in C.A.


@dataclass
class ConcreteReinforcement:
    """Armatura in C.A. per un elemento"""
    num_rebars: int = 2          # Numero ferri longitudinali
    rebar_diameter: int = 10     # Diametro ferri mm
    stirrup_diameter: int = 8    # Diametro staffe mm
    stirrup_spacing: int = 20    # Passo staffe cm


@dataclass
class OpeningGeometry:
    """Geometria dell'apertura"""
    width: float           # cm - Larghezza apertura
    height: float          # cm - Altezza apertura
    dist_left: float       # cm - Distanza dal bordo sinistro del muro
    dist_right: float      # cm - Distanza dal bordo destro del muro
    dist_base: float       # cm - Distanza dalla base del muro
    height_base: float     # cm - Altezza della base (soglia)
    jamb_thickness: float  # cm - Spessore piedritti
    lintel_height: float   # cm - Altezza piattabanda

    @property
    def x(self) -> float:
        """Posizione X (da sinistra) - retrocompatibilità"""
        return self.dist_left

    @property
    def y(self) -> float:
        """Posizione Y (dal basso) - retrocompatibilità"""
        return self.dist_base


@dataclass
class OpeningProfiles:
    """Profilati per la cerchiatura"""
    lintel_profile_id: int = 0       # ID profilato piattabanda
    jamb_profile_id: int = 0         # ID profilato piedritti
    base_profile_id: int = 0         # ID profilato base
    lintel_type: ProfileType = ProfileType.STEEL_PROFILE
    jamb_type: ProfileType = ProfileType.STEEL_PROFILE
    base_type: ProfileType = ProfileType.STEEL_PROFILE
    num_profiles: int = 1            # Numero di profili (doppio UPN, ecc.)


@dataclass
class Opening:
    """
    Apertura completa con geometria, profilati e armatura
    Supporta formato ACCA iEM
    """
    id: int = 0
    geometry: OpeningGeometry = None
    profiles: OpeningProfiles = None

    # Tipo e situazione
    opening_type: OpeningType = OpeningType.RECTANGULAR
    situation: SituationType = SituationType.DESIGN
    frame_type: FrameType = FrameType.FULL_FRAME
    is_door: bool = False

    # Armatura C.A. per elementi
    lintel_reinforcement: ConcreteReinforcement = None
    jamb_reinforcement: ConcreteReinforcement = None
    base_reinforcement: ConcreteReinforcement = None

    # Risultati calcolo (popolati dopo analisi)
    beam_elements: List[Dict] = field(default_factory=list)
    verification_results: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.geometry is None:
            self.geometry = OpeningGeometry(
                width=120.0,
                height=150.0,
                dist_left=50.0,
                dist_right=50.0,
                dist_base=0.0,
                height_base=10.0,
                jamb_thickness=10.0,
                lintel_height=10.0
            )
        if self.profiles is None:
            self.profiles = OpeningProfiles()
        if self.lintel_reinforcement is None:
            self.lintel_reinforcement = ConcreteReinforcement()
        if self.jamb_reinforcement is None:
            self.jamb_reinforcement = ConcreteReinforcement()
        if self.base_reinforcement is None:
            self.base_reinforcement = ConcreteReinforcement()

    @classmethod
    def from_simple(cls, width: float, height: float, x: float, y: float,
                    opening_type: str = "rectangular", is_existing: bool = False):
        """Crea apertura da parametri semplici (retrocompatibilità)"""
        geometry = OpeningGeometry(
            width=width,
            height=height,
            dist_left=x,
            dist_right=0,  # Da calcolare
            dist_base=y,
            height_base=10.0,
            jamb_thickness=10.0,
            lintel_height=10.0
        )
        situation = SituationType.EXISTING if is_existing else SituationType.DESIGN
        op_type = OpeningType(opening_type) if opening_type in [e.value for e in OpeningType] else OpeningType.RECTANGULAR

        return cls(geometry=geometry, opening_type=op_type, situation=situation)

    @classmethod
    def from_acca(cls, foro_data: dict):
        """
        Crea apertura da dati ACCA iEM

        Args:
            foro_data: Dizionario con dati del foro dal database ACCA
        """
        geometry = OpeningGeometry(
            width=foro_data.get('Larghezza', 120),
            height=foro_data.get('Altezza', 150),
            dist_left=foro_data.get('DistLateraleSx', 50),
            dist_right=foro_data.get('DistLateraleDx', 50),
            dist_base=foro_data.get('DistBase', 0),
            height_base=foro_data.get('AltezzaBase', 10),
            jamb_thickness=foro_data.get('SpsPiedritti', 10),
            lintel_height=foro_data.get('AltezzaPiattabanda', 10)
        )

        profiles = OpeningProfiles(
            lintel_profile_id=foro_data.get('ProfilatoPiattabanda', 0),
            jamb_profile_id=foro_data.get('ProfilatoPiedritti', 0),
            base_profile_id=foro_data.get('ProfilatoBase', 0),
            lintel_type=ProfileType(foro_data.get('TipologiaPrfltPittabanda', 11001)),
            jamb_type=ProfileType(foro_data.get('TipologiaPrfltPiedritti', 11001)),
            base_type=ProfileType(foro_data.get('TipologiaPrfltBase', 11001)),
            num_profiles=foro_data.get('NumeroProfili', 1)
        )

        # Armatura piattabanda
        lintel_reinf = ConcreteReinforcement(
            num_rebars=foro_data.get('NumFerriPiattabanda', 2),
            rebar_diameter=foro_data.get('DiamFerriPiattabanda', 10),
            stirrup_diameter=foro_data.get('DiamStaffePiattabanda', 8),
            stirrup_spacing=foro_data.get('PassoStaffePiattabanda', 20)
        )

        # Armatura piedritti
        jamb_reinf = ConcreteReinforcement(
            num_rebars=foro_data.get('NumFerriPiedritti', 2),
            rebar_diameter=foro_data.get('DiamFerriPiedritti', 10),
            stirrup_diameter=foro_data.get('DiamStaffePiedritti', 8),
            stirrup_spacing=foro_data.get('PassoStaffePiedritti', 20)
        )

        # Armatura base
        base_reinf = ConcreteReinforcement(
            num_rebars=foro_data.get('NumFerriBase', 2),
            rebar_diameter=foro_data.get('DiamFerriBase', 10),
            stirrup_diameter=foro_data.get('DiamStaffeBase', 8),
            stirrup_spacing=foro_data.get('PassoStaffeBase', 20)
        )

        # Situazione e tipo
        situation = SituationType(foro_data.get('SituazioneForo', 1))
        frame_type = FrameType(foro_data.get('TipoCerchiatura', 1))
        is_door = bool(foro_data.get('IsPorta', False))

        return cls(
            id=foro_data.get('Id', 0),
            geometry=geometry,
            profiles=profiles,
            situation=situation,
            frame_type=frame_type,
            is_door=is_door,
            lintel_reinforcement=lintel_reinf,
            jamb_reinforcement=jamb_reinf,
            base_reinforcement=base_reinf
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'geometry': {
                'width': self.geometry.width,
                'height': self.geometry.height,
                'dist_left': self.geometry.dist_left,
                'dist_right': self.geometry.dist_right,
                'dist_base': self.geometry.dist_base,
                'height_base': self.geometry.height_base,
                'jamb_thickness': self.geometry.jamb_thickness,
                'lintel_height': self.geometry.lintel_height
            },
            'profiles': {
                'lintel_profile_id': self.profiles.lintel_profile_id,
                'jamb_profile_id': self.profiles.jamb_profile_id,
                'base_profile_id': self.profiles.base_profile_id,
                'lintel_type': self.profiles.lintel_type.value,
                'jamb_type': self.profiles.jamb_type.value,
                'base_type': self.profiles.base_type.value,
                'num_profiles': self.profiles.num_profiles
            },
            'opening_type': self.opening_type.value,
            'situation': self.situation.value,
            'frame_type': self.frame_type.value,
            'is_door': self.is_door,
            'lintel_reinforcement': {
                'num_rebars': self.lintel_reinforcement.num_rebars,
                'rebar_diameter': self.lintel_reinforcement.rebar_diameter,
                'stirrup_diameter': self.lintel_reinforcement.stirrup_diameter,
                'stirrup_spacing': self.lintel_reinforcement.stirrup_spacing
            },
            'jamb_reinforcement': {
                'num_rebars': self.jamb_reinforcement.num_rebars,
                'rebar_diameter': self.jamb_reinforcement.rebar_diameter,
                'stirrup_diameter': self.jamb_reinforcement.stirrup_diameter,
                'stirrup_spacing': self.jamb_reinforcement.stirrup_spacing
            },
            'base_reinforcement': {
                'num_rebars': self.base_reinforcement.num_rebars,
                'rebar_diameter': self.base_reinforcement.rebar_diameter,
                'stirrup_diameter': self.base_reinforcement.stirrup_diameter,
                'stirrup_spacing': self.base_reinforcement.stirrup_spacing
            },
            'beam_elements': self.beam_elements,
            'verification_results': self.verification_results
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Opening':
        """Deserializza da dizionario"""
        geom_data = data.get('geometry', {})
        geometry = OpeningGeometry(
            width=geom_data.get('width', 120),
            height=geom_data.get('height', 150),
            dist_left=geom_data.get('dist_left', geom_data.get('x', 50)),
            dist_right=geom_data.get('dist_right', 50),
            dist_base=geom_data.get('dist_base', geom_data.get('y', 0)),
            height_base=geom_data.get('height_base', 10),
            jamb_thickness=geom_data.get('jamb_thickness', 10),
            lintel_height=geom_data.get('lintel_height', 10)
        )

        prof_data = data.get('profiles', {})
        profiles = OpeningProfiles(
            lintel_profile_id=prof_data.get('lintel_profile_id', 0),
            jamb_profile_id=prof_data.get('jamb_profile_id', 0),
            base_profile_id=prof_data.get('base_profile_id', 0),
            lintel_type=ProfileType(prof_data.get('lintel_type', 11001)),
            jamb_type=ProfileType(prof_data.get('jamb_type', 11001)),
            base_type=ProfileType(prof_data.get('base_type', 11001)),
            num_profiles=prof_data.get('num_profiles', 1)
        )

        # Armature
        def load_reinforcement(reinf_data):
            return ConcreteReinforcement(
                num_rebars=reinf_data.get('num_rebars', 2),
                rebar_diameter=reinf_data.get('rebar_diameter', 10),
                stirrup_diameter=reinf_data.get('stirrup_diameter', 8),
                stirrup_spacing=reinf_data.get('stirrup_spacing', 20)
            )

        lintel_reinf = load_reinforcement(data.get('lintel_reinforcement', {}))
        jamb_reinf = load_reinforcement(data.get('jamb_reinforcement', {}))
        base_reinf = load_reinforcement(data.get('base_reinforcement', {}))

        # Enums
        op_type_val = data.get('opening_type', 'rectangular')
        opening_type = OpeningType(op_type_val) if op_type_val in [e.value for e in OpeningType] else OpeningType.RECTANGULAR

        situation = SituationType(data.get('situation', 1))
        frame_type = FrameType(data.get('frame_type', 1))

        opening = cls(
            id=data.get('id', 0),
            geometry=geometry,
            profiles=profiles,
            opening_type=opening_type,
            situation=situation,
            frame_type=frame_type,
            is_door=data.get('is_door', False),
            lintel_reinforcement=lintel_reinf,
            jamb_reinforcement=jamb_reinf,
            base_reinforcement=base_reinf
        )
        opening.beam_elements = data.get('beam_elements', [])
        opening.verification_results = data.get('verification_results', {})

        return opening

    # Proprietà di retrocompatibilità
    @property
    def width(self) -> float:
        return self.geometry.width

    @property
    def height(self) -> float:
        return self.geometry.height

    @property
    def x(self) -> float:
        return self.geometry.x

    @property
    def y(self) -> float:
        return self.geometry.y

    @property
    def is_existing(self) -> bool:
        return self.situation == SituationType.EXISTING
