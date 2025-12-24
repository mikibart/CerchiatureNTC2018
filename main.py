#!/usr/bin/env python3
"""
Calcolatore Cerchiature NTC 2018 - Entry Point
Arch. Michelangelo Bartolotta
"""

import sys
import os
import traceback
import logging

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(message)s')

# Aggiungi la directory corrente al path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from src.gui.main_window import MainWindow

def exception_hook(exctype, value, tb):
    """Gestore globale per eccezioni non catturate"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(f"ERRORE CRITICO:\n{error_msg}", file=sys.stderr)
    logging.error(f"Eccezione non catturata: {error_msg}")
    QMessageBox.critical(None, "Errore Critico", f"Si è verificato un errore:\n\n{value}\n\nDettagli nel log.")

def main():
    # Installa gestore eccezioni globale
    sys.excepthook = exception_hook

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