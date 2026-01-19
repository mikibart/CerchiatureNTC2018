"""
BasePresenter - Classe Base per Presenter
==========================================

Definisce l'interfaccia comune per tutti i presenter nel pattern MVP.

Pattern MVP:
- Model: Dati e business logic (Service Layer)
- View: Componenti UI (solo visualizzazione)
- Presenter: Mediatore tra View e Model

Arch. Michelangelo Bartolotta
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Risultato di una validazione"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        self.warnings.append(message)


class BasePresenter(ABC):
    """
    Classe base astratta per tutti i Presenter.

    Responsabilità:
    - Gestire la logica di presentazione
    - Validare input utente
    - Coordinare View e Model
    - Emettere eventi per aggiornamenti UI

    Utilizzo:
        class MyPresenter(BasePresenter):
            def validate_data(self, data):
                result = ValidationResult()
                if data['value'] < 0:
                    result.add_error("Valore negativo")
                return result
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._data: Dict[str, Any] = {}
        self._is_dirty = False

    # =========================================================================
    # EVENT SYSTEM
    # =========================================================================

    def on(self, event: str, callback: Callable):
        """
        Registra un listener per un evento.

        Args:
            event: Nome evento (es. 'data_changed', 'validation_error')
            callback: Funzione da chiamare quando l'evento viene emesso
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable = None):
        """
        Rimuove un listener.

        Args:
            event: Nome evento
            callback: Se None, rimuove tutti i listener per l'evento
        """
        if event in self._listeners:
            if callback is None:
                self._listeners[event] = []
            else:
                self._listeners[event] = [cb for cb in self._listeners[event] if cb != callback]

    def emit(self, event: str, *args, **kwargs):
        """
        Emette un evento a tutti i listener registrati.

        Args:
            event: Nome evento
            *args, **kwargs: Argomenti da passare ai listener
        """
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Errore in listener {event}: {e}")

    # =========================================================================
    # DATA MANAGEMENT
    # =========================================================================

    def set_data(self, key: str, value: Any, emit_change: bool = True):
        """
        Imposta un valore nei dati del presenter.

        Args:
            key: Chiave del dato
            value: Valore da impostare
            emit_change: Se True, emette evento 'data_changed'
        """
        old_value = self._data.get(key)
        self._data[key] = value
        self._is_dirty = True

        if emit_change and old_value != value:
            self.emit('data_changed', key, value, old_value)

    def get_data(self, key: str, default: Any = None) -> Any:
        """Restituisce un valore dai dati del presenter."""
        return self._data.get(key, default)

    def get_all_data(self) -> Dict[str, Any]:
        """Restituisce tutti i dati del presenter."""
        return self._data.copy()

    def is_dirty(self) -> bool:
        """Verifica se ci sono modifiche non salvate."""
        return self._is_dirty

    def mark_clean(self):
        """Segna i dati come salvati."""
        self._is_dirty = False

    def reset(self):
        """Resetta tutti i dati ai valori default."""
        self._data = {}
        self._is_dirty = False
        self.emit('reset')

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(self, data: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Valida i dati correnti o quelli forniti.

        Args:
            data (Optional[Dict[str, Any]]): Dati da validare (se None, usa dati interni).

        Returns:
            ValidationResult: Oggetto con esito e messaggi.
        """
        if data is None:
            data = self._data

        result = ValidationResult()

        # Validazione specifica implementata dalle sottoclassi
        self._validate_specific(data, result)

        if not result.is_valid:
            self.emit('validation_error', result.errors)
        elif result.warnings:
            self.emit('validation_warning', result.warnings)

        return result

    @abstractmethod
    def _validate_specific(self, data: Dict[str, Any], result: ValidationResult):
        """
        Implementa la validazione specifica per questo presenter.

        Da implementare nelle sottoclassi.

        Args:
            data (Dict[str, Any]): Dati da validare.
            result (ValidationResult): Oggetto da popolare con errori/warning.
        """
        pass

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def initialize(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Inizializza il presenter con dati opzionali.

        Args:
            initial_data (Optional[Dict[str, Any]]): Dati iniziali.
        """
        if initial_data:
            for key, value in initial_data.items():
                self.set_data(key, value, emit_change=False)
        self._is_dirty = False
        self.emit('initialized')

    def dispose(self):
        """Libera risorse e rimuove tutti i listener."""
        self._listeners.clear()
        self._data.clear()
        logger.debug(f"{self.__class__.__name__} disposed")

    # =========================================================================
    # ABSTRACT METHODS - Da implementare
    # =========================================================================

    @abstractmethod
    def collect_data(self) -> Dict[str, Any]:
        """
        Raccoglie e restituisce tutti i dati per il salvataggio.

        Da implementare nelle sottoclassi.

        Returns:
            Dict[str, Any]: Dizionario con tutti i dati da salvare.
        """
        pass

    @abstractmethod
    def load_data(self, data: Dict[str, Any]):
        """
        Carica dati da una sorgente esterna.

        Da implementare nelle sottoclassi.

        Args:
            data (Dict[str, Any]): Dati da caricare.
        """
        pass
