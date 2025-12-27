"""
Dialog Avanzato per Inserimento/Modifica Aperture
Supporta: archi dettagliati, forme complesse, nicchie, chiusure
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math

class AdvancedOpeningDialog(QDialog):
    """Dialog avanzato per definizione aperture complesse"""
    
    def __init__(self, parent=None, opening_data=None):
        super().__init__(parent)
        self.setWindowTitle("Definizione Apertura Avanzata")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.opening_data = opening_data or {}
        self.setup_ui()
        
        if opening_data:
            self.load_data(opening_data)
            
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget per organizzare le opzioni
        self.tabs = QTabWidget()
        
        # Tab Geometria Base
        self.geometry_tab = self.create_geometry_tab()
        self.tabs.addTab(self.geometry_tab, "Geometria Base")
        
        # Tab Forma Avanzata
        self.shape_tab = self.create_shape_tab()
        self.tabs.addTab(self.shape_tab, "Forma Avanzata")
        
        # Tab Nicchia
        self.niche_tab = self.create_niche_tab()
        self.tabs.addTab(self.niche_tab, "Nicchia")
        
        # Tab Chiusura
        self.closure_tab = self.create_closure_tab()
        self.tabs.addTab(self.closure_tab, "Chiusura Vano")
        
        layout.addWidget(self.tabs)
        
        # Note generali
        notes_group = QGroupBox("Note")
        notes_layout = QVBoxLayout()
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        self.notes_text.setPlaceholderText("Eventuali note sull'apertura...")
        notes_layout.addWidget(self.notes_text)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

        # Connessioni
        self.connect_signals()

        # Inizializza visibilità campi per tipo default (Rettangolare)
        self._update_geometry_fields_visibility(0)
        
    def create_geometry_tab(self):
        """Tab per geometria base"""
        widget = QWidget()
        layout = QFormLayout()

        # Tipo apertura principale
        self.opening_type = QComboBox()
        self.opening_type.addItems([
            "Rettangolare",
            "Ad arco",
            "Circolare",
            "Ovale",
            "Ellittica",
            "Nicchia",
            "Chiusura vano esistente"
        ])
        layout.addRow("Tipo apertura:", self.opening_type)

        # Apertura esistente
        self.existing_check = QCheckBox("Apertura/nicchia esistente")
        layout.addRow("", self.existing_check)

        # Separatore
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        layout.addRow(separator1)

        # Label dimensioni (dinamica)
        self.dim_info_label = QLabel("")
        self.dim_info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addRow(self.dim_info_label)

        # Dimensioni base (visibilità dinamica)
        self.width_label = QLabel("Larghezza:")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 1000)
        self.width_spin.setValue(120)
        self.width_spin.setSuffix(" cm")
        layout.addRow(self.width_label, self.width_spin)

        self.height_label = QLabel("Altezza totale:")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 1000)
        self.height_spin.setValue(230)
        self.height_spin.setSuffix(" cm")
        layout.addRow(self.height_label, self.height_spin)

        # Info altezza calcolata (per archi)
        self.height_calc_label = QLabel("")
        self.height_calc_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        layout.addRow("", self.height_calc_label)

        # Posizione
        self.position_group = QGroupBox("Posizione")
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("X da sinistra:"), 0, 0)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(50)
        self.x_spin.setSuffix(" cm")
        pos_layout.addWidget(self.x_spin, 0, 1)

        pos_layout.addWidget(QLabel("Y dal basso:"), 1, 0)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 1000)
        self.y_spin.setValue(0)
        self.y_spin.setSuffix(" cm")
        pos_layout.addWidget(self.y_spin, 1, 1)

        self.position_group.setLayout(pos_layout)
        layout.addRow(self.position_group)

        widget.setLayout(layout)
        return widget
        
    def create_shape_tab(self):
        """Tab per forme avanzate"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stack widget per diversi tipi di forma
        self.shape_stack = QStackedWidget()
        
        # Pagina rettangolare (vuota, usa dimensioni base)
        rect_page = QWidget()
        self.shape_stack.addWidget(rect_page)
        
        # Pagina arco
        arch_page = self.create_arch_page()
        self.shape_stack.addWidget(arch_page)
        
        # Pagina circolare
        circular_page = self.create_circular_page()
        self.shape_stack.addWidget(circular_page)
        
        # Pagina ovale
        oval_page = self.create_oval_page()
        self.shape_stack.addWidget(oval_page)
        
        # Pagina ellittica
        ellipse_page = self.create_ellipse_page()
        self.shape_stack.addWidget(ellipse_page)
        
        layout.addWidget(self.shape_stack)
        
        widget.setLayout(layout)
        return widget
        
    def create_arch_page(self):
        """Pagina configurazione arco"""
        page = QWidget()
        layout = QFormLayout()
        
        # Tipo di arco
        self.arch_type = QComboBox()
        self.arch_type.addItems([
            "Tutto sesto",
            "Ribassato",
            "Rialzato (ogivale)",
            "Policentrico",
            "A schiena d'asino",
            "Tudor",
            "Ellittico"
        ])
        layout.addRow("Tipo arco:", self.arch_type)
        
        # Altezza imposta (piedritto)
        self.impost_height = QSpinBox()
        self.impost_height.setRange(0, 500)
        self.impost_height.setValue(180)
        self.impost_height.setSuffix(" cm")
        self.impost_height.setToolTip("Altezza dal basso all'inizio dell'arco")
        layout.addRow("Altezza imposta:", self.impost_height)
        
        # Freccia/Monta dell'arco
        self.arch_rise = QSpinBox()
        self.arch_rise.setRange(10, 200)
        self.arch_rise.setValue(60)
        self.arch_rise.setSuffix(" cm")
        self.arch_rise.setToolTip("Altezza massima dell'arco sopra l'imposta")
        layout.addRow("Freccia arco:", self.arch_rise)
        
        # Spessore arco (se diverso dalla larghezza muro)
        self.arch_thickness_check = QCheckBox("Spessore arco diverso dal muro")
        layout.addRow("", self.arch_thickness_check)
        
        self.arch_thickness = QSpinBox()
        self.arch_thickness.setRange(10, 100)
        self.arch_thickness.setValue(30)
        self.arch_thickness.setSuffix(" cm")
        self.arch_thickness.setEnabled(False)
        layout.addRow("Spessore arco:", self.arch_thickness)
        
        # Parametri aggiuntivi per archi complessi
        self.arch_params_group = QGroupBox("Parametri avanzati")
        params_layout = QFormLayout()
        
        # Per arco ribassato
        self.ribassamento = QDoubleSpinBox()
        self.ribassamento.setRange(0.1, 0.9)
        self.ribassamento.setValue(0.5)
        self.ribassamento.setSingleStep(0.1)
        self.ribassamento.setToolTip("Rapporto freccia/semi-luce")
        params_layout.addRow("Rapporto ribassamento:", self.ribassamento)
        
        # Per arco policentrico
        self.n_centers = QSpinBox()
        self.n_centers.setRange(3, 7)
        self.n_centers.setValue(3)
        self.n_centers.setSingleStep(2)
        params_layout.addRow("Numero centri:", self.n_centers)
        
        self.arch_params_group.setLayout(params_layout)
        layout.addRow(self.arch_params_group)
        
        # Anteprima dimensioni calcolate
        self.arch_preview = QLabel("Raggio: - cm\nCorda: - cm")
        self.arch_preview.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        layout.addRow("Anteprima:", self.arch_preview)
        
        page.setLayout(layout)
        return page
        
    def create_circular_page(self):
        """Pagina configurazione apertura circolare"""
        page = QWidget()
        layout = QFormLayout()
        
        # Diametro
        self.diameter = QSpinBox()
        self.diameter.setRange(20, 300)
        self.diameter.setValue(100)
        self.diameter.setSuffix(" cm")
        layout.addRow("Diametro:", self.diameter)
        
        # Centro (se non centrato sull'apertura)
        self.center_offset_check = QCheckBox("Centro personalizzato")
        layout.addRow("", self.center_offset_check)
        
        offset_group = QGroupBox("Offset centro")
        offset_layout = QFormLayout()
        
        self.center_x_offset = QSpinBox()
        self.center_x_offset.setRange(-100, 100)
        self.center_x_offset.setValue(0)
        self.center_x_offset.setSuffix(" cm")
        offset_layout.addRow("Offset X:", self.center_x_offset)
        
        self.center_y_offset = QSpinBox()
        self.center_y_offset.setRange(-100, 100)
        self.center_y_offset.setValue(0)
        self.center_y_offset.setSuffix(" cm")
        offset_layout.addRow("Offset Y:", self.center_y_offset)
        
        offset_group.setLayout(offset_layout)
        offset_group.setEnabled(False)
        layout.addRow(offset_group)
        
        self.circular_offset_group = offset_group
        
        page.setLayout(layout)
        return page
        
    def create_oval_page(self):
        """Pagina configurazione apertura ovale"""
        page = QWidget()
        layout = QFormLayout()
        
        # Orientamento
        self.oval_orientation = QComboBox()
        self.oval_orientation.addItems(["Verticale", "Orizzontale"])
        layout.addRow("Orientamento:", self.oval_orientation)
        
        # Rapporto assi
        self.axis_ratio = QDoubleSpinBox()
        self.axis_ratio.setRange(1.1, 3.0)
        self.axis_ratio.setValue(1.5)
        self.axis_ratio.setSingleStep(0.1)
        self.axis_ratio.setToolTip("Rapporto asse maggiore/asse minore")
        layout.addRow("Rapporto assi:", self.axis_ratio)
        
        # Anteprima dimensioni
        self.oval_preview = QLabel("Asse maggiore: - cm\nAsse minore: - cm")
        self.oval_preview.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        layout.addRow("Anteprima:", self.oval_preview)
        
        page.setLayout(layout)
        return page
        
    def create_ellipse_page(self):
        """Pagina configurazione apertura ellittica"""
        page = QWidget()
        layout = QFormLayout()
        
        # Semi-assi
        self.semi_major = QSpinBox()
        self.semi_major.setRange(20, 200)
        self.semi_major.setValue(80)
        self.semi_major.setSuffix(" cm")
        layout.addRow("Semi-asse maggiore:", self.semi_major)
        
        self.semi_minor = QSpinBox()
        self.semi_minor.setRange(20, 200)
        self.semi_minor.setValue(60)
        self.semi_minor.setSuffix(" cm")
        layout.addRow("Semi-asse minore:", self.semi_minor)
        
        # Rotazione
        self.ellipse_rotation = QSpinBox()
        self.ellipse_rotation.setRange(0, 180)
        self.ellipse_rotation.setValue(0)
        self.ellipse_rotation.setSuffix("°")
        layout.addRow("Rotazione:", self.ellipse_rotation)
        
        page.setLayout(layout)
        return page
        
    def create_niche_tab(self):
        """Tab per configurazione nicchie"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Attiva nicchia
        self.is_niche = QCheckBox("Questa è una nicchia (non passante)")
        layout.addRow("", self.is_niche)
        
        # Gruppo parametri nicchia
        self.niche_group = QGroupBox("Parametri Nicchia")
        niche_layout = QFormLayout()
        
        # Profondità
        self.niche_depth = QSpinBox()
        self.niche_depth.setRange(5, 50)
        self.niche_depth.setValue(15)
        self.niche_depth.setSuffix(" cm")
        niche_layout.addRow("Profondità:", self.niche_depth)
        
        # Tipo di nicchia
        self.niche_type = QComboBox()
        self.niche_type.addItems([
            "Libreria",
            "Armadio a muro",
            "Vano tecnico",
            "Decorativa",
            "Altro"
        ])
        niche_layout.addRow("Tipo nicchia:", self.niche_type)
        
        # Materiale di fondo
        self.niche_back_material = QComboBox()
        self.niche_back_material.addItems([
            "Muratura esistente",
            "Intonaco",
            "Cartongesso",
            "Legno",
            "Altro materiale"
        ])
        niche_layout.addRow("Materiale fondo:", self.niche_back_material)
        
        # Mensole/ripiani
        self.has_shelves = QCheckBox("Presenza mensole/ripiani")
        niche_layout.addRow("", self.has_shelves)
        
        self.n_shelves = QSpinBox()
        self.n_shelves.setRange(1, 10)
        self.n_shelves.setValue(4)
        self.n_shelves.setEnabled(False)
        niche_layout.addRow("Numero ripiani:", self.n_shelves)
        
        self.niche_group.setLayout(niche_layout)
        self.niche_group.setEnabled(False)
        layout.addRow(self.niche_group)
        
        widget.setLayout(layout)
        return widget
        
    def create_closure_tab(self):
        """Tab per chiusura vani esistenti (riempimento apertura)"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Attiva chiusura
        self.is_closure = QCheckBox("Chiusura di vano esistente (riempimento)")
        layout.addWidget(self.is_closure)

        # Gruppo parametri chiusura
        self.closure_group = QGroupBox("Parametri Chiusura/Riempimento")
        closure_layout = QFormLayout()

        # Tipo di chiusura
        self.closure_type = QComboBox()
        self.closure_type.addItems([
            "Muratura piena",
            "Muratura con ammorsamento",
            "Tamponamento leggero",
            "Infisso fisso",
            "Altro"
        ])
        closure_layout.addRow("Tipo chiusura:", self.closure_type)

        # Materiale chiusura (mappato a FillType)
        self.closure_material = QComboBox()
        self.closure_material.addItems([
            "Mattoni pieni",        # FillType.SOLID_BRICK = 1
            "Mattoni forati",       # FillType.HOLLOW_BRICK = 2
            "Blocchi cls",          # FillType.CONCRETE_BLOCK = 3
            "Blocchi laterizio",    # FillType.LATERIZIO_BLOCK = 4
            "Cartongesso",          # FillType.DRYWALL = 5
            "Vetrocemento",         # FillType.GLASS_BLOCK = 6
            "Pannello tamponamento",# FillType.INFILL_PANEL = 7
            "Muratura esistente"    # FillType.EXISTING_MASONRY = 8
        ])
        self.closure_material.currentIndexChanged.connect(self._on_closure_material_changed)
        closure_layout.addRow("Materiale:", self.closure_material)

        # Spessore chiusura
        self.closure_thickness = QSpinBox()
        self.closure_thickness.setRange(5, 50)
        self.closure_thickness.setValue(12)
        self.closure_thickness.setSuffix(" cm")
        closure_layout.addRow("Spessore:", self.closure_thickness)

        # Separatore
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        closure_layout.addRow(separator)

        # === PROPRIETÀ STRUTTURALI (da Calcolus-CERCHIATURA) ===
        struct_label = QLabel("<b>Proprietà strutturali riempimento</b>")
        closure_layout.addRow(struct_label)

        # Modulo elastico E
        self.fill_E = QSpinBox()
        self.fill_E.setRange(0, 5000)
        self.fill_E.setValue(1500)
        self.fill_E.setSuffix(" MPa")
        self.fill_E.setToolTip("Modulo elastico del materiale di riempimento")
        closure_layout.addRow("Modulo E:", self.fill_E)

        # Modulo taglio G
        self.fill_G = QSpinBox()
        self.fill_G.setRange(0, 2000)
        self.fill_G.setValue(500)
        self.fill_G.setSuffix(" MPa")
        self.fill_G.setToolTip("Modulo di taglio del materiale di riempimento")
        closure_layout.addRow("Modulo G:", self.fill_G)

        # Resistenza fk
        self.fill_fk = QDoubleSpinBox()
        self.fill_fk.setRange(0, 10)
        self.fill_fk.setValue(2.4)
        self.fill_fk.setSingleStep(0.1)
        self.fill_fk.setSuffix(" MPa")
        self.fill_fk.setToolTip("Resistenza caratteristica a compressione")
        closure_layout.addRow("Resistenza fk:", self.fill_fk)

        # Resistenza taglio tau0
        self.fill_tau0 = QDoubleSpinBox()
        self.fill_tau0.setRange(0, 1)
        self.fill_tau0.setValue(0.06)
        self.fill_tau0.setSingleStep(0.01)
        self.fill_tau0.setDecimals(3)
        self.fill_tau0.setSuffix(" MPa")
        self.fill_tau0.setToolTip("Resistenza a taglio iniziale")
        closure_layout.addRow("Resistenza τ₀:", self.fill_tau0)

        # Separatore
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        closure_layout.addRow(separator2)

        # === AMMORSAMENTO ===
        amm_label = QLabel("<b>Ammorsamento e contributo</b>")
        closure_layout.addRow(amm_label)

        # Ammorsamento
        self.has_connection = QCheckBox("Ammorsamento con muratura esistente")
        self.has_connection.setChecked(True)
        self.has_connection.toggled.connect(self._on_connection_changed)
        closure_layout.addRow("", self.has_connection)

        # Profondità ammorsamento
        self.connection_depth = QSpinBox()
        self.connection_depth.setRange(5, 30)
        self.connection_depth.setValue(12)
        self.connection_depth.setSuffix(" cm")
        closure_layout.addRow("Prof. ammorsamento:", self.connection_depth)

        # Efficienza collegamento
        self.connection_efficiency = QSpinBox()
        self.connection_efficiency.setRange(0, 100)
        self.connection_efficiency.setValue(50)
        self.connection_efficiency.setSuffix(" %")
        self.connection_efficiency.setToolTip("Efficienza del collegamento con muratura esistente (0-100%)")
        closure_layout.addRow("Efficienza collegamento:", self.connection_efficiency)

        # Separatore
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        closure_layout.addRow(separator3)

        # === CONTRIBUTI CALCOLO ===
        contrib_label = QLabel("<b>Contributo al calcolo parete</b>")
        closure_layout.addRow(contrib_label)

        # Contributo rigidezza
        self.stiffness_contribution = QSpinBox()
        self.stiffness_contribution.setRange(0, 100)
        self.stiffness_contribution.setValue(80)
        self.stiffness_contribution.setSuffix(" %")
        self.stiffness_contribution.setToolTip("Percentuale della rigidezza del riempimento che viene considerata")
        closure_layout.addRow("Contributo rigidezza:", self.stiffness_contribution)

        # Contributo resistenza
        self.resistance_contribution = QSpinBox()
        self.resistance_contribution.setRange(0, 100)
        self.resistance_contribution.setValue(70)
        self.resistance_contribution.setSuffix(" %")
        self.resistance_contribution.setToolTip("Percentuale della resistenza del riempimento che viene considerata")
        closure_layout.addRow("Contributo resistenza:", self.resistance_contribution)

        self.closure_group.setLayout(closure_layout)
        self.closure_group.setEnabled(False)
        layout.addWidget(self.closure_group)

        # Info box
        info_label = QLabel(
            "<i>Nota: Il riempimento contribuisce parzialmente alla rigidezza e resistenza "
            "della parete, in base al tipo di materiale e qualità dell'ammorsamento.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(info_label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _on_closure_material_changed(self, index):
        """Aggiorna proprietà strutturali in base al materiale selezionato"""
        # Valori default per ogni tipo di materiale (da FillMaterial.get_default_properties)
        defaults = {
            0: (1500, 500, 2.4, 0.06, 80, 70),   # Mattoni pieni
            1: (1000, 400, 1.0, 0.04, 50, 40),   # Mattoni forati
            2: (2000, 800, 3.0, 0.08, 90, 80),   # Blocchi cls
            3: (1200, 480, 1.5, 0.05, 60, 50),   # Blocchi laterizio
            4: (50, 20, 0.1, 0.01, 5, 0),        # Cartongesso
            5: (500, 200, 0.5, 0.02, 30, 10),    # Vetrocemento
            6: (200, 80, 0.3, 0.02, 20, 5),      # Pannello tamponamento
            7: (1500, 500, 2.0, 0.06, 70, 60),   # Muratura esistente
        }
        if index in defaults:
            E, G, fk, tau0, K_pct, V_pct = defaults[index]
            self.fill_E.setValue(E)
            self.fill_G.setValue(G)
            self.fill_fk.setValue(fk)
            self.fill_tau0.setValue(tau0)
            self.stiffness_contribution.setValue(K_pct)
            self.resistance_contribution.setValue(V_pct)

    def _on_connection_changed(self, checked):
        """Abilita/disabilita campi ammorsamento"""
        self.connection_depth.setEnabled(checked)
        self.connection_efficiency.setEnabled(checked)
        if not checked:
            self.connection_efficiency.setValue(30)  # Efficienza ridotta senza ammorsamento
        
    def connect_signals(self):
        """Connette tutti i segnali"""
        # Cambio tipo apertura
        self.opening_type.currentIndexChanged.connect(self.on_type_changed)
        
        # Arco
        self.arch_type.currentIndexChanged.connect(self.update_arch_preview)
        self.impost_height.valueChanged.connect(self.update_arch_preview)
        self.arch_rise.valueChanged.connect(self.update_arch_preview)
        self.width_spin.valueChanged.connect(self.update_arch_preview)
        self.arch_thickness_check.toggled.connect(
            lambda checked: self.arch_thickness.setEnabled(checked)
        )
        # Aggiorna altezza calcolata per archi
        self.impost_height.valueChanged.connect(self._update_arch_height_calc)
        self.arch_rise.valueChanged.connect(self._update_arch_height_calc)
        
        # Circolare
        self.diameter.valueChanged.connect(self.update_circular_preview)
        self.center_offset_check.toggled.connect(
            lambda checked: self.circular_offset_group.setEnabled(checked)
        )
        
        # Ovale
        self.oval_orientation.currentIndexChanged.connect(self.update_oval_preview)
        self.axis_ratio.valueChanged.connect(self.update_oval_preview)

        # Ellittica - sincronizza dimensioni base
        self.semi_major.valueChanged.connect(self._update_ellipse_dimensions)
        self.semi_minor.valueChanged.connect(self._update_ellipse_dimensions)

        # Nicchia
        self.is_niche.toggled.connect(
            lambda checked: self.niche_group.setEnabled(checked)
        )
        self.has_shelves.toggled.connect(
            lambda checked: self.n_shelves.setEnabled(checked)
        )
        
        # Chiusura
        self.is_closure.toggled.connect(
            lambda checked: self.closure_group.setEnabled(checked)
        )
        self.has_connection.toggled.connect(
            lambda checked: self.connection_depth.setEnabled(checked)
        )
        
    def on_type_changed(self, index):
        """Gestisce cambio tipo apertura con aggiornamento dinamico campi"""
        # Indici: 0=Rett, 1=Arco, 2=Circ, 3=Ovale, 4=Ellisse, 5=Nicchia, 6=Chiusura

        # Mostra/nasconde tab appropriati
        self.shape_stack.setCurrentIndex(min(index, 4))

        # Abilita/disabilita tab
        self.tabs.setTabEnabled(2, index == 5)  # Tab nicchia
        self.tabs.setTabEnabled(3, index == 6)  # Tab chiusura

        # Gestione dinamica campi in base al tipo
        self._update_geometry_fields_visibility(index)

        # Auto-seleziona checkbox appropriati
        if index == 5:  # Nicchia
            self.is_niche.setChecked(True)
            self.tabs.setCurrentIndex(2)
        elif index == 6:  # Chiusura
            self.is_closure.setChecked(True)
            self.existing_check.setChecked(True)  # La chiusura implica esistente
            self.tabs.setCurrentIndex(3)

    def _update_geometry_fields_visibility(self, type_index):
        """Aggiorna visibilità e comportamento campi geometria in base al tipo"""
        # Reset stato base
        self.width_spin.setEnabled(True)
        self.height_spin.setEnabled(True)
        self.width_label.setVisible(True)
        self.width_spin.setVisible(True)
        self.height_label.setVisible(True)
        self.height_spin.setVisible(True)
        self.height_calc_label.setVisible(False)
        self.dim_info_label.setText("")
        self.position_group.setVisible(True)

        if type_index == 0:  # Rettangolare
            self.dim_info_label.setText("Definisci larghezza e altezza dell'apertura rettangolare")
            self.width_label.setText("Larghezza:")
            self.height_label.setText("Altezza:")

        elif type_index == 1:  # Ad arco
            self.dim_info_label.setText("L'altezza totale sarà calcolata da imposta + freccia arco")
            self.width_label.setText("Luce netta:")
            self.height_label.setText("Altezza totale:")
            self.height_spin.setEnabled(False)
            self.height_calc_label.setVisible(True)
            self._update_arch_height_calc()
            # Vai al tab Forma Avanzata per configurare l'arco
            self.tabs.setCurrentIndex(1)

        elif type_index == 2:  # Circolare
            self.dim_info_label.setText("Per forme circolari, usa il diametro nel tab Forma Avanzata")
            self.width_label.setText("Larghezza (= diametro):")
            self.height_label.setText("Altezza (= diametro):")
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            # Vai al tab Forma Avanzata
            self.tabs.setCurrentIndex(1)

        elif type_index == 3:  # Ovale
            self.dim_info_label.setText("Configura orientamento e rapporto assi nel tab Forma Avanzata")
            self.width_label.setText("Larghezza:")
            self.height_label.setText("Altezza:")
            # Vai al tab Forma Avanzata
            self.tabs.setCurrentIndex(1)

        elif type_index == 4:  # Ellittica
            self.dim_info_label.setText("Configura semi-assi e rotazione nel tab Forma Avanzata")
            self.width_label.setText("Larghezza:")
            self.height_label.setText("Altezza:")
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            # Vai al tab Forma Avanzata
            self.tabs.setCurrentIndex(1)

        elif type_index == 5:  # Nicchia
            self.dim_info_label.setText("Definisci dimensioni della nicchia (cavità non passante)")
            self.width_label.setText("Larghezza nicchia:")
            self.height_label.setText("Altezza nicchia:")

        elif type_index == 6:  # Chiusura vano esistente
            self.dim_info_label.setText("Inserisci le dimensioni del vano da chiudere")
            self.width_label.setText("Larghezza vano:")
            self.height_label.setText("Altezza vano:")

    def _update_arch_height_calc(self):
        """Calcola e mostra altezza totale per apertura ad arco"""
        if self.opening_type.currentIndex() != 1:  # Solo per archi
            return
        impost = self.impost_height.value()
        rise = self.arch_rise.value()
        total_height = impost + rise
        self.height_spin.setValue(total_height)
        self.height_calc_label.setText(f"Altezza calcolata: {impost} (imposta) + {rise} (freccia) = {total_height} cm")

    def _update_ellipse_dimensions(self):
        """Aggiorna dimensioni base in base ai semi-assi ellittici"""
        if self.opening_type.currentIndex() != 4:  # Solo per ellisse
            return
        # Larghezza = 2 * semi-asse maggiore, Altezza = 2 * semi-asse minore (o viceversa)
        self.width_spin.setValue(self.semi_major.value() * 2)
        self.height_spin.setValue(self.semi_minor.value() * 2)

    def update_arch_preview(self):
        """Aggiorna anteprima parametri arco"""
        width = self.width_spin.value()
        rise = self.arch_rise.value()
        
        # Calcola raggio per arco tutto sesto
        if self.arch_type.currentIndex() == 0:  # Tutto sesto
            radius = width / 2
            chord = width
        else:
            # Formula generica per arco ribassato
            radius = (rise**2 + (width/2)**2) / (2 * rise)
            chord = width
            
        self.arch_preview.setText(
            f"Raggio: {radius:.1f} cm\n"
            f"Corda: {chord:.1f} cm\n"
            f"Altezza totale: {self.impost_height.value() + rise} cm"
        )
        
    def update_circular_preview(self):
        """Aggiorna anteprima circolare"""
        # Le dimensioni base vengono ignorate per forma circolare
        self.width_spin.setValue(self.diameter.value())
        self.height_spin.setValue(self.diameter.value())
        
    def update_oval_preview(self):
        """Aggiorna anteprima ovale"""
        if self.oval_orientation.currentIndex() == 0:  # Verticale
            major = self.height_spin.value()
            minor = major / self.axis_ratio.value()
        else:  # Orizzontale
            major = self.width_spin.value()
            minor = major / self.axis_ratio.value()
            
        self.oval_preview.setText(
            f"Asse maggiore: {major:.1f} cm\n"
            f"Asse minore: {minor:.1f} cm"
        )
        
    def validate_and_accept(self):
        """Valida i dati prima di accettare"""
        # Validazioni base
        if self.width_spin.value() <= 0 or self.height_spin.value() <= 0:
            QMessageBox.warning(self, "Attenzione", 
                              "Le dimensioni devono essere positive")
            return
            
        # Validazioni specifiche per tipo
        opening_type = self.opening_type.currentIndex()
        
        if opening_type == 1:  # Arco
            if self.arch_rise.value() > self.width_spin.value() / 2:
                if self.arch_type.currentIndex() == 0:  # Tutto sesto
                    QMessageBox.warning(self, "Attenzione",
                                      "Per arco a tutto sesto la freccia deve essere metà della luce")
                    return
                    
        elif opening_type == 2:  # Circolare
            # Nessuna validazione extra necessaria
            pass
            
        self.accept()
        
    def get_data(self):
        """Restituisce tutti i dati dell'apertura"""
        data = {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'x': self.x_spin.value(),
            'y': self.y_spin.value(),
            'type': self.opening_type.currentText(),
            'existing': self.existing_check.isChecked(),
            'notes': self.notes_text.toPlainText()
        }
        
        # Dati specifici per tipo
        opening_type = self.opening_type.currentIndex()
        
        if opening_type == 1:  # Arco
            data['arch_data'] = {
                'arch_type': self.arch_type.currentText(),
                'impost_height': self.impost_height.value(),
                'arch_rise': self.arch_rise.value(),
                'custom_thickness': self.arch_thickness_check.isChecked(),
                'arch_thickness': self.arch_thickness.value() if self.arch_thickness_check.isChecked() else None,
                'ribassamento': self.ribassamento.value() if self.arch_type.currentIndex() == 1 else None,
                'n_centers': self.n_centers.value() if self.arch_type.currentIndex() == 3 else None
            }
            
        elif opening_type == 2:  # Circolare
            data['circular_data'] = {
                'diameter': self.diameter.value(),
                'custom_center': self.center_offset_check.isChecked(),
                'center_x_offset': self.center_x_offset.value() if self.center_offset_check.isChecked() else 0,
                'center_y_offset': self.center_y_offset.value() if self.center_offset_check.isChecked() else 0
            }
            
        elif opening_type == 3:  # Ovale
            data['oval_data'] = {
                'orientation': self.oval_orientation.currentText(),
                'axis_ratio': self.axis_ratio.value()
            }
            
        elif opening_type == 4:  # Ellittica
            data['ellipse_data'] = {
                'semi_major': self.semi_major.value(),
                'semi_minor': self.semi_minor.value(),
                'rotation': self.ellipse_rotation.value()
            }
            
        # Dati nicchia
        if self.is_niche.isChecked():
            data['niche_data'] = {
                'is_niche': True,
                'depth': self.niche_depth.value(),
                'type': self.niche_type.currentText(),
                'back_material': self.niche_back_material.currentText(),
                'has_shelves': self.has_shelves.isChecked(),
                'n_shelves': self.n_shelves.value() if self.has_shelves.isChecked() else 0
            }
            
        # Dati chiusura
        if self.is_closure.isChecked():
            # Mappa indice materiale a FillType
            material_to_fill_type = {
                0: 1,  # Mattoni pieni -> SOLID_BRICK
                1: 2,  # Mattoni forati -> HOLLOW_BRICK
                2: 3,  # Blocchi cls -> CONCRETE_BLOCK
                3: 4,  # Blocchi laterizio -> LATERIZIO_BLOCK
                4: 5,  # Cartongesso -> DRYWALL
                5: 6,  # Vetrocemento -> GLASS_BLOCK
                6: 7,  # Pannello tamponamento -> INFILL_PANEL
                7: 8,  # Muratura esistente -> EXISTING_MASONRY
            }
            fill_type = material_to_fill_type.get(self.closure_material.currentIndex(), 0)

            data['closure_data'] = {
                'is_closure': True,
                'type': self.closure_type.currentText(),
                'material': self.closure_material.currentText(),
                'thickness': self.closure_thickness.value(),
                'has_connection': self.has_connection.isChecked(),
                'connection_depth': self.connection_depth.value() if self.has_connection.isChecked() else 0
            }

            # fill_material per integrazione con modello Opening
            data['fill_material'] = {
                'fill_type': fill_type,
                'thickness': self.closure_thickness.value(),
                'E': self.fill_E.value(),
                'G': self.fill_G.value(),
                'fk': self.fill_fk.value(),
                'tau0': self.fill_tau0.value(),
                'has_connection': self.has_connection.isChecked(),
                'connection_depth': self.connection_depth.value() if self.has_connection.isChecked() else 0,
                'connection_efficiency': self.connection_efficiency.value() / 100.0,
                'stiffness_contribution': self.stiffness_contribution.value(),
                'resistance_contribution': self.resistance_contribution.value()
            }
        else:
            # Nessun riempimento
            data['fill_material'] = {
                'fill_type': 0,  # NONE
                'thickness': 0,
                'E': 0, 'G': 0, 'fk': 0, 'tau0': 0,
                'has_connection': False,
                'connection_depth': 0,
                'connection_efficiency': 0,
                'stiffness_contribution': 0,
                'resistance_contribution': 0
            }

        return data
        
    def load_data(self, data):
        """Carica dati esistenti"""
        # Dati base
        self.width_spin.setValue(data.get('width', 120))
        self.height_spin.setValue(data.get('height', 230))
        self.x_spin.setValue(data.get('x', 50))
        self.y_spin.setValue(data.get('y', 0))
        
        # Tipo apertura
        type_text = data.get('type', 'Rettangolare')
        index = self.opening_type.findText(type_text)
        if index >= 0:
            self.opening_type.setCurrentIndex(index)
            
        self.existing_check.setChecked(data.get('existing', False))
        self.notes_text.setPlainText(data.get('notes', ''))
        
        # Dati specifici per tipo
        if 'arch_data' in data:
            arch = data['arch_data']
            idx = self.arch_type.findText(arch.get('arch_type', 'Tutto sesto'))
            if idx >= 0:
                self.arch_type.setCurrentIndex(idx)
            self.impost_height.setValue(arch.get('impost_height', 180))
            self.arch_rise.setValue(arch.get('arch_rise', 60))
            self.arch_thickness_check.setChecked(arch.get('custom_thickness', False))
            if arch.get('arch_thickness'):
                self.arch_thickness.setValue(arch['arch_thickness'])
                
        elif 'circular_data' in data:
            circ = data['circular_data']
            self.diameter.setValue(circ.get('diameter', 100))
            self.center_offset_check.setChecked(circ.get('custom_center', False))
            self.center_x_offset.setValue(circ.get('center_x_offset', 0))
            self.center_y_offset.setValue(circ.get('center_y_offset', 0))
            
        elif 'oval_data' in data:
            oval = data['oval_data']
            idx = self.oval_orientation.findText(oval.get('orientation', 'Verticale'))
            if idx >= 0:
                self.oval_orientation.setCurrentIndex(idx)
            self.axis_ratio.setValue(oval.get('axis_ratio', 1.5))
            
        elif 'ellipse_data' in data:
            ell = data['ellipse_data']
            self.semi_major.setValue(ell.get('semi_major', 80))
            self.semi_minor.setValue(ell.get('semi_minor', 60))
            self.ellipse_rotation.setValue(ell.get('rotation', 0))
            
        # Dati nicchia
        if 'niche_data' in data:
            niche = data['niche_data']
            self.is_niche.setChecked(True)
            self.niche_depth.setValue(niche.get('depth', 15))
            idx = self.niche_type.findText(niche.get('type', 'Libreria'))
            if idx >= 0:
                self.niche_type.setCurrentIndex(idx)
            idx = self.niche_back_material.findText(niche.get('back_material', 'Muratura esistente'))
            if idx >= 0:
                self.niche_back_material.setCurrentIndex(idx)
            self.has_shelves.setChecked(niche.get('has_shelves', False))
            self.n_shelves.setValue(niche.get('n_shelves', 4))
            
        # Dati chiusura
        if 'closure_data' in data:
            closure = data['closure_data']
            self.is_closure.setChecked(True)
            idx = self.closure_type.findText(closure.get('type', 'Muratura piena'))
            if idx >= 0:
                self.closure_type.setCurrentIndex(idx)
            idx = self.closure_material.findText(closure.get('material', 'Mattoni pieni'))
            if idx >= 0:
                self.closure_material.setCurrentIndex(idx)
            self.closure_thickness.setValue(closure.get('thickness', 12))
            self.has_connection.setChecked(closure.get('has_connection', True))
            self.connection_depth.setValue(closure.get('connection_depth', 12))

        # Dati fill_material (se presenti, sovrascrivono closure_data)
        if 'fill_material' in data:
            fill = data['fill_material']
            fill_type = fill.get('fill_type', 0)

            if fill_type > 0:  # C'è un riempimento
                self.is_closure.setChecked(True)
                # Mappa FillType a indice combobox
                fill_type_to_index = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7}
                idx = fill_type_to_index.get(fill_type, 0)
                self.closure_material.setCurrentIndex(idx)

                self.closure_thickness.setValue(fill.get('thickness', 12))
                self.fill_E.setValue(int(fill.get('E', 1500)))
                self.fill_G.setValue(int(fill.get('G', 500)))
                self.fill_fk.setValue(fill.get('fk', 2.4))
                self.fill_tau0.setValue(fill.get('tau0', 0.06))
                self.has_connection.setChecked(fill.get('has_connection', False))
                self.connection_depth.setValue(fill.get('connection_depth', 12))
                eff = fill.get('connection_efficiency', 0.5)
                self.connection_efficiency.setValue(int(eff * 100) if eff <= 1 else int(eff))
                self.stiffness_contribution.setValue(int(fill.get('stiffness_contribution', 80)))
                self.resistance_contribution.setValue(int(fill.get('resistance_contribution', 70)))

        # Aggiorna visibilità campi in base al tipo caricato
        current_type = self.opening_type.currentIndex()
        self._update_geometry_fields_visibility(current_type)