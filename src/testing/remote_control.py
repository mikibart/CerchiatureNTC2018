"""
Remote Control Server per CerchiatureNTC2018
Server socket che permette controllo remoto dell'applicazione
Arch. Michelangelo Bartolotta

v2.0 - Con validazione input
"""

import json
import socket
import threading
import logging
import queue
import time
import re
from typing import Dict, Any, Callable, Optional, List, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Q_ARG, Qt

logger = logging.getLogger('RemoteControl')


# === VALIDATORI ===

class ValidationError(Exception):
    """Errore di validazione input."""
    pass


def validate_positive(value: float, name: str) -> float:
    """Valida che un valore sia positivo."""
    if value <= 0:
        raise ValidationError(f"{name} deve essere positivo (ricevuto: {value})")
    return value


def validate_non_negative(value: float, name: str) -> float:
    """Valida che un valore sia non negativo."""
    if value < 0:
        raise ValidationError(f"{name} non può essere negativo (ricevuto: {value})")
    return value


def validate_range(value: float, min_val: float, max_val: float, name: str) -> float:
    """Valida che un valore sia in un range."""
    if value < min_val or value > max_val:
        raise ValidationError(f"{name} deve essere tra {min_val} e {max_val} (ricevuto: {value})")
    return value


def validate_profile(profile: str) -> Tuple[str, int]:
    """
    Valida e parsa un profilo (es. 'HEA 100').
    Restituisce (tipo, dimensione).
    """
    if not profile or not isinstance(profile, str):
        raise ValidationError(f"Profilo non valido: '{profile}'")

    # Pattern: TIPO NUMERO (es. HEA 100, HEB 200, IPE 120)
    match = re.match(r'^(HEA|HEB|HEM|IPE|UPN|UPE)\s+(\d+)$', profile.strip().upper())
    if not match:
        raise ValidationError(
            f"Formato profilo non valido: '{profile}'. "
            f"Usare formato 'TIPO NUMERO' (es. 'HEA 100', 'HEB 200', 'IPE 120')"
        )

    tipo = match.group(1)
    dimensione = int(match.group(2))

    # Verifica dimensioni tipiche
    valid_sizes = {
        'HEA': [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300],
        'HEB': [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300],
        'HEM': [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300],
        'IPE': [80, 100, 120, 140, 160, 180, 200, 220, 240, 270, 300],
        'UPN': [80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300],
        'UPE': [80, 100, 120, 140, 160, 180, 200, 220, 240, 270, 300],
    }

    if dimensione not in valid_sizes.get(tipo, []):
        raise ValidationError(
            f"Dimensione profilo non standard: '{profile}'. "
            f"Dimensioni valide per {tipo}: {valid_sizes.get(tipo, [])}"
        )

    return (tipo, dimensione)


def check_opening_overlap(new_opening: Dict, existing_openings: List[Dict]) -> bool:
    """
    Verifica se una nuova apertura si sovrappone a quelle esistenti.
    Restituisce True se c'è sovrapposizione.
    """
    new_x1 = new_opening.get('x', 0)
    new_x2 = new_x1 + new_opening.get('width', 0)
    new_y1 = new_opening.get('y', 0)
    new_y2 = new_y1 + new_opening.get('height', 0)

    for existing in existing_openings:
        ex_x1 = existing.get('x', 0)
        ex_x2 = ex_x1 + existing.get('width', 0)
        ex_y1 = existing.get('y', 0)
        ex_y2 = ex_y1 + existing.get('height', 0)

        # Verifica sovrapposizione (due rettangoli si sovrappongono se
        # non sono separati né orizzontalmente né verticalmente)
        if not (new_x2 <= ex_x1 or new_x1 >= ex_x2 or new_y2 <= ex_y1 or new_y1 >= ex_y2):
            return True

    return False


class RemoteControlServer(QObject):
    """
    Server socket per controllo remoto dell'applicazione.
    Riceve comandi JSON e restituisce risposte JSON.
    Usa segnali per eseguire azioni nel thread principale Qt.
    """

    # Segnali per eseguire azioni nel thread Qt principale
    command_received = pyqtSignal(str, object)  # command, callback
    status_update = pyqtSignal(str)
    execute_in_main_thread = pyqtSignal(str, dict)  # command_json, params

    def __init__(self, main_window, host: str = 'localhost', port: int = 9999):
        super().__init__()
        self.main_window = main_window
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []

        # Queue per eseguire comandi nel main thread
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()

        # Timer per processare comandi nel main thread
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self._process_pending_commands)
        self.process_timer.start(50)  # Controlla ogni 50ms

        # Registra handler comandi
        self.commands = {
            'ping': self._cmd_ping,
            'get_state': self._cmd_get_state,
            'set_wall': self._cmd_set_wall,
            'set_masonry': self._cmd_set_masonry,
            'add_opening': self._cmd_add_opening,
            'add_reinforcement': self._cmd_add_reinforcement,
            'remove_opening': self._cmd_remove_opening,
            'calculate': self._cmd_calculate,
            'get_results': self._cmd_get_results,
            'reset': self._cmd_reset,
            'screenshot': self._cmd_screenshot,
            'get_openings': self._cmd_get_openings,
            'click_button': self._cmd_click_button,
            'set_tab': self._cmd_set_tab,
            'help': self._cmd_help,
        }

    def _process_pending_commands(self):
        """Processa comandi in coda nel main thread Qt."""
        try:
            while not self.command_queue.empty():
                cmd_id, command, params = self.command_queue.get_nowait()

                # Esegui comando nel main thread
                if command in self.commands:
                    try:
                        result = self.commands[command](params)

                        # Se il risultato contiene già success: False, propaga l'errore
                        if isinstance(result, dict) and result.get('success') is False:
                            self.result_queue.put((cmd_id, {
                                'success': False,
                                'command': command,
                                'error': result.get('error', 'Errore sconosciuto')
                            }))
                        else:
                            self.result_queue.put((cmd_id, {'success': True, 'command': command, 'result': result}))
                    except ValidationError as e:
                        # Gestione specifica errori di validazione
                        self.result_queue.put((cmd_id, {'success': False, 'command': command, 'error': str(e)}))
                    except Exception as e:
                        logger.exception(f"Errore esecuzione comando {command}")
                        self.result_queue.put((cmd_id, {'success': False, 'error': str(e)}))
                else:
                    self.result_queue.put((cmd_id, {'success': False, 'error': f'Comando sconosciuto: {command}'}))

        except queue.Empty:
            pass
        except Exception as e:
            logger.exception(f"Errore processando comandi: {e}")

    def start(self):
        """Avvia il server in un thread separato."""
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Remote Control Server avviato su {self.host}:{self.port}")
        self.status_update.emit(f"Remote Control attivo su porta {self.port}")

    def stop(self):
        """Ferma il server."""
        self.running = False

        # Ferma il timer di processamento
        if hasattr(self, 'process_timer'):
            self.process_timer.stop()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        logger.info("Remote Control Server fermato")

    def _run_server(self):
        """Loop principale del server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            while self.running:
                try:
                    client, addr = self.server_socket.accept()
                    logger.info(f"Client connesso: {addr}")
                    self.clients.append(client)
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Errore accept: {e}")
        except Exception as e:
            logger.error(f"Errore server: {e}")

    def _handle_client(self, client: socket.socket, addr):
        """Gestisce un client connesso."""
        buffer = ""
        try:
            while self.running:
                try:
                    data = client.recv(4096).decode('utf-8')
                    if not data:
                        break

                    buffer += data

                    # Processa messaggi completi (terminati da newline)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            response = self._process_command(line.strip())
                            client.sendall((json.dumps(response) + '\n').encode('utf-8'))

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Errore client {addr}: {e}")
                    break
        finally:
            client.close()
            if client in self.clients:
                self.clients.remove(client)
            logger.info(f"Client disconnesso: {addr}")

    def _process_command(self, message: str) -> Dict[str, Any]:
        """Processa un comando JSON usando la queue per thread safety."""
        try:
            cmd_data = json.loads(message)
            command = cmd_data.get('command', '')
            params = cmd_data.get('params', {})

            # Genera ID univoco per questo comando
            cmd_id = f"{command}_{time.time()}"

            # Metti il comando in coda
            self.command_queue.put((cmd_id, command, params))

            # Attendi risultato (timeout 30 secondi)
            start_time = time.time()
            while time.time() - start_time < 30:
                try:
                    result_id, result = self.result_queue.get(timeout=0.1)
                    if result_id == cmd_id:
                        return result
                    else:
                        # Rimetti in coda risultati di altri comandi
                        self.result_queue.put((result_id, result))
                except queue.Empty:
                    continue

            return {'success': False, 'error': 'Timeout attesa risposta'}

        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON non valido: {e}'}
        except Exception as e:
            logger.exception(f"Errore processando comando: {e}")
            return {'success': False, 'error': str(e)}

    # === COMANDI ===

    def _cmd_ping(self, params: Dict) -> Dict:
        """Test connessione."""
        return {'message': 'pong', 'status': 'running'}

    def _cmd_help(self, params: Dict) -> Dict:
        """Restituisce lista comandi disponibili."""
        commands_help = {
            'ping': 'Test connessione',
            'get_state': 'Ottieni stato completo applicazione',
            'set_wall': 'Imposta parete: {length, height, thickness}',
            'set_masonry': 'Imposta muratura: {type, gamma_m, fc}',
            'add_opening': 'Aggiungi apertura: {x, y, width, height, type, existing}',
            'add_reinforcement': 'Aggiungi rinforzo: {opening_index, type, profile, n_profiles}',
            'remove_opening': 'Rimuovi apertura: {index}',
            'calculate': 'Esegui calcolo',
            'get_results': 'Ottieni risultati calcolo',
            'get_openings': 'Ottieni lista aperture',
            'reset': 'Reset applicazione',
            'screenshot': 'Salva screenshot: {path}',
            'set_tab': 'Cambia tab: {index} (0=Input, 1=Aperture, 2=Calcolo, 3=Report)',
            'click_button': 'Simula click: {button_name}',
        }
        return {'commands': commands_help}

    def _cmd_get_state(self, params: Dict) -> Dict:
        """Restituisce lo stato completo dell'applicazione."""
        try:
            input_module = self.main_window.input_module
            openings_module = self.main_window.openings_module

            # Ottieni aperture da openings_module (sorgente canonica)
            openings_list = []
            if hasattr(openings_module, 'openings') and isinstance(openings_module.openings, list):
                openings_list = openings_module.openings

            # Costruisci lista aperture con gestione sicura
            openings_data = []
            for op in openings_list:
                if isinstance(op, dict):
                    opening_info = {
                        'x': op.get('x', 0),
                        'y': op.get('y', 0),
                        'width': op.get('width', 0),
                        'height': op.get('height', 0),
                        'type': op.get('type', 'Rettangolare'),
                        'existing': op.get('existing', False),
                        'has_reinforcement': 'rinforzo' in op,
                        'reinforcement_type': op.get('rinforzo', {}).get('tipo', None) if 'rinforzo' in op else None
                    }
                    openings_data.append(opening_info)

            state = {
                'wall': {
                    'length': input_module.wall_length.value(),
                    'height': input_module.wall_height.value(),
                    'thickness': input_module.wall_thickness.value(),
                },
                'masonry': {
                    'type': input_module.masonry_type.currentText(),
                    'knowledge_level': input_module.knowledge_level.currentText() if hasattr(input_module, 'knowledge_level') else '',
                    'fcm': input_module.fcm.value() if hasattr(input_module, 'fcm') else 0,
                    'tau0': input_module.tau0.value() if hasattr(input_module, 'tau0') else 0,
                    'E': input_module.E_modulus.value() if hasattr(input_module, 'E_modulus') else 0,
                    'G': input_module.G_modulus.value() if hasattr(input_module, 'G_modulus') else 0,
                },
                'openings': openings_data,
                'openings_count': len(openings_data),
                'current_tab': self.main_window.tabs.currentIndex(),
            }
            return state
        except Exception as e:
            logger.exception("Errore get_state")
            return {'error': str(e)}

    def _cmd_set_wall(self, params: Dict) -> Dict:
        """Imposta dati parete con validazione."""
        try:
            input_module = self.main_window.input_module

            # Validazione dimensioni
            length = int(params.get('length', input_module.wall_length.value()))
            height = int(params.get('height', input_module.wall_height.value()))
            thickness = int(params.get('thickness', input_module.wall_thickness.value()))

            # Valida valori positivi
            validate_positive(length, "Lunghezza parete")
            validate_positive(height, "Altezza parete")
            validate_positive(thickness, "Spessore parete")

            # Valida range ragionevoli (cm)
            validate_range(length, 50, 5000, "Lunghezza parete")
            validate_range(height, 50, 2000, "Altezza parete")
            validate_range(thickness, 5, 200, "Spessore parete")

            # Imposta valori
            input_module.wall_length.setValue(length)
            input_module.wall_height.setValue(height)
            input_module.wall_thickness.setValue(thickness)

            # Aggiorna canvas
            if hasattr(input_module, 'on_wall_changed'):
                input_module.on_wall_changed()

            return {'wall_set': True, 'dimensions': {'length': length, 'height': height, 'thickness': thickness}}

        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.exception("Errore set_wall")
            return {'error': str(e)}

    def _cmd_set_masonry(self, params: Dict) -> Dict:
        """Imposta tipo muratura e coefficienti con validazione."""
        try:
            input_module = self.main_window.input_module

            if 'type' in params:
                masonry_type = params['type']

                # Ottieni tipi muratura validi dal combobox
                valid_types = [input_module.masonry_type.itemText(i)
                              for i in range(input_module.masonry_type.count())]

                index = input_module.masonry_type.findText(masonry_type)
                if index < 0:
                    # Tipo non trovato - restituisci errore con tipi validi
                    raise ValidationError(
                        f"Tipo muratura non valido: '{masonry_type}'. "
                        f"Tipi validi: {', '.join(valid_types[:5])}..."
                    )
                input_module.masonry_type.setCurrentIndex(index)

            # Livello di conoscenza per FC
            if 'knowledge_level' in params and hasattr(input_module, 'knowledge_level'):
                level = params['knowledge_level']
                index = input_module.knowledge_level.findText(level)
                if index < 0:
                    valid_levels = [input_module.knowledge_level.itemText(i)
                                   for i in range(input_module.knowledge_level.count())]
                    raise ValidationError(
                        f"Livello conoscenza non valido: '{level}'. "
                        f"Livelli validi: {', '.join(valid_levels)}"
                    )
                input_module.knowledge_level.setCurrentIndex(index)

            # Parametri meccanici personalizzati (da importazione PT3)
            if 'fcm' in params and hasattr(input_module, 'fcm'):
                input_module.fcm.setValue(float(params['fcm']))

            if 'tau0' in params and hasattr(input_module, 'tau0'):
                input_module.tau0.setValue(float(params['tau0']))

            if 'E' in params and hasattr(input_module, 'E_modulus'):
                input_module.E_modulus.setValue(int(params['E']))

            if 'G' in params and hasattr(input_module, 'G_modulus'):
                input_module.G_modulus.setValue(int(params['G']))

            if 'gamma_m' in params and hasattr(input_module, 'gamma'):
                input_module.gamma.setValue(float(params['gamma_m']))

            return {'masonry_set': True}

        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.exception("Errore set_masonry")
            return {'error': str(e)}

    def _cmd_add_opening(self, params: Dict) -> Dict:
        """Aggiunge un'apertura con validazione completa."""
        try:
            input_module = self.main_window.input_module
            openings_module = self.main_window.openings_module

            # Ottieni dimensioni parete per validazione
            wall_length = input_module.wall_length.value()
            wall_height = input_module.wall_height.value()

            # Estrai e valida parametri
            x = int(params.get('x', 50))
            y = int(params.get('y', 0))
            width = int(params.get('width', 120))
            height = int(params.get('height', 210))
            opening_type = params.get('type', 'Rettangolare')

            # Validazione tipo apertura
            valid_types = ['Rettangolare', 'Circolare', 'Arco']
            if opening_type not in valid_types:
                raise ValidationError(f"Tipo apertura non valido: '{opening_type}'. Tipi validi: {valid_types}")

            # Per aperture circolari, usa il diametro
            if opening_type == 'Circolare':
                diameter = int(params.get('diameter', width))
                validate_positive(diameter, "Diametro")
                if diameter > wall_height:
                    raise ValidationError(
                        f"Diametro ({diameter}cm) maggiore dell'altezza parete ({wall_height}cm)"
                    )
                if diameter > wall_length:
                    raise ValidationError(
                        f"Diametro ({diameter}cm) maggiore della lunghezza parete ({wall_length}cm)"
                    )
                width = diameter
                height = diameter

            # Validazione dimensioni positive
            validate_positive(width, "Larghezza apertura")
            validate_positive(height, "Altezza apertura")

            # Validazione posizione non negativa
            validate_non_negative(x, "Posizione X")
            validate_non_negative(y, "Posizione Y")

            # Validazione che l'apertura sia dentro la parete
            if x + width > wall_length:
                raise ValidationError(
                    f"Apertura fuori dai limiti: X({x}) + larghezza({width}) = {x+width} > lunghezza parete({wall_length})"
                )
            if y + height > wall_height:
                raise ValidationError(
                    f"Apertura fuori dai limiti: Y({y}) + altezza({height}) = {y+height} > altezza parete({wall_height})"
                )

            # Validazione dimensioni minime
            if width < 10:
                raise ValidationError(f"Larghezza apertura troppo piccola: {width}cm (minimo 10cm)")
            if height < 10:
                raise ValidationError(f"Altezza apertura troppo piccola: {height}cm (minimo 10cm)")

            # Crea oggetto apertura
            opening = {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'type': opening_type,
                'existing': params.get('existing', False)
            }

            # Dati speciali per circolari
            if opening_type == 'Circolare':
                opening['circular_data'] = {
                    'diameter': width,
                    'custom_center': False,
                    'center_x_offset': 0,
                    'center_y_offset': 0
                }

            # Verifica sovrapposizioni con aperture esistenti
            if hasattr(openings_module, 'openings'):
                if check_opening_overlap(opening, openings_module.openings):
                    raise ValidationError(
                        f"L'apertura si sovrappone a un'apertura esistente (X={x}, Y={y}, W={width}, H={height})"
                    )

            # Aggiungi solo a openings_module.openings (sorgente canonica)
            index = -1

            if hasattr(openings_module, 'openings'):
                openings_module.openings.append(opening)
                index = len(openings_module.openings) - 1

                # Aggiorna UI openings_module
                if hasattr(openings_module, 'refresh_tree'):
                    openings_module.refresh_tree()
                if hasattr(openings_module, 'update_canvas'):
                    openings_module.update_canvas()

            if index < 0:
                return {'error': 'Impossibile trovare lista aperture'}

            return {'opening_added': True, 'index': index}

        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.exception("Errore add_opening")
            return {'error': str(e)}

    def _cmd_add_reinforcement(self, params: Dict) -> Dict:
        """Aggiunge rinforzo a un'apertura con validazione completa."""
        try:
            openings_module = self.main_window.openings_module
            input_module = self.main_window.input_module

            # Verifica che esistano aperture
            if not hasattr(openings_module, 'openings') or len(openings_module.openings) == 0:
                raise ValidationError("Nessuna apertura presente. Aggiungere prima un'apertura.")

            # Validazione indice
            index = int(params.get('opening_index', 0))
            n_openings = len(openings_module.openings)

            if index < 0:
                raise ValidationError(f"Indice apertura non può essere negativo: {index}")
            if index >= n_openings:
                raise ValidationError(
                    f"Indice apertura fuori range: {index}. "
                    f"Aperture disponibili: 0-{n_openings-1} (totale: {n_openings})"
                )

            # Validazione profilo
            profile = params.get('profile', 'HEA 100')
            validate_profile(profile)  # Lancia ValidationError se invalido

            # Validazione n_profiles
            n_profiles = int(params.get('n_profiles', 1))
            if n_profiles <= 0:
                raise ValidationError(f"Numero profili deve essere positivo: {n_profiles}")
            if n_profiles > 10:
                raise ValidationError(f"Numero profili eccessivo: {n_profiles} (massimo 10)")

            # Validazione tipo rinforzo
            rinforzo_type = params.get('type', 'Solo architrave in acciaio')
            valid_reinforcement_types = [
                'Solo architrave in acciaio',
                'Telaio chiuso in acciaio',
                'Telaio aperto in acciaio',
                'Profili accoppiati',
                'Rinforzo calandrato nell\'arco',
                # Aggiungi anche varianti con underscore per compatibilità
            ]

            # Normalizza tipo (converti underscore in spazi, gestisci case)
            normalized_type = rinforzo_type.replace('_', ' ').strip()

            # Mappa tipi abbreviati
            type_mapping = {
                'architrave': 'Solo architrave in acciaio',
                'telaio chiuso': 'Telaio chiuso in acciaio',
                'telaio aperto': 'Telaio aperto in acciaio',
                'telaio_chiuso': 'Telaio chiuso in acciaio',
                'telaio_aperto': 'Telaio aperto in acciaio',
                'profili accoppiati': 'Profili accoppiati',
                'profili_accoppiati': 'Profili accoppiati',
                'calandrato': 'Rinforzo calandrato nell\'arco',
                'arco': 'Rinforzo calandrato nell\'arco',
            }

            # Cerca corrispondenza
            matched_type = None
            normalized_lower = normalized_type.lower()

            if normalized_lower in type_mapping:
                matched_type = type_mapping[normalized_lower]
            else:
                # Cerca match parziale
                for valid_type in valid_reinforcement_types:
                    if normalized_lower in valid_type.lower() or valid_type.lower() in normalized_lower:
                        matched_type = valid_type
                        break

            if not matched_type:
                raise ValidationError(
                    f"Tipo rinforzo non valido: '{rinforzo_type}'. "
                    f"Tipi validi: {', '.join(valid_reinforcement_types)}"
                )

            rinforzo_type = matched_type

            # Crea oggetto rinforzo
            rinforzo = {
                'tipo': rinforzo_type,
                'materiale': params.get('material', 'acciaio'),
                'classe_acciaio': params.get('steel_class', 'S235'),
                'esistente': params.get('existing', False),
                'architrave': {
                    'profilo': profile,
                    'n_profili': n_profiles,
                    'interasse': 0,
                    'disposizione': 'In linea',
                    'ruotato': False
                },
                'note': ''
            }

            # Per calandrato
            if 'calandrato' in rinforzo_type.lower():
                rinforzo['arco'] = {
                    'tipo_apertura': params.get('arch_type', 'Arco a tutto sesto'),
                    'raggio': params.get('radius', 150),
                    'freccia': params.get('rise', 30),
                    'profilo': profile,
                    'n_profili': n_profiles,
                    'metodo': params.get('bending_method', 'A freddo')
                }

            openings_module.openings[index]['rinforzo'] = rinforzo

            # Aggiorna UI
            if hasattr(openings_module, 'refresh_tree'):
                openings_module.refresh_tree()
            if hasattr(openings_module, 'update_canvas'):
                openings_module.update_canvas()
            if hasattr(input_module, 'update_openings_list'):
                input_module.update_openings_list()
            if hasattr(input_module, 'wall_canvas'):
                input_module.wall_canvas.update()

            return {'reinforcement_added': True, 'opening_index': index, 'type': rinforzo_type}

        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.exception("Errore add_reinforcement")
            return {'error': str(e)}

    def _cmd_remove_opening(self, params: Dict) -> Dict:
        """Rimuove un'apertura."""
        try:
            openings_module = self.main_window.openings_module
            input_module = self.main_window.input_module

            # Ottieni lista aperture
            if hasattr(openings_module, 'openings'):
                openings = openings_module.openings
            elif hasattr(input_module, 'wall_canvas') and hasattr(input_module.wall_canvas, 'openings'):
                openings = input_module.wall_canvas.openings
            else:
                return {'error': 'Impossibile trovare lista aperture'}

            index = params.get('index', -1)

            if 0 <= index < len(openings):
                openings.pop(index)

                # Aggiorna UI
                if hasattr(openings_module, 'refresh_tree'):
                    openings_module.refresh_tree()
                if hasattr(openings_module, 'update_canvas'):
                    openings_module.update_canvas()
                if hasattr(input_module, 'update_openings_list'):
                    input_module.update_openings_list()
                if hasattr(input_module, 'wall_canvas'):
                    input_module.wall_canvas.update()

                return {'removed': True}
            else:
                return {'error': 'Indice non valido'}
        except Exception as e:
            logger.exception("Errore remove_opening")
            return {'error': str(e)}

    def _cmd_get_openings(self, params: Dict) -> Dict:
        """Restituisce lista aperture con dettagli."""
        try:
            openings_module = self.main_window.openings_module
            input_module = self.main_window.input_module

            # Ottieni lista aperture
            if hasattr(openings_module, 'openings'):
                openings_list = openings_module.openings
            elif hasattr(input_module, 'wall_canvas') and hasattr(input_module.wall_canvas, 'openings'):
                openings_list = input_module.wall_canvas.openings
            else:
                return {'openings': [], 'count': 0}

            openings = []
            for i, op in enumerate(openings_list):
                opening_info = {
                    'index': i,
                    'x': op.get('x'),
                    'y': op.get('y'),
                    'width': op.get('width'),
                    'height': op.get('height'),
                    'type': op.get('type'),
                    'existing': op.get('existing', False),
                }

                if 'rinforzo' in op:
                    r = op['rinforzo']
                    opening_info['reinforcement'] = {
                        'type': r.get('tipo'),
                        'material': r.get('materiale'),
                        'profile': r.get('architrave', {}).get('profilo'),
                        'n_profiles': r.get('architrave', {}).get('n_profili', 1),
                        'existing': r.get('esistente', False)
                    }
                    if 'arco' in r:
                        opening_info['reinforcement']['arc'] = r['arco']

                openings.append(opening_info)

            return {'openings': openings, 'count': len(openings)}
        except Exception as e:
            logger.exception("Errore get_openings")
            return {'error': str(e)}

    def _cmd_calculate(self, params: Dict) -> Dict:
        """Esegue il calcolo."""
        try:
            # Passa al tab calcolo
            self.main_window.tabs.setCurrentIndex(2)

            calc_module = self.main_window.calc_module
            input_module = self.main_window.input_module
            openings_module = self.main_window.openings_module

            # Raccogli dati
            project_data = input_module.collect_data()

            # Aggiungi aperture da openings_module nel formato corretto
            # Il calc_module cerca project_data['openings_module']['openings']
            if hasattr(openings_module, 'openings'):
                project_data['openings_module'] = {
                    'openings': openings_module.openings
                }

            # Imposta dati progetto
            calc_module.set_project_data(project_data)

            # Esegui calcolo
            calc_module.run_calculation()

            # Attendi che il calcolo finisca e leggi risultati
            results = calc_module.results if hasattr(calc_module, 'results') else {}

            # Estrai risultati principali
            summary = {}
            if results and 'original' in results:
                summary['original'] = {
                    'K': results['original'].get('K', 0),
                    'V_t1': results['original'].get('V_t1', 0),
                    'V_t2': results['original'].get('V_t2', 0),
                    'V_t3': results['original'].get('V_t3', 0),
                }
            if results and 'modified' in results:
                summary['modified'] = {
                    'K': results['modified'].get('K', 0),
                    'V_t1': results['modified'].get('V_t1', 0),
                    'V_t2': results['modified'].get('V_t2', 0),
                    'V_t3': results['modified'].get('V_t3', 0),
                    'K_frame': results['modified'].get('K_cerchiature', 0),
                }
            if results and 'comparison' in results:
                summary['comparison'] = results['comparison']

            return {'calculated': True, 'results': summary}

        except Exception as e:
            logger.exception("Errore calcolo")
            return {'error': str(e)}

    def _cmd_get_results(self, params: Dict) -> Dict:
        """Restituisce gli ultimi risultati del calcolo."""
        try:
            calc_module = self.main_window.calc_module
            if hasattr(calc_module, 'last_results') and calc_module.last_results:
                return {'results': calc_module.last_results}
            else:
                return {'results': None, 'message': 'Nessun calcolo eseguito'}
        except Exception as e:
            return {'error': str(e)}

    def _cmd_reset(self, params: Dict) -> Dict:
        """Reset dell'applicazione."""
        try:
            input_module = self.main_window.input_module
            openings_module = self.main_window.openings_module
            calc_module = self.main_window.calc_module

            # Reset moduli
            if hasattr(input_module, 'reset'):
                input_module.reset()
            if hasattr(openings_module, 'reset'):
                openings_module.reset()
            if hasattr(calc_module, 'reset'):
                calc_module.reset()

            # Svuota esplicitamente openings (fonte canonica)
            if hasattr(openings_module, 'openings'):
                openings_module.openings = []
                if hasattr(openings_module, 'refresh_tree'):
                    openings_module.refresh_tree()
                if hasattr(openings_module, 'update_canvas'):
                    openings_module.update_canvas()

            return {'reset': True}
        except Exception as e:
            logger.exception("Errore reset")
            return {'error': str(e)}

    def _cmd_set_tab(self, params: Dict) -> Dict:
        """Cambia tab attivo."""
        index = params.get('index', 0)
        if 0 <= index < self.main_window.tabs.count():
            self.main_window.tabs.setCurrentIndex(index)
            return {'tab_set': index}
        else:
            return {'error': 'Indice tab non valido'}

    def _cmd_screenshot(self, params: Dict) -> Dict:
        """Salva screenshot della finestra."""
        try:
            from PyQt5.QtGui import QPixmap
            path = params.get('path', 'screenshot.png')
            pixmap = self.main_window.grab()
            pixmap.save(path)
            return {'saved': path}
        except Exception as e:
            return {'error': str(e)}

    def _cmd_click_button(self, params: Dict) -> Dict:
        """Simula click su un pulsante (per nome oggetto)."""
        button_name = params.get('button_name', '')
        # Trova il pulsante
        from PyQt5.QtWidgets import QPushButton
        for widget in self.main_window.findChildren(QPushButton):
            if widget.objectName() == button_name or widget.text() == button_name:
                widget.click()
                return {'clicked': button_name}
        return {'error': f'Pulsante non trovato: {button_name}'}


def integrate_remote_control(main_window, port: int = 9999):
    """
    Integra il Remote Control Server nella MainWindow.

    Chiamare questa funzione dopo aver creato la MainWindow:

        from src.testing.remote_control import integrate_remote_control
        integrate_remote_control(main_window, port=9999)
    """
    server = RemoteControlServer(main_window, port=port)
    server.start()

    # Salva riferimento nel main_window per evitare garbage collection
    main_window._remote_control_server = server

    return server
