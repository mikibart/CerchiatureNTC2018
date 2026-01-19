"""
frame_result.py - Classe standard per risultati cerchiature
Questo file va creato nella cartella: src/core/engine/
Arch. Michelangelo Bartolotta
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    """
    Risultato standardizzato per calcoli cerchiature.
    Garantisce uniformità di output tra tutti i calcolatori.
    """
    # Risultati principali
    K_frame: float = 0.0      # Rigidezza laterale [kN/m]
    M_max: float = 0.0        # Momento massimo [kNm]
    V_max: float = 0.0        # Taglio massimo [kN]
    N_max: float = 0.0        # Sforzo normale massimo [kN]
    
    # Dati geometrici
    L: float = 0.0            # Luce apertura [m]
    h: float = 0.0            # Altezza apertura [m]
    
    # Identificazione
    tipo: str = ""            # Tipo di rinforzo
    materiale: str = ""       # Materiale (acciaio, ca, etc.)
    
    # Dati aggiuntivi specifici per tipo
    extra_data: Optional[Dict[str, Any]] = None
    
    # Eventuali errori o avvertimenti
    error: Optional[str] = None
    warnings: Optional[list] = None
    
    def __post_init__(self):
        """Inizializzazione post-creazione"""
        if self.extra_data is None:
            self.extra_data = {}
        if self.warnings is None:
            self.warnings = []
            
    def to_dict(self) -> Dict:
        """Converte in dizionario per compatibilità"""
        result = asdict(self)
        
        # Rimuovi campi None per pulizia output
        result = {k: v for k, v in result.items() if v is not None}
        
        # Assicura che extra_data sia sempre presente
        if 'extra_data' not in result:
            result['extra_data'] = {}
            
        return result
        
    def add_warning(self, warning: str):
        """Aggiunge un avvertimento"""
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)
        logger.warning(warning)
        
    def set_error(self, error: str):
        """Imposta un errore"""
        self.error = error
        logger.error(error)
        
    def is_valid(self) -> bool:
        """Verifica se il risultato è valido"""
        return self.error is None and self.K_frame >= 0
        
    def get_summary(self) -> str:
        """Ottiene un riepilogo testuale"""
        summary = [
            f"Cerchiatura {self.materiale.upper()} - {self.tipo}",
            f"Rigidezza: {self.K_frame:.1f} kN/m",
            f"Luce: {self.L:.2f} m, Altezza: {self.h:.2f} m"
        ]
        
        if self.M_max > 0 or self.V_max > 0:
            summary.append(f"Sollecitazioni: M={self.M_max:.1f} kNm, V={self.V_max:.1f} kN")
            
        if self.error:
            summary.append(f"ERRORE: {self.error}")
            
        return "\n".join(summary)