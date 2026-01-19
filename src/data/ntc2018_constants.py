"""
Costanti Normative NTC 2018
===========================

Modulo centralizzato per tutte le costanti normative secondo:
- NTC 2018 (D.M. 17/01/2018) - Norme Tecniche per le Costruzioni
- Circolare n. 7/2019 - Istruzioni per l'applicazione delle NTC 2018

Arch. Michelangelo Bartolotta
Versione: 1.0.0
Data: 2026-01-19

Riferimenti normativi:
- § 4.5 - Costruzioni in acciaio
- § 4.1 - Costruzioni in calcestruzzo armato
- § 8.4.1 - Interventi locali su edifici esistenti
- § 8.7.1.5 - Verifiche muratura esistente
- Tab. C8.5.I - Valori di riferimento parametri meccanici muratura
"""

from typing import Dict, NamedTuple, Optional
from dataclasses import dataclass


# =============================================================================
# COEFFICIENTI DI SICUREZZA
# =============================================================================

class CoefficientiSicurezza:
    """Coefficienti di sicurezza secondo NTC 2018"""

    # --- Muratura ---
    GAMMA_M_MURATURA_ESISTENTE = 2.0  # § 8.7.1 - Muratura esistente
    GAMMA_M_MURATURA_NUOVA = 2.0      # § 4.5.6.1 - Muratura nuova

    # --- Acciaio strutturale ---
    GAMMA_M0 = 1.05  # § 4.2.4.1.1 - Resistenza sezioni (Classe 1-4)
    GAMMA_M1 = 1.05  # § 4.2.4.1.1 - Resistenza instabilità
    GAMMA_M2 = 1.25  # § 4.2.4.1.1 - Resistenza collegamenti

    # --- Calcestruzzo armato ---
    GAMMA_C = 1.5    # § 4.1.2.1.1.1 - Calcestruzzo
    GAMMA_S = 1.15   # § 4.1.2.1.1.2 - Acciaio armatura

    # --- Fattori per carichi di lunga durata ---
    ALPHA_CC = 0.85  # § 4.1.2.1.1.1 - Effetti sfavorevoli carichi lunga durata cls


# =============================================================================
# FATTORI DI CONFIDENZA (FC)
# =============================================================================

class FattoriConfidenza:
    """Fattori di confidenza per edifici esistenti - § 8.5.4"""

    # Livelli di conoscenza
    LC1 = 1.35  # Conoscenza limitata
    LC2 = 1.20  # Conoscenza adeguata
    LC3 = 1.00  # Conoscenza accurata

    @classmethod
    def get_fc(cls, livello: str) -> float:
        """
        Restituisce il fattore di confidenza per il livello specificato

        Args:
            livello: 'LC1', 'LC2' o 'LC3'

        Returns:
            Fattore di confidenza FC
        """
        mapping = {
            'LC1': cls.LC1,
            'LC2': cls.LC2,
            'LC3': cls.LC3
        }
        return mapping.get(livello.upper(), cls.LC1)


# =============================================================================
# LIMITI INTERVENTI LOCALI - § 8.4.1
# =============================================================================

class LimitiInterventiLocali:
    """Limiti per classificazione interventi come 'locali' - § 8.4.1"""

    # Variazione massima di rigidezza (±15%)
    DELTA_K_MAX = 0.15

    # Riduzione massima di resistenza (-20%)
    # N.B.: Il segno è negativo, indica la riduzione massima ammissibile
    DELTA_V_MAX = -0.20

    # Percentuale massima foratura parete (40%)
    FORATURA_MAX = 0.40

    # Larghezza minima maschio murario [m]
    MASCHIO_MIN_WIDTH = 0.80

    # Fattore di collaborazione cerchiatura-muratura
    # Utilizzato per ridurre il contributo delle cerchiature
    GAMMA_COLLABORAZIONE = 1.5


# =============================================================================
# PARAMETRI MECCANICI MURATURA
# =============================================================================

class ParametriMuratura:
    """Parametri meccanici per calcoli muratura - § 8.7.1"""

    # Coefficiente di Poisson muratura
    NU = 0.20

    # Fattore di forma sezione rettangolare (taglio)
    CHI = 1.2

    # Coefficiente limite superiore V_t1
    COEFF_LIMITE_VT1 = 0.065

    # Coefficiente riduzione resistenza per carichi lunga durata
    COEFF_LUNGA_DURATA = 0.85

    # Snellezza massima parete
    SNELLEZZA_MAX = 20

    # Rapporto eccentricità limite (e/t)
    ECCENTRICITA_LIMITE_RATIO = 1/6


# =============================================================================
# FATTORI DI VINCOLO - SCHEMI STATICI
# =============================================================================

class FattoriVincolo:
    """Fattori per rigidezza secondo schema statico - Grinter"""

    # Doppio incastro (telaio con traverso infinitamente rigido)
    DOPPIO_INCASTRO = 12

    # Mensola (incastro-libero)
    MENSOLA = 3

    # Incastro-cerniera
    INCASTRO_CERNIERA = 6

    @classmethod
    def get_fattore(cls, vincolo_base: str, vincolo_sommita: str) -> int:
        """
        Restituisce il fattore di vincolo per lo schema statico

        Args:
            vincolo_base: Tipo vincolo alla base ('Incastro', 'Cerniera')
            vincolo_sommita: Tipo vincolo in sommità ('Incastro', 'Cerniera', 'Libero')

        Returns:
            Fattore k per calcolo rigidezza
        """
        if vincolo_base == 'Incastro' and 'Incastro' in vincolo_sommita:
            return cls.DOPPIO_INCASTRO
        elif vincolo_base == 'Incastro' and 'Libero' in vincolo_sommita:
            return cls.MENSOLA
        else:
            return cls.INCASTRO_CERNIERA


# =============================================================================
# ACCIAIO STRUTTURALE - § 4.2
# =============================================================================

@dataclass(frozen=True)
class ProprietaAcciaio:
    """Proprietà meccaniche acciaio strutturale"""
    fyk: float   # Tensione di snervamento [MPa]
    ftk: float   # Tensione di rottura [MPa]
    E: float     # Modulo elastico [MPa]
    G: float     # Modulo di taglio [MPa]
    nu: float    # Coefficiente di Poisson
    rho: float   # Peso specifico [kN/m³]


class AcciaioStrutturale:
    """Proprietà acciaio strutturale secondo EN 10025 - § 4.2"""

    # Modulo elastico acciaio [MPa]
    E = 210000

    # Modulo di taglio [MPa] - G = E / (2*(1+nu))
    G = 80769

    # Coefficiente di Poisson
    NU = 0.30

    # Peso specifico [kN/m³]
    RHO = 78.5

    # Coefficiente dilatazione termica [1/°C]
    ALPHA = 12e-6

    # Classi di acciaio (Tab. 4.2.I)
    CLASSI = {
        'S235': ProprietaAcciaio(fyk=235, ftk=360, E=210000, G=80769, nu=0.30, rho=78.5),
        'S275': ProprietaAcciaio(fyk=275, ftk=430, E=210000, G=80769, nu=0.30, rho=78.5),
        'S355': ProprietaAcciaio(fyk=355, ftk=510, E=210000, G=80769, nu=0.30, rho=78.5),
        'S450': ProprietaAcciaio(fyk=450, ftk=550, E=210000, G=80769, nu=0.30, rho=78.5),
    }

    @classmethod
    def get_proprieta(cls, classe: str) -> Optional[ProprietaAcciaio]:
        """
        Restituisce le proprietà per la classe di acciaio specificata

        Args:
            classe: Classe acciaio ('S235', 'S275', 'S355', 'S450')

        Returns:
            ProprietaAcciaio o None se classe non trovata
        """
        return cls.CLASSI.get(classe)

    @classmethod
    def get_fyk(cls, classe: str) -> float:
        """Restituisce fyk per la classe specificata"""
        prop = cls.get_proprieta(classe)
        return prop.fyk if prop else 235.0


# =============================================================================
# ACCIAIO ARMATURA - § 4.1.2.1.1.2
# =============================================================================

@dataclass(frozen=True)
class ProprietaAcciaioArmatura:
    """Proprietà meccaniche acciaio per armature"""
    fyk: float   # Tensione caratteristica snervamento [MPa]
    ftk: float   # Tensione caratteristica rottura [MPa]
    Es: float    # Modulo elastico [MPa]
    agt: float   # Allungamento sotto carico massimo [%]


class AcciaioArmatura:
    """Proprietà acciaio per armature secondo NTC 2018 - § 4.1.2.1.1.2"""

    # Modulo elastico [MPa]
    Es = 200000

    # Tipi di acciaio (Tab. 4.1.II)
    TIPI = {
        'B450C': ProprietaAcciaioArmatura(fyk=450, ftk=540, Es=200000, agt=7.5),
        'B450A': ProprietaAcciaioArmatura(fyk=450, ftk=540, Es=200000, agt=2.5),
    }

    @classmethod
    def get_proprieta(cls, tipo: str) -> Optional[ProprietaAcciaioArmatura]:
        """Restituisce le proprietà per il tipo di acciaio specificato"""
        return cls.TIPI.get(tipo)


# =============================================================================
# CALCESTRUZZO - § 4.1.2.1.1.1
# =============================================================================

@dataclass(frozen=True)
class ProprietaCalcestruzzo:
    """Proprietà meccaniche calcestruzzo"""
    fck: float   # Resistenza caratteristica cilindrica [MPa]
    fcm: float   # Resistenza media cilindrica [MPa]
    fctm: float  # Resistenza media a trazione [MPa]
    Ecm: float   # Modulo elastico secante [MPa]


class Calcestruzzo:
    """Proprietà calcestruzzo secondo NTC 2018 - § 4.1.2.1.1.1"""

    # Peso specifico cls armato [kN/m³]
    RHO_ARMATO = 25.0

    # Peso specifico cls non armato [kN/m³]
    RHO_NON_ARMATO = 24.0

    # Coefficiente di Poisson
    NU = 0.20

    # Classi di calcestruzzo (Tab. 4.1.I)
    CLASSI = {
        'C20/25': ProprietaCalcestruzzo(fck=20, fcm=28, fctm=2.2, Ecm=30000),
        'C25/30': ProprietaCalcestruzzo(fck=25, fcm=33, fctm=2.6, Ecm=31000),
        'C28/35': ProprietaCalcestruzzo(fck=28, fcm=36, fctm=2.8, Ecm=32000),
        'C30/37': ProprietaCalcestruzzo(fck=30, fcm=38, fctm=2.9, Ecm=33000),
        'C32/40': ProprietaCalcestruzzo(fck=32, fcm=40, fctm=3.0, Ecm=33000),
        'C35/45': ProprietaCalcestruzzo(fck=35, fcm=43, fctm=3.2, Ecm=34000),
        'C40/50': ProprietaCalcestruzzo(fck=40, fcm=48, fctm=3.5, Ecm=35000),
        'C45/55': ProprietaCalcestruzzo(fck=45, fcm=53, fctm=3.8, Ecm=36000),
        'C50/60': ProprietaCalcestruzzo(fck=50, fcm=58, fctm=4.1, Ecm=37000),
    }

    # Fattore riduzione inerzia per fessurazione SLE
    FATTORE_INERZIA_FESSURATA = 0.50

    @classmethod
    def get_proprieta(cls, classe: str) -> Optional[ProprietaCalcestruzzo]:
        """Restituisce le proprietà per la classe di calcestruzzo specificata"""
        return cls.CLASSI.get(classe)

    @classmethod
    def get_fcd(cls, classe: str, alpha_cc: float = 0.85, gamma_c: float = 1.5) -> float:
        """
        Calcola la resistenza di calcolo a compressione

        Args:
            classe: Classe calcestruzzo
            alpha_cc: Coefficiente effetti lunga durata (default 0.85)
            gamma_c: Coefficiente sicurezza (default 1.5)

        Returns:
            fcd in MPa
        """
        prop = cls.get_proprieta(classe)
        if prop:
            return alpha_cc * prop.fck / gamma_c
        return 0.0


# =============================================================================
# LIMITI CALANDRATURA ACCIAIO
# =============================================================================

class LimitiCalandratura:
    """Limiti per calandratura profili in acciaio"""

    # Rapporto r/h minimo per calandratura a freddo
    RH_MIN_FREDDO = 50

    # Rapporto r/h minimo per calandratura a freddo con preriscaldo
    RH_MIN_PRERISCALDO = 30

    # Rapporto r/h minimo per calandratura a caldo
    RH_MIN_CALDO = 15

    # Rapporto r/h critico (rischio rottura)
    RH_CRITICO = 10

    # Rapporto tensione residua / fy critico
    STRESS_RATIO_CRITICO = 0.80
    STRESS_RATIO_ALTO = 0.50
    STRESS_RATIO_MODERATO = 0.30


# =============================================================================
# CLASSE PRINCIPALE DI ACCESSO
# =============================================================================

class NTC2018:
    """
    Classe principale per accesso a tutte le costanti NTC 2018

    Esempio d'uso:
        from src.data.ntc2018_constants import NTC2018

        # Coefficienti sicurezza
        gamma_m = NTC2018.Sicurezza.GAMMA_M_MURATURA_ESISTENTE
        gamma_c = NTC2018.Sicurezza.GAMMA_C

        # Fattori confidenza
        fc = NTC2018.FC.get_fc('LC2')

        # Limiti interventi locali
        delta_k_max = NTC2018.InterventiLocali.DELTA_K_MAX

        # Acciaio strutturale
        acciaio = NTC2018.Acciaio.get_proprieta('S355')

        # Calcestruzzo
        cls = NTC2018.Cls.get_proprieta('C25/30')
    """

    # Sottoclassi per accesso organizzato
    Sicurezza = CoefficientiSicurezza
    FC = FattoriConfidenza
    InterventiLocali = LimitiInterventiLocali
    Muratura = ParametriMuratura
    Vincoli = FattoriVincolo
    Acciaio = AcciaioStrutturale
    AcciaioArm = AcciaioArmatura
    Cls = Calcestruzzo
    Calandratura = LimitiCalandratura

    # Versione modulo
    VERSION = "1.0.0"

    # Riferimento normativo
    NORMATIVA = "D.M. 17/01/2018 - NTC 2018"
    CIRCOLARE = "Circolare n. 7 del 21/01/2019"


# =============================================================================
# TEST MODULO
# =============================================================================

if __name__ == "__main__":
    print("=== Test Modulo NTC2018 Constants ===\n")

    # Test coefficienti sicurezza
    print("COEFFICIENTI SICUREZZA:")
    print(f"  γ_m muratura esistente: {NTC2018.Sicurezza.GAMMA_M_MURATURA_ESISTENTE}")
    print(f"  γ_m0 acciaio: {NTC2018.Sicurezza.GAMMA_M0}")
    print(f"  γ_c calcestruzzo: {NTC2018.Sicurezza.GAMMA_C}")
    print(f"  γ_s armatura: {NTC2018.Sicurezza.GAMMA_S}")

    # Test fattori confidenza
    print("\nFATTORI CONFIDENZA:")
    for lc in ['LC1', 'LC2', 'LC3']:
        print(f"  {lc}: FC = {NTC2018.FC.get_fc(lc)}")

    # Test limiti interventi locali
    print("\nLIMITI INTERVENTI LOCALI:")
    print(f"  ΔK max: ±{NTC2018.InterventiLocali.DELTA_K_MAX*100:.0f}%")
    print(f"  ΔV max: -{NTC2018.InterventiLocali.DELTA_V_MAX*100:.0f}%")

    # Test acciaio
    print("\nACCIAIO STRUTTURALE:")
    for classe in ['S235', 'S275', 'S355']:
        prop = NTC2018.Acciaio.get_proprieta(classe)
        print(f"  {classe}: fyk={prop.fyk} MPa, ftk={prop.ftk} MPa")

    # Test calcestruzzo
    print("\nCALCESTRUZZO:")
    for classe in ['C25/30', 'C30/37', 'C35/45']:
        prop = NTC2018.Cls.get_proprieta(classe)
        print(f"  {classe}: fck={prop.fck} MPa, Ecm={prop.Ecm} MPa")

    print(f"\nVersione modulo: {NTC2018.VERSION}")
    print(f"Normativa: {NTC2018.NORMATIVA}")
