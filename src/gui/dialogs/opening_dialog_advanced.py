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
        
        # Dimensioni base (sempre visibili)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 1000)
        self.width_spin.setValue(120)
        self.width_spin.setSuffix(" cm")
        layout.addRow("Larghezza:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 1000)
        self.height_spin.setValue(230)
        self.height_spin.setSuffix(" cm")
        layout.addRow("Altezza totale:", self.height_spin)
        
        # Posizione
        position_group = QGroupBox("Posizione")
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
        
        position_group.setLayout(pos_layout)
        layout.addRow(position_group)
        
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
        """Tab per chiusura vani esistenti"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Attiva chiusura
        self.is_closure = QCheckBox("Chiusura di vano esistente")
        layout.addRow("", self.is_closure)
        
        # Gruppo parametri chiusura
        self.closure_group = QGroupBox("Parametri Chiusura")
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
        
        # Materiale chiusura
        self.closure_material = QComboBox()
        self.closure_material.addItems([
            "Mattoni pieni",
            "Mattoni forati",
            "Blocchi cls",
            "Blocchi laterizio",
            "Cartongesso",
            "Vetrocemento",
            "Altro"
        ])
        closure_layout.addRow("Materiale:", self.closure_material)
        
        # Spessore chiusura
        self.closure_thickness = QSpinBox()
        self.closure_thickness.setRange(5, 50)
        self.closure_thickness.setValue(12)
        self.closure_thickness.setSuffix(" cm")
        closure_layout.addRow("Spessore:", self.closure_thickness)
        
        # Ammorsamento
        self.has_connection = QCheckBox("Ammorsamento con muratura esistente")
        self.has_connection.setChecked(True)
        closure_layout.addRow("", self.has_connection)
        
        # Profondità ammorsamento
        self.connection_depth = QSpinBox()
        self.connection_depth.setRange(5, 30)
        self.connection_depth.setValue(12)
        self.connection_depth.setSuffix(" cm")
        closure_layout.addRow("Prof. ammorsamento:", self.connection_depth)
        
        self.closure_group.setLayout(closure_layout)
        self.closure_group.setEnabled(False)
        layout.addRow(self.closure_group)
        
        widget.setLayout(layout)
        return widget
        
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
        
        # Circolare
        self.diameter.valueChanged.connect(self.update_circular_preview)
        self.center_offset_check.toggled.connect(
            lambda checked: self.circular_offset_group.setEnabled(checked)
        )
        
        # Ovale
        self.oval_orientation.currentIndexChanged.connect(self.update_oval_preview)
        self.axis_ratio.valueChanged.connect(self.update_oval_preview)
        
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
        """Gestisce cambio tipo apertura"""
        # Indici: 0=Rett, 1=Arco, 2=Circ, 3=Ovale, 4=Ellisse, 5=Nicchia, 6=Chiusura
        
        # Mostra/nasconde tab appropriati
        self.shape_stack.setCurrentIndex(min(index, 4))
        
        # Abilita/disabilita tab
        self.tabs.setTabEnabled(2, index == 5)  # Tab nicchia
        self.tabs.setTabEnabled(3, index == 6)  # Tab chiusura
        
        # Auto-seleziona checkbox appropriati
        if index == 5:  # Nicchia
            self.is_niche.setChecked(True)
            self.tabs.setCurrentIndex(2)
        elif index == 6:  # Chiusura
            self.is_closure.setChecked(True)
            self.tabs.setCurrentIndex(3)
            
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
            data['closure_data'] = {
                'is_closure': True,
                'type': self.closure_type.currentText(),
                'material': self.closure_material.currentText(),
                'thickness': self.closure_thickness.value(),
                'has_connection': self.has_connection.isChecked(),
                'connection_depth': self.connection_depth.value() if self.has_connection.isChecked() else 0
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