"""
Modelli Verifiche NTC 2018
Verifiche strutturali per cerchiature e maschi murari
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class VerificationStatus(Enum):
    """Esito verifica"""
    NOT_VERIFIED = 0   # Non verificato
    VERIFIED = 1       # Verificato


@dataclass
class ResistanceVerification:
    """
    Verifica di resistenza globale
    Confronto tra resistenza di fatto e di progetto
    """
    id: int = 0
    resistance_existing: float = 0.0   # N - Resistenza di fatto
    resistance_design: float = 0.0     # N - Resistenza di progetto
    safety_factor: float = 1.0         # Coefficiente di sicurezza
    status: VerificationStatus = VerificationStatus.NOT_VERIFIED

    @property
    def is_verified(self) -> bool:
        """La verifica è soddisfatta se R_progetto >= R_fatto"""
        return self.resistance_design >= self.resistance_existing

    def calculate_safety_factor(self):
        """Calcola il coefficiente di sicurezza"""
        if self.resistance_existing > 0:
            self.safety_factor = self.resistance_design / self.resistance_existing
        else:
            self.safety_factor = float('inf')
        self.status = VerificationStatus.VERIFIED if self.is_verified else VerificationStatus.NOT_VERIFIED

    @classmethod
    def from_acca(cls, data: dict) -> 'ResistanceVerification':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            resistance_existing=data.get('ResistenzaDiFatto', 0),
            resistance_design=data.get('ResistenzaDiProgetto', 0),
            safety_factor=data.get('CoeffSic', 1),
            status=VerificationStatus(data.get('FlagVerifica', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'resistance_existing': self.resistance_existing,
            'resistance_design': self.resistance_design,
            'safety_factor': self.safety_factor,
            'status': self.status.value
        }


@dataclass
class StiffnessVerification:
    """
    Verifica di rigidezza
    Confronto tra rigidezza di fatto e di progetto
    """
    id: int = 0
    stiffness_existing: float = 0.0   # N/mm - Rigidezza di fatto
    stiffness_design: float = 0.0     # N/mm - Rigidezza di progetto
    safety_factor: float = 1.0
    status: VerificationStatus = VerificationStatus.NOT_VERIFIED

    @property
    def is_verified(self) -> bool:
        """La verifica è soddisfatta se K_progetto >= K_fatto"""
        return self.stiffness_design >= self.stiffness_existing

    def calculate_safety_factor(self):
        """Calcola il coefficiente di sicurezza"""
        if self.stiffness_existing > 0:
            self.safety_factor = self.stiffness_design / self.stiffness_existing
        else:
            self.safety_factor = float('inf')
        self.status = VerificationStatus.VERIFIED if self.is_verified else VerificationStatus.NOT_VERIFIED

    @classmethod
    def from_acca(cls, data: dict) -> 'StiffnessVerification':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            stiffness_existing=data.get('RigidezzaDocDifatto', 0),
            stiffness_design=data.get('RigidezzaDocDiProgetto', 0),
            safety_factor=data.get('CoeffSic', 1),
            status=VerificationStatus(data.get('FlagVerifica', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'stiffness_existing': self.stiffness_existing,
            'stiffness_design': self.stiffness_design,
            'safety_factor': self.safety_factor,
            'status': self.status.value
        }


@dataclass
class DisplacementVerification:
    """
    Verifica di spostamento
    Confronto tra spostamento di fatto e di progetto
    """
    id: int = 0
    displacement_existing: float = 0.0  # mm - Spostamento di fatto
    displacement_design: float = 0.0    # mm - Spostamento di progetto (ammissibile)
    safety_factor: float = 1.0
    status: VerificationStatus = VerificationStatus.NOT_VERIFIED

    @property
    def is_verified(self) -> bool:
        """La verifica è soddisfatta se d_fatto <= d_progetto (ammissibile)"""
        return self.displacement_existing <= self.displacement_design

    def calculate_safety_factor(self):
        """Calcola il coefficiente di sicurezza"""
        if self.displacement_existing > 0:
            self.safety_factor = self.displacement_design / self.displacement_existing
        else:
            self.safety_factor = float('inf')
        self.status = VerificationStatus.VERIFIED if self.is_verified else VerificationStatus.NOT_VERIFIED

    @classmethod
    def from_acca(cls, data: dict) -> 'DisplacementVerification':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            displacement_existing=data.get('SpostamentoDiFatto', 0),
            displacement_design=data.get('SpostamentoDiProgetto', 0),
            safety_factor=data.get('CoeffSic', 1),
            status=VerificationStatus(data.get('FlagVerifica', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'displacement_existing': self.displacement_existing,
            'displacement_design': self.displacement_design,
            'safety_factor': self.safety_factor,
            'status': self.status.value
        }


@dataclass
class BendingVerification:
    """
    Verifica a pressoflessione (NTC 2018 - 4.1.2.1.2)
    Per elementi beam della cerchiatura
    """
    id: int = 0
    beam_id: int = 0

    # Sollecitazioni di progetto
    Nd: float = 0.0   # N - Sforzo normale di progetto
    Md: float = 0.0   # Nmm - Momento flettente di progetto
    Vd: float = 0.0   # N - Taglio di progetto

    # Resistenze
    Mr: float = 0.0   # Nmm - Momento resistente

    safety_factor: float = 1.0
    status: VerificationStatus = VerificationStatus.NOT_VERIFIED

    @property
    def is_verified(self) -> bool:
        """Verifica: Md <= Mr"""
        return abs(self.Md) <= abs(self.Mr)

    def calculate_safety_factor(self):
        """Calcola il coefficiente di sicurezza"""
        if abs(self.Md) > 0:
            self.safety_factor = abs(self.Mr) / abs(self.Md)
        else:
            self.safety_factor = float('inf') if self.Mr != 0 else 1.0
        self.status = VerificationStatus.VERIFIED if self.is_verified else VerificationStatus.NOT_VERIFIED

    @classmethod
    def from_acca(cls, data: dict) -> 'BendingVerification':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            beam_id=data.get('IdBeam', 0),
            Nd=data.get('Nd', 0),
            Md=data.get('Md', 0),
            Vd=data.get('Vd', 0),
            Mr=data.get('Mr', 0),
            safety_factor=data.get('CoeffSic', 1),
            status=VerificationStatus(data.get('FlagVerifica', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'beam_id': self.beam_id,
            'Nd': self.Nd,
            'Md': self.Md,
            'Vd': self.Vd,
            'Mr': self.Mr,
            'safety_factor': self.safety_factor,
            'status': self.status.value
        }


@dataclass
class ShearVerification:
    """
    Verifica a taglio (NTC 2018 - 4.1.2.3)
    Per elementi beam della cerchiatura
    """
    id: int = 0
    beam_id: int = 0

    # Sollecitazioni e resistenze
    Td: float = 0.0    # N - Taglio di progetto
    Tr: float = 0.0    # N - Taglio resistente

    # Per sezioni in C.A.
    Vcc: float = 0.0   # N - Contributo calcestruzzo compresso
    Vwd: float = 0.0   # N - Contributo armatura trasversale
    Aft: float = 0.0   # mm² - Area staffe/passo
    cot_theta: float = 1.0  # Cotangente angolo puntone

    safety_factor: float = 1.0
    status: VerificationStatus = VerificationStatus.NOT_VERIFIED

    @property
    def is_verified(self) -> bool:
        """Verifica: Td <= Tr"""
        return abs(self.Td) <= abs(self.Tr)

    def calculate_safety_factor(self):
        """Calcola il coefficiente di sicurezza"""
        if abs(self.Td) > 0:
            self.safety_factor = abs(self.Tr) / abs(self.Td)
        else:
            self.safety_factor = float('inf') if self.Tr != 0 else 1.0
        # Limita a 100 per visualizzazione
        self.safety_factor = min(self.safety_factor, 100.0)
        self.status = VerificationStatus.VERIFIED if self.is_verified else VerificationStatus.NOT_VERIFIED

    @classmethod
    def from_acca(cls, data: dict) -> 'ShearVerification':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            beam_id=data.get('IdBeam', 0),
            Td=data.get('Td', 0),
            Tr=data.get('Tr', 0),
            Vcc=data.get('Vcc', 0),
            Vwd=data.get('Vwd', 0),
            Aft=data.get('Aft', 0),
            cot_theta=data.get('CtgTheta', 1),
            safety_factor=data.get('CoeffSic', 1),
            status=VerificationStatus(data.get('FlagVerifica', 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'beam_id': self.beam_id,
            'Td': self.Td,
            'Tr': self.Tr,
            'Vcc': self.Vcc,
            'Vwd': self.Vwd,
            'Aft': self.Aft,
            'cot_theta': self.cot_theta,
            'safety_factor': self.safety_factor,
            'status': self.status.value
        }


@dataclass
class VerificationResults:
    """
    Raccolta di tutti i risultati delle verifiche
    """
    # Verifiche globali
    resistance: Optional[ResistanceVerification] = None
    stiffness: Optional[StiffnessVerification] = None
    displacement: Optional[DisplacementVerification] = None

    # Verifiche locali per beam
    bending_verifications: List[BendingVerification] = field(default_factory=list)
    shear_verifications: List[ShearVerification] = field(default_factory=list)

    @property
    def all_verified(self) -> bool:
        """Tutte le verifiche sono soddisfatte"""
        global_ok = True
        if self.resistance:
            global_ok = global_ok and self.resistance.is_verified
        if self.stiffness:
            global_ok = global_ok and self.stiffness.is_verified
        if self.displacement:
            global_ok = global_ok and self.displacement.is_verified

        bending_ok = all(v.is_verified for v in self.bending_verifications)
        shear_ok = all(v.is_verified for v in self.shear_verifications)

        return global_ok and bending_ok and shear_ok

    @property
    def min_safety_factor(self) -> float:
        """Coefficiente di sicurezza minimo tra tutte le verifiche"""
        factors = []

        if self.resistance:
            factors.append(self.resistance.safety_factor)
        if self.stiffness:
            factors.append(self.stiffness.safety_factor)
        if self.displacement:
            factors.append(self.displacement.safety_factor)

        for v in self.bending_verifications:
            factors.append(v.safety_factor)
        for v in self.shear_verifications:
            factors.append(v.safety_factor)

        return min(factors) if factors else 1.0

    def get_critical_verification(self) -> str:
        """Restituisce la verifica più critica"""
        min_factor = float('inf')
        critical = "Nessuna"

        if self.resistance and self.resistance.safety_factor < min_factor:
            min_factor = self.resistance.safety_factor
            critical = "Resistenza globale"

        if self.stiffness and self.stiffness.safety_factor < min_factor:
            min_factor = self.stiffness.safety_factor
            critical = "Rigidezza"

        if self.displacement and self.displacement.safety_factor < min_factor:
            min_factor = self.displacement.safety_factor
            critical = "Spostamento"

        for v in self.bending_verifications:
            if v.safety_factor < min_factor:
                min_factor = v.safety_factor
                critical = f"Pressoflessione Beam {v.beam_id}"

        for v in self.shear_verifications:
            if v.safety_factor < min_factor:
                min_factor = v.safety_factor
                critical = f"Taglio Beam {v.beam_id}"

        return critical

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'resistance': self.resistance.to_dict() if self.resistance else None,
            'stiffness': self.stiffness.to_dict() if self.stiffness else None,
            'displacement': self.displacement.to_dict() if self.displacement else None,
            'bending_verifications': [v.to_dict() for v in self.bending_verifications],
            'shear_verifications': [v.to_dict() for v in self.shear_verifications],
            'all_verified': self.all_verified,
            'min_safety_factor': self.min_safety_factor,
            'critical_verification': self.get_critical_verification()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationResults':
        """Deserializza da dizionario"""
        result = cls()

        if data.get('resistance'):
            result.resistance = ResistanceVerification(**data['resistance'])

        if data.get('stiffness'):
            result.stiffness = StiffnessVerification(**data['stiffness'])

        if data.get('displacement'):
            result.displacement = DisplacementVerification(**data['displacement'])

        for v_data in data.get('bending_verifications', []):
            result.bending_verifications.append(BendingVerification(**v_data))

        for v_data in data.get('shear_verifications', []):
            result.shear_verifications.append(ShearVerification(**v_data))

        return result
