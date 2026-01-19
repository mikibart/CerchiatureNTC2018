"""
Modulo Input Struttura
Gestisce l'inserimento dei dati geometrici del muro
Versione aggiornata con gestione materiali avanzata
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import re
from datetime import datetime

# Import aggiornati
from src.gui.dialogs.opening_dialog_advanced import AdvancedOpeningDialog
from src.widgets.wall_canvas_advanced import AdvancedWallCanvas
from src.core.database.materials_database import MaterialsDatabase, MaterialEditorDialog

# Fallback imports per compatibilità
try:
    from src.widgets.wall_canvas_advanced import AdvancedWallCanvas
except ImportError:
    try:
        from ...widgets.wall_canvas_advanced import AdvancedWallCanvas
    except ImportError:
        print("Errore import AdvancedWallCanvas - creando classe placeholder")
        class AdvancedWallCanvas(QWidget):
            def __init__(self):
                super().__init__()
            def set_wall_data(self, *args): pass
            def add_opening(self, *args): pass
            def remove_opening(self, *args): pass
            def update(self): pass


class OpeningDialog(QDialog):
    """Dialog semplice per inserimento aperture (fallback per AdvancedOpeningDialog)"""

    def __init__(self, parent=None, opening_data=None):
        super().__init__(parent)
        self.setWindowTitle("Definizione Apertura")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.opening_data = opening_data or {}
        self.setup_ui()

        if opening_data:
            self.load_data(opening_data)

    def setup_ui(self):
        layout = QFormLayout()

        # Tipo apertura
        self.opening_type = QComboBox()
        self.opening_type.addItems(["Rettangolare", "Ad arco"])
        layout.addRow("Tipo:", self.opening_type)

        # Apertura esistente
        self.existing_check = QCheckBox("Apertura esistente")
        layout.addRow("", self.existing_check)

        # Dimensioni
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 1000)
        self.width_spin.setValue(120)
        self.width_spin.setSuffix(" cm")
        layout.addRow("Larghezza:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 500)
        self.height_spin.setValue(210)
        self.height_spin.setSuffix(" cm")
        layout.addRow("Altezza:", self.height_spin)

        # Posizione X
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(100)
        self.x_spin.setSuffix(" cm")
        layout.addRow("Posizione X:", self.x_spin)

        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_data(self, data):
        """Carica dati apertura esistente"""
        if 'type' in data:
            idx = self.opening_type.findText(data['type'])
            if idx >= 0:
                self.opening_type.setCurrentIndex(idx)
        self.existing_check.setChecked(data.get('existing', False))
        self.width_spin.setValue(data.get('width', 120))
        self.height_spin.setValue(data.get('height', 210))
        self.x_spin.setValue(data.get('x', 100))

    def get_data(self):
        """Restituisce dati apertura"""
        return {
            'type': self.opening_type.currentText(),
            'existing': self.existing_check.isChecked(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'x': self.x_spin.value(),
            'y': 0
        }


class MaterialsManagerDialog(QDialog):
    """Dialog per gestione completa database materiali"""

    def __init__(self, parent=None, materials_db=None):
        super().__init__(parent)
        self.materials_db = materials_db
        self.setWindowTitle("Gestione Database Materiali")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_materials()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Aggiungi")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.add_btn.clicked.connect(self.add_material)
        toolbar_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Modifica")
        self.edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.edit_btn.clicked.connect(self.edit_material)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Elimina")
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_btn.clicked.connect(self.delete_material)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        self.duplicate_btn = QPushButton("Duplica")
        self.duplicate_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.duplicate_btn.clicked.connect(self.duplicate_material)
        self.duplicate_btn.setEnabled(False)
        toolbar_layout.addWidget(self.duplicate_btn)
        
        toolbar_layout.addStretch()
        
        # Filtro categoria
        toolbar_layout.addWidget(QLabel("Categoria:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Tutte")
        self.category_filter.currentTextChanged.connect(self.filter_materials)
        toolbar_layout.addWidget(self.category_filter)
        
        layout.addLayout(toolbar_layout)
        
        # Tabella materiali
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(8)
        self.materials_table.setHorizontalHeaderLabels([
            "Nome", "Categoria", "fcm\n[MPa]", "τ0\n[MPa]", 
            "E\n[MPa]", "G\n[MPa]", "γ\n[kN/m³]", "Tipo"
        ])
        self.materials_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.materials_table.doubleClicked.connect(self.edit_material)
        
        # Larghezza colonne
        self.materials_table.setColumnWidth(0, 300)
        self.materials_table.setColumnWidth(1, 100)
        self.materials_table.setColumnWidth(7, 100)
        
        layout.addWidget(self.materials_table)
        
        # Info panel
        info_group = QGroupBox("Dettagli Materiale")
        info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Pulsanti dialog
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def load_materials(self):
        """Carica materiali nella tabella"""
        self.materials_table.setRowCount(0)
        
        # Aggiorna categorie
        categories = self.materials_db.get_categories()
        self.category_filter.blockSignals(True)
        current_cat = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("Tutte")
        self.category_filter.addItems(categories)
        
        # Ripristina selezione
        index = self.category_filter.findText(current_cat)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)
        self.category_filter.blockSignals(False)
        
        # Carica materiali
        all_materials = self.materials_db.get_all_materials()
        
        for key, material in all_materials.items():
            self.add_material_row(key, material)
            
    def add_material_row(self, key, material):
        """Aggiunge riga materiale alla tabella"""
        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        
        # Nome
        name_item = QTableWidgetItem(material['name'])
        name_item.setData(Qt.UserRole, key)
        self.materials_table.setItem(row, 0, name_item)
        
        # Altri campi
        self.materials_table.setItem(row, 1, QTableWidgetItem(material.get('category', '')))
        self.materials_table.setItem(row, 2, QTableWidgetItem(f"{material.get('fcm', 0):.1f}"))
        self.materials_table.setItem(row, 3, QTableWidgetItem(f"{material.get('tau0', 0):.3f}"))
        self.materials_table.setItem(row, 4, QTableWidgetItem(str(material.get('E', 0))))
        self.materials_table.setItem(row, 5, QTableWidgetItem(str(material.get('G', 0))))
        self.materials_table.setItem(row, 6, QTableWidgetItem(f"{material.get('w', 0):.1f}"))
        
        # Tipo
        tipo = "Normativo" if material.get('normative', False) else "Personalizzato"
        tipo_item = QTableWidgetItem(tipo)
        
        # Colora diversamente
        if material.get('normative', False):
            tipo_item.setBackground(QColor(220, 255, 220))
        else:
            tipo_item.setBackground(QColor(255, 255, 220))
            
        self.materials_table.setItem(row, 7, tipo_item)
        
        # Disabilita modifica per materiali normativi
        if material.get('normative', False):
            for col in range(self.materials_table.columnCount()):
                item = self.materials_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    
    def filter_materials(self, category):
        """Filtra materiali per categoria"""
        for row in range(self.materials_table.rowCount()):
            if category == "Tutte":
                self.materials_table.setRowHidden(row, False)
            else:
                cat_item = self.materials_table.item(row, 1)
                if cat_item:
                    self.materials_table.setRowHidden(row, cat_item.text() != category)
                    
    def on_selection_changed(self):
        """Gestisce cambio selezione"""
        selected = self.materials_table.selectedItems()
        if selected:
            row = selected[0].row()
            key = self.materials_table.item(row, 0).data(Qt.UserRole)
            material = self.materials_db.get_material(key)
            
            # Mostra info
            if material:
                info = f"Chiave: {key}\n"
                if material.get('normative'):
                    info += f"Riferimento: {material.get('reference', 'N.D.')}\n"
                if 'notes' in material:
                    info += f"\nNote: {material['notes']}"
                    
                self.info_text.setText(info)
                
                # Abilita pulsanti
                is_custom = not material.get('normative', False)
                self.edit_btn.setEnabled(is_custom)
                self.delete_btn.setEnabled(is_custom)
                self.duplicate_btn.setEnabled(True)
        else:
            self.info_text.clear()
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
            
    def add_material(self):
        """Aggiunge nuovo materiale"""
        dialog = MaterialEditorDialog(self)
        if dialog.exec_():
            material_data = dialog.get_data()
            
            # Genera chiave
            key = re.sub(r'[^\w\s-]', '', material_data['name'].lower())
            key = re.sub(r'[-\s]+', '_', key)
            key = f"custom_{key}"
            
            # Verifica unicità
            if self.materials_db.get_material(key):
                key = f"{key}_{int(QDateTime.currentDateTime().toSecsSinceEpoch())}"
                
            if self.materials_db.add_custom_material(key, material_data):
                self.load_materials()
                
    def edit_material(self):
        """Modifica materiale selezionato"""
        selected = self.materials_table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        key = self.materials_table.item(row, 0).data(Qt.UserRole)
        material = self.materials_db.get_material(key)
        
        if material and not material.get('normative', False):
            dialog = MaterialEditorDialog(self, material, key)
            if dialog.exec_():
                material_data = dialog.get_data()
                if self.materials_db.update_custom_material(key, material_data):
                    self.load_materials()
                    
    def delete_material(self):
        """Elimina materiale selezionato"""
        selected = self.materials_table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        key = self.materials_table.item(row, 0).data(Qt.UserRole)
        material = self.materials_db.get_material(key)
        
        if material and not material.get('normative', False):
            reply = QMessageBox.question(
                self, "Conferma eliminazione",
                f"Eliminare il materiale '{material['name']}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.materials_db.delete_custom_material(key):
                    self.load_materials()
                    
    def duplicate_material(self):
        """Duplica materiale selezionato"""
        selected = self.materials_table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        key = self.materials_table.item(row, 0).data(Qt.UserRole)
        material = self.materials_db.get_material(key)
        
        if material:
            # Crea copia
            new_material = material.copy()
            new_material['name'] = f"{material['name']} - Copia"
            new_material['normative'] = False
            new_material['custom'] = True
            
            dialog = MaterialEditorDialog(self, new_material)
            if dialog.exec_():
                material_data = dialog.get_data()
                
                # Genera nuova chiave
                new_key = re.sub(r'[^\w\s-]', '', material_data['name'].lower())
                new_key = re.sub(r'[-\s]+', '_', new_key)
                new_key = f"custom_{new_key}"
                
                if self.materials_db.add_custom_material(new_key, material_data):
                    self.load_materials()


class InputModule(QWidget):
    """Modulo per input dati struttura con gestione materiali avanzata"""
    
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # Aggiungi database materiali
        self.materials_db = MaterialsDatabase()
        self.materials_db.database_updated.connect(self.update_materials_list)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Costruisce interfaccia input"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pannello sinistro - Input dati
        left_panel = self.create_left_panel()
        
        # Pannello destro - Visualizzazione
        right_panel = self.create_right_panel()
        
        # Splitter per ridimensionamento pannelli
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)  # Pannello sinistro
        splitter.setStretchFactor(1, 3)  # Pannello destro più grande
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def create_left_panel(self):
        """Crea pannello sinistro con input dati"""
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # Scroll area per contenere tutti i gruppi
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 1. Informazioni progetto
        project_group = self.create_project_group()
        scroll_layout.addWidget(project_group)
        
        # 2. Geometria muro
        wall_group = self.create_wall_group()
        scroll_layout.addWidget(wall_group)
        
        # 3. Caratteristiche muratura (versione aggiornata)
        masonry_group = self.create_masonry_group()
        scroll_layout.addWidget(masonry_group)
        
        # 4. Aperture
        openings_group = self.create_openings_group()
        scroll_layout.addWidget(openings_group)
        
        # 5. Carichi
        loads_group = self.create_loads_group()
        scroll_layout.addWidget(loads_group)
        
        # 6. Vincoli
        constraints_group = self.create_constraints_group()
        scroll_layout.addWidget(constraints_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        left_layout.addWidget(scroll)
        left_panel.setLayout(left_layout)
        
        return left_panel
        
    def create_right_panel(self):
        """Crea pannello destro con visualizzazione"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Titolo
        title_label = QLabel("<h3>Anteprima Struttura</h3>")
        right_layout.addWidget(title_label)
        
        # Canvas avanzato per disegno muro
        self.wall_canvas = AdvancedWallCanvas()
        self.wall_canvas.setMinimumSize(600, 400)
        right_layout.addWidget(self.wall_canvas)
        
        # Info riepilogo
        info_group = QGroupBox("Riepilogo")
        info_layout = QGridLayout()
        
        self.info_labels = {}
        info_items = [
            ('wall_area', 'Area muro:'),
            ('openings_count', 'N° aperture:'),
            ('openings_area', 'Area apertura:'),
            ('masonry_percentage', '% muratura residua:'),
            ('vertical_load', 'Carico verticale:')
        ]
        
        for i, (key, label) in enumerate(info_items):
            info_layout.addWidget(QLabel(label), i, 0)
            self.info_labels[key] = QLabel("-")
            self.info_labels[key].setStyleSheet("font-weight: bold;")
            info_layout.addWidget(self.info_labels[key], i, 1)
            
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        right_panel.setLayout(right_layout)
        return right_panel
        
    def create_project_group(self):
        """Crea gruppo informazioni progetto"""
        group = QGroupBox("Informazioni Progetto")
        layout = QFormLayout()
        
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Nome del progetto...")
        layout.addRow("Nome progetto:", self.project_name)
        
        self.project_location = QLineEdit()
        self.project_location.setPlaceholderText("Via/Piazza, Città...")
        layout.addRow("Ubicazione:", self.project_location)
        
        self.project_client = QLineEdit()
        self.project_client.setPlaceholderText("Nome committente...")
        layout.addRow("Committente:", self.project_client)
        
        self.project_date = QDateEdit()
        self.project_date.setDate(QDate.currentDate())
        self.project_date.setCalendarPopup(True)
        layout.addRow("Data:", self.project_date)
        
        group.setLayout(layout)
        return group
        
    def create_wall_group(self):
        """Crea gruppo geometria muro"""
        group = QGroupBox("Geometria Muro")
        layout = QGridLayout()
        
        # Lunghezza
        layout.addWidget(QLabel("Lunghezza L:"), 0, 0)
        self.wall_length = QSpinBox()
        self.wall_length.setRange(100, 2000)
        self.wall_length.setValue(423)
        self.wall_length.setSuffix(" cm")
        self.wall_length.setToolTip("Lunghezza totale del muro")
        layout.addWidget(self.wall_length, 0, 1)
        
        # Altezza
        layout.addWidget(QLabel("Altezza H:"), 1, 0)
        self.wall_height = QSpinBox()
        self.wall_height.setRange(100, 1000)
        self.wall_height.setValue(350)
        self.wall_height.setSuffix(" cm")
        self.wall_height.setToolTip("Altezza del muro")
        layout.addWidget(self.wall_height, 1, 1)
        
        # Spessore
        layout.addWidget(QLabel("Spessore s:"), 2, 0)
        self.wall_thickness = QSpinBox()
        self.wall_thickness.setRange(10, 100)
        self.wall_thickness.setValue(30)
        self.wall_thickness.setSuffix(" cm")
        self.wall_thickness.setToolTip("Spessore del muro")
        layout.addWidget(self.wall_thickness, 2, 1)
        
        group.setLayout(layout)
        return group
        
    def create_masonry_group(self):
        """Crea gruppo caratteristiche muratura con gestione avanzata"""
        group = QGroupBox("Caratteristiche Muratura")
        layout = QGridLayout()
        
        # Tipologia con database espanso
        layout.addWidget(QLabel("Tipologia:"), 0, 0)
        self.masonry_type = QComboBox()
        self.masonry_type.setMaximumWidth(500)
        self.update_materials_list()  # Popola la lista
        layout.addWidget(self.masonry_type, 0, 1, 1, 3)
        
        # Pulsante gestione materiali
        self.manage_materials_btn = QPushButton("Gestisci")
        self.manage_materials_btn.setMaximumWidth(80)
        self.manage_materials_btn.setToolTip("Gestisci database materiali")
        self.manage_materials_btn.clicked.connect(self.show_materials_manager)
        layout.addWidget(self.manage_materials_btn, 0, 4)
        
        # Livello conoscenza
        layout.addWidget(QLabel("Livello conoscenza:"), 1, 0)
        self.knowledge_level = QComboBox()
        self.knowledge_level.addItems(["LC1 (FC=1.35)", "LC2 (FC=1.20)", "LC3 (FC=1.00)"])
        layout.addWidget(self.knowledge_level, 1, 1, 1, 3)
        
        # Parametri meccanici
        layout.addWidget(QLabel("f<sub>cm</sub> [N/mm²]:"), 2, 0)
        self.fcm = QDoubleSpinBox()
        self.fcm.setRange(0.1, 10.0)
        self.fcm.setValue(2.0)
        self.fcm.setDecimals(1)
        self.fcm.setSingleStep(0.1)
        layout.addWidget(self.fcm, 2, 1)
        
        layout.addWidget(QLabel("τ<sub>0</sub> [N/mm²]:"), 2, 2)
        self.tau0 = QDoubleSpinBox()
        self.tau0.setRange(0.001, 1.0)
        self.tau0.setValue(0.074)
        self.tau0.setDecimals(3)
        self.tau0.setSingleStep(0.001)
        layout.addWidget(self.tau0, 2, 3)
        
        layout.addWidget(QLabel("E [N/mm²]:"), 3, 0)
        self.E_modulus = QSpinBox()
        self.E_modulus.setRange(100, 10000)
        self.E_modulus.setValue(1410)
        self.E_modulus.setSingleStep(10)
        layout.addWidget(self.E_modulus, 3, 1)
        
        layout.addWidget(QLabel("G [N/mm²]:"), 3, 2)
        self.G_modulus = QSpinBox()
        self.G_modulus.setRange(50, 5000)
        self.G_modulus.setValue(470)
        self.G_modulus.setSingleStep(10)
        layout.addWidget(self.G_modulus, 3, 3)
        
        layout.addWidget(QLabel("γ [kN/m³]:"), 4, 0)
        self.gamma = QDoubleSpinBox()
        self.gamma.setRange(10.0, 30.0)
        self.gamma.setValue(14.5)
        self.gamma.setDecimals(1)
        layout.addWidget(self.gamma, 4, 1)
        
        # Checkbox per modifiche manuali
        self.manual_params = QCheckBox("Modifica manuale parametri")
        self.manual_params.setToolTip("Permette di modificare i parametri indipendentemente dal materiale selezionato")
        layout.addWidget(self.manual_params, 5, 0, 1, 2)
        
        # Info materiale
        self.material_info_label = QLabel("")
        self.material_info_label.setWordWrap(True)
        self.material_info_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; }")
        layout.addWidget(self.material_info_label, 5, 2, 1, 3)
        
        # Valori di progetto (con FC applicato)
        design_group = QGroupBox("Valori di Progetto")
        design_layout = QGridLayout()
        
        design_layout.addWidget(QLabel("f<sub>cmd</sub>:"), 0, 0)
        self.fcm_d_label = QLabel("-")
        self.fcm_d_label.setStyleSheet("font-weight: bold;")
        design_layout.addWidget(self.fcm_d_label, 0, 1)
        
        design_layout.addWidget(QLabel("τ<sub>0d</sub>:"), 0, 2)
        self.tau0_d_label = QLabel("-")
        self.tau0_d_label.setStyleSheet("font-weight: bold;")
        design_layout.addWidget(self.tau0_d_label, 0, 3)
        
        design_group.setLayout(design_layout)
        layout.addWidget(design_group, 6, 0, 1, 5)
        
        group.setLayout(layout)
        
        # Connessioni
        self.masonry_type.currentIndexChanged.connect(self.on_masonry_type_changed_advanced)
        self.knowledge_level.currentIndexChanged.connect(self.update_design_values)
        self.manual_params.toggled.connect(self.on_manual_params_toggled)
        self.fcm.valueChanged.connect(self.on_param_changed)
        self.tau0.valueChanged.connect(self.on_param_changed)
        
        return group
        
    def update_materials_list(self):
        """Aggiorna lista materiali nel ComboBox"""
        current_text = self.masonry_type.currentText()
        
        self.masonry_type.blockSignals(True)
        self.masonry_type.clear()
        
        # Ottieni lista materiali dal database
        materials_list = self.materials_db.get_display_list()
        self.masonry_type.addItems(materials_list)
        
        # Ripristina selezione se possibile
        index = self.masonry_type.findText(current_text)
        if index >= 0:
            self.masonry_type.setCurrentIndex(index)
        else:
            # Seleziona blocchi di tufo come default
            default_index = self.masonry_type.findText("Muratura in blocchi di tufo")
            if default_index >= 0:
                self.masonry_type.setCurrentIndex(default_index)
                
        self.masonry_type.blockSignals(False)
        
    def on_masonry_type_changed_advanced(self):
        """Gestisce cambio tipo muratura con database avanzato"""
        material_name = self.masonry_type.currentText()
        
        # Controlla se è l'opzione per aggiungere materiale personalizzato
        if "Aggiungi materiale personalizzato" in material_name:
            self.add_custom_material()
            return
            
        # Rimuovi indicatore [Personalizzato] se presente
        if "[Personalizzato]" in material_name:
            material_name = material_name.replace(" [Personalizzato]", "")
            
        # Ottieni dati materiale dal database
        material = self.materials_db.get_material_by_name(material_name)
        
        if material and not self.manual_params.isChecked():
            # Carica parametri automaticamente
            self.fcm.blockSignals(True)
            self.tau0.blockSignals(True)
            self.E_modulus.blockSignals(True)
            self.G_modulus.blockSignals(True)
            self.gamma.blockSignals(True)
            
            self.fcm.setValue(material.get('fcm', 2.0))
            self.tau0.setValue(material.get('tau0', 0.074))
            self.E_modulus.setValue(material.get('E', 1410))
            self.G_modulus.setValue(material.get('G', 470))
            self.gamma.setValue(material.get('w', 14.5))
            
            self.fcm.blockSignals(False)
            self.tau0.blockSignals(False)
            self.E_modulus.blockSignals(False)
            self.G_modulus.blockSignals(False)
            self.gamma.blockSignals(False)
            
            # Aggiorna info materiale
            if material.get('normative', False):
                info = f"Materiale normativo - {material.get('reference', '')}"
            else:
                info = "Materiale personalizzato"
                
            if 'notes' in material:
                info += f"\n{material['notes']}"
                
            self.material_info_label.setText(info)
            
            # Aggiorna valori di progetto
            self.update_design_values()
            
        # Emetti segnale di modifica
        self.data_changed.emit()
        
    def on_manual_params_toggled(self, checked):
        """Gestisce toggle modifica manuale"""
        # Abilita/disabilita spin box parametri
        self.fcm.setReadOnly(not checked)
        self.tau0.setReadOnly(not checked)
        self.E_modulus.setReadOnly(not checked)
        self.G_modulus.setReadOnly(not checked)
        self.gamma.setReadOnly(not checked)
        
        # Cambia stile per indicare stato
        style = "QSpinBox, QDoubleSpinBox { background-color: #ffffcc; }" if checked else ""
        self.fcm.setStyleSheet(style)
        self.tau0.setStyleSheet(style)
        self.E_modulus.setStyleSheet(style)
        self.G_modulus.setStyleSheet(style)
        self.gamma.setStyleSheet(style)
        
        if checked:
            self.material_info_label.setText("⚠️ Modifica manuale attiva - I parametri non si aggiorneranno automaticamente")
        else:
            # Ricarica parametri dal materiale selezionato
            self.on_masonry_type_changed_advanced()
            
    def on_param_changed(self):
        """Chiamato quando un parametro viene modificato manualmente"""
        if self.manual_params.isChecked():
            self.update_design_values()
            self.data_changed.emit()
            
    def update_design_values(self):
        """Aggiorna valori di progetto con FC applicato"""
        FC = self.get_confidence_factor(self.knowledge_level.currentText())
        
        fcm_d = self.fcm.value() / FC
        tau0_d = self.tau0.value() / FC
        
        self.fcm_d_label.setText(f"{fcm_d:.3f} MPa")
        self.tau0_d_label.setText(f"{tau0_d:.4f} MPa")
        
    def get_confidence_factor(self, level_text):
        """Estrae fattore di confidenza dal testo"""
        if "FC=1.35" in level_text:
            return 1.35
        elif "FC=1.20" in level_text:
            return 1.20
        else:
            return 1.00
            
    def show_materials_manager(self):
        """Mostra dialog gestione materiali"""
        dialog = MaterialsManagerDialog(self, self.materials_db)
        if dialog.exec_():
            # Aggiorna lista se ci sono state modifiche
            self.update_materials_list()
            
    def add_custom_material(self):
        """Aggiunge nuovo materiale personalizzato"""
        dialog = MaterialEditorDialog(self)
        if dialog.exec_():
            material_data = dialog.get_data()
            
            # Genera chiave univoca
            key = re.sub(r'[^\w\s-]', '', material_data['name'].lower())
            key = re.sub(r'[-\s]+', '_', key)
            
            # Aggiungi al database
            if self.materials_db.add_custom_material(f"custom_{key}", material_data):
                QMessageBox.information(self, "Successo", 
                                      "Materiale aggiunto con successo")
                                      
                # Seleziona il nuovo materiale
                self.update_materials_list()
                index = self.masonry_type.findText(f"{material_data['name']} [Personalizzato]")
                if index >= 0:
                    self.masonry_type.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "Errore",
                                   "Impossibile aggiungere il materiale")
                                   
        # Ripristina selezione precedente se annullato
        else:
            self.masonry_type.setCurrentIndex(0)
        
    def create_openings_group(self):
        """Crea gruppo aperture"""
        group = QGroupBox("Aperture")
        layout = QVBoxLayout()
        
        # Lista aperture
        self.openings_list = QListWidget()
        self.openings_list.setMaximumHeight(150)
        self.openings_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.openings_list)
        
        # Pulsanti aperture
        buttons_layout = QHBoxLayout()
        
        self.add_opening_btn = QPushButton("Aggiungi")
        self.add_opening_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOkButton))
        buttons_layout.addWidget(self.add_opening_btn)
        
        self.edit_opening_btn = QPushButton("Modifica")
        self.edit_opening_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.edit_opening_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_opening_btn)
        
        self.remove_opening_btn = QPushButton("Rimuovi")
        self.remove_opening_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.remove_opening_btn.setEnabled(False)
        buttons_layout.addWidget(self.remove_opening_btn)
        
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
        
    def create_loads_group(self):
        """Crea gruppo carichi"""
        group = QGroupBox("Carichi")
        layout = QGridLayout()
        
        # Carico verticale
        layout.addWidget(QLabel("Carico verticale N:"), 0, 0)
        self.vertical_load = QDoubleSpinBox()
        self.vertical_load.setRange(0, 10000)
        self.vertical_load.setValue(0)
        self.vertical_load.setSuffix(" kN")
        self.vertical_load.setToolTip("Carico verticale totale agente sul muro")
        layout.addWidget(self.vertical_load, 0, 1)
        
        # Eccentricità
        layout.addWidget(QLabel("Eccentricità e:"), 1, 0)
        self.eccentricity = QSpinBox()
        self.eccentricity.setRange(-50, 50)
        self.eccentricity.setValue(0)
        self.eccentricity.setSuffix(" cm")
        self.eccentricity.setToolTip("Eccentricità del carico rispetto all'asse del muro")
        layout.addWidget(self.eccentricity, 1, 1)
        
        # Nota su carico zero
        note_label = QLabel(
            "<small><i>Nota: Per risultati realistici, inserire il carico verticale "
            "effettivo (tipicamente 100-300 kN per pareti portanti)</i></small>"
        )
        note_label.setWordWrap(True)
        layout.addWidget(note_label, 2, 0, 1, 2)
        
        group.setLayout(layout)
        return group
        
    def create_constraints_group(self):
        """Crea gruppo vincoli"""
        group = QGroupBox("Condizioni di Vincolo")
        layout = QGridLayout()
        
        # Vincolo al piede
        layout.addWidget(QLabel("Vincolo al piede:"), 0, 0)
        self.bottom_constraint = QComboBox()
        self.bottom_constraint.addItems(["Incastro", "Cerniera"])
        layout.addWidget(self.bottom_constraint, 0, 1)
        
        # Vincolo in testa
        layout.addWidget(QLabel("Vincolo in testa:"), 1, 0)
        self.top_constraint = QComboBox()
        self.top_constraint.addItems(["Incastro (Grinter)", "Libero (Mensola)"])
        layout.addWidget(self.top_constraint, 1, 1)
        
        group.setLayout(layout)
        return group
        
    def connect_signals(self):
        """Connette i segnali"""
        # Geometria muro
        self.wall_length.valueChanged.connect(self.on_wall_changed)
        self.wall_height.valueChanged.connect(self.on_wall_changed)
        self.wall_thickness.valueChanged.connect(self.on_wall_changed)
        
        # Aperture
        self.add_opening_btn.clicked.connect(self.add_opening)
        self.edit_opening_btn.clicked.connect(self.edit_opening)
        self.remove_opening_btn.clicked.connect(self.remove_opening)
        self.openings_list.itemSelectionChanged.connect(self.on_opening_selection_changed)
        self.openings_list.itemDoubleClicked.connect(self.edit_opening)
        
        # Altri cambiamenti
        self.project_name.textChanged.connect(lambda: self.data_changed.emit())
        self.project_location.textChanged.connect(lambda: self.data_changed.emit())
        self.project_client.textChanged.connect(lambda: self.data_changed.emit())
        self.vertical_load.valueChanged.connect(self.update_info)
        
    def on_wall_changed(self):
        """Chiamato quando cambiano le dimensioni del muro"""
        self.wall_canvas.set_wall_data(
            self.wall_length.value(),
            self.wall_height.value(),
            self.wall_thickness.value()
        )
        self.update_info()
        self.data_changed.emit()
        
    def on_opening_selection_changed(self):
        """Chiamato quando cambia la selezione apertura"""
        has_selection = len(self.openings_list.selectedItems()) > 0
        self.edit_opening_btn.setEnabled(has_selection)
        self.remove_opening_btn.setEnabled(has_selection)
        
    def add_opening(self):
        """Aggiunge nuova apertura"""
        dialog = AdvancedOpeningDialog(self)
        if dialog.exec_():
            opening_data = dialog.get_data()
            
            # Valida posizione
            if self.validate_opening_position(opening_data):
                self.wall_canvas.add_opening(opening_data)
                self.update_openings_list()
                self.update_info()
                self.data_changed.emit()
            else:
                QMessageBox.warning(
                    self, "Posizione non valida",
                    "L'apertura esce dai limiti del muro o si sovrappone ad altre aperture."
                )
                
    def edit_opening(self):
        """Modifica apertura selezionata"""
        current_row = self.openings_list.currentRow()
        if current_row >= 0:
            opening_data = self.wall_canvas.openings[current_row]
            dialog = AdvancedOpeningDialog(self, opening_data)
            if dialog.exec_():
                new_data = dialog.get_data()
                
                # Rimuovi temporaneamente l'apertura corrente per validazione
                temp_openings = self.wall_canvas.openings.copy()
                temp_openings.pop(current_row)
                
                if self.validate_opening_position(new_data, temp_openings):
                    self.wall_canvas.openings[current_row] = new_data
                    self.wall_canvas.update()
                    self.update_openings_list()
                    self.update_info()
                    self.data_changed.emit()
                else:
                    QMessageBox.warning(
                        self, "Posizione non valida",
                        "L'apertura esce dai limiti del muro o si sovrappone ad altre aperture."
                    )
                    
    def remove_opening(self):
        """Rimuove apertura selezionata"""
        current_row = self.openings_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, 'Conferma',
                'Rimuovere l\'apertura selezionata?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.wall_canvas.remove_opening(current_row)
                self.update_openings_list()
                self.update_info()
                self.data_changed.emit()
                
    def validate_opening_position(self, opening_data, existing_openings=None):
        """Valida che l'apertura sia entro i limiti e non si sovrapponga"""
        if existing_openings is None:
            existing_openings = self.wall_canvas.openings
            
        # Verifica limiti muro
        wall_length = self.wall_length.value()
        wall_height = self.wall_height.value()
        
        if (opening_data['x'] < 0 or 
            opening_data['y'] < 0 or
            opening_data['x'] + opening_data['width'] > wall_length or
            opening_data['y'] + opening_data['height'] > wall_height):
            return False
            
        # Verifica sovrapposizioni
        for other in existing_openings:
            if (opening_data['x'] < other['x'] + other['width'] and
                opening_data['x'] + opening_data['width'] > other['x'] and
                opening_data['y'] < other['y'] + other['height'] and
                opening_data['y'] + opening_data['height'] > other['y']):
                return False
                
        return True
        
    def update_openings_list(self):
        """Aggiorna lista aperture"""
        self.openings_list.clear()
        for i, opening in enumerate(self.wall_canvas.openings):
            text = f"A{i+1}: {opening['type']} {opening['width']}×{opening['height']}cm"
            if opening.get('existing'):
                text += " (esistente)"
            text += f" - Pos: ({opening['x']}, {opening['y']})"
            self.openings_list.addItem(text)
            
    def update_info(self):
        """Aggiorna informazioni riepilogo"""
        # Area muro
        wall_area = self.wall_length.value() * self.wall_height.value() / 10000  # m²
        self.info_labels['wall_area'].setText(f"{wall_area:.2f} m²")
        
        # Numero aperture
        n_openings = len(self.wall_canvas.openings)
        self.info_labels['openings_count'].setText(str(n_openings))
        
        # Area aperture
        openings_area = sum(
            op['width'] * op['height'] / 10000 
            for op in self.wall_canvas.openings
        )
        self.info_labels['openings_area'].setText(f"{openings_area:.2f} m²")
        
        # Percentuale muratura residua
        if wall_area > 0:
            masonry_percentage = ((wall_area - openings_area) / wall_area) * 100
            self.info_labels['masonry_percentage'].setText(f"{masonry_percentage:.1f}%")
        else:
            self.info_labels['masonry_percentage'].setText("-")
            
        # Carico verticale
        vertical_load = self.vertical_load.value()
        self.info_labels['vertical_load'].setText(f"{vertical_load:.1f} kN")
        
    def collect_data(self):
        """Raccoglie tutti i dati del modulo"""
        return {
            'info': {
                'name': self.project_name.text(),
                'location': self.project_location.text(),
                'client': self.project_client.text(),
                'date': self.project_date.date().toString(Qt.ISODate),
                'engineer': 'Arch. Michelangelo Bartolotta'
            },
            'wall': {
                'length': self.wall_length.value(),
                'height': self.wall_height.value(),
                'thickness': self.wall_thickness.value()
            },
            'masonry': {
                'type': self.masonry_type.currentText(),
                'knowledge_level': self.knowledge_level.currentText(),
                'fcm': self.fcm.value(),
                'tau0': self.tau0.value(),
                'E': self.E_modulus.value(),
                'G': self.G_modulus.value(),
                'gamma': self.gamma.value()
            },
            'openings': self.wall_canvas.openings,
            'loads': {
                'vertical': self.vertical_load.value(),
                'eccentricity': self.eccentricity.value()
            },
            'constraints': {
                'bottom': self.bottom_constraint.currentText(),
                'top': self.top_constraint.currentText()
            }
        }
        
    def load_data(self, data):
        """Carica dati da dizionario"""
        # Info progetto
        info = data.get('info', {})
        self.project_name.setText(info.get('name', ''))
        self.project_location.setText(info.get('location', ''))
        self.project_client.setText(info.get('client', ''))
        if 'date' in info:
            self.project_date.setDate(QDate.fromString(info['date'], Qt.ISODate))
            
        # Geometria muro
        wall = data.get('wall', {})
        self.wall_length.setValue(wall.get('length', 423))
        self.wall_height.setValue(wall.get('height', 350))
        self.wall_thickness.setValue(wall.get('thickness', 30))
        
        # Muratura
        masonry = data.get('masonry', {})
        if 'type' in masonry:
            index = self.masonry_type.findText(masonry['type'])
            if index >= 0:
                self.masonry_type.setCurrentIndex(index)
        if 'knowledge_level' in masonry:
            index = self.knowledge_level.findText(masonry['knowledge_level'])
            if index >= 0:
                self.knowledge_level.setCurrentIndex(index)
        self.fcm.setValue(masonry.get('fcm', 2.0))
        self.tau0.setValue(masonry.get('tau0', 0.074))
        self.E_modulus.setValue(masonry.get('E', 1410))
        self.G_modulus.setValue(masonry.get('G', 470))
        self.gamma.setValue(masonry.get('gamma', 14.5))
        
        # Aperture
        self.wall_canvas.openings = data.get('openings', [])
        self.wall_canvas.update()
        self.update_openings_list()
        
        # Carichi
        loads = data.get('loads', {})
        self.vertical_load.setValue(loads.get('vertical', 0))
        self.eccentricity.setValue(loads.get('eccentricity', 0))
        
        # Vincoli
        constraints = data.get('constraints', {})
        if 'bottom' in constraints:
            index = self.bottom_constraint.findText(constraints['bottom'])
            if index >= 0:
                self.bottom_constraint.setCurrentIndex(index)
        if 'top' in constraints:
            index = self.top_constraint.findText(constraints['top'])
            if index >= 0:
                self.top_constraint.setCurrentIndex(index)
                
        # Aggiorna visualizzazione
        self.on_wall_changed()
        self.update_info()
        
    def reset(self):
        """Reset completo del modulo"""
        # Reset campi
        self.project_name.clear()
        self.project_location.clear()
        self.project_client.clear()
        self.project_date.setDate(QDate.currentDate())
        
        self.wall_length.setValue(423)
        self.wall_height.setValue(350)
        self.wall_thickness.setValue(30)
        
        # Reset materiali al default
        self.update_materials_list()
        default_index = self.masonry_type.findText("Muratura in blocchi di tufo")
        if default_index >= 0:
            self.masonry_type.setCurrentIndex(default_index)
        self.knowledge_level.setCurrentIndex(0)
        
        self.vertical_load.setValue(0)
        self.eccentricity.setValue(0)
        
        self.bottom_constraint.setCurrentIndex(0)
        self.top_constraint.setCurrentIndex(0)
        
        # Reset aperture
        self.wall_canvas.openings = []
        self.wall_canvas.update()
        self.update_openings_list()
        
        # Aggiorna
        self.on_wall_changed()
        self.update_info()