"""
Test calcoli muratura
"""

import unittest
from src.core.engine.masonry import MasonryCalculator

class TestMasonryCalculator(unittest.TestCase):
    """Test per calcoli muratura"""
    
    def setUp(self):
        self.calculator = MasonryCalculator()
        
    def test_resistance_calculation(self):
        """Test calcolo resistenze"""
        # TODO: Implementare test
        pass

if __name__ == '__main__':
    unittest.main()
