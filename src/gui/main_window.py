"""
Finestra principale applicazione
Calcolatore Cerchiature NTC 2018
Versione con UI migliorata
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import json
import logging

logger = logging.getLogger(__name__)

# Import nuovi componenti UI
try:
    from src.gui.ui_enhancements import (
        WorkflowIndicator, SummaryDock, ToastManager,
        ProgressButton, create_separator
    )
    from src.gui.modern_style import apply_modern_style, toggle_theme, get_current_theme, COLORS
    UI_ENHANCEMENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UI Enhancements non disponibili: {e}")
    UI_ENHANCEMENTS_AVAILABLE = False

# Import nuove funzionalità
try:
    from src.core.app_config import get_app_config, get_undo_manager, get_autosave_manager
    from src.core.project_templates import get_all_templates, get_categories, template_to_project_data
    from src.core.exporters import export_to_excel, export_to_dxf
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Funzionalità avanzate non disponibili: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

try:
    from src.widgets.wall_3d_view import Wall3DView
    VIEW_3D_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vista 3D non disponibile: {e}")
    VIEW_3D_AVAILABLE = False

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
    """Finestra principale con gestione moduli e UI migliorata"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calcolatore Cerchiature NTC 2018 - Arch. M. Bartolotta")
        self.setGeometry(100, 100, 1400, 900)

        # Centra la finestra
        self.center_window()

        # Dati progetto condivisi tra moduli
        self.project_data = {}
        self.current_file = None
        self.is_modified = False
        self.calculation_results = None  # Risultati ultimo calcolo

        # Inizializza Toast Manager per notifiche
        if UI_ENHANCEMENTS_AVAILABLE:
            self.toast_manager = ToastManager(self)
        else:
            self.toast_manager = None

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_shortcuts()
        self.setup_summary_dock()
        
    def center_window(self):
        """Centra la finestra sullo schermo"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def setup_ui(self):
        """Configura interfaccia con tabs e workflow indicator"""
        # Widget centrale
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Workflow Indicator (se disponibile)
        if UI_ENHANCEMENTS_AVAILABLE:
            self.workflow_indicator = WorkflowIndicator()
            self.workflow_indicator.step_clicked.connect(self.on_workflow_step_clicked)
            # Container con sfondo
            workflow_container = QWidget()
            workflow_container.setStyleSheet("""
                QWidget {
                    background: #ffffff;
                    border-bottom: 1px solid #dcdde1;
                }
            """)
            workflow_layout = QHBoxLayout()
            workflow_layout.setContentsMargins(10, 5, 10, 5)
            workflow_layout.addWidget(self.workflow_indicator)
            workflow_container.setLayout(workflow_layout)
            central_layout.addWidget(workflow_container)
        else:
            self.workflow_indicator = None

        # Widget centrale con tab
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        central_layout.addWidget(self.tabs)

        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)
        
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

        # Importa da PT3
        import_pt3_action = QAction('Importa da &PT3 (.pt3)...', self)
        import_pt3_action.setStatusTip('Importa progetto da file PT3 (Particolare 3)')
        import_pt3_action.triggered.connect(self.import_pt3_project)
        file_menu.addAction(import_pt3_action)

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
        export_excel.setShortcut('Ctrl+E')
        export_excel.setStatusTip('Esporta dati e risultati in formato Excel')
        export_excel.triggered.connect(self.export_to_excel)
        export_menu.addAction(export_excel)

        export_dxf = QAction('Esporta geometria DXF...', self)
        export_dxf.setStatusTip('Esporta geometria in formato DXF per CAD')
        export_dxf.triggered.connect(self.export_to_dxf)
        export_menu.addAction(export_dxf)
        
        file_menu.addSeparator()
        
        exit_action = QAction(QIcon.fromTheme('application-exit'), '&Esci', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Esci dall\'applicazione')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Modifica
        edit_menu = menubar.addMenu('&Modifica')

        self.undo_action = QAction(QIcon.fromTheme('edit-undo'), '&Annulla', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.setStatusTip('Annulla ultima modifica')
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction(QIcon.fromTheme('edit-redo'), '&Ripeti', self)
        self.redo_action.setShortcut('Ctrl+Y')
        self.redo_action.setStatusTip('Ripeti modifica annullata')
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        # Menu Template
        template_menu = edit_menu.addMenu('Carica &Template')
        if ADVANCED_FEATURES_AVAILABLE:
            templates = get_all_templates()
            categories = get_categories()
            for category in sorted(categories):
                cat_menu = template_menu.addMenu(category)
                for template_id, template in templates.items():
                    if template.category == category:
                        action = QAction(template.name, self)
                        action.setStatusTip(template.description)
                        action.triggered.connect(
                            lambda checked, tid=template_id: self.load_template(tid)
                        )
                        cat_menu.addAction(action)
        else:
            template_menu.setEnabled(False)

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

        view_menu.addSeparator()

        # Vista 3D
        view_3d_action = QAction('Vista &3D...', self)
        view_3d_action.setShortcut('F3')
        view_3d_action.setStatusTip('Mostra vista 3D isometrica del muro')
        view_3d_action.triggered.connect(self.show_3d_view)
        view_3d_action.setEnabled(VIEW_3D_AVAILABLE)
        view_menu.addAction(view_3d_action)

        view_menu.addSeparator()

        # Toggle tema
        self.theme_action = QAction('Tema &Scuro', self)
        self.theme_action.setShortcut('Ctrl+D')
        self.theme_action.setStatusTip('Alterna tra tema chiaro e scuro')
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)
        
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

        # Aggiorna summary dock
        self.update_summary_dock()

        # Aggiorna workflow indicator
        self.update_workflow_state()
            
    def on_tab_changed(self, index):
        """Chiamato quando si cambia tab"""
        tab_names = ["Struttura", "Aperture", "Calcolo", "Relazione", "Relazione Completa"]
        if index < len(tab_names):
            self.status_bar.showMessage(f"Modulo attivo: {tab_names[index]}")

        # Aggiorna workflow indicator
        if self.workflow_indicator and index < 4:
            self.workflow_indicator.set_current_step(index)
            
        # Sincronizza dati quando si passa al modulo aperture
        if index == 1 and hasattr(self, 'input_module') and hasattr(self, 'openings_module'):
            wall_data = self.input_module.collect_data().get('wall')
            if wall_data:
                self.openings_module.set_wall_data(wall_data)

            # Sincronizza aperture dal modulo input al modulo aperture
            # MA solo se non ci sono già aperture nel modulo (es. dopo importazione ACCA)
            if not self.openings_module.openings:
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

    def import_pt3_project(self):
        """Importa progetto da file PT3 (Particolare 3)"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Importa Progetto PT3',
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
            self, "Importa Progetto PT3",
            "",
            "File PT3 (*.pt3);;Tutti i file (*.*)"
        )

        if filename:
            self.load_pt3_file(filename)

    def load_pt3_file(self, filename):
        """Carica un file PT3 (Particolare 3)"""
        try:
            # Importa modulo PT3
            import sys
            if 'src' not in sys.path:
                sys.path.insert(0, 'src')
            from core.importers.pt3_importer import import_pt3

            # Mostra dialogo di progresso
            progress = QProgressDialog("Importazione PT3 in corso...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Importazione PT3")
            progress.show()
            QApplication.processEvents()

            # Importa il progetto
            project_data = import_pt3(filename)

            progress.close()

            if project_data:
                # Mostra riepilogo importazione
                wall = project_data.get('wall', {})
                masonry = project_data.get('masonry', {})
                openings = project_data.get('openings', [])

                msg = f"""
<h3>Importazione PT3 completata</h3>
<p><b>File:</b> {os.path.basename(filename)}</p>
<p><b>Dimensioni parete:</b> {wall.get('length', 0):.0f} x {wall.get('height', 0):.0f} x {wall.get('thickness', 0):.0f} cm</p>
<p><b>Muratura:</b> {masonry.get('type', 'N/D')}</p>
<p><b>Aperture:</b> {len(openings)}</p>
"""
                QMessageBox.information(self, "Importazione PT3", msg)

                # Carica dati nei moduli GUI
                self.load_pt3_data(project_data)

                # Aggiorna stato
                self.current_file = None  # File importato, non salvato
                self.is_modified = True
                self.update_title()

                self.status_bar.showMessage(
                    f"Progetto importato da PT3: {os.path.basename(filename)}", 5000
                )
            else:
                QMessageBox.warning(
                    self, "Errore Importazione",
                    "Impossibile importare il file PT3.\n"
                    "Verifica che il file sia un file PT3 valido."
                )

        except ImportError as e:
            QMessageBox.critical(
                self, "Errore",
                f"Modulo di importazione PT3 non disponibile:\n{str(e)}"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "Errore",
                f"Errore durante l'importazione PT3:\n{str(e)}"
            )

    def load_pt3_data(self, project_data):
        """Carica i dati importati da PT3 nei moduli GUI"""
        try:
            wall = project_data.get('wall', {})
            masonry = project_data.get('masonry', {})
            openings = project_data.get('openings', [])

            # Carica dati parete nel modulo input
            if hasattr(self, 'input_module') and self.input_module:
                try:
                    self.input_module.wall_length.setValue(int(wall.get('length', 300)))
                    self.input_module.wall_height.setValue(int(wall.get('height', 300)))
                    self.input_module.wall_thickness.setValue(int(wall.get('thickness', 30)))

                    # Imposta tipo muratura se corrispondente
                    masonry_type = masonry.get('type', '')
                    index = self.input_module.masonry_type.findText(masonry_type)
                    if index >= 0:
                        self.input_module.masonry_type.setCurrentIndex(index)

                    # Imposta proprietà meccaniche (questi sono i valori dal file PT3)
                    if masonry.get('E', 0) > 0:
                        self.input_module.E_modulus.setValue(int(masonry.get('E', 1500)))
                    if masonry.get('G', 0) > 0:
                        self.input_module.G_modulus.setValue(int(masonry.get('G', 500)))
                    if masonry.get('tau0', 0) > 0:
                        self.input_module.tau0.setValue(masonry.get('tau0', 0.06))
                    if masonry.get('fcd', 0) > 0:
                        self.input_module.fcm.setValue(masonry.get('fcd', 2.4))

                    # Aggiorna il canvas del modulo Struttura
                    self.input_module.on_wall_changed()

                    logger.info("Valori PT3 impostati negli spinbox")
                except Exception as e:
                    logger.warning(f"Errore impostazione spinbox PT3: {e}")

            # Prepara dati parete per modulo aperture
            wall_data = {
                'length': int(wall.get('length', 300)),
                'height': int(wall.get('height', 300)),
                'thickness': int(wall.get('thickness', 30)),
                'height_left': int(wall.get('height', 300)),
                'height_right': int(wall.get('height', 300)),
                'knowledge_level': 'LC1'
            }

            # Imposta dati muro nel modulo aperture
            if hasattr(self, 'openings_module') and self.openings_module:
                self.openings_module.set_wall_data(wall_data)
                logger.info("Dati muro PT3 impostati nel modulo aperture")

            # Converti e carica aperture
            if openings and hasattr(self, 'openings_module') and self.openings_module:
                openings_data = []
                for i, op in enumerate(openings):
                    is_existing = op.get('existing', False)
                    rinforzo = op.get('rinforzo') or {}
                    profilo = rinforzo.get('profilo', 'HEA 120') if rinforzo else ''

                    op_dict = {
                        'id': i + 1,
                        'name': f"A{i+1}",
                        'width': int(op.get('width', 100)),
                        'height': int(op.get('height', 200)),
                        'x': int(op.get('x', 100)),
                        'y': int(op.get('y', 0)),
                        'type': op.get('type', 'Rettangolare'),
                        'existing': is_existing,
                        'is_door': op.get('y', 0) == 0,  # Se y=0, probabilmente è una porta
                        'frame_type': 0 if is_existing else 1,  # 0=nessuno, 1=telaio chiuso
                    }

                    # Aggiungi rinforzo solo per aperture nuove
                    if not is_existing and rinforzo:
                        # Tipo deve corrispondere esattamente ai valori del combo
                        # 0: "Telaio completo in acciaio"
                        # 1: "Solo architrave in acciaio"
                        tipo_rinforzo = rinforzo.get('tipo', 'telaio_chiuso')
                        if 'telaio' in tipo_rinforzo.lower() or 'chiuso' in tipo_rinforzo.lower() or 'completo' in tipo_rinforzo.lower():
                            tipo_gui = 'Telaio completo in acciaio'
                        elif 'architrave' in tipo_rinforzo.lower():
                            tipo_gui = 'Solo architrave in acciaio'
                        else:
                            tipo_gui = 'Telaio completo in acciaio'

                        op_dict['rinforzo'] = {
                            'tipo': tipo_gui,
                            'materiale': 'acciaio',
                            'architrave': {
                                'profilo': profilo,
                                'n_profili': rinforzo.get('n_profili', 1)
                            },
                            'piedritti': {
                                'profilo': profilo,
                                'n_profili': rinforzo.get('n_profili', 1)
                            },
                            # Base con trave di collegamento
                            'base': {
                                'tipo': 'Trave di collegamento',
                                'trave': {
                                    'profilo': profilo,
                                    'n_profili': rinforzo.get('n_profili', 1)
                                }
                            }
                        }
                    else:
                        op_dict['rinforzo'] = None

                    openings_data.append(op_dict)
                    status = "ESISTENTE" if is_existing else f"NUOVA con {profilo}"
                    logger.info(f"Apertura PT3 {i+1}: {op_dict['width']}x{op_dict['height']} @ ({op_dict['x']}, {op_dict['y']}) - {status}")

                try:
                    # Imposta aperture nel modulo Aperture
                    self.openings_module.openings = openings_data
                    self.openings_module.refresh_all()
                    logger.info(f"Caricate {len(openings_data)} aperture PT3 nel modulo Aperture")
                except Exception as e:
                    logger.warning(f"Errore caricamento aperture PT3: {e}")

                # Carica aperture anche nel modulo Struttura
                try:
                    if hasattr(self, 'input_module') and self.input_module:
                        self.input_module.wall_canvas.openings = openings_data.copy()
                        self.input_module.update_openings_list()
                        self.input_module.wall_canvas.update()
                        logger.info(f"Caricate {len(openings_data)} aperture PT3 nel modulo Struttura")
                except Exception as e:
                    logger.warning(f"Errore caricamento aperture PT3 in Struttura: {e}")

                # Salva dati in project_data
                self.project_data = {
                    'wall': wall_data,
                    'masonry': masonry,
                    'openings': openings_data,
                    'openings_module': {'openings': openings_data},
                    'imported_from_pt3': True
                }

            # Forza refresh
            QApplication.processEvents()

            # Vai al tab Struttura
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(0)
            self.tabs.blockSignals(False)

            # Refresh finale
            if hasattr(self, 'openings_module') and self.openings_module:
                self.openings_module.refresh_all()
                self.openings_module.wall_canvas.update()

        except Exception as e:
            logger.exception(f"Errore caricamento dati PT3: {e}")

    def load_imported_project(self, project):
        """Carica un progetto importato nei moduli GUI"""
        try:
            wall_data = None
            openings_data = []

            # Converti dati del muro (converti float a int per spinbox)
            wall_segments = []
            if project.wall:
                # Estrai setti murari se presenti
                wall_segments = project.wall.wall_segments if hasattr(project.wall, 'wall_segments') else []

                # Calcola altezze sx/dx dai setti o dalla geometria
                if wall_segments:
                    first_seg = wall_segments[0]
                    last_seg = wall_segments[-1]
                    height_left = int(first_seg.get('AltezzaSx', project.wall.height))
                    height_right = int(last_seg.get('AltezzaDx', project.wall.height))
                    is_variable = abs(height_left - height_right) > 0.1
                elif hasattr(project.wall, 'geometry') and project.wall.geometry:
                    height_left = int(project.wall.geometry.height_left)
                    height_right = int(project.wall.geometry.height_right)
                    is_variable = abs(height_left - height_right) > 0.1
                else:
                    height_left = int(project.wall.height)
                    height_right = int(project.wall.height)
                    is_variable = False

                wall_data = {
                    'length': int(project.wall.length),
                    'height': int(project.wall.height),
                    'thickness': int(project.wall.thickness),
                    'height_left': height_left,
                    'height_right': height_right,
                    'knowledge_level': project.wall.knowledge_level.value if hasattr(project.wall.knowledge_level, 'value') else 'LC1',
                    'segments': wall_segments
                }
                logger.info(f"Dati muro importati: {wall_data}")
                if wall_segments:
                    logger.info(f"Setti murari importati: {len(wall_segments)}")

                # Carica nel modulo input - imposta direttamente i valori
                if hasattr(self, 'input_module') and self.input_module:
                    try:
                        self.input_module.wall_length.setValue(wall_data['length'])
                        self.input_module.wall_height.setValue(wall_data['height'])
                        self.input_module.wall_thickness.setValue(wall_data['thickness'])

                        # Imposta altezza variabile se presente
                        if is_variable or wall_segments:
                            self.input_module.variable_height_check.setChecked(True)
                            self.input_module.wall_height_left.setValue(height_left)
                            self.input_module.wall_height_right.setValue(height_right)

                        # Imposta setti
                        if wall_segments:
                            self.input_module.wall_segments = wall_segments

                        # IMPORTANTE: Aggiorna il canvas del modulo Struttura
                        self.input_module.on_wall_changed()

                        logger.info("Valori muro impostati negli spinbox")
                    except Exception as e:
                        logger.warning(f"Errore impostazione spinbox muro: {e}")

                # IMPORTANTE: Imposta dati muro nel modulo aperture PRIMA delle aperture
                if hasattr(self, 'openings_module') and self.openings_module:
                    self.openings_module.set_wall_data(wall_data)
                    logger.info("Dati muro impostati nel modulo aperture")

            # Converti aperture (converti float a int per spinbox)
            if project.openings and hasattr(self, 'openings_module') and self.openings_module:
                openings_data = []
                for i, op in enumerate(project.openings):
                    # Determina nome profilo (usa nome risolto se disponibile)
                    lintel_name = op.profiles.lintel_profile_name or f"ID {op.profiles.lintel_profile_id}"
                    jamb_name = op.profiles.jamb_profile_name or f"ID {op.profiles.jamb_profile_id}"
                    base_name = op.profiles.base_profile_name or f"ID {op.profiles.base_profile_id}"

                    op_dict = {
                        'id': i + 1,
                        'name': f"A{i+1}",
                        'width': int(op.geometry.width),
                        'height': int(op.geometry.height),
                        'x': int(op.geometry.dist_left),
                        'y': int(op.geometry.dist_base),
                        'type': 'Rettangolare',  # Tipo apertura per GUI
                        'existing': op.situation.value == 1,  # 1 = esistente in ACCA
                        'is_door': op.is_door,
                        'frame_type': op.frame_type.value if hasattr(op.frame_type, 'value') else 1,
                        'rinforzo': {
                            'tipo': 'Telaio completo in acciaio' if op.frame_type.value == 1 else 'Solo architrave in acciaio',
                            'materiale': 'acciaio',
                            'architrave': {
                                'profilo': lintel_name,
                                'n_profili': op.profiles.num_profiles,
                                'Ix': op.profiles.lintel_Ix,
                                'Wpl': op.profiles.lintel_Wpl
                            },
                            'piedritti': {
                                'profilo': jamb_name,
                                'n_profili': op.profiles.num_profiles,
                                'Ix': op.profiles.jamb_Ix,
                                'Wpl': op.profiles.jamb_Wpl
                            },
                            'base': {
                                'tipo': 'Trave di collegamento',
                                'trave': {
                                    'profilo': base_name,
                                    'n_profili': op.profiles.num_profiles
                                }
                            },
                            'profiles': {
                                'lintel': op.profiles.lintel_profile_id,
                                'jamb': op.profiles.jamb_profile_id,
                                'base': op.profiles.base_profile_id
                            }
                        }
                    }
                    openings_data.append(op_dict)
                    logger.info(f"Apertura importata: {op_dict}")

                try:
                    # Imposta aperture nel modulo Aperture
                    self.openings_module.openings = openings_data
                    # Forza refresh completo
                    self.openings_module.refresh_all()
                    logger.info(f"Caricate {len(openings_data)} aperture nel modulo Aperture")
                except Exception as e:
                    logger.warning(f"Errore caricamento aperture in modulo Aperture: {e}")

                # IMPORTANTE: Carica aperture anche nel modulo Struttura (input_module)
                try:
                    if hasattr(self, 'input_module') and self.input_module:
                        # Imposta aperture nel wall_canvas del modulo input
                        self.input_module.wall_canvas.openings = openings_data.copy()
                        self.input_module.update_openings_list()
                        self.input_module.wall_canvas.update()
                        logger.info(f"Caricate {len(openings_data)} aperture nel modulo Struttura")
                except Exception as e:
                    logger.warning(f"Errore caricamento aperture in modulo Struttura: {e}")

            # Salva dati completi del progetto importato
            self.project_data = project.to_dict()
            self.project_data['imported_from_acca'] = True

            # IMPORTANTE: Imposta anche openings_module nei project_data per il calc_module
            if wall_data:
                self.project_data['wall'] = wall_data
            if openings_data:
                self.project_data['openings_module'] = {'openings': openings_data}
                self.project_data['openings'] = openings_data
                logger.info(f"Dati aperture salvati in project_data: {len(openings_data)} aperture")

            # Forza refresh completo di tutti i widget
            QApplication.processEvents()

            # IMPORTANTE: Blocca i segnali durante il cambio tab per evitare che
            # on_tab_changed sovrascriva le aperture appena importate
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(0)  # Tab Struttura (gestione progressiva)
            self.tabs.blockSignals(False)

            # Refresh finale delle aperture importate
            if hasattr(self, 'openings_module') and self.openings_module:
                self.openings_module.refresh_all()
                self.openings_module.wall_canvas.update()
                self.openings_module.openings_tree.update()
                logger.info(f"Refresh finale: {len(self.openings_module.openings)} aperture visualizzate")

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
        self.calculation_results = results  # Salva risultati
        self.status_bar.showMessage("Calcolo completato", 3000)

        # Notifica toast
        if self.toast_manager:
            verif = results.get('verification', {})
            if verif.get('is_local'):
                self.toast_manager.success("Calcolo completato: Intervento LOCALE verificato")
            else:
                self.toast_manager.warning("Calcolo completato: Intervento NON locale")

        # Aggiorna workflow indicator
        if self.workflow_indicator:
            self.workflow_indicator.set_step_complete(2, True)

        # Aggiorna summary dock
        self.update_summary_dock()

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

        # Aggiorna workflow indicator
        if self.workflow_indicator:
            self.workflow_indicator.set_step_complete(3, True)

    def setup_shortcuts(self):
        """Configura scorciatoie da tastiera aggiuntive"""
        shortcuts = [
            ("F5", self.run_calculation, "Esegui calcolo"),
            ("Ctrl+1", lambda: self.tabs.setCurrentIndex(0), "Tab Struttura"),
            ("Ctrl+2", lambda: self.tabs.setCurrentIndex(1), "Tab Aperture"),
            ("Ctrl+3", lambda: self.tabs.setCurrentIndex(2), "Tab Calcolo"),
            ("Ctrl+4", lambda: self.tabs.setCurrentIndex(3), "Tab Relazione"),
            ("Ctrl+R", self.generate_report, "Genera relazione"),
            ("F1", self.show_manual, "Mostra manuale"),
        ]

        for key, callback, tip in shortcuts:
            try:
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.activated.connect(callback)
                shortcut.setWhatsThis(tip)
            except Exception as e:
                logger.warning(f"Errore creazione shortcut {key}: {e}")

    def setup_summary_dock(self):
        """Configura il dock widget di riepilogo"""
        if not UI_ENHANCEMENTS_AVAILABLE:
            self.summary_dock = None
            return

        self.summary_dock = SummaryDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.summary_dock)

        # Aggiorna con dati iniziali
        self.update_summary_dock()

    def on_workflow_step_clicked(self, step_index):
        """Gestisce click su step del workflow"""
        if 0 <= step_index < self.tabs.count():
            self.tabs.setCurrentIndex(step_index)

    def update_summary_dock(self):
        """Aggiorna il dock widget di riepilogo"""
        if not hasattr(self, 'summary_dock') or not self.summary_dock:
            return

        # Raccogli dati
        project_data = {}
        wall_area = 0

        if hasattr(self, 'input_module') and self.input_module:
            project_data = self.input_module.collect_data()
            wall = project_data.get('wall', {})
            wall_area = wall.get('length', 0) * wall.get('height', 0) / 10000

        # Aggiorna sezioni
        self.summary_dock.update_wall_data(project_data.get('wall', {}))
        self.summary_dock.update_masonry_data(project_data.get('masonry', {}))

        # Aperture
        openings = []
        if hasattr(self, 'openings_module') and self.openings_module:
            openings_data = self.openings_module.collect_data()
            openings = openings_data.get('openings', [])
        elif 'openings' in project_data:
            openings = project_data.get('openings', [])

        self.summary_dock.update_openings_data(openings, wall_area)

        # Verifica
        if self.calculation_results:
            self.summary_dock.update_verification(self.calculation_results)

    def update_workflow_state(self):
        """Aggiorna lo stato del workflow indicator"""
        if not self.workflow_indicator:
            return

        # Step 0: Struttura - completo se ci sono dati muro validi
        if hasattr(self, 'input_module') and self.input_module:
            data = self.input_module.collect_data()
            wall = data.get('wall', {})
            if wall.get('length', 0) > 0 and wall.get('height', 0) > 0:
                self.workflow_indicator.set_step_complete(0, True)
            else:
                self.workflow_indicator.set_step_complete(0, False)

        # Step 1: Aperture - completo se ci sono aperture con rinforzi
        if hasattr(self, 'openings_module') and self.openings_module:
            openings_data = self.openings_module.collect_data()
            openings = openings_data.get('openings', [])
            has_reinforcement = any('rinforzo' in op for op in openings)
            self.workflow_indicator.set_step_complete(1, has_reinforcement)

        # Step 2: Calcolo - completo se ci sono risultati
        self.workflow_indicator.set_step_complete(2, self.calculation_results is not None)

        # Step 3: Relazione - viene impostato in generate_report()

    def show_toast(self, message, type_="info"):
        """Mostra una notifica toast"""
        if self.toast_manager:
            if type_ == "success":
                self.toast_manager.success(message)
            elif type_ == "error":
                self.toast_manager.error(message)
            elif type_ == "warning":
                self.toast_manager.warning(message)
            else:
                self.toast_manager.info(message)

    # ===== NUOVE FUNZIONALITA' =====

    def export_to_excel(self):
        """Esporta progetto e risultati in Excel"""
        if not ADVANCED_FEATURES_AVAILABLE:
            QMessageBox.warning(self, "Non disponibile",
                              "Funzionalità export Excel non disponibile.\n"
                              "Installare openpyxl: pip install openpyxl")
            return

        # Raccogli dati
        project_data = self.collect_all_data()
        results = self.calculation_results or {}

        # Dialogo salvataggio
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Esporta in Excel",
            "cerchiature_export.xlsx",
            "File Excel (*.xlsx);;File CSV (*.csv)"
        )

        if filepath:
            try:
                saved_path = export_to_excel(filepath, project_data, results)
                self.show_toast(f"Esportato in {os.path.basename(saved_path)}", "success")
                self.status_bar.showMessage(f"Esportato: {saved_path}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore esportazione: {e}")
                logger.error(f"Errore export Excel: {e}")

    def export_to_dxf(self):
        """Esporta geometria in DXF"""
        if not ADVANCED_FEATURES_AVAILABLE:
            QMessageBox.warning(self, "Non disponibile",
                              "Funzionalità export DXF non disponibile.")
            return

        # Raccogli dati
        project_data = self.collect_all_data()
        results = self.calculation_results

        # Dialogo salvataggio
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Esporta in DXF",
            "cerchiature_geometria.dxf",
            "File DXF (*.dxf)"
        )

        if filepath:
            try:
                saved_path = export_to_dxf(filepath, project_data, results)
                self.show_toast(f"Esportato in {os.path.basename(saved_path)}", "success")
                self.status_bar.showMessage(f"Esportato: {saved_path}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore esportazione DXF: {e}")
                logger.error(f"Errore export DXF: {e}")

    def collect_all_data(self):
        """Raccoglie tutti i dati del progetto"""
        project_data = {}

        if hasattr(self, 'input_module') and self.input_module:
            project_data.update(self.input_module.collect_data())

        if hasattr(self, 'openings_module') and self.openings_module:
            project_data['openings_module'] = self.openings_module.collect_data()

        project_data['project_info'] = {
            'name': os.path.basename(self.current_file) if self.current_file else 'Nuovo progetto'
        }

        return project_data

    def undo(self):
        """Annulla ultima modifica"""
        if ADVANCED_FEATURES_AVAILABLE:
            undo_manager = get_undo_manager()
            if undo_manager.can_undo():
                state = undo_manager.undo()
                if state:
                    self.restore_state(state)
                    self.show_toast("Annullato", "info")
                self.update_undo_redo_state()

    def redo(self):
        """Ripristina modifica annullata"""
        if ADVANCED_FEATURES_AVAILABLE:
            undo_manager = get_undo_manager()
            if undo_manager.can_redo():
                state = undo_manager.redo()
                if state:
                    self.restore_state(state)
                    self.show_toast("Ripristinato", "info")
                self.update_undo_redo_state()

    def save_undo_state(self, description="Modifica"):
        """Salva stato corrente per undo"""
        if ADVANCED_FEATURES_AVAILABLE:
            state = self.collect_all_data()
            undo_manager = get_undo_manager()
            undo_manager.save_state(state, description)
            self.update_undo_redo_state()

    def restore_state(self, state):
        """Ripristina stato salvato"""
        if hasattr(self, 'input_module') and self.input_module:
            self.input_module.set_data(state)
        self.sync_modules_data()

    def update_undo_redo_state(self):
        """Aggiorna stato pulsanti undo/redo"""
        if ADVANCED_FEATURES_AVAILABLE and hasattr(self, 'undo_action'):
            undo_manager = get_undo_manager()
            self.undo_action.setEnabled(undo_manager.can_undo())
            self.redo_action.setEnabled(undo_manager.can_redo())

    def load_template(self, template_id):
        """Carica un template di progetto"""
        if not ADVANCED_FEATURES_AVAILABLE:
            return

        templates = get_all_templates()
        template = templates.get(template_id)

        if template:
            reply = QMessageBox.question(
                self, "Carica Template",
                f"Caricare il template '{template.name}'?\n\n{template.description}\n\n"
                "I dati correnti saranno sovrascritti.",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                project_data = template_to_project_data(template)

                # Applica dati
                if hasattr(self, 'input_module') and self.input_module:
                    self.input_module.load_data(project_data)

                self.sync_modules_data()
                self.is_modified = True
                self.update_title()
                self.show_toast(f"Template '{template.name}' caricato", "success")

    def show_3d_view(self):
        """Mostra finestra vista 3D"""
        if not VIEW_3D_AVAILABLE:
            QMessageBox.warning(self, "Non disponibile",
                              "Vista 3D non disponibile.")
            return

        # Crea dialog con vista 3D
        dialog = QDialog(self)
        dialog.setWindowTitle("Vista 3D Muro")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout()

        # Widget vista 3D
        view_3d = Wall3DView()

        # Imposta dati muro
        if hasattr(self, 'input_module') and self.input_module:
            data = self.input_module.collect_data()
            wall = data.get('wall', {})
            view_3d.set_wall_data(
                wall.get('length', 300),
                wall.get('height', 300),
                wall.get('thickness', 30)
            )

            # Imposta aperture
            if hasattr(self, 'openings_module') and self.openings_module:
                openings_data = self.openings_module.collect_data()
                view_3d.set_openings(openings_data.get('openings', []))

        layout.addWidget(view_3d)

        # Pulsanti
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Vista")
        reset_btn.clicked.connect(view_3d.reset_view)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        close_btn = QPushButton("Chiudi")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def toggle_theme(self):
        """Alterna tema chiaro/scuro"""
        if UI_ENHANCEMENTS_AVAILABLE:
            new_theme = toggle_theme(QApplication.instance())
            self.theme_action.setChecked(new_theme == 'dark')
            self.show_toast(f"Tema: {'Scuro' if new_theme == 'dark' else 'Chiaro'}", "info")