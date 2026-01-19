"""
Gestione caricamento/salvataggio progetti
Arch. Michelangelo Bartolotta
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class ProjectManager:
    """Gestore progetti - Salvataggio e caricamento file .cerch"""

    VERSION = "1.0"
    FILE_EXTENSION = ".cerch"

    def __init__(self):
        self.current_file = None
        self.last_error = None

    def save_project(self, project_data: Dict, filepath: str) -> bool:
        """
        Salva progetto in formato .cerch (JSON)

        Args:
            project_data: Dizionario con tutti i dati del progetto
            filepath: Percorso file di destinazione

        Returns:
            bool: True se salvato con successo
        """
        try:
            # Assicura estensione corretta
            if not filepath.endswith(self.FILE_EXTENSION):
                filepath += self.FILE_EXTENSION

            # Prepara dati per serializzazione
            save_data = self._prepare_for_save(project_data)

            # Aggiungi metadata
            save_data['_metadata'] = {
                'version': self.VERSION,
                'created': datetime.now().isoformat(),
                'software': 'Calcolatore Cerchiature NTC 2018',
                'author': 'Arch. Michelangelo Bartolotta'
            }

            # Salva file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)

            self.current_file = filepath
            self.last_error = None
            return True

        except Exception as e:
            self.last_error = f"Errore salvataggio: {str(e)}"
            print(self.last_error)
            return False

    def load_project(self, filepath: str) -> Optional[Dict]:
        """
        Carica progetto da file .cerch

        Args:
            filepath: Percorso file da caricare

        Returns:
            Dict con dati progetto o None se errore
        """
        try:
            if not os.path.exists(filepath):
                self.last_error = f"File non trovato: {filepath}"
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Verifica versione e compatibilità
            metadata = data.get('_metadata', {})
            file_version = metadata.get('version', '1.0')

            # Rimuovi metadata dai dati progetto
            if '_metadata' in data:
                del data['_metadata']

            # Converti dati se necessario (per compatibilità versioni future)
            project_data = self._convert_if_needed(data, file_version)

            self.current_file = filepath
            self.last_error = None
            return project_data

        except json.JSONDecodeError as e:
            self.last_error = f"Errore formato file: {str(e)}"
            print(self.last_error)
            return None
        except Exception as e:
            self.last_error = f"Errore caricamento: {str(e)}"
            print(self.last_error)
            return None

    def _prepare_for_save(self, data: Dict) -> Dict:
        """Prepara dati per serializzazione JSON"""
        result = {}

        for key, value in data.items():
            if value is None:
                result[key] = None
            elif isinstance(value, (str, int, float, bool)):
                result[key] = value
            elif isinstance(value, (list, tuple)):
                result[key] = [self._prepare_value(item) for item in value]
            elif isinstance(value, dict):
                result[key] = self._prepare_for_save(value)
            elif hasattr(value, '__dict__'):
                # Oggetto con attributi - converti in dict
                result[key] = self._prepare_for_save(value.__dict__)
            else:
                # Fallback: converti a stringa
                result[key] = str(value)

        return result

    def _prepare_value(self, value: Any) -> Any:
        """Prepara singolo valore per serializzazione"""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, dict):
            return self._prepare_for_save(value)
        elif isinstance(value, (list, tuple)):
            return [self._prepare_value(item) for item in value]
        elif hasattr(value, '__dict__'):
            return self._prepare_for_save(value.__dict__)
        else:
            return str(value)

    def _convert_if_needed(self, data: Dict, version: str) -> Dict:
        """Converte dati da versioni precedenti se necessario"""
        # Per ora non serve conversione, ma struttura pronta per futuro
        if version == self.VERSION:
            return data

        # Qui aggiungere logica di migrazione per versioni future
        return data

    def get_recent_projects(self, max_count: int = 10) -> list:
        """Restituisce lista progetti recenti (da implementare con registro)"""
        # Per ora restituisce lista vuota
        # In futuro: leggere da file di configurazione
        return []

    def export_to_json(self, project_data: Dict, filepath: str) -> bool:
        """Esporta progetto in formato JSON standard"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            self.last_error = f"Errore esportazione: {str(e)}"
            return False

    def get_project_info(self, filepath: str) -> Optional[Dict]:
        """Restituisce informazioni sul progetto senza caricarlo completamente"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            info = {
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'metadata': data.get('_metadata', {}),
                'project_name': data.get('project_info', {}).get('name', 'Senza nome'),
                'modified': os.path.getmtime(filepath)
            }
            return info

        except Exception:
            return None
