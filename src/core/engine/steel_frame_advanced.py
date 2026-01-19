"""
Calcolatore avanzato per telai in acciaio con profili multipli
Gestisce profili accoppiati e vincoli complessi
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional

class SteelFrameAdvancedCalculator:
    """Calcola rigidezza e resistenza telai acciaio con profili multipli"""
    
    def __init__(self):
        # Database profili (proprietà geometriche)
        self.steel_profiles = {
            'HEA 100': {'A': 21.2, 'Iy': 349, 'Iz': 133, 'Wel_y': 72.8, 'h': 96, 'b': 100},
            'HEA 120': {'A': 25.3, 'Iy': 606, 'Iz': 231, 'Wel_y': 106, 'h': 114, 'b': 120},
            'HEA 140': {'A': 31.4, 'Iy': 1033, 'Iz': 389, 'Wel_y': 155, 'h': 133, 'b': 140},
            'HEA 160': {'A': 38.8, 'Iy': 1673, 'Iz': 616, 'Wel_y': 220, 'h': 152, 'b': 160},
            'HEA 180': {'A': 45.3, 'Iy': 2510, 'Iz': 925, 'Wel_y': 294, 'h': 171, 'b': 180},
            'HEA 200': {'A': 53.8, 'Iy': 3692, 'Iz': 1336, 'Wel_y': 389, 'h': 190, 'b': 200},
            
            'HEB 100': {'A': 26.0, 'Iy': 450, 'Iz': 167, 'Wel_y': 89.9, 'h': 100, 'b': 100},
            'HEB 120': {'A': 34.0, 'Iy': 864, 'Iz': 318, 'Wel_y': 144, 'h': 120, 'b': 120},
            'HEB 140': {'A': 43.0, 'Iy': 1509, 'Iz': 550, 'Wel_y': 216, 'h': 140, 'b': 140},
            'HEB 160': {'A': 54.3, 'Iy': 2492, 'Iz': 889, 'Wel_y': 311, 'h': 160, 'b': 160},
            
            'IPE 100': {'A': 10.3, 'Iy': 171, 'Iz': 15.9, 'Wel_y': 34.2, 'h': 100, 'b': 55},
            'IPE 120': {'A': 13.2, 'Iy': 318, 'Iz': 27.7, 'Wel_y': 53.0, 'h': 120, 'b': 64},
            'IPE 140': {'A': 16.4, 'Iy': 541, 'Iz': 44.9, 'Wel_y': 77.3, 'h': 140, 'b': 73},
            'IPE 160': {'A': 20.1, 'Iy': 869, 'Iz': 68.3, 'Wel_y': 109, 'h': 160, 'b': 82},
            'IPE 180': {'A': 23.9, 'Iy': 1317, 'Iz': 101, 'Wel_y': 146, 'h': 180, 'b': 91},
            'IPE 200': {'A': 28.5, 'Iy': 1943, 'Iz': 142, 'Wel_y': 194, 'h': 200, 'b': 100},
        }
        
        # Proprietà acciaio
        self.steel_properties = {
            'S235': {'fy': 235, 'fu': 360, 'E': 210000},
            'S275': {'fy': 275, 'fu': 430, 'E': 210000},
            'S355': {'fy': 355, 'fu': 510, 'E': 210000},
            'S450': {'fy': 440, 'fu': 550, 'E': 210000},
        }
        
    def calculate_frame_stiffness_advanced(self, opening: Dict, reinforcement: Dict, wall_data: Dict) -> Dict:
        """
        Calcola rigidezza telaio con profili multipli e vincoli avanzati.

        Args:
            opening (Dict): Dati geometrici dell'apertura.
            reinforcement (Dict): Dati del rinforzo con profili multipli.
            wall_data (Dict): Dati geometrici della parete.

        Returns:
            Dict: Dizionario con rigidezza e altre proprietà calcolate.
        """
        
        # Estrai dati
        L = opening['width'] / 100  # m
        H = opening['height'] / 100  # m
        
        # Dati architrave
        arch_data = reinforcement.get('architrave', {})
        n_arch = arch_data.get('n_profili', 1)
        arch_profile = arch_data.get('profilo', 'HEA 200')
        arch_spacing = arch_data.get('interasse', 0) / 100  # m
        arch_disposition = arch_data.get('disposizione', 'In linea')
        
        # Dati piedritti (se telaio completo)
        if 'piedritti' in reinforcement:
            pied_data = reinforcement['piedritti']
            n_pied = pied_data.get('n_profili', 1)
            pied_profile = pied_data.get('profilo', 'HEA 200')
            pied_spacing = pied_data.get('interasse', 0) / 100  # m
            is_portal = True
        else:
            is_portal = False
            
        # Calcola proprietà sezione composta architrave
        arch_props = self._calculate_composite_properties(
            arch_profile, n_arch, arch_spacing, arch_disposition
        )
        
        # Calcola proprietà sezione composta piedritti
        if is_portal:
            pied_props = self._calculate_composite_properties(
                pied_profile, n_pied, pied_spacing, pied_data.get('disposizione', 'In linea')
            )
        
        # Estrai vincoli
        vincoli = reinforcement.get('vincoli', {})
        
        # Calcola rigidezza considerando vincoli
        if is_portal:
            K_frame = self._calculate_portal_stiffness_advanced(
                L, H, arch_props, pied_props, vincoli
            )
        else:
            K_frame = self._calculate_beam_stiffness_advanced(
                L, arch_props, vincoli
            )
            
        # Calcola sollecitazioni di progetto
        design_forces = self._calculate_design_forces(
            opening, reinforcement, wall_data, K_frame
        )
        
        return {
            'K_frame': K_frame,
            'arch_props': arch_props,
            'pied_props': pied_props if is_portal else None,
            'design_forces': design_forces,
            'n_arch': n_arch,
            'n_pied': n_pied if is_portal else 0,
        }
        
    def _calculate_composite_properties(self, profile_name: str, n_profiles: int, 
                                      spacing: float, disposition: str) -> Dict:
        """
        Calcola proprietà sezione composta da profili multipli.

        Args:
            profile_name (str): Nome del profilo singolo (es. 'HEA 200').
            n_profiles (int): Numero di profili.
            spacing (float): Interasse tra i profili [m].
            disposition (str): Disposizione profili ('In linea', 'Sfalsati', 'Accoppiati').

        Returns:
            Dict: Proprietà della sezione composta (Area, Inerzie, Moduli).
        """
        
        # Proprietà profilo singolo
        if profile_name not in self.steel_profiles:
            # Usa default se profilo non trovato
            profile_name = 'HEA 200'
            
        single = self.steel_profiles[profile_name]
        
        # Area totale
        A_tot = single['A'] * n_profiles  # cm²
        
        # Momento d'inerzia composto
        if n_profiles == 1:
            Iy_tot = single['Iy']  # cm⁴
            Iz_tot = single['Iz']  # cm⁴
        else:
            # Calcola in base alla disposizione
            if disposition == 'In linea':
                # Profili allineati su asse forte
                Iy_tot = single['Iy'] * n_profiles
                # Teorema di Huygens per asse debole
                if spacing > 0:
                    for i in range(n_profiles):
                        d = (i - (n_profiles-1)/2) * spacing * 100  # cm
                        Iz_tot = single['Iz'] + single['A'] * d**2
                    Iz_tot *= n_profiles
                else:
                    # Profili accoppiati
                    Iz_tot = single['Iz'] * n_profiles
                    
            elif disposition == 'Sfalsati':
                # Configurazione sfalsata
                Iy_tot = single['Iy'] * n_profiles * 1.2  # Fattore empirico
                Iz_tot = single['Iz'] * n_profiles * 1.5
                
            elif 'Accoppiati' in disposition:
                # Es. "Accoppiati 2+2"
                Iy_tot = single['Iy'] * n_profiles * 1.1
                Iz_tot = single['Iz'] * n_profiles * 1.3
                
            else:
                # Default
                Iy_tot = single['Iy'] * n_profiles
                Iz_tot = single['Iz'] * n_profiles
                
        # Modulo resistente
        h = single['h'] / 10  # cm -> dm per coerenza
        Wel_y_tot = 2 * Iy_tot / h  # cm³
        
        return {
            'A': A_tot,
            'Iy': Iy_tot,
            'Iz': Iz_tot,
            'Wel_y': Wel_y_tot,
            'profile_name': profile_name,
            'n_profiles': n_profiles,
            'spacing': spacing
        }
        
    def _calculate_portal_stiffness_advanced(self, L: float, H: float, 
                                           arch_props: Dict, pied_props: Dict,
                                           vincoli: Dict) -> float:
        """
        Calcola rigidezza portale con vincoli avanzati.

        Args:
            L (float): Larghezza portale [m].
            H (float): Altezza portale [m].
            arch_props (Dict): Proprietà sezione architrave.
            pied_props (Dict): Proprietà sezione piedritti.
            vincoli (Dict): Definizione vincoli alla base e ai nodi.

        Returns:
            float: Rigidezza traslante effettiva [kN/m].
        """
        
        E = 210000 * 1000  # kN/m²
        
        # Inerzie in m⁴
        Ib = arch_props['Iy'] * 1e-8
        Ic = pied_props['Iy'] * 1e-8
        
        # Fattori di vincolo
        base_factors = self._get_base_constraint_factors(vincoli)
        node_factors = self._get_node_constraint_factors(vincoli)
        
        # Rigidezza base del portale
        K_base = 12 * E * Ic / (H**3) * (1 + 3*Ic*H/(Ib*L))
        
        # Applica fattori di vincolo
        K_eff = K_base * base_factors['k_mult'] * node_factors['k_mult']
        
        # Considera collaborazione muratura
        collab = vincoli.get('collaborazione', {})
        if collab.get('tipo') == 'Collaborazione totale':
            K_eff *= 1.3  # Incremento empirico
        elif collab.get('tipo') == 'Collaborazione parziale':
            K_eff *= 1.15
            
        # Effetti secondo ordine se richiesti
        if vincoli.get('avanzate', {}).get('secondo_ordine', False):
            # Riduzione per effetti P-Delta
            K_eff *= 0.9
            
        return K_eff
        
    def _calculate_beam_stiffness_advanced(self, L: float, arch_props: Dict, 
                                          vincoli: Dict) -> float:
        """
        Calcola rigidezza trave con vincoli avanzati.

        Args:
            L (float): Larghezza trave [m].
            arch_props (Dict): Proprietà sezione architrave.
            vincoli (Dict): Vincoli agli estremi.

        Returns:
            float: Rigidezza flessionale equivalente [kN/m].
        """
        
        E = 210000 * 1000  # kN/m²
        I = arch_props['Iy'] * 1e-8  # m⁴
        
        # Rigidezza base trave
        K_base = 48 * E * I / L**3
        
        # Fattori per vincoli agli estremi
        if 'arco_sx' in vincoli or 'arco_dx' in vincoli:
            # Vincoli per arco
            K_base *= 0.7  # Riduzione per vincoli arco
            
        return K_base
        
    def _get_base_constraint_factors(self, vincoli: Dict) -> Dict:
        """
        Ottiene fattori moltiplicativi per vincoli alla base.

        Args:
            vincoli (Dict): Definizione vincoli.

        Returns:
            Dict: Fattori moltiplicativi per rigidezza e resistenza.
        """
        
        factors = {'k_mult': 1.0, 'strength_mult': 1.0}
        
        # Vincolo sinistro
        base_sx = vincoli.get('base_sx', {}).get('tipo', 'Incastro perfetto')
        base_dx = vincoli.get('base_dx', base_sx)  # Se non specificato, uguale a sx
        
        # Fattori per tipo vincolo
        constraint_factors = {
            'Incastro perfetto': 1.0,
            'Cerniera': 0.5,
            'Appoggio semplice': 0.3,
            'Semincastro elastico': 0.7,
            'Vincolo elastico': 0.6,
            'Carrello verticale': 0.4,
            'Carrello orizzontale': 0.2
        }
        
        # Media dei fattori (approssimazione)
        f_sx = constraint_factors.get(base_sx, 1.0)
        f_dx = constraint_factors.get(base_dx.get('tipo') if isinstance(base_dx, dict) else base_dx, f_sx)
        
        factors['k_mult'] = (f_sx + f_dx) / 2
        
        return factors
        
    def _get_node_constraint_factors(self, vincoli: Dict) -> Dict:
        """
        Ottiene fattori moltiplicativi per vincoli ai nodi.

        Args:
            vincoli (Dict): Definizione vincoli.

        Returns:
            Dict: Fattori moltiplicativi per rigidezza e resistenza.
        """
        
        factors = {'k_mult': 1.0, 'strength_mult': 1.0}
        
        # Vincolo nodi
        nodo_sx = vincoli.get('nodo_sx', {}).get('tipo', 'Incastro (continuità)')
        nodo_dx = vincoli.get('nodo_dx', nodo_sx)
        
        node_factors = {
            'Incastro (continuità)': 1.0,
            'Cerniera': 0.6,
            'Semincastro con riduzione': 0.8,
            'Giunzione bullonata': 0.9,
            'Giunzione saldata parziale': 0.85
        }
        
        f_sx = node_factors.get(nodo_sx, 1.0)
        f_dx = node_factors.get(nodo_dx.get('tipo') if isinstance(nodo_dx, dict) else nodo_dx, f_sx)
        
        factors['k_mult'] = (f_sx + f_dx) / 2
        
        return factors
        
    def _calculate_design_forces(self, opening: Dict, reinforcement: Dict,
                                wall_data: Dict, K_frame: float) -> Dict:
        """
        Calcola sollecitazioni di progetto sul telaio.

        Args:
            opening (Dict): Dati apertura.
            reinforcement (Dict): Dati rinforzo.
            wall_data (Dict): Dati parete.
            K_frame (float): Rigidezza calcolata [kN/m].

        Returns:
            Dict: Sollecitazioni massime (M_max, V_max, N_max).
        """
        
        # Carichi dal muro
        t = wall_data.get('thickness', 30) / 100  # m
        h_muro = wall_data.get('height', 350) / 100  # m
        
        # Carico verticale sull'architrave (semplificato)
        h_sopra = h_muro - (opening['y'] + opening['height']) / 100
        q_vert = 18 * t * h_sopra  # kN/m (peso muratura sopra)
        
        # Momento max architrave
        L = opening['width'] / 100  # m
        M_max = q_vert * L**2 / 8  # kNm
        
        # Taglio max
        V_max = q_vert * L / 2  # kN
        
        # Sforzo normale nei piedritti
        N_max = V_max  # kN (approssimazione)
        
        return {
            'M_max': M_max,
            'V_max': V_max,
            'N_max': N_max,
            'q_vert': q_vert
        }