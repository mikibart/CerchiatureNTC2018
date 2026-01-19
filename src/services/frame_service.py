"""
FrameService - Servizio Calcolo Cerchiature
============================================

Service per il calcolo dei telai di rinforzo (cerchiature):
- Telai in acciaio (standard e avanzato)
- Telai in cemento armato
- Archi e aperture curve
- Verifiche connessioni

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging
import json
import os

from src.data.ntc2018_constants import NTC2018
from src.core.engine.steel_frame import SteelFrameCalculator
from src.core.engine.steel_frame_advanced import SteelFrameAdvancedCalculator
from src.core.engine.concrete_frame import ConcreteFrameCalculator
from src.core.engine.arch_reinforcement import ArchReinforcementManager
from src.core.engine.connections import ConnectionsVerifier

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    """Risultato calcolo singola cerchiatura"""
    # Rigidezza e resistenza
    K_frame: float = 0.0        # Rigidezza telaio [kN/m]
    V_resistance: float = 0.0   # Resistenza telaio [kN]

    # Sollecitazioni
    M_max: float = 0.0          # Momento massimo [kN·m]
    V_max: float = 0.0          # Taglio massimo [kN]
    N_max: float = 0.0          # Sforzo normale massimo [kN]

    # Proprietà
    materiale: str = ""         # 'acciaio' o 'ca'
    tipo: str = ""              # Tipo telaio

    # Info arco (se presente)
    is_arch: bool = False
    arch_radius: float = 0.0
    arch_length: float = 0.0

    # Verifiche
    bending_ok: bool = True
    connections: Dict = field(default_factory=dict)

    # Errori e warning
    error: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Converte in dizionario per compatibilità"""
        return {
            'K_frame': self.K_frame,
            'V_resistance': self.V_resistance,
            'M_max': self.M_max,
            'V_max': self.V_max,
            'N_max': self.N_max,
            'materiale': self.materiale,
            'tipo': self.tipo,
            'is_arch': self.is_arch,
            'arch_radius': self.arch_radius,
            'arch_length': self.arch_length,
            'bending_ok': self.bending_ok,
            'connections': self.connections,
            'error': self.error,
            'warnings': self.warnings
        }


class FrameService:
    """
    Servizio per il calcolo delle cerchiature.

    Gestisce:
    - Selezione del calculator appropriato (acciaio, c.a., avanzato)
    - Calcolo forze stimate sul telaio
    - Calcolo resistenza telaio
    - Verifica calandrabilità per archi
    - Verifica connessioni

    Esempio:
        service = FrameService()
        result = service.calculate_frame(opening, rinforzo, wall_data)
        print(f"K = {result['K_frame']:.1f} kN/m")
    """

    VERSION = "1.0.0"

    def __init__(self):
        """Inizializza i calculator"""
        self.steel_calc = SteelFrameCalculator()
        self.steel_advanced_calc = SteelFrameAdvancedCalculator()
        self.concrete_calc = ConcreteFrameCalculator()
        self.arch_manager = ArchReinforcementManager()
        self.connections_verifier = ConnectionsVerifier()

        # Cache moduli plastici profili
        self._plastic_moduli_cache = None

        logger.info(f"FrameService inizializzato - v{self.VERSION}")

    def calculate_frame(self, opening: Dict, rinforzo: Dict,
                       wall_data: Dict) -> Dict:
        """
        Calcola rigidezza e resistenza di una cerchiatura.

        Args:
            opening: Dict con geometria apertura
            rinforzo: Dict con dati rinforzo (profili, materiale, etc.)
            wall_data: Dict con dati parete

        Returns:
            Dict con risultati (K_frame, V_resistance, etc.)
        """
        result = FrameResult()
        result.materiale = rinforzo.get('materiale', 'acciaio')
        result.tipo = rinforzo.get('tipo', 'standard')

        logger.info(f"Calcolo cerchiatura: {result.materiale}, tipo {result.tipo}")

        try:
            # 1. Verifica se è un arco
            if opening.get('type') == 'Ad arco':
                result.is_arch = True
                self._handle_arch_opening(opening, rinforzo, result)

            # 2. Calcolo rigidezza in base al materiale
            if result.materiale == 'acciaio':
                self._calculate_steel_frame(opening, rinforzo, wall_data, result)
            elif result.materiale == 'ca':
                self._calculate_concrete_frame(opening, rinforzo, result)
            else:
                result.error = f"Materiale non supportato: {result.materiale}"
                logger.error(result.error)

            # 3. Stima forze sul telaio
            if not result.error:
                forces = self._estimate_frame_forces(opening, wall_data)
                result.M_max = forces.get('M_max', 0)
                result.V_max = forces.get('V_max', 0)
                result.N_max = forces.get('N_max', 0)

            # 4. Calcolo resistenza telaio
            if not result.error and result.materiale == 'acciaio':
                result.V_resistance = self._calculate_frame_resistance(
                    opening, rinforzo
                )

            # 5. Verifica connessioni
            if not result.error and 'ancoraggio' in rinforzo:
                result.connections = self._verify_connections(
                    rinforzo.get('ancoraggio', {}), result
                )

        except Exception as e:
            result.error = str(e)
            logger.error(f"Errore calcolo cerchiatura: {e}")

        return result.to_dict()

    def _handle_arch_opening(self, opening: Dict, rinforzo: Dict,
                            result: FrameResult):
        """Gestisce aperture ad arco"""
        # Calcolo raggio arco
        result.arch_radius = self.arch_manager.calculate_arch_radius(opening)
        result.arch_length = self.arch_manager.calculate_arch_length(opening)

        logger.info(f"Arco: raggio={result.arch_radius:.2f}m, "
                   f"lunghezza={result.arch_length:.2f}m")

        # Verifica calandrabilità profilo
        if rinforzo.get('materiale') == 'acciaio':
            architrave = rinforzo.get('architrave', {})
            profilo = architrave.get('profilo', '')
            classe_acciaio = rinforzo.get('classe_acciaio', 'S275')

            if profilo and result.arch_radius > 0:
                bending_check = self.arch_manager.check_bendability(
                    profilo, result.arch_radius, classe_acciaio
                )

                result.bending_ok = bending_check.get('is_ok', False)

                if not result.bending_ok:
                    msg = bending_check.get('message', 'Calandratura non verificata')
                    result.warnings.append(f"Arco: {msg}")
                    logger.warning(f"Calandratura profilo {profilo}: {msg}")

    def _calculate_steel_frame(self, opening: Dict, rinforzo: Dict,
                              wall_data: Dict, result: FrameResult):
        """Calcola cerchiatura in acciaio"""
        # Determina se usare calculator avanzato
        architrave = rinforzo.get('architrave', {})
        piedritti = rinforzo.get('piedritti', {})

        arch_n = architrave.get('n_profili', 1)
        pied_n = piedritti.get('n_profili', 1)

        if arch_n > 1 or pied_n > 1:
            # Calculator avanzato per profili multipli
            logger.info(f"Usando SteelFrameAdvancedCalculator (profili: {arch_n}+{pied_n})")
            calc_result = self.steel_advanced_calc.calculate_frame_stiffness_advanced(
                opening, rinforzo, wall_data
            )
        else:
            # Calculator standard
            logger.info("Usando SteelFrameCalculator standard")
            calc_result = self.steel_calc.calculate_frame_stiffness(
                opening, rinforzo
            )

        # Estrai risultati
        if calc_result:
            result.K_frame = calc_result.get('K_frame', calc_result.get('K', 0))

            # Unisci warning
            if 'warnings' in calc_result:
                result.warnings.extend(calc_result['warnings'])

            logger.info(f"Acciaio K_frame = {result.K_frame:.1f} kN/m")
        else:
            result.error = "Calcolo acciaio fallito"

    def _calculate_concrete_frame(self, opening: Dict, rinforzo: Dict,
                                  result: FrameResult):
        """Calcola cerchiatura in cemento armato"""
        logger.info("Usando ConcreteFrameCalculator")

        calc_result = self.concrete_calc.calculate_frame_stiffness(
            opening, rinforzo
        )

        if calc_result:
            result.K_frame = calc_result.get('K_frame', calc_result.get('K', 0))

            # Verifica armatura minima
            if hasattr(self.concrete_calc, 'verify_minimum_reinforcement'):
                arm_check = self.concrete_calc.verify_minimum_reinforcement(rinforzo)
                if not arm_check.get('is_ok', True):
                    result.warnings.append(arm_check.get('message', 'Armatura insufficiente'))

            logger.info(f"C.A. K_frame = {result.K_frame:.1f} kN/m")
        else:
            result.error = "Calcolo c.a. fallito"

    def _estimate_frame_forces(self, opening: Dict, wall_data: Dict) -> Dict:
        """
        Stima le forze agenti sul telaio.

        Calcola momento e taglio basandosi su:
        - Peso muratura sovrastante
        - Geometria apertura
        - Schema statico semplificato
        """
        # Geometria
        h_opening = opening.get('height', 0) / 100  # cm -> m
        w_opening = opening.get('width', 0) / 100   # cm -> m
        y_opening = opening.get('y', 0) / 100       # cm -> m
        t_wall = wall_data.get('thickness', 30) / 100  # cm -> m
        h_wall = wall_data.get('height', 270) / 100    # cm -> m

        # Altezza muratura sopra l'apertura
        h_above = h_wall - (y_opening + h_opening)
        h_above = max(0, h_above)

        # Peso specifico muratura (kN/m³)
        gamma_masonry = 18.0  # Valore tipico

        # Carico distribuito sull'architrave
        q = gamma_masonry * t_wall * h_above  # kN/m

        # Schema trave su due appoggi
        # M_max = q * L² / 8
        # V_max = q * L / 2
        M_max = q * w_opening**2 / 8 if w_opening > 0 else 0
        V_max = q * w_opening / 2 if w_opening > 0 else 0

        # Sforzo normale (peso proprio + sovraccarico)
        N_max = q * w_opening / 2  # Reazione verticale

        logger.debug(f"Forze stimate: M={M_max:.2f} kN·m, V={V_max:.2f} kN, N={N_max:.2f} kN")

        return {
            'M_max': M_max,
            'V_max': V_max,
            'N_max': N_max,
            'q_architrave': q
        }

    def _calculate_frame_resistance(self, opening: Dict, rinforzo: Dict) -> float:
        """
        Calcola la resistenza a taglio del telaio in acciaio.

        Basato su:
        - Modulo plastico del profilo
        - Resistenza acciaio
        - Schema di calcolo semplificato
        """
        architrave = rinforzo.get('architrave', {})
        profilo = architrave.get('profilo', '')
        ruotato = architrave.get('ruotato', False)
        classe = rinforzo.get('classe_acciaio', 'S275')
        n_profili = architrave.get('n_profili', 1)

        if not profilo:
            return 0.0

        # Resistenza acciaio
        fy = self._get_steel_yield_strength(classe)

        # Modulo plastico
        W_pl = self._get_plastic_modulus(profilo, ruotato)

        if W_pl <= 0:
            logger.warning(f"Modulo plastico non trovato per {profilo}")
            return 0.0

        # Momento plastico
        M_pl = W_pl * fy / 1000  # kN·m

        # Altezza apertura per calcolo taglio
        h_opening = opening.get('height', 100) / 100  # cm -> m

        # Resistenza a taglio: V = 2 * M_pl / h (schema a portale)
        if h_opening > 0:
            V_resistance = 2 * M_pl * n_profili / h_opening
        else:
            V_resistance = 0

        # Coefficiente sicurezza
        gamma_s = NTC2018.Sicurezza.GAMMA_S_ACCIAIO
        V_resistance = V_resistance / gamma_s

        logger.info(f"Resistenza telaio: V={V_resistance:.1f} kN "
                   f"(profilo {profilo} x{n_profili}, {classe})")

        return V_resistance

    def _get_steel_yield_strength(self, classe: str) -> float:
        """Restituisce la tensione di snervamento dell'acciaio [MPa]"""
        return NTC2018.Acciaio.get_fyk(classe)

    def _get_plastic_modulus(self, profilo: str, ruotato: bool = False) -> float:
        """
        Restituisce il modulo plastico del profilo [cm³].

        Args:
            profilo: Nome profilo (es. 'HEA 100')
            ruotato: True se il profilo è ruotato di 90°
        """
        # Carica cache se necessario
        if self._plastic_moduli_cache is None:
            self._load_profiles_database()

        if self._plastic_moduli_cache is None:
            return 0.0

        profile_data = self._plastic_moduli_cache.get(profilo, {})

        if ruotato:
            return profile_data.get('Wpl_z', profile_data.get('Wpl_y', 0))
        else:
            return profile_data.get('Wpl_y', 0)

    def _load_profiles_database(self):
        """Carica il database dei profili"""
        try:
            # Percorsi possibili per il database
            paths = [
                'data/profiles.json',
                'data/steel_profiles.json',
                os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'profiles.json')
            ]

            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Costruisci cache
                    self._plastic_moduli_cache = {}
                    for category in data.values():
                        if isinstance(category, dict):
                            for name, props in category.items():
                                if isinstance(props, dict):
                                    self._plastic_moduli_cache[name] = props

                    logger.info(f"Caricati {len(self._plastic_moduli_cache)} profili")
                    return

            logger.warning("Database profili non trovato")
            self._plastic_moduli_cache = {}

        except Exception as e:
            logger.error(f"Errore caricamento profili: {e}")
            self._plastic_moduli_cache = {}

    def _verify_connections(self, ancoraggio: Dict, frame_result: FrameResult) -> Dict:
        """Verifica le connessioni/ancoraggi"""
        try:
            return self.connections_verifier.verify_anchors(
                ancoraggio,
                frame_result.to_dict()
            )
        except Exception as e:
            logger.error(f"Errore verifica connessioni: {e}")
            return {'error': str(e)}
