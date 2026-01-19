"""
Test per modulo rigidezza muratura
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine.masonry.stiffness import MasonryStiffness, StiffnessResult
from src.data.ntc2018_constants import NTC2018


class TestStiffnessResult(unittest.TestCase):
    """Test classe StiffnessResult"""

    def test_default_values(self):
        """Test valori default"""
        result = StiffnessResult()
        self.assertEqual(result.K_total, 0)
        self.assertEqual(result.K_maschi, [])


class TestShearModulus(unittest.TestCase):
    """Test calcolo modulo taglio"""

    def test_shear_modulus_default(self):
        """Test G con nu default"""
        # G = E / (2*(1+nu)) con nu=0.2
        # G = 1410 / (2*1.2) = 587.5 MPa
        G = MasonryStiffness.calculate_shear_modulus(1410)
        expected = 1410 / (2 * 1.2)
        self.assertAlmostEqual(G, expected, places=1)

    def test_shear_modulus_custom_nu(self):
        """Test G con nu custom"""
        G = MasonryStiffness.calculate_shear_modulus(1000, nu=0.25)
        expected = 1000 / (2 * 1.25)
        self.assertAlmostEqual(G, expected, places=1)


class TestConstraintFactor(unittest.TestCase):
    """Test fattori di vincolo"""

    def test_double_fixed(self):
        """Test doppio incastro"""
        k = MasonryStiffness.get_constraint_factor('Incastro', 'Incastro (Grinter)')
        self.assertEqual(k, 12)

    def test_cantilever(self):
        """Test mensola"""
        k = MasonryStiffness.get_constraint_factor('Incastro', 'Libero')
        self.assertEqual(k, 3)

    def test_fixed_pinned(self):
        """Test incastro-cerniera"""
        k = MasonryStiffness.get_constraint_factor('Incastro', 'Cerniera')
        self.assertEqual(k, 6)


class TestFlexStiffness(unittest.TestCase):
    """Test rigidezza flessionale"""

    def test_flex_stiffness_basic(self):
        """Test formula K_flex = k*E*I/h³"""
        E_Pa = 1410e6  # Pa
        I = 0.1        # m⁴
        h = 2.7        # m
        k = 12

        K_flex = MasonryStiffness.calculate_flex_stiffness(E_Pa, I, h, k)
        expected = 12 * 1410e6 * 0.1 / (2.7**3)
        self.assertAlmostEqual(K_flex, expected, places=0)

    def test_flex_stiffness_zero_height(self):
        """Test con altezza zero"""
        K_flex = MasonryStiffness.calculate_flex_stiffness(1410e6, 0.1, 0, 12)
        self.assertEqual(K_flex, 0)


class TestShearStiffness(unittest.TestCase):
    """Test rigidezza tagliante"""

    def test_shear_stiffness_basic(self):
        """Test formula K_shear = χ*G*A/h"""
        G_Pa = 587e6   # Pa
        A = 0.6        # m²
        h = 2.7        # m

        K_shear = MasonryStiffness.calculate_shear_stiffness(G_Pa, A, h)
        chi = NTC2018.Muratura.CHI  # 1.2
        expected = chi * 587e6 * 0.6 / 2.7
        self.assertAlmostEqual(K_shear, expected, places=0)


class TestCombineStiffness(unittest.TestCase):
    """Test combinazione rigidezze"""

    def test_combine_equal(self):
        """Test combinazione rigidezze uguali"""
        # 1/K = 1/100 + 1/100 = 2/100 -> K = 50
        K = MasonryStiffness.combine_stiffness(100, 100)
        self.assertEqual(K, 50)

    def test_combine_unequal(self):
        """Test combinazione rigidezze diverse"""
        # 1/K = 1/100 + 1/200 = 3/200 -> K = 66.67
        K = MasonryStiffness.combine_stiffness(100, 200)
        self.assertAlmostEqual(K, 200/3, places=2)

    def test_combine_zero(self):
        """Test con rigidezza zero"""
        K = MasonryStiffness.combine_stiffness(100, 0)
        self.assertEqual(K, 0)


class TestWallStiffness(unittest.TestCase):
    """Test rigidezza parete completa"""

    def test_wall_stiffness_basic(self):
        """Test calcolo base"""
        result = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3,
            E=1410, bottom='Incastro', top='Incastro (Grinter)'
        )

        self.assertIsInstance(result, StiffnessResult)
        self.assertGreater(result.K_total, 0)
        self.assertGreater(result.K_flex, 0)
        self.assertGreater(result.K_shear, 0)
        self.assertEqual(result.k_constraint, 12)

    def test_wall_stiffness_cantilever(self):
        """Test parete a mensola (rigidezza minore)"""
        result_fixed = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3,
            E=1410, bottom='Incastro', top='Incastro (Grinter)'
        )

        result_cantilever = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3,
            E=1410, bottom='Incastro', top='Libero'
        )

        # Mensola ha k=3, doppio incastro k=12 -> rigidezza 4x minore
        self.assertLess(result_cantilever.K_total, result_fixed.K_total)


class TestWallWithOpeningsStiffness(unittest.TestCase):
    """Test rigidezza parete con aperture"""

    def test_single_opening(self):
        """Test con singola apertura"""
        # Parete 3m con due maschi da 1m ciascuno
        result = MasonryStiffness.calculate_wall_with_openings_stiffness(
            wall_length=3.0, h=2.7, t=0.3,
            E=1410, maschi_lengths=[1.0, 1.0],
            bottom='Incastro', top='Incastro (Grinter)'
        )

        self.assertGreater(result.K_total, 0)
        self.assertEqual(len(result.K_maschi), 2)

    def test_openings_reduce_stiffness(self):
        """Test che aperture riducano la rigidezza"""
        result_solid = MasonryStiffness.calculate_wall_stiffness(
            L=3.0, h=2.7, t=0.3,
            E=1410, bottom='Incastro', top='Incastro (Grinter)'
        )

        result_openings = MasonryStiffness.calculate_wall_with_openings_stiffness(
            wall_length=3.0, h=2.7, t=0.3,
            E=1410, maschi_lengths=[1.0, 1.0],  # 2m totale vs 3m
            bottom='Incastro', top='Incastro (Grinter)'
        )

        self.assertLess(result_openings.K_total, result_solid.K_total)


if __name__ == '__main__':
    unittest.main(verbosity=2)
