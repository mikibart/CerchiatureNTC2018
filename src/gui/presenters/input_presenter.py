"""
InputPresenter - Logica Input Dati Progetto
===========================================

Presenter per la gestione dei dati di input:
- Geometria parete
- Parametri meccanici muratura
- Aperture esistenti
- Carichi e vincoli

Separa la logica di business dalla vista (InputModule).

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import os

from .base_presenter import BasePresenter, ValidationResult
from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


class InputPresenter(BasePresenter):
    """
    Presenter per il modulo di input dati.

    Gestisce:
    - Validazione geometria parete
    - Gestione materiali muratura
    - Calcolo valori di progetto (fcm_d, tau0_d)
    - Validazione posizione aperture
    - Gestione carichi e vincoli

    Eventi emessi:
    - 'wall_updated': Geometria parete modificata
    - 'masonry_updated': Parametri muratura modificati
    - 'openings_updated': Lista aperture modificata
    - 'design_values_calculated': Valori di progetto calcolati
    - 'validation_error': Errore di validazione
    """

    # Limiti geometrici
    WALL_LENGTH_MIN = 50    # cm
    WALL_LENGTH_MAX = 2000  # cm
    WALL_HEIGHT_MIN = 100   # cm
    WALL_HEIGHT_MAX = 1000  # cm
    WALL_THICKNESS_MIN = 15 # cm
    WALL_THICKNESS_MAX = 100 # cm

    def __init__(self, materials_db_path: str = None):
        super().__init__()

        # Database materiali
        self.materials_db_path = materials_db_path or self._find_materials_db()
        self.materials_db = self._load_materials_db()

        # Dati default
        self._init_default_data()

    def _find_materials_db(self) -> str:
        """Trova il percorso del database materiali"""
        paths = [
            'data/materials.json',
            'data/masonry_materials.json',
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'materials.json')
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return 'data/materials.json'

    def _load_materials_db(self) -> Dict[str, Any]:
        """Carica il database dei materiali."""
        try:
            if os.path.exists(self.materials_db_path):
                with open(self.materials_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Errore caricamento materiali: {e}")

        # Default materials se file non trovato
        return {
            'masonry_types': {
                'pietrame_disordinata': {'name': 'Pietra disordinata', 'fcm': 1.0, 'tau0': 0.020, 'E': 690, 'G': 230},
                'pietrame_buona': {'name': 'Pietra a filari', 'fcm': 2.0, 'tau0': 0.035, 'E': 1230, 'G': 410},
                'mattoni_pieni': {'name': 'Muratura in mattoni pieni', 'fcm': 2.4, 'tau0': 0.060, 'E': 1500, 'G': 500},
                'mattoni_semipieni': {'name': 'Muratura in mattoni semipieni', 'fcm': 5.0, 'tau0': 0.240, 'E': 3500, 'G': 875},
                'blocchi_cls': {'name': 'Muratura in blocchi di cls', 'fcm': 3.0, 'tau0': 0.180, 'E': 2400, 'G': 600},
                'blocchi_tufo': {'name': 'Blocchi di tufo', 'fcm': 1.4, 'tau0': 0.028, 'E': 900, 'G': 300},
            }
        }

    def _init_default_data(self):
        """Inizializza i dati con valori default"""
        self._data = {
            # Progetto
            'project_name': 'Nuovo Progetto',
            'project_location': '',

            # Parete
            'wall_length': 300,     # cm
            'wall_height': 270,     # cm
            'wall_thickness': 30,   # cm

            # Muratura
            'masonry_type': 'Muratura in mattoni pieni',
            'fcm': 2.4,             # MPa
            'tau0': 0.060,          # MPa
            'E': 1500,              # MPa
            'knowledge_level': 'LC1',
            'manual_params': False,

            # Valori di progetto (calcolati)
            'fcm_d': 0.0,
            'tau0_d': 0.0,
            'FC': 1.35,

            # Carichi
            'vertical_load': 0,     # kN
            'eccentricity': 0,      # cm

            # Vincoli
            'constraint_bottom': 'Incastro',
            'constraint_top': 'Incastro (Grinter)',

            # Aperture esistenti
            'openings': []
        }

        # Calcola valori di progetto iniziali
        self._calculate_design_values()

    # =========================================================================
    # WALL GEOMETRY
    # =========================================================================

    def set_wall_dimensions(self, length: float, height: float, thickness: float) -> ValidationResult:
        """
        Imposta le dimensioni della parete.

        Args:
            length: Lunghezza in cm
            height: Altezza in cm
            thickness: Spessore in cm

        Returns:
            ValidationResult con esito validazione
        """
        result = ValidationResult()

        # Validazione
        if length < self.WALL_LENGTH_MIN or length > self.WALL_LENGTH_MAX:
            result.add_error(f"Lunghezza deve essere tra {self.WALL_LENGTH_MIN} e {self.WALL_LENGTH_MAX} cm")

        if height < self.WALL_HEIGHT_MIN or height > self.WALL_HEIGHT_MAX:
            result.add_error(f"Altezza deve essere tra {self.WALL_HEIGHT_MIN} e {self.WALL_HEIGHT_MAX} cm")

        if thickness < self.WALL_THICKNESS_MIN or thickness > self.WALL_THICKNESS_MAX:
            result.add_error(f"Spessore deve essere tra {self.WALL_THICKNESS_MIN} e {self.WALL_THICKNESS_MAX} cm")

        # Warning per snellezza
        if result.is_valid:
            slenderness = height / thickness
            if slenderness > NTC2018.Muratura.SNELLEZZA_MAX:
                result.add_warning(f"Snellezza h/t = {slenderness:.1f} > {NTC2018.Muratura.SNELLEZZA_MAX}")

        # Aggiorna dati se valido
        if result.is_valid:
            self.set_data('wall_length', length)
            self.set_data('wall_height', height)
            self.set_data('wall_thickness', thickness)
            self.emit('wall_updated', self.get_wall_data())

        return result

    def get_wall_data(self) -> Dict[str, Any]:
        """Restituisce i dati della parete."""
        return {
            'length': self.get_data('wall_length'),
            'height': self.get_data('wall_height'),
            'thickness': self.get_data('wall_thickness')
        }

    # =========================================================================
    # MASONRY PROPERTIES
    # =========================================================================

    def get_available_materials(self) -> List[str]:
        """Restituisce la lista dei materiali disponibili"""
        return list(self.materials_db.get('masonry_types', {}).keys())

    def set_masonry_type(self, masonry_type: str) -> bool:
        """
        Imposta il tipo di muratura e carica i parametri.

        Args:
            masonry_type: Nome del tipo di muratura

        Returns:
            True se impostato correttamente
        """
        materials = self.materials_db.get('masonry_types', {})

        if masonry_type not in materials:
            logger.warning(f"Tipo muratura non trovato: {masonry_type}")
            return False

        props = materials[masonry_type]

        self.set_data('masonry_type', masonry_type)
        self.set_data('fcm', props.get('fcm', 2.0))
        self.set_data('tau0', props.get('tau0', 0.074))
        self.set_data('E', props.get('E', 1410))

        # Ricalcola valori di progetto
        self._calculate_design_values()

        self.emit('masonry_updated', self.get_masonry_data())
        return True

    def set_masonry_params(self, fcm: float, tau0: float, E: float = None) -> ValidationResult:
        """
        Imposta i parametri meccanici della muratura manualmente.

        Args:
            fcm: Resistenza a compressione [MPa]
            tau0: Resistenza a taglio [MPa]
            E: Modulo elastico [MPa] (opzionale)
        """
        result = ValidationResult()

        # Validazione
        if fcm <= 0:
            result.add_error("fcm deve essere > 0")
        if fcm > 20:
            result.add_warning("fcm > 20 MPa è insolito per muratura esistente")

        if tau0 <= 0:
            result.add_error("tau0 deve essere > 0")
        if tau0 > 1:
            result.add_warning("tau0 > 1 MPa è insolito per muratura esistente")

        if E is not None and E <= 0:
            result.add_error("E deve essere > 0")

        if result.is_valid:
            self.set_data('fcm', fcm)
            self.set_data('tau0', tau0)
            if E is not None:
                self.set_data('E', E)
            self.set_data('manual_params', True)

            self._calculate_design_values()
            self.emit('masonry_updated', self.get_masonry_data())

        return result

    def set_knowledge_level(self, level: str):
        """
        Imposta il livello di conoscenza e ricalcola FC.

        Args:
            level: 'LC1', 'LC2', o 'LC3'
        """
        if level not in ['LC1', 'LC2', 'LC3']:
            level = 'LC1'

        self.set_data('knowledge_level', level)
        self._calculate_design_values()
        self.emit('design_values_calculated', self.get_design_values())

    def _calculate_design_values(self):
        """Calcola i valori di progetto (fcm_d, tau0_d)"""
        kl = self.get_data('knowledge_level', 'LC1')
        FC = NTC2018.FC.get_fc(kl)

        fcm = self.get_data('fcm', 2.0)
        tau0 = self.get_data('tau0', 0.074)

        self.set_data('FC', FC, emit_change=False)
        self.set_data('fcm_d', fcm / FC, emit_change=False)
        self.set_data('tau0_d', tau0 / FC, emit_change=False)

    def get_masonry_data(self) -> Dict[str, Any]:
        """Restituisce i dati della muratura."""
        return {
            'type': self.get_data('masonry_type'),
            'fcm': self.get_data('fcm'),
            'tau0': self.get_data('tau0'),
            'E': self.get_data('E'),
            'knowledge_level': self.get_data('knowledge_level')
        }

    def get_design_values(self) -> Dict[str, Any]:
        """Restituisce i valori di progetto."""
        return {
            'FC': self.get_data('FC'),
            'fcm_d': self.get_data('fcm_d'),
            'tau0_d': self.get_data('tau0_d')
        }

    # =========================================================================
    # OPENINGS MANAGEMENT
    # =========================================================================

    def validate_opening(self, opening: Dict[str, Any], exclude_index: int = -1) -> ValidationResult:
        """
        Valida un'apertura (posizione, dimensioni, sovrapposizioni).

        Args:
            opening (Dict[str, Any]): Dict con x, y, width, height.
            exclude_index (int): Indice apertura da escludere (per modifica).

        Returns:
            ValidationResult: Risultato della validazione.
        """
        result = ValidationResult()

        x = opening.get('x', 0)
        y = opening.get('y', 0)
        w = opening.get('width', 0)
        h = opening.get('height', 0)

        wall_L = self.get_data('wall_length')
        wall_H = self.get_data('wall_height')

        # Validazione dimensioni
        if w <= 0 or h <= 0:
            result.add_error("Dimensioni apertura non valide")
            return result

        # Validazione posizione
        if x < 0:
            result.add_error("Posizione X non può essere negativa")
        if y < 0:
            result.add_error("Posizione Y non può essere negativa")

        # Verifica limiti parete
        if x + w > wall_L:
            result.add_error(f"Apertura eccede la lunghezza parete (max {wall_L} cm)")
        if y + h > wall_H:
            result.add_error(f"Apertura eccede l'altezza parete (max {wall_H} cm)")

        # Verifica sovrapposizioni
        openings = self.get_data('openings', [])
        for i, existing in enumerate(openings):
            if i == exclude_index:
                continue

            if self._openings_overlap(opening, existing):
                result.add_error(f"Apertura si sovrappone all'apertura #{i+1}")
                break

        # Warning per maschi murari stretti
        if result.is_valid:
            maschi_warnings = self._check_maschi_width(opening, exclude_index)
            for warning in maschi_warnings:
                result.add_warning(warning)

        return result

    def _openings_overlap(self, op1: Dict[str, Any], op2: Dict[str, Any], margin: float = 1) -> bool:
        """Verifica se due aperture si sovrappongono."""
        x1, y1, w1, h1 = op1['x'], op1['y'], op1['width'], op1['height']
        x2, y2, w2, h2 = op2['x'], op2['y'], op2['width'], op2['height']

        return not (x1 + w1 + margin <= x2 or
                   x2 + w2 + margin <= x1 or
                   y1 + h1 + margin <= y2 or
                   y2 + h2 + margin <= y1)

    def _check_maschi_width(self, new_opening: Dict[str, Any], exclude_index: int = -1) -> List[str]:
        """Verifica larghezza maschi murari risultanti."""
        warnings = []
        min_width = NTC2018.InterventiLocali.MASCHIO_MIN_WIDTH * 100  # m -> cm

        wall_L = self.get_data('wall_length')
        openings = self.get_data('openings', []).copy()

        # Aggiungi/sostituisci nuova apertura
        if exclude_index >= 0 and exclude_index < len(openings):
            openings[exclude_index] = new_opening
        else:
            openings.append(new_opening)

        # Ordina per posizione X
        openings.sort(key=lambda o: o['x'])

        # Verifica maschi
        prev_end = 0
        for i, op in enumerate(openings):
            maschio_width = op['x'] - prev_end
            if 0 < maschio_width < min_width:
                warnings.append(f"Maschio sinistro apertura #{i+1} = {maschio_width:.0f} cm < {min_width:.0f} cm")
            prev_end = op['x'] + op['width']

        # Maschio destro
        last_maschio = wall_L - prev_end
        if 0 < last_maschio < min_width:
            warnings.append(f"Maschio destro = {last_maschio:.0f} cm < {min_width:.0f} cm")

        return warnings

    def add_opening(self, opening: Dict[str, Any]) -> Tuple[bool, ValidationResult]:
        """
        Aggiunge un'apertura esistente.

        Args:
            opening (Dict[str, Any]): Dict con x, y, width, height, [existing=True].

        Returns:
            Tuple[bool, ValidationResult]: (successo, risultato validazione).
        """
        # Imposta come esistente
        opening['existing'] = opening.get('existing', True)

        validation = self.validate_opening(opening)
        if not validation.is_valid:
            return False, validation

        openings = self.get_data('openings', [])
        openings.append(opening)
        self.set_data('openings', openings)

        self.emit('openings_updated', openings)
        return True, validation

    def update_opening(self, index: int, opening: Dict[str, Any]) -> Tuple[bool, ValidationResult]:
        """Aggiorna un'apertura esistente."""
        openings = self.get_data('openings', [])
        if index < 0 or index >= len(openings):
            result = ValidationResult()
            result.add_error("Indice apertura non valido")
            return False, result

        validation = self.validate_opening(opening, exclude_index=index)
        if not validation.is_valid:
            return False, validation

        opening['existing'] = openings[index].get('existing', True)
        openings[index] = opening
        self.set_data('openings', openings)

        self.emit('openings_updated', openings)
        return True, validation

    def remove_opening(self, index: int) -> bool:
        """Rimuove un'apertura"""
        openings = self.get_data('openings', [])
        if 0 <= index < len(openings):
            openings.pop(index)
            self.set_data('openings', openings)
            self.emit('openings_updated', openings)
            return True
        return False

    def get_openings(self) -> List[Dict[str, Any]]:
        """Restituisce la lista delle aperture."""
        return self.get_data('openings', []).copy()

    # =========================================================================
    # LOADS AND CONSTRAINTS
    # =========================================================================

    def set_loads(self, vertical: float, eccentricity: float) -> ValidationResult:
        """Imposta i carichi"""
        result = ValidationResult()

        if vertical < 0:
            result.add_error("Carico verticale non può essere negativo")

        thickness = self.get_data('wall_thickness', 30)
        max_ecc = thickness / 2

        if abs(eccentricity) > max_ecc:
            result.add_error(f"Eccentricità non può superare t/2 = {max_ecc:.1f} cm")
        elif abs(eccentricity) > thickness / 6:
            result.add_warning(f"Eccentricità > t/6 = {thickness/6:.1f} cm (parzializzazione)")

        if result.is_valid:
            self.set_data('vertical_load', vertical)
            self.set_data('eccentricity', eccentricity)

        return result

    def set_constraints(self, bottom: str, top: str):
        """Imposta i vincoli"""
        self.set_data('constraint_bottom', bottom)
        self.set_data('constraint_top', top)

    def get_loads_data(self) -> Dict[str, Any]:
        """Restituisce i dati dei carichi."""
        return {
            'vertical': self.get_data('vertical_load'),
            'eccentricity': self.get_data('eccentricity')
        }

    def get_constraints_data(self) -> Dict[str, Any]:
        """Restituisce i dati dei vincoli."""
        return {
            'bottom': self.get_data('constraint_bottom'),
            'top': self.get_data('constraint_top')
        }

    # =========================================================================
    # VALIDATION & DATA COLLECTION
    # =========================================================================

    def _validate_specific(self, data: Dict[str, Any], result: ValidationResult):
        """Implementa validazione specifica per InputPresenter."""
        # Parete
        if data.get('wall_length', 0) <= 0:
            result.add_error("Lunghezza parete non valida")
        if data.get('wall_height', 0) <= 0:
            result.add_error("Altezza parete non valida")
        if data.get('wall_thickness', 0) <= 0:
            result.add_error("Spessore parete non valido")

        # Muratura
        if data.get('fcm', 0) <= 0:
            result.add_error("fcm deve essere > 0")
        if data.get('tau0', 0) <= 0:
            result.add_error("tau0 deve essere > 0")

    def collect_data(self) -> Dict[str, Any]:
        """
        Raccoglie tutti i dati per il salvataggio/calcolo.

        Returns:
            Dict[str, Any]: Dict strutturato con tutti i dati di input.
        """
        return {
            'project': {
                'name': self.get_data('project_name'),
                'location': self.get_data('project_location')
            },
            'wall': self.get_wall_data(),
            'masonry': self.get_masonry_data(),
            'loads': self.get_loads_data(),
            'constraints': self.get_constraints_data(),
            'FC': self.get_data('FC'),
            'openings': self.get_openings()
        }

    def load_data(self, data: Dict[str, Any]):
        """Carica dati da una sorgente esterna."""
        # Progetto
        project = data.get('project', {})
        self.set_data('project_name', project.get('name', 'Nuovo Progetto'))
        self.set_data('project_location', project.get('location', ''))

        # Parete
        wall = data.get('wall', {})
        self.set_data('wall_length', wall.get('length', 300))
        self.set_data('wall_height', wall.get('height', 270))
        self.set_data('wall_thickness', wall.get('thickness', 30))

        # Muratura
        masonry = data.get('masonry', {})
        self.set_data('masonry_type', masonry.get('type', 'Muratura in mattoni pieni'))
        self.set_data('fcm', masonry.get('fcm', 2.4))
        self.set_data('tau0', masonry.get('tau0', 0.074))
        self.set_data('E', masonry.get('E', 1410))
        self.set_data('knowledge_level', masonry.get('knowledge_level', 'LC1'))

        # Carichi
        loads = data.get('loads', {})
        self.set_data('vertical_load', loads.get('vertical', 0))
        self.set_data('eccentricity', loads.get('eccentricity', 0))

        # Vincoli
        constraints = data.get('constraints', {})
        self.set_data('constraint_bottom', constraints.get('bottom', 'Incastro'))
        self.set_data('constraint_top', constraints.get('top', 'Incastro (Grinter)'))

        # FC
        if 'FC' in data:
            self.set_data('FC', data['FC'])

        # Aperture
        self.set_data('openings', data.get('openings', []))

        # Ricalcola valori di progetto
        self._calculate_design_values()

        self.mark_clean()
        self.emit('data_loaded')
