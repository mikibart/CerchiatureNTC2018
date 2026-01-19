"""
Test per Domain Layer - Engine
==============================

Test unitari per:
- SteelFrameCalculator (cerchiature acciaio)
- ConcreteFrameCalculator (cerchiature C.A.)
- FrameResult (risultati standardizzati)
- NTC2018Verifier (verifiche normative)

Arch. Michelangelo Bartolotta
"""

import unittest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.engine.steel_frame import SteelFrameCalculator
from src.core.engine.concrete_frame import ConcreteFrameCalculator
from src.core.engine.frame_result import FrameResult
from src.core.engine.verifications import NTC2018Verifier


# =============================================================================
# TEST FrameResult
# =============================================================================

class TestFrameResult(unittest.TestCase):
    """Test per FrameResult dataclass"""

    def test_default_values(self):
        """Test valori default"""
        result = FrameResult()
        self.assertEqual(result.K_frame, 0.0)
        self.assertEqual(result.M_max, 0.0)
        self.assertEqual(result.V_max, 0.0)
        self.assertEqual(result.materiale, "")
        self.assertIsNotNone(result.extra_data)
        self.assertEqual(result.extra_data, {})

    def test_init_with_values(self):
        """Test inizializzazione con valori"""
        result = FrameResult(
            K_frame=1000.0,
            M_max=50.0,
            V_max=25.0,
            L=2.0,
            h=1.5,
            tipo="Telaio completo",
            materiale="acciaio"
        )
        self.assertEqual(result.K_frame, 1000.0)
        self.assertEqual(result.L, 2.0)
        self.assertEqual(result.materiale, "acciaio")

    def test_to_dict(self):
        """Test conversione a dizionario"""
        result = FrameResult(
            K_frame=1000.0,
            materiale="acciaio"
        )
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['K_frame'], 1000.0)
        self.assertEqual(d['materiale'], 'acciaio')
        self.assertIn('extra_data', d)

    def test_add_warning(self):
        """Test aggiunta warning"""
        result = FrameResult()
        result.add_warning("Test warning")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Test warning", result.warnings)

    def test_set_error(self):
        """Test impostazione errore"""
        result = FrameResult()
        result.set_error("Test error")
        self.assertEqual(result.error, "Test error")

    def test_is_valid_true(self):
        """Test risultato valido"""
        result = FrameResult(K_frame=100.0)
        self.assertTrue(result.is_valid())

    def test_is_valid_false_with_error(self):
        """Test risultato invalido con errore"""
        result = FrameResult(K_frame=100.0)
        result.set_error("Test error")
        self.assertFalse(result.is_valid())

    def test_is_valid_false_negative_k(self):
        """Test risultato invalido con K negativo"""
        result = FrameResult(K_frame=-100.0)
        self.assertFalse(result.is_valid())

    def test_get_summary(self):
        """Test riepilogo testuale"""
        result = FrameResult(
            K_frame=1500.0,
            L=2.0,
            h=1.8,
            tipo="Telaio completo",
            materiale="acciaio"
        )
        summary = result.get_summary()
        self.assertIn("ACCIAIO", summary)
        self.assertIn("1500.0", summary)
        self.assertIn("Telaio completo", summary)

    def test_extra_data(self):
        """Test extra_data"""
        result = FrameResult(
            extra_data={'profilo': 'HEA 160', 'classe': 'S235'}
        )
        self.assertEqual(result.extra_data['profilo'], 'HEA 160')


# =============================================================================
# TEST SteelFrameCalculator
# =============================================================================

class TestSteelFrameCalculator(unittest.TestCase):
    """Test per SteelFrameCalculator"""

    def setUp(self):
        self.calculator = SteelFrameCalculator()
        self.opening_data = {
            'x': 50, 'y': 0, 'width': 100, 'height': 200
        }
        self.rinforzo_telaio = {
            'materiale': 'acciaio',
            'tipo': 'Telaio completo in acciaio',
            'classe_acciaio': 'S235',
            'architrave': {'profilo': 'HEA 160', 'doppio': False, 'ruotato': False},
            'piedritti': {'profilo': 'HEA 160', 'doppio': False, 'ruotato': False},
            'vincoli': {'base': 'Incastro', 'nodo': 'Incastro (continuità)'}
        }
        self.rinforzo_architrave = {
            'materiale': 'acciaio',
            'tipo': 'Solo architrave in acciaio',
            'classe_acciaio': 'S235',
            'architrave': {'profilo': 'HEA 160', 'doppio': False}
        }

    def test_steel_grades(self):
        """Test classi acciaio caricate"""
        self.assertIn('S235', self.calculator.steel_grades)
        self.assertIn('S355', self.calculator.steel_grades)
        self.assertEqual(self.calculator.steel_grades['S235']['fyk'], 235)

    def test_profiles_db(self):
        """Test database profili"""
        self.assertIn('HEA', self.calculator.profiles_db)
        self.assertIn('HEB', self.calculator.profiles_db)
        self.assertIn('IPE', self.calculator.profiles_db)
        self.assertIn('160', self.calculator.profiles_db['HEA'])

    def test_calculate_frame_stiffness_telaio(self):
        """Test calcolo rigidezza telaio completo"""
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )
        self.assertIn('K_frame', result)
        self.assertGreater(result['K_frame'], 0)
        self.assertEqual(result['materiale'], 'acciaio')
        self.assertEqual(result['tipo'], 'Telaio completo in acciaio')

    def test_calculate_frame_stiffness_architrave(self):
        """Test calcolo rigidezza solo architrave"""
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_architrave
        )
        self.assertIn('K_frame', result)
        self.assertGreater(result['K_frame'], 0)

    def test_calculate_frame_stiffness_wrong_material(self):
        """Test con materiale errato"""
        rinforzo = {'materiale': 'ca'}  # Calcestruzzo invece di acciaio
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo
        )
        self.assertEqual(result['K_frame'], 0)

    def test_calculate_frame_stiffness_double_profiles(self):
        """Test profili doppi (aumenta rigidezza)"""
        # Singolo
        result_single = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )

        # Doppio
        rinforzo_doppio = self.rinforzo_telaio.copy()
        rinforzo_doppio['architrave'] = {'profilo': 'HEA 160', 'doppio': True}
        rinforzo_doppio['piedritti'] = {'profilo': 'HEA 160', 'doppio': True}
        result_double = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo_doppio
        )

        # Doppio deve avere rigidezza maggiore
        self.assertGreater(result_double['K_frame'], result_single['K_frame'])

    def test_calculate_frame_stiffness_rotated_profile(self):
        """Test profilo ruotato (Ix <-> Iy)"""
        # Profilo normale
        result_normal = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )

        # Profilo ruotato
        rinforzo_ruotato = self.rinforzo_telaio.copy()
        rinforzo_ruotato['architrave'] = {'profilo': 'HEA 160', 'ruotato': True}
        rinforzo_ruotato['piedritti'] = {'profilo': 'HEA 160', 'ruotato': True}
        result_rotated = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo_ruotato
        )

        # Rigidezze diverse (Ix != Iy per HEA)
        self.assertNotEqual(result_normal['K_frame'], result_rotated['K_frame'])

    def test_calculate_frame_capacity(self):
        """Test calcolo capacità"""
        result = self.calculator.calculate_frame_capacity(
            self.opening_data, self.rinforzo_telaio, {}
        )
        self.assertIn('M_Rd_beam', result)
        self.assertIn('V_Rd_beam', result)
        self.assertGreater(result['M_Rd_beam'], 0)
        self.assertGreater(result['V_Rd_beam'], 0)

    def test_calculate_frame_capacity_columns(self):
        """Test capacità piedritti"""
        result = self.calculator.calculate_frame_capacity(
            self.opening_data, self.rinforzo_telaio, {}
        )
        self.assertIn('N_Rd_column', result)
        self.assertIn('M_Rd_column', result)
        self.assertGreater(result['N_Rd_column'], 0)

    def test_get_profile_property(self):
        """Test recupero proprietà profilo"""
        Ix = self.calculator._get_profile_property('HEA 160', 'Ix', False)
        self.assertIsNotNone(Ix)
        self.assertEqual(Ix, 1673)  # Valore HEA 160

    def test_get_profile_property_rotated(self):
        """Test proprietà profilo ruotato"""
        Ix = self.calculator._get_profile_property('HEA 160', 'Ix', False)
        Iy_as_Ix = self.calculator._get_profile_property('HEA 160', 'Ix', True)
        Iy = self.calculator._get_profile_property('HEA 160', 'Iy', False)

        self.assertEqual(Iy_as_Ix, Iy)  # Ruotato: Ix diventa Iy

    def test_get_profile_property_invalid(self):
        """Test profilo non valido"""
        result = self.calculator._get_profile_property('INVALID 999', 'Ix', False)
        self.assertIsNone(result)

    def test_arch_stiffness(self):
        """Test rigidezza arco"""
        rinforzo_arco = {
            'materiale': 'acciaio',
            'tipo': 'Arco metallico con piedritti',
            'architrave': {'profilo': 'HEA 160'},
            'piedritti': {'profilo': 'HEA 160'}
        }
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo_arco
        )
        self.assertGreater(result['K_frame'], 0)

    def test_larger_profile_higher_stiffness(self):
        """Test profilo maggiore = rigidezza maggiore"""
        # HEA 160
        result_160 = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )

        # HEA 200
        rinforzo_200 = self.rinforzo_telaio.copy()
        rinforzo_200['architrave'] = {'profilo': 'HEA 200'}
        rinforzo_200['piedritti'] = {'profilo': 'HEA 200'}
        result_200 = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo_200
        )

        self.assertGreater(result_200['K_frame'], result_160['K_frame'])


# =============================================================================
# TEST ConcreteFrameCalculator
# =============================================================================

class TestConcreteFrameCalculator(unittest.TestCase):
    """Test per ConcreteFrameCalculator"""

    def setUp(self):
        self.calculator = ConcreteFrameCalculator()
        self.opening_data = {
            'x': 50, 'y': 0, 'width': 100, 'height': 200
        }
        self.rinforzo_telaio = {
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
        self.rinforzo_architrave = {
            'materiale': 'ca',
            'tipo': 'Solo architrave in C.A.',
            'classe_cls': 'C25/30',
            'tipo_acciaio': 'B450C',
            'copriferro': 30,
            'architrave': {
                'base': 30,
                'altezza': 40,
                'armatura_sup': '3φ16',
                'armatura_inf': '3φ16',
                'staffe': 'φ8/20'
            }
        }

    def test_concrete_properties(self):
        """Test proprietà calcestruzzo"""
        self.assertIn('C25/30', self.calculator.concrete_properties)
        self.assertIn('C30/37', self.calculator.concrete_properties)
        c25 = self.calculator.concrete_properties['C25/30']
        self.assertEqual(c25['fck'], 25)

    def test_steel_properties(self):
        """Test proprietà acciaio armatura"""
        self.assertIn('B450C', self.calculator.steel_properties)
        b450 = self.calculator.steel_properties['B450C']
        self.assertEqual(b450['fyk'], 450)

    def test_calculate_frame_stiffness_telaio(self):
        """Test calcolo rigidezza telaio C.A."""
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )
        self.assertIn('K_frame', result)
        self.assertGreater(result['K_frame'], 0)
        self.assertEqual(result['materiale'], 'ca')

    def test_calculate_frame_stiffness_architrave(self):
        """Test calcolo rigidezza solo architrave C.A."""
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_architrave
        )
        self.assertIn('K_frame', result)
        self.assertGreater(result['K_frame'], 0)

    def test_calculate_frame_stiffness_wrong_material(self):
        """Test con materiale errato"""
        rinforzo = {'materiale': 'acciaio'}
        result = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo
        )
        self.assertEqual(result['K_frame'], 0)

    def test_calculate_frame_capacity(self):
        """Test calcolo capacità C.A."""
        result = self.calculator.calculate_frame_capacity(
            self.opening_data, self.rinforzo_telaio, {}
        )
        self.assertIn('M_Rd_beam', result)
        self.assertIn('V_Rd_beam', result)
        self.assertGreater(result['M_Rd_beam'], 0)
        self.assertGreater(result['V_Rd_beam'], 0)

    def test_calculate_frame_capacity_columns(self):
        """Test capacità piedritti C.A."""
        result = self.calculator.calculate_frame_capacity(
            self.opening_data, self.rinforzo_telaio, {}
        )
        self.assertIn('N_Rd_column', result)
        self.assertGreater(result['N_Rd_column'], 0)

    def test_parse_reinforcement(self):
        """Test parsing stringa armatura"""
        result = self.calculator._parse_reinforcement('3φ16')
        self.assertEqual(result['n_bars'], 3)
        self.assertEqual(result['diameter'], 16)
        expected_area = 3 * math.pi * 8**2  # 3 * π * r²
        self.assertAlmostEqual(result['area'], expected_area, delta=1)

    def test_parse_reinforcement_4phi20(self):
        """Test parsing 4φ20"""
        result = self.calculator._parse_reinforcement('4φ20')
        self.assertEqual(result['n_bars'], 4)
        self.assertEqual(result['diameter'], 20)

    def test_parse_reinforcement_invalid(self):
        """Test parsing stringa non valida"""
        result = self.calculator._parse_reinforcement('invalid')
        # Deve restituire default
        self.assertEqual(result['n_bars'], 3)
        self.assertEqual(result['diameter'], 16)

    def test_verify_minimum_reinforcement_ok(self):
        """Test verifica armature minime OK"""
        result = self.calculator.verify_minimum_reinforcement(self.rinforzo_telaio)
        self.assertTrue(result['all_ok'])

    def test_verify_minimum_reinforcement_insufficient(self):
        """Test armatura insufficiente"""
        rinforzo = self.rinforzo_telaio.copy()
        rinforzo['architrave'] = {
            'base': 30,
            'altezza': 40,
            'armatura_sup': '1φ8',  # Insufficiente
            'armatura_inf': '1φ8',
            'staffe': 'φ8/20'
        }
        result = self.calculator.verify_minimum_reinforcement(rinforzo)
        self.assertFalse(result['all_ok'])
        self.assertGreater(len(result['messages']), 0)

    def test_verify_staffe_passo_eccessivo(self):
        """Test passo staffe eccessivo"""
        rinforzo = self.rinforzo_telaio.copy()
        rinforzo['architrave'] = {
            'base': 30,
            'altezza': 40,
            'armatura_sup': '3φ16',
            'armatura_inf': '3φ16',
            'staffe': 'φ8/50'  # Passo troppo grande
        }
        result = self.calculator.verify_minimum_reinforcement(rinforzo)
        self.assertFalse(result['all_ok'])

    def test_calculate_crack_width(self):
        """Test calcolo apertura fessure"""
        w_k = self.calculator.calculate_crack_width(20.0, self.rinforzo_telaio)
        # Deve restituire un valore positivo
        self.assertGreater(w_k, 0)
        # Tipicamente < 0.4mm per condizioni normali
        self.assertLess(w_k, 1.0)

    def test_calculate_crack_width_wrong_material(self):
        """Test fessure con materiale errato"""
        rinforzo = {'materiale': 'acciaio'}
        w_k = self.calculator.calculate_crack_width(20.0, rinforzo)
        self.assertEqual(w_k, 0)

    def test_larger_section_higher_stiffness(self):
        """Test sezione maggiore = rigidezza maggiore"""
        # Sezione 30x40
        result_small = self.calculator.calculate_frame_stiffness(
            self.opening_data, self.rinforzo_telaio
        )

        # Sezione 40x50
        rinforzo_big = self.rinforzo_telaio.copy()
        rinforzo_big['architrave'] = {
            'base': 40, 'altezza': 50,
            'armatura_sup': '4φ20', 'armatura_inf': '4φ20',
            'staffe': 'φ8/15'
        }
        result_big = self.calculator.calculate_frame_stiffness(
            self.opening_data, rinforzo_big
        )

        self.assertGreater(result_big['K_frame'], result_small['K_frame'])


# =============================================================================
# TEST NTC2018Verifier
# =============================================================================

class TestNTC2018Verifier(unittest.TestCase):
    """Test per NTC2018Verifier"""

    def setUp(self):
        self.verifier = NTC2018Verifier()

    def test_verify_local_intervention_ok(self):
        """Test intervento locale verificato"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=1050,  # +5% (entro limite 15%)
            V_original=100, V_modified=100  # Nessuna riduzione
        )
        self.assertTrue(result['is_local'])
        self.assertTrue(result['stiffness_ok'])
        self.assertTrue(result['resistance_ok'])

    def test_verify_local_intervention_stiffness_exceeded(self):
        """Test rigidezza eccede limiti"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=1500,  # +50% > 15%
            V_original=100, V_modified=100
        )
        self.assertFalse(result['is_local'])
        self.assertFalse(result['stiffness_ok'])
        self.assertEqual(result['stiffness_variation'], 50.0)

    def test_verify_local_intervention_resistance_exceeded(self):
        """Test riduzione resistenza eccede limiti"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=1000,
            V_original=100, V_modified=70  # -30% > 20%
        )
        self.assertFalse(result['is_local'])
        self.assertFalse(result['resistance_ok'])

    def test_verify_local_intervention_resistance_increase(self):
        """Test aumento resistenza sempre OK"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=1000,
            V_original=100, V_modified=150  # +50% OK
        )
        self.assertTrue(result['is_local'])
        self.assertTrue(result['resistance_ok'])

    def test_verify_local_intervention_both_exceeded(self):
        """Test entrambi i limiti superati"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=500,  # -50%
            V_original=100, V_modified=50  # -50%
        )
        self.assertFalse(result['is_local'])
        self.assertFalse(result['stiffness_ok'])
        self.assertFalse(result['resistance_ok'])

    def test_verify_local_intervention_ratios(self):
        """Test calcolo rapporti"""
        result = self.verifier.verify_local_intervention(
            K_original=1000, K_modified=1100,
            V_original=100, V_modified=120
        )
        self.assertAlmostEqual(result['stiffness_ratio'], 1.1)
        self.assertAlmostEqual(result['resistance_ratio'], 1.2)

    def test_verify_opening_limits(self):
        """Test limiti aperture"""
        wall_data = {'length': 500, 'height': 300}  # 5m x 3m
        openings = [
            {'x': 100, 'y': 0, 'width': 100, 'height': 200}  # 1m x 2m
        ]
        result = self.verifier.verify_opening_limits(wall_data, openings)

        # Foratura = 2/(5*3) = 13.3%
        self.assertAlmostEqual(result['opening_ratio'], 13.33, delta=0.1)
        self.assertTrue(result['opening_ratio_ok'])

    def test_verify_opening_limits_exceeded(self):
        """Test foratura eccessiva"""
        wall_data = {'length': 300, 'height': 300}  # 3m x 3m
        openings = [
            {'x': 50, 'y': 0, 'width': 200, 'height': 250}  # 2m x 2.5m = 5m²
        ]
        result = self.verifier.verify_opening_limits(wall_data, openings)

        # Foratura = 5/9 = 55.5% > 40%
        self.assertGreater(result['opening_ratio'], 40)
        self.assertFalse(result['opening_ratio_ok'])

    def test_verify_maschi_ok(self):
        """Test maschi murari OK"""
        wall_data = {'length': 500, 'height': 300}
        openings = [
            {'x': 100, 'y': 0, 'width': 100, 'height': 200}  # Maschi: 1m - aper - 3m
        ]
        result = self.verifier.verify_opening_limits(wall_data, openings)
        self.assertTrue(result['min_maschio_ok'])

    def test_verify_maschi_insufficient(self):
        """Test maschi insufficienti"""
        wall_data = {'length': 300, 'height': 300}
        openings = [
            {'x': 20, 'y': 0, 'width': 100, 'height': 200}  # Maschio iniziale 20cm < 50cm
        ]
        result = self.verifier.verify_opening_limits(wall_data, openings)
        self.assertFalse(result['min_maschio_ok'])

    def test_calculate_safety_factors(self):
        """Test coefficienti sicurezza"""
        result = self.verifier.calculate_safety_factors(
            V_design=150, V_demand=100,
            K_provided=1200, K_required=1000
        )
        self.assertEqual(result['safety_resistance'], 1.5)
        self.assertEqual(result['safety_stiffness'], 1.2)
        self.assertEqual(result['global_safety'], 1.2)  # min
        self.assertTrue(result['is_safe'])

    def test_calculate_safety_factors_unsafe(self):
        """Test coefficienti insufficienti"""
        result = self.verifier.calculate_safety_factors(
            V_design=80, V_demand=100,  # < 1.0
            K_provided=1200, K_required=1000
        )
        self.assertEqual(result['safety_resistance'], 0.8)
        self.assertFalse(result['is_safe'])

    def test_get_verification_summary_ok(self):
        """Test riepilogo verifica OK"""
        results = {
            'is_local': True,
            'stiffness_ok': True,
            'resistance_ok': True,
            'stiffness_variation': 10.0,
            'stiffness_variation_limit': 15.0,
            'resistance_variation': 5.0,
            'resistance_variation_limit': 20.0
        }
        summary = self.verifier.get_verification_summary(results)
        self.assertIn("CLASSIFICABILE COME LOCALE", summary)
        self.assertIn("✓", summary)

    def test_get_verification_summary_not_ok(self):
        """Test riepilogo verifica KO"""
        results = {
            'is_local': False,
            'stiffness_ok': False,
            'resistance_ok': True,
            'stiffness_variation': 25.0,
            'stiffness_variation_limit': 15.0,
            'resistance_variation': 5.0,
            'resistance_variation_limit': 20.0
        }
        summary = self.verifier.get_verification_summary(results)
        self.assertIn("NON È CLASSIFICABILE COME LOCALE", summary)
        self.assertIn("SUPERA", summary)
        self.assertIn("RACCOMANDAZIONI", summary)


# =============================================================================
# TEST INTEGRAZIONE DOMAIN LAYER
# =============================================================================

class TestDomainIntegration(unittest.TestCase):
    """Test integrazione Domain Layer"""

    def test_steel_vs_concrete_stiffness(self):
        """Confronto rigidezza acciaio vs C.A."""
        opening = {'x': 0, 'y': 0, 'width': 100, 'height': 200}

        # Acciaio HEA 160
        steel_calc = SteelFrameCalculator()
        steel_result = steel_calc.calculate_frame_stiffness(opening, {
            'materiale': 'acciaio',
            'tipo': 'Telaio completo in acciaio',
            'architrave': {'profilo': 'HEA 160'},
            'piedritti': {'profilo': 'HEA 160'}
        })

        # C.A. 30x40
        concrete_calc = ConcreteFrameCalculator()
        concrete_result = concrete_calc.calculate_frame_stiffness(opening, {
            'materiale': 'ca',
            'tipo': 'Telaio in C.A.',
            'classe_cls': 'C25/30',
            'architrave': {'base': 30, 'altezza': 40},
            'piedritti': {'base': 30, 'spessore': 30}
        })

        # Entrambi devono avere rigidezza > 0
        self.assertGreater(steel_result['K_frame'], 0)
        self.assertGreater(concrete_result['K_frame'], 0)

    def test_verification_with_calculated_values(self):
        """Test verifica con valori calcolati"""
        opening = {'x': 0, 'y': 0, 'width': 100, 'height': 200}

        # Calcola rigidezza cerchiatura
        steel_calc = SteelFrameCalculator()
        result = steel_calc.calculate_frame_stiffness(opening, {
            'materiale': 'acciaio',
            'tipo': 'Telaio completo in acciaio',
            'architrave': {'profilo': 'HEA 160'},
            'piedritti': {'profilo': 'HEA 160'}
        })

        K_frame = result['K_frame']

        # Verifica intervento locale
        verifier = NTC2018Verifier()
        # Assumendo rigidezza originale parete
        K_wall = K_frame * 10  # Parete molto più rigida

        verification = verifier.verify_local_intervention(
            K_original=K_wall,
            K_modified=K_wall + K_frame,  # Aggiunta cerchiatura
            V_original=100,
            V_modified=100
        )

        # La variazione dovrebbe essere piccola
        self.assertLess(verification['stiffness_variation'], 20)

    def test_frame_result_from_calculator(self):
        """Test FrameResult da calcolatore"""
        calc = SteelFrameCalculator()
        result_dict = calc.calculate_frame_stiffness(
            {'width': 100, 'height': 200},
            {
                'materiale': 'acciaio',
                'tipo': 'Telaio completo in acciaio',
                'architrave': {'profilo': 'HEA 160'},
                'piedritti': {'profilo': 'HEA 160'}
            }
        )

        # Crea FrameResult dal dict
        frame_result = FrameResult(
            K_frame=result_dict['K_frame'],
            L=result_dict['L'],
            h=result_dict['h'],
            tipo=result_dict['tipo'],
            materiale=result_dict['materiale']
        )

        self.assertTrue(frame_result.is_valid())
        self.assertGreater(frame_result.K_frame, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
