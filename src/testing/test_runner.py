"""
Test Runner per CerchiatureNTC2018
Permette di testare il software programmaticamente senza GUI
Arch. Michelangelo Bartolotta
"""

import sys
import json
import logging
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
logger = logging.getLogger('TestRunner')

# Aggiungi il path del progetto
sys.path.insert(0, r'D:\Cerchiatura\CerchiatureNTC2018 - Copia (2)\CerchiatureNTC2018')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


class TestRunner:
    """
    Runner per test automatizzati del software CerchiatureNTC2018.
    Permette di creare scenari di test e verificare i risultati.
    """

    def __init__(self, headless: bool = True):
        """
        Inizializza il test runner.

        Args:
            headless: Se True, non mostra la GUI (più veloce per test)
        """
        self.headless = headless
        self.app = None
        self.main_window = None
        self.results = {}

    def setup(self):
        """Inizializza l'applicazione Qt"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        # Import dopo QApplication
        from src.gui.main_window import MainWindow
        self.main_window = MainWindow()

        if not self.headless:
            self.main_window.show()

        logger.info("Test Runner inizializzato")
        return self

    def set_wall_data(self, length: float, height: float, thickness: float,
                      height_left: float = None, height_right: float = None) -> 'TestRunner':
        """
        Imposta i dati della parete.

        Args:
            length: Lunghezza parete [cm]
            height: Altezza parete [cm]
            thickness: Spessore parete [cm]
            height_left: Altezza sinistra (opzionale)
            height_right: Altezza destra (opzionale)
        """
        input_module = self.main_window.input_module

        input_module.length_spin.setValue(int(length))
        input_module.height_spin.setValue(int(height))
        input_module.thickness_spin.setValue(int(thickness))

        if height_left is not None:
            input_module.height_left_spin.setValue(int(height_left))
        if height_right is not None:
            input_module.height_right_spin.setValue(int(height_right))

        logger.info(f"Parete impostata: L={length}cm, H={height}cm, t={thickness}cm")
        return self

    def set_masonry_type(self, masonry_type: str) -> 'TestRunner':
        """
        Imposta il tipo di muratura.

        Args:
            masonry_type: Tipo muratura (es. "Muratura in pietrame disordinata")
        """
        input_module = self.main_window.input_module
        index = input_module.masonry_type.findText(masonry_type)
        if index >= 0:
            input_module.masonry_type.setCurrentIndex(index)
            logger.info(f"Muratura impostata: {masonry_type}")
        else:
            logger.warning(f"Tipo muratura non trovato: {masonry_type}")
        return self

    def set_safety_factors(self, gamma_m: float = 2.0, fc: float = 1.35) -> 'TestRunner':
        """
        Imposta i coefficienti di sicurezza.

        Args:
            gamma_m: Coefficiente parziale materiale
            fc: Fattore di confidenza
        """
        input_module = self.main_window.input_module
        input_module.gamma_m_spin.setValue(gamma_m)
        input_module.fc_spin.setValue(fc)
        logger.info(f"Coefficienti: γ_m={gamma_m}, FC={fc}")
        return self

    def add_opening(self, x: int, y: int, width: int, height: int,
                    opening_type: str = "Rettangolare",
                    existing: bool = False) -> 'TestRunner':
        """
        Aggiunge un'apertura.

        Args:
            x: Posizione X dal bordo sinistro [cm]
            y: Posizione Y dal basso [cm]
            width: Larghezza apertura [cm]
            height: Altezza apertura [cm]
            opening_type: Tipo apertura
            existing: Se è un'apertura esistente
        """
        input_module = self.main_window.input_module

        opening_data = {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'type': opening_type,
            'existing': existing
        }

        # Aggiungi direttamente alla lista
        input_module.openings.append(opening_data)
        input_module.update_openings_list()
        input_module.update_canvas()

        logger.info(f"Apertura aggiunta: {opening_type} {width}x{height}cm @ ({x},{y})")
        return self

    def add_circular_opening(self, x: int, y: int, diameter: int,
                             existing: bool = False) -> 'TestRunner':
        """
        Aggiunge un'apertura circolare.

        Args:
            x: Posizione X del centro [cm]
            y: Posizione Y del centro [cm]
            diameter: Diametro [cm]
            existing: Se esistente
        """
        opening_data = {
            'x': x - diameter // 2,  # Converti da centro a angolo
            'y': y - diameter // 2,
            'width': diameter,
            'height': diameter,
            'type': 'Circolare',
            'existing': existing,
            'circular_data': {
                'diameter': diameter,
                'custom_center': False,
                'center_x_offset': 0,
                'center_y_offset': 0
            }
        }

        input_module = self.main_window.input_module
        input_module.openings.append(opening_data)
        input_module.update_openings_list()
        input_module.update_canvas()

        logger.info(f"Apertura circolare aggiunta: Ø{diameter}cm @ ({x},{y})")
        return self

    def add_reinforcement(self, opening_index: int, reinforcement_type: str,
                          profile: str = "HEA 100", n_profiles: int = 1,
                          existing: bool = False) -> 'TestRunner':
        """
        Aggiunge rinforzo a un'apertura.

        Args:
            opening_index: Indice apertura (0-based)
            reinforcement_type: Tipo rinforzo
            profile: Profilo (es. "HEA 100")
            n_profiles: Numero profili
            existing: Se rinforzo esistente
        """
        input_module = self.main_window.input_module

        if opening_index >= len(input_module.openings):
            logger.error(f"Indice apertura non valido: {opening_index}")
            return self

        rinforzo = {
            'tipo': reinforcement_type,
            'materiale': 'acciaio',
            'classe_acciaio': 'S235',
            'esistente': existing,
            'architrave': {
                'profilo': profile,
                'n_profili': n_profiles,
                'interasse': 0,
                'disposizione': 'In linea',
                'ruotato': False
            },
            'note': ''
        }

        # Per calandrato, aggiungi dati arco
        if 'calandrato' in reinforcement_type.lower():
            rinforzo['arco'] = {
                'tipo_apertura': 'Arco a tutto sesto',
                'raggio': 150,
                'freccia': 30,
                'profilo': profile,
                'n_profili': n_profiles,
                'metodo': 'A freddo'
            }

        input_module.openings[opening_index]['rinforzo'] = rinforzo
        input_module.update_openings_list()
        input_module.update_canvas()

        logger.info(f"Rinforzo aggiunto ad A{opening_index+1}: {reinforcement_type}, {n_profiles}x{profile}")
        return self

    def run_calculation(self) -> Dict[str, Any]:
        """
        Esegue il calcolo e restituisce i risultati.

        Returns:
            Dict con risultati del calcolo
        """
        # Passa al tab calcoli
        self.main_window.tabs.setCurrentIndex(2)  # Tab Calcolo

        # Esegui calcolo
        calc_module = self.main_window.calc_module

        # Raccogli dati
        wall_data = self.main_window.input_module.collect_data()
        openings_data = self.main_window.openings_module.collect_data()

        # Prepara dati per calcolo
        calc_module.set_wall_data(wall_data)
        calc_module.set_openings(openings_data.get('openings', []))

        # Esegui
        results = calc_module.perform_calculation()

        self.results = results

        # Log risultati principali
        if results:
            logger.info("=== RISULTATI CALCOLO ===")
            if 'original' in results:
                orig = results['original']
                logger.info(f"Stato di fatto: K={orig.get('K', 0):.1f} kN/m, V_t1={orig.get('V_t1', 0):.1f} kN")
            if 'modified' in results:
                mod = results['modified']
                logger.info(f"Stato di progetto: K={mod.get('K', 0):.1f} kN/m, V_t1={mod.get('V_t1', 0):.1f} kN")
            if 'comparison' in results:
                comp = results['comparison']
                logger.info(f"Variazioni: ΔK={comp.get('delta_K', 0):.1f}%, ΔV={comp.get('delta_V', 0):.1f}%")

        return results

    def get_results(self) -> Dict[str, Any]:
        """Restituisce gli ultimi risultati del calcolo."""
        return self.results

    def verify_stiffness(self, expected_K: float, tolerance: float = 0.05) -> bool:
        """
        Verifica che la rigidezza sia entro la tolleranza.

        Args:
            expected_K: Rigidezza attesa [kN/m]
            tolerance: Tolleranza (es. 0.05 = 5%)

        Returns:
            True se OK
        """
        if 'modified' not in self.results:
            logger.error("Nessun risultato disponibile")
            return False

        actual_K = self.results['modified'].get('K', 0)
        diff = abs(actual_K - expected_K) / expected_K if expected_K > 0 else 0

        ok = diff <= tolerance
        status = "OK" if ok else "FAIL"
        logger.info(f"Verifica K: atteso={expected_K:.1f}, ottenuto={actual_K:.1f}, diff={diff*100:.1f}% [{status}]")

        return ok

    def verify_resistance(self, expected_V: float, tolerance: float = 0.05) -> bool:
        """
        Verifica che la resistenza sia entro la tolleranza.

        Args:
            expected_V: Resistenza attesa [kN]
            tolerance: Tolleranza

        Returns:
            True se OK
        """
        if 'modified' not in self.results:
            logger.error("Nessun risultato disponibile")
            return False

        actual_V = self.results['modified'].get('V_t1', 0)
        diff = abs(actual_V - expected_V) / expected_V if expected_V > 0 else 0

        ok = diff <= tolerance
        status = "OK" if ok else "FAIL"
        logger.info(f"Verifica V: atteso={expected_V:.1f}, ottenuto={actual_V:.1f}, diff={diff*100:.1f}% [{status}]")

        return ok

    def reset(self) -> 'TestRunner':
        """Resetta lo stato per un nuovo test."""
        if self.main_window:
            self.main_window.input_module.reset_to_defaults()
            self.main_window.openings_module.reset()
        self.results = {}
        logger.info("Test Runner resettato")
        return self

    def cleanup(self):
        """Chiude l'applicazione."""
        if self.main_window:
            self.main_window.close()
        logger.info("Test Runner chiuso")


def run_test_scenario():
    """Esegue uno scenario di test di esempio."""

    logger.info("=" * 60)
    logger.info("INIZIO TEST SCENARIO: Apertura circolare con calandrato")
    logger.info("=" * 60)

    runner = TestRunner(headless=True)
    runner.setup()

    # Configura parete
    runner.set_wall_data(length=423, height=350, thickness=30)
    runner.set_masonry_type("Muratura in pietrame disordinata")
    runner.set_safety_factors(gamma_m=2.0, fc=1.35)

    # Aggiungi apertura circolare
    runner.add_circular_opening(x=200, y=100, diameter=100, existing=False)

    # Aggiungi rinforzo calandrato
    runner.add_reinforcement(
        opening_index=0,
        reinforcement_type="Rinforzo calandrato nell'arco",
        profile="HEA 100",
        n_profiles=1
    )

    # Esegui calcolo
    results = runner.run_calculation()

    # Verifica risultati
    logger.info("-" * 40)
    logger.info("VERIFICA RISULTATI")

    # Test con 2 profili
    logger.info("-" * 40)
    logger.info("TEST: Cambio a 2 profili")

    runner.add_reinforcement(
        opening_index=0,
        reinforcement_type="Rinforzo calandrato nell'arco",
        profile="HEA 100",
        n_profiles=2
    )

    results2 = runner.run_calculation()

    # Verifica che K sia aumentata
    K1 = results.get('modified', {}).get('K', 0)
    K2 = results2.get('modified', {}).get('K', 0)

    if K2 > K1:
        logger.info(f"OK: K aumentata da {K1:.1f} a {K2:.1f} kN/m (+{(K2-K1)/K1*100:.1f}%)")
    else:
        logger.error(f"FAIL: K non aumentata (K1={K1:.1f}, K2={K2:.1f})")

    runner.cleanup()

    logger.info("=" * 60)
    logger.info("FINE TEST SCENARIO")
    logger.info("=" * 60)

    return results2


if __name__ == '__main__':
    run_test_scenario()
