"""
Test per ProjectService
"""

import unittest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.project_service import ProjectService, ProjectInfo, ProjectState
from src.data.ntc2018_constants import NTC2018


class TestProjectState(unittest.TestCase):
    """Test classe ProjectState"""

    def test_default_values(self):
        """Test valori default"""
        state = ProjectState()
        self.assertFalse(state.is_modified)
        self.assertTrue(state.is_new)
        self.assertIsNone(state.last_saved)


class TestProjectServiceInit(unittest.TestCase):
    """Test inizializzazione service"""

    def test_service_creation(self):
        """Test creazione service"""
        service = ProjectService()
        self.assertIsNotNone(service.state)

    def test_version(self):
        """Test versione"""
        self.assertEqual(ProjectService.VERSION, "1.0.0")

    def test_file_extension(self):
        """Test estensione file"""
        self.assertEqual(ProjectService.FILE_EXTENSION, ".cerch")


class TestProjectServiceNewProject(unittest.TestCase):
    """Test creazione nuovo progetto"""

    def setUp(self):
        self.service = ProjectService()

    def test_new_project_structure(self):
        """Test struttura nuovo progetto"""
        project = self.service.new_project()

        self.assertIn('info', project)
        self.assertIn('wall', project)
        self.assertIn('masonry', project)
        self.assertIn('loads', project)
        self.assertIn('constraints', project)
        self.assertIn('FC', project)
        self.assertIn('openings', project)

    def test_new_project_wall_defaults(self):
        """Test default parete"""
        project = self.service.new_project()
        wall = project['wall']

        self.assertEqual(wall['length'], 300)
        self.assertEqual(wall['height'], 270)
        self.assertEqual(wall['thickness'], 30)

    def test_new_project_masonry_defaults(self):
        """Test default muratura"""
        project = self.service.new_project()
        masonry = project['masonry']

        self.assertEqual(masonry['fcm'], 2.4)
        self.assertEqual(masonry['tau0'], 0.074)
        self.assertEqual(masonry['E'], 1410)

    def test_new_project_fc_default(self):
        """Test FC default (LC1)"""
        project = self.service.new_project()
        self.assertEqual(project['FC'], NTC2018.FC.LC1)

    def test_new_project_empty_openings(self):
        """Test aperture vuote"""
        project = self.service.new_project()
        self.assertEqual(len(project['openings']), 0)

    def test_new_project_name(self):
        """Test nome progetto"""
        project = self.service.new_project("Test Project")
        self.assertEqual(project['info']['name'], "Test Project")

    def test_new_project_state(self):
        """Test stato dopo creazione"""
        self.service.new_project()

        self.assertFalse(self.service.state.is_modified)
        self.assertTrue(self.service.state.is_new)


class TestProjectServiceSaveLoad(unittest.TestCase):
    """Test salvataggio e caricamento"""

    def setUp(self):
        self.service = ProjectService()
        self.temp_dir = tempfile.mkdtemp()

    def test_save_project(self):
        """Test salvataggio progetto"""
        project = self.service.new_project("Test Save")
        file_path = os.path.join(self.temp_dir, "test.cerch")

        result = self.service.save_project(project, file_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))

    def test_save_adds_extension(self):
        """Test aggiunta estensione automatica"""
        project = self.service.new_project()
        file_path = os.path.join(self.temp_dir, "test_no_ext")

        self.service.save_project(project, file_path)

        expected_path = file_path + ".cerch"
        self.assertTrue(os.path.exists(expected_path))

    def test_save_updates_state(self):
        """Test aggiornamento stato dopo salvataggio"""
        project = self.service.new_project()
        file_path = os.path.join(self.temp_dir, "test.cerch")

        self.service.save_project(project, file_path)

        self.assertFalse(self.service.state.is_modified)
        self.assertFalse(self.service.state.is_new)

    def test_load_project(self):
        """Test caricamento progetto"""
        # Prima salva
        project = self.service.new_project("Test Load")
        project['wall']['length'] = 500
        file_path = os.path.join(self.temp_dir, "test.cerch")
        self.service.save_project(project, file_path)

        # Poi carica
        loaded = self.service.load_project(file_path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['wall']['length'], 500)

    def test_load_nonexistent_file(self):
        """Test caricamento file inesistente"""
        loaded = self.service.load_project("nonexistent.cerch")
        self.assertIsNone(loaded)

    def test_load_invalid_json(self):
        """Test caricamento JSON invalido"""
        file_path = os.path.join(self.temp_dir, "invalid.cerch")
        with open(file_path, 'w') as f:
            f.write("not valid json {{{")

        loaded = self.service.load_project(file_path)
        self.assertIsNone(loaded)


class TestProjectServiceMigration(unittest.TestCase):
    """Test migrazione progetti vecchi"""

    def setUp(self):
        self.service = ProjectService()

    def test_migrate_adds_constraints(self):
        """Test migrazione aggiunge vincoli"""
        old_project = {
            '_format_version': '1.0',
            'wall': {'length': 300, 'height': 270, 'thickness': 30}
        }

        migrated = self.service._migrate_project(old_project)

        self.assertIn('constraints', migrated)
        self.assertEqual(migrated['constraints']['bottom'], 'Incastro')

    def test_migrate_adds_fc(self):
        """Test migrazione aggiunge FC"""
        old_project = {
            '_format_version': '1.0',
            'masonry': {'knowledge_level': 'LC2'}
        }

        migrated = self.service._migrate_project(old_project)

        self.assertIn('FC', migrated)
        self.assertEqual(migrated['FC'], 1.20)  # LC2

    def test_migrate_openings_module(self):
        """Test migrazione openings_module -> openings"""
        old_project = {
            '_format_version': '1.0',
            'openings_module': {
                'openings': [{'x': 100, 'width': 100}]
            }
        }

        migrated = self.service._migrate_project(old_project)

        self.assertIn('openings', migrated)
        self.assertEqual(len(migrated['openings']), 1)


class TestProjectServiceValidation(unittest.TestCase):
    """Test validazione progetto"""

    def setUp(self):
        self.service = ProjectService()

    def test_validate_valid_project(self):
        """Test progetto valido"""
        project = self.service.new_project()
        errors = self.service.validate_project(project)

        self.assertEqual(len(errors), 0)

    def test_validate_missing_wall(self):
        """Test parete mancante"""
        project = {'masonry': {'fcm': 2.0, 'tau0': 0.074}}
        errors = self.service.validate_project(project)

        self.assertGreater(len(errors), 0)
        self.assertTrue(any('wall' in e.lower() for e in errors))

    def test_validate_negative_dimension(self):
        """Test dimensione negativa"""
        project = {
            'wall': {'length': -100, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.0, 'tau0': 0.074}
        }
        errors = self.service.validate_project(project)

        self.assertGreater(len(errors), 0)

    def test_validate_missing_masonry_param(self):
        """Test parametro muratura mancante"""
        project = {
            'wall': {'length': 300, 'height': 270, 'thickness': 30},
            'masonry': {'fcm': 2.0}  # manca tau0
        }
        errors = self.service.validate_project(project)

        self.assertGreater(len(errors), 0)


class TestProjectServiceModified(unittest.TestCase):
    """Test tracciamento modifiche"""

    def setUp(self):
        self.service = ProjectService()

    def test_mark_modified(self):
        """Test segnare come modificato"""
        self.service.new_project()
        self.assertFalse(self.service.is_modified())

        self.service.mark_modified()
        self.assertTrue(self.service.is_modified())

    def test_save_clears_modified(self):
        """Test salvataggio azzera modified"""
        project = self.service.new_project()
        self.service.mark_modified()

        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "test.cerch")
        self.service.save_project(project, file_path)

        self.assertFalse(self.service.is_modified())


class TestProjectServiceSummary(unittest.TestCase):
    """Test riepilogo progetto"""

    def setUp(self):
        self.service = ProjectService()

    def test_get_summary(self):
        """Test generazione riepilogo"""
        project = self.service.new_project("Test Summary")
        project['openings'] = [
            {'x': 50, 'existing': True},
            {'x': 150, 'existing': False, 'rinforzo': {'tipo': 'telaio'}}
        ]

        summary = self.service.get_project_summary(project)

        self.assertEqual(summary['name'], "Test Summary")
        self.assertEqual(summary['total_openings'], 2)
        self.assertEqual(summary['existing_openings'], 1)
        self.assertEqual(summary['new_openings'], 1)
        self.assertEqual(summary['reinforced_openings'], 1)


class TestProjectServiceExport(unittest.TestCase):
    """Test esportazione progetto"""

    def setUp(self):
        self.service = ProjectService()

    def test_export_to_dict(self):
        """Test esportazione a dizionario"""
        project = self.service.new_project()
        project['results'] = {'K': 1000, 'V': 50}

        exported = self.service.export_to_dict(project)

        self.assertIn('wall', exported)
        self.assertIn('masonry', exported)
        self.assertIn('results', exported)

    def test_export_without_results(self):
        """Test esportazione senza risultati"""
        project = self.service.new_project()
        project['results'] = {'K': 1000}

        exported = self.service.export_to_dict(project, include_results=False)

        self.assertNotIn('results', exported)


if __name__ == '__main__':
    unittest.main(verbosity=2)
