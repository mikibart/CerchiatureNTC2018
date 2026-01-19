"""
ReinforcementRegistry - Sistema Plugin per Calcolatori Rinforzo
===============================================================

Registry centrale che gestisce i calcolatori di rinforzo:
- Registrazione automatica dei calcolatori
- Selezione del calcolatore appropriato
- Discovery dei calcolatori disponibili

Pattern: Service Locator + Plugin Registry

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional, Type
import logging

from .reinforcement_interface import (
    ReinforcementCalculator,
    ReinforcementCapability,
    ReinforcementMaterial,
    ReinforcementType,
    CalculationInput,
    CalculationOutput
)

logger = logging.getLogger(__name__)


class ReinforcementRegistry:
    """
    Registry centrale per i calcolatori di rinforzo.

    Gestisce la registrazione e la selezione dei calcolatori.
    Supporta registrazione automatica tramite decoratore.

    Usage:
        # Registrazione
        @ReinforcementRegistry.register
        class MyCalculator(ReinforcementCalculator):
            ...

        # Oppure manuale
        registry = ReinforcementRegistry()
        registry.register_calculator(MyCalculator())

        # Utilizzo
        calc = registry.get_calculator_for(reinforcement_data)
        result = calc.calculate(input_data)
    """

    _instance = None
    _calculators: Dict[str, ReinforcementCalculator] = {}

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._calculators = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_default_calculators()
            self._initialized = True

    def _initialize_default_calculators(self):
        """Inizializza i calcolatori di default"""
        # I calcolatori vengono registrati quando importati
        # o esplicitamente tramite register_calculator
        logger.info("ReinforcementRegistry inizializzato")

    @classmethod
    def register(cls, calculator_class: Type[ReinforcementCalculator]):
        """
        Decoratore per registrare automaticamente un calcolatore.

        Usage:
            @ReinforcementRegistry.register
            class MyCalculator(ReinforcementCalculator):
                ...
        """
        instance = cls()
        calc = calculator_class()
        instance.register_calculator(calc)
        return calculator_class

    def register_calculator(self, calculator: ReinforcementCalculator) -> bool:
        """
        Registra un calcolatore nel registry.

        Args:
            calculator: Istanza del calcolatore

        Returns:
            True se registrato con successo
        """
        try:
            capability = calculator.get_capability()
            key = self._make_key(capability.name)

            if key in self._calculators:
                logger.warning(f"Calcolatore '{capability.name}' già registrato, sovrascrittura")

            self._calculators[key] = calculator
            logger.info(f"Calcolatore registrato: {capability.name} v{capability.version}")
            return True

        except Exception as e:
            logger.error(f"Errore registrazione calcolatore: {e}")
            return False

    def unregister_calculator(self, name: str) -> bool:
        """
        Rimuove un calcolatore dal registry.

        Args:
            name: Nome del calcolatore

        Returns:
            True se rimosso
        """
        key = self._make_key(name)
        if key in self._calculators:
            del self._calculators[key]
            logger.info(f"Calcolatore rimosso: {name}")
            return True
        return False

    def _make_key(self, name: str) -> str:
        """Crea chiave univoca per il registry"""
        return name.lower().replace(' ', '_')

    def get_calculator(self, name: str) -> Optional[ReinforcementCalculator]:
        """
        Ottiene un calcolatore per nome.

        Args:
            name: Nome del calcolatore

        Returns:
            Calcolatore o None se non trovato
        """
        key = self._make_key(name)
        return self._calculators.get(key)

    def get_calculator_for(self, reinforcement_data: Dict) -> Optional[ReinforcementCalculator]:
        """
        Trova il calcolatore appropriato per un tipo di rinforzo.

        Args:
            reinforcement_data: Dati del rinforzo

        Returns:
            Calcolatore appropriato o None
        """
        for calc in self._calculators.values():
            if calc.can_handle(reinforcement_data):
                return calc
        return None

    def get_all_calculators(self) -> List[ReinforcementCalculator]:
        """Restituisce tutti i calcolatori registrati"""
        return list(self._calculators.values())

    def get_available_materials(self) -> List[ReinforcementMaterial]:
        """Restituisce i materiali supportati da tutti i calcolatori"""
        materials = set()
        for calc in self._calculators.values():
            cap = calc.get_capability()
            materials.update(cap.materials)
        return list(materials)

    def get_available_types(self) -> List[ReinforcementType]:
        """Restituisce i tipi di rinforzo supportati"""
        types = set()
        for calc in self._calculators.values():
            cap = calc.get_capability()
            types.update(cap.types)
        return list(types)

    def get_capabilities(self) -> List[ReinforcementCapability]:
        """Restituisce le capacità di tutti i calcolatori"""
        return [calc.get_capability() for calc in self._calculators.values()]

    def calculate(self, reinforcement_data: Dict, opening_data: Dict,
                  wall_data: Optional[Dict] = None,
                  loads_data: Optional[Dict] = None) -> CalculationOutput:
        """
        Esegue il calcolo usando il calcolatore appropriato.

        Args:
            reinforcement_data: Dati rinforzo
            opening_data: Dati apertura
            wall_data: Dati parete (opzionale)
            loads_data: Carichi (opzionale)

        Returns:
            CalculationOutput con risultati
        """
        # Trova calcolatore
        calculator = self.get_calculator_for(reinforcement_data)

        if not calculator:
            output = CalculationOutput(success=False)
            output.add_error(f"Nessun calcolatore per materiale: {reinforcement_data.get('materiale')}")
            return output

        # Prepara input
        input_data = CalculationInput(
            opening=opening_data,
            reinforcement=reinforcement_data,
            wall=wall_data,
            loads=loads_data
        )

        # Calcola
        return calculator.calculate(input_data)

    def get_info(self) -> str:
        """Restituisce informazioni sul registry"""
        lines = ["ReinforcementRegistry Status:"]
        lines.append(f"  Calcolatori registrati: {len(self._calculators)}")
        lines.append("")

        for name, calc in self._calculators.items():
            cap = calc.get_capability()
            materials = ', '.join(m.value for m in cap.materials)
            lines.append(f"  - {cap.name} v{cap.version}")
            lines.append(f"    Materiali: {materials}")
            lines.append(f"    Archi: {'Sì' if cap.supports_arch else 'No'}")

        return '\n'.join(lines)


# Singleton globale
_registry = None


def get_registry() -> ReinforcementRegistry:
    """Ottiene l'istanza singleton del registry"""
    global _registry
    if _registry is None:
        _registry = ReinforcementRegistry()
    return _registry


def register_calculator(calculator: ReinforcementCalculator) -> bool:
    """Funzione helper per registrare un calcolatore"""
    return get_registry().register_calculator(calculator)


def get_calculator_for(reinforcement_data: Dict) -> Optional[ReinforcementCalculator]:
    """Funzione helper per ottenere un calcolatore"""
    return get_registry().get_calculator_for(reinforcement_data)
