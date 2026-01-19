"""
Modulo Calcolo e Verifica
Esegue i calcoli secondo NTC 2018 e mostra i risultati
Versione aggiornata con supporto profili multipli, vincoli avanzati e aperture ad arco
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import asdict
import json

# Import refactoring
from src.gui.formatters.result_formatter import ResultFormatter
from src.gui.widgets.results_canvas import ResultsCanvas
from src.gui.dialogs.advanced_details_dialog import AdvancedDetailsDialog
from src.services.calculation_service import CalculationService

# Import del motore di calcolo (necessari per BendingVerificationDialog e costanti)
try:
    from src.core.engine.arch_reinforcement import (
        ArchReinforcementManager, 
        BendingVerificationDialog
    )
    # Altri import potrebbero non servire se si usa solo CalculationService,
    # ma BendingVerificationDialog è usato direttamente nella UI

    print(">>> USANDO CORE ENGINE COMPLETO - MODULI CARICATI CORRETTAMENTE")
    
except ImportError as e:
    print(f"ERRORE CRITICO: Moduli di calcolo non trovati - {e}")
    raise Exception("IMPOSSIBILE CARICARE I MODULI CORE - VERIFICARE INSTALLAZIONE")

# Configurazione logging
logger = logging.getLogger(__name__)


class CalcModule(QWidget):
    """Modulo calcolo e verifica con supporto funzionalità avanzate"""
    
    calculation_done = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.project_data = {}
        self.results = {}
        self._is_calculating = False
        
        # Service
        self.calc_service = CalculationService()
        
        self.setup_ui()
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
        
    def run_calculation(self):
        """Esegue il calcolo completo utilizzando il Service Layer"""
        if self._is_calculating:
            logger.warning("Calcolo già in corso - richiesta ignorata")
            return
            
        if not self.project_data:
            QMessageBox.warning(self, "Attenzione", 
                              "Nessun dato di progetto disponibile")
            return
            
        self._is_calculating = True
        
        try:
            self.status_label.setText("Calcolo in corso...")
            QApplication.processEvents()
            
            # Esegui calcolo tramite servizio
            calc_result = self.calc_service.calculate(self.project_data)
            
            if not calc_result.is_valid:
                error_msg = "; ".join(calc_result.errors)
                raise Exception(error_msg)
            
            # Mappatura risultati dal service al formato GUI
            self.results = {
                'original': asdict(calc_result.original),
                'modified': {
                    'K': calc_result.K_total_modified,
                    'V_t1': calc_result.modified.V_t1,
                    'V_t2': calc_result.modified.V_t2,
                    'V_t3': calc_result.modified.V_t3,
                    'V_min': calc_result.V_total_modified,
                    'K_cerchiature': calc_result.K_frames,
                    'V_cerchiature': calc_result.V_frames
                },
                'verification': asdict(calc_result.verification),
                'FC': calc_result.FC,
                'frame_results': calc_result.frame_results
            }
            
            # Calcola risultati per maschi murari (non gestito dal service)
            openings_module = self.project_data.get('openings_module', {})
            openings_with_reinforcement = openings_module.get('openings', [])
            self.calculate_maschi_results(self.project_data.get('wall', {}), openings_with_reinforcement)
            
            # Aggiorna interfaccia
            self.update_results_display()
            self.generate_notes()
            self.update_graphs()
            
            self.status_label.setText("Calcolo completato")
            self.export_btn.setEnabled(True)
            self.advanced_btn.setEnabled(True)
            
            self.calculation_done.emit(self.results)
            
        except Exception as e:
            import traceback
            print(f"\nERRORE NEL CALCOLO:")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Errore", 
                               f"Errore durante il calcolo:\n{str(e)}")
            self.status_label.setText("Errore nel calcolo")
            
        finally:
            self._is_calculating = False
            
    def update_results_display(self):
        """Aggiorna visualizzazione risultati con dettagli cerchiature"""
        if not self.results:
            return
            
        # Verifica intervento locale
        verif = self.results['verification']
        self.local_check_label.setText(
            ResultFormatter.format_verification_label(verif['is_local'])
        )
            
        # Variazioni
        stiff_var = verif['stiffness_variation']
        limit_K = verif.get('stiffness_variation_limit', 15)
        self.stiffness_var_label.setText(
            ResultFormatter.format_variation(stiff_var, limit_K, verif['stiffness_ok'], is_stiffness=True)
        )
            
        res_var = verif['resistance_variation']
        limit_V = verif.get('resistance_variation_limit', 20)
        self.resistance_var_label.setText(
            ResultFormatter.format_variation(res_var, limit_V, verif['resistance_ok'], is_stiffness=False)
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
        k_masonry = mod['K'] - mod.get('K_cerchiature', 0)
        self.modified_k_label.setText(
            ResultFormatter.format_stiffness_label(k_masonry, mod.get('K_cerchiature', 0))
        )
        self.modified_vt1_label.setText(f"{mod['V_t1']:.1f} kN")
        self.modified_vt2_label.setText(f"{mod['V_t2']:.1f} kN")
        self.modified_vt3_label.setText(f"{mod['V_t3']:.1f} kN")
        self.modified_vmin_label.setText(f"<b>{mod['V_min']:.1f} kN</b>")
        
        # Maschi murari e Dettaglio cerchiature (UI code kept here)
        self._update_maschi_ui()
        self._update_frames_ui()

    def _update_maschi_ui(self):
        """Aggiorna UI maschi murari"""
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

    def _update_frames_ui(self):
        """Aggiorna UI cerchiature"""
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
        notes_text = ResultFormatter.generate_notes(self.results, self.project_data)
        self.notes_text.setPlainText(notes_text)
        
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
        
    def calculate_maschi_results(self, wall_data, openings):
        """Calcola risultati per singoli maschi murari"""
        if not openings:
            return
            
        # Ordina aperture per posizione X
        sorted_openings = sorted(openings, key=lambda o: o['x'])
        
        maschi_results = []
        wall_length = wall_data.get('length', 0)
        
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
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.results, f, indent=2, ensure_ascii=False)
                else:
                    text = ResultFormatter.generate_export_text(self.results, self.project_data)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(text)
                        
                QMessageBox.information(self, "Esportazione completata",
                                      "I risultati sono stati esportati correttamente")
                                      
            except Exception as e:
                logger.error(f"Errore export: {e}")
                QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione:\n{str(e)}")

    def reset(self):
        """Reset del modulo"""
        self.project_data = {}
        self.results = {}
        self._is_calculating = False
        
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
