"""
ReinforcementCalculator Interface
=================================

Interfaccia base per tutti i calcolatori di rinforzo (cerchiature).
Definisce il contratto che ogni calcolatore deve implementare.

Pattern: Strategy + Plugin
Ogni tipo di rinforzo (acciaio, c.a., arco) implementa questa interfaccia.

Arch. Michelangelo Bartolotta
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from src.core.engine.frame_result import FrameResult

logger = logging.getLogger(__name__)


class ReinforcementMaterial(Enum):
    """Materiali supportati per rinforzi"""
    STEEL = "acciaio"
    CONCRETE = "ca"
    MIXED = "misto"
    WOOD = "legno"  # Per future estensioni
    FRP = "frp"     # Per future estensioni


class ReinforcementType(Enum):
    """Tipi di rinforzo supportati"""
    PORTAL_FRAME = "telaio_completo"
    BEAM_ONLY = "solo_architrave"
    ARCH = "arco"
    ARCH_BENT = "arco_calandrato"


@dataclass
class ReinforcementCapability:
    """Descrive le capacità di un calcolatore di rinforzo"""
    name: str
    description: str
    materials: List[ReinforcementMaterial]
    types: List[ReinforcementType]
    supports_arch: bool = False
    supports_capacity_check: bool = True
    supports_crack_check: bool = False
    version: str = "1.0.0"
    author: str = ""


@dataclass
class CalculationInput:
    """Input standardizzato per il calcolo"""
    opening: Dict[str, Any]      # Dati apertura (x, y, width, height, type)
    reinforcement: Dict[str, Any] # Dati rinforzo (tipo, materiale, profili/sezioni)
    wall: Optional[Dict[str, Any]] = None  # Dati parete (opzionale)
    loads: Optional[Dict[str, Any]] = None # Carichi applicati (opzionale)

    def validate(self) -> List[str]:
        """Valida l'input e restituisce lista errori"""
        errors = []

        if not self.opening:
            errors.append("Dati apertura mancanti")
        elif not self.opening.get('width') or not self.opening.get('height'):
            errors.append("Dimensioni apertura incomplete")

        if not self.reinforcement:
            errors.append("Dati rinforzo mancanti")
        elif not self.reinforcement.get('materiale'):
            errors.append("Materiale rinforzo non specificato")

        return errors


@dataclass
class CalculationOutput:
    """Output standardizzato del calcolo"""
    # Risultati principali
    K_frame: float = 0.0          # Rigidezza laterale [kN/m]
    V_capacity: float = 0.0       # Capacità tagliante [kN]
    M_capacity: float = 0.0       # Capacità momento [kNm]
    N_capacity: float = 0.0       # Capacità assiale [kN]

    # Stato
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Dettagli aggiuntivi
    details: Dict[str, Any] = field(default_factory=dict)
    frame_result: Optional[FrameResult] = None

    def add_error(self, error: str):
        """Aggiunge un errore"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str):
        """Aggiunge un warning"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict:
        """Converte in dizionario"""
        result = {
            'K_frame': self.K_frame,
            'V_capacity': self.V_capacity,
            'M_capacity': self.M_capacity,
            'N_capacity': self.N_capacity,
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': self.details
        }
        if self.frame_result:
            result['frame_result'] = self.frame_result.to_dict()
        return result


class ReinforcementCalculator(ABC):
    """
    Interfaccia base per calcolatori di rinforzo.

    Ogni calcolatore (acciaio, c.a., arco, etc.) deve implementare
    questa interfaccia per essere registrato nel sistema plugin.

    Metodi richiesti:
    - get_capability(): Restituisce le capacità del calcolatore
    - can_handle(): Verifica se può gestire un certo rinforzo
    - calculate_stiffness(): Calcola la rigidezza del rinforzo
    - calculate_capacity(): Calcola la capacità portante

    Metodi opzionali:
    - validate_input(): Validazione input specifica
    - get_default_config(): Configurazione default
    """

    @abstractmethod
    def get_capability(self) -> ReinforcementCapability:
        """
        Restituisce le capacità del calcolatore.

        Returns:
            ReinforcementCapability con descrizione capacità
        """
        pass

    @abstractmethod
    def can_handle(self, reinforcement_data: Dict) -> bool:
        """
        Verifica se il calcolatore può gestire questo tipo di rinforzo.

        Args:
            reinforcement_data: Dati del rinforzo da verificare

        Returns:
            True se può gestire, False altrimenti
        """
        pass

    @abstractmethod
    def calculate_stiffness(self, input_data: CalculationInput) -> CalculationOutput:
        """
        Calcola la rigidezza laterale del rinforzo.

        Args:
            input_data: Input standardizzato con dati apertura e rinforzo

        Returns:
            CalculationOutput con rigidezza e dettagli
        """
        pass

    @abstractmethod
    def calculate_capacity(self, input_data: CalculationInput) -> CalculationOutput:
        """
        Calcola la capacità portante del rinforzo.

        Args:
            input_data: Input standardizzato

        Returns:
            CalculationOutput con capacità M, V, N
        """
        pass

    def validate_input(self, input_data: CalculationInput) -> List[str]:
        """
        Validazione input specifica per questo calcolatore.

        Override per aggiungere validazioni specifiche.

        Args:
            input_data: Input da validare

        Returns:
            Lista errori (vuota se valido)
        """
        return input_data.validate()

    def get_default_config(self) -> Dict:
        """
        Restituisce configurazione default per questo tipo di rinforzo.

        Override per fornire configurazioni predefinite.

        Returns:
            Dict con configurazione default
        """
        return {}

    def calculate(self, input_data: CalculationInput) -> CalculationOutput:
        """
        Metodo principale che esegue il calcolo completo.

        Combina stiffness e capacity in un unico risultato.

        Args:
            input_data: Input standardizzato

        Returns:
            CalculationOutput completo
        """
        # Valida input
        errors = self.validate_input(input_data)
        if errors:
            output = CalculationOutput(success=False)
            for error in errors:
                output.add_error(error)
            return output

        # Calcola rigidezza
        stiffness_result = self.calculate_stiffness(input_data)
        if not stiffness_result.success:
            return stiffness_result

        # Calcola capacità
        capacity_result = self.calculate_capacity(input_data)

        # Combina risultati
        combined = CalculationOutput(
            K_frame=stiffness_result.K_frame,
            V_capacity=capacity_result.V_capacity,
            M_capacity=capacity_result.M_capacity,
            N_capacity=capacity_result.N_capacity,
            success=stiffness_result.success and capacity_result.success,
            errors=stiffness_result.errors + capacity_result.errors,
            warnings=stiffness_result.warnings + capacity_result.warnings,
            details={**stiffness_result.details, **capacity_result.details},
            frame_result=stiffness_result.frame_result
        )

        return combined
