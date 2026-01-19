"""
Test per modulo validazione muratura
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine.masonry.validation import MasonryValidator, ValidationResult


class TestValidationResult(unittest.TestCase):
    """Test classe ValidationResult"""

    def test_valid_result(self):
        """Test risultato valido"""
        result = ValidationResult(is_valid=True)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_add_error(self):
        """Test aggiunta errore"""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        self.assertFalse(result.is_valid)
        self.assertIn("Test error", result.errors)

    def test_add_warning(self):
        """Test aggiunta warning (non invalida)"""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        self.assertTrue(result.is_valid)  # Resta valido
        self.assertIn("Test warning", result.warnings)


class TestMasonryValidatorGeometry(unittest.TestCase):
    """Test validazione geometria"""

    def test_valid_geometry(self):
        """Test geometria valida"""
        wall_data = {'length': 300, 'height': 270, 'thickness': 30}
        result = MasonryValidator.validate_wall_geometry(wall_data)
        self.assertTrue(result.is_valid)

    def test_missing_field(self):
        """Test campo mancante"""
        wall_data = {'length': 300, 'height': 270}  # manca thickness
        result = MasonryValidator.validate_wall_geometry(wall_data)
        self.assertFalse(result.is_valid)

    def test_negative_length(self):
        """Test lunghezza negativa"""
        wall_data = {'length': -100, 'height': 270, 'thickness': 30}
        result = MasonryValidator.validate_wall_geometry(wall_data)
        self.assertFalse(result.is_valid)

    def test_zero_thickness(self):
        """Test spessore zero"""
        wall_data = {'length': 300, 'height': 270, 'thickness': 0}
        result = MasonryValidator.validate_wall_geometry(wall_data)
        self.assertFalse(result.is_valid)

    def test_high_slenderness_warning(self):
        """Test warning per snellezza elevata"""
        # h/t = 300/10 = 30 > 20
        wall_data = {'length': 300, 'height': 300, 'thickness': 10}
        result = MasonryValidator.validate_wall_geometry(wall_data)
        self.assertTrue(result.is_valid)  # Valido ma con warning
        self.assertTrue(any('Snellezza' in w for w in result.warnings))


class TestMasonryValidatorProperties(unittest.TestCase):
    """Test validazione proprietà meccaniche"""

    def test_valid_properties(self):
        """Test proprietà valide"""
        masonry_data = {'fcm': 2.0, 'tau0': 0.074, 'E': 1410}
        result = MasonryValidator.validate_masonry_properties(masonry_data)
        self.assertTrue(result.is_valid)

    def test_negative_fcm(self):
        """Test fcm negativo"""
        masonry_data = {'fcm': -1.0, 'tau0': 0.074}
        result = MasonryValidator.validate_masonry_properties(masonry_data)
        self.assertFalse(result.is_valid)

    def test_zero_tau0(self):
        """Test tau0 zero"""
        masonry_data = {'fcm': 2.0, 'tau0': 0}
        result = MasonryValidator.validate_masonry_properties(masonry_data)
        self.assertFalse(result.is_valid)


class TestMasonryValidatorLoads(unittest.TestCase):
    """Test validazione carichi"""

    def test_valid_loads(self):
        """Test carichi validi"""
        loads = {'vertical': 100, 'eccentricity': 0}
        wall_data = {'thickness': 30}
        result = MasonryValidator.validate_loads(loads, wall_data)
        self.assertTrue(result.is_valid)

    def test_high_eccentricity_warning(self):
        """Test warning per eccentricità elevata"""
        # e > t/6 = 30/6 = 5 cm
        loads = {'vertical': 100, 'eccentricity': 10}
        wall_data = {'thickness': 30}
        result = MasonryValidator.validate_loads(loads, wall_data)
        self.assertTrue(result.is_valid)
        self.assertTrue(any('Eccentricità' in w for w in result.warnings))

    def test_extreme_eccentricity_error(self):
        """Test errore per eccentricità fuori sezione"""
        # e > t/2 = 30/2 = 15 cm
        loads = {'vertical': 100, 'eccentricity': 20}
        wall_data = {'thickness': 30}
        result = MasonryValidator.validate_loads(loads, wall_data)
        self.assertFalse(result.is_valid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
