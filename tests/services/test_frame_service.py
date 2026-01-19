"""
Test per FrameService
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.frame_service import FrameService, FrameResult
from src.data.ntc2018_constants import NTC2018


class TestFrameResult(unittest.TestCase):
    """Test classe FrameResult"""

    def test_default_values(self):
        """Test valori default"""
        result = FrameResult()
        self.assertEqual(result.K_frame, 0.0)
        self.assertEqual(result.V_resistance, 0.0)
        self.assertEqual(result.materiale, "")
        self.assertFalse(result.is_arch)

    def test_to_dict(self):
        """Test conversione a dizionario"""
        result = FrameResult(
            K_frame=1000,
            V_resistance=50,
            materiale='acciaio'
        )
        d = result.to_dict()

        self.assertEqual(d['K_frame'], 1000)
        self.assertEqual(d['V_resistance'], 50)
        self.assertEqual(d['materiale'], 'acciaio')

    def test_warnings_list(self):
        """Test lista warning"""
        result = FrameResult()
        result.warnings.append("Warning 1")
        result.warnings.append("Warning 2")

        self.assertEqual(len(result.warnings), 2)


class TestFrameServiceInit(unittest.TestCase):
    """Test inizializzazione service"""

    def test_service_creation(self):
        """Test creazione service"""
        service = FrameService()

        self.assertIsNotNone(service.steel_calc)
        self.assertIsNotNone(service.concrete_calc)
        self.assertIsNotNone(service.arch_manager)

    def test_version(self):
        """Test versione"""
        self.assertEqual(FrameService.VERSION, "1.0.0")


class TestFrameServiceForceEstimation(unittest.TestCase):
    """Test stima forze"""

    def setUp(self):
        self.service = FrameService()

    def test_estimate_forces_basic(self):
        """Test stima forze base"""
        opening = {
            'width': 100,   # cm
            'height': 200,  # cm
            'y': 0          # cm
        }
        wall = {
            'thickness': 30,  # cm
            'height': 270     # cm
        }

        forces = self.service._estimate_frame_forces(opening, wall)

        self.assertIn('M_max', forces)
        self.assertIn('V_max', forces)
        self.assertIn('N_max', forces)
        self.assertGreater(forces['M_max'], 0)

    def test_estimate_forces_no_weight_above(self):
        """Test forze con apertura in alto"""
        opening = {
            'width': 100,
            'height': 100,
            'y': 170  # Apertura in alto, poca muratura sopra
        }
        wall = {
            'thickness': 30,
            'height': 270
        }

        forces = self.service._estimate_frame_forces(opening, wall)

        # Dovrebbe avere forze minori
        self.assertGreaterEqual(forces['M_max'], 0)


class TestFrameServiceSteelYield(unittest.TestCase):
    """Test resistenza acciaio"""

    def setUp(self):
        self.service = FrameService()

    def test_s235_yield(self):
        """Test fy S235"""
        fy = self.service._get_steel_yield_strength('S235')
        self.assertEqual(fy, 235)

    def test_s275_yield(self):
        """Test fy S275"""
        fy = self.service._get_steel_yield_strength('S275')
        self.assertEqual(fy, 275)

    def test_s355_yield(self):
        """Test fy S355"""
        fy = self.service._get_steel_yield_strength('S355')
        self.assertEqual(fy, 355)

    def test_unknown_defaults_to_s235(self):
        """Test classe sconosciuta -> default S235"""
        fy = self.service._get_steel_yield_strength('UNKNOWN')
        self.assertEqual(fy, 235)  # Default di get_fyk


class TestFrameServiceCalculateFrame(unittest.TestCase):
    """Test calcolo cerchiatura"""

    def setUp(self):
        self.service = FrameService()

    def test_calculate_frame_steel_basic(self):
        """Test calcolo cerchiatura acciaio base"""
        opening = {
            'type': 'Rettangolare',
            'width': 100,
            'height': 200,
            'y': 0
        }
        rinforzo = {
            'materiale': 'acciaio',
            'tipo': 'standard',
            'architrave': {
                'profilo': 'HEA 100',
                'n_profili': 1,
                'ruotato': False
            },
            'piedritti': {
                'profilo': 'HEA 100',
                'n_profili': 1
            },
            'classe_acciaio': 'S275'
        }
        wall = {'thickness': 30, 'height': 270}

        result = self.service.calculate_frame(opening, rinforzo, wall)

        self.assertIn('K_frame', result)
        self.assertIn('materiale', result)
        self.assertEqual(result['materiale'], 'acciaio')
        # Non verifichiamo il valore esatto perché dipende dal calculator

    def test_calculate_frame_unsupported_material(self):
        """Test materiale non supportato"""
        opening = {'type': 'Rettangolare', 'width': 100, 'height': 200}
        rinforzo = {'materiale': 'legno'}  # Non supportato
        wall = {'thickness': 30, 'height': 270}

        result = self.service.calculate_frame(opening, rinforzo, wall)

        self.assertIn('error', result)
        self.assertIn('non supportato', result['error'])

    def test_calculate_arch_opening(self):
        """Test apertura ad arco"""
        opening = {
            'type': 'Ad arco',
            'width': 100,
            'height': 200,
            'arch_rise': 30,  # freccia arco
            'y': 0
        }
        rinforzo = {
            'materiale': 'acciaio',
            'architrave': {'profilo': 'HEA 100', 'n_profili': 1},
            'classe_acciaio': 'S275'
        }
        wall = {'thickness': 30, 'height': 270}

        result = self.service.calculate_frame(opening, rinforzo, wall)

        self.assertTrue(result.get('is_arch', False))


class TestFrameServiceResistance(unittest.TestCase):
    """Test calcolo resistenza"""

    def setUp(self):
        self.service = FrameService()

    def test_resistance_no_profile(self):
        """Test resistenza senza profilo"""
        opening = {'height': 200}
        rinforzo = {'architrave': {}}

        V = self.service._calculate_frame_resistance(opening, rinforzo)
        self.assertEqual(V, 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
