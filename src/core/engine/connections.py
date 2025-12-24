"""
Verificatore per collegamenti e ancoraggi
Verifica tasselli, saldature e giunzioni
"""

import math
from typing import Dict, List, Optional

class ConnectionsVerifier:
    """Verifica collegamenti strutturali"""
    
    def __init__(self):
        # Database resistenze ancoraggi
        self.anchor_database = {
            'M12': {'Nrd': 15, 'Vrd': 10},  # kN
            'M16': {'Nrd': 25, 'Vrd': 18},
            'M20': {'Nrd': 40, 'Vrd': 30},
            'M24': {'Nrd': 60, 'Vrd': 45},
            'M27': {'Nrd': 80, 'Vrd': 60},
            'M30': {'Nrd': 100, 'Vrd': 75},
        }
        
        # Fattori riduzione per tipo ancoraggio
        self.anchor_factors = {
            'Tasselli chimici ad iniezione': 1.0,
            'Barre filettate con resina epossidica': 0.95,
            'Zanche/Staffe murate': 0.8,
            'Piastre con tasselli meccanici': 0.85,
            'Barre passanti con piastra': 1.1,
        }
        
    def verify_anchors(self, anchor_data: Dict, frame_forces: Dict) -> Dict:
        """
        Verifica ancoraggi alla muratura
        
        Args:
            anchor_data: dati sistema ancoraggio
            frame_forces: sollecitazioni dal telaio
            
        Returns:
            Dict con esito verifica
        """
        
        # Sistema ancoraggio
        sistema = anchor_data.get('sistema', 'Tasselli chimici ad iniezione')
        
        if 'chimici' in anchor_data:
            return self._verify_chemical_anchors(
                anchor_data['chimici'], frame_forces, sistema
            )
        elif 'zanche' in anchor_data:
            return self._verify_embedded_anchors(
                anchor_data['zanche'], frame_forces
            )
        else:
            # Default
            return {'verified': True, 'safety_factor': 2.0}
            
    def _verify_chemical_anchors(self, chimici: Dict, forces: Dict, 
                                sistema: str) -> Dict:
        """Verifica tasselli chimici"""
        
        # Dati tassello
        diametro = chimici.get('diametro', 'M16')
        n_per_nodo = chimici.get('n_per_nodo', 4)
        profondita = chimici.get('profondita', 20)  # cm
        disposizione = chimici.get('disposizione', 'Quadrata')
        
        # Resistenze base
        if diametro not in self.anchor_database:
            diametro = 'M16'  # default
            
        Nrd_single = self.anchor_database[diametro]['Nrd']
        Vrd_single = self.anchor_database[diametro]['Vrd']
        
        # Applica fattore per sistema
        k_sistema = self.anchor_factors.get(sistema, 1.0)
        
        # Fattore profondità (semplificato)
        k_prof = min(profondita / 15, 1.2)  # 15cm profondità riferimento
        
        # Fattore disposizione
        disposition_factors = {
            'Quadrata': 1.0,
            'Circolare': 0.95,
            'In linea': 0.85,
            'Sfalsata': 0.9
        }
        k_disp = disposition_factors.get(disposizione, 1.0)
        
        # Resistenze totali
        Nrd_tot = Nrd_single * n_per_nodo * k_sistema * k_prof * k_disp
        Vrd_tot = Vrd_single * n_per_nodo * k_sistema * k_prof * k_disp * 0.8
        
        # Sollecitazioni (stima da forze telaio)
        N_max = abs(forces.get('N_max', 0))
        V_max = abs(forces.get('V_max', 0))
        M_max = abs(forces.get('M_max', 0))
        
        # Forza risultante su ancoraggio (semplificata)
        # Considera momento che genera trazione
        h_nodo = 0.3  # altezza nodo m
        N_anchor = N_max + M_max / h_nodo
        V_anchor = V_max
        
        # Verifica combinata (ellisse interazione)
        utilization = (N_anchor/Nrd_tot)**2 + (V_anchor/Vrd_tot)**2
        
        safety_factor = 1.0 / math.sqrt(utilization) if utilization > 0 else 999
        
        return {
            'verified': safety_factor > 1.5,
            'safety_factor': safety_factor,
            'anchor_force_N': N_anchor,
            'anchor_force_V': V_anchor,
            'resistance_N': Nrd_tot,
            'resistance_V': Vrd_tot,
            'utilization': utilization,
            'details': {
                'diameter': diametro,
                'n_anchors': n_per_nodo,
                'depth': profondita,
                'disposition': disposizione
            }
        }
        
    def _verify_embedded_anchors(self, zanche: Dict, forces: Dict) -> Dict:
        """Verifica zanche murate"""
        
        tipo = zanche.get('tipo', 'Zanca a L')
        n_per_metro = zanche.get('n_per_metro', 4)
        ammorsamento = zanche.get('ammorsamento', 20)  # cm
        
        # Resistenza empirica per zanca
        R_zanca = 10 * (ammorsamento / 20)  # kN per zanca
        
        # Fattori per tipo
        type_factors = {
            'Zanca a L': 1.0,
            'Zanca a U': 1.2,
            'Staffa chiusa': 1.5,
            'Zanca con piastra': 1.3
        }
        k_tipo = type_factors.get(tipo, 1.0)
        
        # Resistenza totale (per metro)
        R_tot = R_zanca * n_per_metro * k_tipo
        
        # Sollecitazione
        F_max = max(abs(forces.get('V_max', 0)), abs(forces.get('N_max', 0)))
        
        safety_factor = R_tot / F_max if F_max > 0 else 999
        
        return {
            'verified': safety_factor > 2.0,
            'safety_factor': safety_factor,
            'force': F_max,
            'resistance': R_tot,
            'details': {
                'type': tipo,
                'n_per_m': n_per_metro,
                'embedment': ammorsamento
            }
        }
        
    def verify_welded_connection(self, weld_data: Dict, forces: Dict) -> Dict:
        """Verifica giunzione saldata"""
        
        tipo_saldatura = weld_data.get('tipo', 'A cordone d\'angolo')
        altezza_cordone = weld_data.get('altezza_cordone', 6)  # mm
        controllo = weld_data.get('controllo', 'Visivo')
        
        # Resistenza saldatura (semplificata)
        # Tensione ammissibile cordone
        sigma_w = 180  # N/mm² per S235
        
        # Lunghezza efficace cordone (stima)
        L_weld = 500  # mm (esempio)
        
        # Area gola
        a = altezza_cordone * 0.7  # gola efficace
        A_weld = a * L_weld  # mm²
        
        # Resistenza
        F_Rd = sigma_w * A_weld / 1000  # kN
        
        # Sollecitazione
        F_Ed = math.sqrt(forces.get('N_max', 0)**2 + forces.get('V_max', 0)**2)
        
        safety_factor = F_Rd / F_Ed if F_Ed > 0 else 999
        
        return {
            'verified': safety_factor > 1.5,
            'safety_factor': safety_factor,
            'force': F_Ed,
            'resistance': F_Rd,
            'weld_type': tipo_saldatura,
            'throat': a
        }
        
    def verify_bolted_connection(self, bolt_data: Dict, forces: Dict) -> Dict:
        """Verifica giunzione bullonata"""
        
        classe = bolt_data.get('classe', '8.8')
        diametro = bolt_data.get('diametro', 'M16')
        n_bulloni = bolt_data.get('n_bulloni', 4)
        precarico = bolt_data.get('precarico', False)
        
        # Resistenze bullone (da normativa)
        bolt_resistance = {
            'M12': {'Fv_Rd': 22, 'Fb_Rd': 29},  # kN
            'M16': {'Fv_Rd': 39, 'Fb_Rd': 51},
            'M20': {'Fv_Rd': 61, 'Fb_Rd': 80},
            'M24': {'Fv_Rd': 88, 'Fb_Rd': 115},
        }
        
        if diametro not in bolt_resistance:
            diametro = 'M16'
            
        Fv_Rd = bolt_resistance[diametro]['Fv_Rd'] * n_bulloni
        
        # Con precarico categoria B
        if precarico:
            Fv_Rd *= 1.25
            
        # Sollecitazione
        F_Ed = abs(forces.get('V_max', 0))
        
        safety_factor = Fv_Rd / F_Ed if F_Ed > 0 else 999
        
        return {
            'verified': safety_factor > 1.5,
            'safety_factor': safety_factor,
            'force': F_Ed,
            'resistance': Fv_Rd,
            'n_bolts': n_bulloni,
            'diameter': diametro,
            'class': classe
        }