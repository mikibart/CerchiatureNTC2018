"""
Modulo Calcolo e Verifica
Esegue i calcoli secondo NTC 2018 e mostra i risultati
Versione aggiornata con supporto profili multipli, vincoli avanzati e aperture ad arco
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import math
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import logging

# Configurazione logging
logger = logging.getLogger(__name__)

# Import del motore di calcolo - FORZA USO CORE ENGINE
ENGINE_TYPE = None
import sys
sys.path.insert(0, '.')  # Assicura che cerchi nella directory corrente

try:
    from src.core.engine.masonry import MasonryCalculator
    from src.core.engine.steel_frame import SteelFrameCalculator
    from src.core.engine.concrete_frame import ConcreteFrameCalculator
    from src.core.engine.verifications import NTC2018Verifier
    # Import nuovi moduli per funzionalità avanzate
    from src.core.engine.steel_frame_advanced import SteelFrameAdvancedCalculator
    from src.core.engine.curved_openings import CurvedOpeningsCalculator
    from src.core.engine.connections import ConnectionsVerifier
    from src.core.engine.frame_result import FrameResult
    # Import modulo aperture ad arco
    from src.core.engine.arch_reinforcement import (
        ArchReinforcementManager, 
        BendingVerificationDialog
    )
    ENGINE_TYPE = "CORE"
    print(">>> USANDO CORE ENGINE COMPLETO - MODULI CARICATI CORRETTAMENTE")
    
except ImportError as e:
    print(f"ERRORE CRITICO: Moduli di calcolo non trovati - {e}")
    raise Exception("IMPOSSIBILE CARICARE I MODULI CORE - VERIFICARE INSTALLAZIONE")


class ResultsCanvas(FigureCanvas):
    """Canvas per visualizzazione grafici risultati"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 6), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)
        
    def plot_capacity_curves(self, results):
        """Traccia curve di capacità fisicamente corrette per muratura"""
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.set_xlabel('Spostamento [mm]')
        ax.set_ylabel('Taglio [kN]')
        ax.set_title('Curve di Capacità - Confronto Stato di Fatto/Progetto')
        ax.grid(True, alpha=0.3)
        
        # Parametri base per comportamento muratura
        mu_ductility_base = 2.5  # Duttilità tipica muratura (2-3)
        beta_degradation_base = 0.3  # Fattore di degrado post-picco (0.2-0.4)
        
        # Stato di fatto
        if 'original' in results:
            K_orig = results['original']['K']  # Rigidezza [kN/m]
            V_max_orig = results['original']['V_min']  # Resistenza [kN]
            
            # Determina il meccanismo di rottura critico
            if results['original']['V_t1'] == results['original']['V_min']:
                mechanism = 'shear'  # Taglio puro - comportamento più fragile
                mu_ductility = 2.0
                beta_degradation = 0.4
            elif results['original']['V_t3'] == results['original']['V_min']:
                mechanism = 'flexure'  # Presso-flessione - più duttile
                mu_ductility = 3.0
                beta_degradation = 0.2
            else:
                mechanism = 'mixed'  # Misto
                mu_ductility = mu_ductility_base
                beta_degradation = beta_degradation_base
            
            # Calcola spostamenti caratteristici
            d_yield_orig = V_max_orig / K_orig * 1000  # [mm] spostamento al limite elastico
            d_max_orig = d_yield_orig * mu_ductility  # [mm] spostamento ultimo
            
            # Genera punti curva
            d = np.linspace(0, d_max_orig * 1.2, 200)
            V = np.zeros_like(d)
            
            for i, di in enumerate(d):
                if di <= d_yield_orig:
                    # Tratto elastico lineare
                    V[i] = K_orig * di / 1000  # K in kN/m, d in mm
                elif di <= d_max_orig:
                    # Tratto post-picco con degrado
                    V[i] = V_max_orig * (1 - beta_degradation * 
                                        (di - d_yield_orig) / (d_max_orig - d_yield_orig))
                else:
                    # Residuo minimo (20% della resistenza)
                    V[i] = V_max_orig * (1 - beta_degradation)
                    
            ax.plot(d, V, 'b-', linewidth=2, label='Stato di fatto')
            
            # Marca punto di snervamento
            ax.plot(d_yield_orig, V_max_orig, 'bo', markersize=8)
            
            # Aggiungi annotazione per meccanismo
            ax.annotate(f'Meccanismo: {mechanism}', 
                       xy=(d_yield_orig, V_max_orig), 
                       xytext=(d_yield_orig + 5, V_max_orig * 0.9),
                       fontsize=8, style='italic')
            
        # Stato di progetto
        if 'modified' in results:
            K_mod = results['modified']['K']  # Rigidezza [kN/m]
            V_max_mod = results['modified']['V_min']  # Resistenza [kN]
            
            # Determina il meccanismo di rottura critico per stato modificato
            if results['modified']['V_t1'] == results['modified']['V_min']:
                mechanism_mod = 'shear'
                mu_ductility_mod = 2.0
                beta_degradation_mod = 0.4
            elif results['modified']['V_t3'] == results['modified']['V_min']:
                mechanism_mod = 'flexure'
                mu_ductility_mod = 3.0
                beta_degradation_mod = 0.2
            else:
                mechanism_mod = 'mixed'
                mu_ductility_mod = mu_ductility_base
                beta_degradation_mod = beta_degradation_base
            
            # La presenza di cerchiature può aumentare la duttilità
            if 'K_cerchiature' in results['modified'] and results['modified']['K_cerchiature'] > 0:
                frame_contribution = results['modified']['K_cerchiature'] / results['modified']['K']
                if frame_contribution > 0.3:  # Contributo significativo delle cerchiature
                    mu_ductility_mod *= 1.3  # Aumento duttilità del 30%
                    beta_degradation_mod *= 0.8  # Degrado più graduale
            
            # Calcola spostamenti caratteristici
            d_yield_mod = V_max_mod / K_mod * 1000  # [mm]
            d_max_mod = d_yield_mod * mu_ductility_mod  # [mm]
            
            # Genera punti curva
            d = np.linspace(0, d_max_mod * 1.2, 200)
            V = np.zeros_like(d)
            
            for i, di in enumerate(d):
                if di <= d_yield_mod:
                    # Tratto elastico
                    V[i] = K_mod * di / 1000
                elif di <= d_max_mod:
                    # Tratto post-picco
                    V[i] = V_max_mod * (1 - beta_degradation_mod * 
                                       (di - d_yield_mod) / (d_max_mod - d_yield_mod))
                else:
                    # Residuo
                    V[i] = V_max_mod * (1 - beta_degradation_mod)
                    
            ax.plot(d, V, 'r--', linewidth=2, label='Stato di progetto')
            
            # Marca punto di snervamento
            ax.plot(d_yield_mod, V_max_mod, 'ro', markersize=8)
            
            # Annotazione
            ax.annotate(f'Meccanismo: {mechanism_mod}', 
                       xy=(d_yield_mod, V_max_mod), 
                       xytext=(d_yield_mod + 5, V_max_mod * 0.9),
                       fontsize=8, style='italic')
        
        # Aggiungi informazioni aggiuntive
        if 'original' in results and 'modified' in results:
            # Box con informazioni riassuntive
            textstr = f'Rigidezza:\nOriginale: {K_orig:.0f} kN/m\nProgetto: {K_mod:.0f} kN/m\n\n'
            textstr += f'Resistenza:\nOriginale: {V_max_orig:.1f} kN\nProgetto: {V_max_mod:.1f} kN\n\n'
            textstr += f'Duttilità:\nOriginale: μ={mu_ductility:.1f}\nProgetto: μ={mu_ductility_mod:.1f}'
            
            if 'K_cerchiature' in results['modified'] and results['modified']['K_cerchiature'] > 0:
                contrib_percent = (results['modified']['K_cerchiature'] / results['modified']['K']) * 100
                textstr += f'\n\nContributo cerchiature: {contrib_percent:.0f}%'
            
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.65, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', bbox=props)
        
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper right')
        self.draw()
    
    def analyze_capacity_parameters(self, results):
        """Analizza parametri di capacità per comportamento non lineare"""
        params = {}
        
        if 'original' in results:
            # Analisi stato originale
            K = results['original']['K']
            V_min = results['original']['V_min']
            
            # Identifica meccanismo
            if results['original']['V_t1'] == V_min:
                params['original_mechanism'] = 'taglio'
                params['original_ductility'] = 2.0
            elif results['original']['V_t3'] == V_min:
                params['original_mechanism'] = 'pressoflessione'
                params['original_ductility'] = 3.0
            else:
                params['original_mechanism'] = 'misto'
                params['original_ductility'] = 2.5
                
            # Spostamento al limite elastico
            params['original_dy'] = V_min / K * 1000  # mm
            
        if 'modified' in results:
            # Analisi stato modificato
            K = results['modified']['K']
            V_min = results['modified']['V_min']
            
            # Meccanismo modificato
            if results['modified']['V_t1'] == V_min:
                params['modified_mechanism'] = 'taglio'
                base_ductility = 2.0
            elif results['modified']['V_t3'] == V_min:
                params['modified_mechanism'] = 'pressoflessione'
                base_ductility = 3.0
            else:
                params['modified_mechanism'] = 'misto'
                base_ductility = 2.5
                
            # Incremento duttilità per cerchiature
            if 'K_cerchiature' in results['modified']:
                frame_ratio = results['modified']['K_cerchiature'] / K
                ductility_factor = 1 + 0.3 * min(frame_ratio / 0.3, 1.0)
                params['modified_ductility'] = base_ductility * ductility_factor
            else:
                params['modified_ductility'] = base_ductility
                
            params['modified_dy'] = V_min / K * 1000  # mm
            
        return params
        
    def plot_stiffness_comparison(self, results):
        """Grafico confronto rigidezze"""
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        
        if 'original' in results and 'modified' in results:
            labels = ['Stato di fatto', 'Stato di progetto']
            values = [results['original']['K'], results['modified']['K']]
            colors = ['blue', 'red']
            
            bars = ax.bar(labels, values, color=colors, alpha=0.7)
            
            # Aggiungi valori sopra le barre
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}',
                       ha='center', va='bottom')
                       
            # Linea limite variazione 15%
            K_original = results['original']['K']
            ax.axhline(y=K_original * 1.15, color='g', linestyle='--', 
                      label='Limite +15%', alpha=0.5)
            ax.axhline(y=K_original * 0.85, color='g', linestyle='--', 
                      label='Limite -15%', alpha=0.5)
            
            ax.set_ylabel('Rigidezza [kN/m]')
            ax.set_title('Confronto Rigidezze')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
        self.draw()
        
    def plot_resistance_comparison(self, results):
        """Grafico confronto resistenze"""
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        
        if 'original' in results and 'modified' in results:
            categories = ['V_t1\n(Taglio)', 'V_t2\n(Taglio con\nfattore forma)', 
                         'V_t3\n(Presso-\nflessione)']
            
            x = np.arange(len(categories))
            width = 0.35
            
            values_original = [
                results['original']['V_t1'],
                results['original']['V_t2'],
                results['original']['V_t3']
            ]
            values_modified = [
                results['modified']['V_t1'],
                results['modified']['V_t2'],
                results['modified']['V_t3']
            ]
            
            bars1 = ax.bar(x - width/2, values_original, width, 
                          label='Stato di fatto', color='blue', alpha=0.7)
            bars2 = ax.bar(x + width/2, values_modified, width, 
                          label='Stato di progetto', color='red', alpha=0.7)
            
            # Valori sopra le barre
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=9)
            
            ax.set_ylabel('Resistenza [kN]')
            ax.set_title('Confronto Resistenze')
            ax.set_xticks(x)
            ax.set_xticklabels(categories)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
        self.draw()
        
    def plot_frame_details(self, frame_results):
        """Grafico dettagli cerchiature"""
        self.figure.clear()
        
        if not frame_results:
            return
            
        # Crea subplot per ogni cerchiatura
        n_frames = len(frame_results)
        rows = int(np.ceil(np.sqrt(n_frames)))
        cols = int(np.ceil(n_frames / rows))
        
        for i, (opening_id, frame_data) in enumerate(frame_results.items()):
            ax = self.figure.add_subplot(rows, cols, i+1)
            
            # Dati da plottare
            categories = ['K_frame', 'N_max', 'M_max', 'V_max']
            values = [
                frame_data.get('K_frame', 0) / 1000,  # in MN/m
                frame_data.get('N_max', 0),  # kN
                frame_data.get('M_max', 0),  # kNm
                frame_data.get('V_max', 0)   # kN
            ]
            
            bars = ax.bar(categories, values, color=['blue', 'red', 'green', 'orange'])
            ax.set_title(f'Apertura {opening_id}')
            ax.set_ylabel('Valore')
            
            # Valori sopra le barre
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{value:.1f}',
                       ha='center', va='bottom', fontsize=8)
                       
        self.figure.tight_layout()
        self.draw()


class CalcModule(QWidget):
    """Modulo calcolo e verifica con supporto funzionalità avanzate"""
    
    calculation_done = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.project_data = {}
        self.results = {}
        self._is_calculating = False  # Flag anti-ripetizione
        self.setup_ui()
        
        # Inizializza calcolatori
        self.masonry_calc = MasonryCalculator()
        self.steel_calc = SteelFrameCalculator()
        self.steel_advanced_calc = SteelFrameAdvancedCalculator()
        self.concrete_calc = ConcreteFrameCalculator()
        self.curved_calc = CurvedOpeningsCalculator()
        self.connections_verifier = ConnectionsVerifier()
        self.verifier = NTC2018Verifier()
        self.arch_manager = ArchReinforcementManager()  # Nuovo manager archi
        
        print(f"\n>>> CalcModule inizializzato con supporto avanzato e aperture ad arco")
        
    def setup_ui(self):
        """Costruisce interfaccia calcolo"""
        main_layout = QVBoxLayout()
        
        # Toolbar calcolo
        toolbar_layout = QHBoxLayout()
        
        self.calc_btn = QPushButton("Esegui Calcolo")
        self.calc_btn.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.calc_btn.clicked.connect(self.run_calculation)
        toolbar_layout.addWidget(self.calc_btn)
        
        self.export_btn = QPushButton("Esporta Risultati")
        self.export_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_results)
        toolbar_layout.addWidget(self.export_btn)
        
        # Nuovo pulsante per dettagli avanzati
        self.advanced_btn = QPushButton("Dettagli Avanzati")
        self.advanced_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.advanced_btn.setEnabled(False)
        self.advanced_btn.clicked.connect(self.show_advanced_details)
        toolbar_layout.addWidget(self.advanced_btn)
        
        toolbar_layout.addStretch()
        
        self.status_label = QLabel("In attesa di dati...")
        toolbar_layout.addWidget(self.status_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # Splitter principale
        splitter = QSplitter(Qt.Horizontal)
        
        # Pannello sinistro - Risultati numerici
        left_panel = self.create_results_panel()
        splitter.addWidget(left_panel)
        
        # Pannello destro - Grafici
        right_panel = self.create_graphs_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def set_project_data(self, data):
        """Imposta i dati del progetto per il calcolo"""
        self.project_data = data
        
        # Abilita il pulsante di calcolo se ci sono dati validi
        if data and all(key in data for key in ['wall', 'masonry', 'openings']):
            self.calc_btn.setEnabled(True)
            self.status_label.setText("Pronto per il calcolo")
        else:
            self.calc_btn.setEnabled(False)
            self.status_label.setText("Dati incompleti")
            
        # Reset risultati precedenti quando cambiano i dati
        self.results = {}
        self.export_btn.setEnabled(False)
        self.advanced_btn.setEnabled(False)
        
        # Pulisce visualizzazioni precedenti
        self.reset_displays()
        
    def reset_displays(self):
        """Reset delle visualizzazioni mantenendo la struttura"""
        # Reset etichette risultati
        self.local_check_label.setText("-")
        self.stiffness_var_label.setText("-")
        self.resistance_var_label.setText("-")
        
        self.original_k_label.setText("-")
        self.original_vt1_label.setText("-")
        self.original_vt2_label.setText("-")
        self.original_vt3_label.setText("-")
        self.original_vmin_label.setText("-")
        
        self.modified_k_label.setText("-")
        self.modified_vt1_label.setText("-")
        self.modified_vt2_label.setText("-")
        self.modified_vt3_label.setText("-")
        self.modified_vmin_label.setText("-")
        
        self.notes_text.clear()
        
        # Clear layouts
        for layout in [self.maschi_layout, self.cerchiature_layout]:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        # Clear grafici
        for canvas in [self.capacity_canvas, self.stiffness_canvas, 
                      self.resistance_canvas, self.frames_canvas]:
            canvas.figure.clear()
            canvas.draw()
        
    def create_results_panel(self):
        """Crea pannello risultati numerici"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area per contenere tutti i risultati
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Riepilogo verifiche
        self.verification_group = QGroupBox("Verifica Intervento Locale")
        verif_layout = QFormLayout()
        
        self.local_check_label = QLabel("-")
        verif_layout.addRow("Intervento locale:", self.local_check_label)
        
        self.stiffness_var_label = QLabel("-")
        verif_layout.addRow("Variazione rigidezza:", self.stiffness_var_label)
        
        self.resistance_var_label = QLabel("-")
        verif_layout.addRow("Variazione resistenza:", self.resistance_var_label)
        
        self.verification_group.setLayout(verif_layout)
        scroll_layout.addWidget(self.verification_group)
        
        # Risultati stato di fatto
        self.original_group = QGroupBox("Stato di Fatto")
        original_layout = QFormLayout()
        
        self.original_k_label = QLabel("-")
        original_layout.addRow("Rigidezza K:", self.original_k_label)
        
        self.original_vt1_label = QLabel("-")
        original_layout.addRow("V_t1 (taglio):", self.original_vt1_label)
        
        self.original_vt2_label = QLabel("-")
        original_layout.addRow("V_t2 (taglio f.f.):", self.original_vt2_label)
        
        self.original_vt3_label = QLabel("-")
        original_layout.addRow("V_t3 (presso-flex):", self.original_vt3_label)
        
        self.original_vmin_label = QLabel("-")
        original_layout.addRow("V_min:", self.original_vmin_label)
        
        self.original_group.setLayout(original_layout)
        scroll_layout.addWidget(self.original_group)
        
        # Risultati stato di progetto
        self.modified_group = QGroupBox("Stato di Progetto")
        modified_layout = QFormLayout()
        
        self.modified_k_label = QLabel("-")
        modified_layout.addRow("Rigidezza K:", self.modified_k_label)
        
        self.modified_vt1_label = QLabel("-")
        modified_layout.addRow("V_t1 (taglio):", self.modified_vt1_label)
        
        self.modified_vt2_label = QLabel("-")
        modified_layout.addRow("V_t2 (taglio f.f.):", self.modified_vt2_label)
        
        self.modified_vt3_label = QLabel("-")
        modified_layout.addRow("V_t3 (presso-flex):", self.modified_vt3_label)
        
        self.modified_vmin_label = QLabel("-")
        modified_layout.addRow("V_min:", self.modified_vmin_label)
        
        self.modified_group.setLayout(modified_layout)
        scroll_layout.addWidget(self.modified_group)
        
        # Dettaglio maschi murari
        self.maschi_group = QGroupBox("Maschi Murari")
        self.maschi_layout = QVBoxLayout()
        self.maschi_group.setLayout(self.maschi_layout)
        scroll_layout.addWidget(self.maschi_group)
        
        # Nuovo: Dettaglio cerchiature
        self.cerchiature_group = QGroupBox("Dettaglio Cerchiature")
        self.cerchiature_layout = QVBoxLayout()
        self.cerchiature_group.setLayout(self.cerchiature_layout)
        scroll_layout.addWidget(self.cerchiature_group)
        
        # Note e avvertimenti
        self.notes_group = QGroupBox("Note e Avvertimenti")
        notes_layout = QVBoxLayout()
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(150)
        notes_layout.addWidget(self.notes_text)
        self.notes_group.setLayout(notes_layout)
        scroll_layout.addWidget(self.notes_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        panel.setLayout(layout)
        return panel
        
    def create_graphs_panel(self):
        """Crea pannello grafici"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Tab per diversi grafici
        self.graph_tabs = QTabWidget()
        
        # Grafico curve di capacità
        self.capacity_canvas = ResultsCanvas()
        self.graph_tabs.addTab(self.capacity_canvas, "Curve di Capacità")
        
        # Grafico confronto rigidezze
        self.stiffness_canvas = ResultsCanvas()
        self.graph_tabs.addTab(self.stiffness_canvas, "Confronto Rigidezze")
        
        # Grafico confronto resistenze
        self.resistance_canvas = ResultsCanvas()
        self.graph_tabs.addTab(self.resistance_canvas, "Confronto Resistenze")
        
        # Nuovo: Grafico dettagli cerchiature
        self.frames_canvas = ResultsCanvas()
        self.graph_tabs.addTab(self.frames_canvas, "Dettagli Cerchiature")
        
        layout.addWidget(self.graph_tabs)
        
        panel.setLayout(layout)
        return panel

    def _calculate_frame_contribution(self, opening: Dict, rinforzo: Dict, 
                                     wall_data: Dict, opening_id: str) -> Dict:
        """
        Metodo unificato per calcolare il contributo di una cerchiatura
        Gestisce tutti i tipi di rinforzo in modo robusto
        
        Args:
            opening: dati apertura
            rinforzo: dati rinforzo
            wall_data: dati parete
            opening_id: identificativo apertura
            
        Returns:
            Dict con risultati standardizzati
        """
        try:
            materiale = rinforzo.get('materiale', '')
            tipo = rinforzo.get('tipo', '')
            
            # Log per debug
            logger.info(f"Calcolo cerchiatura {opening_id}: materiale={materiale}, tipo={tipo}")
            
            # Inizializza risultato default
            frame_result = {
                'K_frame': 0,
                'M_max': 0,
                'V_max': 0,
                'N_max': 0,
                'V_resistance': 0,  # NUOVO: resistenza a taglio del telaio
                'materiale': materiale,
                'tipo': tipo,
                'error': None,
                'warnings': []
            }
            
            # Flag per determinare se procedere con calcolo standard
            use_standard_calc = True
            
            # Verifica calandrabilità per aperture ad arco
            if opening.get('type') == 'Ad arco' or 'calandrat' in tipo.lower():
                # Verifica se il profilo è calandrabile
                if materiale == 'acciaio':
                    radius = self.arch_manager.calculate_arch_radius(opening)
                    profile = rinforzo.get('architrave', {}).get('profilo', '')
                    steel = rinforzo.get('classe_acciaio', 'S235')
                    
                    if radius > 0 and profile:  # Solo se abbiamo dati validi
                        check = self.arch_manager.check_bendability(profile, radius, steel)
                        
                        # Aggiungi sempre info calandratura ai risultati
                        frame_result['bending_info'] = check
                        frame_result['arch_radius'] = radius
                        frame_result['arch_length'] = self.arch_manager.calculate_arch_length(opening)
                        
                        if not check['bendable']:
                            # IMPORTANTE: Non bloccare il calcolo, solo avvisare
                            logger.warning(f"Profilo {profile} non calandrabile: {check['method']}")
                            frame_result['warnings'].append(f"ATTENZIONE: {check['method']}")
                            frame_result['warnings'].extend(check['warnings'])
                            
                            # Per aperture ad arco con profilo non calandrabile:
                            # Possiamo procedere con approccio alternativo
                            frame_result['warnings'].append(
                                "Si suggerisce: profili segmentati saldati o cambio sezione"
                            )
                            # Procedi comunque con il calcolo standard come approssimazione
                            # In realtà il telaio potrebbe essere realizzato con segmenti
            
            # Routing basato su materiale e tipo
            if materiale == 'acciaio':
                # Verifica profili multipli
                arch_n_profili = rinforzo.get('architrave', {}).get('n_profili', 1)
                pied_n_profili = rinforzo.get('piedritti', {}).get('n_profili', 1)
                
                # Determina quale calcolatore usare
                if use_standard_calc:
                    if arch_n_profili > 1 or pied_n_profili > 1:
                        # Calcolo avanzato per profili multipli
                        result = self.steel_advanced_calc.calculate_frame_stiffness_advanced(
                            opening, rinforzo, wall_data
                        )
                    else:
                        # Calcolo standard
                        result = self.steel_calc.calculate_frame_stiffness(
                            opening, rinforzo
                        )
                else:
                    # Se abbiamo disabilitato il calcolo standard (per future implementazioni)
                    result = {'K_frame': 0}
                    
            elif materiale == 'ca':
                result = self.concrete_calc.calculate_frame_stiffness(
                    opening, rinforzo
                )
            else:
                logger.warning(f"Materiale non riconosciuto: {materiale}")
                result = frame_result
                
            # Gestisce sia vecchio formato (float) che nuovo (dict)
            if isinstance(result, dict):
                # Mantieni warnings e info già presenti
                current_warnings = frame_result.get('warnings', [])
                current_bending_info = frame_result.get('bending_info')
                current_arch_radius = frame_result.get('arch_radius')
                current_arch_length = frame_result.get('arch_length')
                
                frame_result.update(result)
                
                # Ripristina info che potrebbero essere state sovrascritte
                if current_warnings:
                    frame_result['warnings'] = current_warnings
                if current_bending_info:
                    frame_result['bending_info'] = current_bending_info
                if current_arch_radius:
                    frame_result['arch_radius'] = current_arch_radius
                if current_arch_length:
                    frame_result['arch_length'] = current_arch_length
            else:
                # Retrocompatibilità
                logger.warning(f"Risultato non standard da {opening_id}: {type(result)}")
                frame_result['K_frame'] = float(result) if result else 0
                
            # Calcola sollecitazioni se non presenti
            if frame_result.get('M_max', 0) == 0 or frame_result.get('V_max', 0) == 0:
                design_forces = self._estimate_frame_forces(opening, wall_data)
                frame_result.update(design_forces)
                
            # NUOVO: Calcola resistenza del telaio
            if materiale == 'acciaio' and frame_result.get('K_frame', 0) > 0:
                # Calcola resistenza considerando l'orientamento
                frame_resistance = self._calculate_frame_resistance(opening, rinforzo)
                frame_result['V_resistance'] = frame_resistance
                logger.info(f"{opening_id}: V_resistance = {frame_resistance:.1f} kN")
                
            # Verifica connessioni se presenti dati
            if 'ancoraggio' in rinforzo:
                connection_result = self.connections_verifier.verify_anchors(
                    rinforzo['ancoraggio'], frame_result
                )
                frame_result['connections'] = connection_result
                
        except Exception as e:
            logger.error(f"Errore calcolo cerchiatura {opening_id}: {str(e)}")
            frame_result['error'] = str(e)
            
        return frame_result

    def _estimate_frame_forces(self, opening: Dict, wall_data: Dict) -> Dict:
        """Stima sollecitazioni sul telaio"""
        L = opening['width'] / 100  # m
        h = opening['height'] / 100  # m
        t = wall_data.get('thickness', 30) / 100  # m
        h_muro = wall_data.get('height', 350) / 100  # m
        
        # Carico verticale sull'architrave
        h_sopra = h_muro - (opening['y'] + opening['height']) / 100
        h_sopra = max(h_sopra, 0)  # Evita valori negativi
        q_vert = 18 * t * h_sopra  # kN/m (peso muratura sopra)
        
        return {
            'M_max': q_vert * L**2 / 8,  # kNm
            'V_max': q_vert * L / 2,      # kN
            'N_max': q_vert * L / 2,      # kN (stima)
            'q_vert': q_vert
        }
        
    def _calculate_frame_resistance(self, opening: Dict, rinforzo: Dict) -> float:
        """
        Calcola la resistenza a taglio del telaio considerando l'orientamento
        
        Returns:
            V_resistance: Resistenza a taglio del telaio [kN]
        """
        # Database momenti plastici profili IPE/HEB [kNm]
        # Formato: {profilo: (Wpl_y, Wpl_z)} con orientamento normale e ruotato
        PLASTIC_MODULI = {
            'IPE 100': (39.4, 9.15),
            'IPE 120': (60.7, 13.6),
            'IPE 140': (88.3, 19.2),
            'IPE 160': (124, 26.1),    # Wy=124cm³, Wz=26.1cm³
            'IPE 180': (166, 34.6),
            'IPE 200': (221, 44.6),
            'IPE 220': (285, 58.1),
            'IPE 240': (367, 73.9),
            'HEB 100': (104, 51.4),
            'HEB 120': (165, 77.8),
            'HEB 140': (246, 112),
            'HEB 160': (354, 158),
            'HEB 180': (482, 213),
            'HEB 200': (643, 282),
        }
        
        try:
            # Dati architrave
            arch = rinforzo.get('architrave', {})
            profilo = arch.get('profilo', '')
            n_profili = arch.get('n_profili', 1)
            ruotato = arch.get('ruotato', False)
            classe_acciaio = rinforzo.get('classe_acciaio', 'S235')
            
            # Tensione di snervamento
            fy = {
                'S235': 235,
                'S275': 275,
                'S355': 355,
                'S450': 450
            }.get(classe_acciaio, 235)  # MPa
            
            # Modulo plastico
            if profilo in PLASTIC_MODULI:
                Wpl_y, Wpl_z = PLASTIC_MODULI[profilo]
                # Seleziona modulo in base all'orientamento
                Wpl = Wpl_z if ruotato else Wpl_y  # cm³
                
                logger.info(f"Profilo {profilo}: ruotato={ruotato}, Wpl={Wpl} cm³")
            else:
                # Stima per profili non in database
                logger.warning(f"Profilo {profilo} non in database, stima approssimata")
                Wpl = 100  # cm³ - valore di default
                
            # Momento plastico architrave
            Mp_arch = (Wpl * fy / 1000) * n_profili  # kNm
            
            # Geometria apertura
            L = opening['width'] / 100  # m
            h = opening['height'] / 100  # m
            
            # Resistenza telaio - meccanismo a portale
            # V = 2 * (Mp_arch + Mp_pied) / h
            # Assumiamo piedritti con stesso profilo
            Mp_pied = Mp_arch  # Semplificazione conservativa
            
            V_frame = 2 * (Mp_arch + Mp_pied) / h  # kN
            
            # Limita per snellezza telaio
            if h/L > 2:
                # Telaio molto snello, riduco resistenza
                V_frame *= 0.7
                
            logger.info(f"Resistenza telaio: Mp={Mp_arch:.1f} kNm, V={V_frame:.1f} kN")
            
            return V_frame
            
        except Exception as e:
            logger.error(f"Errore calcolo resistenza telaio: {str(e)}")
            return 0
        
    def run_calculation(self):
        """Esegue il calcolo completo con supporto profili multipli"""
        # Controllo anti-ripetizione
        if self._is_calculating:
            logger.warning("Calcolo già in corso - richiesta ignorata")
            return
            
        if not self.project_data:
            QMessageBox.warning(self, "Attenzione", 
                              "Nessun dato di progetto disponibile")
            return
            
        self._is_calculating = True  # Imposta flag
        
        try:
            self.status_label.setText("Calcolo in corso...")
            QApplication.processEvents()
            
            # Estrai dati necessari
            wall_data = self.project_data.get('wall', {})
            masonry_data = self.project_data.get('masonry', {})
            openings_input = self.project_data.get('openings', [])
            openings_module = self.project_data.get('openings_module', {})
            openings_with_reinforcement = openings_module.get('openings', [])
            loads_data = self.project_data.get('loads', {})
            
            # DEBUG: Verifica dati rinforzi
            print(f"\n=== DEBUG APERTURE CON RINFORZI ===")
            for i, opening in enumerate(openings_with_reinforcement):
                print(f"\nApertura {i+1}:")
                print(f"  Tipo apertura: {opening.get('type', 'Rettangolare')}")
                print(f"  Rinforzo presente: {'rinforzo' in opening}")
                if 'rinforzo' in opening:
                    print(f"  Tipo: {opening['rinforzo'].get('tipo', 'N.D.')}")
                    print(f"  Materiale: {opening['rinforzo'].get('materiale', 'N.D.')}")
                    if 'architrave' in opening['rinforzo']:
                        print(f"  Architrave: {opening['rinforzo']['architrave']}")
            
            # Applica fattore di confidenza
            FC = self.get_confidence_factor(masonry_data.get('knowledge_level'))
            self.masonry_calc.FC = FC
            self.masonry_calc.set_project_data(self.project_data)
            
            print(f"\nFC applicato: {FC}")
            print(f"Aperture esistenti: {len([op for op in openings_input if op.get('existing', False)])}")
            print(f"Aperture totali con rinforzi: {len(openings_with_reinforcement)}")
            
            # Calcolo stato di fatto (solo aperture esistenti)
            existing_openings = [op for op in openings_input if op.get('existing', False)]
            
            print(f"\n--- CALCOLO STATO DI FATTO ---")
            V_t1_orig, V_t2_orig, V_t3_orig = self.masonry_calc.calculate_resistance(
                wall_data, masonry_data, existing_openings
            )
            K_orig = self.masonry_calc.calculate_stiffness(
                wall_data, masonry_data, existing_openings
            )
            
            # Calcolo stato di progetto (tutte le aperture)
            print(f"\n--- CALCOLO STATO DI PROGETTO ---")
            V_t1_mod, V_t2_mod, V_t3_mod = self.masonry_calc.calculate_resistance(
                wall_data, masonry_data, openings_with_reinforcement
            )
            K_base = self.masonry_calc.calculate_stiffness(
                wall_data, masonry_data, openings_with_reinforcement
            )
            
            # Calcolo avanzato contributo cerchiature
            K_cerchiature = 0
            V_cerchiature = 0  # NUOVO: contributo resistenza cerchiature
            frame_results = {}
            
            logger.info(f"\n=== CALCOLO CONTRIBUTO CERCHIATURE ===")
            logger.info(f"Aperture con rinforzo: {len(openings_with_reinforcement)}")
            
            for i, opening in enumerate(openings_with_reinforcement):
                if 'rinforzo' in opening:
                    opening_id = f"A{i+1}"
                    
                    # Usa il nuovo metodo unificato e robusto
                    frame_result = self._calculate_frame_contribution(
                        opening, 
                        opening['rinforzo'], 
                        wall_data, 
                        opening_id
                    )
                    
                    # Accumula rigidezza
                    k_contrib = frame_result.get('K_frame', 0)
                    K_cerchiature += k_contrib
                    
                    # NUOVO: Accumula resistenza
                    v_contrib = frame_result.get('V_resistance', 0)
                    V_cerchiature += v_contrib
                    
                    # Salva risultati
                    frame_results[opening_id] = frame_result
                    
                    # Log per debug
                    logger.info(f"{opening_id}: K_frame = {k_contrib:.1f} kN/m, "
                              f"V_resistance = {v_contrib:.1f} kN, "
                              f"tipo = {frame_result.get('tipo', 'N.D.')}")
                    
                    if frame_result.get('error'):
                        logger.error(f"{opening_id}: {frame_result['error']}")
                        
            K_mod = K_base + K_cerchiature
            
            # NUOVO: Applica contributo resistenza cerchiature
            # Fattore di collaborazione muratura-telaio
            collaborazione = 0.7  # Valore tipico per cerchiature metalliche
            
            # Le cerchiature contribuiscono principalmente a V_t3 (pressoflessione)
            # e parzialmente a V_t1 e V_t2 (taglio)
            V_t1_cerch = V_cerchiature * 0.3 * collaborazione
            V_t2_cerch = V_cerchiature * 0.3 * collaborazione  
            V_t3_cerch = V_cerchiature * 0.8 * collaborazione
            
            # Somma contributi
            V_t1_mod += V_t1_cerch
            V_t2_mod += V_t2_cerch
            V_t3_mod += V_t3_cerch
            
            logger.info(f"K_cerchiature totale = {K_cerchiature:.1f} kN/m")
            logger.info(f"V_cerchiature totale = {V_cerchiature:.1f} kN")
            logger.info(f"Contributi resistenza: V_t1+={V_t1_cerch:.1f}, "
                       f"V_t2+={V_t2_cerch:.1f}, V_t3+={V_t3_cerch:.1f}")
            logger.info(f"K_mod finale = {K_mod:.1f} kN/m")
            
            # Resistenze minime
            V_min_orig = min(V_t1_orig, V_t2_orig, V_t3_orig)
            V_min_mod = min(V_t1_mod, V_t2_mod, V_t3_mod)
            
            # Debug risultati
            print(f"\n{'='*30} RISULTATI CALC {'='*30}")
            print(f"STATO DI FATTO:")
            print(f"  K_orig = {K_orig:.1f} kN/m")
            print(f"  V_min_orig = {V_min_orig:.1f} kN")
            
            print(f"\nSTATO DI PROGETTO:")
            print(f"  K_mod = {K_mod:.1f} kN/m (base: {K_base:.1f} + cerch: {K_cerchiature:.1f})")
            print(f"  V_min_mod = {V_min_mod:.1f} kN (include contributo cerchiature)")
            print(f"  Incremento resistenza cerchiature: +{V_cerchiature * collaborazione:.1f} kN")
            
            # Dettagli cerchiature
            print(f"\nDETTAGLI CERCHIATURE:")
            for opening_id, frame_data in frame_results.items():
                print(f"  {opening_id}: K_frame = {frame_data.get('K_frame', 0):.1f} kN/m, "
                      f"V_resistance = {frame_data.get('V_resistance', 0):.1f} kN")
                
            # Verifica intervento locale
            verification = self.verifier.verify_local_intervention(
                K_orig, K_mod, V_min_orig, V_min_mod
            )
            
            # Salva risultati
            self.results = {
                'original': {
                    'K': K_orig,
                    'V_t1': V_t1_orig,
                    'V_t2': V_t2_orig,
                    'V_t3': V_t3_orig,
                    'V_min': V_min_orig
                },
                'modified': {
                    'K': K_mod,
                    'V_t1': V_t1_mod,
                    'V_t2': V_t2_mod,
                    'V_t3': V_t3_mod,
                    'V_min': V_min_mod,
                    'K_cerchiature': K_cerchiature,
                    'V_cerchiature': V_cerchiature  # NUOVO: contributo resistenza
                },
                'verification': verification,
                'FC': FC,
                'frame_results': frame_results
            }
            
            # Calcola risultati per maschi murari
            self.calculate_maschi_results(wall_data, openings_with_reinforcement)
            
            # Aggiorna interfaccia
            self.update_results_display()
            
            # Genera note e avvertimenti
            self.generate_notes()
            
            # Aggiorna grafici
            self.update_graphs()
            
            self.status_label.setText("Calcolo completato")
            self.export_btn.setEnabled(True)
            self.advanced_btn.setEnabled(True)
            
            # Emetti segnale con risultati
            self.calculation_done.emit(self.results)
            
        except Exception as e:
            import traceback
            print(f"\nERRORE NEL CALCOLO:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Errore", 
                               f"Errore durante il calcolo:\n{str(e)}")
            self.status_label.setText("Errore nel calcolo")
            
        finally:
            self._is_calculating = False  # Reset flag
            
    def update_results_display(self):
        """Aggiorna visualizzazione risultati con dettagli cerchiature"""
        if not self.results:
            return
            
        # Verifica intervento locale
        verif = self.results['verification']
        if verif['is_local']:
            self.local_check_label.setText(
                '<span style="color: green;">✓ VERIFICATO</span>'
            )
        else:
            self.local_check_label.setText(
                '<span style="color: red;">✗ NON VERIFICATO</span>'
            )
            
        # Variazioni
        stiff_var = verif['stiffness_variation']
        if verif['stiffness_ok']:
            self.stiffness_var_label.setText(
                f'<span style="color: green;">{stiff_var:.1f}% (≤ 15%)</span>'
            )
        else:
            self.stiffness_var_label.setText(
                f'<span style="color: red;">{stiff_var:.1f}% (> 15%)</span>'
            )
            
        res_var = verif['resistance_variation']
        if verif['resistance_ok']:
            self.resistance_var_label.setText(
                f'<span style="color: green;">{res_var:.1f}% (≤ 20%)</span>'
            )
        else:
            self.resistance_var_label.setText(
                f'<span style="color: red;">{res_var:.1f}% (> 20%)</span>'
            )
            
        # Stato di fatto
        orig = self.results['original']
        self.original_k_label.setText(f"{orig['K']:.1f} kN/m")
        self.original_vt1_label.setText(f"{orig['V_t1']:.1f} kN")
        self.original_vt2_label.setText(f"{orig['V_t2']:.1f} kN")
        self.original_vt3_label.setText(f"{orig['V_t3']:.1f} kN")
        self.original_vmin_label.setText(f"<b>{orig['V_min']:.1f} kN</b>")
        
        # Stato di progetto
        mod = self.results['modified']
        self.modified_k_label.setText(
            f"{mod['K']:.1f} kN/m (cerch: +{mod['K_cerchiature']:.1f})"
        )
        self.modified_vt1_label.setText(f"{mod['V_t1']:.1f} kN")
        self.modified_vt2_label.setText(f"{mod['V_t2']:.1f} kN")
        self.modified_vt3_label.setText(f"{mod['V_t3']:.1f} kN")
        self.modified_vmin_label.setText(f"<b>{mod['V_min']:.1f} kN</b>")
        
        # Maschi murari
        while self.maschi_layout.count():
            child = self.maschi_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if 'maschi' in self.results:
            for maschio in self.results['maschi']:
                label = QLabel(
                    f"{maschio['id']} - Lunghezza: {maschio['length']} cm "
                    f"({maschio['position']})"
                )
                self.maschi_layout.addWidget(label)
                
        # Dettaglio cerchiature
        while self.cerchiature_layout.count():
            child = self.cerchiature_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        frame_results = self.results.get('frame_results', {})
        openings_module = self.project_data.get('openings_module', {})
        openings_with_reinforcement = openings_module.get('openings', [])
        
        for i, (opening_id, frame_data) in enumerate(frame_results.items()):
            opening = openings_with_reinforcement[i] if i < len(openings_with_reinforcement) else {}
            rinforzo = opening.get('rinforzo', {})
            
            # Crea widget per dettagli cerchiatura
            frame_widget = QGroupBox(f"Apertura {opening_id}")
            frame_layout = QFormLayout()
            
            # Tipo rinforzo
            tipo = rinforzo.get('tipo', 'N.D.')
            frame_layout.addRow("Tipo:", QLabel(tipo))
            
            # Se apertura ad arco, mostra info
            if opening.get('type') == 'Ad arco':
                frame_layout.addRow("Tipo apertura:", QLabel("Ad arco"))
                if 'arch_radius' in frame_data:
                    frame_layout.addRow("Raggio arco:", QLabel(f"{frame_data['arch_radius']:.1f} cm"))
                if 'arch_length' in frame_data:
                    frame_layout.addRow("Lunghezza sviluppata:", QLabel(f"{frame_data['arch_length']:.1f} cm"))
            
            # Materiale e profili
            if rinforzo.get('materiale') == 'acciaio':
                arch = rinforzo.get('architrave', {})
                profilo_text = f"{arch.get('n_profili', 1)}x {arch.get('profilo', 'N.D.')}"
                frame_layout.addRow("Architrave:", QLabel(profilo_text))
                
                # Info calandratura se presente
                if 'bending_info' in frame_data:
                    bend_info = frame_data['bending_info']
                    bend_label = QLabel(bend_info['method'])
                    
                    # Colora in base alla criticità
                    if not bend_info.get('bendable', True):
                        bend_label.setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        if bend_info.get('r_h_ratio', 0) < 30:
                            bend_label.setStyleSheet("color: orange;")
                        else:
                            bend_label.setStyleSheet("color: green;")
                    frame_layout.addRow("Calandrabilità:", bend_label)
                    
                    # Pulsante per dettagli calandratura
                    details_btn = QPushButton("Verifica dettagliata")
                    details_btn.clicked.connect(
                        lambda checked, o=opening, p=arch.get('profilo', ''), 
                        s=rinforzo.get('classe_acciaio', 'S235'): 
                        self.show_bending_verification(o, p, s)
                    )
                    frame_layout.addRow("", details_btn)
                
                if 'piedritti' in rinforzo:
                    pied = rinforzo['piedritti']
                    profilo_text = f"{pied.get('n_profili', 1)}x {pied.get('profilo', 'N.D.')}"
                    frame_layout.addRow("Piedritti:", QLabel(profilo_text))
                    
            # Rigidezza contributo
            k_frame = frame_data.get('K_frame', 0)
            k_label = QLabel(f"{k_frame:.1f} kN/m")
            if k_frame == 0 and frame_data.get('warnings'):
                k_label.setStyleSheet("color: orange; font-weight: bold;")
            frame_layout.addRow("K cerchiatura:", k_label)
            
            # NUOVO: Resistenza contributo
            v_frame = frame_data.get('V_resistance', 0)
            if v_frame > 0:
                v_label = QLabel(f"{v_frame:.1f} kN")
                v_label.setStyleSheet("color: green; font-weight: bold;")
                frame_layout.addRow("V resistenza:", v_label)
            
            # Avvisi
            if frame_data.get('warnings'):
                warning_text = '\n'.join(f"⚠️ {w}" for w in frame_data['warnings'])
                warning_label = QLabel(warning_text)
                warning_label.setStyleSheet("color: orange;")
                warning_label.setWordWrap(True)
                frame_layout.addRow("Avvisi:", warning_label)
            
            # Verifica connessioni se presente
            if 'connections' in frame_data:
                conn = frame_data['connections']
                verifica = "✓ OK" if conn.get('verified', False) else "✗ Non verificato"
                frame_layout.addRow("Verifica ancoraggi:", QLabel(verifica))
                
            frame_widget.setLayout(frame_layout)
            self.cerchiature_layout.addWidget(frame_widget)
    
    def show_bending_verification(self, opening_data, profile_name, steel_grade):
        """Mostra dialog verifica calandratura"""
        dialog = BendingVerificationDialog(self, opening_data, profile_name, steel_grade)
        dialog.exec_()
            
    def generate_notes(self):
        """Genera note e avvertimenti con dettagli avanzati"""
        notes = []
        
        # Fattore di confidenza
        notes.append(f"Fattore di confidenza FC = {self.results['FC']}")
        
        # Verifica intervento locale
        verif = self.results['verification']
        if not verif['is_local']:
            notes.append("\n⚠️ ATTENZIONE: L'intervento NON può essere classificato "
                        "come LOCALE secondo NTC 2018 § 8.4.1")
            
            if not verif['stiffness_ok']:
                notes.append(f"- La variazione di rigidezza ({verif['stiffness_variation']:.1f}%) "
                           f"supera il limite del 15%")
                           
            if not verif['resistance_ok']:
                notes.append(f"- La riduzione di resistenza ({verif['resistance_variation']:.1f}%) "
                           f"supera il limite del 20%")
                           
            notes.append("\nSi consiglia di:\n"
                        "• Aumentare le sezioni delle cerchiature\n"
                        "• Ridurre il numero/dimensione delle aperture\n"
                        "• Valutare un intervento di miglioramento/adeguamento")
        else:
            notes.append("\n✓ L'intervento può essere classificato come LOCALE")
            
        # Resistenza critica
        orig = self.results['original']
        mod = self.results['modified']
        
        # Trova quale resistenza è minima
        resistances = [
            ('V_t1', 'taglio puro'),
            ('V_t2', 'taglio con fattore di forma'),
            ('V_t3', 'presso-flessione')
        ]
        
        for key, desc in resistances:
            if orig[key] == orig['V_min']:
                notes.append(f"\nStato di fatto: resistenza critica per {desc}")
            if mod[key] == mod['V_min']:
                notes.append(f"Stato di progetto: resistenza critica per {desc}")
                
        # Analisi comportamento non lineare
        capacity_params = self.capacity_canvas.analyze_capacity_parameters(self.results)
        
        if capacity_params:
            notes.append("\n📊 COMPORTAMENTO NON LINEARE:")
            
            if 'original_mechanism' in capacity_params:
                notes.append(f"Stato di fatto - Meccanismo: {capacity_params['original_mechanism']}")
                notes.append(f"  Duttilità stimata: μ={capacity_params['original_ductility']:.1f}")
                notes.append(f"  Spostamento al limite elastico: {capacity_params['original_dy']:.1f} mm")
            
            if 'modified_mechanism' in capacity_params:
                notes.append(f"Stato di progetto - Meccanismo: {capacity_params['modified_mechanism']}")
                notes.append(f"  Duttilità stimata: μ={capacity_params['modified_ductility']:.1f}")
                notes.append(f"  Spostamento al limite elastico: {capacity_params['modified_dy']:.1f} mm")
                
                # Confronto duttilità
                if 'original_ductility' in capacity_params:
                    ductility_increase = ((capacity_params['modified_ductility'] - 
                                         capacity_params['original_ductility']) / 
                                        capacity_params['original_ductility'] * 100)
                    if ductility_increase > 0:
                        notes.append(f"  Incremento duttilità: +{ductility_increase:.0f}%")
                
        # Contributo cerchiature
        if mod['K_cerchiature'] > 0:
            contrib_k_percent = (mod['K_cerchiature'] / mod['K']) * 100
            notes.append(f"\nLe cerchiature contribuiscono per il {contrib_k_percent:.1f}% "
                        f"alla rigidezza totale")
                        
        # NUOVO: Contributo resistenza cerchiature
        if mod.get('V_cerchiature', 0) > 0:
            V_cerch = mod['V_cerchiature'] * 0.7  # con fattore collaborazione
            notes.append(f"\nContributo resistenza cerchiature: +{V_cerch:.1f} kN")
            incremento_res = (mod['V_min'] - orig['V_min']) / orig['V_min'] * 100
            notes.append(f"Incremento resistenza totale: +{incremento_res:.1f}%")
                        
        # Analisi tipo di cerchiature
        openings_module = self.project_data.get('openings_module', {})
        openings_with_reinforcement = openings_module.get('openings', [])
        
        n_acciaio = 0
        n_ca = 0
        n_profili_multipli = 0
        n_calandrate = 0
        n_archi = 0
        n_non_calandrabili = 0
        
        for opening in openings_with_reinforcement:
            if opening.get('type') == 'Ad arco':
                n_archi += 1
                
            if 'rinforzo' in opening:
                rinforzo = opening['rinforzo']
                if rinforzo.get('materiale') == 'acciaio':
                    n_acciaio += 1
                    # Conta profili multipli
                    if 'architrave' in rinforzo and rinforzo['architrave'].get('n_profili', 1) > 1:
                        n_profili_multipli += 1
                    # Conta calandrate
                    if 'calandrat' in rinforzo.get('tipo', '').lower() or opening.get('type') == 'Ad arco':
                        n_calandrate += 1
                elif rinforzo.get('materiale') == 'ca':
                    n_ca += 1
        
        # Conta profili non calandrabili
        frame_results = self.results.get('frame_results', {})
        for frame_data in frame_results.values():
            if 'bending_info' in frame_data and not frame_data['bending_info'].get('bendable', True):
                n_non_calandrabili += 1
        
        # Note su aperture ad arco
        if n_archi > 0:
            notes.append(f"\n📐 {n_archi} aperture ad arco rilevate")
            if n_non_calandrabili > 0:
                notes.append(f"  ⚠️ {n_non_calandrabili} profili NON calandrabili con metodo standard")
                notes.append("  Valutare soluzioni alternative:")
                notes.append("  - Profili segmentati saldati")
                notes.append("  - Cambio sezione profilo")
                notes.append("  - Calandratura a caldo specializzata")
                    
        if n_acciaio > 0:
            notes.append(f"\n• {n_acciaio} cerchiature in acciaio")
            if n_profili_multipli > 0:
                notes.append(f"  - {n_profili_multipli} con profili multipli accoppiati")
            if n_calandrate > 0:
                notes.append(f"  - {n_calandrate} cerchiature curve/calandrate")
                notes.append("  📋 Verificare preventivi officine specializzate")
                
        if n_ca > 0:
            notes.append(f"• {n_ca} cerchiature in C.A.")
            notes.append("  Verificare armature minime secondo NTC 2018")
            
        # Analisi avvisi calandratura
        has_bending_warnings = False
        critical_warnings = []
        
        for opening_id, frame_data in frame_results.items():
            if frame_data.get('warnings'):
                has_bending_warnings = True
                for warning in frame_data['warnings']:
                    if 'non calandrabile' in warning.lower():
                        critical_warnings.append(f"{opening_id}: {warning}")
                
        if critical_warnings:
            notes.append("\n🔴 AVVISI CRITICI CALANDRATURA:")
            for warning in critical_warnings:
                notes.append(f"  {warning}")
            
        # Note su vincoli avanzati
        has_advanced_constraints = False
        for opening in openings_with_reinforcement:
            if 'rinforzo' in opening:
                rinforzo = opening['rinforzo']
                if 'vincoli' in rinforzo and 'avanzate' in rinforzo['vincoli']:
                    has_advanced_constraints = True
                    break
                    
        if has_advanced_constraints:
            notes.append("\n⚠️ Sono state utilizzate opzioni di analisi avanzate")
            notes.append("  Verificare l'applicabilità delle ipotesi adottate")
                        
        self.notes_text.setPlainText('\n'.join(notes))
        
    def update_graphs(self):
        """Aggiorna tutti i grafici inclusi quelli avanzati"""
        if not self.results:
            return
            
        # Curve di capacità
        self.capacity_canvas.plot_capacity_curves(self.results)
        
        # Confronto rigidezze
        self.stiffness_canvas.plot_stiffness_comparison(self.results)
        
        # Confronto resistenze
        self.resistance_canvas.plot_resistance_comparison(self.results)
        
        # Dettagli cerchiature
        frame_results = self.results.get('frame_results', {})
        if frame_results:
            self.frames_canvas.plot_frame_details(frame_results)
            
    def show_advanced_details(self):
        """Mostra dialog con dettagli avanzati calcolo"""
        dialog = AdvancedDetailsDialog(self, self.results, self.project_data)
        dialog.exec_()
        
    def get_confidence_factor(self, knowledge_level):
        """Ottiene fattore di confidenza"""
        factors = {
            'LC1 (FC=1.35)': 1.35,
            'LC2 (FC=1.20)': 1.20,
            'LC3 (FC=1.00)': 1.00
        }
        return factors.get(knowledge_level, 1.35)
        
    def calculate_maschi_results(self, wall_data, openings):
        """Calcola risultati per singoli maschi murari"""
        if not openings:
            return
            
        # Ordina aperture per posizione X
        sorted_openings = sorted(openings, key=lambda o: o['x'])
        
        maschi_results = []
        wall_length = wall_data['length']
        
        # Maschio iniziale
        if sorted_openings[0]['x'] > 0:
            maschio = {
                'id': 'M1',
                'length': sorted_openings[0]['x'],
                'position': 'Iniziale'
            }
            maschi_results.append(maschio)
            
        # Maschi intermedi
        for i in range(len(sorted_openings) - 1):
            x1 = sorted_openings[i]['x'] + sorted_openings[i]['width']
            x2 = sorted_openings[i + 1]['x']
            if x2 > x1:
                maschio = {
                    'id': f'M{i + 2}',
                    'length': x2 - x1,
                    'position': f'Tra A{i + 1} e A{i + 2}'
                }
                maschi_results.append(maschio)
                
        # Maschio finale
        last_opening = sorted_openings[-1]
        x_end = last_opening['x'] + last_opening['width']
        if x_end < wall_length:
            maschio = {
                'id': f'M{len(sorted_openings) + 1}',
                'length': wall_length - x_end,
                'position': 'Finale'
            }
            maschi_results.append(maschio)
            
        self.results['maschi'] = maschi_results
        
    def export_results(self):
        """Esporta risultati con dettagli avanzati"""
        if not self.results:
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Esporta Risultati",
            "risultati_calcolo_dettagliato.txt",
            "File di testo (*.txt);;CSV (*.csv);;JSON (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    # Export JSON completo
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.results, f, indent=2, ensure_ascii=False)
                else:
                    # Export testuale dettagliato
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("RISULTATI CALCOLO CERCHIATURE NTC 2018\n")
                        f.write("=" * 70 + "\n\n")
                        
                        # Data e info progetto
                        f.write(f"Data calcolo: {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm:ss')}\n")
                        f.write(f"Progettista: Arch. Michelangelo Bartolotta\n\n")
                        
                        # Verifica
                        verif = self.results['verification']
                        f.write("VERIFICA INTERVENTO LOCALE\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Esito: {'VERIFICATO' if verif['is_local'] else 'NON VERIFICATO'}\n")
                        f.write(f"Variazione rigidezza: {verif['stiffness_variation']:.1f}%\n")
                        f.write(f"Variazione resistenza: {verif['resistance_variation']:.1f}%\n\n")
                        
                        # Stato di fatto
                        orig = self.results['original']
                        f.write("STATO DI FATTO\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Rigidezza K: {orig['K']:.1f} kN/m\n")
                        f.write(f"V_t1 (taglio): {orig['V_t1']:.1f} kN\n")
                        f.write(f"V_t2 (taglio f.f.): {orig['V_t2']:.1f} kN\n")
                        f.write(f"V_t3 (presso-flex): {orig['V_t3']:.1f} kN\n")
                        f.write(f"V_min: {orig['V_min']:.1f} kN\n\n")
                        
                        # Stato di progetto
                        mod = self.results['modified']
                        f.write("STATO DI PROGETTO\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Rigidezza K totale: {mod['K']:.1f} kN/m\n")
                        f.write(f"Rigidezza muratura: {mod['K'] - mod['K_cerchiature']:.1f} kN/m\n")
                        f.write(f"Contributo cerchiature: {mod['K_cerchiature']:.1f} kN/m\n")
                        f.write(f"V_t1 (taglio): {mod['V_t1']:.1f} kN\n")
                        f.write(f"V_t2 (taglio f.f.): {mod['V_t2']:.1f} kN\n")
                        f.write(f"V_t3 (presso-flex): {mod['V_t3']:.1f} kN\n")
                        f.write(f"V_min: {mod['V_min']:.1f} kN\n\n")
                        
                        # Dettaglio cerchiature
                        frame_results = self.results.get('frame_results', {})
                        if frame_results:
                            f.write("DETTAGLIO CERCHIATURE\n")
                            f.write("-" * 30 + "\n")
                            
                            openings_module = self.project_data.get('openings_module', {})
                            openings = openings_module.get('openings', [])
                            
                            for i, (opening_id, frame_data) in enumerate(frame_results.items()):
                                f.write(f"\n{opening_id}:\n")
                                
                                if i < len(openings):
                                    opening = openings[i]
                                    f.write(f"  Tipo apertura: {opening.get('type', 'Rettangolare')}\n")
                                    
                                    if 'rinforzo' in opening:
                                        rinforzo = opening['rinforzo']
                                        f.write(f"  Tipo rinforzo: {rinforzo.get('tipo', 'N.D.')}\n")
                                        f.write(f"  Materiale: {rinforzo.get('materiale', 'N.D.')}\n")
                                        
                                        if rinforzo.get('materiale') == 'acciaio':
                                            arch = rinforzo.get('architrave', {})
                                            f.write(f"  Architrave: {arch.get('n_profili', 1)}x {arch.get('profilo', 'N.D.')}\n")
                                            
                                            if 'piedritti' in rinforzo:
                                                pied = rinforzo['piedritti']
                                                f.write(f"  Piedritti: {pied.get('n_profili', 1)}x {pied.get('profilo', 'N.D.')}\n")
                                    
                                    # Dati apertura ad arco
                                    if opening.get('type') == 'Ad arco':
                                        f.write("\n  PARAMETRI ARCO:\n")
                                        if 'arch_radius' in frame_data:
                                            f.write(f"    Raggio: {frame_data['arch_radius']:.1f} cm\n")
                                        if 'arch_length' in frame_data:
                                            f.write(f"    Lunghezza sviluppata: {frame_data['arch_length']:.1f} cm\n")
                                            
                                        # Info calandratura
                                        if 'bending_info' in frame_data:
                                            bend = frame_data['bending_info']
                                            f.write(f"\n  VERIFICA CALANDRATURA:\n")
                                            f.write(f"    Rapporto r/h: {bend['r_h_ratio']:.1f}\n")
                                            f.write(f"    Metodo: {bend['method']}\n")
                                            f.write(f"    Tensioni residue: {bend['residual_stress']:.0f} MPa\n")
                                            
                                            if bend.get('warnings'):
                                                f.write("    Avvisi:\n")
                                                for warning in bend['warnings']:
                                                    f.write(f"      - {warning}\n")
                                        
                                        # Report calandratura per officina
                                        if opening.get('type') == 'Ad arco' and 'rinforzo' in opening:
                                            report = self.arch_manager.generate_bending_report(
                                                opening, opening['rinforzo']
                                            )
                                            f.write("\n" + report + "\n")
                                                
                                f.write(f"  K_cerchiatura: {frame_data.get('K_frame', 0):.1f} kN/m\n")
                                
                                # NUOVO: Resistenza cerchiatura
                                if frame_data.get('V_resistance', 0) > 0:
                                    f.write(f"  V_resistenza: {frame_data.get('V_resistance', 0):.1f} kN\n")
                                    # Info orientamento profilo
                                    if 'rinforzo' in opening and opening['rinforzo'].get('materiale') == 'acciaio':
                                        arch = opening['rinforzo'].get('architrave', {})
                                        if arch.get('ruotato', False):
                                            f.write("  Nota: Profilo ruotato 90° (asse debole)\n")
                                
                                if frame_data.get('warnings'):
                                    f.write("  Avvertimenti:\n")
                                    for warning in frame_data['warnings']:
                                        f.write(f"    - {warning}\n")
                                
                                if 'connections' in frame_data:
                                    conn = frame_data['connections']
                                    f.write(f"  Verifica ancoraggi: {'OK' if conn.get('verified', False) else 'NON VERIFICATO'}\n")
                                    
                        # Maschi murari
                        if 'maschi' in self.results:
                            f.write("\nMASCHI MURARI\n")
                            f.write("-" * 30 + "\n")
                            for maschio in self.results['maschi']:
                                f.write(f"{maschio['id']}: L = {maschio['length']} cm ({maschio['position']})\n")
                    
                QMessageBox.information(self, "Esportazione completata",
                                      "I risultati sono stati esportati correttamente")
                                      
            except Exception as e:
                import traceback
                print(f"\nERRORE DURANTE L'ESPORTAZIONE:")
                print(traceback.format_exc())
                QMessageBox.critical(self, "Errore",
                                   f"Errore durante l'esportazione:\n{str(e)}")
                                   
    def reset(self):
        """Reset del modulo"""
        self.project_data = {}
        self.results = {}
        self._is_calculating = False  # Reset flag
        
        # Reset etichette
        self.local_check_label.setText("-")
        self.stiffness_var_label.setText("-")
        self.resistance_var_label.setText("-")
        
        self.original_k_label.setText("-")
        self.original_vt1_label.setText("-")
        self.original_vt2_label.setText("-")
        self.original_vt3_label.setText("-")
        self.original_vmin_label.setText("-")
        
        self.modified_k_label.setText("-")
        self.modified_vt1_label.setText("-")
        self.modified_vt2_label.setText("-")
        self.modified_vt3_label.setText("-")
        self.modified_vmin_label.setText("-")
        
        self.notes_text.clear()
        
        # Clear layouts
        for layout in [self.maschi_layout, self.cerchiature_layout]:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
        # Clear graphs
        for canvas in [self.capacity_canvas, self.stiffness_canvas, 
                      self.resistance_canvas, self.frames_canvas]:
            canvas.figure.clear()
            canvas.draw()
        
        self.status_label.setText("In attesa di dati...")
        self.calc_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.advanced_btn.setEnabled(False)


class AdvancedDetailsDialog(QDialog):
    """Dialog per visualizzare dettagli avanzati del calcolo"""
    
    def __init__(self, parent=None, results=None, project_data=None):
        super().__init__(parent)
        self.results = results or {}
        self.project_data = project_data or {}
        self.setWindowTitle("Dettagli Avanzati Calcolo")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget per organizzare i dettagli
        tabs = QTabWidget()
        
        # Tab vincoli
        vincoli_tab = self.create_vincoli_tab()
        tabs.addTab(vincoli_tab, "Vincoli e Modellazione")
        
        # Tab collegamenti
        collegamenti_tab = self.create_collegamenti_tab()
        tabs.addTab(collegamenti_tab, "Collegamenti e Giunzioni")
        
        # Tab verifiche locali
        verifiche_tab = self.create_verifiche_tab()
        tabs.addTab(verifiche_tab, "Verifiche Locali")
        
        # Nuovo: Tab calandratura
        calandratura_tab = self.create_calandratura_tab()
        tabs.addTab(calandratura_tab, "Calandratura Profili")
        
        layout.addWidget(tabs)
        
        # Pulsanti
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def create_vincoli_tab(self):
        """Crea tab con dettagli vincoli"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Analizza vincoli per ogni apertura
        openings_module = self.project_data.get('openings_module', {})
        openings = openings_module.get('openings', [])
        
        for i, opening in enumerate(openings):
            if 'rinforzo' in opening and 'vincoli' in opening['rinforzo']:
                group = QGroupBox(f"Apertura A{i+1}")
                group_layout = QFormLayout()
                
                vincoli = opening['rinforzo']['vincoli']
                
                # Vincoli base
                if 'base_sx' in vincoli:
                    group_layout.addRow("Base SX:", QLabel(vincoli['base_sx'].get('tipo', 'N.D.')))
                if 'base_dx' in vincoli:
                    group_layout.addRow("Base DX:", QLabel(vincoli['base_dx'].get('tipo', 'N.D.')))
                    
                # Vincoli nodi
                if 'nodo_sx' in vincoli:
                    group_layout.addRow("Nodo SX:", QLabel(vincoli['nodo_sx'].get('tipo', 'N.D.')))
                if 'nodo_dx' in vincoli:
                    group_layout.addRow("Nodo DX:", QLabel(vincoli['nodo_dx'].get('tipo', 'N.D.')))
                    
                # Opzioni avanzate
                if 'avanzate' in vincoli:
                    av = vincoli['avanzate']
                    if av.get('secondo_ordine'):
                        group_layout.addRow("", QLabel("✓ Effetti II ordine"))
                    if av.get('non_linearita'):
                        group_layout.addRow("", QLabel("✓ Non linearità geometrica"))
                        
                group.setLayout(group_layout)
                content_layout.addWidget(group)
                
        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
        
    def create_collegamenti_tab(self):
        """Crea tab con dettagli collegamenti"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        
        # Genera report testuale
        report = []
        frame_results = self.results.get('frame_results', {})
        
        for opening_id, frame_data in frame_results.items():
            report.append(f"\n{opening_id}:")
            
            if 'connections' in frame_data:
                conn = frame_data['connections']
                report.append(f"  Verifica ancoraggi: {'OK' if conn.get('verified') else 'NON VERIFICATO'}")
                
                if 'anchor_force' in conn:
                    report.append(f"  Forza max ancoraggio: {conn['anchor_force']:.1f} kN")
                if 'safety_factor' in conn:
                    report.append(f"  Coefficiente sicurezza: {conn['safety_factor']:.2f}")
                    
        text.setPlainText('\n'.join(report))
        layout.addWidget(text)
        
        widget.setLayout(layout)
        return widget
        
    def create_verifiche_tab(self):
        """Crea tab con verifiche locali dettagliate"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tabella verifiche
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Elemento", "Sollecitazione", "Resistenza", "Verifica"])
        
        # Popola con dati esempio
        frame_results = self.results.get('frame_results', {})
        row = 0
        
        for opening_id, frame_data in frame_results.items():
            if 'verifications' in frame_data:
                for verif_type, verif_data in frame_data['verifications'].items():
                    table.insertRow(row)
                    table.setItem(row, 0, QTableWidgetItem(opening_id))
                    table.setItem(row, 1, QTableWidgetItem(verif_type))
                    table.setItem(row, 2, QTableWidgetItem(f"{verif_data.get('demand', 0):.1f}"))
                    table.setItem(row, 3, QTableWidgetItem(f"{verif_data.get('capacity', 0):.1f}"))
                    row += 1
                    
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
        
    def create_calandratura_tab(self):
        """Crea tab con dettagli calandratura"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Analizza aperture con calandratura
        frame_results = self.results.get('frame_results', {})
        openings_module = self.project_data.get('openings_module', {})
        openings = openings_module.get('openings', [])
        
        has_curved = False
        
        for i, (opening_id, frame_data) in enumerate(frame_results.items()):
            if i >= len(openings):
                continue
                
            opening = openings[i]
            
            # Verifica se è ad arco o calandrata
            if opening.get('type') == 'Ad arco' or 'bending_info' in frame_data:
                has_curved = True
                
                group = QGroupBox(f"Apertura {opening_id}")
                group_layout = QFormLayout()
                
                # Info apertura
                group_layout.addRow("Tipo:", QLabel(opening.get('type', 'Rettangolare')))
                
                if 'arch_radius' in frame_data:
                    group_layout.addRow("Raggio arco:", 
                                      QLabel(f"{frame_data['arch_radius']:.1f} cm"))
                if 'arch_length' in frame_data:
                    group_layout.addRow("Lunghezza sviluppata:", 
                                      QLabel(f"{frame_data['arch_length']:.1f} cm"))
                
                # Info calandratura
                if 'bending_info' in frame_data:
                    bend = frame_data['bending_info']
                    
                    # Rapporto r/h con colore
                    rh_label = QLabel(f"{bend['r_h_ratio']:.1f}")
                    if bend['r_h_ratio'] < 15:
                        rh_label.setStyleSheet("color: red; font-weight: bold;")
                    elif bend['r_h_ratio'] < 30:
                        rh_label.setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        rh_label.setStyleSheet("color: green; font-weight: bold;")
                    group_layout.addRow("Rapporto r/h:", rh_label)
                    
                    group_layout.addRow("Metodo:", QLabel(bend['method']))
                    group_layout.addRow("Tensioni residue:", 
                                      QLabel(f"{bend['residual_stress']:.0f} MPa"))
                    
                    # Calandrabile o no
                    if not bend.get('bendable', True):
                        status_label = QLabel("⚠️ NON CALANDRABILE CON METODI STANDARD")
                        status_label.setStyleSheet("color: red; font-weight: bold;")
                        group_layout.addRow("Stato:", status_label)
                    
                    # Avvisi
                    if bend.get('warnings'):
                        warnings_text = '\n'.join(bend['warnings'])
                        warnings_label = QLabel(warnings_text)
                        warnings_label.setStyleSheet("color: red;")
                        warnings_label.setWordWrap(True)
                        group_layout.addRow("Avvisi:", warnings_label)
                
                # Avvisi aggiuntivi dal frame
                if frame_data.get('warnings'):
                    frame_warnings = '\n'.join(f"⚠️ {w}" for w in frame_data['warnings'])
                    frame_warnings_label = QLabel(frame_warnings)
                    frame_warnings_label.setStyleSheet("color: orange;")
                    frame_warnings_label.setWordWrap(True)
                    group_layout.addRow("Note calcolo:", frame_warnings_label)
                        
                group.setLayout(group_layout)
                content_layout.addWidget(group)
                
        if not has_curved:
            label = QLabel("Nessuna apertura con calandratura rilevata")
            label.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(label)
            
        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget