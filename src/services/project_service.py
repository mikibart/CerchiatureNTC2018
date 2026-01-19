"""
ProjectService - Gestione Ciclo Vita Progetto
==============================================

Service per la gestione completa del progetto:
- Creazione nuovo progetto
- Salvataggio/caricamento file .cerch
- Validazione dati progetto
- Gestione stato modificato/non salvato

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from pathlib import Path
import json
import logging
from datetime import datetime

from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Informazioni base progetto"""
    name: str = "Nuovo Progetto"
    description: str = ""
    author: str = ""
    created: str = ""
    modified: str = ""
    version: str = "1.0"
    file_path: Optional[str] = None


@dataclass
class ProjectState:
    """Stato corrente del progetto"""
    is_modified: bool = False
    is_new: bool = True
    last_saved: Optional[str] = None
    last_calculated: Optional[str] = None


class ProjectService:
    """
    Servizio per la gestione del ciclo vita del progetto.

    Responsabilità:
    - Creazione nuovi progetti con valori default
    - Salvataggio/caricamento file .cerch (JSON)
    - Tracciamento modifiche
    - Validazione struttura dati

    Esempio:
        service = ProjectService()

        # Nuovo progetto
        project = service.new_project()

        # Modifica e salva
        project['wall']['length'] = 400
        service.save_project(project, 'progetto.cerch')

        # Carica esistente
        loaded = service.load_project('progetto.cerch')
    """

    VERSION = "1.0.0"
    FILE_EXTENSION = ".cerch"
    FILE_FORMAT_VERSION = "2.0"

    def __init__(self):
        self.state = ProjectState()
        self._change_callbacks: List[Callable] = []

        logger.info(f"ProjectService inizializzato - v{self.VERSION}")

    def new_project(self, name: str = "Nuovo Progetto") -> Dict:
        """
        Crea un nuovo progetto con valori di default.

        Returns:
            Dict con struttura progetto completa
        """
        now = datetime.now().isoformat()

        project = {
            # Metadati
            'info': {
                'name': name,
                'description': '',
                'author': '',
                'created': now,
                'modified': now,
                'version': self.FILE_FORMAT_VERSION
            },

            # Geometria parete
            'wall': {
                'length': 300,      # cm
                'height': 270,      # cm
                'thickness': 30     # cm
            },

            # Parametri muratura
            'masonry': {
                'fcm': 2.4,         # MPa
                'tau0': 0.074,      # MPa
                'E': 1410,          # MPa
                'knowledge_level': 'LC1',
                'type': 'Pietra disordinata'
            },

            # Carichi
            'loads': {
                'vertical': 0,      # kN
                'eccentricity': 0   # cm
            },

            # Vincoli
            'constraints': {
                'bottom': 'Incastro',
                'top': 'Incastro (Grinter)'
            },

            # Fattore di confidenza
            'FC': NTC2018.FC.LC1,

            # Aperture (lista vuota iniziale)
            'openings': [],

            # Risultati calcolo (vuoti inizialmente)
            'results': None
        }

        # Aggiorna stato
        self.state = ProjectState(
            is_modified=False,
            is_new=True,
            last_saved=None
        )

        logger.info(f"Nuovo progetto creato: {name}")
        self._notify_change('new', project)

        return project

    def save_project(self, project: Dict, file_path: str) -> bool:
        """
        Salva il progetto su file.

        Args:
            project: Dict con dati progetto
            file_path: Percorso file di destinazione

        Returns:
            True se salvato con successo
        """
        try:
            path = Path(file_path)

            # Assicura estensione corretta
            if path.suffix.lower() != self.FILE_EXTENSION:
                path = path.with_suffix(self.FILE_EXTENSION)

            # Aggiorna metadati
            if 'info' in project:
                project['info']['modified'] = datetime.now().isoformat()
                project['info']['version'] = self.FILE_FORMAT_VERSION
            else:
                project['info'] = {
                    'modified': datetime.now().isoformat(),
                    'version': self.FILE_FORMAT_VERSION
                }

            # Aggiungi versione formato
            project['_format_version'] = self.FILE_FORMAT_VERSION
            project['_app_version'] = self.VERSION

            # Serializza e salva
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(project, f, indent=2, ensure_ascii=False)

            # Aggiorna stato
            self.state.is_modified = False
            self.state.is_new = False
            self.state.last_saved = datetime.now().isoformat()

            logger.info(f"Progetto salvato: {path}")
            self._notify_change('save', {'path': str(path)})

            return True

        except Exception as e:
            logger.error(f"Errore salvataggio progetto: {e}")
            return False

    def load_project(self, file_path: str) -> Optional[Dict]:
        """
        Carica un progetto da file.

        Args:
            file_path: Percorso file da caricare

        Returns:
            Dict con dati progetto o None se errore
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"File non trovato: {path}")

            with open(path, 'r', encoding='utf-8') as f:
                project = json.load(f)

            # Valida e migra se necessario
            project = self._migrate_project(project)

            # Aggiorna stato
            self.state.is_modified = False
            self.state.is_new = False
            self.state.last_saved = project.get('info', {}).get('modified')

            logger.info(f"Progetto caricato: {path}")
            self._notify_change('load', {'path': str(path)})

            return project

        except json.JSONDecodeError as e:
            logger.error(f"Errore formato JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore caricamento progetto: {e}")
            return None

    def _migrate_project(self, project: Dict) -> Dict:
        """
        Migra progetti da versioni precedenti.

        Gestisce retrocompatibilità con formati vecchi.
        """
        format_version = project.get('_format_version', '1.0')

        if format_version < '2.0':
            logger.info(f"Migrazione progetto da versione {format_version}")

            # Migrazione formato v1.x -> v2.x
            # Aggiungi campi mancanti con default

            if 'constraints' not in project:
                project['constraints'] = {
                    'bottom': 'Incastro',
                    'top': 'Incastro (Grinter)'
                }

            if 'FC' not in project:
                kl = project.get('masonry', {}).get('knowledge_level', 'LC1')
                fc_map = {'LC1': 1.35, 'LC2': 1.20, 'LC3': 1.00}
                project['FC'] = fc_map.get(kl, 1.35)

            # Migra openings_module -> openings
            if 'openings_module' in project and 'openings' not in project:
                project['openings'] = project['openings_module'].get('openings', [])

            # Migra input_module -> wall, masonry
            if 'input_module' in project:
                im = project['input_module']
                if 'wall' in im and 'wall' not in project:
                    project['wall'] = im['wall']
                if 'masonry' in im and 'masonry' not in project:
                    project['masonry'] = im['masonry']

        return project

    def validate_project(self, project: Dict) -> List[str]:
        """
        Valida la struttura del progetto.

        Returns:
            Lista di errori (vuota se valido)
        """
        errors = []

        # Verifica campi obbligatori
        required = ['wall', 'masonry']
        for field in required:
            if field not in project:
                errors.append(f"Campo obbligatorio mancante: {field}")

        # Verifica geometria parete
        wall = project.get('wall', {})
        for dim in ['length', 'height', 'thickness']:
            if dim not in wall:
                errors.append(f"Dimensione parete mancante: {dim}")
            elif wall.get(dim, 0) <= 0:
                errors.append(f"Dimensione parete non valida: {dim}={wall.get(dim)}")

        # Verifica parametri muratura
        masonry = project.get('masonry', {})
        for param in ['fcm', 'tau0']:
            if param not in masonry:
                errors.append(f"Parametro muratura mancante: {param}")
            elif masonry.get(param, 0) <= 0:
                errors.append(f"Parametro muratura non valido: {param}={masonry.get(param)}")

        return errors

    def mark_modified(self, project: Dict = None):
        """Segna il progetto come modificato"""
        self.state.is_modified = True
        self._notify_change('modified', project)

    def is_modified(self) -> bool:
        """Verifica se ci sono modifiche non salvate"""
        return self.state.is_modified

    def on_change(self, callback: Callable):
        """Registra callback per notifiche cambio stato"""
        self._change_callbacks.append(callback)

    def _notify_change(self, event: str, data: any = None):
        """Notifica cambio stato ai listener"""
        for callback in self._change_callbacks:
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"Errore callback cambio stato: {e}")

    def get_project_summary(self, project: Dict) -> Dict:
        """
        Genera un riepilogo del progetto.

        Returns:
            Dict con statistiche e info principali
        """
        wall = project.get('wall', {})
        masonry = project.get('masonry', {})
        openings = project.get('openings', [])

        existing_openings = [o for o in openings if o.get('existing', False)]
        new_openings = [o for o in openings if not o.get('existing', False)]
        reinforced = [o for o in new_openings if o.get('rinforzo')]

        return {
            'name': project.get('info', {}).get('name', 'Senza nome'),
            'wall_dimensions': f"{wall.get('length', 0)/100:.2f} x {wall.get('height', 0)/100:.2f} x {wall.get('thickness', 0)/100:.2f} m",
            'masonry_type': masonry.get('type', 'Non specificato'),
            'fcm': masonry.get('fcm', 0),
            'knowledge_level': masonry.get('knowledge_level', 'LC1'),
            'total_openings': len(openings),
            'existing_openings': len(existing_openings),
            'new_openings': len(new_openings),
            'reinforced_openings': len(reinforced),
            'is_modified': self.state.is_modified,
            'last_calculated': self.state.last_calculated
        }

    def export_to_dict(self, project: Dict, include_results: bool = True) -> Dict:
        """
        Esporta progetto in formato dizionario pulito.

        Args:
            project: Progetto da esportare
            include_results: Se includere i risultati calcolo

        Returns:
            Dict pronto per serializzazione/export
        """
        exported = {
            'info': project.get('info', {}),
            'wall': project.get('wall', {}),
            'masonry': project.get('masonry', {}),
            'loads': project.get('loads', {}),
            'constraints': project.get('constraints', {}),
            'FC': project.get('FC', 1.0),
            'openings': project.get('openings', [])
        }

        if include_results and 'results' in project:
            exported['results'] = project['results']

        return exported
