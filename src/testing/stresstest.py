"""
Stress Test - CerchiatureNTC2018
Test aggressivi per trovare bug e problemi di stabilità
"""

import sys
import os
import time
import random
import traceback

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.testing.remote_client import RemoteClient


class StressTest:
    """Stress test aggressivo per trovare bug"""

    def __init__(self, host='localhost', port=9999):
        self.client = RemoteClient(host, port)
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.bugs_found = []

    def log(self, msg, level='INFO'):
        """Log con timestamp"""
        prefix = {'INFO': '  ', 'OK': '  [OK]', 'FAIL': '  [FAIL]', 'BUG': '  [BUG]', 'WARN': '  [WARN]'}
        print(f"{prefix.get(level, '  ')} {msg}")

    def report_bug(self, description, details=None):
        """Registra un bug trovato"""
        bug = {'description': description, 'details': details}
        self.bugs_found.append(bug)
        self.log(f"BUG TROVATO: {description}", 'BUG')
        if details:
            print(f"       Dettagli: {details}")

    # =========================================================================
    # TEST 1: VALORI LIMITE PARETE
    # =========================================================================

    def test_extreme_wall_dimensions(self):
        """Test dimensioni parete estreme"""
        print("\n" + "="*70)
        print("  STRESS TEST 1: VALORI LIMITE PARETE")
        print("="*70)

        test_cases = [
            # (length, height, thickness, description, should_fail)
            (100, 100, 10, "Parete minima", False),
            (50, 50, 5, "Parete piccola", False),
            (2000, 1000, 100, "Parete enorme", False),
            (3000, 800, 80, "Parete molto lunga", False),
            (200, 1500, 50, "Parete molto alta", False),
            (500, 350, 5, "Spessore minimo", False),
            (500, 350, 150, "Spessore grande", False),
            (0, 350, 30, "Lunghezza zero", True),
            (500, 0, 30, "Altezza zero", True),
            (500, 350, 0, "Spessore zero", True),
            (-500, 350, 30, "Lunghezza negativa", True),
            (500, -350, 30, "Altezza negativa", True),
            (500, 350, -30, "Spessore negativo", True),
        ]

        for length, height, thickness, desc, should_fail in test_cases:
            self.client.reset()
            result = self.client.set_wall(length, height, thickness)

            if should_fail:
                # Valori invalidi - dovrebbe fallire o gestire l'errore
                if result.get('success'):
                    self.report_bug(
                        f"Accettato valore invalido: {desc}",
                        f"L={length}, H={height}, t={thickness}"
                    )
                else:
                    self.log(f"{desc}: Correttamente rifiutato", 'OK')
            else:
                if result.get('success'):
                    self.log(f"{desc}: OK", 'OK')
                else:
                    self.log(f"{desc}: Fallito", 'FAIL')

    def test_extreme_opening_dimensions(self):
        """Test dimensioni aperture estreme"""
        print("\n" + "="*70)
        print("  STRESS TEST 2: VALORI LIMITE APERTURE")
        print("="*70)

        test_cases = [
            # (width, height, x_pos, description, should_fail)
            (10, 10, 100, "Apertura minima", False),
            (5, 5, 100, "Apertura troppo piccola (< 10cm)", True),
            (400, 300, 50, "Apertura grande", False),
            (100, 200, 0, "Apertura sul bordo sinistro", False),
            (100, 200, 400, "Apertura sul bordo destro", False),
            (100, 200, 450, "Apertura fuori parete", True),
            (100, 200, -50, "Posizione negativa", True),
            (0, 200, 100, "Larghezza zero", True),
            (100, 0, 100, "Altezza zero", True),
            (-100, 200, 100, "Larghezza negativa", True),
            (600, 200, 0, "Apertura più larga della parete", True),
            (100, 400, 100, "Apertura più alta della parete", True),
        ]

        for width, height, x_pos, desc, should_fail in test_cases:
            self.client.reset()
            self.client.set_wall(500, 350, 30)

            # Calcola y per centrare verticalmente
            y_pos = (350 - height) // 2 if height < 350 else 0

            result = self.client.add_opening(x_pos, y_pos, width, height)

            if should_fail:
                if result.get('success'):
                    self.report_bug(
                        f"Accettata apertura invalida: {desc}",
                        f"W={width}, H={height}, X={x_pos}"
                    )
                else:
                    self.log(f"{desc}: Correttamente rifiutato", 'OK')
            else:
                if result.get('success'):
                    self.log(f"{desc}: OK", 'OK')
                else:
                    self.log(f"{desc}: Fallito inaspettatamente", 'FAIL')

    def test_overlapping_openings(self):
        """Test aperture sovrapposte"""
        print("\n" + "="*70)
        print("  STRESS TEST 3: APERTURE SOVRAPPOSTE")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)

        # Aggiungi prima apertura
        r1 = self.client.add_opening(100, 75, 100, 200)

        if not r1.get('success'):
            self.log("Prima apertura fallita", 'FAIL')
            return

        self.log("Prima apertura aggiunta: X=100, W=100", 'OK')

        # Prova ad aggiungere apertura sovrapposta
        r2 = self.client.add_opening(150, 75, 100, 200)

        if r2.get('success'):
            self.report_bug(
                "Accettata apertura sovrapposta",
                "Apertura 1: X=100, W=100; Apertura 2: X=150, W=100"
            )
        else:
            self.log("Apertura sovrapposta correttamente rifiutata", 'OK')

        # Prova apertura completamente contenuta
        self.client.reset()
        self.client.set_wall(500, 350, 30)
        self.client.add_opening(100, 50, 200, 250)  # Grande
        r3 = self.client.add_opening(150, 100, 50, 50)  # Piccola dentro

        if r3.get('success'):
            self.report_bug(
                "Accettata apertura contenuta in altra",
                "Grande: X=100, W=200; Piccola: X=150, W=50"
            )
        else:
            self.log("Apertura contenuta correttamente rifiutata", 'OK')

    # =========================================================================
    # TEST 2: OPERAZIONI RIPETUTE (MEMORY LEAK)
    # =========================================================================

    def test_repeated_reset(self):
        """Test reset ripetuti"""
        print("\n" + "="*70)
        print("  STRESS TEST 4: RESET RIPETUTI (100x)")
        print("="*70)

        start_time = time.time()
        errors = 0

        for i in range(100):
            result = self.client.reset()
            if not result.get('success'):
                errors += 1

        elapsed = time.time() - start_time

        if errors == 0:
            self.log(f"100 reset completati in {elapsed:.2f}s", 'OK')
        else:
            self.report_bug(f"{errors} reset falliti su 100", f"Tempo: {elapsed:.2f}s")

    def test_repeated_add_remove(self):
        """Test aggiunta/rimozione ripetuta"""
        print("\n" + "="*70)
        print("  STRESS TEST 5: AGGIUNTA/RIMOZIONE RIPETUTA (50x)")
        print("="*70)

        errors = 0
        start_time = time.time()

        for i in range(50):
            self.client.reset()
            self.client.set_wall(500, 350, 30)

            # Aggiungi apertura
            r1 = self.client.add_opening(100, 75, 100, 200)
            if not r1.get('success'):
                errors += 1
                continue

            # Aggiungi rinforzo
            r2 = self.client.add_reinforcement(0, 'telaio_chiuso', 'HEA 140')
            if not r2.get('success'):
                errors += 1
                continue

            # Calcola
            r3 = self.client.calculate()
            if not r3.get('success'):
                errors += 1

        elapsed = time.time() - start_time

        if errors == 0:
            self.log(f"50 cicli add/calc/reset in {elapsed:.2f}s", 'OK')
        else:
            self.report_bug(f"{errors} errori in 50 cicli add/remove", f"Tempo: {elapsed:.2f}s")

    def test_many_openings(self):
        """Test molte aperture"""
        print("\n" + "="*70)
        print("  STRESS TEST 6: MOLTE APERTURE")
        print("="*70)

        self.client.reset()
        self.client.set_wall(2000, 350, 30)  # Parete molto lunga

        max_openings = 15
        added = 0

        for i in range(max_openings):
            x_pos = 50 + i * 130  # Spaziatura
            result = self.client.add_opening(x_pos, 75, 80, 200)
            if result.get('success'):
                added += 1
            else:
                self.log(f"Apertura {i+1} fallita a X={x_pos}", 'WARN')
                break

        self.log(f"Aggiunte {added} aperture su {max_openings} tentate", 'INFO')

        # Aggiungi rinforzi a tutte
        reinforced = 0
        for i in range(added):
            result = self.client.add_reinforcement(i, 'telaio_chiuso', 'HEA 100')
            if result.get('success'):
                reinforced += 1

        self.log(f"Rinforzate {reinforced}/{added} aperture", 'INFO')

        # Calcola
        result = self.client.calculate()
        if result.get('success'):
            results = result.get('results', {})
            k_frame = results.get('K_cerchiature', 0)
            self.log(f"Calcolo OK: K_cerchiature = {k_frame:.0f} kN/m", 'OK')
        else:
            self.report_bug("Calcolo fallito con molte aperture", f"Aperture: {added}")

    # =========================================================================
    # TEST 3: INPUT INVALIDI
    # =========================================================================

    def test_invalid_masonry_type(self):
        """Test tipo muratura invalido"""
        print("\n" + "="*70)
        print("  STRESS TEST 7: TIPO MURATURA INVALIDO")
        print("="*70)

        self.client.reset()

        invalid_types = [
            "Muratura inesistente",
            "",
            "123",
            "SELECT * FROM users",
            "<script>alert('xss')</script>",
            "A" * 500,
        ]

        for tipo in invalid_types:
            result = self.client.set_masonry(tipo)
            if result.get('success'):
                self.report_bug(
                    f"Accettato tipo muratura invalido",
                    f"Tipo: {tipo[:50]}..."
                )
            else:
                self.log(f"Tipo invalido rifiutato: {tipo[:30]}...", 'OK')

    def test_invalid_reinforcement_type(self):
        """Test tipo rinforzo invalido"""
        print("\n" + "="*70)
        print("  STRESS TEST 8: TIPO RINFORZO INVALIDO")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)
        self.client.add_opening(100, 75, 100, 200)

        invalid_types = [
            "rinforzo_magico",
            "",
            "telaio chiuso",  # Spazio invece di underscore
            "TELAIO_CHIUSO",  # Maiuscolo
            "telaio",
        ]

        for tipo in invalid_types:
            self.client.reset()
            self.client.set_wall(500, 350, 30)
            self.client.add_opening(100, 75, 100, 200)

            result = self.client.add_reinforcement(0, tipo, 'HEA 140')
            if result.get('success'):
                # Verifica se il calcolo funziona
                calc = self.client.calculate()
                if calc.get('success'):
                    self.log(f"Tipo '{tipo}' accettato (potrebbe essere gestito)", 'WARN')
                else:
                    self.report_bug(f"Tipo '{tipo}' accettato ma calcolo fallisce")
            else:
                self.log(f"Tipo invalido rifiutato: {tipo}", 'OK')

    def test_invalid_profile(self):
        """Test profilo invalido"""
        print("\n" + "="*70)
        print("  STRESS TEST 9: PROFILO INVALIDO")
        print("="*70)

        invalid_profiles = [
            "HEA 999",
            "XYZ 100",
            "",
            "HEA",
            "100",
            "HEA100",
        ]

        for profilo in invalid_profiles:
            self.client.reset()
            self.client.set_wall(500, 350, 30)
            self.client.add_opening(100, 75, 100, 200)

            result = self.client.add_reinforcement(0, 'telaio_chiuso', profilo)
            if result.get('success'):
                calc = self.client.calculate()
                if calc.get('success'):
                    results = calc.get('results', {})
                    k = results.get('K_cerchiature', 0)
                    if k > 0:
                        self.log(f"Profilo '{profilo}' accettato con stima (K={k:.0f})", 'WARN')
                    else:
                        self.report_bug(f"Profilo '{profilo}' accettato ma K=0")
                else:
                    self.report_bug(f"Profilo '{profilo}' accettato ma calcolo fallisce")
            else:
                self.log(f"Profilo invalido rifiutato: {profilo}", 'OK')

    def test_invalid_index(self):
        """Test indici apertura invalidi"""
        print("\n" + "="*70)
        print("  STRESS TEST 10: INDICI INVALIDI")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)
        self.client.add_opening(100, 75, 100, 200)

        invalid_indices = [-1, 1, 10, 100, 999999]

        for idx in invalid_indices:
            result = self.client.add_reinforcement(idx, 'telaio_chiuso', 'HEA 140')
            if result.get('success'):
                self.report_bug(
                    f"Accettato indice invalido per rinforzo",
                    f"Index: {idx}, aperture presenti: 1"
                )
            else:
                self.log(f"Indice {idx} correttamente rifiutato", 'OK')

    # =========================================================================
    # TEST 4: CALCOLI CON DATI INCOMPLETI
    # =========================================================================

    def test_calculate_empty(self):
        """Test calcolo senza dati"""
        print("\n" + "="*70)
        print("  STRESS TEST 11: CALCOLO SENZA DATI")
        print("="*70)

        self.client.reset()

        # Calcolo senza parete configurata
        result = self.client.calculate()
        if result.get('success'):
            self.log("Calcolo senza configurazione: restituisce risultati", 'WARN')
        else:
            self.log("Calcolo senza configurazione: correttamente fallito", 'OK')

    def test_calculate_no_reinforcement(self):
        """Test calcolo senza rinforzi"""
        print("\n" + "="*70)
        print("  STRESS TEST 12: CALCOLO SENZA RINFORZI")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)
        self.client.add_opening(100, 75, 100, 200)

        result = self.client.calculate()
        if result.get('success'):
            results = result.get('results', {})
            k_frame = results.get('K_cerchiature', 0)
            if k_frame == 0:
                self.log("Calcolo senza rinforzi: K_cerchiature=0 (corretto)", 'OK')
            else:
                self.report_bug(
                    "K_cerchiature > 0 senza rinforzi",
                    f"K_cerchiature = {k_frame}"
                )
        else:
            self.log("Calcolo senza rinforzi: fallito", 'WARN')

    # =========================================================================
    # TEST 5: COMBINAZIONI STRANE
    # =========================================================================

    def test_circular_with_rectangular_reinforcement(self):
        """Test rinforzo rettangolare su apertura circolare"""
        print("\n" + "="*70)
        print("  STRESS TEST 13: COMBINAZIONI INCOMPATIBILI")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)

        # Apertura circolare
        self.client.add_circular_opening(200, 100, 80)

        # Prova telaio chiuso su circolare
        result = self.client.add_reinforcement(0, 'telaio_chiuso', 'HEA 140')

        if result.get('success'):
            calc = self.client.calculate()
            if calc.get('success'):
                self.log("Telaio chiuso su circolare: accettato e calcolato", 'WARN')
            else:
                self.report_bug("Telaio chiuso su circolare accettato ma calcolo fallisce")
        else:
            self.log("Telaio chiuso su circolare: rifiutato", 'OK')

    def test_reinforcement_before_opening(self):
        """Test rinforzo prima di aggiungere apertura"""
        print("\n" + "="*70)
        print("  STRESS TEST 14: RINFORZO SENZA APERTURA")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)

        # Prova ad aggiungere rinforzo senza aperture
        result = self.client.add_reinforcement(0, 'telaio_chiuso', 'HEA 140')

        if result.get('success'):
            self.report_bug("Rinforzo aggiunto senza aperture presenti")
        else:
            self.log("Rinforzo senza apertura: correttamente rifiutato", 'OK')

    # =========================================================================
    # TEST 6: RAPIDITA' E CONCORRENZA
    # =========================================================================

    def test_rapid_commands(self):
        """Test comandi rapidi in successione"""
        print("\n" + "="*70)
        print("  STRESS TEST 15: COMANDI RAPIDI (200 comandi)")
        print("="*70)

        start_time = time.time()
        errors = 0

        for i in range(200):
            cmd = random.choice(['ping', 'get_state', 'help'])
            result = self.client.send_command(cmd)
            if not result.get('success', False):
                errors += 1

        elapsed = time.time() - start_time

        if errors == 0:
            self.log(f"200 comandi in {elapsed:.2f}s ({200/elapsed:.0f} cmd/s)", 'OK')
        else:
            self.report_bug(f"{errors}/200 comandi falliti", f"Tempo: {elapsed:.2f}s")

    # =========================================================================
    # TEST 7: CONSISTENZA DATI
    # =========================================================================

    def test_data_consistency(self):
        """Test consistenza dati dopo operazioni"""
        print("\n" + "="*70)
        print("  STRESS TEST 16: CONSISTENZA DATI")
        print("="*70)

        self.client.reset()
        self.client.set_wall(500, 350, 30)

        # Aggiungi 3 aperture non sovrapposte
        positions = [(50, 80), (200, 80), (350, 80)]
        for x, w in positions:
            self.client.add_opening(x, 75, w, 200)

        # Verifica stato
        state = self.client.get_state()
        if state.get('success'):
            data = state.get('result', {})
            openings_count = len(data.get('openings', []))
            if openings_count == 3:
                self.log(f"Stato corretto: {openings_count} aperture", 'OK')
            else:
                self.report_bug(
                    f"Conteggio aperture errato",
                    f"Atteso: 3, Trovato: {openings_count}"
                )
        else:
            self.log("Impossibile verificare stato", 'FAIL')

        # Aggiungi rinforzo solo alla seconda
        self.client.add_reinforcement(1, 'telaio_chiuso', 'HEA 140')

        # Calcola e verifica
        result = self.client.calculate()
        if result.get('success'):
            self.log(f"Calcolo con 1/3 rinforzate: OK", 'OK')
        else:
            self.report_bug("Calcolo fallito con aperture parzialmente rinforzate")

    # =========================================================================
    # TEST 8: APERTURE CIRCOLARI
    # =========================================================================

    def test_circular_openings(self):
        """Test aperture circolari"""
        print("\n" + "="*70)
        print("  STRESS TEST 17: APERTURE CIRCOLARI")
        print("="*70)

        # Test con posizione y variabile per evitare che l'apertura esca dalla parete
        test_cases = [
            # (diameter, y_pos, description, should_fail)
            (80, 100, "Diametro normale", False),
            (10, 100, "Diametro piccolo (minimo 10cm)", False),
            (5, 100, "Diametro troppo piccolo (< 10cm)", True),
            (200, 50, "Diametro grande", False),  # y=50, y+d=250 < 350
            (400, 0, "Diametro > altezza parete", True),
            (0, 100, "Diametro zero", True),
            (-50, 100, "Diametro negativo", True),
        ]

        for diameter, y_pos, desc, should_fail in test_cases:
            self.client.reset()
            self.client.set_wall(500, 350, 30)

            result = self.client.add_circular_opening(200, y_pos, diameter)

            if should_fail:
                if result.get('success'):
                    self.report_bug(f"Accettata apertura circolare invalida: {desc}", f"D={diameter}")
                else:
                    self.log(f"{desc}: Correttamente rifiutato", 'OK')
            else:
                if result.get('success'):
                    self.log(f"{desc}: OK", 'OK')
                else:
                    self.log(f"{desc}: Fallito", 'FAIL')

    # =========================================================================
    # TEST 9: NUMERO PROFILI
    # =========================================================================

    def test_n_profiles(self):
        """Test numero profili invalido"""
        print("\n" + "="*70)
        print("  STRESS TEST 18: NUMERO PROFILI INVALIDO")
        print("="*70)

        test_cases = [
            (0, "Zero profili"),
            (-1, "Profili negativi"),
            (10, "Troppi profili"),
            (100, "Moltissimi profili"),
        ]

        for n, desc in test_cases:
            self.client.reset()
            self.client.set_wall(500, 350, 30)
            self.client.add_opening(100, 75, 100, 200)

            result = self.client.add_reinforcement(0, 'telaio_chiuso', 'HEA 140', n)

            if n <= 0:
                if result.get('success'):
                    self.report_bug(f"Accettato n_profili invalido: {desc}", f"n={n}")
                else:
                    self.log(f"{desc}: Correttamente rifiutato", 'OK')
            else:
                if result.get('success'):
                    calc = self.client.calculate()
                    if calc.get('success'):
                        self.log(f"{desc}: Accettato e calcolato", 'WARN' if n > 4 else 'OK')
                    else:
                        self.report_bug(f"{desc}: Accettato ma calcolo fallisce")
                else:
                    self.log(f"{desc}: Rifiutato", 'OK' if n > 10 else 'WARN')

    # =========================================================================
    # ESECUZIONE
    # =========================================================================

    def run_all(self):
        """Esegue tutti gli stress test"""
        print("="*70)
        print("  STRESS TEST - CerchiatureNTC2018")
        print("="*70)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self.client.connect()
            print(f"Connesso a {self.client.host}:{self.client.port}")
        except Exception as e:
            print(f"ERRORE: Impossibile connettersi - {e}")
            return

        try:
            # Test valori limite
            self.test_extreme_wall_dimensions()
            self.test_extreme_opening_dimensions()
            self.test_overlapping_openings()

            # Test operazioni ripetute
            self.test_repeated_reset()
            self.test_repeated_add_remove()
            self.test_many_openings()

            # Test input invalidi
            self.test_invalid_masonry_type()
            self.test_invalid_reinforcement_type()
            self.test_invalid_profile()
            self.test_invalid_index()

            # Test calcoli incompleti
            self.test_calculate_empty()
            self.test_calculate_no_reinforcement()

            # Test combinazioni strane
            self.test_circular_with_rectangular_reinforcement()
            self.test_reinforcement_before_opening()

            # Test rapidità
            self.test_rapid_commands()

            # Test consistenza
            self.test_data_consistency()

            # Test circolari
            self.test_circular_openings()

            # Test n_profiles
            self.test_n_profiles()

        except Exception as e:
            print(f"\nERRORE CRITICO: {e}")
            traceback.print_exc()
        finally:
            self.client.disconnect()

        # Riepilogo
        print("\n" + "="*70)
        print("  RIEPILOGO STRESS TEST")
        print("="*70)

        if self.bugs_found:
            print(f"\n  BUG TROVATI: {len(self.bugs_found)}")
            print("-"*70)
            for i, bug in enumerate(self.bugs_found, 1):
                print(f"  {i}. {bug['description']}")
                if bug['details']:
                    print(f"     Dettagli: {bug['details']}")
        else:
            print("\n  Nessun bug critico trovato!")

        print("="*70)


if __name__ == '__main__':
    test = StressTest()
    test.run_all()
