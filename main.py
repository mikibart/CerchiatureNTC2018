#!/usr/bin/env python3
"""
Calcolatore Cerchiature NTC 2018 - Entry Point
Arch. Michelangelo Bartolotta
Versione con UI migliorata
"""

import sys
import os
import traceback
import logging
import argparse

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Aggiungi la directory corrente al path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from src.gui.main_window import MainWindow

# Import stile moderno (opzionale)
try:
    from src.gui.modern_style import apply_modern_style
    MODERN_STYLE_AVAILABLE = True
except ImportError:
    MODERN_STYLE_AVAILABLE = False
    logger.info("Stile moderno non disponibile, usando stile predefinito")


def exception_hook(exctype, value, tb):
    """Gestore globale per eccezioni non catturate"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(f"ERRORE CRITICO:\n{error_msg}", file=sys.stderr)
    logging.error(f"Eccezione non catturata: {error_msg}")
    QMessageBox.critical(None, "Errore Critico", f"Si è verificato un errore:\n\n{value}\n\nDettagli nel log.")


def main():
    # Parse argomenti da riga di comando
    parser = argparse.ArgumentParser(description='Calcolatore Cerchiature NTC 2018')
    parser.add_argument('--remote', '-r', action='store_true',
                        help='Abilita server controllo remoto')
    parser.add_argument('--port', '-p', type=int, default=9999,
                        help='Porta per il server di controllo remoto (default: 9999)')
    args = parser.parse_args()

    # Installa gestore eccezioni globale
    sys.excepthook = exception_hook

    # Abilita high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Cerchiature NTC 2018")
    app.setOrganizationName("Arch. M. Bartolotta")

    # Stile applicazione
    app.setStyle('Fusion')

    # Applica stile moderno se disponibile
    if MODERN_STYLE_AVAILABLE:
        apply_modern_style(app)
        logger.info("Stile moderno applicato")

    window = MainWindow()
    window.show()

    # Avvia server controllo remoto se richiesto
    if args.remote:
        try:
            from src.testing.remote_control import integrate_remote_control
            integrate_remote_control(window, port=args.port)
            logger.info(f"Server controllo remoto avviato su porta {args.port}")
        except Exception as e:
            logger.error(f"Errore avvio server controllo remoto: {e}")

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()