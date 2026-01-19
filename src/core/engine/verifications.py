"""
Verifiche secondo NTC 2018 § 8.4.1
Verifica se l'intervento può essere classificato come locale
Arch. Michelangelo Bartolotta
REFACTORING: Costanti centralizzate in NTC2018
"""

from typing import Dict, Tuple
import math

from src.data.ntc2018_constants import NTC2018


class NTC2018Verifier:
    """Verificatore secondo NTC 2018 § 8.4.1 - Interventi locali"""

    # Limiti normativi per interventi locali (da modulo centralizzato)
    STIFFNESS_LIMIT = NTC2018.InterventiLocali.DELTA_K_MAX  # ±15% variazione rigidezza
    RESISTANCE_LIMIT = NTC2018.InterventiLocali.DELTA_V_MAX  # Max riduzione resistenza 20%

    def __init__(self):
        pass
        
    def verify_local_intervention(self, K_original: float, K_modified: float,
                                V_original: float, V_modified: float) -> Dict:
        """
        Verifica se l'intervento è classificabile come locale secondo NTC 2018
        
        Args:
            K_original: Rigidezza stato di fatto [kN/m]
            K_modified: Rigidezza stato di progetto [kN/m]
            V_original: Resistenza minima stato di fatto [kN]
            V_modified: Resistenza minima stato di progetto [kN]
            
        Returns:
            Dict con risultati verifica
        """
        # Calcola variazioni
        delta_K = abs(K_modified - K_original) / K_original if K_original > 0 else 0
        
        # CORREZIONE: Calcola sempre la variazione percentuale di resistenza
        # Positiva se aumenta, negativa se diminuisce
        if V_original > 0:
            delta_V_percent = ((V_modified - V_original) / V_original) * 100
        else:
            delta_V_percent = 0
            
        # Per la verifica normativa, consideriamo solo le riduzioni
        if V_modified < V_original:
            delta_V_check = (V_original - V_modified) / V_original if V_original > 0 else 0
        else:
            delta_V_check = 0  # Aumento di resistenza è sempre accettabile per la verifica
            
        # Verifiche
        stiffness_ok = delta_K <= self.STIFFNESS_LIMIT
        # RESISTANCE_LIMIT è negativo (-0.2 = -20%), quindi usiamo il valore assoluto
        resistance_ok = delta_V_check <= abs(self.RESISTANCE_LIMIT)
        
        # L'intervento è locale se entrambe le verifiche sono soddisfatte
        is_local = stiffness_ok and resistance_ok
        
        return {
            'is_local': is_local,
            'stiffness_variation': delta_K * 100,  # % (sempre positiva)
            'stiffness_variation_limit': self.STIFFNESS_LIMIT * 100,  # %
            'resistance_variation': delta_V_percent,  # % (può essere positiva o negativa)
            'resistance_variation_for_check': delta_V_check * 100,  # % (solo per verifica)
            'resistance_variation_limit': self.RESISTANCE_LIMIT * 100,  # %
            'stiffness_ok': stiffness_ok,
            'resistance_ok': resistance_ok,
            'stiffness_ratio': K_modified / K_original if K_original > 0 else 1,
            'resistance_ratio': V_modified / V_original if V_original > 0 else 1
        }
        
    def verify_opening_limits(self, wall_data: Dict, openings: list) -> Dict:
        """
        Verifica i limiti geometrici delle aperture
        
        Returns:
            Dict con risultati verifiche geometriche
        """
        L_wall = wall_data['length'] / 100  # m
        h_wall = wall_data['height'] / 100  # m
        
        # Area totale muro
        A_wall = L_wall * h_wall
        
        # Area totale aperture
        A_openings = 0
        for opening in openings:
            A_openings += (opening['width'] / 100) * (opening['height'] / 100)
            
        # Percentuale di foratura
        opening_ratio = A_openings / A_wall if A_wall > 0 else 0
        
        # Verifica maschi murari minimi (da NTC2018)
        maschi_ok = True
        min_maschio = NTC2018.InterventiLocali.MASCHIO_MIN_WIDTH  # m - larghezza minima maschio murario
        
        if openings:
            # Ordina aperture
            sorted_openings = sorted(openings, key=lambda o: o['x'])
            
            # Verifica maschio iniziale
            if sorted_openings[0]['x'] / 100 < min_maschio:
                maschi_ok = False
                
            # Verifica maschi intermedi
            for i in range(len(sorted_openings) - 1):
                x1 = (sorted_openings[i]['x'] + sorted_openings[i]['width']) / 100
                x2 = sorted_openings[i + 1]['x'] / 100
                if x2 - x1 < min_maschio:
                    maschi_ok = False
                    
            # Verifica maschio finale
            last = sorted_openings[-1]
            if (L_wall - (last['x'] + last['width']) / 100) < min_maschio:
                maschi_ok = False
                
        return {
            'opening_ratio': opening_ratio * 100,  # %
            'opening_ratio_ok': opening_ratio <= NTC2018.InterventiLocali.FORATURA_MAX,  # Max 40% foratura
            'min_maschio_ok': maschi_ok,
            'min_maschio_width': min_maschio * 100  # cm
        }
        
    def calculate_safety_factors(self, V_design: float, V_demand: float,
                               K_provided: float, K_required: float) -> Dict:
        """
        Calcola i coefficienti di sicurezza
        
        Args:
            V_design: Resistenza di progetto [kN]
            V_demand: Domanda (azione sismica) [kN]
            K_provided: Rigidezza fornita [kN/m]
            K_required: Rigidezza richiesta [kN/m]
            
        Returns:
            Dict con coefficienti di sicurezza
        """
        # Coefficiente di sicurezza sulla resistenza
        if V_demand > 0:
            safety_resistance = V_design / V_demand
        else:
            safety_resistance = float('inf')
            
        # Coefficiente di sicurezza sulla rigidezza
        if K_required > 0:
            safety_stiffness = K_provided / K_required
        else:
            safety_stiffness = float('inf')
            
        return {
            'safety_resistance': safety_resistance,
            'safety_stiffness': safety_stiffness,
            'global_safety': min(safety_resistance, safety_stiffness),
            'is_safe': safety_resistance >= 1.0 and safety_stiffness >= 1.0
        }
        
    def get_verification_summary(self, results: Dict) -> str:
        """
        Genera un riepilogo testuale delle verifiche
        
        Args:
            results: Dizionario con tutti i risultati delle verifiche
            
        Returns:
            Stringa con riepilogo verifiche
        """
        summary = []
        
        # Verifica principale
        if results.get('is_local'):
            summary.append("✓ L'INTERVENTO È CLASSIFICABILE COME LOCALE secondo NTC 2018 § 8.4.1")
        else:
            summary.append("✗ L'INTERVENTO NON È CLASSIFICABILE COME LOCALE")
            
        summary.append("")
        
        # Dettagli verifiche
        summary.append("VERIFICHE DI RIGIDEZZA:")
        if results.get('stiffness_ok'):
            summary.append(f"✓ Variazione rigidezza: {results['stiffness_variation']:.1f}% "
                         f"(limite: ±{results['stiffness_variation_limit']:.0f}%)")
        else:
            summary.append(f"✗ Variazione rigidezza: {results['stiffness_variation']:.1f}% "
                         f"SUPERA il limite di ±{results['stiffness_variation_limit']:.0f}%")
                         
        summary.append("")
        summary.append("VERIFICHE DI RESISTENZA:")
        
        # Mostra la variazione effettiva (positiva o negativa)
        res_var = results.get('resistance_variation', 0)
        if res_var >= 0:
            summary.append(f"✓ Incremento resistenza: +{res_var:.1f}%")
        else:
            summary.append(f"Riduzione resistenza: {res_var:.1f}%")
            
        # Verifica normativa
        if results.get('resistance_ok'):
            if res_var < 0:
                summary.append(f"✓ Riduzione accettabile (limite: -{results['resistance_variation_limit']:.0f}%)")
            else:
                summary.append(f"✓ Incremento sempre accettabile per interventi locali")
        else:
            summary.append(f"✗ Riduzione resistenza SUPERA il limite del {results['resistance_variation_limit']:.0f}%")
                         
        # Raccomandazioni
        if not results.get('is_local'):
            summary.append("")
            summary.append("RACCOMANDAZIONI:")
            
            if not results.get('stiffness_ok'):
                summary.append("• Aumentare la rigidezza delle cerchiature (profili maggiori)")
                summary.append("• Ridurre il numero o le dimensioni delle aperture")
                
            if not results.get('resistance_ok'):
                summary.append("• Limitare le aperture ai soli maschi murari secondari")
                summary.append("• Prevedere rinforzi aggiuntivi (FRP, intonaco armato)")
                
            summary.append("")
            summary.append("In alternativa, classificare l'intervento come MIGLIORAMENTO "
                         "o ADEGUAMENTO SISMICO con le relative verifiche globali.")
                         
        return "\n".join(summary)