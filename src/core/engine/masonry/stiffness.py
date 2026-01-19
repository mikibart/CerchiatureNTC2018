"""
Rigidezza Muratura NTC 2018
===========================

Modulo per il calcolo della rigidezza laterale delle pareti in muratura.
Combina contributo flessionale e tagliante secondo teoria di Timoshenko.

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass
from typing import List, Tuple
import logging

from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class StiffnessResult:
    """Risultato del calcolo rigidezza"""
    K_total: float = 0.0      # Rigidezza totale [kN/m]
    K_flex: float = 0.0       # Rigidezza flessionale [kN/m]
    K_shear: float = 0.0      # Rigidezza tagliante [kN/m]
    k_constraint: int = 12    # Fattore di vincolo

    # Dettagli per pareti con aperture
    K_maschi: List[float] = None  # Rigidezze singoli maschi [kN/m]

    def __post_init__(self):
        if self.K_maschi is None:
            self.K_maschi = []


class MasonryStiffness:
    """Calcoli di rigidezza muratura"""

    @staticmethod
    def calculate_shear_modulus(E: float, nu: float = None) -> float:
        """
        Calcola il modulo di taglio G

        Args:
            E: Modulo elastico [MPa]
            nu: Coefficiente di Poisson (default da NTC2018)

        Returns:
            G: Modulo di taglio [MPa]
        """
        if nu is None:
            nu = NTC2018.Muratura.NU
        return E / (2 * (1 + nu))

    @staticmethod
    def get_constraint_factor(bottom: str, top: str) -> int:
        """
        Determina il fattore di vincolo per lo schema statico

        Args:
            bottom: Vincolo alla base ('Incastro', 'Cerniera')
            top: Vincolo in sommità ('Incastro', 'Cerniera', 'Libero')

        Returns:
            k: Fattore di vincolo (3, 6, o 12)
        """
        return NTC2018.Vincoli.get_fattore(bottom, top)

    @staticmethod
    def calculate_flex_stiffness(E_Pa: float, I: float, h: float, k: int) -> float:
        """
        Calcola la rigidezza flessionale

        Formula: K_flex = k × E × I / h³

        Args:
            E_Pa: Modulo elastico [Pa]
            I: Momento d'inerzia [m⁴]
            h: Altezza [m]
            k: Fattore di vincolo (3, 6, 12)

        Returns:
            K_flex: Rigidezza flessionale [N/m]
        """
        if h <= 0:
            return 0.0
        return k * E_Pa * I / h**3

    @staticmethod
    def calculate_shear_stiffness(G_Pa: float, A: float, h: float,
                                 chi: float = None) -> float:
        """
        Calcola la rigidezza tagliante

        Formula: K_shear = χ × G × A / h

        Args:
            G_Pa: Modulo di taglio [Pa]
            A: Area sezione [m²]
            h: Altezza [m]
            chi: Fattore di forma sezione (default da NTC2018)

        Returns:
            K_shear: Rigidezza tagliante [N/m]
        """
        if chi is None:
            chi = NTC2018.Muratura.CHI
        if h <= 0:
            return 0.0
        return chi * G_Pa * A / h

    @staticmethod
    def combine_stiffness(K_flex: float, K_shear: float) -> float:
        """
        Combina rigidezza flessionale e tagliante (molle in serie)

        Formula: 1/K = 1/K_flex + 1/K_shear

        Args:
            K_flex: Rigidezza flessionale [N/m o kN/m]
            K_shear: Rigidezza tagliante [N/m o kN/m]

        Returns:
            K: Rigidezza combinata [stessa unità input]
        """
        if K_flex <= 0 or K_shear <= 0:
            return 0.0
        return 1 / (1/K_flex + 1/K_shear)

    @classmethod
    def calculate_wall_stiffness(cls, L: float, h: float, t: float,
                                E: float, bottom: str, top: str) -> StiffnessResult:
        """
        Calcola la rigidezza di una parete senza aperture

        Args:
            L: Lunghezza [m]
            h: Altezza [m]
            t: Spessore [m]
            E: Modulo elastico muratura [MPa]
            bottom: Vincolo alla base
            top: Vincolo in sommità

        Returns:
            StiffnessResult con rigidezze calcolate
        """
        result = StiffnessResult()

        # Converti E in Pa
        E_Pa = E * 1e6

        # Modulo di taglio
        G = cls.calculate_shear_modulus(E)
        G_Pa = G * 1e6

        # Proprietà geometriche
        I = t * L**3 / 12  # Momento d'inerzia [m⁴]
        A = L * t          # Area [m²]

        # Fattore di vincolo
        result.k_constraint = cls.get_constraint_factor(bottom, top)

        # Rigidezza flessionale
        K_flex = cls.calculate_flex_stiffness(E_Pa, I, h, result.k_constraint)
        result.K_flex = K_flex / 1000  # N/m -> kN/m

        # Rigidezza tagliante
        K_shear = cls.calculate_shear_stiffness(G_Pa, A, h)
        result.K_shear = K_shear / 1000  # N/m -> kN/m

        # Combinazione
        K = cls.combine_stiffness(K_flex, K_shear)
        result.K_total = K / 1000  # N/m -> kN/m

        logger.info(f"Rigidezza parete: K_flex={result.K_flex:.1f}, "
                   f"K_shear={result.K_shear:.1f}, K_tot={result.K_total:.1f} kN/m")

        return result

    @classmethod
    def calculate_wall_with_openings_stiffness(cls, wall_length: float, h: float, t: float,
                                               E: float, maschi_lengths: List[float],
                                               bottom: str, top: str) -> StiffnessResult:
        """
        Calcola la rigidezza di una parete con aperture

        I maschi lavorano in parallelo.

        Args:
            wall_length: Lunghezza totale parete [m]
            h: Altezza [m]
            t: Spessore [m]
            E: Modulo elastico [MPa]
            maschi_lengths: Lista lunghezze maschi [m]
            bottom: Vincolo alla base
            top: Vincolo in sommità

        Returns:
            StiffnessResult con rigidezze calcolate
        """
        result = StiffnessResult()
        result.k_constraint = cls.get_constraint_factor(bottom, top)
        result.K_maschi = []

        # Converti E in Pa
        E_Pa = E * 1e6
        G = cls.calculate_shear_modulus(E)
        G_Pa = G * 1e6

        K_total = 0
        K_flex_total = 0
        K_shear_total = 0

        for i, L_m in enumerate(maschi_lengths):
            if L_m <= 0:
                result.K_maschi.append(0)
                continue

            # Proprietà geometriche maschio
            I_m = t * L_m**3 / 12
            A_m = L_m * t

            # Rigidezza flessionale maschio
            K_flex_m = cls.calculate_flex_stiffness(E_Pa, I_m, h, result.k_constraint)

            # Rigidezza tagliante maschio
            K_shear_m = cls.calculate_shear_stiffness(G_Pa, A_m, h)

            # Rigidezza combinata maschio
            K_m = cls.combine_stiffness(K_flex_m, K_shear_m)

            # Accumula (maschi in parallelo)
            K_total += K_m
            K_flex_total += K_flex_m
            K_shear_total += K_shear_m

            result.K_maschi.append(K_m / 1000)  # kN/m

            logger.debug(f"Maschio {i+1}: L={L_m*100:.0f}cm, K={K_m/1000:.1f} kN/m")

        # Risultati totali
        result.K_total = K_total / 1000  # kN/m
        result.K_flex = K_flex_total / 1000
        result.K_shear = K_shear_total / 1000

        logger.info(f"Rigidezza con aperture: K_tot={result.K_total:.1f} kN/m "
                   f"({len(maschi_lengths)} maschi)")

        return result
