"""
CalcPresenter - Logica Calcolo e Verifica
=========================================

Presenter per il modulo di calcolo:
- Orchestrazione calcoli via CalculationService
- Gestione risultati
- Verifica intervento locale

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
import logging

from .base_presenter import BasePresenter, ValidationResult
from src.services.calculation_service import CalculationService, CalculationResult
from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class CalcState:
    """Stato del calcolo"""
    is_calculating: bool = False
    has_results: bool = False
    last_error: str = ""


class CalcPresenter(BasePresenter):
    """
    Presenter per il modulo di calcolo.

    Interfaccia tra la View (CalcModule) e il Service Layer (CalculationService).

    Gestisce:
    - Esecuzione calcoli in modo controllato
    - Formattazione risultati per visualizzazione
    - Gestione stato calcolo
    - Export risultati

    Eventi emessi:
    - 'calculation_started': Calcolo avviato
    - 'calculation_completed': Calcolo completato con risultati
    - 'calculation_failed': Calcolo fallito con errore
    - 'results_ready': Risultati pronti per visualizzazione
    """

    def __init__(self):
        super().__init__()

        # Service layer
        self._calc_service = CalculationService()

        # Stato
        self._state = CalcState()
        self._results: Optional[CalculationResult] = None
        self._project_data: Dict = {}

    # =========================================================================
    # PROJECT DATA
    # =========================================================================

    def set_project_data(self, project_data: Dict):
        """
        Imposta i dati del progetto per il calcolo.

        Args:
            project_data: Dict con wall, masonry, openings, loads, etc.
        """
        self._project_data = project_data
        self._state.has_results = False
        self._results = None

    def get_project_data(self) -> Dict:
        """Restituisce i dati del progetto corrente"""
        return self._project_data.copy()

    # =========================================================================
    # CALCULATION
    # =========================================================================

    def can_calculate(self) -> Tuple[bool, List[str]]:
        """
        Verifica se è possibile eseguire il calcolo.

        Returns:
            Tuple (can_calculate, list_of_reasons_if_not)
        """
        reasons = []

        if self._state.is_calculating:
            reasons.append("Calcolo già in corso")
            return False, reasons

        # Verifica dati parete
        wall = self._project_data.get('wall', {})
        if not wall.get('length') or not wall.get('height') or not wall.get('thickness'):
            reasons.append("Geometria parete incompleta")

        # Verifica dati muratura
        masonry = self._project_data.get('masonry', {})
        if not masonry.get('fcm') or not masonry.get('tau0'):
            reasons.append("Parametri muratura incompleti")

        # Verifica aperture nuove hanno rinforzo
        openings = self._project_data.get('openings', [])
        for i, op in enumerate(openings):
            if not op.get('existing', False) and not op.get('rinforzo'):
                reasons.append(f"Apertura {i+1} nuova senza rinforzo")

        return len(reasons) == 0, reasons

    def run_calculation(self, on_complete: Callable = None, on_error: Callable = None):
        """
        Esegue il calcolo completo.

        Args:
            on_complete: Callback chiamato al completamento (results)
            on_error: Callback chiamato in caso di errore (error_message)
        """
        # Verifica se può calcolare
        can_calc, reasons = self.can_calculate()
        if not can_calc:
            error_msg = "Impossibile calcolare: " + "; ".join(reasons)
            self._state.last_error = error_msg
            self.emit('calculation_failed', error_msg)
            if on_error:
                on_error(error_msg)
            return

        # Avvia calcolo
        self._state.is_calculating = True
        self._state.last_error = ""
        self.emit('calculation_started')

        try:
            # Esegui calcolo via service
            logger.info("Avvio calcolo progetto...")
            result = self._calc_service.calculate(self._project_data)

            # Salva risultati
            self._results = result
            self._state.has_results = result.is_valid
            self._state.is_calculating = False

            if result.is_valid:
                self.emit('calculation_completed', result)
                self.emit('results_ready', self.get_formatted_results())
                if on_complete:
                    on_complete(result)
            else:
                error_msg = "; ".join(result.errors)
                self._state.last_error = error_msg
                self.emit('calculation_failed', error_msg)
                if on_error:
                    on_error(error_msg)

        except Exception as e:
            self._state.is_calculating = False
            self._state.last_error = str(e)
            logger.error(f"Errore calcolo: {e}")
            self.emit('calculation_failed', str(e))
            if on_error:
                on_error(str(e))

    def is_calculating(self) -> bool:
        """Verifica se un calcolo è in corso"""
        return self._state.is_calculating

    def has_results(self) -> bool:
        """Verifica se ci sono risultati disponibili"""
        return self._state.has_results

    # =========================================================================
    # RESULTS ACCESS
    # =========================================================================

    def get_results(self) -> Optional[CalculationResult]:
        """Restituisce i risultati grezzi"""
        return self._results

    def get_formatted_results(self) -> Optional[Dict]:
        """
        Restituisce i risultati formattati per visualizzazione.

        Returns:
            Dict con risultati organizzati per la view
        """
        if not self._results:
            return None

        r = self._results

        return {
            'original': {
                'K': r.original.K,
                'K_formatted': f"{r.original.K:.0f} kN/m",
                'V_t1': r.original.V_t1,
                'V_t2': r.original.V_t2,
                'V_t3': r.original.V_t3,
                'V_min': r.original.V_min,
                'V_min_formatted': f"{r.original.V_min:.1f} kN"
            },
            'modified': {
                'K_masonry': r.modified.K,
                'K_frames': r.K_frames,
                'K_total': r.K_total_modified,
                'K_total_formatted': f"{r.K_total_modified:.0f} kN/m",
                'V_masonry': r.modified.V_min,
                'V_frames': r.V_frames,
                'V_total': r.V_total_modified,
                'V_total_formatted': f"{r.V_total_modified:.1f} kN"
            },
            'verification': {
                'is_local': r.verification.is_local,
                'status': "LOCALE" if r.verification.is_local else "NON LOCALE",
                'delta_K': r.verification.stiffness_variation,
                'delta_K_formatted': f"{r.verification.stiffness_variation:+.1f}%",
                'delta_K_ok': r.verification.stiffness_ok,
                'delta_V': r.verification.resistance_variation,
                'delta_V_formatted': f"{r.verification.resistance_variation:+.1f}%",
                'delta_V_ok': r.verification.resistance_ok,
                'message': r.verification.message
            },
            'parameters': {
                'FC': r.FC,
                'gamma_collab': r.gamma_collaborazione
            },
            'frames': r.frame_results,
            'warnings': r.warnings,
            'errors': r.errors
        }

    def get_original_state(self) -> Optional[Dict]:
        """Restituisce lo stato originale"""
        if not self._results:
            return None
        return {
            'K': self._results.original.K,
            'V_t1': self._results.original.V_t1,
            'V_t2': self._results.original.V_t2,
            'V_t3': self._results.original.V_t3,
            'V_min': self._results.original.V_min
        }

    def get_modified_state(self) -> Optional[Dict]:
        """Restituisce lo stato modificato"""
        if not self._results:
            return None
        return {
            'K': self._results.K_total_modified,
            'V_min': self._results.V_total_modified,
            'K_frames': self._results.K_frames,
            'V_frames': self._results.V_frames
        }

    def get_verification_result(self) -> Optional[Dict]:
        """Restituisce il risultato della verifica"""
        if not self._results:
            return None
        return {
            'is_local': self._results.verification.is_local,
            'delta_K': self._results.verification.stiffness_variation,
            'delta_V': self._results.verification.resistance_variation,
            'stiffness_ok': self._results.verification.stiffness_ok,
            'resistance_ok': self._results.verification.resistance_ok,
            'message': self._results.verification.message
        }

    # =========================================================================
    # CHART DATA
    # =========================================================================

    def get_capacity_curve_data(self) -> Optional[Dict]:
        """
        Prepara i dati per le curve di capacità.

        Returns:
            Dict con dati per grafico
        """
        if not self._results:
            return None

        orig = self._results.original
        mod_K = self._results.K_total_modified
        mod_V = self._results.V_total_modified

        return {
            'original': {
                'K': orig.K,
                'V_max': orig.V_min,
                'mechanism': self._determine_mechanism(orig)
            },
            'modified': {
                'K': mod_K,
                'V_max': mod_V,
                'K_frames': self._results.K_frames
            }
        }

    def _determine_mechanism(self, state) -> str:
        """Determina il meccanismo di rottura critico"""
        if state.V_min == state.V_t1:
            return 'shear'
        elif state.V_min == state.V_t3:
            return 'flexure'
        return 'mixed'

    def get_comparison_data(self) -> Optional[Dict]:
        """
        Prepara i dati per confronto stato originale/modificato.

        Returns:
            Dict con dati per tabella comparativa
        """
        if not self._results:
            return None

        orig = self._results.original
        mod_K = self._results.K_total_modified
        mod_V = self._results.V_total_modified

        return {
            'rows': [
                {
                    'param': 'Rigidezza K',
                    'unit': 'kN/m',
                    'original': orig.K,
                    'modified': mod_K,
                    'delta': self._results.verification.stiffness_variation,
                    'limit': '±15%',
                    'ok': self._results.verification.stiffness_ok
                },
                {
                    'param': 'Resistenza V',
                    'unit': 'kN',
                    'original': orig.V_min,
                    'modified': mod_V,
                    'delta': self._results.verification.resistance_variation,
                    'limit': '≥-20%',
                    'ok': self._results.verification.resistance_ok
                }
            ]
        }

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_results(self, format: str = 'dict') -> Optional[Dict]:
        """
        Esporta i risultati nel formato richiesto.

        Args:
            format: 'dict', 'summary', 'detailed'

        Returns:
            Dati esportati
        """
        if not self._results:
            return None

        if format == 'summary':
            return {
                'verifica': self._results.verification.message,
                'K_originale': f"{self._results.original.K:.0f} kN/m",
                'K_modificato': f"{self._results.K_total_modified:.0f} kN/m",
                'V_originale': f"{self._results.original.V_min:.1f} kN",
                'V_modificato': f"{self._results.V_total_modified:.1f} kN",
                'delta_K': f"{self._results.verification.stiffness_variation:+.1f}%",
                'delta_V': f"{self._results.verification.resistance_variation:+.1f}%"
            }

        elif format == 'detailed':
            return self.get_formatted_results()

        else:
            return {
                'project_data': self._project_data,
                'results': self.get_formatted_results()
            }

    # =========================================================================
    # BASE PRESENTER IMPLEMENTATION
    # =========================================================================

    def _validate_specific(self, data: Dict, result: ValidationResult):
        """Validazione specifica"""
        can_calc, reasons = self.can_calculate()
        if not can_calc:
            for reason in reasons:
                result.add_error(reason)

    def collect_data(self) -> Dict:
        """Raccoglie i dati"""
        return {
            'project_data': self._project_data,
            'results': self.get_formatted_results() if self._results else None,
            'state': {
                'is_calculating': self._state.is_calculating,
                'has_results': self._state.has_results,
                'last_error': self._state.last_error
            }
        }

    def load_data(self, data: Dict):
        """Carica dati"""
        if 'project_data' in data:
            self._project_data = data['project_data']

        # Non ricarichiamo risultati - devono essere ricalcolati
        self._results = None
        self._state.has_results = False
