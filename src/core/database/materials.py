"""
Database Materiali Muratura secondo NTC 2018 con supporto materiali personalizzati
Arch. Michelangelo Bartolotta
"""

import json
import os
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal

class MaterialsDatabase(QObject):
    """Database materiali muratura con gestione personalizzata"""
    
    # Segnale emesso quando il database viene modificato
    database_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.materials = {}
        self.custom_materials = {}
        self.init_default_materials()
        self.load_custom_materials()
        
    def init_default_materials(self):
        """Inizializza materiali da normativa NTC 2018 Tab. C8.5.I"""
        self.materials = {
            # Muratura in pietrame
            'pietrame_disordinata': {
                'name': 'Muratura in pietrame disordinata',
                'category': 'Pietrame',
                'fcm': 1.0,      # N/mm² - Resistenza media compressione
                'tau0': 0.020,   # N/mm² - Resistenza media taglio
                'E': 870,        # N/mm² - Modulo elastico medio
                'G': 290,        # N/mm² - Modulo di elasticità tangenziale
                'w': 19.0,       # kN/m³ - Peso specifico
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 1'
            },
            'pietrame_sbozzata': {
                'name': 'Muratura a conci sbozzati, con paramento di limitato spessore e nucleo interno',
                'category': 'Pietrame',
                'fcm': 2.0,
                'tau0': 0.035,
                'E': 1050,
                'G': 350,
                'w': 20.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 2'
            },
            'pietrame_buona': {
                'name': 'Muratura in pietre a spacco con buona tessitura',
                'category': 'Pietrame',
                'fcm': 2.6,
                'tau0': 0.056,
                'E': 1260,
                'G': 420,
                'w': 21.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 3'
            },
            'pietrame_blocchi': {
                'name': 'Muratura a blocchi lapidei squadrati',
                'category': 'Pietrame',
                'fcm': 5.8,
                'tau0': 0.090,
                'E': 1740,
                'G': 580,
                'w': 22.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 4'
            },
            
            # Muratura in mattoni
            'mattoni_pieni': {
                'name': 'Muratura in mattoni pieni e malta di calce',
                'category': 'Mattoni',
                'fcm': 2.4,
                'tau0': 0.060,
                'E': 1500,
                'G': 500,
                'w': 18.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 5'
            },
            'mattoni_semipieni': {
                'name': 'Muratura in mattoni semipieni con malta cementizia',
                'category': 'Mattoni',
                'fcm': 3.8,
                'tau0': 0.092,
                'E': 1740,
                'G': 580,
                'w': 15.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 6'
            },
            'mattoni_forati': {
                'name': 'Muratura in mattoni forati con malta cementizia',
                'category': 'Mattoni',
                'fcm': 2.8,
                'tau0': 0.056,
                'E': 1080,
                'G': 360,
                'w': 12.0,
                'normative': True,
                'reference': 'Tab. C8.5.I - riga 7'
            },
            
            # Muratura in blocchi
            'blocchi_tufo': {
                'name': 'Muratura in blocchi di tufo',
                'category': 'Blocchi',
                'fcm': 2.0,
                'tau0': 0.074,
                'E': 1410,
                'G': 470,
                'w': 14.5,
                'normative': True,
                'reference': 'Tab. C8.5.I'
            },
            'blocchi_calcarenite': {
                'name': 'Muratura in blocchi di calcarenite',
                'category': 'Blocchi',
                'fcm': 2.0,
                'tau0': 0.074,
                'E': 1410,
                'G': 470,
                'w': 14.5,
                'normative': True,
                'reference': 'Tab. C8.5.I'
            },
            'blocchi_cls': {
                'name': 'Muratura in blocchi di calcestruzzo',
                'category': 'Blocchi',
                'fcm': 3.0,
                'tau0': 0.080,
                'E': 1800,
                'G': 600,
                'w': 16.0,
                'normative': True,
                'reference': 'Tab. C8.5.I'
            },
            'blocchi_laterizio': {
                'name': 'Muratura in blocchi di laterizio',
                'category': 'Blocchi',
                'fcm': 4.0,
                'tau0': 0.100,
                'E': 2400,
                'G': 800,
                'w': 11.0,
                'normative': True,
                'reference': 'Tab. C8.5.I'
            },
            
            # Muratura mista
            'mista': {
                'name': 'Muratura mista (pietrame + mattoni)',
                'category': 'Mista',
                'fcm': 1.8,
                'tau0': 0.025,
                'E': 1200,
                'G': 400,
                'w': 19.0,
                'normative': True,
                'reference': 'Tab. C8.5.I'
            }
        }
        
    def load_custom_materials(self):
        """Carica materiali personalizzati da file"""
        try:
            # Path del file materiali personalizzati
            app_data_dir = os.path.expanduser("~/.cerchiature_ntc2018")
            os.makedirs(app_data_dir, exist_ok=True)
            
            custom_file = os.path.join(app_data_dir, "custom_materials.json")
            
            if os.path.exists(custom_file):
                with open(custom_file, 'r', encoding='utf-8') as f:
                    self.custom_materials = json.load(f)
                    
        except Exception as e:
            print(f"Errore caricamento materiali personalizzati: {e}")
            self.custom_materials = {}
            
    def save_custom_materials(self):
        """Salva materiali personalizzati su file"""
        try:
            app_data_dir = os.path.expanduser("~/.cerchiature_ntc2018")
            os.makedirs(app_data_dir, exist_ok=True)
            
            custom_file = os.path.join(app_data_dir, "custom_materials.json")
            
            with open(custom_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_materials, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"Errore salvataggio materiali personalizzati: {e}")
            return False
            
    def get_all_materials(self) -> Dict:
        """Restituisce tutti i materiali (normativi + personalizzati)"""
        all_materials = self.materials.copy()
        all_materials.update(self.custom_materials)
        return all_materials
        
    def get_categories(self) -> List[str]:
        """Restituisce lista categorie disponibili"""
        categories = set()
        
        for material in self.get_all_materials().values():
            categories.add(material.get('category', 'Altro'))
            
        return sorted(list(categories))
        
    def get_materials_by_category(self, category: str) -> Dict:
        """Restituisce materiali di una categoria"""
        result = {}
        
        for key, material in self.get_all_materials().items():
            if material.get('category') == category:
                result[key] = material
                
        return result
        
    def get_material(self, key: str) -> Optional[Dict]:
        """Restituisce un materiale specifico"""
        all_materials = self.get_all_materials()
        return all_materials.get(key)
        
    def get_material_by_name(self, name: str) -> Optional[Dict]:
        """Restituisce materiale per nome"""
        for key, material in self.get_all_materials().items():
            if material['name'] == name:
                return material
        return None
        
    def add_custom_material(self, key: str, material_data: Dict) -> bool:
        """Aggiunge un materiale personalizzato"""
        # Validazione dati
        required_fields = ['name', 'fcm', 'tau0', 'E', 'G', 'w']
        for field in required_fields:
            if field not in material_data:
                return False
                
        # Aggiungi flag personalizzato
        material_data['normative'] = False
        material_data['custom'] = True
        
        # Aggiungi al database
        self.custom_materials[key] = material_data
        
        # Salva su file
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
            
        return False
        
    def update_custom_material(self, key: str, material_data: Dict) -> bool:
        """Aggiorna un materiale personalizzato"""
        if key not in self.custom_materials:
            return False
            
        self.custom_materials[key] = material_data
        
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
            
        return False
        
    def delete_custom_material(self, key: str) -> bool:
        """Elimina un materiale personalizzato"""
        if key not in self.custom_materials:
            return False
            
        del self.custom_materials[key]
        
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
            
        return False
        
    def get_display_list(self) -> List[str]:
        """Restituisce lista materiali per ComboBox"""
        display_list = []
        
        # Prima i materiali normativi per categoria
        for category in self.get_categories():
            materials = self.get_materials_by_category(category)
            
            # Separa normativi e custom
            normative = {k: v for k, v in materials.items() if v.get('normative', False)}
            custom = {k: v for k, v in materials.items() if not v.get('normative', False)}
            
            # Aggiungi normativi
            for material in normative.values():
                display_list.append(material['name'])
                
            # Aggiungi custom con indicazione
            for material in custom.values():
                display_list.append(f"{material['name']} [Personalizzato]")
                
        # Aggiungi opzione per personalizzato
        display_list.append("--- Aggiungi materiale personalizzato ---")
        
        return display_list
        
    def calculate_reduced_values(self, material: Dict, FC: float = 1.0) -> Dict:
        """Calcola valori ridotti per fattore di confidenza"""
        reduced = material.copy()
        
        # Applica FC solo a resistenze
        reduced['fcm_d'] = material['fcm'] / FC
        reduced['tau0_d'] = material['tau0'] / FC
        
        # Moduli elastici non vengono ridotti
        reduced['E_d'] = material['E']
        reduced['G_d'] = material['G']
        
        return reduced


class MaterialEditorDialog(QDialog):
    """Dialog per aggiunta/modifica materiali personalizzati"""
    
    def __init__(self, parent=None, material_data=None, key=None):
        super().__init__(parent)
        self.material_data = material_data
        self.key = key
        self.setWindowTitle("Materiale Personalizzato")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
        if material_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form dati materiale
        form_layout = QFormLayout()
        
        # Nome
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Es: Muratura in blocchi di pietra locale")
        form_layout.addRow("Nome materiale:", self.name_edit)
        
        # Categoria
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(['Pietrame', 'Mattoni', 'Blocchi', 'Mista', 'Altro'])
        form_layout.addRow("Categoria:", self.category_combo)
        
        # Parametri meccanici
        params_group = QGroupBox("Parametri Meccanici")
        params_layout = QFormLayout()
        
        # fcm
        self.fcm_spin = QDoubleSpinBox()
        self.fcm_spin.setRange(0.1, 20.0)
        self.fcm_spin.setDecimals(1)
        self.fcm_spin.setSingleStep(0.1)
        self.fcm_spin.setSuffix(" N/mm²")
        self.fcm_spin.setToolTip("Resistenza media a compressione")
        params_layout.addRow("f<sub>cm</sub>:", self.fcm_spin)
        
        # tau0
        self.tau0_spin = QDoubleSpinBox()
        self.tau0_spin.setRange(0.001, 1.0)
        self.tau0_spin.setDecimals(3)
        self.tau0_spin.setSingleStep(0.001)
        self.tau0_spin.setSuffix(" N/mm²")
        self.tau0_spin.setToolTip("Resistenza media a taglio in assenza di compressione")
        params_layout.addRow("τ<sub>0</sub>:", self.tau0_spin)
        
        # E
        self.E_spin = QSpinBox()
        self.E_spin.setRange(100, 10000)
        self.E_spin.setSingleStep(10)
        self.E_spin.setSuffix(" N/mm²")
        self.E_spin.setToolTip("Modulo di elasticità normale medio")
        params_layout.addRow("E:", self.E_spin)
        
        # G
        self.G_spin = QSpinBox()
        self.G_spin.setRange(50, 5000)
        self.G_spin.setSingleStep(10)
        self.G_spin.setSuffix(" N/mm²")
        self.G_spin.setToolTip("Modulo di elasticità tangenziale medio")
        params_layout.addRow("G:", self.G_spin)
        
        # w
        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(5.0, 30.0)
        self.w_spin.setDecimals(1)
        self.w_spin.setSingleStep(0.5)
        self.w_spin.setSuffix(" kN/m³")
        self.w_spin.setToolTip("Peso specifico medio")
        params_layout.addRow("γ:", self.w_spin)
        
        params_group.setLayout(params_layout)
        
        # Note
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Note aggiuntive sul materiale (provenienza, riferimenti, etc.)")
        
        # Calcolo automatico G da E
        self.auto_G_check = QCheckBox("Calcola G automaticamente (G = E/2.4)")
        self.auto_G_check.setChecked(True)
        self.auto_G_check.toggled.connect(self.on_auto_G_changed)
        self.E_spin.valueChanged.connect(self.update_G_value)
        
        # Layout finale
        layout.addLayout(form_layout)
        layout.addWidget(params_group)
        layout.addWidget(self.auto_G_check)
        layout.addWidget(QLabel("Note:"))
        layout.addWidget(self.notes_edit)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def on_auto_G_changed(self, checked):
        """Gestisce cambio checkbox auto-calcolo G"""
        self.G_spin.setEnabled(not checked)
        if checked:
            self.update_G_value()
            
    def update_G_value(self):
        """Aggiorna valore G se auto-calcolo attivo"""
        if self.auto_G_check.isChecked():
            E = self.E_spin.value()
            G = int(E / 2.4)  # Rapporto tipico per murature
            self.G_spin.setValue(G)
            
    def validate_and_accept(self):
        """Valida dati prima di accettare"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Attenzione", 
                              "Inserire il nome del materiale")
            return
            
        # Verifica valori sensati
        if self.fcm_spin.value() <= 0 or self.tau0_spin.value() <= 0:
            QMessageBox.warning(self, "Attenzione",
                              "Le resistenze devono essere positive")
            return
            
        if self.G_spin.value() > self.E_spin.value():
            QMessageBox.warning(self, "Attenzione",
                              "G non può essere maggiore di E")
            return
            
        self.accept()
        
    def get_data(self):
        """Restituisce i dati del materiale"""
        return {
            'name': self.name_edit.text().strip(),
            'category': self.category_combo.currentText(),
            'fcm': self.fcm_spin.value(),
            'tau0': self.tau0_spin.value(),
            'E': self.E_spin.value(),
            'G': self.G_spin.value(),
            'w': self.w_spin.value(),
            'notes': self.notes_edit.toPlainText()
        }
        
    def load_data(self):
        """Carica dati esistenti"""
        if not self.material_data:
            return
            
        self.name_edit.setText(self.material_data.get('name', ''))
        
        # Categoria
        category = self.material_data.get('category', 'Altro')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setEditText(category)
            
        # Parametri
        self.fcm_spin.setValue(self.material_data.get('fcm', 1.0))
        self.tau0_spin.setValue(self.material_data.get('tau0', 0.02))
        self.E_spin.setValue(self.material_data.get('E', 1000))
        self.G_spin.setValue(self.material_data.get('G', 400))
        self.w_spin.setValue(self.material_data.get('w', 18.0))
        
        # Note
        self.notes_edit.setPlainText(self.material_data.get('notes', ''))
        
        # Disabilita auto-calcolo G se stiamo modificando
        self.auto_G_check.setChecked(False)