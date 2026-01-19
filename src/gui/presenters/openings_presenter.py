"""
OpeningsPresenter - Logica Gestione Aperture
=============================================

Presenter per la gestione delle aperture e rinforzi:
- Visualizzazione e selezione aperture
- Configurazione cerchiature
- Statistiche aperture/rinforzi

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from .base_presenter import BasePresenter, ValidationResult
from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class OpeningStats:
    """Statistiche sulle aperture"""
    total_count: int = 0
    existing_count: int = 0
    new_count: int = 0
    reinforced_count: int = 0
    total_area: float = 0.0         # m²
    opening_ratio: float = 0.0      # % di foratura
    maschi_count: int = 0


class OpeningsPresenter(BasePresenter):
    """
    Presenter per il modulo aperture.

    Gestisce:
    - Lista aperture con stato (esistente/nuova)
    - Configurazione rinforzi (cerchiature)
    - Statistiche e riepilogo
    - Validazione configurazioni

    Eventi emessi:
    - 'openings_changed': Lista aperture modificata
    - 'selection_changed': Selezione corrente cambiata
    - 'reinforcement_updated': Rinforzo configurato
    - 'stats_updated': Statistiche aggiornate
    """

    def __init__(self):
        super().__init__()

        # Stato
        self._openings: List[Dict] = []
        self._selected_index: int = -1
        self._wall_data: Dict = {}

    # =========================================================================
    # WALL CONTEXT
    # =========================================================================

    def set_wall_context(self, wall_data: Dict[str, Any]):
        """
        Imposta il contesto parete per validazione aperture.

        Args:
            wall_data (Dict[str, Any]): Dict con length, height, thickness.
        """
        self._wall_data = wall_data
        self.emit('context_updated', wall_data)

    def get_wall_context(self) -> Dict[str, Any]:
        """Restituisce il contesto parete."""
        return self._wall_data.copy()

    # =========================================================================
    # OPENINGS MANAGEMENT
    # =========================================================================

    def set_openings(self, openings: List[Dict[str, Any]]):
        """
        Imposta la lista completa delle aperture.

        Args:
            openings (List[Dict[str, Any]]): Lista di aperture.
        """
        self._openings = [self._normalize_opening(o) for o in openings]
        self._selected_index = 0 if self._openings else -1
        self._update_stats()
        self.emit('openings_changed', self._openings)

    def _normalize_opening(self, opening: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizza i dati di un'apertura."""
        return {
            'x': opening.get('x', 0),
            'y': opening.get('y', 0),
            'width': opening.get('width', 100),
            'height': opening.get('height', 200),
            'type': opening.get('type', 'Rettangolare'),
            'existing': opening.get('existing', False),
            'rinforzo': opening.get('rinforzo', None),
            'id': opening.get('id', None)
        }

    def get_openings(self) -> List[Dict[str, Any]]:
        """Restituisce la lista delle aperture."""
        return [o.copy() for o in self._openings]

    def get_opening(self, index: int) -> Optional[Dict[str, Any]]:
        """Restituisce un'apertura specifica."""
        if 0 <= index < len(self._openings):
            return self._openings[index].copy()
        return None

    def get_opening_count(self) -> int:
        """Restituisce il numero di aperture"""
        return len(self._openings)

    # =========================================================================
    # SELECTION
    # =========================================================================

    def select_opening(self, index: int) -> bool:
        """
        Seleziona un'apertura.

        Args:
            index: Indice apertura (0-based)

        Returns:
            True se selezione valida
        """
        if 0 <= index < len(self._openings):
            self._selected_index = index
            self.emit('selection_changed', index, self._openings[index])
            return True
        return False

    def get_selected_index(self) -> int:
        """Restituisce l'indice dell'apertura selezionata"""
        return self._selected_index

    def get_selected_opening(self) -> Optional[Dict[str, Any]]:
        """Restituisce l'apertura selezionata."""
        return self.get_opening(self._selected_index)

    # =========================================================================
    # OPENING MODIFICATION
    # =========================================================================

    def add_opening(self, opening: Dict[str, Any]) -> Tuple[bool, ValidationResult]:
        """
        Aggiunge una nuova apertura.

        Args:
            opening (Dict[str, Any]): Dati apertura.

        Returns:
            Tuple[bool, ValidationResult]: (successo, risultato validazione).
        """
        normalized = self._normalize_opening(opening)
        validation = self._validate_opening(normalized)

        if validation.is_valid:
            self._openings.append(normalized)
            self._selected_index = len(self._openings) - 1
            self._update_stats()
            self.emit('openings_changed', self._openings)
            self.emit('selection_changed', self._selected_index, normalized)

        return validation.is_valid, validation

    def update_opening_geometry(self, index: int, geometry: Dict[str, Any]) -> Tuple[bool, ValidationResult]:
        """
        Aggiorna la geometria di un'apertura.

        Args:
            index (int): Indice apertura.
            geometry (Dict[str, Any]): Dict con x, y, width, height.

        Returns:
            Tuple[bool, ValidationResult]: (successo, risultato validazione).
        """
        if index < 0 or index >= len(self._openings):
            result = ValidationResult()
            result.add_error("Indice non valido")
            return False, result

        # Prepara apertura aggiornata
        updated = self._openings[index].copy()
        updated.update(geometry)

        validation = self._validate_opening(updated, exclude_index=index)

        if validation.is_valid:
            self._openings[index].update(geometry)
            self._update_stats()
            self.emit('openings_changed', self._openings)

        return validation.is_valid, validation

    def remove_opening(self, index: int) -> bool:
        """
        Rimuove un'apertura.

        Args:
            index: Indice apertura da rimuovere

        Returns:
            True se rimossa
        """
        if 0 <= index < len(self._openings):
            self._openings.pop(index)

            # Aggiorna selezione
            if self._selected_index >= len(self._openings):
                self._selected_index = len(self._openings) - 1

            self._update_stats()
            self.emit('openings_changed', self._openings)
            return True
        return False

    def _validate_opening(self, opening: Dict[str, Any], exclude_index: int = -1) -> ValidationResult:
        """Valida un'apertura."""
        result = ValidationResult()

        x, y = opening.get('x', 0), opening.get('y', 0)
        w, h = opening.get('width', 0), opening.get('height', 0)

        # Dimensioni positive
        if w <= 0 or h <= 0:
            result.add_error("Dimensioni apertura non valide")
            return result

        # Posizione positiva
        if x < 0 or y < 0:
            result.add_error("Posizione apertura non può essere negativa")
            return result

        # Entro limiti parete
        wall_L = self._wall_data.get('length', 300)
        wall_H = self._wall_data.get('height', 270)

        if x + w > wall_L:
            result.add_error(f"Apertura eccede lunghezza parete")
        if y + h > wall_H:
            result.add_error(f"Apertura eccede altezza parete")

        # Sovrapposizioni
        for i, other in enumerate(self._openings):
            if i == exclude_index:
                continue
            if self._check_overlap(opening, other):
                result.add_error(f"Sovrapposizione con apertura {i+1}")
                break

        # Warning maschi stretti
        if result.is_valid:
            self._check_maschi_warnings(opening, exclude_index, result)

        return result

    def _check_overlap(self, op1: Dict[str, Any], op2: Dict[str, Any]) -> bool:
        """Verifica sovrapposizione tra due aperture."""
        margin = 1  # cm minimo
        return not (op1['x'] + op1['width'] + margin <= op2['x'] or
                   op2['x'] + op2['width'] + margin <= op1['x'] or
                   op1['y'] + op1['height'] + margin <= op2['y'] or
                   op2['y'] + op2['height'] + margin <= op1['y'])

    def _check_maschi_warnings(self, opening: Dict[str, Any], exclude_index: int, result: ValidationResult):
        """Aggiunge warning per maschi stretti."""
        min_width = NTC2018.InterventiLocali.MASCHIO_MIN_WIDTH * 100  # m -> cm
        wall_L = self._wall_data.get('length', 300)

        # Lista aperture con la nuova
        test_openings = self._openings.copy()
        if exclude_index >= 0:
            test_openings[exclude_index] = opening
        else:
            test_openings.append(opening)

        test_openings.sort(key=lambda o: o['x'])

        prev_end = 0
        for op in test_openings:
            maschio = op['x'] - prev_end
            if 0 < maschio < min_width:
                result.add_warning(f"Maschio murario = {maschio:.0f} cm < {min_width:.0f} cm min")
            prev_end = op['x'] + op['width']

        # Ultimo maschio
        last = wall_L - prev_end
        if 0 < last < min_width:
            result.add_warning(f"Maschio destro = {last:.0f} cm < {min_width:.0f} cm min")

    # =========================================================================
    # REINFORCEMENT
    # =========================================================================

    def set_reinforcement(self, index: int, rinforzo: Dict[str, Any]) -> ValidationResult:
        """
        Imposta il rinforzo per un'apertura.

        Args:
            index (int): Indice apertura.
            rinforzo (Dict[str, Any]): Configurazione rinforzo.

        Returns:
            ValidationResult: Risultato validazione.
        """
        result = ValidationResult()

        if index < 0 or index >= len(self._openings):
            result.add_error("Indice apertura non valido")
            return result

        opening = self._openings[index]

        # Non può avere rinforzo se è apertura esistente
        if opening.get('existing', False):
            result.add_error("Aperture esistenti non richiedono rinforzo")
            return result

        # Validazione rinforzo
        self._validate_reinforcement(rinforzo, opening, result)

        if result.is_valid:
            self._openings[index]['rinforzo'] = rinforzo
            self._update_stats()
            self.emit('reinforcement_updated', index, rinforzo)
            self.emit('openings_changed', self._openings)

        return result

    def remove_reinforcement(self, index: int) -> bool:
        """Rimuove il rinforzo da un'apertura"""
        if 0 <= index < len(self._openings):
            self._openings[index]['rinforzo'] = None
            self._update_stats()
            self.emit('reinforcement_updated', index, None)
            self.emit('openings_changed', self._openings)
            return True
        return False

    def get_reinforcement(self, index: int) -> Optional[Dict[str, Any]]:
        """Restituisce il rinforzo di un'apertura."""
        if 0 <= index < len(self._openings):
            return self._openings[index].get('rinforzo')
        return None

    def _validate_reinforcement(self, rinforzo: Dict[str, Any], opening: Dict[str, Any], result: ValidationResult):
        """Valida la configurazione del rinforzo."""
        if not rinforzo:
            result.add_error("Configurazione rinforzo vuota")
            return

        tipo = rinforzo.get('tipo', '')
        materiale = rinforzo.get('materiale', '')

        if not tipo:
            result.add_error("Tipo rinforzo non specificato")

        if not materiale:
            result.add_error("Materiale rinforzo non specificato")
        elif materiale not in ['acciaio', 'ca']:
            result.add_error(f"Materiale '{materiale}' non supportato")

        # Verifica profili per acciaio
        if materiale == 'acciaio':
            architrave = rinforzo.get('architrave', {})
            if not architrave.get('profilo'):
                result.add_error("Profilo architrave non specificato")

            piedritti = rinforzo.get('piedritti', {})
            if not piedritti.get('profilo'):
                result.add_error("Profilo piedritti non specificato")

        # Verifica sezioni per c.a.
        if materiale == 'ca':
            sezione = rinforzo.get('sezione', {})
            if sezione.get('base', 0) <= 0 or sezione.get('altezza', 0) <= 0:
                result.add_error("Sezione c.a. non valida")

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def _update_stats(self):
        """Aggiorna le statistiche"""
        stats = self.calculate_stats()
        self.emit('stats_updated', stats)

    def calculate_stats(self) -> OpeningStats:
        """Calcola statistiche sulle aperture"""
        stats = OpeningStats()

        stats.total_count = len(self._openings)
        stats.existing_count = sum(1 for o in self._openings if o.get('existing', False))
        stats.new_count = stats.total_count - stats.existing_count
        stats.reinforced_count = sum(1 for o in self._openings if o.get('rinforzo'))

        # Area totale aperture
        stats.total_area = sum(
            o['width'] * o['height'] / 10000  # cm² -> m²
            for o in self._openings
        )

        # Rapporto foratura
        wall_L = self._wall_data.get('length', 300)
        wall_H = self._wall_data.get('height', 270)
        wall_area = wall_L * wall_H / 10000  # m²

        if wall_area > 0:
            stats.opening_ratio = (stats.total_area / wall_area) * 100

        # Numero maschi
        stats.maschi_count = self._count_maschi()

        return stats

    def _count_maschi(self) -> int:
        """Conta i maschi murari"""
        if not self._openings:
            return 1

        # Maschi = aperture + 1 (semplificato, senza considerare sovrapposizioni verticali)
        return len(self._openings) + 1

    def get_stats(self) -> OpeningStats:
        """Restituisce le statistiche correnti"""
        return self.calculate_stats()

    # =========================================================================
    # DATA COLLECTION
    # =========================================================================

    def _validate_specific(self, data: Dict[str, Any], result: ValidationResult):
        """Validazione specifica per OpeningsPresenter."""
        openings = data.get('openings', [])

        # Verifica che nuove aperture abbiano rinforzo
        for i, op in enumerate(openings):
            if not op.get('existing', False) and not op.get('rinforzo'):
                result.add_warning(f"Apertura {i+1} nuova senza rinforzo configurato")

        # Verifica rapporto foratura
        stats = self.calculate_stats()
        if stats.opening_ratio > NTC2018.InterventiLocali.FORATURA_MAX * 100:
            result.add_error(f"Foratura {stats.opening_ratio:.1f}% > {NTC2018.InterventiLocali.FORATURA_MAX*100:.0f}% max")

    def collect_data(self) -> Dict[str, Any]:
        """Raccoglie i dati per salvataggio/calcolo."""
        return {
            'openings': self.get_openings(),
            'stats': {
                'total': self.calculate_stats().total_count,
                'reinforced': self.calculate_stats().reinforced_count,
                'opening_ratio': self.calculate_stats().opening_ratio
            }
        }

    def load_data(self, data: Dict[str, Any]):
        """Carica dati."""
        openings = data.get('openings', [])
        self.set_openings(openings)

        if 'wall' in data:
            self.set_wall_context(data['wall'])

        self.mark_clean()
