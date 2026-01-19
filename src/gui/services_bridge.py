"""
Services Bridge - Ponte tra GUI e Service Layer
================================================

Questo modulo fa da ponte tra la GUI esistente (CalcModule) e
il nuovo Service Layer. Permette una migrazione graduale.

Utilizzo:
    from src.gui.services_bridge import CalculationBridge

    bridge = CalculationBridge()
    results = bridge.calculate(project_data)

    # I risultati sono nello stesso formato usato dalla GUI
    if results['verification']['is_local']:
        print("Intervento locale!")

Arch. Michelangelo Bartolotta
"""

from typing import Dict, Optional
import logging

from src.services.calculation_service import CalculationService, CalculationResult
from src.services.frame_service import FrameService
from src.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class CalculationBridge:
    """
    Ponte tra GUI e Service Layer.

    Converte i dati dal formato GUI al formato Service
    e viceversa per i risultati.
    """

    def __init__(self):
        self.calc_service = CalculationService()
        self.project_service = ProjectService()

    def calculate(self, project_data: Dict) -> Dict:
        """
        Esegue il calcolo usando il service layer.

        Args:
            project_data: Dati nel formato usato dalla GUI (CalcModule)

        Returns:
            Dict nel formato atteso dalla GUI per visualizzazione
        """
        # Normalizza i dati dal formato GUI
        normalized = self._normalize_project_data(project_data)

        # Esegui calcolo via service
        service_result = self.calc_service.calculate(normalized)

        # Converti risultati al formato GUI
        gui_result = self._convert_to_gui_format(service_result)

        return gui_result

    def _normalize_project_data(self, project_data: Dict) -> Dict:
        """
        Normalizza i dati dal formato GUI al formato service.

        La GUI può avere dati annidati in 'input_module', 'openings_module', etc.
        """
        normalized = {}

        # Wall data
        if 'wall' in project_data:
            normalized['wall'] = project_data['wall']
        elif 'input_module' in project_data:
            im = project_data['input_module']
            normalized['wall'] = im.get('wall', {})

        # Masonry data
        if 'masonry' in project_data:
            normalized['masonry'] = project_data['masonry']
        elif 'input_module' in project_data:
            im = project_data['input_module']
            normalized['masonry'] = im.get('masonry', {})

        # Openings
        if 'openings_module' in project_data:
            normalized['openings'] = project_data['openings_module'].get('openings', [])
        elif 'openings' in project_data:
            normalized['openings'] = project_data['openings']
        else:
            normalized['openings'] = []

        # Loads
        normalized['loads'] = project_data.get('loads', {'vertical': 0, 'eccentricity': 0})

        # Constraints
        normalized['constraints'] = project_data.get('constraints', {
            'bottom': 'Incastro',
            'top': 'Incastro (Grinter)'
        })

        # FC
        if 'FC' in project_data:
            normalized['FC'] = project_data['FC']
        else:
            # Determina da knowledge_level
            masonry = normalized.get('masonry', {})
            kl = masonry.get('knowledge_level', 'LC1')
            fc_map = {'LC1': 1.35, 'LC2': 1.20, 'LC3': 1.00}
            normalized['FC'] = fc_map.get(kl, 1.35)

        return normalized

    def _convert_to_gui_format(self, result: CalculationResult) -> Dict:
        """
        Converte CalculationResult al formato Dict usato dalla GUI.

        Formato atteso dalla GUI:
        {
            'original': {'K': ..., 'V_t1': ..., 'V_t2': ..., 'V_t3': ..., 'V_min': ...},
            'modified': {...},
            'verification': {'is_local': ..., 'stiffness_variation': ..., ...},
            'FC': ...,
            'frame_results': {...}
        }
        """
        return {
            'original': {
                'K': result.original.K,
                'V_t1': result.original.V_t1,
                'V_t2': result.original.V_t2,
                'V_t3': result.original.V_t3,
                'V_min': result.original.V_min
            },
            'modified': {
                'K': result.modified.K,
                'V_t1': result.modified.V_t1,
                'V_t2': result.modified.V_t2,
                'V_t3': result.modified.V_t3,
                'V_min': result.modified.V_min,
                'K_cerchiature': result.K_frames,
                'V_cerchiature': result.V_frames,
                'K_totale': result.K_total_modified,
                'V_totale': result.V_total_modified
            },
            'verification': {
                'is_local': result.verification.is_local,
                'stiffness_variation': result.verification.stiffness_variation,
                'resistance_variation': result.verification.resistance_variation,
                'stiffness_ok': result.verification.stiffness_ok,
                'resistance_ok': result.verification.resistance_ok,
                'message': result.verification.message
            },
            'FC': result.FC,
            'gamma_collaborazione': result.gamma_collaborazione,
            'frame_results': result.frame_results,
            'errors': result.errors,
            'warnings': result.warnings,
            'is_valid': result.is_valid
        }

    def validate_project(self, project_data: Dict) -> Dict:
        """
        Valida i dati del progetto.

        Returns:
            Dict con 'is_valid' e lista 'errors'
        """
        normalized = self._normalize_project_data(project_data)
        errors = self.project_service.validate_project(normalized)

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }


class ProjectBridge:
    """
    Ponte per gestione progetti.
    """

    def __init__(self):
        self.service = ProjectService()

    def new_project(self, name: str = "Nuovo Progetto") -> Dict:
        """Crea nuovo progetto"""
        return self.service.new_project(name)

    def save_project(self, project_data: Dict, file_path: str) -> bool:
        """Salva progetto"""
        return self.service.save_project(project_data, file_path)

    def load_project(self, file_path: str) -> Optional[Dict]:
        """Carica progetto"""
        return self.service.load_project(file_path)

    def is_modified(self) -> bool:
        """Verifica modifiche non salvate"""
        return self.service.is_modified()

    def mark_modified(self):
        """Segna come modificato"""
        self.service.mark_modified()

    def get_summary(self, project_data: Dict) -> Dict:
        """Riepilogo progetto"""
        return self.service.get_project_summary(project_data)


# Esempio di utilizzo
if __name__ == '__main__':
    # Test del bridge
    bridge = CalculationBridge()

    # Simula dati progetto nel formato GUI
    test_project = {
        'input_module': {
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410, 'knowledge_level': 'LC1'}
        },
        'openings_module': {
            'openings': []
        },
        'loads': {'vertical': 100, 'eccentricity': 0}
    }

    print("=== Test CalculationBridge ===")

    # Validazione
    validation = bridge.validate_project(test_project)
    print(f"Validazione: {'OK' if validation['is_valid'] else 'ERRORI'}")

    if validation['is_valid']:
        # Calcolo
        results = bridge.calculate(test_project)

        print(f"\nStato originale:")
        print(f"  K = {results['original']['K']:.1f} kN/m")
        print(f"  V_min = {results['original']['V_min']:.1f} kN")

        print(f"\nVerifica intervento locale:")
        print(f"  {results['verification']['message']}")
