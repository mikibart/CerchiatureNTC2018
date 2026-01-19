"""
CalculationService - Orchestratore Principale Calcoli
======================================================

Service layer che orchestra tutti i calcoli secondo NTC 2018:
- Stato originale (muratura con aperture esistenti)
- Stato modificato (muratura con nuove aperture + cerchiature)
- Verifica intervento locale § 8.4.1

Separa la logica di business dalla GUI.

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

from src.data.ntc2018_constants import NTC2018
from src.core.engine.masonry import MasonryCalculator
from src.core.engine.verifications import NTC2018Verifier

logger = logging.getLogger(__name__)


@dataclass
class MasonryState:
    """Stato della muratura (originale o modificato)"""
    K: float = 0.0          # Rigidezza totale [kN/m]
    V_t1: float = 0.0       # Resistenza taglio diagonale [kN]
    V_t2: float = 0.0       # Resistenza con fattore forma [kN]
    V_t3: float = 0.0       # Resistenza pressoflessione [kN]
    V_min: float = 0.0      # Minimo delle resistenze [kN]


@dataclass
class VerificationResult:
    """Risultato verifica intervento locale"""
    is_local: bool = False              # Intervento classificabile come locale
    stiffness_variation: float = 0.0    # ΔK/K [%]
    resistance_variation: float = 0.0   # ΔV/V [%]
    stiffness_ok: bool = False          # Rispetta limite ±15%
    resistance_ok: bool = False         # Rispetta limite -20%
    message: str = ""


@dataclass
class CalculationResult:
    """Risultato completo del calcolo"""
    # Stati muratura
    original: MasonryState = field(default_factory=MasonryState)
    modified: MasonryState = field(default_factory=MasonryState)

    # Contributi cerchiature
    K_frames: float = 0.0       # Rigidezza totale cerchiature [kN/m]
    V_frames: float = 0.0       # Resistenza totale cerchiature [kN]

    # Risultati per singola apertura
    frame_results: Dict = field(default_factory=dict)

    # Verifica NTC 2018
    verification: VerificationResult = field(default_factory=VerificationResult)

    # Parametri usati
    FC: float = 1.0             # Fattore di confidenza
    gamma_collaborazione: float = 1.0  # Fattore collaborazione

    # Errori e warning
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def K_total_modified(self) -> float:
        """Rigidezza totale stato modificato (muratura + cerchiature)"""
        return self.modified.K + self.K_frames

    @property
    def V_total_modified(self) -> float:
        """Resistenza totale stato modificato (muratura + cerchiature)"""
        return self.modified.V_min + self.V_frames

    @property
    def is_valid(self) -> bool:
        """Verifica se il calcolo è valido (senza errori critici)"""
        return len(self.errors) == 0


class CalculationService:
    """
    Servizio principale per orchestrare i calcoli strutturali.

    Questa classe:
    - Coordina i calcoli tra stato originale e modificato
    - Gestisce i contributi delle cerchiature
    - Esegue la verifica di intervento locale NTC 2018 § 8.4.1

    Esempio d'uso:
        service = CalculationService()
        result = service.calculate(project_data)

        if result.is_valid:
            print(f"ΔK = {result.verification.stiffness_variation:.1f}%")
            print(f"Verifica: {'OK' if result.verification.is_local else 'NON LOCALE'}")
    """

    VERSION = "1.0.0"

    def __init__(self):
        """Inizializza il servizio con i calculator necessari"""
        self.masonry_calc = MasonryCalculator()
        self.verifier = NTC2018Verifier()

        # Frame service sarà iniettato o creato lazy
        self._frame_service = None

        logger.info(f"CalculationService inizializzato - v{self.VERSION}")

    @property
    def frame_service(self):
        """Lazy loading del frame service"""
        if self._frame_service is None:
            from .frame_service import FrameService
            self._frame_service = FrameService()
        return self._frame_service

    def calculate(self, project_data: Dict) -> CalculationResult:
        """
        Esegue il calcolo completo per un progetto.

        Args:
            project_data: Dict contenente:
                - wall: geometria parete
                - masonry: parametri meccanici muratura
                - openings: lista aperture con rinforzi
                - loads: carichi (opzionale)
                - FC: fattore di confidenza
                - constraints: vincoli (opzionale)

        Returns:
            CalculationResult con tutti i risultati
        """
        logger.info("=== INIZIO CALCOLO PROGETTO ===")
        result = CalculationResult()

        try:
            # 1. Estrazione e validazione dati
            wall_data = self._extract_wall_data(project_data)
            masonry_data = self._extract_masonry_data(project_data)
            all_openings = self._extract_openings(project_data)

            # 2. Configurazione coefficienti
            result.FC = self._get_confidence_factor(project_data, masonry_data)
            result.gamma_collaborazione = NTC2018.InterventiLocali.GAMMA_COLLABORAZIONE

            # Configura calculator muratura
            self._configure_masonry_calculator(project_data, result.FC)

            # 3. Separazione aperture esistenti vs nuove
            existing_openings = [o for o in all_openings if o.get('existing', False)]

            # 4. Calcolo STATO ORIGINALE (solo aperture esistenti)
            result.original = self._calculate_masonry_state(
                wall_data, masonry_data, existing_openings, "ORIGINALE"
            )

            # 5. Calcolo STATO MODIFICATO BASE (tutte le aperture, senza cerchiature)
            result.modified = self._calculate_masonry_state(
                wall_data, masonry_data, all_openings, "MODIFICATO"
            )

            # 6. Calcolo contributi CERCHIATURE
            openings_with_reinforcement = [
                o for o in all_openings
                if o.get('rinforzo') and not o.get('existing', False)
            ]

            if openings_with_reinforcement:
                K_frames, V_frames, frame_results = self._calculate_frames_contribution(
                    openings_with_reinforcement, wall_data, masonry_data
                )
                result.K_frames = K_frames
                result.V_frames = V_frames
                result.frame_results = frame_results

                # Aggiungi warning dai frame
                for opening_id, frame_result in frame_results.items():
                    if 'warnings' in frame_result:
                        result.warnings.extend(frame_result['warnings'])

            # 7. Verifica intervento locale NTC 2018 § 8.4.1
            result.verification = self._verify_local_intervention(
                result.original, result.modified, result.K_frames, result.V_frames
            )

            logger.info("=== FINE CALCOLO PROGETTO ===")
            logger.info(f"Verifica locale: {result.verification.is_local}")

        except Exception as e:
            logger.error(f"Errore durante il calcolo: {e}")
            result.errors.append(str(e))

        return result

    def _extract_wall_data(self, project_data: Dict) -> Dict:
        """Estrae e valida i dati della parete"""
        wall = project_data.get('wall', {})

        # Supporta anche formato con 'input_module'
        if not wall and 'input_module' in project_data:
            wall = project_data['input_module'].get('wall', {})

        if not wall:
            raise ValueError("Dati parete mancanti")

        return {
            'length': wall.get('length', 0),
            'height': wall.get('height', 0),
            'thickness': wall.get('thickness', 0)
        }

    def _extract_masonry_data(self, project_data: Dict) -> Dict:
        """Estrae i parametri della muratura"""
        masonry = project_data.get('masonry', {})

        if not masonry and 'input_module' in project_data:
            masonry = project_data['input_module'].get('masonry', {})

        return {
            'fcm': masonry.get('fcm', 2.0),
            'tau0': masonry.get('tau0', 0.074),
            'E': masonry.get('E', 1410),
            'knowledge_level': masonry.get('knowledge_level', 'LC1')
        }

    def _extract_openings(self, project_data: Dict) -> List[Dict]:
        """Estrae la lista delle aperture"""
        # Prima cerca in openings_module (formato preferito)
        if 'openings_module' in project_data:
            openings = project_data['openings_module'].get('openings', [])
            if openings:
                return openings

        # Fallback a 'openings' diretto
        return project_data.get('openings', [])

    def _get_confidence_factor(self, project_data: Dict, masonry_data: Dict) -> float:
        """Determina il fattore di confidenza FC"""
        # FC esplicito
        if 'FC' in project_data:
            return project_data['FC']

        # Da livello di conoscenza
        kl = masonry_data.get('knowledge_level', 'LC1')
        fc_map = {
            'LC1': NTC2018.FC.LC1,
            'LC2': NTC2018.FC.LC2,
            'LC3': NTC2018.FC.LC3
        }
        return fc_map.get(kl, NTC2018.FC.LC1)

    def _configure_masonry_calculator(self, project_data: Dict, FC: float):
        """Configura il calculator della muratura"""
        loads = project_data.get('loads', {})
        constraints = project_data.get('constraints', {
            'bottom': 'Incastro',
            'top': 'Incastro (Grinter)'
        })

        self.masonry_calc.set_project_data({
            'loads': loads,
            'constraints': constraints,
            'FC': FC
        })

    def _calculate_masonry_state(self, wall_data: Dict, masonry_data: Dict,
                                  openings: List[Dict], state_name: str) -> MasonryState:
        """Calcola lo stato della muratura (originale o modificato)"""
        logger.info(f"Calcolo stato {state_name} - {len(openings)} aperture")

        state = MasonryState()

        # Resistenze
        V_t1, V_t2, V_t3 = self.masonry_calc.calculate_resistance(
            wall_data, masonry_data, openings if openings else None
        )
        state.V_t1 = V_t1
        state.V_t2 = V_t2
        state.V_t3 = V_t3
        state.V_min = min(V_t1, V_t2, V_t3) if V_t3 > 0 else min(V_t1, V_t2)

        # Rigidezza
        state.K = self.masonry_calc.calculate_stiffness(
            wall_data, masonry_data, openings if openings else None
        )

        logger.info(f"Stato {state_name}: K={state.K:.1f} kN/m, V_min={state.V_min:.1f} kN")

        return state

    def _calculate_frames_contribution(self, openings: List[Dict],
                                       wall_data: Dict,
                                       masonry_data: Dict) -> Tuple[float, float, Dict]:
        """
        Calcola il contributo delle cerchiature.

        Returns:
            Tuple (K_totale, V_totale, results_per_opening)
        """
        logger.info(f"Calcolo contributo {len(openings)} cerchiature")

        K_total = 0.0
        V_total = 0.0
        frame_results = {}

        for i, opening in enumerate(openings):
            opening_id = opening.get('id', f'A{i+1}')
            rinforzo = opening.get('rinforzo', {})

            if not rinforzo:
                continue

            try:
                # Delega al frame service
                frame_result = self.frame_service.calculate_frame(
                    opening, rinforzo, wall_data
                )

                frame_results[opening_id] = frame_result

                # Accumula contributi
                K_frame = frame_result.get('K_frame', 0)
                V_frame = frame_result.get('V_resistance', 0)

                K_total += K_frame
                V_total += V_frame

                logger.info(f"Cerchiatura {opening_id}: K={K_frame:.1f}, V={V_frame:.1f}")

            except Exception as e:
                logger.error(f"Errore calcolo cerchiatura {opening_id}: {e}")
                frame_results[opening_id] = {
                    'error': str(e),
                    'K_frame': 0,
                    'V_resistance': 0
                }

        # Applica fattore di collaborazione
        gamma = NTC2018.InterventiLocali.GAMMA_COLLABORAZIONE
        K_total_reduced = K_total / gamma
        V_total_reduced = V_total / gamma

        logger.info(f"Totale cerchiature: K={K_total_reduced:.1f} kN/m (γ={gamma}), "
                   f"V={V_total_reduced:.1f} kN")

        return K_total_reduced, V_total_reduced, frame_results

    def _verify_local_intervention(self, original: MasonryState, modified: MasonryState,
                                   K_frames: float, V_frames: float) -> VerificationResult:
        """
        Verifica se l'intervento è classificabile come locale secondo NTC 2018 § 8.4.1.

        Limiti:
        - ΔK/K ≤ ±15%
        - ΔV/V ≥ -20%
        """
        result = VerificationResult()

        K_orig = original.K
        K_mod = modified.K + K_frames
        V_orig = original.V_min
        V_mod = modified.V_min + V_frames

        # Calcolo variazioni percentuali
        if K_orig > 0:
            result.stiffness_variation = ((K_mod - K_orig) / K_orig) * 100

        if V_orig > 0:
            result.resistance_variation = ((V_mod - V_orig) / V_orig) * 100

        # Verifica limiti
        delta_K_max = NTC2018.InterventiLocali.DELTA_K_MAX * 100  # ±15%
        delta_V_max = NTC2018.InterventiLocali.DELTA_V_MAX * 100  # -20%

        result.stiffness_ok = abs(result.stiffness_variation) <= delta_K_max
        # DELTA_V_MAX è già negativo (-0.20 = -20%), verifica ΔV >= -20%
        result.resistance_ok = result.resistance_variation >= delta_V_max

        result.is_local = result.stiffness_ok and result.resistance_ok

        # Messaggio descrittivo
        if result.is_local:
            result.message = "Intervento classificabile come LOCALE (§ 8.4.1 NTC 2018)"
        else:
            problems = []
            if not result.stiffness_ok:
                problems.append(f"ΔK={result.stiffness_variation:.1f}% (limite ±{delta_K_max:.0f}%)")
            if not result.resistance_ok:
                problems.append(f"ΔV={result.resistance_variation:.1f}% (limite {delta_V_max:.0f}%)")
            result.message = f"Intervento NON LOCALE: {', '.join(problems)}"

        logger.warning(f"VERIFICA: {result.message}")

        return result

    def calculate_quick(self, wall_data: Dict, masonry_data: Dict,
                       openings: Optional[List[Dict]] = None) -> Tuple[float, float, float, float]:
        """
        Calcolo rapido senza cerchiature.

        Args:
            wall_data (Dict): Dati geometrici della parete.
            masonry_data (Dict): Dati del materiale muratura.
            openings (Optional[List[Dict]]): Lista delle aperture.

        Returns:
            Tuple[float, float, float, float]: Tuple (K, V_t1, V_t2, V_t3).
        """
        V_t1, V_t2, V_t3 = self.masonry_calc.calculate_resistance(
            wall_data, masonry_data, openings
        )
        K = self.masonry_calc.calculate_stiffness(
            wall_data, masonry_data, openings
        )
        return K, V_t1, V_t2, V_t3
