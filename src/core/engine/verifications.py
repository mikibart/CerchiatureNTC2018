"""
Verifiche secondo NTC 2018 § 8.4.1
Verifica se l'intervento può essere classificato come locale
Arch. Michelangelo Bartolotta
"""

from typing import Dict, Tuple
import math


class NTC2018Verifier:
    """Verificatore secondo NTC 2018 § 8.4.1 - Interventi locali"""
    
    # Limiti normativi per interventi locali
    STIFFNESS_LIMIT = 0.15  # ±15% variazione rigidezza
    RESISTANCE_LIMIT = 0.20  # Max riduzione resistenza 20%
    
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
        resistance_ok = delta_V_check <= self.RESISTANCE_LIMIT
        
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
        
        # Verifica maschi murari minimi
        maschi_ok = True
        min_maschio = 0.8  # m - larghezza minima maschio murario
        
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
            'opening_ratio_ok': opening_ratio <= 0.4,  # Max 40% foratura
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

    # =========================================================================
    # VERIFICHE PIATTABANDA E PIEDRITTI (da Calcolus-CERCHIATURA)
    # =========================================================================

    def verify_lintel(self, opening_data: Dict, profile_data: Dict,
                     masonry_data: Dict, loads: Dict = None) -> Dict:
        """
        Verifica piattabanda (architrave) secondo NTC 2018.

        La piattabanda è l'elemento orizzontale superiore che deve resistere:
        - Peso proprio del muro soprastante
        - Carichi applicati
        - Azioni sismiche

        Args:
            opening_data: Dati apertura (width, height, x, y)
            profile_data: Dati profilo (tipo, dimensioni, proprietà)
            masonry_data: Dati muratura (peso, spessore)
            loads: Carichi aggiuntivi opzionali

        Returns:
            Dict con risultati verifica
        """
        # Estrai geometria
        L_opening = opening_data.get('width', 120) / 100  # cm -> m
        H_wall = opening_data.get('wall_height', 300) / 100  # cm -> m
        H_opening = opening_data.get('height', 220) / 100  # cm -> m
        Y_opening = opening_data.get('y', 0) / 100  # cm -> m
        t_wall = masonry_data.get('thickness', 30) / 100  # cm -> m

        # Altezza muro sopra l'apertura
        H_above = H_wall - Y_opening - H_opening
        if H_above < 0:
            H_above = 0

        # Peso proprio muratura sopra (triangolo di scarico o rettangolo)
        gamma_mur = masonry_data.get('weight', 18)  # kN/m³
        # Carico distribuito sulla piattabanda
        # Schema semplificato: triangolo di carico (45°) fino a min(L_opening, H_above)
        h_triangle = min(L_opening, H_above)
        q_mur = gamma_mur * t_wall * h_triangle / 2  # kN/m

        # Carichi aggiuntivi
        q_add = 0
        if loads:
            q_add = loads.get('distributed_load', 0)  # kN/m
            P_point = loads.get('point_load', 0)  # kN

        q_total = q_mur + q_add

        # Luce netta (luce + 2 * appoggio)
        appoggio = 0.15  # m - appoggio sui maschi
        L_eff = L_opening + 2 * appoggio

        # Momento sollecitante (schema appoggio-appoggio)
        M_Ed = q_total * L_eff**2 / 8  # kNm

        # Taglio sollecitante
        V_Ed = q_total * L_eff / 2  # kN

        # Proprietà profilo
        Wpl = profile_data.get('Wpl', 100)  # cm³ - modulo plastico
        A_shear = profile_data.get('A_shear', 10)  # cm² - area di taglio
        fy = profile_data.get('fy', 235)  # MPa - tensione snervamento

        # Coefficiente di sicurezza acciaio
        gamma_M0 = 1.05

        # Resistenze
        M_Rd = Wpl * (fy / gamma_M0) / 1000  # kNm (Wpl in cm³, fy in MPa)
        V_Rd = A_shear * (fy / (math.sqrt(3) * gamma_M0)) / 10  # kN

        # Verifiche
        flex_ratio = M_Ed / M_Rd if M_Rd > 0 else float('inf')
        shear_ratio = V_Ed / V_Rd if V_Rd > 0 else float('inf')

        flex_ok = flex_ratio <= 1.0
        shear_ok = shear_ratio <= 1.0

        return {
            'element': 'piattabanda',
            'L_eff': L_eff * 100,  # cm
            'q_mur': q_mur,
            'q_total': q_total,
            'M_Ed': M_Ed,
            'V_Ed': V_Ed,
            'M_Rd': M_Rd,
            'V_Rd': V_Rd,
            'flex_ratio': flex_ratio,
            'shear_ratio': shear_ratio,
            'flex_ok': flex_ok,
            'shear_ok': shear_ok,
            'verified': flex_ok and shear_ok
        }

    def verify_jamb(self, opening_data: Dict, profile_data: Dict,
                   masonry_data: Dict, loads: Dict = None,
                   seismic_force: float = 0) -> Dict:
        """
        Verifica piedritto (montante) secondo NTC 2018.

        Il piedritto è l'elemento verticale laterale che deve resistere:
        - Compressione dovuta al peso della muratura
        - Flessione dovuta alle azioni orizzontali
        - Instabilità (verifica a compressione)

        Args:
            opening_data: Dati apertura
            profile_data: Dati profilo
            masonry_data: Dati muratura
            loads: Carichi aggiuntivi
            seismic_force: Forza sismica orizzontale [kN]

        Returns:
            Dict con risultati verifica
        """
        # Geometria
        H_opening = opening_data.get('height', 220) / 100  # cm -> m
        t_wall = masonry_data.get('thickness', 30) / 100  # cm -> m
        L_opening = opening_data.get('width', 120) / 100  # cm -> m

        # Proprietà profilo
        A = profile_data.get('A', 20)  # cm² - area sezione
        Ix = profile_data.get('Ix', 500)  # cm⁴ - momento inerzia
        Wpl = profile_data.get('Wpl', 50)  # cm³ - modulo plastico
        fy = profile_data.get('fy', 235)  # MPa
        E_steel = 210000  # MPa

        gamma_M0 = 1.05
        gamma_M1 = 1.05  # Per instabilità

        # Carico verticale dal peso muratura
        gamma_mur = masonry_data.get('weight', 18)  # kN/m³
        H_above = opening_data.get('wall_height', 300) / 100 - opening_data.get('height', 220) / 100 - opening_data.get('y', 0) / 100
        if H_above < 0:
            H_above = 0

        # Larghezza tributaria (metà larghezza apertura)
        L_trib = L_opening / 2 + 0.15  # m

        # Compressione sul piedritto
        N_Ed = gamma_mur * t_wall * H_above * L_trib  # kN

        # Momento da forza sismica (se applicata)
        # Schema a mensola: M = F × h / 2 (ripartito sui 2 piedritti)
        M_Ed = (seismic_force / 2) * H_opening / 2 if seismic_force > 0 else 0  # kNm

        # Resistenze
        N_Rd = A * (fy / gamma_M0) / 10  # kN
        M_Rd = Wpl * (fy / gamma_M0) / 1000  # kNm

        # Verifica instabilità (snellezza)
        L_0 = H_opening  # Lunghezza libera di inflessione
        i_min = math.sqrt(Ix / A)  # raggio d'inerzia (cm)
        lambda_slender = (L_0 * 100) / i_min  # snellezza

        # Snellezza limite (Eulero)
        lambda_1 = math.pi * math.sqrt(E_steel / fy)  # circa 93.9 per S235
        lambda_rel = lambda_slender / lambda_1  # snellezza relativa

        # Curva di instabilità (curva b per profili laminati H)
        alpha = 0.34  # curva b
        phi = 0.5 * (1 + alpha * (lambda_rel - 0.2) + lambda_rel**2)
        chi = 1 / (phi + math.sqrt(phi**2 - lambda_rel**2)) if phi**2 >= lambda_rel**2 else 0.5
        chi = min(1.0, max(0.1, chi))

        # Resistenza ridotta per instabilità
        N_b_Rd = chi * A * (fy / gamma_M1) / 10  # kN

        # Verifiche
        compr_ratio = N_Ed / N_Rd if N_Rd > 0 else 0
        buckling_ratio = N_Ed / N_b_Rd if N_b_Rd > 0 else 0
        flex_ratio = M_Ed / M_Rd if M_Rd > 0 else 0

        # Verifica combinata presso-flessione (formula semplificata)
        combined_ratio = compr_ratio + flex_ratio

        compr_ok = compr_ratio <= 1.0
        buckling_ok = buckling_ratio <= 1.0
        flex_ok = flex_ratio <= 1.0
        combined_ok = combined_ratio <= 1.0

        return {
            'element': 'piedritto',
            'H_eff': H_opening * 100,  # cm
            'N_Ed': N_Ed,
            'M_Ed': M_Ed,
            'N_Rd': N_Rd,
            'N_b_Rd': N_b_Rd,
            'M_Rd': M_Rd,
            'lambda_slender': lambda_slender,
            'lambda_rel': lambda_rel,
            'chi': chi,
            'compr_ratio': compr_ratio,
            'buckling_ratio': buckling_ratio,
            'flex_ratio': flex_ratio,
            'combined_ratio': combined_ratio,
            'compr_ok': compr_ok,
            'buckling_ok': buckling_ok,
            'flex_ok': flex_ok,
            'combined_ok': combined_ok,
            'verified': compr_ok and buckling_ok and flex_ok and combined_ok
        }

    def verify_frame(self, opening_data: Dict, lintel_profile: Dict,
                    jamb_profile: Dict, masonry_data: Dict,
                    loads: Dict = None, seismic_force: float = 0) -> Dict:
        """
        Verifica completa telaio cerchiatura (piattabanda + piedritti).

        Args:
            opening_data: Dati apertura
            lintel_profile: Profilo piattabanda
            jamb_profile: Profilo piedritti
            masonry_data: Dati muratura
            loads: Carichi aggiuntivi
            seismic_force: Forza sismica [kN]

        Returns:
            Dict con risultati verifiche complete
        """
        # Verifica piattabanda
        lintel_result = self.verify_lintel(opening_data, lintel_profile,
                                          masonry_data, loads)

        # Verifica piedritti
        jamb_result = self.verify_jamb(opening_data, jamb_profile,
                                      masonry_data, loads, seismic_force)

        # Risultato globale
        all_ok = lintel_result['verified'] and jamb_result['verified']

        return {
            'lintel': lintel_result,
            'jamb': jamb_result,
            'verified': all_ok,
            'summary': self._generate_frame_summary(lintel_result, jamb_result)
        }

    def _generate_frame_summary(self, lintel: Dict, jamb: Dict) -> str:
        """Genera riepilogo testuale verifiche telaio"""
        lines = []
        lines.append("=" * 50)
        lines.append("VERIFICA TELAIO CERCHIATURA")
        lines.append("=" * 50)

        # Piattabanda
        lines.append("\nPIATTABANDA:")
        lines.append(f"  Luce efficace: {lintel['L_eff']:.0f} cm")
        lines.append(f"  Carico distribuito: q = {lintel['q_total']:.2f} kN/m")
        lines.append(f"  Momento: M_Ed = {lintel['M_Ed']:.2f} kNm")
        lines.append(f"  Taglio: V_Ed = {lintel['V_Ed']:.2f} kN")
        lines.append(f"  Verifica flessione: {lintel['flex_ratio']:.2f} {'✓' if lintel['flex_ok'] else '✗'}")
        lines.append(f"  Verifica taglio: {lintel['shear_ratio']:.2f} {'✓' if lintel['shear_ok'] else '✗'}")

        # Piedritti
        lines.append("\nPIEDRITTI:")
        lines.append(f"  Altezza efficace: {jamb['H_eff']:.0f} cm")
        lines.append(f"  Compressione: N_Ed = {jamb['N_Ed']:.2f} kN")
        lines.append(f"  Snellezza: λ = {jamb['lambda_slender']:.1f}")
        lines.append(f"  Fattore χ: {jamb['chi']:.3f}")
        lines.append(f"  Verifica compressione: {jamb['compr_ratio']:.2f} {'✓' if jamb['compr_ok'] else '✗'}")
        lines.append(f"  Verifica instabilità: {jamb['buckling_ratio']:.2f} {'✓' if jamb['buckling_ok'] else '✗'}")
        if jamb['M_Ed'] > 0:
            lines.append(f"  Verifica flessione: {jamb['flex_ratio']:.2f} {'✓' if jamb['flex_ok'] else '✗'}")
            lines.append(f"  Verifica combinata: {jamb['combined_ratio']:.2f} {'✓' if jamb['combined_ok'] else '✗'}")

        # Esito globale
        lines.append("\n" + "=" * 50)
        if lintel['verified'] and jamb['verified']:
            lines.append("VERIFICA TELAIO: SODDISFATTA ✓")
        else:
            lines.append("VERIFICA TELAIO: NON SODDISFATTA ✗")
            lines.append("Aumentare le dimensioni dei profili")
        lines.append("=" * 50)

        return "\n".join(lines)