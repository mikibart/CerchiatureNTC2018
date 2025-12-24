#!/usr/bin/env python3
"""
Calcolatore Cerchiature NTC 2018 - Entry Point
Arch. Michelangelo Bartolotta
"""

import sys
import os

# Aggiungi la directory corrente al path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cerchiature NTC 2018")
    app.setOrganizationName("Arch. M. Bartolotta")
    
    # Stile applicazione
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()