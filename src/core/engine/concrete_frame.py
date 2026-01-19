"""
Calcoli Cerchiature in Calcestruzzo Armato secondo NTC 2018
Arch. Michelangelo Bartolotta
VERSIONE MODIFICATA CON OUTPUT STANDARDIZZATO
REFACTORING: Costanti centralizzate in NTC2018
"""

import numpy as np
import math
from typing import Dict, Optional, Tuple

# NUOVA IMPORT
from src.core.engine.frame_result import FrameResult
from src.data.ntc2018_constants import NTC2018


class ConcreteFrameCalculator:
    """Calcolatore per cerchiature in calcestruzzo armato"""
    
    def __init__(self):
        # Coefficienti di sicurezza da NTC2018
        self.gamma_c = NTC2018.Sicurezza.GAMMA_C      # Calcestruzzo
        self.gamma_s = NTC2018.Sicurezza.GAMMA_S      # Acciaio armatura
        self.alpha_cc = NTC2018.Sicurezza.ALPHA_CC    # Coefficiente effetto carichi di lunga durata

        # Proprietà materiali da NTC2018
        self.concrete_properties = {
            classe: {'fck': prop.fck, 'fcm': prop.fcm, 'fctm': prop.fctm, 'Ecm': prop.Ecm}
            for classe, prop in NTC2018.Cls.CLASSI.items()
        }

        self.steel_properties = {
            tipo: {'fyk': prop.fyk, 'ftk': prop.ftk, 'Es': prop.Es}
            for tipo, prop in NTC2018.AcciaioArm.TIPI.items()
        }
        
    def calculate_frame_stiffness(self, opening_data: Dict, rinforzo_data: Dict) -> Dict:
        """
        Calcola la rigidezza del telaio in C.A.

        Args:
            opening_data (Dict): Dati geometrici dell'apertura.
            rinforzo_data (Dict): Dati del rinforzo in C.A.

        Returns:
            Dict: Risultato standardizzato con rigidezza e proprietà.
        """
        # Inizializza risultato standard
        result = FrameResult(materiale='ca')
        
        if not rinforzo_data or rinforzo_data.get('materiale') != 'ca':
            return result.to_dict()
            
        # Dimensioni apertura
        L = opening_data['width'] / 100  # m
        h = opening_data['height'] / 100  # m
        
        result.L = L
        result.h = h
        result.tipo = rinforzo_data.get('tipo', '')
        
        tipo = rinforzo_data.get('tipo', '')
        
        # Calcola rigidezza in base al tipo
        if 'Telaio in C.A.' in tipo:
            K = self._calculate_rc_portal_frame_stiffness(h, L, rinforzo_data)
        elif 'Solo architrave in C.A.' in tipo:
            K = self._calculate_rc_beam_stiffness(L, rinforzo_data)
        else:
            K = 0
            result.add_warning(f"Tipo di rinforzo C.A. non riconosciuto: {tipo}")
            
        result.K_frame = K
        
        # Aggiungi dati specifici C.A.
        architrave = rinforzo_data.get('architrave', {})
        piedritti = rinforzo_data.get('piedritti', {})
        
        result.extra_data = {
            'classe_cls': rinforzo_data.get('classe_cls', 'C25/30'),
            'tipo_acciaio': rinforzo_data.get('tipo_acciaio', 'B450C'),
            'copriferro': rinforzo_data.get('copriferro', 30),
            'base_architrave': architrave.get('base', 30),
            'altezza_architrave': architrave.get('altezza', 40),
            'armatura_sup': architrave.get('armatura_sup', '3φ16'),
            'armatura_inf': architrave.get('armatura_inf', '3φ16'),
            'staffe': architrave.get('staffe', 'φ8/20')
        }
        
        if piedritti:
            result.extra_data.update({
                'base_piedritti': piedritti.get('base', 30),
                'spessore_piedritti': piedritti.get('spessore', 30),
                'armatura_piedritti': piedritti.get('armatura', '4φ16')
            })
        
        # Calcola capacità
        capacity = self.calculate_frame_capacity(opening_data, rinforzo_data, {})
        if capacity:
            result.M_max = capacity.get('M_Rd_beam', 0)
            result.V_max = capacity.get('V_Rd_beam', 0)
            result.N_max = capacity.get('N_Rd_column', 0)
            
        # Verifica armature minime
        verif_arm = self.verify_minimum_reinforcement(rinforzo_data)
        if not verif_arm['all_ok']:
            for msg in verif_arm['messages']:
                result.add_warning(msg)
                
        return result.to_dict()
            
    def _calculate_rc_portal_frame_stiffness(self, h: float, L: float, 
                                           rinforzo_data: Dict) -> float:
        """
        Calcola rigidezza telaio completo in C.A.

        Args:
            h (float): Altezza apertura [m].
            L (float): Larghezza apertura [m].
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            float: Rigidezza traslante del telaio [kN/m].
        """
        # Proprietà calcestruzzo
        concrete_class = rinforzo_data.get('classe_cls', 'C25/30')
        concrete = self.concrete_properties.get(concrete_class, self.concrete_properties['C25/30'])
        Ecm = concrete['Ecm'] * 1e6  # Pa
        
        # Sezioni
        architrave = rinforzo_data.get('architrave', {})
        b_beam = architrave.get('base', 30) / 100  # m
        h_beam = architrave.get('altezza', 40) / 100  # m
        
        # Momento d'inerzia architrave
        I_beam = b_beam * h_beam**3 / 12
        
        # Per telaio completo
        if 'piedritti' in rinforzo_data:
            piedritti = rinforzo_data['piedritti']
            b_col = piedritti.get('base', 30) / 100  # m
            h_col = piedritti.get('spessore', 30) / 100  # m
            
            # Momento d'inerzia piedritti (sezione ruotata)
            I_col = h_col * b_col**3 / 12
            
            # Rigidezza telaio con nodi rigidi
            # Formula semplificata per portale
            k1 = 12 * Ecm * I_col / h**3
            k2 = 12 * Ecm * I_beam / L**3
            K = 1 / (1/k1 + 1/k2) * 2  # Due piedritti
            
            # Riduzione per fessurazione (SLE)
            K *= NTC2018.Cls.FATTORE_INERZIA_FESSURATA  # Inerzia fessurata ≈ 0.5 Ig
            
        else:
            # Solo architrave
            K = self._calculate_rc_beam_stiffness(L, rinforzo_data)
            
        return K / 1000  # kN/m
        
    def _calculate_rc_beam_stiffness(self, L: float, rinforzo_data: Dict) -> float:
        """
        Calcola rigidezza solo architrave C.A.

        Args:
            L (float): Larghezza apertura [m].
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            float: Rigidezza equivalente [kN/m].
        """
        # Proprietà calcestruzzo
        concrete_class = rinforzo_data.get('classe_cls', 'C25/30')
        concrete = self.concrete_properties.get(concrete_class, self.concrete_properties['C25/30'])
        Ecm = concrete['Ecm'] * 1e6  # Pa
        
        # Sezione architrave
        architrave = rinforzo_data.get('architrave', {})
        b = architrave.get('base', 30) / 100  # m
        h = architrave.get('altezza', 40) / 100  # m
        
        # Momento d'inerzia
        I = b * h**3 / 12
        
        # Rigidezza trave appoggiata
        K = 48 * Ecm * I / L**3
        
        # Riduzione per fessurazione
        K *= NTC2018.Cls.FATTORE_INERZIA_FESSURATA

        return K / 1000  # kN/m
        
    def calculate_frame_capacity(self, opening_data: Dict, rinforzo_data: Dict,
                               wall_data: Dict) -> Dict:
        """
        Calcola la capacità portante del telaio C.A.

        Args:
            opening_data (Dict): Dati apertura.
            rinforzo_data (Dict): Dati rinforzo.
            wall_data (Dict): Dati parete.

        Returns:
            Dict: Dizionario con M_Rd, V_Rd, N_Rd per i vari elementi.
        """
        if not rinforzo_data or rinforzo_data.get('materiale') != 'ca':
            return {'M_Rd': 0, 'V_Rd': 0, 'N_Rd': 0}
            
        results = {}
        
        # Proprietà materiali
        concrete_class = rinforzo_data.get('classe_cls', 'C25/30')
        concrete = self.concrete_properties.get(concrete_class, self.concrete_properties['C25/30'])
        steel_type = rinforzo_data.get('tipo_acciaio', 'B450C')
        steel = self.steel_properties.get(steel_type, self.steel_properties['B450C'])
        
        # Resistenze di calcolo
        fcd = self.alpha_cc * concrete['fck'] / self.gamma_c  # MPa
        fyd = steel['fyk'] / self.gamma_s  # MPa
        
        # Calcolo architrave
        if 'architrave' in rinforzo_data:
            arch = rinforzo_data['architrave']
            b = arch.get('base', 30) / 100  # m
            h = arch.get('altezza', 40) / 100  # m
            copri = rinforzo_data.get('copriferro', 30) / 1000  # m
            
            # Armatura (parsing stringa tipo "3φ16")
            arm_sup = self._parse_reinforcement(arch.get('armatura_sup', '3φ16'))
            arm_inf = self._parse_reinforcement(arch.get('armatura_inf', '3φ16'))
            
            # Altezza utile
            d = h - copri - 0.008  # Assumendo staffe φ8
            
            # Momento resistente (semplificato)
            As = arm_inf['area'] * 1e-4  # m²
            x = As * fyd / (0.8 * b * fcd) * 1e-3  # Asse neutro
            if x < 0.259 * d:  # Campo 2
                M_Rd = As * fyd * (d - 0.4 * x) * 1e3  # kN·m
            else:
                M_Rd = 0.259 * b * d**2 * fcd * 1e3  # Limite campo 3
                
            results['M_Rd_beam'] = M_Rd
            
            # Taglio resistente (elementi senza armatura a taglio specifica)
            # Formula semplificata
            k = min(1 + math.sqrt(200/d/1000), 2.0)
            rho_l = As / (b * d)
            V_Rd = 0.18 * k * (100 * rho_l * concrete['fck'])**(1/3) * b * d * 1000
            results['V_Rd_beam'] = V_Rd
            
        # Calcolo piedritti (se presenti)
        if 'piedritti' in rinforzo_data:
            pied = rinforzo_data['piedritti']
            b_col = pied.get('base', 30) / 100  # m
            h_col = pied.get('spessore', 30) / 100  # m
            
            # Assumiamo armatura minima 4φ16
            As_col = 4 * 201 * 1e-6  # m² (4φ16)
            
            # Capacità a compressione
            N_Rd = (0.8 * b_col * h_col * fcd + As_col * fyd) * 1e3  # kN
            results['N_Rd_column'] = N_Rd
            
            # Momento resistente piedritti
            d_col = h_col - copri - 0.008
            M_Rd_col = As_col * fyd * d_col * 0.9 * 1e3  # kN·m semplificato
            results['M_Rd_column'] = M_Rd_col
            
        return results
        
    def _parse_reinforcement(self, reinforcement_str: str) -> Dict:
        """
        Analizza stringa armatura tipo "3φ16" o "4φ20".

        Args:
            reinforcement_str (str): Stringa descrittiva armatura.

        Returns:
            Dict: Dizionario con numero barre, diametro e area totale.
        """
        import re
        
        # Pattern per estrarre numero e diametro
        pattern = r'(\d+)φ(\d+)'
        match = re.match(pattern, reinforcement_str)
        
        if match:
            n_bars = int(match.group(1))
            diameter = int(match.group(2))
            
            # Area singola barra
            area_bar = math.pi * (diameter/2)**2  # mm²
            
            return {
                'n_bars': n_bars,
                'diameter': diameter,
                'area': n_bars * area_bar  # mm²
            }
        else:
            # Default se parsing fallisce
            return {
                'n_bars': 3,
                'diameter': 16,
                'area': 3 * 201  # 3φ16
            }
            
    def verify_minimum_reinforcement(self, rinforzo_data: Dict) -> Dict:
        """
        Verifica armature minime secondo NTC 2018.

        Args:
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            Dict: Risultati delle verifiche.
        """
        results = {'all_ok': True, 'messages': []}
        
        if rinforzo_data.get('materiale') != 'ca':
            return results
            
        # Sezioni
        architrave = rinforzo_data.get('architrave', {})
        b = architrave.get('base', 30)  # cm
        h = architrave.get('altezza', 40)  # cm
        
        # Area minima longitudinale (0.1% Ac)
        Ac = b * h  # cm²
        As_min = 0.001 * Ac * 100  # mm²
        
        # Verifica armatura superiore
        arm_sup = self._parse_reinforcement(architrave.get('armatura_sup', '3φ16'))
        if arm_sup['area'] < As_min:
            results['all_ok'] = False
            results['messages'].append(
                f"Armatura superiore insufficiente: {arm_sup['area']:.0f} mm² < {As_min:.0f} mm²"
            )
            
        # Verifica armatura inferiore
        arm_inf = self._parse_reinforcement(architrave.get('armatura_inf', '3φ16'))
        if arm_inf['area'] < As_min:
            results['all_ok'] = False
            results['messages'].append(
                f"Armatura inferiore insufficiente: {arm_inf['area']:.0f} mm² < {As_min:.0f} mm²"
            )
            
        # Verifica staffe (passo massimo)
        staffe = architrave.get('staffe', 'φ8/20')
        passo = int(staffe.split('/')[-1]) if '/' in staffe else 20
        passo_max = min(0.8 * (h - 5), 30)  # cm
        
        if passo > passo_max:
            results['all_ok'] = False
            results['messages'].append(
                f"Passo staffe eccessivo: {passo} cm > {passo_max:.0f} cm"
            )
            
        if results['all_ok']:
            results['messages'].append("✓ Tutte le armature rispettano i minimi normativi")
            
        return results
        
    def calculate_crack_width(self, M_Ed: float, rinforzo_data: Dict) -> float:
        """
        Calcola apertura fessure in esercizio (SLE).

        Args:
            M_Ed (float): Momento in esercizio [kN·m].
            rinforzo_data (Dict): Dati rinforzo.

        Returns:
            float: Apertura caratteristica fessure w_k [mm].
        """
        if rinforzo_data.get('materiale') != 'ca':
            return 0
            
        # Sezione
        architrave = rinforzo_data.get('architrave', {})
        b = architrave.get('base', 30) / 100  # m
        h = architrave.get('altezza', 40) / 100  # m
        copri = rinforzo_data.get('copriferro', 30) / 1000  # m
        
        # Armatura tesa
        arm_inf = self._parse_reinforcement(architrave.get('armatura_inf', '3φ16'))
        As = arm_inf['area'] * 1e-6  # m²
        phi = arm_inf['diameter']  # mm
        
        # Altezza utile
        d = h - copri - phi/2000
        
        # Tensione armatura in esercizio
        x = 0.3 * d  # Asse neutro stimato
        z = 0.9 * d  # Braccio leva
        sigma_s = M_Ed / (As * z) / 1000  # MPa
        
        # Formula EC2 semplificata per fessurazione
        # w_k = sr,max * (εsm - εcm)
        
        # Distanza massima fessure
        k1 = 0.8  # Barre ad aderenza migliorata
        k2 = 0.5  # Flessione
        rho_eff = As / (2.5 * b * copri)
        sr_max = 3.4 * copri + 0.425 * k1 * k2 * phi / rho_eff
        
        # Deformazione media
        steel = self.steel_properties.get(rinforzo_data.get('tipo_acciaio', 'B450C'))
        Es = steel['Es']  # MPa
        
        kt = 0.4  # Carichi di lunga durata
        epsilon_sm_cm = sigma_s / Es * (1 - kt * (sigma_s/250)**2)
        epsilon_sm_cm = max(epsilon_sm_cm, 0.6 * sigma_s / Es)
        
        # Apertura fessure
        w_k = sr_max * epsilon_sm_cm
        
        return w_k  # mm