"""
Test per modulo resistenza muratura
"""

import unittest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine.masonry.resistance import MasonryResistance, ResistanceResult
from src.data.ntc2018_constants import NTC2018


class TestResistanceResult(unittest.TestCase):
    """Test classe ResistanceResult"""

    def test_v_min_calculation(self):
        """Test calcolo automatico V_min"""
        result = ResistanceResult(V_t1=100, V_t2=80, V_t3=120)
        self.assertEqual(result.V_min, 80)

    def test_v_min_without_v_t3(self):
        """Test V_min quando V_t3=0"""
        result = ResistanceResult(V_t1=100, V_t2=80, V_t3=0)
        self.assertEqual(result.V_min, 80)


class TestSigmaCalculations(unittest.TestCase):
    """Test calcoli tensione"""

    def test_sigma_0_basic(self):
        """Test tensione media"""
        # N=100kN, A=1m² -> sigma_0 = 100/(1*1000) = 0.1 MPa
        sigma_0 = MasonryResistance.calculate_sigma_0(100, 1.0)
        self.assertAlmostEqual(sigma_0, 0.1, places=4)

    def test_sigma_0_zero_area(self):
        """Test con area zero"""
        sigma_0 = MasonryResistance.calculate_sigma_0(100, 0)
        self.assertEqual(sigma_0, 0)

    def test_sigma_max_no_eccentricity(self):
        """Test sigma_max senza eccentricità"""
        # Senza eccentricità, sigma_max = sigma_med
        sigma_max = MasonryResistance.calculate_sigma_max(100, 1.0, 0, 2.0)
        expected = 100 / (1.0 * 1000)  # 0.1 MPa
        self.assertAlmostEqual(sigma_max, expected, places=4)

    def test_sigma_max_with_eccentricity(self):
        """Test sigma_max con eccentricità"""
        # sigma_max > sigma_med per e > 0
        sigma_max_e0 = MasonryResistance.calculate_sigma_max(100, 1.0, 0, 2.0)
        sigma_max_e1 = MasonryResistance.calculate_sigma_max(100, 1.0, 0.1, 2.0)
        self.assertGreater(sigma_max_e1, sigma_max_e0)


class TestBFactor(unittest.TestCase):
    """Test fattore di forma b"""

    def test_b_factor_high_ratio(self):
        """Test b=1.0 per h/L >= 1.5"""
        b = MasonryResistance.calculate_b_factor(3.0, 2.0)  # h/L = 1.5
        self.assertEqual(b, 1.0)

        b = MasonryResistance.calculate_b_factor(4.0, 2.0)  # h/L = 2.0
        self.assertEqual(b, 1.0)

    def test_b_factor_low_ratio(self):
        """Test formula b per h/L < 1.5"""
        # h/L = 0.9 -> b = 1.5 - 0.9/3 = 1.5 - 0.3 = 1.2
        b = MasonryResistance.calculate_b_factor(0.9, 1.0)
        self.assertAlmostEqual(b, 1.2, places=4)

    def test_b_factor_limits(self):
        """Test limiti b (1.0 <= b <= 1.5)"""
        # Caso estremo h/L molto basso -> b max 1.5
        b = MasonryResistance.calculate_b_factor(0.1, 1.0)
        self.assertLessEqual(b, 1.5)
        self.assertGreaterEqual(b, 1.0)


class TestVt1Calculation(unittest.TestCase):
    """Test calcolo V_t1"""

    def test_v_t1_basic(self):
        """Test V_t1 base"""
        # A=0.6m², tau0=0.074, sigma_0=0.1, fcm=2.0, gamma=2.0
        V_t1, V_t1_base, V_t1_limite = MasonryResistance.calculate_V_t1(
            A=0.6, tau0=0.074, sigma_0=0.1, fcm=2.0, gamma_tot=2.0
        )
        self.assertGreater(V_t1, 0)
        self.assertGreater(V_t1_base, 0)
        self.assertGreater(V_t1_limite, 0)

    def test_v_t1_with_limit(self):
        """Test che V_t1 rispetti il limite"""
        # V_t1_finale <= min(V_t1_base, V_t1_limite) / gamma
        V_t1, V_t1_base, V_t1_limite = MasonryResistance.calculate_V_t1(
            A=1.0, tau0=0.1, sigma_0=0.5, fcm=2.0, gamma_tot=2.0
        )
        expected_max = min(V_t1_base, V_t1_limite) / 2.0
        self.assertAlmostEqual(V_t1, expected_max, places=2)


class TestVt2Calculation(unittest.TestCase):
    """Test calcolo V_t2"""

    def test_v_t2_formula(self):
        """Test formula V_t2 = V_t1 * b"""
        V_t2 = MasonryResistance.calculate_V_t2(100, 1.2)
        self.assertEqual(V_t2, 120)


class TestVt3Calculation(unittest.TestCase):
    """Test calcolo V_t3"""

    def test_v_t3_normal(self):
        """Test V_t3 in condizioni normali"""
        V_t3, mu = MasonryResistance.calculate_V_t3(
            A=0.6, fcm=2.0, sigma_max=0.1, gamma_tot=2.0
        )
        self.assertGreater(V_t3, 0)
        self.assertGreater(mu, 0)
        self.assertLess(mu, 1)

    def test_v_t3_high_compression(self):
        """Test V_t3 con compressione elevata"""
        # sigma_max >= 0.85*fcm -> V_t3 = 0
        fcm = 2.0
        sigma_max = 0.85 * fcm + 0.1  # Supera limite
        V_t3, mu = MasonryResistance.calculate_V_t3(
            A=0.6, fcm=fcm, sigma_max=sigma_max, gamma_tot=2.0
        )
        self.assertEqual(V_t3, 0)
        self.assertEqual(mu, 0)


class TestFullResistanceCalculation(unittest.TestCase):
    """Test calcolo completo resistenze"""

    def test_calculate_resistance(self):
        """Test metodo principale"""
        result = MasonryResistance.calculate_resistance(
            L=2.0, h=2.7, t=0.3,
            N=100, e=0,
            fcm=2.0, tau0=0.074,
            gamma_m=2.0, FC=1.0
        )

        self.assertIsInstance(result, ResistanceResult)
        self.assertGreater(result.V_t1, 0)
        self.assertGreater(result.V_t2, 0)
        # V_t3 potrebbe essere > 0 o = 0
        self.assertGreater(result.V_min, 0)

    def test_resistance_consistency(self):
        """Test coerenza risultati"""
        result = MasonryResistance.calculate_resistance(
            L=2.0, h=2.7, t=0.3,
            N=100, e=0,
            fcm=2.0, tau0=0.074,
            gamma_m=2.0, FC=1.0
        )

        # V_t2 = V_t1 * b
        expected_V_t2 = result.V_t1 * result.b_factor
        self.assertAlmostEqual(result.V_t2, expected_V_t2, places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
