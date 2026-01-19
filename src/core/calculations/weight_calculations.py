"""
Modulo per calcoli che utilizzano il peso specifico della muratura
Arch. Michelangelo Bartolotta
"""

from typing import Dict, List, Optional
import math
from PyQt5.QtWidgets import QGroupBox, QLabel, QFormLayout
from PyQt5.QtCore import Qt

class WeightCalculations:
    """Calcoli relativi al peso proprio e carichi gravitazionali"""
    
    def __init__(self):
        self.g = 9.81  # Accelerazione di gravità m/s²
        
    def calculate_wall_weight(self, wall_data: Dict, masonry_data: Dict, 
                            openings: Optional[List[Dict]] = None) -> Dict:
        """
        Calcola il peso proprio del muro
        
        Args:
            wall_data: Dati geometrici del muro
            masonry_data: Dati del materiale muratura
            openings: Lista aperture (opzionale)
            
        Returns:
            Dict con peso totale, peso per metro lineare, baricentro
        """
        # Dimensioni muro
        L = wall_data['length'] / 100  # cm -> m
        h = wall_data['height'] / 100  # cm -> m
        t = wall_data['thickness'] / 100  # cm -> m
        
        # Peso specifico
        gamma = masonry_data.get('gamma', masonry_data.get('w', 18.0))  # kN/m³
        
        # Volume lordo
        V_lordo = L * h * t  # m³
        
        # Sottrai volume aperture
        V_aperture = 0
        momento_statico_x = 0
        momento_statico_y = 0
        
        if openings:
            for opening in openings:
                # Considera solo aperture passanti (non nicchie)
                if not opening.get('niche_data', {}).get('is_niche', False):
                    # Se è una chiusura, considera il peso del materiale di chiusura
                    if opening.get('closure_data'):
                        closure = opening['closure_data']
                        # Peso specifico materiale chiusura (valori tipici)
                        gamma_closure = self._get_closure_weight(closure['material'])
                        t_closure = closure.get('thickness', 12) / 100  # cm -> m
                        
                        # Volume chiusura
                        V_closure = (opening['width'] / 100) * (opening['height'] / 100) * t_closure
                        
                        # Aggiungi al peso totale invece di sottrarre
                        V_aperture -= V_closure * (1 - gamma_closure / gamma)
                    else:
                        # Apertura normale - sottrai volume
                        V_opening = (opening['width'] / 100) * (opening['height'] / 100) * t
                        V_aperture += V_opening
                        
                        # Momento statico per baricentro
                        x_opening = opening['x'] / 100 + opening['width'] / 200
                        y_opening = opening['y'] / 100 + opening['height'] / 200
                        momento_statico_x += V_opening * x_opening * gamma
                        momento_statico_y += V_opening * y_opening * gamma
                        
                # Per nicchie, considera la riduzione di volume
                elif opening.get('niche_data'):
                    niche = opening['niche_data']
                    depth = niche.get('depth', 15) / 100  # cm -> m
                    
                    # Volume nicchia
                    V_niche = (opening['width'] / 100) * (opening['height'] / 100) * depth
                    V_aperture += V_niche
                    
        # Volume netto
        V_netto = V_lordo - V_aperture
        
        # Peso totale
        W_totale = V_netto * gamma  # kN
        
        # Peso per metro lineare (utile per fondazioni)
        W_lineare = W_totale / L  # kN/m
        
        # Baricentro del peso
        # Muro pieno
        momento_x_pieno = V_lordo * gamma * L / 2
        momento_y_pieno = V_lordo * gamma * h / 2
        
        # Sottrai contributo aperture
        momento_x_totale = momento_x_pieno - momento_statico_x
        momento_y_totale = momento_y_pieno - momento_statico_y
        
        if W_totale > 0:
            x_g = momento_x_totale / W_totale
            y_g = momento_y_totale / W_totale
        else:
            x_g = L / 2
            y_g = h / 2
            
        return {
            'peso_totale': W_totale,  # kN
            'peso_lineare': W_lineare,  # kN/m
            'volume_lordo': V_lordo,  # m³
            'volume_netto': V_netto,  # m³
            'baricentro': {
                'x': x_g,  # m da sinistra
                'y': y_g   # m dal basso
            },
            'gamma': gamma  # kN/m³
        }
        
    def calculate_seismic_mass(self, wall_data: Dict, masonry_data: Dict,
                             additional_loads: Optional[Dict] = None) -> float:
        """
        Calcola la massa sismica del muro per analisi dinamica
        
        Args:
            wall_data: Dati geometrici
            masonry_data: Dati materiale
            additional_loads: Carichi aggiuntivi (solaio, copertura)
            
        Returns:
            Massa sismica in tonnellate
        """
        # Peso proprio muro
        weight_data = self.calculate_wall_weight(wall_data, masonry_data)
        W_muro = weight_data['peso_totale']
        
        # Carichi permanenti aggiuntivi
        G2 = 0
        if additional_loads:
            # Carico da solaio (se il muro lo porta)
            if additional_loads.get('solaio'):
                area_influenza = additional_loads['solaio'].get('area_influenza', 0)  # m²
                g2_solaio = additional_loads['solaio'].get('g2', 2.0)  # kN/m²
                G2 += area_influenza * g2_solaio
                
            # Carico da copertura
            if additional_loads.get('copertura'):
                area_influenza = additional_loads['copertura'].get('area_influenza', 0)  # m²
                g2_copertura = additional_loads['copertura'].get('g2', 1.5)  # kN/m²
                G2 += area_influenza * g2_copertura
                
        # Carichi variabili (con coefficiente ψ2)
        Q = 0
        if additional_loads:
            psi2 = additional_loads.get('psi2', 0.3)  # Coefficiente combinazione sismica
            
            if additional_loads.get('solaio'):
                area_influenza = additional_loads['solaio'].get('area_influenza', 0)
                q_solaio = additional_loads['solaio'].get('q', 2.0)  # kN/m²
                Q += psi2 * area_influenza * q_solaio
                
        # Peso sismico totale
        W_sismico = W_muro + G2 + Q  # kN
        
        # Converti in massa (tonnellate)
        massa_sismica = W_sismico / self.g  # kN / (m/s²) = ton
        
        return massa_sismica
        
    def calculate_foundation_loads(self, wall_data: Dict, masonry_data: Dict,
                                 vertical_load: float = 0, 
                                 eccentricity: float = 0) -> Dict:
        """
        Calcola i carichi in fondazione
        
        Args:
            wall_data: Dati muro
            masonry_data: Dati materiale
            vertical_load: Carico verticale aggiuntivo [kN]
            eccentricity: Eccentricità del carico [m]
            
        Returns:
            Dict con pressioni in fondazione
        """
        # Peso proprio
        weight_data = self.calculate_wall_weight(wall_data, masonry_data)
        W = weight_data['peso_totale']
        
        # Carico totale
        N_totale = W + vertical_load  # kN
        
        # Momento per eccentricità
        M = N_totale * eccentricity  # kN·m
        
        # Larghezza muro (base)
        B = wall_data['thickness'] / 100  # m
        L = wall_data['length'] / 100  # m
        
        # Area base
        A = B * L  # m²
        
        # Modulo resistenza
        W_x = B * L**2 / 6  # m³
        
        # Pressioni estreme
        sigma_max = N_totale / A + abs(M) / W_x  # kN/m²
        sigma_min = N_totale / A - abs(M) / W_x  # kN/m²
        
        # Verifica se la sezione è parzializzata
        if sigma_min < 0:
            # Sezione parzializzata - ricalcola
            # Lunghezza compressa
            L_compressa = 3 * (L/2 - abs(eccentricity))
            
            if L_compressa > 0:
                sigma_max = 2 * N_totale / (B * L_compressa)
                sigma_min = 0
            else:
                # Eccentricità eccessiva
                sigma_max = float('inf')
                sigma_min = 0
                
        return {
            'N_totale': N_totale,  # kN
            'M_totale': M,  # kN·m
            'sigma_max': sigma_max,  # kN/m²
            'sigma_min': sigma_min,  # kN/m²
            'parzializzazione': sigma_min <= 0,
            'peso_proprio': W,  # kN
            'peso_esterno': vertical_load  # kN
        }
        
    def _get_closure_weight(self, material: str) -> float:
        """
        Restituisce peso specifico tipico per materiali di chiusura
        
        Args:
            material: Tipo materiale chiusura
            
        Returns:
            Peso specifico in kN/m³
        """
        closure_weights = {
            'Mattoni pieni': 18.0,
            'Mattoni forati': 12.0,
            'Blocchi cls': 16.0,
            'Blocchi laterizio': 11.0,
            'Cartongesso': 8.0,
            'Vetrocemento': 20.0,
            'Altro': 15.0  # Valore medio
        }
        
        return closure_weights.get(material, 15.0)
        
    def calculate_overturning_moment(self, wall_data: Dict, masonry_data: Dict,
                                   horizontal_force: float, 
                                   force_height: float) -> Dict:
        """
        Calcola momento ribaltante e verifica stabilità
        
        Args:
            wall_data: Dati muro
            masonry_data: Dati materiale  
            horizontal_force: Forza orizzontale [kN]
            force_height: Altezza applicazione forza [m]
            
        Returns:
            Dict con momenti e fattore sicurezza
        """
        # Peso muro
        weight_data = self.calculate_wall_weight(wall_data, masonry_data)
        W = weight_data['peso_totale']
        x_g = weight_data['baricentro']['x']
        
        # Larghezza muro
        B = wall_data['thickness'] / 100  # m
        
        # Momento ribaltante (rispetto allo spigolo)
        M_ribaltante = horizontal_force * force_height  # kN·m
        
        # Momento stabilizzante (peso proprio)
        # Braccio dal punto di ribaltamento (spigolo compresso)
        braccio_stabilizzante = B / 2  # Per sezione rettangolare
        M_stabilizzante = W * braccio_stabilizzante  # kN·m
        
        # Fattore di sicurezza
        if M_ribaltante > 0:
            FS_ribaltamento = M_stabilizzante / M_ribaltante
        else:
            FS_ribaltamento = float('inf')
            
        return {
            'M_ribaltante': M_ribaltante,  # kN·m
            'M_stabilizzante': M_stabilizzante,  # kN·m
            'FS_ribaltamento': FS_ribaltamento,
            'verificato': FS_ribaltamento >= 1.5  # Fattore sicurezza minimo
        }
        

class SeismicWeightWidget(QGroupBox):
    """Widget per visualizzare calcoli peso sismico"""
    
    def __init__(self):
        super().__init__("Calcolo Masse Sismiche")
        self.weight_calc = WeightCalculations()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        # Peso proprio muro
        self.peso_muro_label = QLabel("-")
        self.peso_muro_label.setStyleSheet("font-weight: bold;")
        layout.addRow("Peso proprio muro:", self.peso_muro_label)
        
        # Volume
        self.volume_label = QLabel("-")
        layout.addRow("Volume netto:", self.volume_label)
        
        # Baricentro
        self.baricentro_label = QLabel("-")
        layout.addRow("Baricentro:", self.baricentro_label)
        
        # Massa sismica
        self.massa_sismica_label = QLabel("-")
        self.massa_sismica_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addRow("Massa sismica:", self.massa_sismica_label)
        
        self.setLayout(layout)
        
    def update_calculations(self, wall_data: Dict, masonry_data: Dict, 
                          openings: Optional[List[Dict]] = None):
        """Aggiorna i calcoli"""
        if not wall_data or not masonry_data:
            return
            
        # Calcola peso
        weight_data = self.weight_calc.calculate_wall_weight(
            wall_data, masonry_data, openings
        )
        
        # Aggiorna etichette
        self.peso_muro_label.setText(f"{weight_data['peso_totale']:.1f} kN")
        self.volume_label.setText(f"{weight_data['volume_netto']:.2f} m³")
        self.baricentro_label.setText(
            f"x={weight_data['baricentro']['x']:.2f}m, "
            f"y={weight_data['baricentro']['y']:.2f}m"
        )
        
        # Massa sismica
        massa = self.weight_calc.calculate_seismic_mass(wall_data, masonry_data)
        self.massa_sismica_label.setText(f"{massa:.2f} ton")