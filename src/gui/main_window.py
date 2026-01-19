"""
Finestra principale applicazione
Calcolatore Cerchiature NTC 2018

Pattern MVP: MainWindow orchestra i Presenter che gestiscono la logica,
mentre i moduli (View) si occupano solo della visualizzazione.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import json
import logging

# Import dei Presenter (MVP Pattern)
try:
    from src.gui.presenters import InputPresenter, OpeningsPresenter, CalcPresenter
    PRESENTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Presenter non disponibili: {e}")
    PRESENTERS_AVAILABLE = False

# Import dei moduli (View)
try:
    from src.gui.modules.input_module import InputModule
except ImportError:
    print("Warning: InputModule non trovato")
    InputModule = None

try:
    from src.gui.modules.openings_module import OpeningsModule  
except ImportError:
    print("Warning: OpeningsModule non trovato")
    OpeningsModule = None

try:
    from src.gui.modules.calc_module import CalcModule
except ImportError:
    print("Warning: CalcModule non trovato")
    CalcModule = None

try:
    from src.gui.modules.report_module import ReportModule  
except ImportError:
    print("Warning: ReportModule non trovato")
    ReportModule = None

try:
    from src.gui.modules.enhanced_report_module import EnhancedReportModule
    ENHANCED_REPORT_AVAILABLE = True
except ImportError:
    ENHANCED_REPORT_AVAILABLE = False
    print("EnhancedReportModule non disponibile")

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Finestra principale con gestione moduli.

    Pattern MVP:
    - MainWindow: Coordinator che orchestra presenter e view
    - Presenter: Gestiscono la logica di business
    - Module (View): Gestiscono solo la visualizzazione

    I Presenter comunicano tramite eventi, MainWindow li connette alle View.
    """

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

        # Inizializza Presenter (MVP Pattern)
        self._init_presenters()

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        # Connetti eventi presenter dopo setup UI
        self._connect_presenter_events()

    def _init_presenters(self):
        """Inizializza i presenter per il pattern MVP"""
        if PRESENTERS_AVAILABLE:
            self.input_presenter = InputPresenter()
            self.openings_presenter = OpeningsPresenter()
            self.calc_presenter = CalcPresenter()
            logger.info("Presenter MVP inizializzati")
        else:
            self.input_presenter = None
            self.openings_presenter = None
            self.calc_presenter = None
            logger.warning("Presenter non disponibili, modalità legacy")

    def _connect_presenter_events(self):
        """Connette gli eventi dei presenter alle view"""
        if not PRESENTERS_AVAILABLE:
            return

        # Eventi InputPresenter
        self.input_presenter.on('wall_updated', self._on_wall_updated)
        self.input_presenter.on('masonry_updated', self._on_masonry_updated)
        self.input_presenter.on('openings_updated', self._on_openings_updated)
        self.input_presenter.on('data_changed', self._on_presenter_data_changed)

        # Eventi OpeningsPresenter
        self.openings_presenter.on('openings_changed', self._on_openings_changed)
        self.openings_presenter.on('reinforcement_updated', self._on_reinforcement_updated)
        self.openings_presenter.on('stats_updated', self._on_stats_updated)

        # Eventi CalcPresenter
        self.calc_presenter.on('calculation_started', self._on_calculation_started)
        self.calc_presenter.on('calculation_completed', self._on_calculation_completed)
        self.calc_presenter.on('calculation_failed', self._on_calculation_failed)
        self.calc_presenter.on('results_ready', self._on_results_ready)

        logger.info("Eventi presenter connessi")

    # =========================================================================
    # PRESENTER EVENT HANDLERS
    # =========================================================================

    def _on_wall_updated(self, wall_data):
        """Gestisce aggiornamento dati parete dal presenter"""
        # Sincronizza con openings_presenter
        if self.openings_presenter:
            self.openings_presenter.set_wall_context(wall_data)
        # Aggiorna view se necessario
        if hasattr(self, 'openings_module') and self.openings_module:
            self.openings_module.set_wall_data(wall_data)
        self.is_modified = True
        self.update_title()

    def _on_masonry_updated(self, masonry_data):
        """Gestisce aggiornamento dati muratura"""
        self.is_modified = True
        self.update_title()

    def _on_openings_updated(self, openings):
        """Gestisce aggiornamento aperture da InputPresenter"""
        if self.openings_presenter:
            self.openings_presenter.set_openings(openings)
        if hasattr(self, 'openings_module') and self.openings_module:
            self.openings_module.set_openings(openings)
        self.is_modified = True
        self.update_title()

    def _on_presenter_data_changed(self):
        """Gestisce cambio dati generico da presenter"""
        self.is_modified = True
        self.update_title()

    def _on_openings_changed(self, openings):
        """Gestisce cambio aperture da OpeningsPresenter"""
        self.is_modified = True
        self.update_title()

    def _on_reinforcement_updated(self, index, rinforzo):
        """Gestisce aggiornamento rinforzo"""
        self.is_modified = True
        self.update_title()
        logger.info(f"Rinforzo apertura {index} aggiornato")

    def _on_stats_updated(self, stats):
        """Gestisce aggiornamento statistiche aperture"""
        pass  # View gestisce visualizzazione

    def _on_calculation_started(self):
        """Gestisce avvio calcolo"""
        self.status_bar.showMessage("Calcolo in corso...")
        self.calc_action.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def _on_calculation_completed(self, result):
        """Gestisce completamento calcolo"""
        QApplication.restoreOverrideCursor()
        self.calc_action.setEnabled(True)
        self.report_action.setEnabled(True)
        self.status_bar.showMessage("Calcolo completato", 3000)
        logger.info("Calcolo completato con successo")

    def _on_calculation_failed(self, error_msg):
        """Gestisce fallimento calcolo"""
        QApplication.restoreOverrideCursor()
        self.calc_action.setEnabled(True)
        self.status_bar.showMessage(f"Errore: {error_msg}", 5000)
        logger.error(f"Calcolo fallito: {error_msg}")

    def _on_results_ready(self, formatted_results):
        """Gestisce risultati pronti per visualizzazione"""
        # Passa risultati ai moduli report
        if hasattr(self, 'report_module') and self.report_module:
            self.report_module.set_results(formatted_results)
        if hasattr(self, 'enhanced_report_module') and self.enhanced_report_module:
            project_data = self._collect_all_data()
            self.enhanced_report_module.set_data(project_data, formatted_results)
        
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
        """
        Sincronizza i dati tra i moduli.

        Con pattern MVP: sincronizza tramite presenter.
        Fallback legacy: sincronizza direttamente tra moduli.
        """
        if PRESENTERS_AVAILABLE and self.input_presenter:
            # Pattern MVP: sincronizza via presenter
            self._sync_via_presenters()
        else:
            # Legacy: sincronizza direttamente
            self._sync_legacy()

    def _sync_via_presenters(self):
        """Sincronizza dati tramite presenter (MVP)"""
        # Carica dati da input_module nel presenter
        if hasattr(self, 'input_module') and self.input_module:
            input_data = self.input_module.collect_data()

            # Aggiorna input_presenter
            wall = input_data.get('wall', {})
            if wall:
                self.input_presenter.set_wall_dimensions(
                    wall.get('length', 300),
                    wall.get('height', 270),
                    wall.get('thickness', 30)
                )

            masonry = input_data.get('masonry', {})
            if masonry:
                self.input_presenter.set_masonry_params(
                    fcm=masonry.get('fcm', 2.4),
                    tau0=masonry.get('tau0', 0.074),
                    E=masonry.get('E', 1500)
                )

            # Sincronizza openings_presenter con contesto parete
            if self.openings_presenter:
                self.openings_presenter.set_wall_context(wall)
                openings = input_data.get('openings', [])
                self.openings_presenter.set_openings(openings)

    def _sync_legacy(self):
        """Sincronizza dati in modalità legacy (senza presenter)"""
        if hasattr(self, 'input_module') and hasattr(self, 'openings_module'):
            wall_data = self.input_module.collect_data().get('wall')
            if wall_data:
                self.openings_module.set_wall_data(wall_data)

            openings = self.input_module.collect_data().get('openings', [])
            self.openings_module.set_openings(openings)

    def _collect_all_data(self) -> dict:
        """
        Raccoglie tutti i dati del progetto dai presenter/moduli.

        Returns:
            Dict con tutti i dati del progetto
        """
        project_data = {}

        # Priorità: usa presenter se disponibili
        if PRESENTERS_AVAILABLE and self.input_presenter:
            project_data = self.input_presenter.collect_data()

            if self.openings_presenter:
                openings_data = self.openings_presenter.collect_data()
                project_data['openings_module'] = openings_data
        else:
            # Fallback legacy
            if hasattr(self, 'input_module') and self.input_module:
                project_data = self.input_module.collect_data()

            if hasattr(self, 'openings_module') and self.openings_module:
                project_data['openings_module'] = self.openings_module.collect_data()

        return project_data
            
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
        
        # Reset presenter (MVP)
        if PRESENTERS_AVAILABLE:
            self._init_presenters()
            self._connect_presenter_events()

        # Reset tutti i moduli (view)
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
        """
        Carica un file progetto.

        MVP: Carica dati nei presenter e sincronizza con le view.
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Carica dati nei presenter (MVP)
            if PRESENTERS_AVAILABLE:
                self._load_data_to_presenters(data)

            # Carica i dati nei moduli (view)
            if hasattr(self, 'input_module') and self.input_module:
                self.input_module.load_data(data)

            if hasattr(self, 'openings_module') and self.openings_module:
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
            logger.info(f"Progetto caricato: {filename}")

        except Exception as e:
            logger.error(f"Errore caricamento: {e}")
            QMessageBox.critical(
                self, "Errore",
                f"Errore nel caricamento del file:\n{str(e)}"
            )

    def _load_data_to_presenters(self, data: dict):
        """Carica dati nei presenter"""
        if self.input_presenter:
            self.input_presenter.load_data(data)

        if self.openings_presenter:
            openings_data = data.get('openings_module', {})
            if 'wall' in data:
                openings_data['wall'] = data['wall']
            self.openings_presenter.load_data(openings_data)
            
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
        """
        Salva progetto su file.

        MVP: Raccoglie dati dai presenter quando disponibili.
        """
        try:
            # Raccogli dati (usa presenter se disponibili)
            self.project_data = self._collect_all_data()

            # Aggiungi dati del modulo relazione
            if hasattr(self, 'report_module') and self.report_module:
                self.project_data['report_module'] = self.report_module.collect_data()

            # Aggiungi risultati calcolo se presenti
            if PRESENTERS_AVAILABLE and self.calc_presenter and self.calc_presenter.has_results():
                self.project_data['calc_results'] = self.calc_presenter.export_results('detailed')

            # Salva su file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)

            # Aggiorna stato
            self.current_file = filename
            self.is_modified = False
            self.update_title()
            self.add_to_recent(filename)

            # Marca presenter come "puliti"
            if PRESENTERS_AVAILABLE:
                if self.input_presenter:
                    self.input_presenter.mark_clean()
                if self.openings_presenter:
                    self.openings_presenter.mark_clean()

            self.status_bar.showMessage(f"Progetto salvato: {os.path.basename(filename)}", 3000)
            logger.info(f"Progetto salvato: {filename}")
            return True

        except Exception as e:
            logger.error(f"Errore salvataggio: {e}")
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
        """
        Aggiorna i dati nel modulo calcolo.

        MVP: Usa CalcPresenter per gestire i dati.
        """
        project_data = self._collect_all_data()

        # Aggiorna CalcPresenter (MVP)
        if PRESENTERS_AVAILABLE and self.calc_presenter:
            self.calc_presenter.set_project_data(project_data)

        # Aggiorna anche il modulo view per visualizzazione
        if hasattr(self, 'calc_module') and self.calc_module:
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
        """
        Avvia il calcolo dal toolbar.

        MVP: Usa CalcPresenter per eseguire il calcolo.
        """
        # Vai al tab calcolo
        self.tabs.setCurrentIndex(2)

        # Aggiorna dati
        self.update_calc_module_data()

        # Esegui calcolo via presenter (MVP)
        if PRESENTERS_AVAILABLE and self.calc_presenter:
            # Verifica se può calcolare
            can_calc, reasons = self.calc_presenter.can_calculate()
            if not can_calc:
                QMessageBox.warning(
                    self, "Impossibile Calcolare",
                    "Verifica i dati:\n• " + "\n• ".join(reasons)
                )
                return

            # Avvia calcolo via presenter
            self.calc_presenter.run_calculation(
                on_complete=self._on_calc_presenter_complete,
                on_error=self._on_calc_presenter_error
            )
        elif hasattr(self, 'calc_module') and self.calc_module:
            # Fallback legacy
            self.calc_module.run_calculation()

    def _on_calc_presenter_complete(self, result):
        """Callback completamento calcolo da presenter"""
        # Passa risultati al modulo view per visualizzazione
        if hasattr(self, 'calc_module') and self.calc_module:
            self.calc_module.display_results(result)

    def _on_calc_presenter_error(self, error_msg):
        """Callback errore calcolo da presenter"""
        QMessageBox.critical(
            self, "Errore Calcolo",
            f"Si è verificato un errore durante il calcolo:\n\n{error_msg}"
        )
            
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