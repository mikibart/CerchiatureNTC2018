"""
Finestra principale applicazione
Calcolatore Cerchiature NTC 2018
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import json
import logging

logger = logging.getLogger(__name__)

# Import dei moduli
try:
    from src.gui.modules.input_module import InputModule
except ImportError as e:
    logger.warning(f"InputModule non trovato: {e}")
    InputModule = None

try:
    from src.gui.modules.openings_module import OpeningsModule
except ImportError as e:
    logger.warning(f"OpeningsModule non trovato: {e}")
    OpeningsModule = None

try:
    from src.gui.modules.calc_module import CalcModule
except ImportError as e:
    logger.warning(f"CalcModule non trovato: {e}")
    CalcModule = None

try:
    from src.gui.modules.report_module import ReportModule
except ImportError as e:
    logger.warning(f"ReportModule non trovato: {e}")
    ReportModule = None

try:
    from src.gui.modules.enhanced_report_module import EnhancedReportModule
    ENHANCED_REPORT_AVAILABLE = True
except ImportError as e:
    ENHANCED_REPORT_AVAILABLE = False
    logger.info(f"EnhancedReportModule non disponibile: {e}")

class MainWindow(QMainWindow):
    """Finestra principale con gestione moduli"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calcolatore Cerchiature NTC 2018 - Arch. M. Bartolotta")
        self.setGeometry(100, 100, 1200, 800)
        
        # Centra la finestra
        self.center_window()
        
        # Dati progetto condivisi tra moduli
        self.project_data = {}
        self.current_file = None
        self.is_modified = False
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        
    def center_window(self):
        """Centra la finestra sullo schermo"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def setup_ui(self):
        """Configura interfaccia con tabs"""
        # Widget centrale con tab
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.setCentralWidget(self.tabs)
        
        # Stile per i tab
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
        """)
        
        # Modulo input struttura
        if InputModule:
            self.input_module = InputModule()
            self.input_module.data_changed.connect(self.on_data_changed)
            self.tabs.addTab(self.input_module, "📐 Struttura")
        else:
            self.tabs.addTab(QLabel("Errore caricamento modulo"), "Struttura")
        
        # Modulo aperture
        if OpeningsModule:
            self.openings_module = OpeningsModule()
            self.openings_module.data_changed.connect(self.on_data_changed)
            self.tabs.addTab(self.openings_module, "🔧 Aperture")
        else:
            # Placeholder se modulo non disponibile
            openings_placeholder = QWidget()
            openings_layout = QVBoxLayout()
            openings_label = QLabel(
                "<h2>Modulo Aperture e Rinforzi</h2>"
                "<p>Errore nel caricamento del modulo.</p>"
            )
            openings_label.setWordWrap(True)
            openings_label.setMargin(20)
            openings_layout.addWidget(openings_label)
            openings_layout.addStretch()
            openings_placeholder.setLayout(openings_layout)
            self.tabs.addTab(openings_placeholder, "🔧 Aperture")
        
        # Modulo calcolo
        if CalcModule:
            self.calc_module = CalcModule()
            self.calc_module.calculation_done.connect(self.on_calculation_done)
            self.tabs.addTab(self.calc_module, "🧮 Calcolo")
        else:
            calc_placeholder = QWidget()
            calc_layout = QVBoxLayout()
            calc_label = QLabel(
                "<h2>Modulo Calcolo e Verifica</h2>"
                "<p>Errore nel caricamento del modulo.</p>"
            )
            calc_label.setWordWrap(True)
            calc_label.setMargin(20)
            calc_layout.addWidget(calc_label)
            calc_layout.addStretch()
            calc_placeholder.setLayout(calc_layout)
            self.tabs.addTab(calc_placeholder, "🧮 Calcolo")
        
        # Modulo relazione standard
        if ReportModule:
            self.report_module = ReportModule()
            self.report_module.data_changed.connect(self.on_data_changed)
            self.tabs.addTab(self.report_module, "📄 Relazione")
        else:
            # Placeholder se modulo non disponibile
            report_placeholder = QWidget()
            report_layout = QVBoxLayout()
            report_label = QLabel(
                "<h2>Modulo Generazione Relazione</h2>"
                "<p>Errore nel caricamento del modulo.</p>"
            )
            report_label.setWordWrap(True)
            report_label.setMargin(20)
            report_layout.addWidget(report_label)
            report_layout.addStretch()
            report_placeholder.setLayout(report_layout)
            self.tabs.addTab(report_placeholder, "📄 Relazione")
            
        # Modulo relazione avanzata
        if ENHANCED_REPORT_AVAILABLE:
            self.enhanced_report_module = EnhancedReportModule()
            self.enhanced_report_module.data_changed.connect(self.on_data_changed)
            self.tabs.addTab(self.enhanced_report_module, "📄 Relazione Completa")
        else:
            # Placeholder se modulo non disponibile
            enhanced_report_placeholder = QWidget()
            enhanced_report_layout = QVBoxLayout()
            enhanced_report_label = QLabel(
                "<h2>Modulo Relazione Avanzata</h2>"
                "<p>Per utilizzare questo modulo installare:</p>"
                "<pre>pip install python-docx matplotlib</pre>"
                "<p>Questo modulo genera relazioni complete con:</p>"
                "<ul>"
                "<li>Formule dettagliate e procedure di calcolo</li>"
                "<li>Disegni tecnici stato di fatto/progetto</li>"
                "<li>Diagrammi comparativi</li>"
                "<li>Tabelle riassuntive</li>"
                "</ul>"
            )
            enhanced_report_label.setWordWrap(True)
            enhanced_report_label.setTextFormat(Qt.RichText)
            enhanced_report_label.setMargin(20)
            enhanced_report_layout.addWidget(enhanced_report_label)
            enhanced_report_layout.addStretch()
            enhanced_report_placeholder.setLayout(enhanced_report_layout)
            self.tabs.addTab(enhanced_report_placeholder, "📄 Relazione Completa")
        
        # Connetti il cambio tab
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Sincronizza dati tra moduli
        self.sync_modules_data()
        
    def sync_modules_data(self):
        """Sincronizza i dati tra i moduli"""
        # Quando cambiano i dati nel modulo input, aggiorna modulo aperture
        if hasattr(self, 'input_module') and hasattr(self, 'openings_module'):
            # Passa dati iniziali del muro al modulo aperture
            wall_data = self.input_module.collect_data().get('wall')
            if wall_data:
                self.openings_module.set_wall_data(wall_data)
                
            # Passa aperture esistenti
            openings = self.input_module.collect_data().get('openings', [])
            self.openings_module.set_openings(openings)
            
    def setup_menu(self):
        """Configura menu applicazione"""
        menubar = self.menuBar()
        
        # Menu File
        file_menu = menubar.addMenu('&File')
        
        new_action = QAction(QIcon.fromTheme('document-new'), '&Nuovo Progetto', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('Crea un nuovo progetto')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction(QIcon.fromTheme('document-open'), '&Apri Progetto...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Apri un progetto esistente')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        # Importa da ACCA
        import_acca_action = QAction('&Importa da ACCA (.iEM)...', self)
        import_acca_action.setShortcut('Ctrl+I')
        import_acca_action.setStatusTip('Importa progetto da file ACCA Calcolus-Cerchiatura')
        import_acca_action.triggered.connect(self.import_acca_project)
        file_menu.addAction(import_acca_action)

        file_menu.addSeparator()

        save_action = QAction(QIcon.fromTheme('document-save'), '&Salva Progetto', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Salva il progetto corrente')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction(QIcon.fromTheme('document-save-as'), 'Salva con &nome...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.setStatusTip('Salva il progetto con un nuovo nome')
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Menu progetti recenti
        self.recent_menu = file_menu.addMenu('Progetti &recenti')
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu('&Esporta')
        
        export_excel = QAction('Esporta in Excel...', self)
        export_excel.setStatusTip('Esporta dati in formato Excel')
        export_menu.addAction(export_excel)
        
        export_dxf = QAction('Esporta geometria DXF...', self)
        export_dxf.setStatusTip('Esporta geometria in formato DXF')
        export_menu.addAction(export_dxf)
        
        file_menu.addSeparator()
        
        exit_action = QAction(QIcon.fromTheme('application-exit'), '&Esci', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Esci dall\'applicazione')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Modifica
        edit_menu = menubar.addMenu('&Modifica')
        
        undo_action = QAction(QIcon.fromTheme('edit-undo'), '&Annulla', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(QIcon.fromTheme('edit-redo'), '&Ripeti', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction(QIcon.fromTheme('edit-copy'), '&Copia', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.setEnabled(False)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction(QIcon.fromTheme('edit-paste'), '&Incolla', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.setEnabled(False)
        edit_menu.addAction(paste_action)
        
        # Menu Visualizza
        view_menu = menubar.addMenu('&Visualizza')
        
        zoom_in_action = QAction('Zoom &avanti', self)
        zoom_in_action.setShortcut('Ctrl++')
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &indietro', self)
        zoom_out_action.setShortcut('Ctrl+-')
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction('&Adatta alla finestra', self)
        zoom_fit_action.setShortcut('Ctrl+0')
        view_menu.addAction(zoom_fit_action)
        
        # Menu Strumenti
        tools_menu = menubar.addMenu('&Strumenti')
        
        materials_action = QAction('&Database Materiali...', self)
        materials_action.setStatusTip('Gestisci database materiali')
        materials_action.triggered.connect(self.show_materials_dialog)
        tools_menu.addAction(materials_action)
        
        profiles_action = QAction('Database &Profili...', self)
        profiles_action.setStatusTip('Gestisci database profili metallici')
        profiles_action.triggered.connect(self.show_profiles_dialog)
        tools_menu.addAction(profiles_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction('&Impostazioni...', self)
        settings_action.setStatusTip('Configura impostazioni applicazione')
        settings_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(settings_action)
        
        # Menu Aiuto
        help_menu = menubar.addMenu('&Aiuto')
        
        manual_action = QAction(QIcon.fromTheme('help-contents'), '&Manuale Utente', self)
        manual_action.setShortcut('F1')
        manual_action.setStatusTip('Apri il manuale utente')
        manual_action.triggered.connect(self.show_manual)
        help_menu.addAction(manual_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(QIcon.fromTheme('help-about'), '&Informazioni', self)
        about_action.setStatusTip('Informazioni sul programma')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        about_qt_action = QAction('Informazioni su &Qt', self)
        about_qt_action.setStatusTip('Informazioni su Qt')
        about_qt_action.triggered.connect(QApplication.aboutQt)
        help_menu.addAction(about_qt_action)
        
    def setup_toolbar(self):
        """Configura toolbar"""
        toolbar = self.addToolBar('Principale')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)
        
        # Azioni toolbar
        new_action = QAction(
            self.style().standardIcon(QStyle.SP_FileDialogNewFolder), 
            'Nuovo', self
        )
        new_action.setStatusTip('Crea nuovo progetto')
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        open_action = QAction(
            self.style().standardIcon(QStyle.SP_DirOpenIcon),
            'Apri', self
        )
        open_action.setStatusTip('Apri progetto esistente')
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        save_action = QAction(
            self.style().standardIcon(QStyle.SP_DialogSaveButton),
            'Salva', self
        )
        save_action.setStatusTip('Salva progetto corrente')
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Pulsante calcola
        self.calc_action = QAction(
            self.style().standardIcon(QStyle.SP_ComputerIcon),
            'Calcola', self
        )
        self.calc_action.setStatusTip('Esegui calcoli')
        self.calc_action.triggered.connect(self.run_calculation)
        toolbar.addAction(self.calc_action)
        
        # Pulsante relazione
        self.report_action = QAction(
            self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            'Relazione', self
        )
        self.report_action.setStatusTip('Genera relazione di calcolo')
        self.report_action.setEnabled(False)
        self.report_action.triggered.connect(self.generate_report)
        toolbar.addAction(self.report_action)
        
        # Spacer per allineare a destra
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Info progetto nella toolbar
        self.project_info_label = QLabel("Nuovo progetto")
        self.project_info_label.setStyleSheet("padding: 0 10px;")
        toolbar.addWidget(self.project_info_label)
        
    def setup_statusbar(self):
        """Configura status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto")
        
        # Widget permanenti nella status bar
        self.coord_label = QLabel("X: 0, Y: 0")
        self.coord_label.setMinimumWidth(100)
        self.status_bar.addPermanentWidget(self.coord_label)
        
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setMinimumWidth(80)
        self.status_bar.addPermanentWidget(self.zoom_label)
        
    def on_data_changed(self):
        """Chiamato quando i dati cambiano"""
        self.is_modified = True
        self.update_title()
        
        # Sincronizza dati tra moduli quando cambiano
        if self.tabs.currentIndex() == 0:  # Tab struttura
            self.sync_modules_data()
            
    def on_tab_changed(self, index):
        """Chiamato quando si cambia tab"""
        tab_names = ["Struttura", "Aperture", "Calcolo", "Relazione", "Relazione Completa"]
        if index < len(tab_names):
            self.status_bar.showMessage(f"Modulo attivo: {tab_names[index]}")
            
        # Sincronizza dati quando si passa al modulo aperture
        if index == 1 and hasattr(self, 'input_module') and hasattr(self, 'openings_module'):
            wall_data = self.input_module.collect_data().get('wall')
            if wall_data:
                self.openings_module.set_wall_data(wall_data)
                
            # Sincronizza aperture dal modulo input al modulo aperture
            openings = self.input_module.collect_data().get('openings', [])
            self.openings_module.set_openings(openings)
            
        # Passa dati al modulo calcolo quando si attiva
        elif index == 2 and hasattr(self, 'calc_module'):
            self.update_calc_module_data()
            
        # Passa dati al modulo relazione quando si attiva
        elif index == 3 and hasattr(self, 'report_module') and self.report_module:
            self.update_report_module_data()
            # Se ci sono risultati di calcolo, passali anche quelli
            if hasattr(self, 'calc_module') and hasattr(self.calc_module, 'results'):
                self.report_module.set_results(self.calc_module.results)
                
        # Passa dati al modulo relazione avanzata quando si attiva
        elif index == 4 and hasattr(self, 'enhanced_report_module') and self.enhanced_report_module:
            self.update_enhanced_report_module_data()
            
    def new_project(self):
        """Crea nuovo progetto"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Nuovo Progetto',
                'Il progetto corrente ha modifiche non salvate.\n'
                'Vuoi salvare prima di creare un nuovo progetto?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        # Reset tutti i moduli
        if hasattr(self, 'input_module') and self.input_module:
            self.input_module.reset()
        if hasattr(self, 'openings_module') and self.openings_module:
            self.openings_module.reset()
        if hasattr(self, 'calc_module') and self.calc_module:
            self.calc_module.reset()
        if hasattr(self, 'report_module') and self.report_module:
            self.report_module.reset()
        if hasattr(self, 'enhanced_report_module') and self.enhanced_report_module:
            self.enhanced_report_module.project_data = {}
            self.enhanced_report_module.results = {}
            self.enhanced_report_module.generator.set_data({}, {})
            self.enhanced_report_module.preview_text.clear()
        
        # Reset stato
        self.project_data = {}
        self.current_file = None
        self.is_modified = False
        self.update_title()
        
        self.status_bar.showMessage("Nuovo progetto creato", 3000)
        
    def open_project(self):
        """Apri progetto esistente"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Apri Progetto',
                'Il progetto corrente ha modifiche non salvate.\n'
                'Vuoi salvare prima di aprire un altro progetto?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Apri Progetto",
            os.path.join(os.path.expanduser("~"), "projects"),
            "File Cerchiature (*.cerch);;JSON (*.json);;Tutti i file (*.*)"
        )
        
        if filename:
            self.load_project_file(filename)
            
    def load_project_file(self, filename):
        """Carica un file progetto"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Carica i dati nei moduli
            if hasattr(self, 'input_module') and self.input_module:
                self.input_module.load_data(data)
                
            if hasattr(self, 'openings_module') and self.openings_module:
                # Le aperture con rinforzi sono nel modulo aperture
                openings_data = data.get('openings_module', {})
                self.openings_module.load_data(openings_data)
                
            if hasattr(self, 'report_module') and self.report_module:
                report_data = data.get('report_module', {})
                self.report_module.load_data(report_data)
            
            # Aggiorna stato
            self.project_data = data
            self.current_file = filename
            self.is_modified = False
            self.update_title()
            self.add_to_recent(filename)
            
            self.status_bar.showMessage(f"Progetto caricato: {os.path.basename(filename)}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self, "Errore",
                f"Errore nel caricamento del file:\n{str(e)}"
            )

    def import_acca_project(self):
        """Importa progetto da file ACCA iEM"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Importa Progetto ACCA',
                'Il progetto corrente ha modifiche non salvate.\n'
                'Vuoi salvare prima di importare un altro progetto?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return

        filename, _ = QFileDialog.getOpenFileName(
            self, "Importa Progetto ACCA",
            "",
            "File ACCA iEM (*.iEM);;Tutti i file (*.*)"
        )

        if filename:
            self.load_acca_file(filename)

    def load_acca_file(self, filename):
        """Carica un file ACCA iEM"""
        try:
            # Importa modulo ACCA
            import sys
            if 'src' not in sys.path:
                sys.path.insert(0, 'src')
            from file_io.acca_importer import import_acca_file

            # Mostra dialogo di progresso
            progress = QProgressDialog("Importazione in corso...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Importazione ACCA")
            progress.show()
            QApplication.processEvents()

            # Importa il progetto
            project = import_acca_file(filename)

            progress.close()

            if project:
                # Mostra riepilogo importazione
                summary = project.get_summary()
                msg = f"""
<h3>Importazione completata</h3>
<p><b>Progetto:</b> {summary.get('name', 'N/D')}</p>
<p><b>Localizzazione:</b> {summary.get('location', 'N/D')}</p>
<p><b>Aperture:</b> {summary.get('num_openings', 0)}</p>
<p><b>Dimensioni muro:</b> {summary.get('wall_dimensions', 'N/D')}</p>
"""
                if project.verification_results:
                    msg += f"""
<p><b>Verifiche:</b> {'Tutte OK' if summary.get('all_verified') else 'Alcune non verificate'}</p>
<p><b>CS minimo:</b> {summary.get('min_safety_factor', 'N/D'):.2f}</p>
"""
                QMessageBox.information(self, "Importazione ACCA", msg)

                # Converti in formato interno e carica nei moduli
                self.load_imported_project(project)

                # Aggiorna stato
                self.current_file = None  # File importato, non salvato
                self.is_modified = True
                self.update_title()

                self.status_bar.showMessage(
                    f"Progetto importato da ACCA: {os.path.basename(filename)}", 5000
                )
            else:
                QMessageBox.warning(
                    self, "Errore Importazione",
                    "Impossibile importare il file ACCA.\n"
                    "Verifica che il file sia un database iEM valido."
                )

        except ImportError as e:
            QMessageBox.critical(
                self, "Errore",
                f"Modulo di importazione non disponibile:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Errore",
                f"Errore durante l'importazione:\n{str(e)}"
            )

    def load_imported_project(self, project):
        """Carica un progetto importato nei moduli GUI"""
        try:
            # Converti dati del muro
            if project.wall and hasattr(self, 'input_module') and self.input_module:
                wall_data = {
                    'length': project.wall.length,
                    'height': project.wall.height,
                    'thickness': project.wall.thickness,
                    'knowledge_level': project.wall.knowledge_level.value if hasattr(project.wall.knowledge_level, 'value') else 'LC1'
                }
                # Prova a caricare i dati nel modulo input
                try:
                    self.input_module.load_wall_data(wall_data)
                except AttributeError:
                    # Se il metodo non esiste, prova con load_data
                    data = {'wall': wall_data}
                    self.input_module.load_data(data)

            # Converti aperture
            if project.openings and hasattr(self, 'openings_module') and self.openings_module:
                openings_data = []
                for op in project.openings:
                    op_dict = {
                        'width': op.geometry.width,
                        'height': op.geometry.height,
                        'x': op.geometry.dist_left,
                        'y': op.geometry.dist_base,
                        'is_door': op.is_door,
                        'frame_type': op.frame_type.value if hasattr(op.frame_type, 'value') else 1,
                        'profiles': {
                            'lintel': op.profiles.lintel_profile_id,
                            'jamb': op.profiles.jamb_profile_id,
                            'base': op.profiles.base_profile_id
                        }
                    }
                    openings_data.append(op_dict)

                try:
                    self.openings_module.set_openings(openings_data)
                except Exception as e:
                    logger.warning(f"Errore caricamento aperture: {e}")

            # Salva dati completi del progetto importato
            self.project_data = project.to_dict()
            self.project_data['imported_from_acca'] = True

        except Exception as e:
            logger.exception(f"Errore caricamento progetto importato: {e}")

    def save_project(self):
        """Salva progetto"""
        if not self.current_file:
            return self.save_project_as()
            
        return self.save_project_file(self.current_file)
        
    def save_project_as(self):
        """Salva progetto con nome"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salva Progetto",
            os.path.join(os.path.expanduser("~"), "projects", "progetto.cerch"),
            "File Cerchiature (*.cerch);;JSON (*.json)"
        )
        
        if filename:
            # Assicura estensione corretta
            if not filename.endswith(('.cerch', '.json')):
                filename += '.cerch'
                
            return self.save_project_file(filename)
            
        return False
        
    def save_project_file(self, filename):
        """Salva progetto su file"""
        try:
            # Raccogli dati da tutti i moduli
            if hasattr(self, 'input_module') and self.input_module:
                self.project_data = self.input_module.collect_data()
                
            # Aggiungi dati del modulo aperture
            if hasattr(self, 'openings_module') and self.openings_module:
                self.project_data['openings_module'] = self.openings_module.collect_data()
                
            # Aggiungi dati del modulo relazione
            if hasattr(self, 'report_module') and self.report_module:
                self.project_data['report_module'] = self.report_module.collect_data()
            
            # Salva su file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)
                
            # Aggiorna stato
            self.current_file = filename
            self.is_modified = False
            self.update_title()
            self.add_to_recent(filename)
            
            self.status_bar.showMessage(f"Progetto salvato: {os.path.basename(filename)}", 3000)
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self, "Errore",
                f"Errore nel salvataggio del file:\n{str(e)}"
            )
            return False
            
    def update_title(self):
        """Aggiorna titolo finestra"""
        title = "Calcolatore Cerchiature NTC 2018 - Arch. M. Bartolotta"
        
        if self.current_file:
            title = f"{os.path.basename(self.current_file)} - {title}"
            self.project_info_label.setText(os.path.basename(self.current_file))
        else:
            self.project_info_label.setText("Nuovo progetto")
            
        if self.is_modified:
            title = f"*{title}"
            
        self.setWindowTitle(title)
        
    def add_to_recent(self, filename):
        """Aggiunge file ai recenti"""
        settings = QSettings("ArchBartolotta", "CerchiatureNTC2018")
        recent = settings.value("recentFiles", [])
        
        if isinstance(recent, str):
            recent = [recent] if recent else []
            
        # Rimuovi se già presente
        if filename in recent:
            recent.remove(filename)
            
        # Aggiungi in cima
        recent.insert(0, filename)
        
        # Mantieni solo gli ultimi 10
        recent = recent[:10]
        
        settings.setValue("recentFiles", recent)
        self.update_recent_menu()
        
    def update_recent_menu(self):
        """Aggiorna menu progetti recenti"""
        self.recent_menu.clear()
        
        settings = QSettings("ArchBartolotta", "CerchiatureNTC2018")
        recent = settings.value("recentFiles", [])
        
        if isinstance(recent, str):
            recent = [recent] if recent else []
            
        for i, filename in enumerate(recent):
            if os.path.exists(filename):
                action = QAction(f"{i+1}. {os.path.basename(filename)}", self)
                action.setData(filename)
                action.triggered.connect(lambda checked, f=filename: self.load_project_file(f))
                self.recent_menu.addAction(action)
                
        if not self.recent_menu.isEmpty():
            self.recent_menu.addSeparator()
            clear_action = QAction("Cancella lista", self)
            clear_action.triggered.connect(self.clear_recent)
            self.recent_menu.addAction(clear_action)
            
    def clear_recent(self):
        """Cancella lista progetti recenti"""
        settings = QSettings("ArchBartolotta", "CerchiatureNTC2018")
        settings.setValue("recentFiles", [])
        self.update_recent_menu()
        
    def show_materials_dialog(self):
        """Mostra dialog database materiali"""
        QMessageBox.information(
            self, "Database Materiali",
            "Il database materiali sarà disponibile nella prossima versione.\n\n"
            "Conterrà:\n"
            "• Tipologie di muratura\n"
            "• Parametri meccanici\n"
            "• Valori da normativa"
        )
        
    def show_profiles_dialog(self):
        """Mostra dialog database profili"""
        QMessageBox.information(
            self, "Database Profili",
            "Il database profili sarà disponibile nella prossima versione.\n\n"
            "Conterrà:\n"
            "• Profili HEA, HEB, IPE\n"
            "• Profili UNP, L\n"
            "• Tubolari\n"
            "• Caratteristiche geometriche"
        )
        
    def show_settings_dialog(self):
        """Mostra dialog impostazioni"""
        QMessageBox.information(
            self, "Impostazioni",
            "Le impostazioni saranno disponibili nella prossima versione.\n\n"
            "Sarà possibile configurare:\n"
            "• Dati professionista\n"
            "• Percorsi predefiniti\n"
            "• Unità di misura\n"
            "• Opzioni di calcolo"
        )
        
    def show_manual(self):
        """Mostra manuale utente"""
        QMessageBox.information(
            self, "Manuale Utente",
            "Il manuale utente è in preparazione.\n\n"
            "Per assistenza:\n"
            "Arch. Michelangelo Bartolotta\n"
            "architettomichelangelo@gmail.com"
        )
        
    def show_about(self):
        """Mostra dialog informazioni"""
        about_text = """
        <h2>Calcolatore Cerchiature NTC 2018</h2>
        <p><b>Versione 1.0.0</b></p>
        
        <p>Software professionale per la verifica di interventi locali<br>
        su murature portanti secondo NTC 2018 § 8.4.1</p>
        
        <p><b>Sviluppato da:</b><br>
        Arch. Michelangelo Bartolotta<br>
        Ordine degli Architetti di Agrigento n. 1557</p>
        
        <p><b>Contatti:</b><br>
        Via Domenico Scinà n. 28, Palermo<br>
        architettomichelangelo@gmail.com</p>
        
        <p><b>Tecnologie utilizzate:</b><br>
        Python 3, PyQt5, NumPy, Matplotlib</p>
        
        <hr>
        <p><small>Copyright © 2024 - Tutti i diritti riservati</small></p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Informazioni")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Aggiungi icona se disponibile
        # msg_box.setIconPixmap(QPixmap("resources/icons/logo.png").scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        msg_box.exec_()
        
    def closeEvent(self, event):
        """Gestisce chiusura applicazione"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Esci',
                'Il progetto corrente ha modifiche non salvate.\n'
                'Vuoi salvare prima di uscire?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if self.save_project():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
    def update_calc_module_data(self):
        """Aggiorna i dati nel modulo calcolo"""
        if not hasattr(self, 'calc_module'):
            return
            
        # Raccogli tutti i dati dai moduli
        project_data = {}
        
        if hasattr(self, 'input_module'):
            input_data = self.input_module.collect_data()
            project_data.update(input_data)
            
        if hasattr(self, 'openings_module'):
            openings_data = self.openings_module.collect_data()
            project_data['openings_module'] = openings_data
            
        # Passa i dati al modulo calcolo
        self.calc_module.set_project_data(project_data)
        
    def update_report_module_data(self):
        """Aggiorna i dati nel modulo relazione"""
        if not hasattr(self, 'report_module') or not self.report_module:
            return
            
        # Raccogli tutti i dati dai moduli
        project_data = {}
        
        if hasattr(self, 'input_module'):
            input_data = self.input_module.collect_data()
            project_data.update(input_data)
            
        if hasattr(self, 'openings_module'):
            openings_data = self.openings_module.collect_data()
            project_data['openings_module'] = openings_data
            
        # Passa i dati al modulo relazione
        self.report_module.set_project_data(project_data)
        
    def update_enhanced_report_module_data(self):
        """Aggiorna i dati nel modulo relazione avanzata"""
        if not hasattr(self, 'enhanced_report_module') or not self.enhanced_report_module:
            return
            
        # Raccogli tutti i dati dai moduli
        project_data = {}
        
        if hasattr(self, 'input_module'):
            input_data = self.input_module.collect_data()
            project_data.update(input_data)
            
        if hasattr(self, 'openings_module'):
            openings_data = self.openings_module.collect_data()
            project_data['openings_module'] = openings_data
            
        # Passa i dati al modulo relazione avanzata
        if hasattr(self, 'calc_module') and hasattr(self.calc_module, 'results'):
            self.enhanced_report_module.set_data(project_data, self.calc_module.results)
        else:
            self.enhanced_report_module.set_data(project_data, {})
        
    def run_calculation(self):
        """Avvia il calcolo dal toolbar"""
        # Vai al tab calcolo
        self.tabs.setCurrentIndex(2)
        
        # Aggiorna dati e avvia calcolo
        if hasattr(self, 'calc_module'):
            self.update_calc_module_data()
            self.calc_module.run_calculation()
            
    def on_calculation_done(self, results):
        """Chiamato quando il calcolo è completato"""
        self.status_bar.showMessage("Calcolo completato", 3000)
        
        # Abilita il pulsante per generare la relazione
        if hasattr(self, 'report_action'):
            self.report_action.setEnabled(True)
            
        # Passa i risultati al modulo relazione standard
        if hasattr(self, 'report_module') and self.report_module:
            self.report_module.set_results(results)
            
        # Passa i risultati anche al modulo relazione avanzata
        if hasattr(self, 'enhanced_report_module') and self.enhanced_report_module:
            # Raccogli i dati del progetto
            project_data = {}
            if hasattr(self, 'input_module'):
                project_data.update(self.input_module.collect_data())
            if hasattr(self, 'openings_module'):
                project_data['openings_module'] = self.openings_module.collect_data()
            # Passa sia i dati che i risultati
            self.enhanced_report_module.set_data(project_data, results)
            
    def generate_report(self):
        """Genera relazione dal toolbar"""
        # Vai al tab relazione
        self.tabs.setCurrentIndex(3)
        
        # Aggiorna dati e genera
        if hasattr(self, 'report_module') and self.report_module:
            self.update_report_module_data()
            # Attiva la generazione se ci sono risultati
            if hasattr(self, 'calc_module') and hasattr(self.calc_module, 'results'):
                self.report_module.generate_report()