"""
Gestione caricamento/salvataggio progetti
Calcolatore Cerchiature NTC 2018
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectManager:
    """Gestore progetti per salvataggio e caricamento file .cerch"""

    VERSION = "1.0"
    FILE_EXTENSION = ".cerch"

    def __init__(self):
        self.current_file: Optional[Path] = None
        self.is_modified: bool = False

    def save_project(self, project_data: Dict, filepath: str) -> bool:
        """
        Salva progetto in formato .cerch (JSON)

        Args:
            project_data: Dizionario con tutti i dati del progetto
            filepath: Percorso del file di destinazione

        Returns:
            True se il salvataggio ha avuto successo, False altrimenti
        """
        try:
            filepath = Path(filepath)

            # Assicura estensione corretta
            if filepath.suffix.lower() != self.FILE_EXTENSION:
                filepath = filepath.with_suffix(self.FILE_EXTENSION)

            # Aggiungi metadati
            save_data = {
                'version': self.VERSION,
                'created': datetime.now().isoformat(),
                'software': 'Calcolatore Cerchiature NTC 2018',
                'author': 'Arch. Michelangelo Bartolotta',
                'project': project_data
            }

            # Salva su file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self.current_file = filepath
            self.is_modified = False

            logger.info(f"Progetto salvato: {filepath}")
            return True

        except Exception as e:
            logger.exception(f"Errore salvataggio progetto: {e}")
            return False

    def load_project(self, filepath: str) -> Optional[Dict]:
        """
        Carica progetto da file .cerch

        Args:
            filepath: Percorso del file da caricare

        Returns:
            Dizionario con i dati del progetto o None in caso di errore
        """
        try:
            filepath = Path(filepath)

            if not filepath.exists():
                logger.error(f"File non trovato: {filepath}")
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Verifica versione
            file_version = data.get('version', '0.0')
            if file_version != self.VERSION:
                logger.warning(f"Versione file ({file_version}) diversa da versione corrente ({self.VERSION})")

            self.current_file = filepath
            self.is_modified = False

            logger.info(f"Progetto caricato: {filepath}")

            # Restituisci i dati del progetto
            return data.get('project', data)

        except json.JSONDecodeError as e:
            logger.error(f"Errore parsing JSON: {e}")
            return None
        except Exception as e:
            logger.exception(f"Errore caricamento progetto: {e}")
            return None

    def get_project_info(self, filepath: str) -> Optional[Dict]:
        """
        Ottiene informazioni su un file progetto senza caricarlo completamente

        Args:
            filepath: Percorso del file

        Returns:
            Dizionario con metadati del progetto
        """
        try:
            filepath = Path(filepath)

            if not filepath.exists():
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                'version': data.get('version', 'N/D'),
                'created': data.get('created', 'N/D'),
                'software': data.get('software', 'N/D'),
                'filename': filepath.name,
                'path': str(filepath)
            }

        except Exception as e:
            logger.error(f"Errore lettura info progetto: {e}")
            return None

    def export_to_json(self, project_data: Dict, filepath: str) -> bool:
        """
        Esporta progetto in formato JSON standard

        Args:
            project_data: Dati del progetto
            filepath: Percorso di destinazione

        Returns:
            True se l'esportazione ha avuto successo
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Progetto esportato in JSON: {filepath}")
            return True

        except Exception as e:
            logger.exception(f"Errore esportazione JSON: {e}")
            return False

    def mark_modified(self):
        """Marca il progetto come modificato"""
        self.is_modified = True

    def get_current_file(self) -> Optional[Path]:
        """Restituisce il percorso del file corrente"""
        return self.current_file

    def has_unsaved_changes(self) -> bool:
        """Verifica se ci sono modifiche non salvate"""
        return self.is_modified
