"""
Test per il modulo costanti NTC 2018
Verifica correttezza valori normativi

Arch. Michelangelo Bartolotta
"""

import unittest
import sys
import os

# Aggiungi path per import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.ntc2018_constants import (
    NTC2018,
    CoefficientiSicurezza,
    FattoriConfidenza,
    LimitiInterventiLocali,
    ParametriMuratura,
    FattoriVincolo,
    AcciaioStrutturale,
    AcciaioArmatura,
    Calcestruzzo,
    LimitiCalandratura
)


class TestCoefficientiSicurezza(unittest.TestCase):
    """Test coefficienti di sicurezza"""

    def test_gamma_m_muratura(self):
        """Verifica γ_m muratura esistente = 2.0 (§ 8.7.1)"""
        self.assertEqual(CoefficientiSicurezza.GAMMA_M_MURATURA_ESISTENTE, 2.0)

    def test_gamma_m0_acciaio(self):
        """Verifica γ_m0 acciaio = 1.05 (§ 4.2.4.1.1)"""
        self.assertEqual(CoefficientiSicurezza.GAMMA_M0, 1.05)

    def test_gamma_c_calcestruzzo(self):
        """Verifica γ_c calcestruzzo = 1.5 (§ 4.1.2.1.1.1)"""
        self.assertEqual(CoefficientiSicurezza.GAMMA_C, 1.5)

    def test_gamma_s_armatura(self):
        """Verifica γ_s armatura = 1.15 (§ 4.1.2.1.1.2)"""
        self.assertEqual(CoefficientiSicurezza.GAMMA_S, 1.15)

    def test_alpha_cc(self):
        """Verifica α_cc = 0.85 (§ 4.1.2.1.1.1)"""
        self.assertEqual(CoefficientiSicurezza.ALPHA_CC, 0.85)


class TestFattoriConfidenza(unittest.TestCase):
    """Test fattori di confidenza per edifici esistenti"""

    def test_fc_lc1(self):
        """Verifica FC per LC1 = 1.35 (§ 8.5.4)"""
        self.assertEqual(FattoriConfidenza.LC1, 1.35)

    def test_fc_lc2(self):
        """Verifica FC per LC2 = 1.20 (§ 8.5.4)"""
        self.assertEqual(FattoriConfidenza.LC2, 1.20)

    def test_fc_lc3(self):
        """Verifica FC per LC3 = 1.00 (§ 8.5.4)"""
        self.assertEqual(FattoriConfidenza.LC3, 1.00)

    def test_get_fc_method(self):
        """Test metodo get_fc"""
        self.assertEqual(FattoriConfidenza.get_fc('LC1'), 1.35)
        self.assertEqual(FattoriConfidenza.get_fc('LC2'), 1.20)
        self.assertEqual(FattoriConfidenza.get_fc('LC3'), 1.00)
        # Case insensitive
        self.assertEqual(FattoriConfidenza.get_fc('lc2'), 1.20)
        # Default a LC1 per valori non validi
        self.assertEqual(FattoriConfidenza.get_fc('invalid'), 1.35)


class TestLimitiInterventiLocali(unittest.TestCase):
    """Test limiti per interventi locali § 8.4.1"""

    def test_delta_k_max(self):
        """Verifica ΔK max = ±15%"""
        self.assertEqual(LimitiInterventiLocali.DELTA_K_MAX, 0.15)

    def test_delta_v_max(self):
        """Verifica ΔV max = -20% (valore negativo)"""
        self.assertEqual(LimitiInterventiLocali.DELTA_V_MAX, -0.20)

    def test_foratura_max(self):
        """Verifica foratura max = 40%"""
        self.assertEqual(LimitiInterventiLocali.FORATURA_MAX, 0.40)

    def test_maschio_min_width(self):
        """Verifica larghezza minima maschio = 0.80 m"""
        self.assertEqual(LimitiInterventiLocali.MASCHIO_MIN_WIDTH, 0.80)


class TestParametriMuratura(unittest.TestCase):
    """Test parametri meccanici muratura"""

    def test_nu(self):
        """Verifica coefficiente di Poisson = 0.20"""
        self.assertEqual(ParametriMuratura.NU, 0.20)

    def test_chi(self):
        """Verifica fattore di forma = 1.2"""
        self.assertEqual(ParametriMuratura.CHI, 1.2)

    def test_coeff_limite_vt1(self):
        """Verifica coefficiente limite V_t1 = 0.065"""
        self.assertEqual(ParametriMuratura.COEFF_LIMITE_VT1, 0.065)

    def test_coeff_lunga_durata(self):
        """Verifica coefficiente carichi lunga durata = 0.85"""
        self.assertEqual(ParametriMuratura.COEFF_LUNGA_DURATA, 0.85)

    def test_snellezza_max(self):
        """Verifica snellezza massima = 20"""
        self.assertEqual(ParametriMuratura.SNELLEZZA_MAX, 20)


class TestFattoriVincolo(unittest.TestCase):
    """Test fattori di vincolo per schemi statici"""

    def test_doppio_incastro(self):
        """Verifica k = 12 per doppio incastro"""
        self.assertEqual(FattoriVincolo.DOPPIO_INCASTRO, 12)

    def test_mensola(self):
        """Verifica k = 3 per mensola"""
        self.assertEqual(FattoriVincolo.MENSOLA, 3)

    def test_incastro_cerniera(self):
        """Verifica k = 6 per incastro-cerniera"""
        self.assertEqual(FattoriVincolo.INCASTRO_CERNIERA, 6)

    def test_get_fattore(self):
        """Test metodo get_fattore"""
        self.assertEqual(FattoriVincolo.get_fattore('Incastro', 'Incastro (Grinter)'), 12)
        self.assertEqual(FattoriVincolo.get_fattore('Incastro', 'Libero'), 3)
        self.assertEqual(FattoriVincolo.get_fattore('Incastro', 'Cerniera'), 6)
        self.assertEqual(FattoriVincolo.get_fattore('Cerniera', 'Cerniera'), 6)


class TestAcciaioStrutturale(unittest.TestCase):
    """Test proprietà acciaio strutturale"""

    def test_modulo_elastico(self):
        """Verifica E = 210000 MPa"""
        self.assertEqual(AcciaioStrutturale.E, 210000)

    def test_s235(self):
        """Verifica proprietà S235"""
        prop = AcciaioStrutturale.get_proprieta('S235')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fyk, 235)
        self.assertEqual(prop.ftk, 360)

    def test_s275(self):
        """Verifica proprietà S275"""
        prop = AcciaioStrutturale.get_proprieta('S275')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fyk, 275)
        self.assertEqual(prop.ftk, 430)

    def test_s355(self):
        """Verifica proprietà S355"""
        prop = AcciaioStrutturale.get_proprieta('S355')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fyk, 355)
        self.assertEqual(prop.ftk, 510)

    def test_get_fyk(self):
        """Test metodo get_fyk"""
        self.assertEqual(AcciaioStrutturale.get_fyk('S235'), 235)
        self.assertEqual(AcciaioStrutturale.get_fyk('S355'), 355)
        # Default 235 per classe non trovata
        self.assertEqual(AcciaioStrutturale.get_fyk('invalid'), 235.0)


class TestAcciaioArmatura(unittest.TestCase):
    """Test proprietà acciaio armatura"""

    def test_modulo_elastico(self):
        """Verifica Es = 200000 MPa"""
        self.assertEqual(AcciaioArmatura.Es, 200000)

    def test_b450c(self):
        """Verifica proprietà B450C"""
        prop = AcciaioArmatura.get_proprieta('B450C')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fyk, 450)
        self.assertEqual(prop.ftk, 540)


class TestCalcestruzzo(unittest.TestCase):
    """Test proprietà calcestruzzo"""

    def test_c25_30(self):
        """Verifica proprietà C25/30"""
        prop = Calcestruzzo.get_proprieta('C25/30')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fck, 25)
        self.assertEqual(prop.fcm, 33)
        self.assertEqual(prop.Ecm, 31000)

    def test_c35_45(self):
        """Verifica proprietà C35/45"""
        prop = Calcestruzzo.get_proprieta('C35/45')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.fck, 35)
        self.assertEqual(prop.fcm, 43)

    def test_fcd_calculation(self):
        """Verifica calcolo fcd"""
        # fcd = alpha_cc * fck / gamma_c = 0.85 * 25 / 1.5 = 14.17 MPa
        fcd = Calcestruzzo.get_fcd('C25/30')
        self.assertAlmostEqual(fcd, 14.167, places=2)

    def test_fattore_inerzia_fessurata(self):
        """Verifica fattore inerzia fessurata = 0.50"""
        self.assertEqual(Calcestruzzo.FATTORE_INERZIA_FESSURATA, 0.50)


class TestLimitiCalandratura(unittest.TestCase):
    """Test limiti calandratura"""

    def test_rh_limits(self):
        """Verifica limiti r/h"""
        self.assertEqual(LimitiCalandratura.RH_MIN_FREDDO, 50)
        self.assertEqual(LimitiCalandratura.RH_MIN_PRERISCALDO, 30)
        self.assertEqual(LimitiCalandratura.RH_MIN_CALDO, 15)
        self.assertEqual(LimitiCalandratura.RH_CRITICO, 10)

    def test_stress_ratio_limits(self):
        """Verifica limiti stress ratio"""
        self.assertEqual(LimitiCalandratura.STRESS_RATIO_CRITICO, 0.80)
        self.assertEqual(LimitiCalandratura.STRESS_RATIO_ALTO, 0.50)
        self.assertEqual(LimitiCalandratura.STRESS_RATIO_MODERATO, 0.30)


class TestNTC2018Class(unittest.TestCase):
    """Test classe principale NTC2018"""

    def test_access_via_main_class(self):
        """Verifica accesso tramite classe principale"""
        self.assertEqual(NTC2018.Sicurezza.GAMMA_C, 1.5)
        self.assertEqual(NTC2018.FC.get_fc('LC2'), 1.20)
        self.assertEqual(NTC2018.InterventiLocali.DELTA_K_MAX, 0.15)
        self.assertEqual(NTC2018.Acciaio.E, 210000)
        self.assertIsNotNone(NTC2018.Cls.get_proprieta('C25/30'))

    def test_version(self):
        """Verifica versione modulo"""
        self.assertEqual(NTC2018.VERSION, "1.0.0")


if __name__ == '__main__':
    unittest.main(verbosity=2)
