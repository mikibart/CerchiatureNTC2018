"""
Test per Sistema Plugin Rinforzi
================================

Test unitari per:
- ReinforcementInterface
- ReinforcementRegistry
- Plugin Acciaio e C.A.

Arch. Michelangelo Bartolotta
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.engine.reinforcement_interface import (
    ReinforcementCalculator,
    ReinforcementCapability,
    ReinforcementMaterial,
    ReinforcementType,
    CalculationInput,
    CalculationOutput
)
from src.core.engine.reinforcement_registry import (
    ReinforcementRegistry,
    get_registry,
    get_calculator_for
)
from src.core.engine.reinforcement_plugins import (
    SteelFramePlugin,
    ConcreteFramePlugin
)


# =============================================================================
# TEST CalculationInput
# =============================================================================

class TestCalculationInput(unittest.TestCase):
    """Test per CalculationInput"""

    def test_valid_input(self):
        """Test input valido"""
        input_data = CalculationInput(
            opening={'x': 50, 'y': 0, 'width': 100, 'height': 200},
            reinforcement={'materiale': 'acciaio', 'tipo': 'Telaio'}
        )
        errors = input_data.validate()
        self.assertEqual(len(errors), 0)

    def test_missing_opening(self):
        """Test apertura mancante"""
        input_data = CalculationInput(
            opening=None,
            reinforcement={'materiale': 'acciaio'}
        )
        errors = input_data.validate()
        self.assertIn("Dati apertura mancanti", errors)

    def test_missing_dimensions(self):
        """Test dimensioni mancanti"""
        input_data = CalculationInput(
            opening={'x': 50, 'y': 0},
            reinforcement={'materiale': 'acciaio'}
        )
        errors = input_data.validate()
        self.assertIn("Dimensioni apertura incomplete", errors)

    def test_missing_material(self):
        """Test materiale mancante"""
        input_data = CalculationInput(
            opening={'width': 100, 'height': 200},
            reinforcement={'tipo': 'Telaio'}
        )
        errors = input_data.validate()
        self.assertIn("Materiale rinforzo non specificato", errors)


# =============================================================================
# TEST CalculationOutput
# =============================================================================

class TestCalculationOutput(unittest.TestCase):
    """Test per CalculationOutput"""

    def test_default_success(self):
        """Test output default è success"""
        output = CalculationOutput()
        self.assertTrue(output.success)
        self.assertEqual(len(output.errors), 0)

    def test_add_error(self):
        """Test aggiunta errore"""
        output = CalculationOutput()
        output.add_error("Test error")
        self.assertFalse(output.success)
        self.assertIn("Test error", output.errors)

    def test_add_warning(self):
        """Test aggiunta warning"""
        output = CalculationOutput()
        output.add_warning("Test warning")
        self.assertTrue(output.success)  # Warning non cambia success
        self.assertIn("Test warning", output.warnings)

    def test_to_dict(self):
        """Test conversione a dizionario"""
        output = CalculationOutput(
            K_frame=1000,
            V_capacity=50,
            M_capacity=25
        )
        d = output.to_dict()
        self.assertEqual(d['K_frame'], 1000)
        self.assertEqual(d['V_capacity'], 50)
        self.assertTrue(d['success'])


# =============================================================================
# TEST ReinforcementRegistry
# =============================================================================

class TestReinforcementRegistry(unittest.TestCase):
    """Test per ReinforcementRegistry"""

    def setUp(self):
        """Setup per ogni test"""
        # Il registry è singleton, i plugin sono già registrati
        self.registry = get_registry()

    def test_singleton(self):
        """Test che registry è singleton"""
        registry2 = ReinforcementRegistry()
        self.assertIs(self.registry, registry2)

    def test_calculators_registered(self):
        """Test che i calcolatori sono registrati"""
        calculators = self.registry.get_all_calculators()
        self.assertGreater(len(calculators), 0)

    def test_get_calculator_for_steel(self):
        """Test selezione calcolatore acciaio"""
        calc = self.registry.get_calculator_for({'materiale': 'acciaio'})
        self.assertIsNotNone(calc)
        cap = calc.get_capability()
        self.assertIn(ReinforcementMaterial.STEEL, cap.materials)

    def test_get_calculator_for_concrete(self):
        """Test selezione calcolatore c.a."""
        calc = self.registry.get_calculator_for({'materiale': 'ca'})
        self.assertIsNotNone(calc)
        cap = calc.get_capability()
        self.assertIn(ReinforcementMaterial.CONCRETE, cap.materials)

    def test_get_calculator_for_unknown(self):
        """Test materiale sconosciuto"""
        calc = self.registry.get_calculator_for({'materiale': 'sconosciuto'})
        self.assertIsNone(calc)

    def test_get_capabilities(self):
        """Test ottenimento capacità"""
        caps = self.registry.get_capabilities()
        self.assertGreater(len(caps), 0)
        for cap in caps:
            self.assertIsInstance(cap, ReinforcementCapability)
            self.assertTrue(cap.name)

    def test_get_available_materials(self):
        """Test materiali disponibili"""
        materials = self.registry.get_available_materials()
        self.assertIn(ReinforcementMaterial.STEEL, materials)
        self.assertIn(ReinforcementMaterial.CONCRETE, materials)


# =============================================================================
# TEST SteelFramePlugin
# =============================================================================

class TestSteelFramePlugin(unittest.TestCase):
    """Test per SteelFramePlugin"""

    def setUp(self):
        self.plugin = SteelFramePlugin()
        self.sample_opening = {
            'x': 50, 'y': 0, 'width': 100, 'height': 200
        }
        self.sample_reinforcement = {
            'materiale': 'acciaio',
            'tipo': 'Telaio completo in acciaio',
            'classe_acciaio': 'S235',
            'architrave': {'profilo': 'HEA 160', 'doppio': False},
            'piedritti': {'profilo': 'HEA 160', 'doppio': False}
        }

    def test_capability(self):
        """Test capacità plugin"""
        cap = self.plugin.get_capability()
        self.assertEqual(cap.name, "Cerchiature Acciaio")
        self.assertIn(ReinforcementMaterial.STEEL, cap.materials)
        self.assertTrue(cap.supports_arch)

    def test_can_handle_steel(self):
        """Test può gestire acciaio"""
        self.assertTrue(self.plugin.can_handle({'materiale': 'acciaio'}))
        self.assertTrue(self.plugin.can_handle({'materiale': 'steel'}))

    def test_cannot_handle_concrete(self):
        """Test non gestisce c.a."""
        self.assertFalse(self.plugin.can_handle({'materiale': 'ca'}))

    def test_calculate_stiffness(self):
        """Test calcolo rigidezza"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate_stiffness(input_data)
        self.assertTrue(output.success)
        self.assertGreater(output.K_frame, 0)

    def test_calculate_capacity(self):
        """Test calcolo capacità"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate_capacity(input_data)
        self.assertTrue(output.success)

    def test_calculate_full(self):
        """Test calcolo completo"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate(input_data)
        self.assertTrue(output.success)
        self.assertGreater(output.K_frame, 0)

    def test_default_config(self):
        """Test configurazione default"""
        config = self.plugin.get_default_config()
        self.assertEqual(config['materiale'], 'acciaio')
        self.assertIn('architrave', config)
        self.assertIn('piedritti', config)


# =============================================================================
# TEST ConcreteFramePlugin
# =============================================================================

class TestConcreteFramePlugin(unittest.TestCase):
    """Test per ConcreteFramePlugin"""

    def setUp(self):
        self.plugin = ConcreteFramePlugin()
        self.sample_opening = {
            'x': 50, 'y': 0, 'width': 100, 'height': 200
        }
        self.sample_reinforcement = {
            'materiale': 'ca',
            'tipo': 'Telaio in C.A.',
            'classe_cls': 'C25/30',
            'tipo_acciaio': 'B450C',
            'copriferro': 30,
            'architrave': {
                'base': 30,
                'altezza': 40,
                'armatura_sup': '3φ16',
                'armatura_inf': '3φ16',
                'staffe': 'φ8/20'
            },
            'piedritti': {
                'base': 30,
                'spessore': 30,
                'armatura': '4φ16'
            }
        }

    def test_capability(self):
        """Test capacità plugin"""
        cap = self.plugin.get_capability()
        self.assertEqual(cap.name, "Cerchiature C.A.")
        self.assertIn(ReinforcementMaterial.CONCRETE, cap.materials)
        self.assertTrue(cap.supports_crack_check)

    def test_can_handle_concrete(self):
        """Test può gestire c.a."""
        self.assertTrue(self.plugin.can_handle({'materiale': 'ca'}))
        self.assertTrue(self.plugin.can_handle({'materiale': 'calcestruzzo'}))

    def test_cannot_handle_steel(self):
        """Test non gestisce acciaio"""
        self.assertFalse(self.plugin.can_handle({'materiale': 'acciaio'}))

    def test_calculate_stiffness(self):
        """Test calcolo rigidezza"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate_stiffness(input_data)
        self.assertTrue(output.success)
        self.assertGreater(output.K_frame, 0)

    def test_calculate_capacity(self):
        """Test calcolo capacità"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate_capacity(input_data)
        self.assertTrue(output.success)

    def test_calculate_full(self):
        """Test calcolo completo"""
        input_data = CalculationInput(
            opening=self.sample_opening,
            reinforcement=self.sample_reinforcement
        )
        output = self.plugin.calculate(input_data)
        self.assertTrue(output.success)
        self.assertGreater(output.K_frame, 0)

    def test_default_config(self):
        """Test configurazione default"""
        config = self.plugin.get_default_config()
        self.assertEqual(config['materiale'], 'ca')
        self.assertIn('architrave', config)
        self.assertEqual(config['classe_cls'], 'C25/30')


# =============================================================================
# TEST INTEGRAZIONE REGISTRY
# =============================================================================

class TestRegistryIntegration(unittest.TestCase):
    """Test integrazione registry con plugin"""

    def test_calculate_via_registry_steel(self):
        """Test calcolo via registry per acciaio"""
        registry = get_registry()

        result = registry.calculate(
            reinforcement_data={
                'materiale': 'acciaio',
                'tipo': 'Telaio completo in acciaio',
                'architrave': {'profilo': 'HEA 160'},
                'piedritti': {'profilo': 'HEA 160'}
            },
            opening_data={'width': 100, 'height': 200}
        )

        self.assertTrue(result.success)
        self.assertGreater(result.K_frame, 0)

    def test_calculate_via_registry_concrete(self):
        """Test calcolo via registry per c.a."""
        registry = get_registry()

        result = registry.calculate(
            reinforcement_data={
                'materiale': 'ca',
                'tipo': 'Telaio in C.A.',
                'classe_cls': 'C25/30',
                'architrave': {
                    'base': 30,
                    'altezza': 40,
                    'armatura_sup': '3φ16',
                    'armatura_inf': '3φ16'
                }
            },
            opening_data={'width': 100, 'height': 200}
        )

        self.assertTrue(result.success)
        self.assertGreater(result.K_frame, 0)

    def test_calculate_unknown_material(self):
        """Test calcolo con materiale sconosciuto"""
        registry = get_registry()

        result = registry.calculate(
            reinforcement_data={'materiale': 'legno'},  # Non supportato
            opening_data={'width': 100, 'height': 200}
        )

        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)

    def test_helper_function_get_calculator_for(self):
        """Test funzione helper get_calculator_for"""
        calc = get_calculator_for({'materiale': 'acciaio'})
        self.assertIsNotNone(calc)
        self.assertIsInstance(calc, SteelFramePlugin)


if __name__ == '__main__':
    unittest.main(verbosity=2)
