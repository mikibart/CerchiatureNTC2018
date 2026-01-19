"""
Test per Models Layer
=====================

Test unitari per:
- Wall (modello parete)
- Opening (modello apertura)
- Reinforcement (modelli rinforzo acciaio e C.A.)
- Project (modello progetto)

Arch. Michelangelo Bartolotta
"""

import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.models.wall import Wall
from src.core.models.opening import Opening
from src.core.models.reinforcement import SteelReinforcement, ConcreteReinforcement
from src.core.models.project import Project, ProjectInfo


# =============================================================================
# TEST Wall
# =============================================================================

class TestWall(unittest.TestCase):
    """Test per Wall model"""

    def test_create_wall(self):
        """Test creazione muro"""
        wall = Wall(length=300, height=280, thickness=30)
        self.assertEqual(wall.length, 300)
        self.assertEqual(wall.height, 280)
        self.assertEqual(wall.thickness, 30)

    def test_wall_default_values(self):
        """Test valori default"""
        wall = Wall(length=300, height=280, thickness=30)
        self.assertEqual(wall.material_type, "blocchi")
        self.assertEqual(wall.knowledge_level, "LC1")

    def test_wall_custom_material(self):
        """Test materiale personalizzato"""
        wall = Wall(
            length=300, height=280, thickness=30,
            material_type="mattoni_pieni_calce"
        )
        self.assertEqual(wall.material_type, "mattoni_pieni_calce")

    def test_wall_knowledge_level(self):
        """Test livello di conoscenza"""
        wall = Wall(
            length=300, height=280, thickness=30,
            knowledge_level="LC2"
        )
        self.assertEqual(wall.knowledge_level, "LC2")

    def test_wall_area(self):
        """Test calcolo area sezione"""
        wall = Wall(length=300, height=280, thickness=30)
        expected_area = 300 * 30  # length * thickness
        self.assertEqual(wall.area, expected_area)

    def test_wall_area_large(self):
        """Test area sezione muro grande"""
        wall = Wall(length=500, height=400, thickness=45)
        self.assertEqual(wall.area, 500 * 45)

    def test_wall_dimensions_positive(self):
        """Test dimensioni positive"""
        wall = Wall(length=100, height=200, thickness=20)
        self.assertGreater(wall.length, 0)
        self.assertGreater(wall.height, 0)
        self.assertGreater(wall.thickness, 0)


# =============================================================================
# TEST Opening
# =============================================================================

class TestOpening(unittest.TestCase):
    """Test per Opening model"""

    def test_create_opening(self):
        """Test creazione apertura"""
        opening = Opening(width=100, height=200, x=50, y=0)
        self.assertEqual(opening.width, 100)
        self.assertEqual(opening.height, 200)
        self.assertEqual(opening.x, 50)
        self.assertEqual(opening.y, 0)

    def test_opening_default_values(self):
        """Test valori default"""
        opening = Opening(width=100, height=200, x=50, y=0)
        self.assertEqual(opening.opening_type, "rectangular")
        self.assertFalse(opening.is_existing)
        self.assertIsNone(opening.reinforcement)

    def test_opening_existing(self):
        """Test apertura esistente"""
        opening = Opening(
            width=100, height=200, x=50, y=0,
            is_existing=True
        )
        self.assertTrue(opening.is_existing)

    def test_opening_type_arch(self):
        """Test apertura ad arco"""
        opening = Opening(
            width=100, height=200, x=50, y=0,
            opening_type="arch"
        )
        self.assertEqual(opening.opening_type, "arch")

    def test_opening_position(self):
        """Test posizione apertura"""
        opening = Opening(width=100, height=200, x=150, y=50)
        self.assertEqual(opening.x, 150)
        self.assertEqual(opening.y, 50)

    def test_opening_door(self):
        """Test porta (y=0)"""
        door = Opening(width=90, height=210, x=100, y=0)
        self.assertEqual(door.y, 0)  # Porta a livello terra

    def test_opening_window(self):
        """Test finestra (y>0)"""
        window = Opening(width=120, height=140, x=100, y=80)
        self.assertGreater(window.y, 0)  # Finestra rialzata


# =============================================================================
# TEST SteelReinforcement
# =============================================================================

class TestSteelReinforcement(unittest.TestCase):
    """Test per SteelReinforcement model"""

    def test_create_steel_reinforcement(self):
        """Test creazione rinforzo acciaio"""
        reinforcement = SteelReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.intervention_type, "frame")

    def test_steel_default_grade(self):
        """Test classe acciaio default"""
        reinforcement = SteelReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.steel_grade, "S235")

    def test_steel_custom_grade(self):
        """Test classe acciaio personalizzata"""
        reinforcement = SteelReinforcement(
            intervention_type="frame",
            steel_grade="S355"
        )
        self.assertEqual(reinforcement.steel_grade, "S355")

    def test_steel_profiles(self):
        """Test profili personalizzati"""
        reinforcement = SteelReinforcement(
            intervention_type="frame",
            profiles={
                'architrave': ['HEA 160'],
                'piedritti': ['HEA 160']
            }
        )
        self.assertIn('architrave', reinforcement.profiles)
        self.assertEqual(reinforcement.profiles['architrave'], ['HEA 160'])

    def test_steel_lintel_type(self):
        """Test tipo architrave"""
        reinforcement = SteelReinforcement(intervention_type="lintel")
        self.assertEqual(reinforcement.intervention_type, "lintel")

    def test_steel_arch_type(self):
        """Test tipo arco"""
        reinforcement = SteelReinforcement(intervention_type="arch")
        self.assertEqual(reinforcement.intervention_type, "arch")

    def test_steel_profiles_default_none(self):
        """Test profili default None"""
        reinforcement = SteelReinforcement(intervention_type="frame")
        self.assertIsNone(reinforcement.profiles)


# =============================================================================
# TEST ConcreteReinforcement
# =============================================================================

class TestConcreteReinforcement(unittest.TestCase):
    """Test per ConcreteReinforcement model"""

    def test_create_concrete_reinforcement(self):
        """Test creazione rinforzo C.A."""
        reinforcement = ConcreteReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.intervention_type, "frame")

    def test_concrete_default_class(self):
        """Test classe calcestruzzo default"""
        reinforcement = ConcreteReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.concrete_class, "C25/30")

    def test_concrete_custom_class(self):
        """Test classe calcestruzzo personalizzata"""
        reinforcement = ConcreteReinforcement(
            intervention_type="frame",
            concrete_class="C30/37"
        )
        self.assertEqual(reinforcement.concrete_class, "C30/37")

    def test_concrete_default_dimensions(self):
        """Test dimensioni default"""
        reinforcement = ConcreteReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.width, 30.0)
        self.assertEqual(reinforcement.height, 30.0)

    def test_concrete_custom_dimensions(self):
        """Test dimensioni personalizzate"""
        reinforcement = ConcreteReinforcement(
            intervention_type="frame",
            width=40.0,
            height=50.0
        )
        self.assertEqual(reinforcement.width, 40.0)
        self.assertEqual(reinforcement.height, 50.0)

    def test_concrete_default_rebar(self):
        """Test armatura default"""
        reinforcement = ConcreteReinforcement(intervention_type="frame")
        self.assertEqual(reinforcement.rebar_diameter, 16)
        self.assertEqual(reinforcement.rebar_count, 4)

    def test_concrete_custom_rebar(self):
        """Test armatura personalizzata"""
        reinforcement = ConcreteReinforcement(
            intervention_type="frame",
            rebar_diameter=20,
            rebar_count=6
        )
        self.assertEqual(reinforcement.rebar_diameter, 20)
        self.assertEqual(reinforcement.rebar_count, 6)

    def test_concrete_lintel_type(self):
        """Test tipo architrave C.A."""
        reinforcement = ConcreteReinforcement(intervention_type="lintel")
        self.assertEqual(reinforcement.intervention_type, "lintel")


# =============================================================================
# TEST ProjectInfo
# =============================================================================

class TestProjectInfo(unittest.TestCase):
    """Test per ProjectInfo model"""

    def test_create_project_info(self):
        """Test creazione info progetto"""
        info = ProjectInfo()
        self.assertIsNotNone(info)

    def test_project_info_defaults(self):
        """Test valori default"""
        info = ProjectInfo()
        self.assertEqual(info.name, "")
        self.assertEqual(info.location, "")
        self.assertEqual(info.client, "")
        self.assertEqual(info.engineer, "Arch. Michelangelo Bartolotta")

    def test_project_info_custom(self):
        """Test valori personalizzati"""
        info = ProjectInfo(
            name="Progetto Test",
            location="Roma, Via Test 123",
            client="Cliente Test",
            engineer="Ing. Test"
        )
        self.assertEqual(info.name, "Progetto Test")
        self.assertEqual(info.location, "Roma, Via Test 123")
        self.assertEqual(info.client, "Cliente Test")
        self.assertEqual(info.engineer, "Ing. Test")

    def test_project_info_date(self):
        """Test data progetto"""
        info = ProjectInfo()
        self.assertIsInstance(info.date, datetime)
        # Data deve essere recente
        now = datetime.now()
        diff = now - info.date
        self.assertLess(diff.total_seconds(), 60)  # Meno di 60 secondi


# =============================================================================
# TEST Project
# =============================================================================

class TestProject(unittest.TestCase):
    """Test per Project model"""

    def test_create_project(self):
        """Test creazione progetto"""
        project = Project()
        self.assertIsNotNone(project)

    def test_project_default_info(self):
        """Test info default"""
        project = Project()
        self.assertIsInstance(project.info, ProjectInfo)

    def test_project_custom_info(self):
        """Test info personalizzata"""
        info = ProjectInfo(name="Test Project")
        project = Project(info=info)
        self.assertEqual(project.info.name, "Test Project")

    def test_project_wall(self):
        """Test muro progetto"""
        project = Project()
        self.assertIsNone(project.wall)

        wall = Wall(length=300, height=280, thickness=30)
        project.wall = wall
        self.assertIsNotNone(project.wall)
        self.assertEqual(project.wall.length, 300)

    def test_project_openings_default(self):
        """Test aperture default"""
        project = Project()
        self.assertIsInstance(project.openings, list)
        self.assertEqual(len(project.openings), 0)

    def test_project_add_opening(self):
        """Test aggiunta apertura"""
        project = Project()
        opening = Opening(width=100, height=200, x=50, y=0)
        project.openings.append(opening)
        self.assertEqual(len(project.openings), 1)

    def test_project_multiple_openings(self):
        """Test aperture multiple"""
        project = Project()
        project.openings.append(Opening(width=100, height=200, x=50, y=0))
        project.openings.append(Opening(width=120, height=140, x=200, y=80))
        self.assertEqual(len(project.openings), 2)

    def test_project_materials_default(self):
        """Test materiali default"""
        project = Project()
        self.assertIsInstance(project.materials, dict)
        self.assertEqual(len(project.materials), 0)

    def test_project_loads_default(self):
        """Test carichi default"""
        project = Project()
        self.assertIsInstance(project.loads, dict)
        self.assertEqual(len(project.loads), 0)

    def test_project_results_default(self):
        """Test risultati default"""
        project = Project()
        self.assertIsNone(project.results)

    def test_project_version(self):
        """Test versione progetto"""
        project = Project()
        self.assertEqual(project.version, "1.0")


# =============================================================================
# TEST INTEGRAZIONE MODELS
# =============================================================================

class TestModelsIntegration(unittest.TestCase):
    """Test integrazione Models"""

    def test_full_project_workflow(self):
        """Test workflow completo progetto"""
        # Crea progetto
        project = Project(
            info=ProjectInfo(
                name="Edificio Residenziale",
                location="Roma",
                client="Mario Rossi"
            )
        )

        # Aggiungi muro
        project.wall = Wall(
            length=400,
            height=300,
            thickness=30,
            material_type="mattoni_pieni_calce"
        )

        # Aggiungi aperture
        # Porta
        door = Opening(width=90, height=210, x=50, y=0, is_existing=True)
        project.openings.append(door)

        # Finestra
        window = Opening(width=120, height=140, x=250, y=80)
        project.openings.append(window)

        # Aggiungi materiali
        project.materials = {
            'muratura': {
                'fcm': 2.4,
                'tau0': 0.060,
                'E': 1500
            }
        }

        # Verifica
        self.assertEqual(project.info.name, "Edificio Residenziale")
        self.assertEqual(project.wall.length, 400)
        self.assertEqual(len(project.openings), 2)
        self.assertTrue(project.openings[0].is_existing)
        self.assertIn('muratura', project.materials)

    def test_opening_with_steel_reinforcement(self):
        """Test apertura con rinforzo acciaio"""
        reinforcement = SteelReinforcement(
            intervention_type="frame",
            steel_grade="S235",
            profiles={'architrave': ['HEA 160'], 'piedritti': ['HEA 160']}
        )

        opening = Opening(
            width=100, height=200, x=50, y=0,
            reinforcement=reinforcement
        )

        self.assertIsNotNone(opening.reinforcement)
        self.assertEqual(opening.reinforcement.intervention_type, "frame")
        self.assertEqual(opening.reinforcement.steel_grade, "S235")

    def test_opening_with_concrete_reinforcement(self):
        """Test apertura con rinforzo C.A."""
        reinforcement = ConcreteReinforcement(
            intervention_type="frame",
            concrete_class="C25/30",
            width=30,
            height=40,
            rebar_diameter=16,
            rebar_count=4
        )

        opening = Opening(
            width=100, height=200, x=50, y=0,
            reinforcement=reinforcement
        )

        self.assertIsNotNone(opening.reinforcement)
        self.assertEqual(opening.reinforcement.concrete_class, "C25/30")
        self.assertEqual(opening.reinforcement.rebar_diameter, 16)

    def test_wall_area_for_verification(self):
        """Test area muro per verifiche"""
        wall = Wall(length=400, height=300, thickness=30)

        # Area sezione orizzontale (per verifica taglio)
        area_section = wall.area  # cm²
        self.assertEqual(area_section, 400 * 30)

        # Area parete totale (per foratura)
        area_wall = wall.length * wall.height  # cm²
        self.assertEqual(area_wall, 400 * 300)

    def test_multiple_openings_in_wall(self):
        """Test aperture multiple con verifica maschi"""
        wall = Wall(length=500, height=300, thickness=30)

        # Aperture
        openings = [
            Opening(width=100, height=200, x=50, y=0),   # Maschio iniziale: 50cm
            Opening(width=100, height=200, x=200, y=0),  # Maschio: 50cm
            Opening(width=100, height=200, x=350, y=0)   # Maschio finale: 50cm
        ]

        # Calcola maschi murari
        maschi = []
        maschi.append(openings[0].x)  # Maschio iniziale

        for i in range(len(openings) - 1):
            maschio = openings[i+1].x - (openings[i].x + openings[i].width)
            maschi.append(maschio)

        maschi.append(wall.length - (openings[-1].x + openings[-1].width))  # Finale

        # Verifica maschi
        for m in maschi:
            self.assertGreaterEqual(m, 50)  # Minimo 50cm

    def test_project_serialization_ready(self):
        """Test che progetto sia pronto per serializzazione"""
        project = Project(
            info=ProjectInfo(name="Test", location="Roma")
        )
        project.wall = Wall(length=300, height=280, thickness=30)
        project.openings.append(Opening(width=100, height=200, x=50, y=0))

        # Verifica che tutti gli attributi siano serializzabili
        # (niente lambda, funzioni, etc.)
        self.assertIsInstance(project.info.name, str)
        self.assertIsInstance(project.wall.length, (int, float))
        self.assertIsInstance(project.openings, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
