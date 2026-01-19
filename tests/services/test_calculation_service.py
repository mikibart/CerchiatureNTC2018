"""
Test per CalculationService
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.calculation_service import (
    CalculationService, CalculationResult, MasonryState, VerificationResult
)
from src.data.ntc2018_constants import NTC2018


class TestMasonryState(unittest.TestCase):
    """Test classe MasonryState"""

    def test_default_values(self):
        """Test valori default"""
        state = MasonryState()
        self.assertEqual(state.K, 0.0)
        self.assertEqual(state.V_min, 0.0)

    def test_custom_values(self):
        """Test valori personalizzati"""
        state = MasonryState(K=1000, V_t1=50, V_t2=60, V_t3=80, V_min=50)
        self.assertEqual(state.K, 1000)
        self.assertEqual(state.V_min, 50)


class TestVerificationResult(unittest.TestCase):
    """Test classe VerificationResult"""

    def test_default_not_local(self):
        """Test default non locale"""
        result = VerificationResult()
        self.assertFalse(result.is_local)

    def test_local_when_ok(self):
        """Test locale quando limiti rispettati"""
        result = VerificationResult(
            is_local=True,
            stiffness_ok=True,
            resistance_ok=True,
            stiffness_variation=5.0,
            resistance_variation=-10.0
        )
        self.assertTrue(result.is_local)


class TestCalculationResult(unittest.TestCase):
    """Test classe CalculationResult"""

    def test_k_total_modified(self):
        """Test calcolo K totale modificato"""
        result = CalculationResult()
        result.modified.K = 1000
        result.K_frames = 500

        self.assertEqual(result.K_total_modified, 1500)

    def test_v_total_modified(self):
        """Test calcolo V totale modificato"""
        result = CalculationResult()
        result.modified.V_min = 50
        result.V_frames = 30

        self.assertEqual(result.V_total_modified, 80)

    def test_is_valid_no_errors(self):
        """Test validità senza errori"""
        result = CalculationResult()
        self.assertTrue(result.is_valid)

    def test_is_valid_with_errors(self):
        """Test invalidità con errori"""
        result = CalculationResult()
        result.errors.append("Errore test")
        self.assertFalse(result.is_valid)


class TestCalculationServiceInit(unittest.TestCase):
    """Test inizializzazione service"""

    def test_service_creation(self):
        """Test creazione service"""
        service = CalculationService()
        self.assertIsNotNone(service.masonry_calc)
        self.assertIsNotNone(service.verifier)

    def test_version(self):
        """Test versione service"""
        self.assertEqual(CalculationService.VERSION, "1.0.0")


class TestCalculationServiceExtractData(unittest.TestCase):
    """Test estrazione dati"""

    def setUp(self):
        self.service = CalculationService()

    def test_extract_wall_data(self):
        """Test estrazione dati parete"""
        project = {
            'wall': {'length': 300, 'height': 270, 'thickness': 30}
        }
        wall = self.service._extract_wall_data(project)

        self.assertEqual(wall['length'], 300)
        self.assertEqual(wall['height'], 270)
        self.assertEqual(wall['thickness'], 30)

    def test_extract_wall_from_input_module(self):
        """Test estrazione da input_module (retrocompatibilità)"""
        project = {
            'input_module': {
                'wall': {'length': 400, 'height': 300, 'thickness': 40}
            }
        }
        wall = self.service._extract_wall_data(project)

        self.assertEqual(wall['length'], 400)

    def test_extract_wall_missing_raises(self):
        """Test eccezione se parete mancante"""
        project = {}
        with self.assertRaises(ValueError):
            self.service._extract_wall_data(project)

    def test_extract_masonry_data(self):
        """Test estrazione dati muratura"""
        project = {
            'masonry': {'fcm': 2.4, 'tau0': 0.08, 'E': 1500}
        }
        masonry = self.service._extract_masonry_data(project)

        self.assertEqual(masonry['fcm'], 2.4)
        self.assertEqual(masonry['tau0'], 0.08)
        self.assertEqual(masonry['E'], 1500)

    def test_extract_masonry_defaults(self):
        """Test default muratura"""
        project = {'masonry': {}}
        masonry = self.service._extract_masonry_data(project)

        self.assertEqual(masonry['fcm'], 2.0)  # default
        self.assertEqual(masonry['tau0'], 0.074)  # default

    def test_extract_openings_from_openings_module(self):
        """Test estrazione aperture da openings_module"""
        project = {
            'openings_module': {
                'openings': [{'x': 50, 'width': 100}]
            }
        }
        openings = self.service._extract_openings(project)

        self.assertEqual(len(openings), 1)
        self.assertEqual(openings[0]['x'], 50)

    def test_extract_openings_direct(self):
        """Test estrazione aperture diretta"""
        project = {
            'openings': [{'x': 100, 'width': 150}]
        }
        openings = self.service._extract_openings(project)

        self.assertEqual(len(openings), 1)


class TestCalculationServiceConfidenceFactor(unittest.TestCase):
    """Test gestione fattore di confidenza"""

    def setUp(self):
        self.service = CalculationService()

    def test_fc_explicit(self):
        """Test FC esplicito nel progetto"""
        project = {'FC': 1.20}
        masonry = {'knowledge_level': 'LC1'}

        fc = self.service._get_confidence_factor(project, masonry)
        self.assertEqual(fc, 1.20)

    def test_fc_from_lc1(self):
        """Test FC da LC1"""
        project = {}
        masonry = {'knowledge_level': 'LC1'}

        fc = self.service._get_confidence_factor(project, masonry)
        self.assertEqual(fc, NTC2018.FC.LC1)

    def test_fc_from_lc2(self):
        """Test FC da LC2"""
        project = {}
        masonry = {'knowledge_level': 'LC2'}

        fc = self.service._get_confidence_factor(project, masonry)
        self.assertEqual(fc, NTC2018.FC.LC2)

    def test_fc_from_lc3(self):
        """Test FC da LC3"""
        project = {}
        masonry = {'knowledge_level': 'LC3'}

        fc = self.service._get_confidence_factor(project, masonry)
        self.assertEqual(fc, NTC2018.FC.LC3)


class TestCalculationServiceVerification(unittest.TestCase):
    """Test verifica intervento locale"""

    def setUp(self):
        self.service = CalculationService()

    def test_verify_local_ok(self):
        """Test verifica locale OK (variazioni entro limiti)"""
        original = MasonryState(K=1000, V_min=50)
        modified = MasonryState(K=950, V_min=45)  # K e V ridotti

        result = self.service._verify_local_intervention(
            original, modified, K_frames=50, V_frames=5
        )
        # K finale = 950 + 50 = 1000 (0% variazione)
        # V finale = 45 + 5 = 50 (0% variazione)
        self.assertTrue(result.stiffness_ok)
        self.assertTrue(result.resistance_ok)
        self.assertTrue(result.is_local)

    def test_verify_local_stiffness_fail(self):
        """Test verifica fallita per rigidezza"""
        original = MasonryState(K=1000, V_min=50)
        modified = MasonryState(K=700, V_min=50)  # -30% K

        result = self.service._verify_local_intervention(
            original, modified, K_frames=0, V_frames=0
        )

        self.assertFalse(result.stiffness_ok)
        self.assertFalse(result.is_local)

    def test_verify_local_resistance_fail(self):
        """Test verifica fallita per resistenza"""
        original = MasonryState(K=1000, V_min=100)
        modified = MasonryState(K=1000, V_min=70)  # -30% V

        result = self.service._verify_local_intervention(
            original, modified, K_frames=0, V_frames=0
        )

        self.assertFalse(result.resistance_ok)
        self.assertFalse(result.is_local)


class TestCalculationServiceIntegration(unittest.TestCase):
    """Test integrazione calcolo completo"""

    def setUp(self):
        self.service = CalculationService()

    def test_calculate_simple_wall(self):
        """Test calcolo parete semplice senza aperture"""
        project = {
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410},
            'loads': {'vertical': 100, 'eccentricity': 0},
            'constraints': {'bottom': 'Incastro', 'top': 'Incastro (Grinter)'},
            'FC': 1.35,
            'openings': []
        }

        result = self.service.calculate(project)

        self.assertTrue(result.is_valid)
        self.assertGreater(result.original.K, 0)
        self.assertGreater(result.original.V_min, 0)
        self.assertEqual(result.K_frames, 0)  # Nessuna cerchiatura

    def test_calculate_wall_with_existing_opening(self):
        """Test calcolo parete con apertura esistente"""
        project = {
            'wall': {'length': 400, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410},
            'loads': {'vertical': 100, 'eccentricity': 0},
            'FC': 1.35,
            'openings': [
                {'x': 100, 'y': 0, 'width': 100, 'height': 200, 'existing': True}
            ]
        }

        result = self.service.calculate(project)

        self.assertTrue(result.is_valid)
        # Con apertura K e V dovrebbero essere calcolati
        self.assertGreater(result.original.K, 0)

    def test_calculate_quick(self):
        """Test calcolo rapido"""
        wall = {'length': 300, 'height': 270, 'thickness': 30}
        masonry = {'fcm': 2.4, 'tau0': 0.074, 'E': 1410}

        K, V_t1, V_t2, V_t3 = self.service.calculate_quick(wall, masonry)

        self.assertGreater(K, 0)
        self.assertGreater(V_t1, 0)
        self.assertGreater(V_t2, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
