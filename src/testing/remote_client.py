"""
Remote Control Client per CerchiatureNTC2018
Client per controllare l'applicazione da remoto via socket
Arch. Michelangelo Bartolotta
"""

import socket
import json
import time
from typing import Dict, Any, Optional


class RemoteClient:
    """Client per controllo remoto dell'applicazione CerchiatureNTC2018."""

    def __init__(self, host: str = 'localhost', port: int = 9999):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self) -> bool:
        """Connette al server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(30)
            print(f"Connesso a {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Errore connessione: {e}")
            return False

    def disconnect(self):
        """Disconnette dal server."""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnesso")

    def send_command(self, command: str, params: Dict = None) -> Dict[str, Any]:
        """
        Invia un comando al server.

        Args:
            command: Nome del comando
            params: Parametri del comando

        Returns:
            Risposta del server
        """
        if not self.socket:
            return {'success': False, 'error': 'Non connesso'}

        try:
            message = json.dumps({
                'command': command,
                'params': params or {}
            }) + '\n'

            self.socket.sendall(message.encode('utf-8'))

            # Ricevi risposta
            response = ''
            while '\n' not in response:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                response += data

            return json.loads(response.strip())

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === METODI HELPER ===

    def ping(self) -> bool:
        """Test connessione."""
        result = self.send_command('ping')
        return result.get('success', False)

    def get_state(self) -> Dict:
        """Ottiene stato applicazione."""
        return self.send_command('get_state')

    def set_wall(self, length: int, height: int, thickness: int) -> Dict:
        """Imposta dati parete."""
        return self.send_command('set_wall', {
            'length': length,
            'height': height,
            'thickness': thickness
        })

    def set_masonry(self, masonry_type: str, gamma_m: float = 2.0, fc: float = 1.35) -> Dict:
        """Imposta tipo muratura."""
        return self.send_command('set_masonry', {
            'type': masonry_type,
            'gamma_m': gamma_m,
            'fc': fc
        })

    def add_opening(self, x: int, y: int, width: int, height: int,
                    opening_type: str = 'Rettangolare', existing: bool = False) -> Dict:
        """Aggiunge apertura rettangolare."""
        return self.send_command('add_opening', {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'type': opening_type,
            'existing': existing
        })

    def add_circular_opening(self, x: int, y: int, diameter: int,
                             existing: bool = False) -> Dict:
        """Aggiunge apertura circolare."""
        return self.send_command('add_opening', {
            'x': x,
            'y': y,
            'width': diameter,
            'height': diameter,
            'diameter': diameter,
            'type': 'Circolare',
            'existing': existing
        })

    def add_reinforcement(self, opening_index: int, reinforcement_type: str,
                          profile: str = 'HEA 100', n_profiles: int = 1,
                          existing: bool = False) -> Dict:
        """Aggiunge rinforzo a un'apertura."""
        return self.send_command('add_reinforcement', {
            'opening_index': opening_index,
            'type': reinforcement_type,
            'profile': profile,
            'n_profiles': n_profiles,
            'existing': existing
        })

    def calculate(self) -> Dict:
        """Esegue il calcolo."""
        return self.send_command('calculate')

    def get_results(self) -> Dict:
        """Ottiene risultati calcolo."""
        return self.send_command('get_results')

    def get_openings(self) -> Dict:
        """Ottiene lista aperture."""
        return self.send_command('get_openings')

    def reset(self) -> Dict:
        """Reset applicazione."""
        return self.send_command('reset')

    def screenshot(self, path: str) -> Dict:
        """Salva screenshot."""
        return self.send_command('screenshot', {'path': path})

    def set_tab(self, index: int) -> Dict:
        """Cambia tab attivo."""
        return self.send_command('set_tab', {'index': index})

    def help(self) -> Dict:
        """Ottiene lista comandi."""
        return self.send_command('help')


def run_demo_test():
    """
    Esegue un test dimostrativo completo.

    Avviare prima l'applicazione con:
        python main.py --remote
    """
    print("=" * 60)
    print("TEST DIMOSTRATIVO - CerchiatureNTC2018 Remote Control")
    print("=" * 60)

    client = RemoteClient()

    if not client.connect():
        print("ERRORE: Impossibile connettersi al server.")
        print("Assicurarsi che l'applicazione sia avviata con: python main.py --remote")
        return

    try:
        # Test ping
        print("\n1. Test connessione...")
        if client.ping():
            print("   OK - Server raggiungibile")
        else:
            print("   ERRORE - Ping fallito")
            return

        # Reset
        print("\n2. Reset applicazione...")
        client.reset()
        time.sleep(0.5)

        # Imposta parete
        print("\n3. Impostazione parete...")
        result = client.set_wall(length=500, height=350, thickness=30)
        print(f"   Parete: 500x350x30 cm - {result.get('success', False)}")

        # Imposta muratura
        print("\n4. Impostazione muratura...")
        result = client.set_masonry("Muratura in pietrame disordinata", gamma_m=2.0, fc=1.35)
        print(f"   Muratura impostata - {result.get('success', False)}")

        # Aggiungi apertura rettangolare
        print("\n5. Aggiunta apertura rettangolare...")
        result = client.add_opening(x=50, y=0, width=120, height=210,
                                    opening_type='Rettangolare', existing=False)
        print(f"   Apertura aggiunta: index={result.get('result', {}).get('index')}")

        # Aggiungi rinforzo
        print("\n6. Aggiunta rinforzo...")
        result = client.add_reinforcement(
            opening_index=0,
            reinforcement_type="Telaio chiuso in acciaio",
            profile="HEA 140",
            n_profiles=2
        )
        print(f"   Rinforzo aggiunto - {result.get('success', False)}")

        # Aggiungi apertura circolare
        print("\n7. Aggiunta apertura circolare...")
        result = client.add_circular_opening(x=300, y=100, diameter=100, existing=False)
        print(f"   Apertura circolare aggiunta: index={result.get('result', {}).get('index')}")

        # Aggiungi rinforzo calandrato
        print("\n8. Aggiunta rinforzo calandrato...")
        result = client.add_reinforcement(
            opening_index=1,
            reinforcement_type="Rinforzo calandrato nell'arco",
            profile="HEA 100",
            n_profiles=1
        )
        print(f"   Rinforzo calandrato aggiunto - {result.get('success', False)}")

        # Verifica stato
        print("\n9. Verifica stato aperture...")
        result = client.get_openings()
        openings = result.get('result', {}).get('openings', [])
        for op in openings:
            print(f"   A{op['index']+1}: {op['type']} {op['width']}x{op['height']}cm", end='')
            if op.get('reinforcement'):
                print(f" - {op['reinforcement']['type']}", end='')
            print()

        # Esegui calcolo
        print("\n10. Esecuzione calcolo...")
        result = client.calculate()
        if result.get('success'):
            results = result.get('result', {}).get('results', {})

            if 'original' in results:
                orig = results['original']
                print(f"    Stato di fatto:")
                print(f"      K = {orig.get('K', 0):.1f} kN/m")
                print(f"      V_t1 = {orig.get('V_t1', 0):.1f} kN")

            if 'modified' in results:
                mod = results['modified']
                print(f"    Stato di progetto:")
                print(f"      K = {mod.get('K', 0):.1f} kN/m")
                print(f"      V_t1 = {mod.get('V_t1', 0):.1f} kN")
                print(f"      K_cerchiature = {mod.get('K_frame', 0):.1f} kN/m")

            if 'comparison' in results:
                comp = results['comparison']
                print(f"    Variazioni:")
                print(f"      ΔK = {comp.get('delta_K', 0):.1f}%")
                print(f"      ΔV = {comp.get('delta_V', 0):.1f}%")
        else:
            print(f"    ERRORE: {result.get('error', 'sconosciuto')}")

        # Screenshot
        print("\n11. Salvataggio screenshot...")
        result = client.screenshot("test_screenshot.png")
        if result.get('success'):
            print(f"    Screenshot salvato: {result.get('result', {}).get('saved')}")
        else:
            print(f"    ERRORE: {result.get('error')}")

        print("\n" + "=" * 60)
        print("TEST COMPLETATO")
        print("=" * 60)

    except Exception as e:
        print(f"\nERRORE: {e}")
    finally:
        client.disconnect()


def interactive_mode():
    """Modalità interattiva per inviare comandi manualmente."""
    print("=" * 60)
    print("MODALITA' INTERATTIVA - CerchiatureNTC2018 Remote Control")
    print("=" * 60)
    print("Digitare 'help' per lista comandi, 'quit' per uscire\n")

    client = RemoteClient()

    if not client.connect():
        print("ERRORE: Impossibile connettersi al server.")
        return

    try:
        while True:
            try:
                cmd_input = input(">>> ").strip()

                if not cmd_input:
                    continue

                if cmd_input.lower() == 'quit':
                    break

                # Parse comando
                parts = cmd_input.split(maxsplit=1)
                command = parts[0]

                # Parse parametri JSON opzionali
                params = {}
                if len(parts) > 1:
                    try:
                        params = json.loads(parts[1])
                    except json.JSONDecodeError:
                        # Prova come chiave=valore
                        for pair in parts[1].split():
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                try:
                                    params[key] = int(value)
                                except ValueError:
                                    try:
                                        params[key] = float(value)
                                    except ValueError:
                                        params[key] = value

                result = client.send_command(command, params)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            except KeyboardInterrupt:
                print("\nUscita...")
                break
            except Exception as e:
                print(f"Errore: {e}")

    finally:
        client.disconnect()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        run_demo_test()
