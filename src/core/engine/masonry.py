"""
Calcoli Muratura secondo NTC 2018
Implementa le verifiche per la muratura secondo NTC 2018 § 8.7.1.5
Arch. Michelangelo Bartolotta

Versione corretta con:
- Formula corretta fattore b (NTC 2018 § 8.7.1.5)
- Limite superiore V_t1
- Controlli eccentricità e snellezza
- Validazione input
- Debug integrato per tracciare il problema
- CORREZIONE: γ_m = 2.0 × FC per muratura esistente

Versione estesa (da analisi Calcolus-CERCHIATURA):
- Modello taglio muratura selezionabile (scorrimento/diagonale/minimo)
- Angolo di diffusione per altezza maschi
- Grado di incastro personalizzabile (0-100%)
- Calcolo spostamento ultimo (NTC 7.8.2.2.1 e 7.8.2.2.2)
- Duttilità automatica da materiale
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
import math
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MasonryCalculator:
    """Calcolatore per verifiche muratura secondo NTC 2018 con estensioni avanzate"""

    VERSION = "2025.12.27-EXTENDED"  # Versione con funzionalità Calcolus-CERCHIATURA

    # Costanti per duttilità tipiche muratura (da letteratura)
    DUCTILITY_SHEAR = 2.0       # Rottura a taglio - comportamento fragile
    DUCTILITY_FLEXURE = 3.0     # Rottura a presso-flessione - più duttile
    DUCTILITY_MIXED = 2.5       # Comportamento misto

    # Limiti drift SLC (Circ. 7/2019 C8.7.1.4)
    DRIFT_LIMIT_SHEAR = 0.004       # 0.4% per taglio
    DRIFT_LIMIT_FLEXURE = 0.006     # 0.6% per pressoflessione

    def __init__(self):
        self.gamma_m = 2.0  # Coefficiente di sicurezza base per muratura esistente
        self.FC = 1.0       # Fattore di confidenza
        self.project_data = {}  # Inizializzazione
        logger.debug(f"MasonryCalculator inizializzato - Versione: {self.VERSION}")
        
    def calculate_resistance(self, wall_data: Dict, masonry_data: Dict, 
                           opening_data: Optional[List[Dict]] = None) -> Tuple[float, float, float]:
        """
        Calcola le resistenze del maschio murario secondo NTC 2018 § 8.7.1.5
        
        Returns:
            V_t1: Resistenza a taglio per fessurazione diagonale [kN]
            V_t2: Resistenza a taglio con fattore di forma [kN]  
            V_t3: Resistenza a pressoflessione [kN]
        """
        logger.info(f"=== INIZIO CALCOLO RESISTENZE (v.{self.VERSION}) ===")
        
        # Validazione input
        if not self._validate_input(wall_data, masonry_data):
            logger.error("Dati di input non validi")
            return 0.0, 0.0, 0.0
            
        # Estrai parametri geometrici
        L = wall_data['length'] / 100  # cm -> m
        h = wall_data['height'] / 100  # cm -> m
        t = wall_data['thickness'] / 100  # cm -> m
        
        logger.info(f"Geometria parete: L={L}m, h={h}m, t={t}m")
        
        # Controllo snellezza (NTC 2018 § 8.7.1)
        lambda_max = h / t
        if lambda_max > 20:
            logger.warning(f"Snellezza λ={lambda_max:.1f} > 20 - Verifica elementi snelli richiesta")
        
        # Parametri meccanici (NON modificati da FC - FC si applica solo a gamma_m)
        fcm = masonry_data.get('fcm', 2.0)  # N/mm² -> MPa
        tau0 = masonry_data.get('tau0', 0.074)  # N/mm² -> MPa
        
        # Coefficiente di sicurezza totale per muratura esistente
        gamma_totale = self.gamma_m * self.FC  # 2.0 × FC
        
        logger.info(f"Parametri meccanici: fcm={fcm:.3f} MPa, tau0={tau0:.4f} MPa")
        logger.info(f"Coefficienti sicurezza: γ_m={self.gamma_m}, FC={self.FC}, γ_tot={gamma_totale}")
        
        # Carico verticale e eccentricità
        N = self.project_data.get('loads', {}).get('vertical', 0)  # kN
        e = self.project_data.get('loads', {}).get('eccentricity', 0) / 100  # cm -> m
        
        # Controllo eccentricità
        e_limite = t / 6  # Limite per sezione interamente compressa
        if abs(e) > e_limite:
            logger.warning(f"Eccentricità e={e*100:.1f}cm > t/6={e_limite*100:.1f}cm - Sezione parzializzata")
        
        # Se ci sono aperture, calcola per ogni maschio murario
        if opening_data and len(opening_data) > 0:
            maschi = self._get_maschi_murari(wall_data, opening_data)
            
            V_t1_total = 0
            V_t2_total = 0
            V_t3_total = 0
            
            for i, maschio in enumerate(maschi):
                L_m = maschio['length'] / 100  # cm -> m
                if L_m <= 0:
                    continue
                    
                logger.info(f"Calcolo maschio {i+1}: L={L_m*100:.0f}cm")
                
                # Area maschio
                A_m = L_m * t  # m²
                
                # Ripartizione carico verticale proporzionale all'area
                N_m = N * (L_m / L) if L > 0 else 0
                
                # Calcola resistenze per il maschio
                v_t1, v_t2, v_t3 = self._calculate_single_wall_resistance(
                    L_m, h, t, A_m, N_m, e, fcm, tau0, gamma_totale
                )
                
                V_t1_total += v_t1
                V_t2_total += v_t2
                V_t3_total += v_t3
                
            logger.info(f"=== FINE CALCOLO RESISTENZE CON APERTURE ===")
            return V_t1_total, V_t2_total, V_t3_total
            
        else:
            # Calcolo per parete intera senza aperture
            A = L * t  # m²
            V_t1, V_t2, V_t3 = self._calculate_single_wall_resistance(
                L, h, t, A, N, e, fcm, tau0, gamma_totale
            )
            
            logger.debug(f"Calcolo completato: V_t1={V_t1:.1f}, V_t2={V_t2:.1f}, V_t3={V_t3:.1f} kN")

            return V_t1, V_t2, V_t3
            
    def _calculate_single_wall_resistance(self, L: float, h: float, t: float,
                                        A: float, N: float, e: float,
                                        fcm: float, tau0: float,
                                        gamma_totale: float) -> Tuple[float, float, float]:
        """
        Calcola le resistenze per una singola parete o maschio.

        Usa il modello di taglio selezionato nelle impostazioni:
        - Scorrimento: per murature regolari (V = fvk0 + μ·σn)
        - Fessurazione diagonale: per murature irregolari (Turnsek-Cacovic)
        - Minimo: il più sfavorevole tra i due (default, raccomandato)
        """
        logger.info(f"Calcolo resistenze per L={L}m, h={h}m, A={A}m²")

        # Estrai modello di taglio dalle impostazioni
        constraints = self.project_data.get('constraints', {})
        shear_model = constraints.get('shear_model', 'Minimo (scorrimento e diagonale)')

        # Tensione normale di compressione
        sigma_0 = N / (A * 1000) if A > 0 else 0  # kN/m² -> MPa

        # === CALCOLO V_SCORRIMENTO (murature regolari) ===
        # Formula: V_sc = L·t·(fvk0 + μ·σn) / γ_m
        # Coefficiente di attrito μ = 0.4 per muratura
        mu_attrito = 0.4
        fvk0 = tau0  # Resistenza a taglio iniziale
        V_scorrimento = A * (fvk0 + mu_attrito * sigma_0) * 1000 / gamma_totale  # kN

        # === CALCOLO V_DIAGONALE (murature irregolari - Turnsek-Cacovic) ===
        # Formula: V_diag = L·t·τ0·√(1 + σ0/τ0) / γ_m
        if tau0 > 0:
            V_diagonale_base = A * tau0 * math.sqrt(1 + sigma_0 / tau0) * 1000  # kN
        else:
            V_diagonale_base = 0

        # Limite superiore (NTC 2018)
        V_diagonale_limite = A * 0.065 * fcm * 1000  # kN
        V_diagonale = min(V_diagonale_base, V_diagonale_limite) / gamma_totale

        # === SELEZIONE MODELLO ===
        if 'scorrimento' in shear_model.lower() and 'diagonale' not in shear_model.lower():
            V_t1 = V_scorrimento
            logger.info(f"Modello SCORRIMENTO: V_t1={V_t1:.1f} kN")
        elif 'diagonale' in shear_model.lower() and 'scorrimento' not in shear_model.lower():
            V_t1 = V_diagonale
            logger.info(f"Modello DIAGONALE: V_t1={V_t1:.1f} kN")
        else:
            # Minimo tra i due (default, più conservativo)
            V_t1 = min(V_scorrimento, V_diagonale)
            logger.info(f"Modello MINIMO: V_sc={V_scorrimento:.1f}, V_diag={V_diagonale:.1f}, V_t1={V_t1:.1f} kN")

        # === V_t2 - Taglio con fattore di forma (NTC 2018 eq. 8.7.1.17) ===
        rapporto_h_L = h / L if L > 0 else 0

        if rapporto_h_L >= 1.5:
            b = 1.0
        else:
            b = 1.5 - rapporto_h_L / 3.0  # Formula corretta NTC 2018

        V_t2 = V_t1 * b
        logger.debug(f"Fattore b: h/L={rapporto_h_L:.3f}, b={b:.3f}, V_t2={V_t2:.1f} kN")

        # === V_t3 - Pressoflessione (NTC 2018 § 8.7.1.5) ===
        sigma_max = self._calculate_max_compression(N, A, e, L)

        # Verifica limite compressione
        fcm_ridotto = 0.85 * fcm  # Resistenza ridotta per carichi di lunga durata

        if sigma_max < fcm_ridotto:
            # Formula pressoflessione
            mu = 1 - sigma_max / fcm_ridotto
            V_t3 = (A * fcm * mu * 1000) / gamma_totale
        else:
            V_t3 = 0
            mu = 0
            logger.warning(f"Tensione massima {sigma_max:.2f} MPa >= 0.85*fcm = {fcm_ridotto:.2f} MPa")

        logger.debug(f"V_t3: sigma_max={sigma_max:.3f} MPa, mu={mu:.3f}, V_t3={V_t3:.1f} kN")

        return V_t1, V_t2, V_t3
            
    def calculate_stiffness(self, wall_data: Dict, masonry_data: Dict,
                          opening_data: Optional[List[Dict]] = None) -> float:
        """
        Calcola la rigidezza laterale della parete secondo NTC 2018
        
        Returns:
            K: Rigidezza laterale [kN/m]
        """
        logger.info(f"=== INIZIO CALCOLO RIGIDEZZA (v.{self.VERSION}) ===")
        
        # Parametri geometrici
        L = wall_data['length'] / 100  # cm -> m
        h = wall_data['height'] / 100  # cm -> m
        t = wall_data['thickness'] / 100  # cm -> m
        
        # Parametri elastici
        E = masonry_data.get('E', 1410) * 1e6  # MPa -> Pa

        # Usa G direttamente se fornito, altrimenti calcola da E e nu
        G_provided = masonry_data.get('G')
        if G_provided and G_provided > 0:
            G = G_provided * 1e6  # MPa -> Pa
            nu = E / (2 * G) - 1  # Calcola nu da E e G (inverso)
        else:
            nu = masonry_data.get('poisson', 0.2)  # Coefficiente di Poisson
            G = E / (2 * (1 + nu))  # Modulo di taglio

        logger.info(f"Parametri elastici: E={E/1e6:.0f} MPa, G={G/1e6:.0f} MPa, nu={nu:.2f}")
        
        # Condizioni di vincolo e opzioni di calcolo (integrate da ProPT3 e Calcolus-CERCHIATURA)
        constraints = self.project_data.get('constraints', {})
        bottom = constraints.get('bottom', 'Incastro')
        top = constraints.get('top', 'Incastro (Grinter)')
        static_scheme = constraints.get('static_scheme', '')
        height_method = constraints.get('height_method', 'A - Altezza di piano')
        constraint_percentage = constraints.get('constraint_percentage', 100)  # 0-100%
        diffusion_angle = constraints.get('diffusion_angle', 0)  # gradi

        # Fattore k da static_scheme se specificato, altrimenti deduce dai vincoli
        if 'Personalizzato' in static_scheme:
            # k interpolato linearmente tra 3 (0%) e 12 (100%)
            k_vincolo = 3 + (12 - 3) * constraint_percentage / 100
            logger.info(f"Schema statico: Personalizzato (k={k_vincolo:.1f}, {constraint_percentage}%)")
        elif 'k=12' in static_scheme:
            k_vincolo = 12
            logger.info("Schema statico: Doppio incastro (k=12)")
        elif 'k=6' in static_scheme:
            k_vincolo = 6
            logger.info("Schema statico: Incastro-cerniera (k=6)")
        elif 'k=3' in static_scheme:
            k_vincolo = 3
            logger.info("Schema statico: Mensola (k=3)")
        elif bottom == 'Incastro' and 'Incastro' in top:
            k_vincolo = 12  # Doppio incastro
            logger.info("Schema statico (da vincoli): Doppio incastro")
        elif bottom == 'Incastro' and 'Libero' in top:
            k_vincolo = 3   # Mensola
            logger.info("Schema statico (da vincoli): Mensola")
        else:
            k_vincolo = 6   # Caso intermedio (incastro-cerniera)
            logger.info("Schema statico (da vincoli): Incastro-cerniera")

        # Calcola altezza efficace in base al metodo selezionato e angolo di diffusione
        h_eff = self._calculate_effective_height(h, opening_data, height_method, diffusion_angle)
            
        if opening_data and len(opening_data) > 0:
            # Calcola rigidezza equivalente con aperture
            maschi = self._get_maschi_murari(wall_data, opening_data)
            
            # Rigidezze in parallelo dei maschi
            K_total = 0
            
            for i, maschio in enumerate(maschi):
                L_m = maschio['length'] / 100  # cm -> m
                if L_m <= 0:
                    continue
                    
                # Momento d'inerzia maschio
                I_m = t * L_m**3 / 12

                # Rigidezza flessionale (usa h_eff)
                K_flex_m = k_vincolo * E * I_m / h_eff**3

                # Rigidezza tagliante (usa h_eff)
                A_m = L_m * t
                chi = 1.2  # Fattore di forma per sezione rettangolare
                K_shear_m = chi * G * A_m / h_eff
                
                # Rigidezza combinata maschio (molle in serie)
                K_m = 1 / (1/K_flex_m + 1/K_shear_m)
                
                K_total += K_m
                
                logger.debug(f"Maschio {i+1}: K_flex={K_flex_m/1000:.1f} kN/m, "
                           f"K_shear={K_shear_m/1000:.1f} kN/m, K_tot={K_m/1000:.1f} kN/m")
                
            K_result = K_total / 1000  # Pa -> kN/m
            logger.debug(f"Rigidezza con aperture: {K_result:.1f} kN/m")
            return K_result
            
        else:
            # Parete senza aperture (h_eff = h)
            I = t * L**3 / 12  # Momento d'inerzia

            # Rigidezza flessionale (usa h_eff)
            K_flex = k_vincolo * E * I / h_eff**3

            # Rigidezza tagliante (usa h_eff)
            A = L * t
            chi = 1.2  # Fattore di forma per sezione rettangolare
            K_shear = chi * G * A / h_eff
            
            # Rigidezza combinata (molle in serie)
            K = 1 / (1/K_flex + 1/K_shear)
            
            logger.info(f"Rigidezza: K_flex={K_flex/1000:.1f} kN/m, "
                       f"K_shear={K_shear/1000:.1f} kN/m, K_tot={K/1000:.1f} kN/m")
            
            K_result = K / 1000  # Pa -> kN/m
            logger.debug(f"Rigidezza calcolata: {K_result:.1f} kN/m")

            return K_result
            
    def _get_maschi_murari(self, wall_data: Dict, openings: List[Dict]) -> List[Dict]:
        """Identifica i maschi murari tra le aperture"""
        if not openings:
            return []
            
        maschi = []
        wall_length = wall_data['length']
        
        # Ordina aperture per posizione X
        sorted_openings = sorted(openings, key=lambda o: o['x'])
        
        # Maschio iniziale (prima della prima apertura)
        if sorted_openings[0]['x'] > 0:
            maschi.append({
                'start': 0,
                'end': sorted_openings[0]['x'],
                'length': sorted_openings[0]['x']
            })
            
        # Maschi intermedi (tra le aperture)
        for i in range(len(sorted_openings) - 1):
            x1 = sorted_openings[i]['x'] + sorted_openings[i]['width']
            x2 = sorted_openings[i + 1]['x']
            if x2 > x1:
                maschi.append({
                    'start': x1,
                    'end': x2,
                    'length': x2 - x1
                })
                
        # Maschio finale (dopo l'ultima apertura)
        last_opening = sorted_openings[-1]
        x_end = last_opening['x'] + last_opening['width']
        if x_end < wall_length:
            maschi.append({
                'start': x_end,
                'end': wall_length,
                'length': wall_length - x_end
            })
            
        logger.info(f"Identificati {len(maschi)} maschi murari")
        
        return maschi
        
    def _calculate_max_compression(self, N: float, A: float, e: float, L: float) -> float:
        """
        Calcola la tensione massima di compressione considerando pressoflessione
        
        Args:
            N: Carico verticale [kN]
            A: Area sezione [m²]
            e: Eccentricità [m]
            L: Lunghezza sezione [m]
            
        Returns:
            sigma_max: Tensione massima [MPa]
        """
        if A <= 0:
            return 0
            
        # Tensione media
        sigma_med = N / (A * 1000)  # kN/m² -> MPa
        
        # Modulo di resistenza
        W = A * L / 6  # m³
        
        # Momento per eccentricità
        M = abs(N * e)  # kN·m
        
        # Tensione massima (pressoflessione)
        if W > 0:
            sigma_max = sigma_med + M / (W * 1000)  # MPa
        else:
            sigma_max = sigma_med
            
        return max(0, sigma_max)
        
    def _validate_input(self, wall_data: Dict, masonry_data: Dict) -> bool:
        """Valida i dati di input"""
        try:
            # Controllo dimensioni geometriche
            if wall_data['length'] <= 0 or wall_data['height'] <= 0 or wall_data['thickness'] <= 0:
                logger.error("Dimensioni geometriche non valide")
                return False
                
            # Controllo parametri meccanici
            if masonry_data.get('fcm', 0) <= 0 or masonry_data.get('tau0', 0) <= 0:
                logger.error("Parametri meccanici non validi")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Errore validazione input: {e}")
            return False

    def _calculate_effective_height(self, h_wall: float, openings: Optional[List[Dict]],
                                    method: str = 'A - Altezza di piano',
                                    diffusion_angle: float = 0) -> float:
        """
        Calcola l'altezza efficace del maschio murario secondo il metodo selezionato.

        Metodi (da analisi ProPT3 e Calcolus-CERCHIATURA):
        - A: Altezza di piano (non considera rigidezza fasce)
        - B: Fasce rigide (usa max altezza fori adiacenti)
        - C: Metodo Dolce (fasce semirigide - interpolazione)

        L'angolo di diffusione riduce l'altezza efficace considerando la diffusione
        dei carichi attraverso la muratura.

        Args:
            h_wall: Altezza parete [m]
            openings: Lista aperture
            method: Metodo di calcolo selezionato
            diffusion_angle: Angolo di diffusione [gradi] (da Calcolus-CERCHIATURA)

        Returns:
            h_eff: Altezza efficace per il calcolo della rigidezza [m]
        """
        if not openings or len(openings) == 0:
            logger.info(f"Altezza efficace (nessuna apertura): h_eff = {h_wall:.2f} m")
            return h_wall

        # Estrai altezza massima delle aperture
        h_max_opening = max(op.get('height', 0) / 100 for op in openings)  # cm -> m

        if 'A -' in method or method == '':
            # Metodo A: Altezza di piano (tutta l'altezza della parete)
            h_eff = h_wall
            logger.info(f"Metodo A (altezza piano): h_eff = {h_eff:.2f} m")

        elif 'B -' in method:
            # Metodo B: Fasce rigide - usa la massima altezza delle aperture
            h_eff = h_max_opening
            logger.info(f"Metodo B (fasce rigide): h_eff = {h_eff:.2f} m (max h fori)")

        elif 'C -' in method:
            # Metodo C: Metodo Dolce - fasce semirigide (valore intermedio)
            # Formula di Dolce: h_eff = h_apertura + 0.3 × (h_parete - h_apertura)
            h_eff = h_max_opening + 0.3 * (h_wall - h_max_opening)
            logger.info(f"Metodo C (Dolce): h_eff = {h_eff:.2f} m (semirigide)")

        else:
            # Default: usa altezza parete
            h_eff = h_wall
            logger.info(f"Metodo default: h_eff = {h_eff:.2f} m")

        # Applica angolo di diffusione (da Calcolus-CERCHIATURA)
        # L'angolo riduce l'altezza efficace considerando la diffusione dei carichi
        if diffusion_angle > 0:
            # Calcola riduzione basata sull'angolo di diffusione
            # Maggiore l'angolo, minore l'altezza efficace
            angle_rad = math.radians(diffusion_angle)
            # Fattore di riduzione: per angolo 45°, riduzione circa 30%
            reduction_factor = 1 - 0.3 * math.tan(angle_rad) / math.tan(math.radians(45))
            reduction_factor = max(0.5, min(1.0, reduction_factor))  # Limita tra 0.5 e 1.0
            h_eff_reduced = h_eff * reduction_factor
            logger.info(f"Angolo diffusione {diffusion_angle}°: h_eff ridotta da {h_eff:.2f} a {h_eff_reduced:.2f} m")
            h_eff = h_eff_reduced

        return h_eff

    def set_project_data(self, project_data: Dict):
        """Imposta i dati completi del progetto"""
        self.project_data = project_data
        
        # Imposta FC dal progetto
        if 'FC' in project_data:
            self.FC = project_data['FC']
            logger.info(f"Fattore di confidenza impostato: FC={self.FC}")
        
        # Log configurazione
        loads = project_data.get('loads', {})
        constraints = project_data.get('constraints', {})
        
        logger.info(f"Dati progetto impostati: N={loads.get('vertical', 0)} kN, "
                   f"e={loads.get('eccentricity', 0)} cm")
        logger.info(f"Vincoli: {constraints.get('bottom', 'N/D')} - "
                   f"{constraints.get('top', 'N/D')}")

    def calculate_ultimate_displacement(self, wall_data: Dict, masonry_data: Dict,
                                        K: float, V_min: float,
                                        mechanism: str = 'shear') -> Dict:
        """
        Calcola lo spostamento ultimo secondo NTC 2018 § 7.8.2.2

        Formule:
        - 7.8.2.2.1: d_u = drift_limite × h
        - 7.8.2.2.2: d_u = μ × d_y (spostamento anelastico)

        Lo spostamento ultimo è il MINIMO tra le due formule.

        Args:
            wall_data: Dati geometrici parete
            masonry_data: Dati meccanici muratura
            K: Rigidezza [kN/m]
            V_min: Resistenza minima [kN]
            mechanism: Meccanismo di rottura ('shear' o 'flexure')

        Returns:
            Dict con: d_u, d_y, mu, drift, formula_used
        """
        h = wall_data['height'] / 100  # cm -> m

        # Spostamento al limite elastico
        if K > 0:
            d_y = V_min / K  # m
        else:
            d_y = 0

        # Duttilità in base al meccanismo
        if mechanism == 'shear':
            mu = self.DUCTILITY_SHEAR
            drift_limit = self.DRIFT_LIMIT_SHEAR
        elif mechanism == 'flexure':
            mu = self.DUCTILITY_FLEXURE
            drift_limit = self.DRIFT_LIMIT_FLEXURE
        else:
            mu = self.DUCTILITY_MIXED
            drift_limit = (self.DRIFT_LIMIT_SHEAR + self.DRIFT_LIMIT_FLEXURE) / 2

        # Formula 7.8.2.2.1: spostamento da drift limite
        d_u_drift = drift_limit * h

        # Formula 7.8.2.2.2: spostamento anelastico
        d_u_anelastic = mu * d_y

        # Spostamento ultimo = minimo tra le due formule
        if d_u_drift < d_u_anelastic:
            d_u = d_u_drift
            formula_used = '7.8.2.2.1 (drift)'
        else:
            d_u = d_u_anelastic
            formula_used = '7.8.2.2.2 (anelastico)'

        # Calcola drift effettivo
        drift = d_u / h if h > 0 else 0

        logger.info(f"Spostamento ultimo: d_u={d_u*1000:.1f} mm (formula {formula_used})")
        logger.info(f"  d_y={d_y*1000:.1f} mm, μ={mu:.1f}, drift={drift*100:.2f}%")

        return {
            'd_u': d_u,
            'd_y': d_y,
            'mu': mu,
            'drift': drift,
            'drift_limit': drift_limit,
            'd_u_drift': d_u_drift,
            'd_u_anelastic': d_u_anelastic,
            'formula_used': formula_used,
            'mechanism': mechanism
        }

    def calculate_automatic_ductility(self, masonry_type: str, V_t1: float, V_t3: float) -> Dict:
        """
        Calcola automaticamente la duttilità in base al tipo di muratura
        e al meccanismo di rottura critico.

        Duttilità tipiche (da letteratura):
        - Taglio: μ = 1.5 - 2.5 (comportamento fragile)
        - Presso-flessione: μ = 2.5 - 4.0 (comportamento duttile)

        Args:
            masonry_type: Tipo di muratura
            V_t1: Resistenza a taglio
            V_t3: Resistenza a presso-flessione

        Returns:
            Dict con: mu, mechanism, degradation_factor
        """
        # Determina meccanismo critico
        if V_t1 <= V_t3:
            mechanism = 'shear'
            base_mu = self.DUCTILITY_SHEAR
            degradation = 0.4  # Degrado post-picco più rapido
        else:
            mechanism = 'flexure'
            base_mu = self.DUCTILITY_FLEXURE
            degradation = 0.2  # Degrado più graduale

        # Modifica in base al tipo di muratura
        mu = base_mu
        masonry_lower = masonry_type.lower()

        if 'pietrame' in masonry_lower or 'irregolar' in masonry_lower:
            # Murature irregolari: comportamento più fragile
            mu *= 0.8
            degradation *= 1.2
        elif 'mattoni pieni' in masonry_lower or 'regolar' in masonry_lower:
            # Murature regolari: comportamento migliore
            mu *= 1.1
            degradation *= 0.9
        elif 'blocchi' in masonry_lower:
            # Murature in blocchi: comportamento intermedio
            pass  # usa valori base

        # Limita la duttilità
        mu = max(1.5, min(4.0, mu))
        degradation = max(0.1, min(0.5, degradation))

        logger.info(f"Duttilità automatica: μ={mu:.2f}, meccanismo={mechanism}, β={degradation:.2f}")

        return {
            'mu': mu,
            'mechanism': mechanism,
            'degradation_factor': degradation,
            'masonry_type': masonry_type
        }

    def get_capacity_curve_parameters(self, wall_data: Dict, masonry_data: Dict,
                                      K: float, V_min: float, V_t1: float, V_t3: float) -> Dict:
        """
        Calcola i parametri per la curva di capacità bilineare.

        Returns:
            Dict con tutti i parametri per tracciare la curva
        """
        # Duttilità automatica
        ductility_info = self.calculate_automatic_ductility(
            masonry_data.get('type', ''), V_t1, V_t3
        )

        # Spostamento ultimo
        displacement_info = self.calculate_ultimate_displacement(
            wall_data, masonry_data, K, V_min, ductility_info['mechanism']
        )

        return {
            'K': K,
            'V_max': V_min,
            'd_y': displacement_info['d_y'],
            'd_u': displacement_info['d_u'],
            'mu': ductility_info['mu'],
            'mechanism': ductility_info['mechanism'],
            'degradation': ductility_info['degradation_factor'],
            'drift': displacement_info['drift'],
            'drift_limit': displacement_info['drift_limit'],
            'formula_used': displacement_info['formula_used']
        }

    def calculate_fill_contribution(self, wall_data: Dict, opening_data: List[Dict]) -> Dict:
        """
        Calcola il contributo del riempimento delle aperture alla rigidezza/resistenza.

        Basato su analisi Calcolus-CERCHIATURA (RiempimentoApertura).

        Il riempimento di un'apertura esistente può contribuire parzialmente
        alla rigidezza e resistenza della parete, in base a:
        - Tipo di materiale di riempimento
        - Spessore del riempimento
        - Qualità dell'ammorsamento con muratura esistente

        Args:
            wall_data: Dati geometrici parete
            opening_data: Lista aperture con dati riempimento

        Returns:
            Dict con:
            - K_fill: Contributo rigidezza totale riempimenti [kN/m]
            - V_fill: Contributo resistenza totale riempimenti [kN]
            - details: Lista dettagli per ogni apertura riempita
        """
        if not opening_data:
            return {'K_fill': 0, 'V_fill': 0, 'details': []}

        wall_height = wall_data['height'] / 100  # cm -> m
        wall_thickness = wall_data['thickness'] / 100  # cm -> m

        K_fill_total = 0
        V_fill_total = 0
        details = []

        for i, opening in enumerate(opening_data):
            fill_data = opening.get('fill_material', {})

            # Controlla se c'è riempimento
            fill_type = fill_data.get('fill_type', 0)
            if fill_type == 0:  # FillType.NONE
                continue

            # Estrai parametri riempimento
            fill_thickness = fill_data.get('thickness', 0) / 100  # cm -> m
            if fill_thickness <= 0:
                fill_thickness = wall_thickness  # Default: spessore parete

            E_fill = fill_data.get('E', 0) * 1e6  # MPa -> Pa
            G_fill = fill_data.get('G', 0) * 1e6  # MPa -> Pa
            fk_fill = fill_data.get('fk', 0)  # MPa
            tau0_fill = fill_data.get('tau0', 0)  # MPa

            # Percentuali contributo
            K_contrib_pct = fill_data.get('stiffness_contribution', 0) / 100
            V_contrib_pct = fill_data.get('resistance_contribution', 0) / 100

            # Efficienza ammorsamento
            has_connection = fill_data.get('has_connection', False)
            connection_efficiency = fill_data.get('connection_efficiency', 0.5) if has_connection else 0.3

            # Geometria apertura
            opening_width = opening.get('width', 0) / 100  # cm -> m
            opening_height = opening.get('height', 0) / 100  # cm -> m

            if opening_width <= 0 or opening_height <= 0:
                continue

            # Area del riempimento
            A_fill = opening_width * fill_thickness  # m²

            # === CALCOLO RIGIDEZZA RIEMPIMENTO ===
            if E_fill > 0 and G_fill > 0:
                # Momento d'inerzia del riempimento
                I_fill = fill_thickness * opening_width**3 / 12

                # Rigidezza flessionale (schema incastro-cerniera approssimato)
                k_vincolo_fill = 6  # Schema intermedio per riempimento
                K_flex_fill = k_vincolo_fill * E_fill * I_fill / opening_height**3

                # Rigidezza tagliante
                chi = 1.2
                K_shear_fill = chi * G_fill * A_fill / opening_height

                # Rigidezza combinata
                K_fill_raw = 1 / (1/K_flex_fill + 1/K_shear_fill) / 1000  # Pa -> kN/m

                # Applica fattori di riduzione
                K_fill = K_fill_raw * K_contrib_pct * connection_efficiency
            else:
                K_fill = 0
                K_fill_raw = 0

            # === CALCOLO RESISTENZA RIEMPIMENTO ===
            if tau0_fill > 0:
                # Resistenza a taglio del riempimento
                V_fill_raw = A_fill * tau0_fill * 1000  # MPa × m² × 1000 = kN

                # Applica fattori di riduzione
                V_fill = V_fill_raw * V_contrib_pct * connection_efficiency
            else:
                V_fill = 0
                V_fill_raw = 0

            K_fill_total += K_fill
            V_fill_total += V_fill

            details.append({
                'opening_index': i,
                'fill_type': fill_type,
                'K_fill_raw': K_fill_raw,
                'K_fill': K_fill,
                'V_fill_raw': V_fill_raw,
                'V_fill': V_fill,
                'K_contrib_pct': K_contrib_pct * 100,
                'V_contrib_pct': V_contrib_pct * 100,
                'connection_efficiency': connection_efficiency * 100
            })

            logger.info(f"Riempimento apertura {i+1}: K={K_fill:.1f} kN/m, V={V_fill:.1f} kN")

        logger.info(f"Contributo totale riempimenti: K={K_fill_total:.1f} kN/m, V={V_fill_total:.1f} kN")

        return {
            'K_fill': K_fill_total,
            'V_fill': V_fill_total,
            'details': details
        }

    def calculate_with_fill(self, wall_data: Dict, masonry_data: Dict,
                           opening_data: Optional[List[Dict]] = None) -> Dict:
        """
        Calcola rigidezza e resistenza includendo il contributo dei riempimenti.

        Questo metodo estende i calcoli standard aggiungendo il contributo
        delle aperture riempite (chiusure vano).

        Args:
            wall_data: Dati geometrici parete
            masonry_data: Dati meccanici muratura
            opening_data: Lista aperture (può includere fill_material)

        Returns:
            Dict con risultati completi incluso contributo riempimenti
        """
        # Calcoli standard
        V_t1, V_t2, V_t3 = self.calculate_resistance(wall_data, masonry_data, opening_data)
        K_base = self.calculate_stiffness(wall_data, masonry_data, opening_data)

        # Calcola contributo riempimenti
        fill_contrib = self.calculate_fill_contribution(wall_data, opening_data or [])

        # Somma contributi
        K_total = K_base + fill_contrib['K_fill']
        V_total = min(V_t1, V_t2, V_t3) + fill_contrib['V_fill']

        logger.info(f"Rigidezza totale (con riempimenti): K={K_total:.1f} kN/m")
        logger.info(f"Resistenza totale (con riempimenti): V={V_total:.1f} kN")

        return {
            'K_base': K_base,
            'K_fill': fill_contrib['K_fill'],
            'K_total': K_total,
            'V_t1': V_t1,
            'V_t2': V_t2,
            'V_t3': V_t3,
            'V_min_base': min(V_t1, V_t2, V_t3),
            'V_fill': fill_contrib['V_fill'],
            'V_total': V_total,
            'fill_details': fill_contrib['details']
        }