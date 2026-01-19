"""
Test per Data Layer - Database
==============================

Test unitari per:
- ProfilesDatabase (profili metallici EN 10365)
- MaterialsDatabase (materiali murari NTC 2018)

Arch. Michelangelo Bartolotta
"""

import unittest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database.profiles import (
    ProfilesDatabase,
    profiles_db,
    HEA_PROFILES,
    HEB_PROFILES,
    IPE_PROFILES,
    UPN_PROFILES,
    STEEL_GRADES,
    STEEL_PROFILES
)
from src.core.database.materials_database import MaterialsDatabase


# =============================================================================
# TEST ProfilesDatabase
# =============================================================================

class TestProfilesDatabaseData(unittest.TestCase):
    """Test per i dati statici dei profili"""

    def test_hea_profiles_exist(self):
        """Test che HEA profiles contiene dati"""
        self.assertGreater(len(HEA_PROFILES), 10)
        self.assertIn('160', HEA_PROFILES)
        self.assertIn('200', HEA_PROFILES)

    def test_heb_profiles_exist(self):
        """Test che HEB profiles contiene dati"""
        self.assertGreater(len(HEB_PROFILES), 10)
        self.assertIn('160', HEB_PROFILES)
        self.assertIn('200', HEB_PROFILES)

    def test_ipe_profiles_exist(self):
        """Test che IPE profiles contiene dati"""
        self.assertGreater(len(IPE_PROFILES), 10)
        self.assertIn('160', IPE_PROFILES)
        self.assertIn('200', IPE_PROFILES)

    def test_upn_profiles_exist(self):
        """Test che UPN profiles contiene dati"""
        self.assertGreater(len(UPN_PROFILES), 8)
        self.assertIn('160', UPN_PROFILES)
        self.assertIn('200', UPN_PROFILES)

    def test_steel_grades_exist(self):
        """Test classi acciaio"""
        self.assertIn('S235', STEEL_GRADES)
        self.assertIn('S275', STEEL_GRADES)
        self.assertIn('S355', STEEL_GRADES)

    def test_steel_grade_properties(self):
        """Test proprietà classi acciaio"""
        s235 = STEEL_GRADES['S235']
        self.assertEqual(s235['fyk'], 235)
        self.assertEqual(s235['E'], 210000)
        self.assertEqual(s235['gamma_m0'], 1.05)

    def test_profile_has_required_properties(self):
        """Test che ogni profilo ha le proprietà richieste"""
        required_keys = ['h', 'b', 'tw', 'tf', 'A', 'Ix', 'Iy', 'Wx', 'Wy']

        for ptype, profiles in STEEL_PROFILES.items():
            for size, data in profiles.items():
                for key in required_keys:
                    self.assertIn(key, data, f"{ptype} {size} manca {key}")

    def test_hea_160_values(self):
        """Test valori HEA 160 (riferimento)"""
        hea160 = HEA_PROFILES['160']
        self.assertEqual(hea160['h'], 152)
        self.assertEqual(hea160['b'], 160)
        self.assertAlmostEqual(hea160['Ix'], 1673, delta=5)

    def test_heb_200_values(self):
        """Test valori HEB 200 (riferimento)"""
        heb200 = HEB_PROFILES['200']
        self.assertEqual(heb200['h'], 200)
        self.assertEqual(heb200['b'], 200)
        self.assertAlmostEqual(heb200['Ix'], 5696, delta=5)


class TestProfilesDatabase(unittest.TestCase):
    """Test per ProfilesDatabase"""

    def setUp(self):
        self.db = ProfilesDatabase()

    def test_singleton_instance(self):
        """Test istanza globale profiles_db"""
        self.assertIsInstance(profiles_db, ProfilesDatabase)

    def test_get_available_types(self):
        """Test tipi profili disponibili"""
        types = self.db.get_available_types()
        self.assertIn('HEA', types)
        self.assertIn('HEB', types)
        self.assertIn('IPE', types)
        self.assertIn('UPN', types)
        self.assertEqual(len(types), 4)

    def test_get_available_sizes_hea(self):
        """Test dimensioni HEA disponibili"""
        sizes = self.db.get_available_sizes('HEA')
        self.assertIn('100', sizes)
        self.assertIn('160', sizes)
        self.assertIn('500', sizes)
        # Verifica ordine numerico
        self.assertEqual(sizes[0], '100')

    def test_get_available_sizes_invalid_type(self):
        """Test tipo profilo non valido"""
        sizes = self.db.get_available_sizes('INVALID')
        self.assertEqual(sizes, [])

    def test_get_profile_hea_160(self):
        """Test recupero profilo HEA 160"""
        profile = self.db.get_profile('HEA', '160')
        self.assertIsNotNone(profile)
        self.assertEqual(profile['h'], 152)
        self.assertEqual(profile['b'], 160)

    def test_get_profile_heb_200(self):
        """Test recupero profilo HEB 200"""
        profile = self.db.get_profile('HEB', '200')
        self.assertIsNotNone(profile)
        self.assertEqual(profile['h'], 200)
        self.assertEqual(profile['b'], 200)

    def test_get_profile_ipe_300(self):
        """Test recupero profilo IPE 300"""
        profile = self.db.get_profile('IPE', '300')
        self.assertIsNotNone(profile)
        self.assertEqual(profile['h'], 300)

    def test_get_profile_invalid_type(self):
        """Test tipo profilo non valido"""
        profile = self.db.get_profile('INVALID', '160')
        self.assertIsNone(profile)

    def test_get_profile_invalid_size(self):
        """Test dimensione profilo non valida"""
        profile = self.db.get_profile('HEA', '999')
        self.assertIsNone(profile)

    def test_get_steel_grade_s235(self):
        """Test classe acciaio S235"""
        grade = self.db.get_steel_grade('S235')
        self.assertIsNotNone(grade)
        self.assertEqual(grade['fyk'], 235)

    def test_get_steel_grade_s355(self):
        """Test classe acciaio S355"""
        grade = self.db.get_steel_grade('S355')
        self.assertIsNotNone(grade)
        self.assertEqual(grade['fyk'], 355)

    def test_get_steel_grade_invalid(self):
        """Test classe acciaio non valida"""
        grade = self.db.get_steel_grade('S999')
        self.assertIsNone(grade)

    def test_get_available_grades(self):
        """Test classi acciaio disponibili"""
        grades = self.db.get_available_grades()
        self.assertIn('S235', grades)
        self.assertIn('S355', grades)
        self.assertEqual(len(grades), 4)

    def test_get_profile_display_name(self):
        """Test nome visualizzazione profilo"""
        name = self.db.get_profile_display_name('HEA', '160')
        self.assertEqual(name, 'HEA 160')

    def test_search_profiles_min_wx(self):
        """Test ricerca profili per Wx minimo"""
        results = self.db.search_profiles(min_Wx=200)
        self.assertGreater(len(results), 0)
        # Tutti devono avere Wx >= 200
        for r in results:
            self.assertGreaterEqual(r['Wx'], 200)

    def test_search_profiles_min_ix(self):
        """Test ricerca profili per Ix minimo"""
        results = self.db.search_profiles(min_Ix=5000)
        self.assertGreater(len(results), 0)
        # Tutti devono avere Ix >= 5000
        for r in results:
            self.assertGreaterEqual(r['Ix'], 5000)

    def test_search_profiles_filter_types(self):
        """Test ricerca profili filtro per tipo"""
        results = self.db.search_profiles(min_Wx=100, profile_types=['HEA', 'HEB'])
        self.assertGreater(len(results), 0)
        # Solo HEA e HEB
        for r in results:
            self.assertIn(r['type'], ['HEA', 'HEB'])

    def test_search_profiles_sorted_by_wx(self):
        """Test risultati ordinati per Wx"""
        results = self.db.search_profiles(min_Wx=100)
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]['Wx'], results[i+1]['Wx'])

    def test_search_profiles_has_name(self):
        """Test risultati hanno nome"""
        results = self.db.search_profiles(min_Wx=200)
        for r in results:
            self.assertIn('name', r)
            self.assertTrue(r['name'])

    def test_get_optimal_profile(self):
        """Test profilo ottimale"""
        optimal = self.db.get_optimal_profile(required_Wx=200, required_Ix=3000)
        self.assertIsNotNone(optimal)
        self.assertGreaterEqual(optimal['Wx'], 200)
        self.assertGreaterEqual(optimal['Ix'], 3000)

    def test_get_optimal_profile_filter_types(self):
        """Test profilo ottimale con filtro tipi"""
        optimal = self.db.get_optimal_profile(
            required_Wx=200, required_Ix=3000,
            profile_types=['HEB']
        )
        self.assertIsNotNone(optimal)
        self.assertEqual(optimal['type'], 'HEB')

    def test_get_optimal_profile_no_match(self):
        """Test nessun profilo soddisfa requisiti"""
        optimal = self.db.get_optimal_profile(required_Wx=99999, required_Ix=99999)
        self.assertIsNone(optimal)


# =============================================================================
# TEST MaterialsDatabase
# =============================================================================

class TestMaterialsDatabase(unittest.TestCase):
    """Test per MaterialsDatabase"""

    def setUp(self):
        self.db = MaterialsDatabase()

    def test_normative_materials_loaded(self):
        """Test materiali normativi caricati"""
        materials = self.db.get_all_materials()
        self.assertGreater(len(materials), 5)

    def test_pietrame_disordinata_exists(self):
        """Test materiale pietrame disordinata"""
        material = self.db.get_material('pietrame_disordinata')
        self.assertIsNotNone(material)
        self.assertEqual(material['fcm'], 1.0)
        self.assertTrue(material['normative'])

    def test_mattoni_pieni_calce_exists(self):
        """Test materiale mattoni pieni e calce"""
        material = self.db.get_material('mattoni_pieni_calce')
        self.assertIsNotNone(material)
        self.assertEqual(material['fcm'], 2.4)
        self.assertEqual(material['category'], 'Mattoni')

    def test_blocchi_laterizio_exists(self):
        """Test materiale blocchi laterizi"""
        material = self.db.get_material('blocchi_laterizio')
        self.assertIsNotNone(material)
        self.assertEqual(material['fcm'], 5.0)

    def test_get_material_invalid(self):
        """Test materiale non esistente"""
        material = self.db.get_material('invalid_material')
        self.assertIsNone(material)

    def test_get_material_by_name(self):
        """Test recupero per nome"""
        material = self.db.get_material_by_name('Muratura in pietrame disordinata')
        self.assertIsNotNone(material)
        self.assertEqual(material['fcm'], 1.0)

    def test_get_material_by_name_invalid(self):
        """Test nome non esistente"""
        material = self.db.get_material_by_name('Nome Inesistente')
        self.assertIsNone(material)

    def test_get_all_materials(self):
        """Test tutti i materiali"""
        materials = self.db.get_all_materials()
        self.assertIsInstance(materials, dict)
        self.assertIn('pietrame_disordinata', materials)
        self.assertIn('mattoni_pieni_calce', materials)

    def test_get_categories(self):
        """Test categorie disponibili"""
        categories = self.db.get_categories()
        self.assertIn('Pietrame', categories)
        self.assertIn('Mattoni', categories)
        self.assertIn('Blocchi', categories)

    def test_categories_sorted(self):
        """Test categorie ordinate"""
        categories = self.db.get_categories()
        self.assertEqual(categories, sorted(categories))

    def test_get_display_list(self):
        """Test lista visualizzazione"""
        display_list = self.db.get_display_list()
        self.assertGreater(len(display_list), 5)
        # Ultimo elemento è l'opzione per aggiungere
        self.assertEqual(display_list[-1], "--- Aggiungi materiale personalizzato ---")

    def test_material_has_required_properties(self):
        """Test proprietà obbligatorie"""
        required_keys = ['name', 'category', 'fcm', 'tau0', 'E', 'G', 'w']

        for key, material in self.db.materials.items():
            for prop in required_keys:
                self.assertIn(prop, material, f"Materiale {key} manca {prop}")

    def test_material_values_in_range(self):
        """Test valori in range ragionevoli"""
        for key, material in self.db.materials.items():
            # fcm tipicamente 0.5-10 MPa per murature
            self.assertGreater(material['fcm'], 0)
            self.assertLess(material['fcm'], 20)

            # tau0 tipicamente 0.01-0.2 MPa
            self.assertGreater(material['tau0'], 0)
            self.assertLess(material['tau0'], 1.0)

            # E tipicamente 500-5000 MPa
            self.assertGreater(material['E'], 100)
            self.assertLess(material['E'], 10000)

            # Peso specifico 10-25 kN/m³
            self.assertGreater(material['w'], 5)
            self.assertLess(material['w'], 30)


class TestMaterialsDatabaseCustom(unittest.TestCase):
    """Test per materiali personalizzati"""

    def setUp(self):
        self.db = MaterialsDatabase()
        # Usa path temporaneo per test
        self.temp_dir = tempfile.mkdtemp()
        self.db.custom_db_path = os.path.join(self.temp_dir, 'custom_test.json')

    def tearDown(self):
        # Pulisce file temporanei
        if os.path.exists(self.db.custom_db_path):
            os.remove(self.db.custom_db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_add_custom_material(self):
        """Test aggiunta materiale personalizzato"""
        custom_data = {
            'name': 'Test Custom Material',
            'category': 'Test',
            'fcm': 3.0,
            'tau0': 0.070,
            'E': 2000,
            'G': 666,
            'w': 19.0
        }

        result = self.db.add_custom_material('test_custom', custom_data)
        self.assertTrue(result)

        # Verifica che sia stato aggiunto
        material = self.db.get_material('test_custom')
        self.assertIsNotNone(material)
        self.assertEqual(material['name'], 'Test Custom Material')
        self.assertTrue(material['custom'])
        self.assertFalse(material['normative'])

    def test_add_custom_material_duplicate(self):
        """Test aggiunta materiale con chiave esistente"""
        # Prima aggiunta
        self.db.add_custom_material('test_dup', {
            'name': 'Test 1', 'category': 'Test',
            'fcm': 1.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        # Seconda aggiunta con stessa chiave
        result = self.db.add_custom_material('test_dup', {
            'name': 'Test 2', 'category': 'Test',
            'fcm': 2.0, 'tau0': 0.02, 'E': 2000, 'G': 666, 'w': 18.0
        })

        self.assertFalse(result)

    def test_update_custom_material(self):
        """Test aggiornamento materiale personalizzato"""
        # Aggiungi
        self.db.add_custom_material('test_update', {
            'name': 'Original', 'category': 'Test',
            'fcm': 1.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        # Aggiorna
        result = self.db.update_custom_material('test_update', {
            'name': 'Updated', 'category': 'Test',
            'fcm': 2.0, 'tau0': 0.02, 'E': 2000, 'G': 666, 'w': 19.0
        })

        self.assertTrue(result)
        material = self.db.get_material('test_update')
        self.assertEqual(material['name'], 'Updated')
        self.assertEqual(material['fcm'], 2.0)

    def test_update_normative_material_fails(self):
        """Test che non si possono aggiornare materiali normativi"""
        result = self.db.update_custom_material('pietrame_disordinata', {
            'name': 'Hacked', 'category': 'Test',
            'fcm': 99.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        self.assertFalse(result)
        # Materiale originale non modificato
        material = self.db.get_material('pietrame_disordinata')
        self.assertEqual(material['fcm'], 1.0)

    def test_delete_custom_material(self):
        """Test eliminazione materiale personalizzato"""
        # Aggiungi
        self.db.add_custom_material('test_delete', {
            'name': 'To Delete', 'category': 'Test',
            'fcm': 1.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        # Elimina
        result = self.db.delete_custom_material('test_delete')
        self.assertTrue(result)

        # Verifica eliminazione
        material = self.db.get_material('test_delete')
        self.assertIsNone(material)

    def test_delete_normative_material_fails(self):
        """Test che non si possono eliminare materiali normativi"""
        result = self.db.delete_custom_material('pietrame_disordinata')
        self.assertFalse(result)

        # Materiale ancora presente
        material = self.db.get_material('pietrame_disordinata')
        self.assertIsNotNone(material)

    def test_delete_nonexistent_material(self):
        """Test eliminazione materiale non esistente"""
        result = self.db.delete_custom_material('nonexistent_key')
        self.assertFalse(result)

    def test_save_and_load_custom_materials(self):
        """Test salvataggio e caricamento materiali custom"""
        # Aggiungi materiale
        self.db.add_custom_material('test_persist', {
            'name': 'Persistent Material', 'category': 'Test',
            'fcm': 2.5, 'tau0': 0.05, 'E': 1500, 'G': 500, 'w': 18.5
        })

        # Crea nuovo database (simula riavvio)
        db2 = MaterialsDatabase()
        db2.custom_db_path = self.db.custom_db_path
        db2.load_custom_materials()

        # Verifica persistenza
        material = db2.get_material('test_persist')
        self.assertIsNotNone(material)
        self.assertEqual(material['name'], 'Persistent Material')

    def test_custom_in_display_list(self):
        """Test materiali custom nella lista visualizzazione"""
        # Aggiungi materiale custom
        self.db.add_custom_material('test_display', {
            'name': 'Display Test', 'category': 'Test',
            'fcm': 1.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        display_list = self.db.get_display_list()
        # Deve contenere con suffisso [Personalizzato]
        self.assertIn('Display Test [Personalizzato]', display_list)

    def test_get_material_by_name_strips_custom_suffix(self):
        """Test che get_material_by_name rimuove suffisso [Personalizzato]"""
        self.db.add_custom_material('test_suffix', {
            'name': 'Suffix Test', 'category': 'Test',
            'fcm': 1.0, 'tau0': 0.01, 'E': 1000, 'G': 333, 'w': 18.0
        })

        # Cerca con suffisso
        material = self.db.get_material_by_name('Suffix Test [Personalizzato]')
        self.assertIsNotNone(material)
        self.assertEqual(material['name'], 'Suffix Test')


# =============================================================================
# TEST INTEGRAZIONE
# =============================================================================

class TestDatabaseIntegration(unittest.TestCase):
    """Test integrazione database"""

    def test_profiles_and_materials_independent(self):
        """Test che database sono indipendenti"""
        profiles = ProfilesDatabase()
        materials = MaterialsDatabase()

        # Modifica uno non influenza l'altro
        profile = profiles.get_profile('HEA', '160')
        material = materials.get_material('mattoni_pieni_calce')

        self.assertIsNotNone(profile)
        self.assertIsNotNone(material)
        self.assertNotEqual(profile, material)

    def test_profile_for_reinforcement_calculation(self):
        """Test profilo per calcolo rinforzo"""
        db = ProfilesDatabase()

        # Scenario: architrave L=200cm, momento 50kNm
        # Wx richiesto approssimativo con S235: 50*1e6 / (235/1.05) ≈ 223 cm³
        optimal = db.get_optimal_profile(
            required_Wx=223,
            required_Ix=1000,
            profile_types=['HEA', 'HEB', 'IPE']
        )

        self.assertIsNotNone(optimal)
        self.assertGreaterEqual(optimal['Wx'], 223)

    def test_material_for_wall_calculation(self):
        """Test materiale per calcolo parete"""
        db = MaterialsDatabase()

        # Scenario: verifica parete in mattoni
        material = db.get_material('mattoni_pieni_calce')

        # Calcolo resistenza con fattore sicurezza
        fd = material['fcm'] / 2.0  # FC=2 per LC1
        tau_d = material['tau0'] / 2.0

        self.assertGreater(fd, 0)
        self.assertGreater(tau_d, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
