"""
Test di integrazione per verificare coerenza calcoli modulari
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine.masonry.calculator import MasonryCalculator
from src.core.engine.masonry.resistance import MasonryResistance
from src.core.engine.masonry.stiffness import MasonryStiffness
from src.core.engine.masonry.geometry import MasonryGeometry
from src.data.ntc2018_constants import NTC2018


class TestIntegrationReferenceValues(unittest.TestCase):
    """Test con valori di riferimento noti"""

    def test_reference_wall_resistance(self):
        """
        Test parete di riferimento - valori calcolati manualmente

        Parete: L=2.0m, h=2.7m, t=0.3m
        Carico: N=150 kN, e=0
        Muratura: fcm=2.4 MPa, tau0=0.074 MPa, E=1410 MPa
        Coefficienti: gamma_m=2.0, FC=1.35
        """
        result = MasonryResistance.calculate_resistance(
            L=2.0, h=2.7, t=0.3,
            N=150, e=0,
            fcm=2.4, tau0=0.074,
            gamma_m=2.0, FC=1.35
        )

        # Verifiche di base
        self.assertGreater(result.V_t1, 0)
        self.assertGreater(result.V_t2, 0)
        self.assertGreater(result.V_min, 0)

        # V_t2 = V_t1 * b
        self.assertAlmostEqual(result.V_t2, result.V_t1 * result.b_factor, places=2)

        # sigma_0 = N / (A * 1000) = 150 / (0.6 * 1000) = 0.25 MPa
        self.assertAlmostEqual(result.sigma_0, 0.25, places=3)

        # h/L = 2.7/2.0 = 1.35 < 1.5 -> b = 1.5 - 1.35/3 = 1.05
        expected_b = 1.5 - (2.7/2.0) / 3
        self.assertAlmostEqual(result.b_factor, expected_b, places=3)

    def test_reference_wall_stiffness(self):
        """
        Test rigidezza parete di riferimento

        Parete: L=2.0m, h=2.7m, t=0.3m, E=1410 MPa
        Vincoli: doppio incastro (k=12)
        """
        result = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3,
            E=1410, bottom='Incastro', top='Incastro (Grinter)'
        )

        # Verifiche di base
        self.assertGreater(result.K_total, 0)
        self.assertGreater(result.K_flex, 0)
        self.assertGreater(result.K_shear, 0)
        self.assertEqual(result.k_constraint, 12)

        # K_total < min(K_flex, K_shear) per molle in serie
        self.assertLess(result.K_total, result.K_flex)
        self.assertLess(result.K_total, result.K_shear)

        # Verifica formula combinazione: 1/K = 1/K_flex + 1/K_shear
        K_calc = 1 / (1/result.K_flex + 1/result.K_shear)
        self.assertAlmostEqual(result.K_total, K_calc, places=0)

    def test_calculator_orchestration(self):
        """Test che il calculator orchestra correttamente i moduli"""
        calc = MasonryCalculator()

        # Dati parete e muratura
        wall_data = {'length': 300, 'height': 270, 'thickness': 30}
        masonry_data = {'fcm': 2.4, 'tau0': 0.074, 'E': 1410}

        # Setup dati progetto (carichi, vincoli, FC)
        calc.set_project_data({
            'loads': {'vertical': 150, 'eccentricity': 0},
            'constraints': {'bottom': 'Incastro', 'top': 'Incastro (Grinter)'},
            'FC': 1.35
        })

        # Validazione
        validation = calc.validate_input(wall_data, masonry_data)
        self.assertTrue(validation.is_valid)

        # Resistenza
        V_t1, V_t2, V_t3 = calc.calculate_resistance(wall_data, masonry_data)
        V_min = min(V_t1, V_t2, V_t3) if V_t3 > 0 else min(V_t1, V_t2)
        self.assertGreater(V_min, 0)

        # Rigidezza
        K = calc.calculate_stiffness(wall_data, masonry_data)
        self.assertGreater(K, 0)

    def test_geometry_calculations_consistency(self):
        """Test coerenza calcoli geometrici"""
        # Area: L_cm * t_cm -> m²
        A = MasonryGeometry.calculate_area(200, 30)  # 2m x 0.3m
        self.assertAlmostEqual(A, 0.6, places=5)

        # Momento inerzia: t * L³ / 12
        I = MasonryGeometry.calculate_moment_of_inertia(200, 30)
        expected_I = 0.3 * (2.0**3) / 12  # 0.2 m⁴
        self.assertAlmostEqual(I, expected_I, places=5)

        # Snellezza: h/t
        slenderness = MasonryGeometry.calculate_slenderness(270, 30)
        self.assertAlmostEqual(slenderness, 9.0, places=2)

    def test_ntc2018_constants_used(self):
        """Verifica che i moduli usino le costanti NTC2018"""
        # Chi per taglio
        self.assertEqual(NTC2018.Muratura.CHI, 1.2)

        # Fattore di vincolo doppio incastro
        self.assertEqual(NTC2018.Vincoli.DOPPIO_INCASTRO, 12)

        # Coefficiente lunga durata (0.85 * fcm per V_t3)
        self.assertEqual(NTC2018.Muratura.COEFF_LUNGA_DURATA, 0.85)


class TestEdgeCases(unittest.TestCase):
    """Test casi limite"""

    def test_zero_load(self):
        """Test con carico nullo"""
        result = MasonryResistance.calculate_resistance(
            L=2.0, h=2.7, t=0.3,
            N=0, e=0,
            fcm=2.4, tau0=0.074,
            gamma_m=2.0, FC=1.0
        )
        # Con N=0, sigma_0=0, V_t1 dovrebbe essere solo tau0*A/gamma
        self.assertGreater(result.V_t1, 0)
        self.assertEqual(result.sigma_0, 0)

    def test_high_eccentricity(self):
        """Test con eccentricità elevata"""
        result = MasonryResistance.calculate_resistance(
            L=2.0, h=2.7, t=0.3,
            N=100, e=0.1,  # 10cm eccentricità
            fcm=2.4, tau0=0.074,
            gamma_m=2.0, FC=1.0
        )
        # sigma_max > sigma_0 con eccentricità
        self.assertGreater(result.sigma_max, result.sigma_0)

    def test_cantilever_vs_fixed(self):
        """Test confronto mensola vs doppio incastro"""
        result_fixed = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3, E=1410,
            bottom='Incastro', top='Incastro (Grinter)'
        )

        result_cant = MasonryStiffness.calculate_wall_stiffness(
            L=2.0, h=2.7, t=0.3, E=1410,
            bottom='Incastro', top='Libero'
        )

        # Mensola k=3, doppio incastro k=12 -> rigidezza flessionale 4x minore
        self.assertEqual(result_fixed.k_constraint, 12)
        self.assertEqual(result_cant.k_constraint, 3)
        self.assertLess(result_cant.K_flex, result_fixed.K_flex)


class TestBackwardsCompatibility(unittest.TestCase):
    """Test che i re-export funzionino"""

    def test_import_from_facade(self):
        """Test import dal modulo facade originale"""
        from src.core.engine.masonry import (
            MasonryCalculator,
            MasonryValidator,
            MasonryResistance,
            MasonryStiffness,
            MasonryGeometry
        )

        # Verifica che le classi siano importabili e utilizzabili
        self.assertTrue(hasattr(MasonryCalculator, 'VERSION'))
        self.assertTrue(hasattr(MasonryValidator, 'validate_wall_geometry'))
        self.assertTrue(hasattr(MasonryResistance, 'calculate_resistance'))
        self.assertTrue(hasattr(MasonryStiffness, 'calculate_wall_stiffness'))
        self.assertTrue(hasattr(MasonryGeometry, 'calculate_area'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
