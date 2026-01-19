"""
Test per modulo geometria muratura
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine.masonry.geometry import MasonryGeometry, MaschiMurari, Maschio


class TestMaschio(unittest.TestCase):
    """Test classe Maschio"""

    def test_maschio_creation(self):
        """Test creazione maschio"""
        m = Maschio(start=0, end=100, length=100, index=0)
        self.assertEqual(m.length, 100)
        self.assertEqual(m.length_m, 1.0)
        self.assertEqual(m.center, 50)


class TestMaschiMurari(unittest.TestCase):
    """Test classe MaschiMurari"""

    def test_empty_collection(self):
        """Test collezione vuota"""
        mm = MaschiMurari()
        self.assertEqual(len(mm), 0)
        self.assertEqual(mm.foratura_ratio, 0)

    def test_foratura_ratio(self):
        """Test calcolo rapporto foratura"""
        mm = MaschiMurari(
            wall_length=300,
            total_length=200,
            opening_length=100
        )
        self.assertAlmostEqual(mm.foratura_ratio, 100/300)
        self.assertAlmostEqual(mm.maschi_ratio, 200/300)


class TestMasonryGeometryCalculations(unittest.TestCase):
    """Test calcoli geometrici"""

    def test_calculate_area(self):
        """Test calcolo area"""
        # 200 cm x 30 cm = 2m x 0.3m = 0.6 m²
        area = MasonryGeometry.calculate_area(200, 30)
        self.assertAlmostEqual(area, 0.6)

    def test_calculate_moment_of_inertia(self):
        """Test calcolo momento inerzia"""
        # I = t * L³ / 12 = 0.3 * 2³ / 12 = 0.3 * 8 / 12 = 0.2 m⁴
        I = MasonryGeometry.calculate_moment_of_inertia(200, 30)
        self.assertAlmostEqual(I, 0.2, places=5)

    def test_slenderness(self):
        """Test calcolo snellezza"""
        # λ = h/t = 270/30 = 9
        slenderness = MasonryGeometry.calculate_slenderness(270, 30)
        self.assertAlmostEqual(slenderness, 9.0)

    def test_aspect_ratio(self):
        """Test calcolo rapporto h/L"""
        # h/L = 270/300 = 0.9
        ratio = MasonryGeometry.calculate_aspect_ratio(270, 300)
        self.assertAlmostEqual(ratio, 0.9)


class TestIdentifyMaschi(unittest.TestCase):
    """Test identificazione maschi murari"""

    def test_no_openings(self):
        """Test parete senza aperture"""
        wall_data = {'length': 300}
        openings = []
        result = MasonryGeometry.identify_maschi(wall_data, openings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].length, 300)

    def test_single_centered_opening(self):
        """Test singola apertura centrata"""
        # Parete 300cm, apertura 100cm centrata a x=100
        wall_data = {'length': 300}
        openings = [{'x': 100, 'width': 100}]
        result = MasonryGeometry.identify_maschi(wall_data, openings)

        self.assertEqual(len(result), 2)
        # Maschio sinistro: 0-100 = 100cm
        self.assertEqual(result[0].length, 100)
        # Maschio destro: 200-300 = 100cm
        self.assertEqual(result[1].length, 100)

    def test_opening_at_edge(self):
        """Test apertura al bordo"""
        # Apertura che inizia a x=0
        wall_data = {'length': 300}
        openings = [{'x': 0, 'width': 100}]
        result = MasonryGeometry.identify_maschi(wall_data, openings)

        self.assertEqual(len(result), 1)
        # Solo maschio destro: 100-300 = 200cm
        self.assertEqual(result[0].length, 200)

    def test_two_openings(self):
        """Test due aperture"""
        # Parete 500cm, due aperture
        wall_data = {'length': 500}
        openings = [
            {'x': 50, 'width': 100},   # 50-150
            {'x': 250, 'width': 100}   # 250-350
        ]
        result = MasonryGeometry.identify_maschi(wall_data, openings)

        self.assertEqual(len(result), 3)
        # Maschio 1: 0-50 = 50cm
        self.assertEqual(result[0].length, 50)
        # Maschio 2: 150-250 = 100cm
        self.assertEqual(result[1].length, 100)
        # Maschio 3: 350-500 = 150cm
        self.assertEqual(result[2].length, 150)


class TestLoadDistribution(unittest.TestCase):
    """Test ripartizione carichi"""

    def test_distribute_load_equal(self):
        """Test ripartizione uniforme"""
        maschi = MaschiMurari(maschi=[
            Maschio(0, 100, 100, 0),
            Maschio(200, 300, 100, 1)
        ])
        loads = MasonryGeometry.distribute_load(200, maschi, 300)

        # Ogni maschio prende 100/300 * 200 = 66.67 kN
        self.assertEqual(len(loads), 2)
        self.assertAlmostEqual(loads[0], 200 * 100/300, places=2)
        self.assertAlmostEqual(loads[1], 200 * 100/300, places=2)

    def test_distribute_load_unequal(self):
        """Test ripartizione proporzionale"""
        maschi = MaschiMurari(maschi=[
            Maschio(0, 50, 50, 0),    # 50cm
            Maschio(100, 250, 150, 1)  # 150cm
        ])
        loads = MasonryGeometry.distribute_load(100, maschi, 300)

        # Maschio 1: 50/300 * 100 = 16.67 kN
        # Maschio 2: 150/300 * 100 = 50 kN
        self.assertAlmostEqual(loads[0], 100 * 50/300, places=2)
        self.assertAlmostEqual(loads[1], 100 * 150/300, places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
