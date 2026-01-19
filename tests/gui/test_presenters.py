"""
Test per Presenter Layer
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.gui.presenters.base_presenter import BasePresenter, ValidationResult
from src.gui.presenters.input_presenter import InputPresenter
from src.gui.presenters.openings_presenter import OpeningsPresenter, OpeningStats
from src.gui.presenters.calc_presenter import CalcPresenter
from src.data.ntc2018_constants import NTC2018


# =============================================================================
# TEST ValidationResult
# =============================================================================

class TestValidationResult(unittest.TestCase):
    """Test ValidationResult"""

    def test_default_valid(self):
        """Test default è valido"""
        result = ValidationResult()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_add_error_invalidates(self):
        """Test aggiunta errore invalida"""
        result = ValidationResult()
        result.add_error("Test error")
        self.assertFalse(result.is_valid)
        self.assertIn("Test error", result.errors)

    def test_add_warning_keeps_valid(self):
        """Test warning non invalida"""
        result = ValidationResult()
        result.add_warning("Test warning")
        self.assertTrue(result.is_valid)
        self.assertIn("Test warning", result.warnings)


# =============================================================================
# TEST InputPresenter
# =============================================================================

class TestInputPresenterInit(unittest.TestCase):
    """Test inizializzazione InputPresenter"""

    def test_creation(self):
        """Test creazione"""
        presenter = InputPresenter()
        self.assertIsNotNone(presenter)

    def test_default_wall_data(self):
        """Test dati parete default"""
        presenter = InputPresenter()
        wall = presenter.get_wall_data()

        self.assertEqual(wall['length'], 300)
        self.assertEqual(wall['height'], 270)
        self.assertEqual(wall['thickness'], 30)

    def test_default_masonry_data(self):
        """Test dati muratura default"""
        presenter = InputPresenter()
        masonry = presenter.get_masonry_data()

        self.assertGreater(masonry['fcm'], 0)
        self.assertGreater(masonry['tau0'], 0)


class TestInputPresenterWall(unittest.TestCase):
    """Test gestione parete"""

    def setUp(self):
        self.presenter = InputPresenter()

    def test_set_wall_dimensions_valid(self):
        """Test impostazione dimensioni valide"""
        result = self.presenter.set_wall_dimensions(400, 300, 40)
        self.assertTrue(result.is_valid)

        wall = self.presenter.get_wall_data()
        self.assertEqual(wall['length'], 400)
        self.assertEqual(wall['height'], 300)
        self.assertEqual(wall['thickness'], 40)

    def test_set_wall_dimensions_invalid_length(self):
        """Test lunghezza non valida"""
        result = self.presenter.set_wall_dimensions(-100, 270, 30)
        self.assertFalse(result.is_valid)

    def test_set_wall_dimensions_slenderness_warning(self):
        """Test warning snellezza elevata"""
        # h/t = 320/15 = 21.3 > 20 (SNELLEZZA_MAX)
        # thickness=15 è il minimo valido
        result = self.presenter.set_wall_dimensions(300, 320, 15)
        self.assertTrue(result.is_valid)  # Valido ma con warning
        self.assertTrue(len(result.warnings) > 0)


class TestInputPresenterMasonry(unittest.TestCase):
    """Test gestione muratura"""

    def setUp(self):
        self.presenter = InputPresenter()

    def test_get_available_materials(self):
        """Test lista materiali"""
        materials = self.presenter.get_available_materials()
        self.assertGreater(len(materials), 0)

    def test_set_masonry_type(self):
        """Test impostazione tipo muratura"""
        materials = self.presenter.get_available_materials()
        if materials:
            success = self.presenter.set_masonry_type(materials[0])
            self.assertTrue(success)

    def test_set_masonry_params(self):
        """Test impostazione parametri manuali"""
        result = self.presenter.set_masonry_params(fcm=3.0, tau0=0.1, E=2000)
        self.assertTrue(result.is_valid)

        masonry = self.presenter.get_masonry_data()
        self.assertEqual(masonry['fcm'], 3.0)
        self.assertEqual(masonry['tau0'], 0.1)

    def test_set_knowledge_level(self):
        """Test livello di conoscenza"""
        self.presenter.set_knowledge_level('LC2')
        design = self.presenter.get_design_values()

        self.assertEqual(design['FC'], NTC2018.FC.LC2)


class TestInputPresenterOpenings(unittest.TestCase):
    """Test gestione aperture"""

    def setUp(self):
        self.presenter = InputPresenter()

    def test_add_opening_valid(self):
        """Test aggiunta apertura valida"""
        opening = {'x': 50, 'y': 0, 'width': 100, 'height': 200}
        success, result = self.presenter.add_opening(opening)

        self.assertTrue(success)
        self.assertEqual(len(self.presenter.get_openings()), 1)

    def test_add_opening_out_of_bounds(self):
        """Test apertura fuori dai limiti"""
        opening = {'x': 250, 'y': 0, 'width': 100, 'height': 200}  # Eccede 300
        success, result = self.presenter.add_opening(opening)

        self.assertFalse(success)
        self.assertFalse(result.is_valid)

    def test_add_overlapping_openings(self):
        """Test aperture sovrapposte"""
        op1 = {'x': 50, 'y': 0, 'width': 100, 'height': 200}
        op2 = {'x': 100, 'y': 0, 'width': 100, 'height': 200}  # Si sovrappone

        self.presenter.add_opening(op1)
        success, result = self.presenter.add_opening(op2)

        self.assertFalse(success)

    def test_validate_opening_maschi_warning(self):
        """Test warning maschi stretti"""
        # Crea apertura che lascia maschio stretto
        opening = {'x': 10, 'y': 0, 'width': 280, 'height': 200}  # Maschio sx=10cm
        result = self.presenter.validate_opening(opening)

        self.assertTrue(result.is_valid)  # Valido ma con warning
        self.assertTrue(any('Maschio' in w for w in result.warnings))


class TestInputPresenterCollectData(unittest.TestCase):
    """Test raccolta dati"""

    def setUp(self):
        self.presenter = InputPresenter()

    def test_collect_data_structure(self):
        """Test struttura dati raccolti"""
        data = self.presenter.collect_data()

        self.assertIn('wall', data)
        self.assertIn('masonry', data)
        self.assertIn('loads', data)
        self.assertIn('constraints', data)
        self.assertIn('FC', data)
        self.assertIn('openings', data)

    def test_load_data(self):
        """Test caricamento dati"""
        data = {
            'wall': {'length': 500, 'height': 300, 'thickness': 40},
            'masonry': {'fcm': 3.0, 'tau0': 0.1, 'E': 2000, 'knowledge_level': 'LC2'},
            'openings': []
        }

        self.presenter.load_data(data)

        wall = self.presenter.get_wall_data()
        self.assertEqual(wall['length'], 500)


# =============================================================================
# TEST OpeningsPresenter
# =============================================================================

class TestOpeningsPresenterInit(unittest.TestCase):
    """Test inizializzazione OpeningsPresenter"""

    def test_creation(self):
        """Test creazione"""
        presenter = OpeningsPresenter()
        self.assertIsNotNone(presenter)
        self.assertEqual(presenter.get_opening_count(), 0)


class TestOpeningsPresenterOpenings(unittest.TestCase):
    """Test gestione aperture"""

    def setUp(self):
        self.presenter = OpeningsPresenter()
        self.presenter.set_wall_context({'length': 300, 'height': 270})

    def test_set_openings(self):
        """Test impostazione aperture"""
        openings = [
            {'x': 50, 'y': 0, 'width': 100, 'height': 200},
            {'x': 200, 'y': 0, 'width': 80, 'height': 180}
        ]
        self.presenter.set_openings(openings)

        self.assertEqual(self.presenter.get_opening_count(), 2)

    def test_add_opening(self):
        """Test aggiunta apertura"""
        opening = {'x': 50, 'y': 0, 'width': 100, 'height': 200}
        success, result = self.presenter.add_opening(opening)

        self.assertTrue(success)

    def test_select_opening(self):
        """Test selezione apertura"""
        self.presenter.set_openings([
            {'x': 50, 'y': 0, 'width': 100, 'height': 200}
        ])

        success = self.presenter.select_opening(0)
        self.assertTrue(success)
        self.assertEqual(self.presenter.get_selected_index(), 0)

    def test_remove_opening(self):
        """Test rimozione apertura"""
        self.presenter.set_openings([
            {'x': 50, 'y': 0, 'width': 100, 'height': 200}
        ])

        success = self.presenter.remove_opening(0)
        self.assertTrue(success)
        self.assertEqual(self.presenter.get_opening_count(), 0)


class TestOpeningsPresenterReinforcement(unittest.TestCase):
    """Test gestione rinforzi"""

    def setUp(self):
        self.presenter = OpeningsPresenter()
        self.presenter.set_wall_context({'length': 300, 'height': 270})
        self.presenter.set_openings([
            {'x': 50, 'y': 0, 'width': 100, 'height': 200, 'existing': False}
        ])

    def test_set_reinforcement_valid(self):
        """Test impostazione rinforzo valido"""
        rinforzo = {
            'tipo': 'telaio',
            'materiale': 'acciaio',
            'architrave': {'profilo': 'HEA 100'},
            'piedritti': {'profilo': 'HEA 100'}
        }

        result = self.presenter.set_reinforcement(0, rinforzo)
        self.assertTrue(result.is_valid)

    def test_set_reinforcement_invalid_material(self):
        """Test materiale non valido"""
        rinforzo = {
            'tipo': 'telaio',
            'materiale': 'legno'  # Non supportato
        }

        result = self.presenter.set_reinforcement(0, rinforzo)
        self.assertFalse(result.is_valid)

    def test_remove_reinforcement(self):
        """Test rimozione rinforzo"""
        rinforzo = {
            'tipo': 'telaio',
            'materiale': 'acciaio',
            'architrave': {'profilo': 'HEA 100'},
            'piedritti': {'profilo': 'HEA 100'}
        }
        self.presenter.set_reinforcement(0, rinforzo)

        success = self.presenter.remove_reinforcement(0)
        self.assertTrue(success)
        self.assertIsNone(self.presenter.get_reinforcement(0))


class TestOpeningsPresenterStats(unittest.TestCase):
    """Test statistiche"""

    def setUp(self):
        self.presenter = OpeningsPresenter()
        self.presenter.set_wall_context({'length': 300, 'height': 270})

    def test_calculate_stats_empty(self):
        """Test statistiche senza aperture"""
        stats = self.presenter.calculate_stats()

        self.assertEqual(stats.total_count, 0)
        self.assertEqual(stats.opening_ratio, 0)

    def test_calculate_stats_with_openings(self):
        """Test statistiche con aperture"""
        self.presenter.set_openings([
            {'x': 50, 'y': 0, 'width': 100, 'height': 200, 'existing': True},
            {'x': 200, 'y': 0, 'width': 80, 'height': 180, 'existing': False,
             'rinforzo': {'tipo': 'telaio', 'materiale': 'acciaio'}}
        ])

        stats = self.presenter.calculate_stats()

        self.assertEqual(stats.total_count, 2)
        self.assertEqual(stats.existing_count, 1)
        self.assertEqual(stats.new_count, 1)
        self.assertEqual(stats.reinforced_count, 1)
        self.assertGreater(stats.opening_ratio, 0)


# =============================================================================
# TEST CalcPresenter
# =============================================================================

class TestCalcPresenterInit(unittest.TestCase):
    """Test inizializzazione CalcPresenter"""

    def test_creation(self):
        """Test creazione"""
        presenter = CalcPresenter()
        self.assertIsNotNone(presenter)
        self.assertFalse(presenter.is_calculating())
        self.assertFalse(presenter.has_results())


class TestCalcPresenterCanCalculate(unittest.TestCase):
    """Test verifica possibilità calcolo"""

    def setUp(self):
        self.presenter = CalcPresenter()

    def test_cannot_calculate_empty(self):
        """Test impossibile calcolare senza dati"""
        can, reasons = self.presenter.can_calculate()
        self.assertFalse(can)
        self.assertGreater(len(reasons), 0)

    def test_can_calculate_with_data(self):
        """Test possibile calcolare con dati completi"""
        self.presenter.set_project_data({
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410},
            'openings': [],
            'loads': {'vertical': 100, 'eccentricity': 0}
        })

        can, reasons = self.presenter.can_calculate()
        self.assertTrue(can)


class TestCalcPresenterCalculation(unittest.TestCase):
    """Test esecuzione calcolo"""

    def setUp(self):
        self.presenter = CalcPresenter()
        self.presenter.set_project_data({
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410},
            'openings': [],
            'loads': {'vertical': 100, 'eccentricity': 0},
            'constraints': {'bottom': 'Incastro', 'top': 'Incastro (Grinter)'},
            'FC': 1.35
        })

    def test_run_calculation(self):
        """Test esecuzione calcolo"""
        completed = [False]

        def on_complete(result):
            completed[0] = True

        self.presenter.run_calculation(on_complete=on_complete)

        self.assertTrue(completed[0])
        self.assertTrue(self.presenter.has_results())

    def test_get_formatted_results(self):
        """Test risultati formattati"""
        self.presenter.run_calculation()

        results = self.presenter.get_formatted_results()

        self.assertIsNotNone(results)
        self.assertIn('original', results)
        self.assertIn('modified', results)
        self.assertIn('verification', results)

    def test_get_verification_result(self):
        """Test risultato verifica"""
        self.presenter.run_calculation()

        verification = self.presenter.get_verification_result()

        self.assertIsNotNone(verification)
        self.assertIn('is_local', verification)
        self.assertIn('delta_K', verification)
        self.assertIn('delta_V', verification)


class TestCalcPresenterExport(unittest.TestCase):
    """Test export risultati"""

    def setUp(self):
        self.presenter = CalcPresenter()
        self.presenter.set_project_data({
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.4, 'tau0': 0.074, 'E': 1410},
            'openings': [],
            'loads': {'vertical': 100, 'eccentricity': 0}
        })
        self.presenter.run_calculation()

    def test_export_summary(self):
        """Test export riepilogo"""
        summary = self.presenter.export_results(format='summary')

        self.assertIsNotNone(summary)
        self.assertIn('verifica', summary)
        self.assertIn('K_originale', summary)

    def test_export_detailed(self):
        """Test export dettagliato"""
        detailed = self.presenter.export_results(format='detailed')

        self.assertIsNotNone(detailed)
        self.assertIn('original', detailed)
        self.assertIn('modified', detailed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
