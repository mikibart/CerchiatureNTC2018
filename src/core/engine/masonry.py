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
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
import math
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MasonryCalculator:
    """Calcolatore per verifiche muratura secondo NTC 2018"""
    
    VERSION = "2025.05.25-CORRETTA-NTC2018"  # Identificatore versione
    
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
        """Calcola le resistenze per una singola parete o maschio"""
        
        logger.info(f"Calcolo resistenze per L={L}m, h={h}m, A={A}m²")
        
        # V_t1 - Taglio per fessurazione diagonale (NTC 2018 eq. 8.7.1.16)
        sigma_0 = N / (A * 1000) if A > 0 else 0  # kN/m² -> MPa
        
        # Formula base V_t1
        V_t1_base = A * tau0 * math.sqrt(1 + sigma_0/tau0) * 1000  # kN
        
        # Limite superiore V_t1 (NTC 2018 - limite resistenza)
        V_t1_limite = A * 0.065 * fcm * 1000  # kN
        
        # V_t1 finale con coefficienti di sicurezza
        V_t1_pre_sicurezza = min(V_t1_base, V_t1_limite)
        V_t1 = V_t1_pre_sicurezza / gamma_totale  # CORREZIONE: solo gamma_totale
        
        logger.info(f"V_t1: base={V_t1_base:.1f}, limite={V_t1_limite:.1f}, finale={V_t1:.1f} kN")
        
        # V_t2 - Taglio con fattore di forma (NTC 2018 eq. 8.7.1.17)
        # Fattore di forma b corretto secondo NTC 2018
        rapporto_h_L = h / L if L > 0 else 0
        
        if rapporto_h_L >= 1.5:
            b = 1.0
        else:
            b = 1.5 - rapporto_h_L / 3.0  # Formula corretta NTC 2018
        
        V_t2 = V_t1 * b

        logger.debug(f"Fattore b: h/L={rapporto_h_L:.3f}, b={b:.3f}, V_t2={V_t2:.1f} kN")
        
        # V_t3 - Pressoflessione (NTC 2018 § 8.7.1.5)
        sigma_max = self._calculate_max_compression(N, A, e, L)
        
        # Verifica limite compressione
        fcm_ridotto = 0.85 * fcm  # Resistenza ridotta per carichi di lunga durata
        
        if sigma_max < fcm_ridotto:
            # Formula pressoflessione
            mu = 1 - sigma_max / fcm_ridotto
            V_t3 = (A * fcm * mu * 1000) / gamma_totale  # CORREZIONE: gamma_totale
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
        
        # Condizioni di vincolo
        constraints = self.project_data.get('constraints', {})
        bottom = constraints.get('bottom', 'Incastro')
        top = constraints.get('top', 'Incastro (Grinter)')
        
        # Fattore di vincolo secondo schema statico
        if bottom == 'Incastro' and 'Incastro' in top:
            k_vincolo = 12  # Doppio incastro
            logger.info("Schema statico: Doppio incastro")
        elif bottom == 'Incastro' and 'Libero' in top:
            k_vincolo = 3   # Mensola
            logger.info("Schema statico: Mensola")
        else:
            k_vincolo = 6   # Caso intermedio (incastro-cerniera)
            logger.info("Schema statico: Incastro-cerniera")
            
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
                
                # Rigidezza flessionale
                K_flex_m = k_vincolo * E * I_m / h**3
                
                # Rigidezza tagliante
                A_m = L_m * t
                chi = 1.2  # Fattore di forma per sezione rettangolare
                K_shear_m = chi * G * A_m / h
                
                # Rigidezza combinata maschio (molle in serie)
                K_m = 1 / (1/K_flex_m + 1/K_shear_m)
                
                K_total += K_m
                
                logger.debug(f"Maschio {i+1}: K_flex={K_flex_m/1000:.1f} kN/m, "
                           f"K_shear={K_shear_m/1000:.1f} kN/m, K_tot={K_m/1000:.1f} kN/m")
                
            K_result = K_total / 1000  # Pa -> kN/m
            logger.debug(f"Rigidezza con aperture: {K_result:.1f} kN/m")
            return K_result
            
        else:
            # Parete senza aperture
            I = t * L**3 / 12  # Momento d'inerzia
            
            # Rigidezza flessionale
            K_flex = k_vincolo * E * I / h**3
            
            # Rigidezza tagliante
            A = L * t
            chi = 1.2  # Fattore di forma per sezione rettangolare
            K_shear = chi * G * A / h
            
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