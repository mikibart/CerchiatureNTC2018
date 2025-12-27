"""
Hard Test per CerchiatureNTC2018 Remote Control
Testa tutti i tipi di aperture e rinforzi possibili
Arch. Michelangelo Bartolotta
"""

import sys
import time
import json

# Aggiungi path
sys.path.insert(0, r'D:\Cerchiatura\CerchiatureNTC2018 - Copia (2)\CerchiatureNTC2018')

from src.testing.remote_client import RemoteClient


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    print(f"\n--- {text} ---")


def print_result(test_name, success, details=""):
    status = "PASS" if success else "FAIL"
    icon = "[OK]" if success else "[XX]"
    print(f"  {icon} {test_name}: {status} {details}")
    return success


def run_hardtest():
    """Esegue test completo di tutti i casi possibili."""

    print_header("HARD TEST - CerchiatureNTC2018 Remote Control")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    client = RemoteClient()

    if not client.connect():
        print("\nERRORE: Impossibile connettersi al server.")
        print("Assicurarsi che l'applicazione sia avviata con: python main.py --remote")
        return False

    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }

    def record_test(name, success, details=""):
        if success:
            results['passed'] += 1
        else:
            results['failed'] += 1
        results['tests'].append({'name': name, 'success': success, 'details': details})
        return print_result(name, success, details)

    try:
        # ============================================================
        # TEST 1: CONNESSIONE E COMANDI BASE
        # ============================================================
        print_header("TEST 1: CONNESSIONE E COMANDI BASE")

        # Ping
        result = client.ping()
        record_test("Ping server", result)

        # Help
        result = client.help()
        record_test("Help command", result.get('success', False))

        # Reset iniziale
        result = client.reset()
        record_test("Reset iniziale", result.get('success', False))
        time.sleep(0.3)

        # ============================================================
        # TEST 2: CONFIGURAZIONE PARETE
        # ============================================================
        print_header("TEST 2: CONFIGURAZIONE PARETE")

        # Parete standard
        result = client.set_wall(500, 350, 30)
        record_test("Parete 500x350x30", result.get('success', False))

        # Verifica stato
        state = client.get_state()
        wall = state.get('result', {}).get('wall', {})
        correct = wall.get('length') == 500 and wall.get('height') == 350
        record_test("Verifica dimensioni parete", correct, f"L={wall.get('length')}, H={wall.get('height')}")

        # ============================================================
        # TEST 3: TIPI DI MURATURA
        # ============================================================
        print_header("TEST 3: TIPI DI MURATURA")

        masonry_types = [
            "Muratura in pietrame disordinata",
            "Muratura a conci sbozzati",
            "Muratura in mattoni pieni e malta di calce",
            "Muratura in blocchi di tufo",
            "Muratura in blocchi di calcestruzzo",
        ]

        for masonry in masonry_types:
            result = client.set_masonry(masonry)
            success = result.get('success', False)
            record_test(f"Muratura: {masonry[:30]}...", success)

        # Imposta muratura finale per i test
        client.set_masonry("Muratura in pietrame disordinata")

        # ============================================================
        # TEST 4: TUTTI I TIPI DI APERTURE
        # ============================================================
        print_header("TEST 4: TUTTI I TIPI DI APERTURE")

        client.reset()
        time.sleep(0.2)
        client.set_wall(800, 400, 35)
        client.set_masonry("Muratura in pietrame disordinata")

        # 4.1 Apertura rettangolare
        print_section("4.1 Apertura Rettangolare")
        result = client.add_opening(50, 0, 120, 210, 'Rettangolare', False)
        success = result.get('success', False) and result.get('result', {}).get('index') == 0
        record_test("Apertura rettangolare 120x210", success, f"index={result.get('result', {}).get('index')}")

        # 4.2 Apertura circolare
        print_section("4.2 Apertura Circolare")
        result = client.add_circular_opening(300, 100, 80, False)
        success = result.get('success', False)
        record_test("Apertura circolare D=80", success, f"index={result.get('result', {}).get('index')}")

        # 4.3 Apertura rettangolare esistente
        print_section("4.3 Apertura Esistente")
        result = client.add_opening(450, 0, 100, 180, 'Rettangolare', True)
        success = result.get('success', False)
        record_test("Apertura esistente 100x180", success)

        # 4.4 Apertura circolare esistente
        result = client.add_circular_opening(600, 150, 60, True)
        success = result.get('success', False)
        record_test("Apertura circolare esistente D=60", success)

        # Verifica conteggio aperture
        openings = client.get_openings()
        count = openings.get('result', {}).get('count', 0)
        record_test("Verifica 4 aperture create", count == 4, f"count={count}")

        # ============================================================
        # TEST 5: TUTTI I TIPI DI RINFORZO
        # ============================================================
        print_header("TEST 5: TUTTI I TIPI DI RINFORZO")

        client.reset()
        time.sleep(0.2)
        client.set_wall(1200, 400, 40)
        client.set_masonry("Muratura in pietrame disordinata")

        reinforcement_types = [
            ("Solo architrave in acciaio", "HEA 120", 1),
            ("Telaio chiuso in acciaio", "HEA 140", 2),
            ("Telaio aperto in acciaio", "HEA 100", 1),
            ("Profili accoppiati", "HEA 160", 2),
            ("Rinforzo calandrato nell'arco", "HEA 100", 1),
        ]

        x_pos = 50
        for i, (rinf_type, profile, n_prof) in enumerate(reinforcement_types):
            # Aggiungi apertura
            if 'calandrato' in rinf_type.lower():
                result = client.add_circular_opening(x_pos + 50, 100, 100, False)
            else:
                result = client.add_opening(x_pos, 0, 120, 210, 'Rettangolare', False)

            if not result.get('success', False):
                record_test(f"Apertura per {rinf_type[:25]}", False)
                x_pos += 200
                continue

            idx = result.get('result', {}).get('index', i)

            # Aggiungi rinforzo
            result = client.add_reinforcement(idx, rinf_type, profile, n_prof, False)
            success = result.get('success', False)
            record_test(f"{rinf_type[:30]}", success, f"profilo={profile}, n={n_prof}")

            x_pos += 200

        # Verifica aperture con rinforzo
        openings = client.get_openings()
        reinforced = sum(1 for op in openings.get('result', {}).get('openings', [])
                        if op.get('reinforcement'))
        record_test("Verifica aperture con rinforzo", reinforced >= 4, f"reinforced={reinforced}")

        # ============================================================
        # TEST 6: CALCOLO CON DIVERSI SCENARI
        # ============================================================
        print_header("TEST 6: CALCOLO CON DIVERSI SCENARI")

        # Scenario 6.1: Singola apertura con telaio chiuso
        print_section("6.1 Singola apertura con telaio chiuso")
        client.reset()
        time.sleep(0.2)
        client.set_wall(400, 300, 30)
        client.set_masonry("Muratura in blocchi di tufo")
        client.add_opening(100, 0, 120, 210, 'Rettangolare', False)
        client.add_reinforcement(0, "Telaio chiuso in acciaio", "HEA 140", 2, False)

        result = client.calculate()
        success = result.get('success', False)
        if success:
            res = result.get('result', {}).get('results', {})
            K_orig = res.get('original', {}).get('K', 0)
            K_mod = res.get('modified', {}).get('K', 0)
            K_frame = res.get('modified', {}).get('K_frame', 0)
            record_test("Calcolo scenario 6.1", K_frame > 0,
                       f"K_orig={K_orig:.0f}, K_mod={K_mod:.0f}, K_frame={K_frame:.0f}")
        else:
            record_test("Calcolo scenario 6.1", False, result.get('error', ''))

        # Scenario 6.2: Apertura circolare con calandrato
        print_section("6.2 Apertura circolare con calandrato")
        client.reset()
        time.sleep(0.2)
        client.set_wall(400, 350, 30)
        client.set_masonry("Muratura in pietrame disordinata")
        client.add_circular_opening(200, 100, 100, False)
        client.add_reinforcement(0, "Rinforzo calandrato nell'arco", "HEA 100", 1, False)

        result = client.calculate()
        success = result.get('success', False)
        if success:
            res = result.get('result', {}).get('results', {})
            K_frame = res.get('modified', {}).get('K_frame', 0)
            record_test("Calcolo scenario 6.2", K_frame > 0, f"K_frame={K_frame:.0f}")
        else:
            record_test("Calcolo scenario 6.2", False)

        # Scenario 6.3: Multiple aperture miste
        print_section("6.3 Multiple aperture miste")
        client.reset()
        time.sleep(0.2)
        client.set_wall(800, 400, 35)
        client.set_masonry("Muratura a conci sbozzati")

        # Apertura 1: rettangolare con telaio chiuso
        client.add_opening(50, 0, 120, 210, 'Rettangolare', False)
        client.add_reinforcement(0, "Telaio chiuso in acciaio", "HEA 140", 2, False)

        # Apertura 2: circolare con calandrato
        client.add_circular_opening(300, 100, 80, False)
        client.add_reinforcement(1, "Rinforzo calandrato nell'arco", "HEA 100", 1, False)

        # Apertura 3: rettangolare con architrave
        client.add_opening(450, 0, 100, 180, 'Rettangolare', False)
        client.add_reinforcement(2, "Solo architrave in acciaio", "HEA 120", 1, False)

        result = client.calculate()
        success = result.get('success', False)
        if success:
            res = result.get('result', {}).get('results', {})
            K_frame = res.get('modified', {}).get('K_frame', 0)
            V_t1 = res.get('modified', {}).get('V_t1', 0)
            record_test("Calcolo scenario 6.3", K_frame > 0,
                       f"K_frame={K_frame:.0f}, V_t1={V_t1:.1f}")
        else:
            record_test("Calcolo scenario 6.3", False)

        # Scenario 6.4: Aperture esistenti + nuove
        print_section("6.4 Aperture esistenti + nuove")
        client.reset()
        time.sleep(0.2)
        client.set_wall(600, 350, 30)
        client.set_masonry("Muratura in mattoni pieni e malta di calce")

        # Apertura esistente senza rinforzo
        client.add_opening(50, 0, 100, 180, 'Rettangolare', True)

        # Nuova apertura con rinforzo
        client.add_opening(250, 0, 120, 210, 'Rettangolare', False)
        client.add_reinforcement(1, "Telaio chiuso in acciaio", "HEA 160", 2, False)

        result = client.calculate()
        success = result.get('success', False)
        if success:
            res = result.get('result', {}).get('results', {})
            delta_K = res.get('comparison', {}).get('delta_K', 0)
            record_test("Calcolo scenario 6.4", True, f"delta_K={delta_K:.1f}%")
        else:
            record_test("Calcolo scenario 6.4", False)

        # ============================================================
        # TEST 7: PROFILI DIVERSI
        # ============================================================
        print_header("TEST 7: PROFILI DIVERSI")

        profiles = ["HEA 100", "HEA 120", "HEA 140", "HEA 160", "HEA 180", "HEA 200",
                   "HEB 100", "HEB 120", "HEB 140", "IPE 100", "IPE 120", "IPE 140"]

        for profile in profiles[:6]:  # Test solo i primi 6 per velocità
            client.reset()
            time.sleep(0.1)
            client.set_wall(400, 300, 30)
            client.set_masonry("Muratura in pietrame disordinata")
            client.add_opening(100, 0, 120, 210, 'Rettangolare', False)
            client.add_reinforcement(0, "Telaio chiuso in acciaio", profile, 2, False)

            result = client.calculate()
            success = result.get('success', False)
            if success:
                K_frame = result.get('result', {}).get('results', {}).get('modified', {}).get('K_frame', 0)
                record_test(f"Profilo {profile}", K_frame > 0, f"K_frame={K_frame:.0f}")
            else:
                record_test(f"Profilo {profile}", False)

        # ============================================================
        # TEST 8: NUMERO PROFILI
        # ============================================================
        print_header("TEST 8: NUMERO PROFILI (1-4)")

        k_values = []
        for n_profili in [1, 2, 3, 4]:
            client.reset()
            time.sleep(0.1)
            client.set_wall(400, 300, 30)
            client.set_masonry("Muratura in pietrame disordinata")
            client.add_opening(100, 0, 120, 210, 'Rettangolare', False)
            client.add_reinforcement(0, "Telaio chiuso in acciaio", "HEA 140", n_profili, False)

            result = client.calculate()
            success = result.get('success', False)
            if success:
                K_frame = result.get('result', {}).get('results', {}).get('modified', {}).get('K_frame', 0)
                k_values.append(K_frame)
                record_test(f"N. profili = {n_profili}", K_frame > 0, f"K_frame={K_frame:.0f}")
            else:
                record_test(f"N. profili = {n_profili}", False)

        # Verifica che K aumenti con più profili
        if len(k_values) >= 2:
            increasing = all(k_values[i] <= k_values[i+1] for i in range(len(k_values)-1))
            record_test("K cresce con n_profili", increasing, f"K={k_values}")

        # ============================================================
        # TEST 9: DIMENSIONI PARETE ESTREME
        # ============================================================
        print_header("TEST 9: DIMENSIONI PARETE ESTREME")

        wall_configs = [
            (200, 250, 20, "Parete piccola"),
            (500, 350, 30, "Parete media"),
            (1000, 500, 45, "Parete grande"),
            (1500, 600, 60, "Parete molto grande"),
        ]

        for length, height, thick, desc in wall_configs:
            client.reset()
            time.sleep(0.1)
            result = client.set_wall(length, height, thick)
            success = result.get('success', False)

            if success:
                client.set_masonry("Muratura in pietrame disordinata")
                client.add_opening(50, 0, min(100, length//4), min(180, height-50), 'Rettangolare', False)
                client.add_reinforcement(0, "Telaio chiuso in acciaio", "HEA 140", 2, False)

                result = client.calculate()
                calc_success = result.get('success', False)
                record_test(f"{desc} ({length}x{height}x{thick})", calc_success)
            else:
                record_test(f"{desc}", False)

        # ============================================================
        # TEST 10: SCREENSHOT
        # ============================================================
        print_header("TEST 10: SCREENSHOT")

        result = client.screenshot("hardtest_screenshot.png")
        success = result.get('success', False)
        record_test("Salvataggio screenshot", success, result.get('result', {}).get('saved', ''))

        # ============================================================
        # RIEPILOGO FINALE
        # ============================================================
        print_header("RIEPILOGO FINALE")

        total = results['passed'] + results['failed']
        pass_rate = (results['passed'] / total * 100) if total > 0 else 0

        print(f"\n  Test totali:   {total}")
        print(f"  Test passati:  {results['passed']} ({pass_rate:.1f}%)")
        print(f"  Test falliti:  {results['failed']}")

        if results['failed'] > 0:
            print("\n  Test falliti:")
            for test in results['tests']:
                if not test['success']:
                    print(f"    - {test['name']}: {test['details']}")

        print("\n" + "=" * 70)
        if results['failed'] == 0:
            print("  TUTTI I TEST SONO PASSATI!")
        else:
            print(f"  {results['failed']} TEST FALLITI - Verificare i dettagli sopra")
        print("=" * 70)

        return results['failed'] == 0

    except Exception as e:
        print(f"\nERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.disconnect()


if __name__ == '__main__':
    success = run_hardtest()
    sys.exit(0 if success else 1)
