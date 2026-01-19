"""
Reinforcement Plugins - Adapter per Calcolatori Esistenti
=========================================================

Adapter che wrappano i calcolatori esistenti (SteelFrameCalculator,
ConcreteFrameCalculator) con l'interfaccia ReinforcementCalculator.

Questo permette di:
- Mantenere retrocompatibilità con codice esistente
- Usare i calcolatori nel nuovo sistema plugin
- Migrare gradualmente verso la nuova architettura

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional
import logging

from .reinforcement_interface import (
    ReinforcementCalculator,
    ReinforcementCapability,
    ReinforcementMaterial,
    ReinforcementType,
    CalculationInput,
    CalculationOutput
)
from .reinforcement_registry import ReinforcementRegistry
from .steel_frame import SteelFrameCalculator
from .concrete_frame import ConcreteFrameCalculator
from .frame_result import FrameResult

logger = logging.getLogger(__name__)


@ReinforcementRegistry.register
class SteelFramePlugin(ReinforcementCalculator):
    """
    Plugin per cerchiature in acciaio.

    Wrappa SteelFrameCalculator esistente con nuova interfaccia.
    """

    def __init__(self):
        self._calculator = SteelFrameCalculator()

    def get_capability(self) -> ReinforcementCapability:
        return ReinforcementCapability(
            name="Cerchiature Acciaio",
            description="Calcolo cerchiature metalliche in profili laminati (HEA, HEB, IPE)",
            materials=[ReinforcementMaterial.STEEL],
            types=[
                ReinforcementType.PORTAL_FRAME,
                ReinforcementType.BEAM_ONLY,
                ReinforcementType.ARCH,
                ReinforcementType.ARCH_BENT
            ],
            supports_arch=True,
            supports_capacity_check=True,
            supports_crack_check=False,
            version="2.0.0",
            author="Arch. Michelangelo Bartolotta"
        )

    def can_handle(self, reinforcement_data: Dict) -> bool:
        materiale = reinforcement_data.get('materiale', '')
        return materiale.lower() in ['acciaio', 'steel', 'metallo']

    def validate_input(self, input_data: CalculationInput) -> List[str]:
        errors = input_data.validate()

        rinforzo = input_data.reinforcement
        if rinforzo.get('materiale', '').lower() not in ['acciaio', 'steel', 'metallo']:
            errors.append("Questo calcolatore gestisce solo rinforzi in acciaio")

        # Verifica profili
        tipo = rinforzo.get('tipo', '')
        if 'Telaio' in tipo or 'completo' in tipo.lower():
            if not rinforzo.get('architrave', {}).get('profilo'):
                errors.append("Profilo architrave non specificato")
            if not rinforzo.get('piedritti', {}).get('profilo'):
                errors.append("Profilo piedritti non specificato")
        elif 'architrave' in tipo.lower():
            if not rinforzo.get('architrave', {}).get('profilo'):
                errors.append("Profilo architrave non specificato")

        return errors

    def calculate_stiffness(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()

        try:
            # Chiama calcolatore esistente
            result = self._calculator.calculate_frame_stiffness(
                input_data.opening,
                input_data.reinforcement
            )

            output.K_frame = result.get('K_frame', 0)
            output.details = {
                'tipo': result.get('tipo', ''),
                'materiale': result.get('materiale', 'acciaio'),
                'L': result.get('L', 0),
                'h': result.get('h', 0),
                'extra_data': result.get('extra_data', {})
            }

            # Crea FrameResult
            output.frame_result = FrameResult(
                K_frame=output.K_frame,
                L=result.get('L', 0),
                h=result.get('h', 0),
                tipo=result.get('tipo', ''),
                materiale='acciaio',
                extra_data=result.get('extra_data', {})
            )

            # Warnings
            if result.get('warnings'):
                for w in result['warnings']:
                    output.add_warning(w)

        except Exception as e:
            output.add_error(f"Errore calcolo rigidezza acciaio: {str(e)}")
            logger.error(f"SteelFramePlugin.calculate_stiffness error: {e}")

        return output

    def calculate_capacity(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()

        try:
            # Chiama calcolatore esistente
            result = self._calculator.calculate_frame_capacity(
                input_data.opening,
                input_data.reinforcement,
                input_data.wall or {}
            )

            output.M_capacity = result.get('M_Rd_beam', 0)
            output.V_capacity = result.get('V_Rd_beam', 0)
            output.N_capacity = result.get('N_Rd_column', 0)

            output.details.update({
                'M_Rd_beam': result.get('M_Rd_beam', 0),
                'V_Rd_beam': result.get('V_Rd_beam', 0),
                'M_Rd_column': result.get('M_Rd_column', 0),
                'N_Rd_column': result.get('N_Rd_column', 0)
            })

        except Exception as e:
            output.add_error(f"Errore calcolo capacità acciaio: {str(e)}")
            logger.error(f"SteelFramePlugin.calculate_capacity error: {e}")

        return output

    def get_default_config(self) -> Dict:
        return {
            'materiale': 'acciaio',
            'classe_acciaio': 'S235',
            'tipo': 'Telaio completo in acciaio',
            'architrave': {
                'profilo': 'HEA 160',
                'doppio': False,
                'ruotato': False
            },
            'piedritti': {
                'profilo': 'HEA 160',
                'doppio': False,
                'ruotato': False
            },
            'vincoli': {
                'base': 'Incastro',
                'nodo': 'Incastro (continuità)'
            }
        }


@ReinforcementRegistry.register
class ConcreteFramePlugin(ReinforcementCalculator):
    """
    Plugin per cerchiature in calcestruzzo armato.

    Wrappa ConcreteFrameCalculator esistente con nuova interfaccia.
    """

    def __init__(self):
        self._calculator = ConcreteFrameCalculator()

    def get_capability(self) -> ReinforcementCapability:
        return ReinforcementCapability(
            name="Cerchiature C.A.",
            description="Calcolo cerchiature in calcestruzzo armato gettato in opera",
            materials=[ReinforcementMaterial.CONCRETE],
            types=[
                ReinforcementType.PORTAL_FRAME,
                ReinforcementType.BEAM_ONLY
            ],
            supports_arch=False,
            supports_capacity_check=True,
            supports_crack_check=True,
            version="2.0.0",
            author="Arch. Michelangelo Bartolotta"
        )

    def can_handle(self, reinforcement_data: Dict) -> bool:
        materiale = reinforcement_data.get('materiale', '')
        return materiale.lower() in ['ca', 'c.a.', 'calcestruzzo', 'concrete', 'cemento armato']

    def validate_input(self, input_data: CalculationInput) -> List[str]:
        errors = input_data.validate()

        rinforzo = input_data.reinforcement
        if rinforzo.get('materiale', '').lower() not in ['ca', 'c.a.', 'calcestruzzo', 'concrete']:
            errors.append("Questo calcolatore gestisce solo rinforzi in C.A.")

        # Verifica sezione architrave
        architrave = rinforzo.get('architrave', {})
        if not architrave.get('base') or not architrave.get('altezza'):
            errors.append("Sezione architrave non specificata (base, altezza)")

        # Verifica armature
        if not architrave.get('armatura_sup'):
            errors.append("Armatura superiore architrave non specificata")
        if not architrave.get('armatura_inf'):
            errors.append("Armatura inferiore architrave non specificata")

        return errors

    def calculate_stiffness(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()

        try:
            # Chiama calcolatore esistente
            result = self._calculator.calculate_frame_stiffness(
                input_data.opening,
                input_data.reinforcement
            )

            output.K_frame = result.get('K_frame', 0)
            output.details = {
                'tipo': result.get('tipo', ''),
                'materiale': result.get('materiale', 'ca'),
                'L': result.get('L', 0),
                'h': result.get('h', 0),
                'extra_data': result.get('extra_data', {})
            }

            # Crea FrameResult
            output.frame_result = FrameResult(
                K_frame=output.K_frame,
                L=result.get('L', 0),
                h=result.get('h', 0),
                tipo=result.get('tipo', ''),
                materiale='ca',
                extra_data=result.get('extra_data', {})
            )

            # Warnings
            if result.get('warnings'):
                for w in result['warnings']:
                    output.add_warning(w)

        except Exception as e:
            output.add_error(f"Errore calcolo rigidezza C.A.: {str(e)}")
            logger.error(f"ConcreteFramePlugin.calculate_stiffness error: {e}")

        return output

    def calculate_capacity(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()

        try:
            # Chiama calcolatore esistente
            result = self._calculator.calculate_frame_capacity(
                input_data.opening,
                input_data.reinforcement,
                input_data.wall or {}
            )

            output.M_capacity = result.get('M_Rd_beam', 0)
            output.V_capacity = result.get('V_Rd_beam', 0)
            output.N_capacity = result.get('N_Rd_column', 0)

            output.details.update({
                'M_Rd_beam': result.get('M_Rd_beam', 0),
                'V_Rd_beam': result.get('V_Rd_beam', 0),
                'M_Rd_column': result.get('M_Rd_column', 0),
                'N_Rd_column': result.get('N_Rd_column', 0)
            })

            # Verifica armature minime
            verif = self._calculator.verify_minimum_reinforcement(input_data.reinforcement)
            if not verif['all_ok']:
                for msg in verif['messages']:
                    output.add_warning(msg)

        except Exception as e:
            output.add_error(f"Errore calcolo capacità C.A.: {str(e)}")
            logger.error(f"ConcreteFramePlugin.calculate_capacity error: {e}")

        return output

    def get_default_config(self) -> Dict:
        return {
            'materiale': 'ca',
            'classe_cls': 'C25/30',
            'tipo_acciaio': 'B450C',
            'copriferro': 30,
            'tipo': 'Telaio in C.A.',
            'architrave': {
                'base': 30,
                'altezza': 40,
                'armatura_sup': '3φ16',
                'armatura_inf': '3φ16',
                'staffe': 'φ8/20'
            },
            'piedritti': {
                'base': 30,
                'spessore': 30,
                'armatura': '4φ16'
            }
        }

    def calculate_crack_width(self, input_data: CalculationInput,
                               M_Ed: float) -> Optional[float]:
        """
        Calcola apertura fessure (specifico per C.A.).

        Args:
            input_data: Input standard
            M_Ed: Momento in esercizio [kNm]

        Returns:
            Apertura fessure w_k [mm]
        """
        try:
            return self._calculator.calculate_crack_width(
                M_Ed,
                input_data.reinforcement
            )
        except Exception as e:
            logger.error(f"Errore calcolo fessure: {e}")
            return None


# Funzione per inizializzare tutti i plugin
def initialize_plugins():
    """
    Inizializza e registra tutti i plugin disponibili.

    Chiamato automaticamente quando il modulo viene importato.
    """
    # I plugin sono già registrati tramite decoratore @register
    # Questa funzione può essere usata per registrazioni manuali aggiuntive

    from .reinforcement_registry import get_registry
    registry = get_registry()

    logger.info("Plugin rinforzi inizializzati:")
    for calc in registry.get_all_calculators():
        cap = calc.get_capability()
        logger.info(f"  - {cap.name} v{cap.version}")

    return registry


# Auto-inizializzazione all'import
# I plugin vengono registrati automaticamente grazie al decoratore @register
