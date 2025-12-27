"""
App Configuration - Gestione configurazione e preferenze utente
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class UserPreferences:
    """Preferenze utente persistenti"""
    # Tema
    theme: str = 'light'

    # Unità di misura
    length_unit: str = 'cm'
    force_unit: str = 'kN'
    stress_unit: str = 'MPa'

    # Precisione decimali
    decimal_places: int = 2

    # Comportamento
    auto_calculate: bool = True
    auto_save: bool = True
    auto_save_interval: int = 300  # secondi (5 minuti)
    confirm_on_exit: bool = True
    show_tooltips: bool = True
    show_grid: bool = True

    # Finestra
    window_width: int = 1400
    window_height: int = 900
    window_maximized: bool = False

    # Percorsi
    last_project_path: str = ''
    last_export_path: str = ''

    # File recenti
    recent_files: list = field(default_factory=list)
    max_recent_files: int = 10

    # Calcolo
    default_knowledge_level: str = 'LC2'
    default_constraint: str = 'Incastro - Incastro (Grinter)'

    # Report
    company_name: str = ''
    company_logo_path: str = ''
    default_author: str = ''


class AppConfig:
    """Gestione configurazione applicazione"""

    CONFIG_VERSION = '1.0'
    CONFIG_FILENAME = 'cerchiature_config.json'

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_path = self.config_dir / self.CONFIG_FILENAME
        self.preferences = UserPreferences()
        self.load()

    def _get_config_dir(self) -> Path:
        """Restituisce la directory di configurazione"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', Path.home()))
        else:  # Linux/Mac
            base = Path.home() / '.config'

        config_dir = base / 'CerchiatureNTC2018'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def load(self):
        """Carica configurazione da file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Aggiorna preferenze con i valori salvati
                for key, value in data.get('preferences', {}).items():
                    if hasattr(self.preferences, key):
                        setattr(self.preferences, key, value)

                logger.info(f"Configurazione caricata da {self.config_path}")
        except Exception as e:
            logger.warning(f"Errore caricamento configurazione: {e}")

    def save(self):
        """Salva configurazione su file"""
        try:
            data = {
                'version': self.CONFIG_VERSION,
                'last_modified': datetime.now().isoformat(),
                'preferences': asdict(self.preferences)
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configurazione salvata in {self.config_path}")
        except Exception as e:
            logger.error(f"Errore salvataggio configurazione: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene un valore di configurazione"""
        return getattr(self.preferences, key, default)

    def set(self, key: str, value: Any):
        """Imposta un valore di configurazione"""
        if hasattr(self.preferences, key):
            setattr(self.preferences, key, value)
            self.save()

    def add_recent_file(self, filepath: str):
        """Aggiunge un file alla lista dei recenti"""
        filepath = str(Path(filepath).resolve())

        # Rimuovi se già presente
        if filepath in self.preferences.recent_files:
            self.preferences.recent_files.remove(filepath)

        # Aggiungi in cima
        self.preferences.recent_files.insert(0, filepath)

        # Limita dimensione lista
        self.preferences.recent_files = self.preferences.recent_files[:self.preferences.max_recent_files]

        self.save()

    def get_recent_files(self) -> list:
        """Restituisce lista file recenti (solo esistenti)"""
        return [f for f in self.preferences.recent_files if Path(f).exists()]

    def clear_recent_files(self):
        """Svuota lista file recenti"""
        self.preferences.recent_files = []
        self.save()

    def get_autosave_dir(self) -> Path:
        """Restituisce directory per autosave"""
        autosave_dir = self.config_dir / 'autosave'
        autosave_dir.mkdir(exist_ok=True)
        return autosave_dir

    def get_backup_dir(self) -> Path:
        """Restituisce directory per backup"""
        backup_dir = self.config_dir / 'backup'
        backup_dir.mkdir(exist_ok=True)
        return backup_dir


class UndoRedoManager:
    """Gestisce cronologia undo/redo"""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.undo_stack = []
        self.redo_stack = []

    def save_state(self, state: dict, description: str = ''):
        """Salva stato corrente per undo"""
        self.undo_stack.append({
            'state': state.copy(),
            'description': description,
            'timestamp': datetime.now().isoformat()
        })

        # Limita dimensione stack
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        # Pulisci redo stack quando si fa una nuova azione
        self.redo_stack.clear()

    def undo(self) -> Optional[dict]:
        """Annulla ultima azione"""
        if not self.can_undo():
            return None

        # Sposta stato corrente in redo
        current = self.undo_stack.pop()
        self.redo_stack.append(current)

        # Restituisci stato precedente
        if self.undo_stack:
            return self.undo_stack[-1]['state']
        return None

    def redo(self) -> Optional[dict]:
        """Ripristina azione annullata"""
        if not self.can_redo():
            return None

        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        return state['state']

    def can_undo(self) -> bool:
        """Verifica se è possibile fare undo"""
        return len(self.undo_stack) > 1

    def can_redo(self) -> bool:
        """Verifica se è possibile fare redo"""
        return len(self.redo_stack) > 0

    def get_undo_description(self) -> str:
        """Restituisce descrizione azione da annullare"""
        if self.can_undo():
            return self.undo_stack[-1].get('description', 'Azione')
        return ''

    def get_redo_description(self) -> str:
        """Restituisce descrizione azione da ripristinare"""
        if self.can_redo():
            return self.redo_stack[-1].get('description', 'Azione')
        return ''

    def clear(self):
        """Pulisce cronologia"""
        self.undo_stack.clear()
        self.redo_stack.clear()


class AutoSaveManager:
    """Gestisce salvataggio automatico"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.last_save_time = None
        self.is_dirty = False

    def mark_dirty(self):
        """Segna il progetto come modificato"""
        self.is_dirty = True

    def mark_clean(self):
        """Segna il progetto come salvato"""
        self.is_dirty = False
        self.last_save_time = datetime.now()

    def should_autosave(self) -> bool:
        """Verifica se è necessario auto-salvare"""
        if not self.config.get('auto_save'):
            return False

        if not self.is_dirty:
            return False

        if self.last_save_time is None:
            return True

        interval = self.config.get('auto_save_interval', 300)
        elapsed = (datetime.now() - self.last_save_time).total_seconds()
        return elapsed >= interval

    def get_autosave_path(self, project_name: str = 'untitled') -> Path:
        """Genera percorso per file autosave"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"autosave_{project_name}_{timestamp}.cerch"
        return self.config.get_autosave_dir() / filename

    def cleanup_old_autosaves(self, max_files: int = 10):
        """Rimuove vecchi file autosave"""
        autosave_dir = self.config.get_autosave_dir()
        files = sorted(autosave_dir.glob('autosave_*.cerch'),
                      key=lambda f: f.stat().st_mtime,
                      reverse=True)

        for old_file in files[max_files:]:
            try:
                old_file.unlink()
                logger.info(f"Rimosso vecchio autosave: {old_file}")
            except Exception as e:
                logger.warning(f"Errore rimozione autosave: {e}")


# Singleton per accesso globale
_app_config = None
_undo_manager = None
_autosave_manager = None


def get_app_config() -> AppConfig:
    """Restituisce istanza singleton configurazione"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config


def get_undo_manager() -> UndoRedoManager:
    """Restituisce istanza singleton undo manager"""
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoRedoManager()
    return _undo_manager


def get_autosave_manager() -> AutoSaveManager:
    """Restituisce istanza singleton autosave manager"""
    global _autosave_manager
    if _autosave_manager is None:
        _autosave_manager = AutoSaveManager(get_app_config())
    return _autosave_manager
