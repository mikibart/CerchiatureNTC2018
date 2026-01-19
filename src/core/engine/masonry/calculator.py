"""
MasonryCalculator - Orchestratore Calcoli Muratura
==================================================

Classe principale che orchestra tutti i moduli di calcolo muratura:
- Validazione input
- Geometria e maschi murari
- Resistenze V_t1, V_t2, V_t3
- Rigidezza laterale

Questo modulo fa da facade per i moduli specializzati.

Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional, Tuple
import logging

from src.data.ntc2018_constants import NTC2018
from .validation import MasonryValidator, ValidationResult
from .geometry import MasonryGeometry, MaschiMurari
from .resistance import MasonryResistance, ResistanceResult
from .stiffness import MasonryStiffness, StiffnessResult

logger = logging.getLogger(__name__)


class MasonryCalculator:
    """
    Calcolatore principale per verifiche muratura secondo NTC 2018

    Questa classe orchestra i moduli specializzati per:
    - Validazione input
    - Calcolo resistenze (V_t1, V_t2, V_t3)
    - Calcolo rigidezza

    Esempio d'uso:
        calc = MasonryCalculator()
        calc.set_project_data(project_data)

        # Calcolo resistenze
        V_t1, V_t2, V_t3 = calc.calculate_resistance(wall_data, masonry_data)

        # Calcolo rigidezza
        K = calc.calculate_stiffness(wall_data, masonry_data)
    """

    VERSION = "2.0.0-MODULAR"  # Nuova versione modulare

    def __init__(self):
        # Coefficienti di sicurezza (da NTC2018)
        self.gamma_m = NTC2018.Sicurezza.GAMMA_M_MURATURA_ESISTENTE
        self.FC = 1.0  # Fattore di confidenza default (LC3)
        self.project_data = {}

        print(f"\n>>> MasonryCalculator inizializzato - Versione: {self.VERSION}")
        logger.info(f"MasonryCalculator versione: {self.VERSION}")

    def set_project_data(self, project_data: Dict):
        """
        Imposta i dati completi del progetto

        Args:
            project_data: Dict con 'loads', 'constraints', 'FC'
        """
        self.project_data = project_data

        # Imposta FC dal progetto
        if 'FC' in project_data:
            self.FC = project_data['FC']
            logger.info(f"Fattore di confidenza impostato: FC={self.FC}")

        # Log configurazione
        loads = project_data.get('loads', {})
        constraints = project_data.get('constraints', {})

        logger.info(f"Dati progetto impostati: N={loads.get('vertical', 0)} kN, "
                   f"e={loads.get('eccentricity', 0)} cm")
        logger.info(f"Vincoli: {constraints.get('bottom', 'N/D')} - "
                   f"{constraints.get('top', 'N/D')}")

    def validate_input(self, wall_data: Dict, masonry_data: Dict) -> ValidationResult:
        """
        Valida i dati di input

        Args:
            wall_data: Dati geometrici parete
            masonry_data: Parametri meccanici muratura

        Returns:
            ValidationResult con esito e messaggi
        """
        loads = self.project_data.get('loads', None)
        return MasonryValidator.validate_all(wall_data, masonry_data, loads)

    def calculate_resistance(self, wall_data: Dict, masonry_data: Dict,
                           opening_data: Optional[List[Dict]] = None) -> Tuple[float, float, float]:
        """
        Calcola le resistenze del maschio murario secondo NTC 2018 § 8.7.1.5

        Args:
            wall_data: Dict con 'length', 'height', 'thickness' in cm
            masonry_data: Dict con 'fcm', 'tau0' in MPa
            opening_data: Lista aperture (opzionale)

        Returns:
            Tuple (V_t1, V_t2, V_t3) in kN
        """
        logger.info(f"=== INIZIO CALCOLO RESISTENZE (v.{self.VERSION}) ===")

        # Validazione
        validation = self.validate_input(wall_data, masonry_data)
        if not validation.is_valid:
            logger.error(f"Validazione fallita: {validation.errors}")
            return 0.0, 0.0, 0.0

        # Parametri geometrici
        L = wall_data['length'] / 100  # cm -> m
        h = wall_data['height'] / 100  # cm -> m
        t = wall_data['thickness'] / 100  # cm -> m

        # Parametri meccanici
        fcm = masonry_data.get('fcm', 2.0)
        tau0 = masonry_data.get('tau0', 0.074)

        # Coefficiente sicurezza totale
        gamma_tot = self.gamma_m * self.FC

        # Carichi
        N = self.project_data.get('loads', {}).get('vertical', 0)
        e = self.project_data.get('loads', {}).get('eccentricity', 0) / 100  # cm -> m

        logger.info(f"Parametri: L={L}m, h={h}m, t={t}m, fcm={fcm}MPa, tau0={tau0}MPa")
        logger.info(f"Carichi: N={N}kN, e={e*100:.1f}cm, γ_tot={gamma_tot}")

        # Se ci sono aperture, calcola per ogni maschio
        if opening_data and len(opening_data) > 0:
            maschi = MasonryGeometry.identify_maschi(wall_data, opening_data)

            V_t1_total = 0
            V_t2_total = 0
            V_t3_total = 0

            # Ripartizione carichi
            loads_per_maschio = MasonryGeometry.distribute_load(N, maschi, wall_data['length'])

            for i, (maschio, N_m) in enumerate(zip(maschi, loads_per_maschio)):
                L_m = maschio.length_m
                if L_m <= 0:
                    continue

                logger.info(f"Calcolo maschio {i+1}: L={maschio.length:.0f}cm, N={N_m:.1f}kN")

                result = MasonryResistance.calculate_resistance(
                    L_m, h, t, N_m, e, fcm, tau0, self.gamma_m, self.FC
                )

                V_t1_total += result.V_t1
                V_t2_total += result.V_t2
                V_t3_total += result.V_t3

            logger.info(f"=== FINE CALCOLO CON APERTURE ===")
            logger.info(f"TOTALI: V_t1={V_t1_total:.1f}, V_t2={V_t2_total:.1f}, V_t3={V_t3_total:.1f} kN")

            return V_t1_total, V_t2_total, V_t3_total

        else:
            # Parete senza aperture
            result = MasonryResistance.calculate_resistance(
                L, h, t, N, e, fcm, tau0, self.gamma_m, self.FC
            )

            logger.info(f"=== FINE CALCOLO PARETE INTERA ===")
            logger.warning(f"RISULTATI: V_t1={result.V_t1:.1f}, V_t2={result.V_t2:.1f}, V_t3={result.V_t3:.1f} kN")

            return result.V_t1, result.V_t2, result.V_t3

    def calculate_stiffness(self, wall_data: Dict, masonry_data: Dict,
                          opening_data: Optional[List[Dict]] = None) -> float:
        """
        Calcola la rigidezza laterale della parete

        Args:
            wall_data: Dict con 'length', 'height', 'thickness' in cm
            masonry_data: Dict con 'E' in MPa
            opening_data: Lista aperture (opzionale)

        Returns:
            K: Rigidezza laterale [kN/m]
        """
        logger.info(f"=== INIZIO CALCOLO RIGIDEZZA (v.{self.VERSION}) ===")

        # Parametri geometrici
        L = wall_data['length'] / 100  # cm -> m
        h = wall_data['height'] / 100  # cm -> m
        t = wall_data['thickness'] / 100  # cm -> m

        # Modulo elastico
        E = masonry_data.get('E', 1410)  # MPa

        # Vincoli
        constraints = self.project_data.get('constraints', {})
        bottom = constraints.get('bottom', 'Incastro')
        top = constraints.get('top', 'Incastro (Grinter)')

        logger.info(f"Geometria: L={L}m, h={h}m, t={t}m, E={E}MPa")
        logger.info(f"Vincoli: {bottom} - {top}")

        if opening_data and len(opening_data) > 0:
            # Parete con aperture
            maschi = MasonryGeometry.identify_maschi(wall_data, opening_data)
            maschi_lengths = [m.length_m for m in maschi]

            result = MasonryStiffness.calculate_wall_with_openings_stiffness(
                L, h, t, E, maschi_lengths, bottom, top
            )

            logger.warning(f"DEBUG MASONRY - Rigidezza CON aperture: {result.K_total:.1f} kN/m")
            return result.K_total

        else:
            # Parete senza aperture
            result = MasonryStiffness.calculate_wall_stiffness(
                L, h, t, E, bottom, top
            )

            logger.warning(f"DEBUG MASONRY - Rigidezza calcolata: {result.K_total:.1f} kN/m")
            logger.warning(f"DEBUG MASONRY - Schema: {bottom} - {top}, k={result.k_constraint}")

            return result.K_total

    def get_detailed_results(self, wall_data: Dict, masonry_data: Dict,
                            opening_data: Optional[List[Dict]] = None) -> Dict:
        """
        Calcola e restituisce risultati dettagliati per report

        Returns:
            Dict con tutti i risultati e valori intermedi
        """
        # Calcoli base
        V_t1, V_t2, V_t3 = self.calculate_resistance(wall_data, masonry_data, opening_data)
        K = self.calculate_stiffness(wall_data, masonry_data, opening_data)

        # Parametri
        L = wall_data['length'] / 100
        h = wall_data['height'] / 100
        t = wall_data['thickness'] / 100
        fcm = masonry_data.get('fcm', 2.0)
        tau0 = masonry_data.get('tau0', 0.074)
        E = masonry_data.get('E', 1410)

        N = self.project_data.get('loads', {}).get('vertical', 0)
        e = self.project_data.get('loads', {}).get('eccentricity', 0) / 100

        # Maschi murari
        if opening_data:
            maschi = MasonryGeometry.identify_maschi(wall_data, opening_data)
        else:
            maschi = MaschiMurari()

        return {
            'version': self.VERSION,
            'geometry': {
                'L': L, 'h': h, 't': t,
                'A': L * t,
                'I': t * L**3 / 12,
                'slenderness': h / t if t > 0 else 0
            },
            'materials': {
                'fcm': fcm, 'tau0': tau0, 'E': E,
                'G': MasonryStiffness.calculate_shear_modulus(E)
            },
            'loads': {
                'N': N, 'e': e,
                'sigma_0': MasonryResistance.calculate_sigma_0(N, L*t)
            },
            'safety': {
                'gamma_m': self.gamma_m,
                'FC': self.FC,
                'gamma_tot': self.gamma_m * self.FC
            },
            'resistance': {
                'V_t1': V_t1, 'V_t2': V_t2, 'V_t3': V_t3,
                'V_min': min(V_t1, V_t2, V_t3) if V_t3 > 0 else min(V_t1, V_t2),
                'b_factor': MasonryResistance.calculate_b_factor(h, L),
                'h_L_ratio': h / L if L > 0 else 0
            },
            'stiffness': {
                'K': K
            },
            'maschi': {
                'count': len(maschi),
                'foratura_ratio': maschi.foratura_ratio if opening_data else 0,
                'lengths': [m.length for m in maschi] if opening_data else []
            }
        }


# Alias per retrocompatibilità con il vecchio import
# from src.core.engine.masonry import MasonryCalculator
# continuerà a funzionare
