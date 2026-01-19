"""
Calcolatore per aperture curve e cerchiature calandrate
Gestisce archi e volte con rinforzi metallici
"""

import numpy as np
import math
from typing import Dict, Optional

class CurvedOpeningsCalculator:
    """Calcola proprietà e verifiche per aperture curve"""
    
    def __init__(self):
        self.arch_types = {
            'Arco a tutto sesto': {'f/L': 0.5, 'beta': 1.0},
            'Arco ribassato': {'f/L': 0.25, 'beta': 0.8},
            'Arco a sesto acuto': {'f/L': 0.75, 'beta': 1.2},
            'Arco ellittico': {'f/L': 0.4, 'beta': 0.9},
        }
        
    def calculate_curved_frame(self, opening: Dict, reinforcement: Dict, 
                              wall_data: Dict) -> Dict:
        """
        Calcola proprietà cerchiatura calandrata per arco.

        Args:
            opening (Dict): Dati geometrici dell'apertura.
            reinforcement (Dict): Dati del rinforzo con info arco.
            wall_data (Dict): Dati geometrici della parete.

        Returns:
            Dict: Dizionario con rigidezza e proprietà calcolate.
        """
        
        # Estrai dati arco
        arco_data = reinforcement.get('arco', {})
        tipo_apertura = arco_data.get('tipo_apertura', 'Arco a tutto sesto')
        raggio = arco_data.get('raggio', 150) / 100  # m
        freccia = arco_data.get('freccia', 30) / 100  # m
        
        # Profilo calandrato
        profilo = arco_data.get('profilo', 'IPE 160')
        n_profili = arco_data.get('n_profili', 1)
        metodo = arco_data.get('metodo', 'A freddo')
        
        # Calcola geometria arco
        L = opening['width'] / 100  # luce m
        
        # Raggio effettivo se non specificato
        if raggio == 1.5:  # valore default
            # Calcola da freccia e luce
            raggio = (L**2 + 4*freccia**2) / (8*freccia)
            
        # Lunghezza arco
        if freccia < raggio:
            # Arco circolare
            theta = 2 * math.asin(L / (2 * raggio))
            s = raggio * theta  # lunghezza arco
        else:
            # Approssimazione parabolica
            s = L * (1 + 8*freccia**2/(3*L**2))
            
        # Proprietà profilo (semplificato)
        E = 210000 * 1000  # kN/m²
        
        # Inerzia profilo calandrato (ridotta per curvatura)
        I_base = self._get_profile_inertia(profilo) * n_profili
        
        # Riduzione per calandratura
        reduction_factors = {
            'A freddo': 0.85,
            'A caldo': 0.95,
            'Preformato': 1.0
        }
        k_red = reduction_factors.get(metodo, 0.85)
        
        I_eff = I_base * k_red * 1e-8  # m⁴
        
        # Rigidezza arco (formula semplificata)
        # Considera comportamento ad arco
        K_arch = E * I_eff / raggio**3
        
        # Fattore di forma per tipo arco
        arch_factor = self.arch_types.get(tipo_apertura, {}).get('beta', 1.0)
        K_arch *= arch_factor
        
        # Spinta orizzontale
        H = self._calculate_horizontal_thrust(opening, wall_data, raggio, freccia)
        
        return {
            'K_frame': K_arch,
            'geometry': {
                'radius': raggio,
                'rise': freccia,
                'span': L,
                'arc_length': s,
                'angle': theta if 'theta' in locals() else 0
            },
            'horizontal_thrust': H,
            'profile': profilo,
            'n_profiles': n_profili,
            'method': metodo
        }
        
    def _get_profile_inertia(self, profile_name: str) -> float:
        """
        Ottiene inerzia profilo (cm⁴).

        Args:
            profile_name (str): Nome del profilo (es. 'IPE 160').

        Returns:
            float: Momento d'inerzia [cm⁴].
        """
        
        # Database semplificato
        profiles = {
            'IPE 100': 171,
            'IPE 120': 318,
            'IPE 140': 541,
            'IPE 160': 869,
            'IPE 180': 1317,
            'IPE 200': 1943,
            'HEA 100': 349,
            'HEA 120': 606,
            'HEA 140': 1033,
            'HEA 160': 1673,
        }
        
        return profiles.get(profile_name, 869)  # default IPE 160
        
    def _calculate_horizontal_thrust(self, opening: Dict, wall_data: Dict,
                                   radius: float, rise: float) -> float:
        """
        Calcola spinta orizzontale dell'arco.

        Args:
            opening (Dict): Dati apertura.
            wall_data (Dict): Dati parete.
            radius (float): Raggio dell'arco [m].
            rise (float): Freccia dell'arco [m].

        Returns:
            float: Spinta orizzontale [kN].
        """
        
        # Carico verticale
        t = wall_data.get('thickness', 30) / 100  # m
        h_muro = wall_data.get('height', 350) / 100  # m
        h_sopra = h_muro - (opening['y'] + opening['height']) / 100
        
        q = 18 * t * h_sopra  # kN/m
        L = opening['width'] / 100  # m
        
        # Spinta orizzontale (formula arco parabolico)
        H = q * L**2 / (8 * rise)  # kN
        
        return H
        
    def verify_arch_stability(self, arch_data: Dict, wall_data: Dict) -> Dict:
        """
        Verifica stabilità arco.

        Args:
            arch_data (Dict): Dati calcolati dell'arco (inclusa spinta).
            wall_data (Dict): Dati parete.

        Returns:
            Dict: Esito verifica stabilità.
        """
        
        H = arch_data.get('horizontal_thrust', 0)
        geometry = arch_data.get('geometry', {})
        
        # Verifica semplificata
        # Controllo che la spinta sia contenibile dai piedritti
        t_muro = wall_data.get('thickness', 30) / 100  # m
        
        # Resistenza piedritto (molto semplificata)
        H_res = 50 * t_muro  # kN (valore empirico)
        
        safety_factor = H_res / H if H > 0 else 999
        
        return {
            'verified': safety_factor > 1.5,
            'safety_factor': safety_factor,
            'thrust': H,
            'resistance': H_res
        }