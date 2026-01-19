"""
Resistenza Muratura NTC 2018
============================

Modulo per il calcolo delle resistenze a taglio secondo NTC 2018 § 8.7.1.5:
- V_t1: Taglio per fessurazione diagonale
- V_t2: Taglio con fattore di forma
- V_t3: Resistenza a pressoflessione

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass
from typing import Tuple
import math
import logging

from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class ResistanceResult:
    """Risultato del calcolo resistenze"""
    V_t1: float = 0.0       # Taglio fessurazione diagonale [kN]
    V_t2: float = 0.0       # Taglio con fattore forma [kN]
    V_t3: float = 0.0       # Pressoflessione [kN]
    V_min: float = 0.0      # Minimo dei tre [kN]

    # Valori intermedi per debug/report
    sigma_0: float = 0.0    # Tensione compressione media [MPa]
    sigma_max: float = 0.0  # Tensione compressione massima [MPa]
    b_factor: float = 1.0   # Fattore di forma
    h_L_ratio: float = 0.0  # Rapporto h/L

    def __post_init__(self):
        """Calcola V_min dopo l'inizializzazione"""
        self.V_min = min(self.V_t1, self.V_t2, self.V_t3) if self.V_t3 > 0 else min(self.V_t1, self.V_t2)


class MasonryResistance:
    """Calcoli di resistenza muratura secondo NTC 2018 § 8.7.1.5"""

    @staticmethod
    def calculate_sigma_0(N: float, A: float) -> float:
        """
        Calcola la tensione di compressione media

        Args:
            N: Carico verticale [kN]
            A: Area sezione [m²]

        Returns:
            sigma_0: Tensione media [MPa]
        """
        if A <= 0:
            return 0.0
        return N / (A * 1000)  # kN/m² -> MPa

    @staticmethod
    def calculate_sigma_max(N: float, A: float, e: float, L: float) -> float:
        """
        Calcola la tensione massima di compressione (pressoflessione)

        Args:
            N: Carico verticale [kN]
            A: Area sezione [m²]
            e: Eccentricità [m]
            L: Lunghezza sezione [m]

        Returns:
            sigma_max: Tensione massima [MPa]
        """
        if A <= 0:
            return 0.0

        # Tensione media
        sigma_med = N / (A * 1000)  # kN/m² -> MPa

        # Modulo di resistenza
        W = A * L / 6  # m³

        # Momento per eccentricità
        M = abs(N * e)  # kN·m

        # Tensione massima (pressoflessione)
        if W > 0:
            sigma_max = sigma_med + M / (W * 1000)  # MPa
        else:
            sigma_max = sigma_med

        return max(0.0, sigma_max)

    @staticmethod
    def calculate_b_factor(h: float, L: float) -> float:
        """
        Calcola il fattore di forma b secondo NTC 2018 § 8.7.1.5

        Args:
            h: Altezza parete [m]
            L: Lunghezza parete [m]

        Returns:
            b: Fattore di forma (1.0 ≤ b ≤ 1.5)
        """
        if L <= 0:
            return 1.0

        h_L = h / L

        if h_L >= 1.5:
            b = 1.0
        else:
            # Formula NTC 2018: b = 1.5 - h/(3L) = 1.5 - (h/L)/3
            b = 1.5 - h_L / 3.0

        # Limiti
        b = max(1.0, min(1.5, b))

        return b

    @staticmethod
    def calculate_V_t1(A: float, tau0: float, sigma_0: float,
                      fcm: float, gamma_tot: float) -> Tuple[float, float, float]:
        """
        Calcola V_t1 - Resistenza a taglio per fessurazione diagonale

        Formula NTC 2018 eq. 8.7.1.16:
        V_t1 = A × τ_0 × √(1 + σ_0/τ_0) / γ_m

        Args:
            A: Area sezione [m²]
            tau0: Resistenza a taglio della muratura [MPa]
            sigma_0: Tensione di compressione media [MPa]
            fcm: Resistenza a compressione [MPa]
            gamma_tot: Coefficiente sicurezza totale (γ_m × FC)

        Returns:
            Tuple (V_t1_finale, V_t1_base, V_t1_limite) [kN]
        """
        if A <= 0 or tau0 <= 0 or gamma_tot <= 0:
            return 0.0, 0.0, 0.0

        # Formula base
        ratio = 1 + sigma_0 / tau0 if tau0 > 0 else 1
        V_t1_base = A * tau0 * math.sqrt(ratio) * 1000  # kN

        # Limite superiore (NTC 2018)
        V_t1_limite = A * NTC2018.Muratura.COEFF_LIMITE_VT1 * fcm * 1000  # kN

        # Valore finale
        V_t1_pre = min(V_t1_base, V_t1_limite)
        V_t1 = V_t1_pre / gamma_tot

        logger.debug(f"V_t1: base={V_t1_base:.1f}, limite={V_t1_limite:.1f}, "
                    f"finale={V_t1:.1f} kN")

        return V_t1, V_t1_base, V_t1_limite

    @staticmethod
    def calculate_V_t2(V_t1: float, b: float) -> float:
        """
        Calcola V_t2 - Resistenza a taglio con fattore di forma

        Formula NTC 2018 eq. 8.7.1.17:
        V_t2 = V_t1 × b

        Args:
            V_t1: Resistenza base [kN]
            b: Fattore di forma

        Returns:
            V_t2: Resistenza corretta [kN]
        """
        return V_t1 * b

    @staticmethod
    def calculate_V_t3(A: float, fcm: float, sigma_max: float,
                      gamma_tot: float) -> Tuple[float, float]:
        """
        Calcola V_t3 - Resistenza a pressoflessione

        Args:
            A: Area sezione [m²]
            fcm: Resistenza a compressione [MPa]
            sigma_max: Tensione massima [MPa]
            gamma_tot: Coefficiente sicurezza totale

        Returns:
            Tuple (V_t3, mu) dove mu è il coefficiente di riduzione
        """
        if A <= 0 or fcm <= 0 or gamma_tot <= 0:
            return 0.0, 0.0

        # Resistenza ridotta per carichi di lunga durata
        fcm_ridotto = NTC2018.Muratura.COEFF_LUNGA_DURATA * fcm

        if sigma_max >= fcm_ridotto:
            logger.warning(f"σ_max = {sigma_max:.2f} MPa ≥ 0.85×fcm = {fcm_ridotto:.2f} MPa")
            return 0.0, 0.0

        # Coefficiente di riduzione
        mu = 1 - sigma_max / fcm_ridotto

        # Formula pressoflessione
        V_t3 = (A * fcm * mu * 1000) / gamma_tot  # kN

        logger.debug(f"V_t3: sigma_max={sigma_max:.3f}, mu={mu:.3f}, V_t3={V_t3:.1f} kN")

        return V_t3, mu

    @classmethod
    def calculate_resistance(cls, L: float, h: float, t: float,
                            N: float, e: float,
                            fcm: float, tau0: float,
                            gamma_m: float, FC: float) -> ResistanceResult:
        """
        Calcola tutte le resistenze per una parete/maschio

        Args:
            L: Lunghezza [m]
            h: Altezza [m]
            t: Spessore [m]
            N: Carico verticale [kN]
            e: Eccentricità [m]
            fcm: Resistenza a compressione [MPa]
            tau0: Resistenza a taglio [MPa]
            gamma_m: Coefficiente sicurezza muratura
            FC: Fattore di confidenza

        Returns:
            ResistanceResult con tutti i valori calcolati
        """
        result = ResistanceResult()

        # Calcoli preliminari
        A = L * t  # Area [m²]
        gamma_tot = gamma_m * FC

        # Tensioni
        result.sigma_0 = cls.calculate_sigma_0(N, A)
        result.sigma_max = cls.calculate_sigma_max(N, A, e, L)

        # Fattore di forma
        result.h_L_ratio = h / L if L > 0 else 0
        result.b_factor = cls.calculate_b_factor(h, L)

        # V_t1 - Fessurazione diagonale
        result.V_t1, _, _ = cls.calculate_V_t1(A, tau0, result.sigma_0, fcm, gamma_tot)

        # V_t2 - Con fattore forma
        result.V_t2 = cls.calculate_V_t2(result.V_t1, result.b_factor)

        # V_t3 - Pressoflessione
        result.V_t3, _ = cls.calculate_V_t3(A, fcm, result.sigma_max, gamma_tot)

        # Minimo
        if result.V_t3 > 0:
            result.V_min = min(result.V_t1, result.V_t2, result.V_t3)
        else:
            result.V_min = min(result.V_t1, result.V_t2)

        logger.info(f"Resistenze: V_t1={result.V_t1:.1f}, V_t2={result.V_t2:.1f}, "
                   f"V_t3={result.V_t3:.1f}, V_min={result.V_min:.1f} kN")

        return result
