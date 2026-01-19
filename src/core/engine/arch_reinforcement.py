"""
Modulo per gestione rinforzi di aperture ad arco con calandratura
Supporta calcolo e configurazione di cerchiature curve
Arch. Michelangelo Bartolotta
REFACTORING: Costanti centralizzate in NTC2018

Posizione: src/core/engine/arch_reinforcement.py
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math
import logging
from typing import Dict, List, Optional, Tuple, Union

from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


class ArchReinforcementManager:
    """Gestisce il calcolo e la configurazione dei rinforzi per aperture ad arco."""
    
    # Database profili standard con altezze in mm
    PROFILE_DATABASE = {
        'HEA': {
            '100': 96, '120': 114, '140': 133, '160': 152, '180': 171,
            '200': 190, '220': 210, '240': 230, '260': 250, '280': 270,
            '300': 290, '320': 310, '340': 330, '360': 350
        },
        'HEB': {
            '100': 100, '120': 120, '140': 140, '160': 160, '180': 180,
            '200': 200, '220': 220, '240': 240, '260': 260, '280': 280,
            '300': 300, '320': 320, '340': 340, '360': 360
        },
        'IPE': {
            '80': 80, '100': 100, '120': 120, '140': 140, '160': 160,
            '180': 180, '200': 200, '220': 220, '240': 240, '270': 270,
            '300': 300, '330': 330, '360': 360
        }
    }
    
    @staticmethod
    def calculate_arch_length(opening_data: Dict) -> float:
        """
        Calcola la lunghezza sviluppata dell'arco.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.

        Returns:
            float: Lunghezza sviluppata in cm.
        """
        if opening_data.get('type') != 'Ad arco' or 'arch_data' not in opening_data:
            return 0
            
        arch_data = opening_data['arch_data']
        width = opening_data['width']
        arch_type = arch_data.get('arch_type', 'Tutto sesto')
        arch_rise = arch_data.get('arch_rise', 60)
        
        if arch_type == 'Tutto sesto':
            # Semicirconferenza
            radius = width / 2
            return math.pi * radius
            
        elif arch_type == 'Ribassato':
            # Arco di cerchio
            radius = (arch_rise**2 + (width/2)**2) / (2 * arch_rise)
            # Angolo sotteso
            theta = 2 * math.asin(width / (2 * radius))
            # Lunghezza arco
            return radius * theta
            
        elif arch_type == 'Rialzato (ogivale)':
            # Due archi che si intersecano
            radius = width * 0.75
            # Angolo per ogni arco
            theta = math.acos(width / (2 * radius))
            # Lunghezza totale (due archi)
            return 2 * radius * theta
            
        elif arch_type == 'Policentrico':
            # Arco policentrico - approssimazione
            # Usa formula approssimata di Ramanujan per ellisse
            a = width / 2  # semi-asse maggiore
            b = arch_rise  # semi-asse minore
            h = ((a - b)**2) / ((a + b)**2)
            perimeter = math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
            return perimeter / 2  # Solo metà superiore
            
        return 0
        
    @staticmethod
    def calculate_arch_radius(opening_data: Dict) -> float:
        """
        Calcola il raggio di curvatura dell'arco.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.

        Returns:
            float: Raggio di curvatura in cm.
        """
        if opening_data.get('type') != 'Ad arco' or 'arch_data' not in opening_data:
            return 0
            
        arch_data = opening_data['arch_data']
        width = opening_data['width']
        arch_type = arch_data.get('arch_type', 'Tutto sesto')
        arch_rise = arch_data.get('arch_rise', 60)
        
        if arch_type == 'Tutto sesto':
            return width / 2
            
        elif arch_type == 'Ribassato':
            return (arch_rise**2 + (width/2)**2) / (2 * arch_rise)
            
        elif arch_type == 'Rialzato (ogivale)':
            return width * 0.75
            
        elif arch_type == 'Policentrico':
            # Raggio medio approssimato
            return (width/2 + arch_rise) / 2
            
        return 0
        
    @staticmethod
    def get_reinforcement_types_for_arch(opening_data: Dict) -> List[str]:
        """
        Restituisce i tipi di rinforzo applicabili per un arco.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.

        Returns:
            List[str]: Lista dei tipi di rinforzo disponibili.
        """
        if opening_data.get('type') != 'Ad arco':
            return []
            
        return [
            "Telaio completo in acciaio con architrave calandrato",
            "Solo architrave calandrato in acciaio",
            "Telaio in C.A. con architrave curvo",
            "Solo architrave in C.A. curvo",
            "Rinforzo ad arco in acciaio (senza piedritti)",
            "Profilo calandrato che segue l'intradosso",
            "Doppio profilo calandrato (intradosso + estradosso)",
            "Profili segmentati saldati",
            "Nessun rinforzo"
        ]
        
    @staticmethod
    def check_bendability(profile_name: str, radius_cm: float, steel_grade: str = 'S235') -> Dict:
        """
        Verifica la calandrabilità di un profilo.

        Args:
            profile_name (str): Nome del profilo (es. "HEA 200").
            radius_cm (float): Raggio di curvatura in cm.
            steel_grade (str): Classe dell'acciaio.

        Returns:
            Dict: Risultati della verifica con chiavi:
                - bendable (bool): Se è calandrabile.
                - method (str): Metodo consigliato.
                - r_h_ratio (float): Rapporto raggio/altezza.
                - residual_stress (float): Tensioni residue [MPa].
                - warnings (List[str]): Lista avvisi.
        """
        result = {
            'bendable': False,
            'method': 'Non calandrabile',
            'r_h_ratio': 0,
            'residual_stress': 0,
            'warnings': []
        }
        
        # Estrai tipo e dimensione profilo
        try:
            parts = profile_name.split()
            profile_type = parts[0]
            profile_size = parts[1]
            
            # Ottieni altezza profilo in mm
            if profile_type in ArchReinforcementManager.PROFILE_DATABASE:
                h_mm = ArchReinforcementManager.PROFILE_DATABASE[profile_type].get(profile_size, 200)
            else:
                # Stima dall'etichetta
                h_mm = int(''.join(filter(str.isdigit, profile_size)))
        except:
            h_mm = 200  # Default
            result['warnings'].append("Impossibile determinare altezza profilo, uso default 200mm")
            
        # Converti in cm
        h_cm = h_mm / 10
        
        # Calcola rapporto r/h
        r_h = radius_cm / h_cm
        result['r_h_ratio'] = r_h
        
        # Verifica limiti calandratura (da NTC2018)
        if r_h < NTC2018.Calandratura.RH_CRITICO:
            result['bendable'] = False
            result['method'] = 'Non calandrabile - raggio troppo stretto'
            result['warnings'].append(f"Rapporto r/h = {r_h:.1f} < {NTC2018.Calandratura.RH_CRITICO} - Rischio rottura")

        elif r_h < NTC2018.Calandratura.RH_MIN_CALDO:
            result['bendable'] = True
            result['method'] = 'Calandratura a caldo obbligatoria'
            result['warnings'].append(f"Rapporto r/h = {r_h:.1f} < {NTC2018.Calandratura.RH_MIN_CALDO} - Solo calandratura a caldo")
            result['warnings'].append("Verificare disponibilità presso officina specializzata")

        elif r_h < NTC2018.Calandratura.RH_MIN_PRERISCALDO:
            result['bendable'] = True
            result['method'] = 'Calandratura a caldo consigliata'
            result['warnings'].append(f"Rapporto r/h = {r_h:.1f} < {NTC2018.Calandratura.RH_MIN_PRERISCALDO} - Preferibile a caldo")
            result['warnings'].append("Possibile a freddo con pre-riscaldo")

        elif r_h < NTC2018.Calandratura.RH_MIN_FREDDO:
            result['bendable'] = True
            result['method'] = 'Calandratura a freddo possibile'
            result['warnings'].append("Verificare capacità macchina calandratrice")

        else:
            result['bendable'] = True
            result['method'] = 'Calandratura a freddo standard'
            
        # Calcola tensioni residue (formula semplificata)
        E = NTC2018.Acciaio.E  # MPa - modulo elastico acciaio
        radius_m = radius_cm / 100
        h_m = h_mm / 1000

        # sigma = E * h / (2 * R)
        sigma_res = E * h_m / (2 * radius_m)
        result['residual_stress'] = sigma_res

        # Tensione di snervamento (da NTC2018)
        fy = NTC2018.Acciaio.get_fyk(steel_grade)
        
        # Verifica tensioni residue (limiti da NTC2018)
        stress_ratio = sigma_res / fy

        if stress_ratio > NTC2018.Calandratura.STRESS_RATIO_CRITICO:
            result['warnings'].append(f"ATTENZIONE: Tensioni residue molto elevate ({stress_ratio*100:.0f}% fy)")
            result['warnings'].append("Rischio di rottura durante calandratura")
            result['bendable'] = False

        elif stress_ratio > NTC2018.Calandratura.STRESS_RATIO_ALTO:
            result['warnings'].append(f"Tensioni residue elevate ({stress_ratio*100:.0f}% fy)")
            result['warnings'].append("Necessario trattamento termico post-calandratura")

        elif stress_ratio > NTC2018.Calandratura.STRESS_RATIO_MODERATO:
            result['warnings'].append(f"Tensioni residue moderate ({stress_ratio*100:.0f}% fy)")
            result['warnings'].append("Verificare effetti su resistenza a fatica")
            
        return result
        
    @staticmethod
    def calculate_bending_segments(arc_length_cm: float, max_segment_length: float = 100) -> int:
        """
        Calcola numero di segmenti per discretizzazione arco.

        Args:
            arc_length_cm (float): Lunghezza sviluppata arco in cm.
            max_segment_length (float): Lunghezza massima segmento in cm.

        Returns:
            int: Numero di segmenti consigliato.
        """
        n_segments = max(3, int(math.ceil(arc_length_cm / max_segment_length)))
        
        # Assicura numero dispari per simmetria
        if n_segments % 2 == 0:
            n_segments += 1
            
        return n_segments
        
    @staticmethod
    def get_arch_points(opening_data: Dict, n_points: int = 30, offset: float = 0) -> List[Tuple[float, float]]:
        """
        Genera punti per disegnare l'arco.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.
            n_points (int): Numero di punti.
            offset (float): Offset radiale (positivo = esterno, negativo = interno).

        Returns:
            List[Tuple[float, float]]: Lista di tuple (x, y) in coordinate muro.
        """
        points = []
        
        if opening_data.get('type') != 'Ad arco' or 'arch_data' not in opening_data:
            return points
            
        arch_data = opening_data['arch_data']
        x = opening_data['x']
        y = opening_data['y']
        width = opening_data['width']
        arch_type = arch_data.get('arch_type', 'Tutto sesto')
        arch_rise = arch_data.get('arch_rise', 60)
        impost_height = arch_data.get('impost_height', 180)
        
        if arch_type == 'Tutto sesto':
            radius = width / 2 + offset
            center_x = x + width / 2
            center_y = y + impost_height
            
            for i in range(n_points + 1):
                angle = math.pi * (1 - i / n_points)
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append((px, py))
                
        elif arch_type == 'Ribassato':
            radius = (arch_rise**2 + (width/2)**2) / (2 * arch_rise) + offset
            center_x = x + width / 2
            center_y = y + impost_height + arch_rise - radius
            
            half_angle = math.asin(width / (2 * (radius - offset)))
            
            for i in range(n_points + 1):
                angle = math.pi - half_angle + (2 * half_angle * i / n_points)
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append((px, py))
                
        elif arch_type == 'Rialzato (ogivale)':
            radius = width * 0.75 + offset
            
            # Prima metà (arco sinistro)
            center_x1 = x
            center_y1 = y + impost_height
            max_angle = math.acos(width / (2 * (radius - offset)))
            
            for i in range(n_points // 2 + 1):
                angle = max_angle * i / (n_points // 2)
                px = center_x1 + radius * math.cos(angle)
                py = center_y1 + radius * math.sin(angle)
                points.append((px, py))
                
            # Seconda metà (arco destro)
            center_x2 = x + width
            center_y2 = y + impost_height
            
            for i in range(n_points // 2, -1, -1):
                angle = math.pi - max_angle * i / (n_points // 2)
                px = center_x2 + radius * math.cos(angle)
                py = center_y2 + radius * math.sin(angle)
                if i < n_points // 2:  # Evita duplicazione punto centrale
                    points.append((px, py))
                    
        return points
        
    @staticmethod
    def calculate_material_quantity(opening_data: Dict, profile_name: str, n_profiles: int = 1) -> Dict:
        """
        Calcola quantità di materiale necessario.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.
            profile_name (str): Nome del profilo.
            n_profiles (int): Numero di profili.

        Returns:
            Dict: Quantità materiali con chiavi:
                - steel_length_m (float): Lunghezza totale acciaio in metri.
                - weight_kg (float): Peso stimato in kg.
                - welding_length_m (float): Lunghezza saldature in metri.
        """
        result = {
            'steel_length_m': 0,
            'weight_kg': 0,
            'welding_length_m': 0
        }
        
        # Lunghezza sviluppata arco
        arc_length = ArchReinforcementManager.calculate_arch_length(opening_data)
        
        # Aggiungi extra per tagli e sfridi (5%)
        arc_length_with_waste = arc_length * 1.05
        
        # Lunghezza totale in metri
        result['steel_length_m'] = (arc_length_with_waste / 100) * n_profiles
        
        # Stima peso (kg/m approssimato per profili comuni)
        weight_per_meter = {
            'HEA 100': 16.7, 'HEA 120': 19.9, 'HEA 140': 24.7, 'HEA 160': 30.4,
            'HEA 180': 35.5, 'HEA 200': 42.3, 'HEA 220': 50.5, 'HEA 240': 60.3,
            'HEB 100': 20.4, 'HEB 120': 26.7, 'HEB 140': 33.7, 'HEB 160': 42.6,
            'HEB 180': 51.2, 'HEB 200': 61.3, 'HEB 220': 71.5, 'HEB 240': 83.2,
            'IPE 100': 8.1, 'IPE 120': 10.4, 'IPE 140': 12.9, 'IPE 160': 15.8,
            'IPE 180': 18.8, 'IPE 200': 22.4, 'IPE 220': 26.2, 'IPE 240': 30.7
        }
        
        kg_per_m = weight_per_meter.get(profile_name, 40)  # Default 40 kg/m
        result['weight_kg'] = result['steel_length_m'] * kg_per_m
        
        # Lunghezza saldature (se profili multipli)
        if n_profiles > 1:
            # Calastrelli ogni 60cm
            n_connections = int(arc_length / 60)
            # Lunghezza saldatura per calastrello (4 cordoni da 8cm)
            result['welding_length_m'] = (n_connections * 4 * 0.08)
            
        return result
        
    @staticmethod
    def generate_bending_report(opening_data: Dict, reinforcement_data: Dict) -> str:
        """
        Genera report dettagliato per officina di calandratura.

        Args:
            opening_data (Dict): Dizionario con i dati dell'apertura.
            reinforcement_data (Dict): Dizionario con i dati del rinforzo.

        Returns:
            str: Report formattato.
        """
        report = []
        report.append("SCHEDA CALANDRATURA PROFILI")
        report.append("=" * 50)
        report.append("")
        
        # Dati generali
        report.append("DATI APERTURA:")
        report.append(f"Tipo: {opening_data.get('type', 'N.D.')}")
        report.append(f"Dimensioni: {opening_data.get('width', 0)} x {opening_data.get('height', 0)} cm")
        
        if 'arch_data' in opening_data:
            arch_data = opening_data['arch_data']
            report.append(f"Tipo arco: {arch_data.get('arch_type', 'N.D.')}")
            report.append(f"Altezza imposta: {arch_data.get('impost_height', 0)} cm")
            report.append(f"Freccia arco: {arch_data.get('arch_rise', 0)} cm")
            
        report.append("")
        report.append("PARAMETRI CALANDRATURA:")
        
        # Calcola parametri
        radius = ArchReinforcementManager.calculate_arch_radius(opening_data)
        arc_length = ArchReinforcementManager.calculate_arch_length(opening_data)
        
        report.append(f"Raggio di curvatura: {radius:.1f} cm")
        report.append(f"Lunghezza sviluppata: {arc_length:.1f} cm")
        report.append(f"Angolo totale: {180:.0f}°")  # Per semicerchio
        
        if 'architrave' in reinforcement_data:
            arch = reinforcement_data['architrave']
            profile = arch.get('profilo', 'N.D.')
            n_profiles = arch.get('n_profili', 1)
            
            report.append("")
            report.append("PROFILI DA CALANDRARE:")
            report.append(f"Tipo: {profile}")
            report.append(f"Quantità: {n_profiles}")
            
            # Verifica calandrabilità
            steel = reinforcement_data.get('classe_acciaio', 'S235')
            check = ArchReinforcementManager.check_bendability(profile, radius, steel)
            
            report.append("")
            report.append("VERIFICA CALANDRABILITÀ:")
            report.append(f"Rapporto r/h: {check['r_h_ratio']:.1f}")
            report.append(f"Metodo consigliato: {check['method']}")
            report.append(f"Tensioni residue stimate: {check['residual_stress']:.0f} MPa")
            
            if check['warnings']:
                report.append("")
                report.append("AVVERTENZE:")
                for warning in check['warnings']:
                    report.append(f"- {warning}")
                    
        if 'calandratura' in reinforcement_data:
            cal = reinforcement_data['calandratura']
            report.append("")
            report.append("SPECIFICHE RICHIESTE:")
            report.append(f"Metodo: {cal.get('metodo', 'N.D.')}")
            report.append(f"Posizione: {cal.get('posizione', 'N.D.')}")
            
        # Tolleranze
        report.append("")
        report.append("TOLLERANZE:")
        report.append("- Raggio: ± 10 mm")
        report.append("- Planarità: ± L/500")
        report.append("- Torsione: ± 2°/m")
        
        return "\n".join(report)


class BendingVerificationDialog(QDialog):
    """Dialog per verifica dettagliata calandratura"""
    
    def __init__(self, parent, opening_data, profile_name, steel_grade='S235'):
        super().__init__(parent)
        self.opening_data = opening_data
        self.profile_name = profile_name
        self.steel_grade = steel_grade
        
        self.setWindowTitle("Verifica Calandratura Profilo")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self.setup_ui()
        self.calculate()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Info profilo
        info_group = QGroupBox("Profilo da Calandrare")
        info_layout = QFormLayout()
        
        self.profile_label = QLabel(self.profile_name)
        self.profile_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Profilo:", self.profile_label)
        
        self.steel_label = QLabel(self.steel_grade)
        info_layout.addRow("Acciaio:", self.steel_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Parametri geometrici
        geom_group = QGroupBox("Parametri Geometrici")
        geom_layout = QFormLayout()
        
        self.radius_label = QLabel()
        geom_layout.addRow("Raggio curvatura:", self.radius_label)
        
        self.length_label = QLabel()
        geom_layout.addRow("Lunghezza sviluppata:", self.length_label)
        
        self.angle_label = QLabel()
        geom_layout.addRow("Angolo totale:", self.angle_label)
        
        geom_group.setLayout(geom_layout)
        layout.addWidget(geom_group)
        
        # Verifica
        verify_group = QGroupBox("Verifica Calandrabilità")
        verify_layout = QFormLayout()
        
        self.rh_label = QLabel()
        verify_layout.addRow("Rapporto r/h:", self.rh_label)
        
        self.method_label = QLabel()
        self.method_label.setStyleSheet("font-weight: bold;")
        verify_layout.addRow("Metodo:", self.method_label)
        
        self.stress_label = QLabel()
        verify_layout.addRow("Tensioni residue:", self.stress_label)
        
        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)
        
        # Avvertenze
        self.warnings_text = QTextEdit()
        self.warnings_text.setMaximumHeight(100)
        self.warnings_text.setReadOnly(True)
        layout.addWidget(QLabel("Avvertenze:"))
        layout.addWidget(self.warnings_text)
        
        # Pulsanti
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def calculate(self):
        """Esegue i calcoli di verifica"""
        # Calcola parametri geometrici
        radius = ArchReinforcementManager.calculate_arch_radius(self.opening_data)
        length = ArchReinforcementManager.calculate_arch_length(self.opening_data)
        
        self.radius_label.setText(f"{radius:.1f} cm ({radius*10:.0f} mm)")
        self.length_label.setText(f"{length:.1f} cm ({length/100:.2f} m)")
        
        # Angolo (per arco tutto sesto è 180°)
        if self.opening_data.get('arch_data', {}).get('arch_type') == 'Tutto sesto':
            angle = 180
        else:
            # Calcola angolo per altri tipi
            angle = (length / radius) * 180 / math.pi
        self.angle_label.setText(f"{angle:.0f}°")
        
        # Verifica calandrabilità
        check = ArchReinforcementManager.check_bendability(
            self.profile_name, radius, self.steel_grade
        )
        
        # Mostra risultati
        self.rh_label.setText(f"{check['r_h_ratio']:.1f}")
        
        # Colora in base al risultato
        if check['r_h_ratio'] < 15:
            self.rh_label.setStyleSheet("color: red; font-weight: bold;")
        elif check['r_h_ratio'] < 30:
            self.rh_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.rh_label.setStyleSheet("color: green; font-weight: bold;")
            
        self.method_label.setText(check['method'])
        
        # Tensioni residue (da NTC2018)
        fy = NTC2018.Acciaio.get_fyk(self.steel_grade)
        stress_percent = (check['residual_stress'] / fy) * 100
        self.stress_label.setText(f"{check['residual_stress']:.0f} MPa ({stress_percent:.0f}% fy)")
        
        # Avvertenze
        if check['warnings']:
            self.warnings_text.setPlainText('\n'.join(f"• {w}" for w in check['warnings']))
            self.warnings_text.setStyleSheet("QTextEdit { color: red; }")
        else:
            self.warnings_text.setPlainText("Nessuna avvertenza particolare")
            self.warnings_text.setStyleSheet("QTextEdit { color: green; }")


# Test del modulo
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Test dati apertura
    test_opening = {
        'type': 'Ad arco',
        'x': 50,
        'y': 0,
        'width': 120,
        'height': 230,
        'arch_data': {
            'arch_type': 'Tutto sesto',
            'impost_height': 180,
            'arch_rise': 60
        }
    }
    
    # Test calcoli
    manager = ArchReinforcementManager()
    
    print(f"Lunghezza arco: {manager.calculate_arch_length(test_opening):.1f} cm")
    print(f"Raggio: {manager.calculate_arch_radius(test_opening):.1f} cm")
    
    # Test verifica calandrabilità
    check = manager.check_bendability("HEA 200", 60, "S355")
    print(f"\nVerifica HEA 200 con R=60cm:")
    print(f"Calandrabile: {check['bendable']}")
    print(f"Metodo: {check['method']}")
    print(f"r/h: {check['r_h_ratio']:.1f}")
    
    # Test dialog
    dialog = BendingVerificationDialog(None, test_opening, "HEA 200", "S355")
    dialog.exec_()
    
    sys.exit()