"""
Calcoli Cerchiature in Acciaio secondo NTC 2018
Arch. Michelangelo Bartolotta
VERSIONE MODIFICATA CON OUTPUT STANDARDIZZATO
REFACTORING: Costanti centralizzate in NTC2018
"""

import numpy as np
import math
from typing import Dict, Optional

# NUOVA IMPORT
from src.core.engine.frame_result import FrameResult
from src.data.ntc2018_constants import NTC2018


class SteelFrameCalculator:
    """Calcolatore per cerchiature in acciaio"""
    
    def __init__(self):
        # Costanti da NTC2018
        self.E_s = NTC2018.Acciaio.E  # MPa - Modulo elastico acciaio
        self.gamma_m0 = NTC2018.Sicurezza.GAMMA_M0  # Coefficiente sicurezza acciaio
        
        # Database semplificato profili (valori indicativi)
        self.profiles_db = {
            'HEA': {
                '100': {'Ix': 349, 'Iy': 134, 'A': 21.2, 'Wx': 72.8, 'h': 96, 'b': 100},
                '120': {'Ix': 606, 'Iy': 231, 'A': 25.3, 'Wx': 106.3, 'h': 114, 'b': 120},
                '140': {'Ix': 1033, 'Iy': 389, 'A': 31.4, 'Wx': 155.4, 'h': 133, 'b': 140},
                '160': {'Ix': 1673, 'Iy': 616, 'A': 38.8, 'Wx': 220.1, 'h': 152, 'b': 160},
                '180': {'Ix': 2510, 'Iy': 925, 'A': 45.3, 'Wx': 293.6, 'h': 171, 'b': 180},
                '200': {'Ix': 3692, 'Iy': 1336, 'A': 53.8, 'Wx': 388.6, 'h': 190, 'b': 200},
            },
            'HEB': {
                '100': {'Ix': 450, 'Iy': 167, 'A': 26.0, 'Wx': 89.9, 'h': 100, 'b': 100},
                '120': {'Ix': 864, 'Iy': 318, 'A': 34.0, 'Wx': 144.1, 'h': 120, 'b': 120},
                '140': {'Ix': 1509, 'Iy': 550, 'A': 43.0, 'Wx': 215.6, 'h': 140, 'b': 140},
                '160': {'Ix': 2492, 'Iy': 889, 'A': 54.3, 'Wx': 311.5, 'h': 160, 'b': 160},
                '180': {'Ix': 3831, 'Iy': 1363, 'A': 65.3, 'Wx': 425.7, 'h': 180, 'b': 180},
                '200': {'Ix': 5696, 'Iy': 2003, 'A': 78.1, 'Wx': 569.6, 'h': 200, 'b': 200},
            },
            'IPE': {
                '100': {'Ix': 171, 'Iy': 15.9, 'A': 10.3, 'Wx': 34.2, 'h': 100, 'b': 55},
                '120': {'Ix': 318, 'Iy': 27.7, 'A': 13.2, 'Wx': 53.0, 'h': 120, 'b': 64},
                '140': {'Ix': 541, 'Iy': 44.9, 'A': 16.4, 'Wx': 77.3, 'h': 140, 'b': 73},
                '160': {'Ix': 869, 'Iy': 68.3, 'A': 20.1, 'Wx': 108.7, 'h': 160, 'b': 82},
                '180': {'Ix': 1317, 'Iy': 101, 'A': 23.9, 'Wx': 146.3, 'h': 180, 'b': 91},
                '200': {'Ix': 1943, 'Iy': 142, 'A': 28.5, 'Wx': 194.3, 'h': 200, 'b': 100},
            }
        }
        
        # Proprietà acciaio da NTC2018
        self.steel_grades = {
            classe: {'fyk': prop.fyk, 'ftk': prop.ftk}
            for classe, prop in NTC2018.Acciaio.CLASSI.items()
        }
        
    def calculate_frame_stiffness(self, opening_data: Dict, rinforzo_data: Dict) -> Dict:
        """
        Calcola la rigidezza del telaio metallico.

        Args:
            opening_data (Dict): Dati geometrici dell'apertura.
            rinforzo_data (Dict): Dati del rinforzo in acciaio.

        Returns:
            Dict: Risultato standardizzato con rigidezza e proprietà.
        """
        # Inizializza risultato standard
        result = FrameResult(materiale='acciaio')
        
        if not rinforzo_data or rinforzo_data.get('materiale') != 'acciaio':
            return result.to_dict()
            
        # Dimensioni apertura
        L = opening_data['width'] / 100  # m
        h = opening_data['height'] / 100  # m
        
        result.L = L
        result.h = h
        result.tipo = rinforzo_data.get('tipo', '')
        
        tipo = rinforzo_data.get('tipo', '')
        
        # Calcola rigidezza in base al tipo
        if 'Telaio completo' in tipo:
            K = self._calculate_portal_frame_stiffness(h, L, rinforzo_data)
        elif 'Solo architrave' in tipo:
            K = self._calculate_beam_stiffness(L, rinforzo_data)
        elif 'arco' in tipo.lower():
            K = self._calculate_arch_stiffness(L, h, rinforzo_data)
        else:
            K = 0
            result.add_warning(f"Tipo di rinforzo non riconosciuto: {tipo}")
            
        result.K_frame = K
        
        # Aggiungi dati specifici acciaio
        architrave = rinforzo_data.get('architrave', {})
        piedritti = rinforzo_data.get('piedritti', {})
        
        result.extra_data = {
            'profilo_architrave': architrave.get('profilo', ''),
            'profilo_piedritti': piedritti.get('profilo', '') if piedritti else '',
            'classe_acciaio': rinforzo_data.get('classe_acciaio', 'S235'),
            'doppio_architrave': architrave.get('doppio', False),
            'doppio_piedritti': piedritti.get('doppio', False) if piedritti else False,
            'ruotato_architrave': architrave.get('ruotato', False),
            'ruotato_piedritti': piedritti.get('ruotato', False) if piedritti else False
        }
        
        # Calcola capacità se richiesto
        capacity = self.calculate_frame_capacity(opening_data, rinforzo_data, {})
        if capacity:
            result.M_max = capacity.get('M_Rd_beam', 0)
            result.V_max = capacity.get('V_Rd_beam', 0)
            result.N_max = capacity.get('N_Rd_column', 0)
            
        return result.to_dict()
            
    def _calculate_portal_frame_stiffness(self, h: float, L: float, rinforzo_data: Dict) -> float:
        """
        Calcola rigidezza telaio completo (portale).

        Args:
            h (float): Altezza apertura [m].
            L (float): Larghezza apertura [m].
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            float: Rigidezza traslante del telaio [kN/m].
        """
        # Profili
        architrave = rinforzo_data.get('architrave', {})
        piedritti = rinforzo_data.get('piedritti', {})
        
        # Estrai proprietà profili
        I_beam = self._get_profile_property(architrave.get('profilo'), 'Ix', architrave.get('ruotato'))
        I_column = self._get_profile_property(piedritti.get('profilo'), 'Ix', piedritti.get('ruotato'))
        
        if not I_beam or not I_column:
            # Valori di default se profilo non trovato
            I_beam = 1000  # cm^4
            I_column = 1000  # cm^4
            
        # Converti in m^4
        I_beam = I_beam * 1e-8
        I_column = I_column * 1e-8
        
        # Doppio profilo
        if architrave.get('doppio'):
            I_beam *= 2
        if piedritti.get('doppio'):
            I_column *= 2
            
        # Vincoli
        vincoli = rinforzo_data.get('vincoli', {})
        vincolo_base = vincoli.get('base', 'Incastro')
        vincolo_nodo = vincoli.get('nodo', 'Incastro (continuità)')
        
        # Rigidezza secondo Grinter per telai
        if vincolo_base == 'Incastro' and 'Incastro' in vincolo_nodo:
            # Telaio con nodi rigidi e basi incastrate
            k1 = 12 * self.E_s * 1e6 * I_column / h**3
            k2 = 12 * self.E_s * 1e6 * I_beam / L**3
            K = 1 / (1/k1 + 1/k2) * 2  # Due piedritti
        elif vincolo_base == 'Cerniera':
            # Telaio con basi incernierate
            K = 3 * self.E_s * 1e6 * I_column / h**3 * 2
        else:
            # Caso intermedio
            K = 6 * self.E_s * 1e6 * I_column / h**3 * 2
            
        return K / 1000  # kN/m
        
    def _calculate_beam_stiffness(self, L: float, rinforzo_data: Dict) -> float:
        """
        Calcola rigidezza solo architrave (trave su due appoggi elastici).

        Args:
            L (float): Larghezza apertura [m].
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            float: Rigidezza equivalente [kN/m].
        """
        architrave = rinforzo_data.get('architrave', {})
        
        I_beam = self._get_profile_property(architrave.get('profilo'), 'Ix', architrave.get('ruotato'))
        if not I_beam:
            I_beam = 1000  # cm^4 default
            
        I_beam = I_beam * 1e-8  # m^4
        
        if architrave.get('doppio'):
            I_beam *= 2
            
        # Rigidezza trave semplicemente appoggiata
        K = 48 * self.E_s * 1e6 * I_beam / L**3
        
        return K / 1000  # kN/m
        
    def _calculate_arch_stiffness(self, L: float, h: float, rinforzo_data: Dict) -> float:
        """
        Calcola rigidezza arco metallico.

        Args:
            L (float): Larghezza apertura [m].
            h (float): Altezza apertura [m].
            rinforzo_data (Dict): Dati del rinforzo.

        Returns:
            float: Rigidezza equivalente [kN/m].
        """
        if 'calandrato' in rinforzo_data.get('tipo', '').lower():
            # Arco calandrato
            arco = rinforzo_data.get('arco', {})
            R = arco.get('raggio', 150) / 100  # m
            f = arco.get('freccia', 30) / 100  # m
            
            architrave = rinforzo_data.get('architrave', {})
            I_arch = self._get_profile_property(architrave.get('profilo'), 'Ix', False)
            
            if not I_arch:
                I_arch = 1000  # cm^4
                
            I_arch = I_arch * 1e-8  # m^4
            
            if architrave.get('doppio'):
                I_arch *= 2
                
            # Rigidezza arco (formula approssimata)
            K = 3 * self.E_s * 1e6 * I_arch / (R**2 * f)
            
        else:
            # Arco con piedritti
            K = self._calculate_portal_frame_stiffness(h, L, rinforzo_data) * 1.2  # Fattore per arco
            
        return K / 1000  # kN/m
        
    def _get_profile_property(self, profile_name: str, property_name: str, 
                             is_rotated: bool = False) -> Optional[float]:
        """
        Ottiene proprietà del profilo dal database.

        Args:
            profile_name (str): Nome del profilo (es. 'HEA 200').
            property_name (str): Proprietà richiesta ('Ix', 'Iy', 'Wx', 'A').
            is_rotated (bool): Se True, considera il profilo ruotato di 90 gradi.

        Returns:
            Optional[float]: Valore della proprietà o None se non trovata.
        """
        if not profile_name:
            return None
            
        # Estrai tipo e dimensione (es. "HEA 200" -> "HEA", "200")
        parts = profile_name.split()
        if len(parts) < 2:
            return None
            
        profile_type = parts[0]
        size = parts[1]
        
        if profile_type in self.profiles_db and size in self.profiles_db[profile_type]:
            profile = self.profiles_db[profile_type][size]
            
            # Se ruotato di 90°, scambia Ix con Iy
            if is_rotated and property_name == 'Ix':
                return profile.get('Iy', None)
            elif is_rotated and property_name == 'Iy':
                return profile.get('Ix', None)
            else:
                return profile.get(property_name, None)
                
        return None
        
    def calculate_frame_capacity(self, opening_data: Dict, rinforzo_data: Dict, 
                               wall_data: Dict) -> Dict:
        """
        Calcola la capacità portante del telaio.

        Args:
            opening_data (Dict): Dati apertura.
            rinforzo_data (Dict): Dati rinforzo.
            wall_data (Dict): Dati parete.

        Returns:
            Dict: Dizionario con M_Rd, V_Rd, N_Rd.
        """
        if not rinforzo_data or rinforzo_data.get('materiale') != 'acciaio':
            return {'M_Rd': 0, 'V_Rd': 0, 'N_Rd': 0}
            
        # Classe acciaio
        steel_grade = rinforzo_data.get('classe_acciaio', 'S235')
        fyk = self.steel_grades.get(steel_grade, {}).get('fyk', 235)  # MPa
        
        results = {}
        
        # Calcola per architrave
        if 'architrave' in rinforzo_data:
            arch = rinforzo_data['architrave']
            
            W = self._get_profile_property(arch.get('profilo'), 'Wx', arch.get('ruotato'))
            A = self._get_profile_property(arch.get('profilo'), 'A', False)
            
            if W and A:
                W = W * 1e-6  # m³
                A = A * 1e-4  # m²
                
                if arch.get('doppio'):
                    W *= 2
                    A *= 2
                    
                # Momento resistente
                results['M_Rd_beam'] = W * fyk * 1e3 / self.gamma_m0  # kN·m
                
                # Taglio resistente (semplificato)
                results['V_Rd_beam'] = A * fyk * 1e3 / (math.sqrt(3) * self.gamma_m0)  # kN
                
        # Calcola per piedritti
        if 'piedritti' in rinforzo_data:
            pied = rinforzo_data['piedritti']
            
            W = self._get_profile_property(pied.get('profilo'), 'Wx', pied.get('ruotato'))
            A = self._get_profile_property(pied.get('profilo'), 'A', False)
            
            if W and A:
                W = W * 1e-6  # m³
                A = A * 1e-4  # m²
                
                if pied.get('doppio'):
                    W *= 2
                    A *= 2
                    
                # Capacità piedritti
                results['M_Rd_column'] = W * fyk * 1e3 / self.gamma_m0  # kN·m
                results['N_Rd_column'] = A * fyk * 1e3 / self.gamma_m0  # kN
                
        return results