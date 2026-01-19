"""
Database materiali murari con valori normativi e personalizzati
Basato su NTC 2018 - Tabella C8.5.I
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os
from typing import Dict, List, Optional


class MaterialsDatabase(QObject):
    """Database centralizzato per materiali murari"""
    
    # Segnale emesso quando il database viene aggiornato
    database_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Path file database personalizzato
        self.custom_db_path = os.path.join(
            os.path.expanduser("~"),
            ".pushover_advanced",
            "custom_materials.json"
        )
        
        # Carica database
        self.materials = {}
        self.load_normative_materials()
        self.load_custom_materials()
        
    def load_normative_materials(self):
        """Carica materiali normativi da NTC 2018"""
        self.materials.update({
            # Muratura in pietrame disordinata
            "pietrame_disordinata": {
                "name": "Muratura in pietrame disordinata",
                "category": "Pietrame",
                "fcm": 1.0,    # N/mm² - Resistenza media a compressione
                "tau0": 0.020, # N/mm² - Resistenza media a taglio
                "E": 870,      # N/mm² - Modulo elastico normale
                "G": 290,      # N/mm² - Modulo elastico tangenziale
                "w": 19.0,     # kN/m³ - Peso specifico
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Muratura a conci di pietra tenera (tufo, calcarenite, ecc.)"
            },
            
            # Muratura a conci sbozzati
            "pietrame_sbozzati": {
                "name": "Muratura a conci sbozzati",
                "category": "Pietrame",
                "fcm": 2.0,
                "tau0": 0.035,
                "E": 1050,
                "G": 350,
                "w": 20.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Con paramento di limitato spessore e nucleo interno"
            },
            
            # Muratura in pietre a spacco
            "pietrame_spacco": {
                "name": "Muratura in pietre a spacco",
                "category": "Pietrame",
                "fcm": 2.6,
                "tau0": 0.056,
                "E": 1260,
                "G": 420,
                "w": 21.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Con buona tessitura"
            },
            
            # Muratura a blocchi lapidei squadrati
            "blocchi_lapidei": {
                "name": "Muratura a blocchi lapidei squadrati",
                "category": "Pietrame",
                "fcm": 5.8,
                "tau0": 0.090,
                "E": 2400,
                "G": 800,
                "w": 22.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I"
            },
            
            # Muratura in mattoni pieni e malta di calce
            "mattoni_pieni_calce": {
                "name": "Muratura in mattoni pieni e malta di calce",
                "category": "Mattoni",
                "fcm": 2.4,
                "tau0": 0.060,
                "E": 1500,
                "G": 500,
                "w": 18.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I"
            },
            
            # Muratura in mattoni semipieni
            "mattoni_semipieni": {
                "name": "Muratura in mattoni semipieni",
                "category": "Mattoni",
                "fcm": 3.8,
                "tau0": 0.080,
                "E": 2400,
                "G": 800,
                "w": 15.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Con malta cementizia (es. doppio UNI foratura ≤ 40%)"
            },
            
            # Muratura in blocchi di tufo
            "blocchi_tufo": {
                "name": "Muratura in blocchi di tufo",
                "category": "Blocchi",
                "fcm": 2.0,
                "tau0": 0.074,
                "E": 1410,
                "G": 470,
                "w": 14.5,
                "normative": True,
                "reference": "Valori medi da letteratura",
                "notes": "Valori tipici per tufo giallo napoletano"
            },
            
            # Muratura in blocchi di calcarenite
            "blocchi_calcarenite": {
                "name": "Muratura in blocchi di calcarenite",
                "category": "Blocchi",
                "fcm": 2.2,
                "tau0": 0.074,
                "E": 1500,
                "G": 500,
                "w": 16.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Blocchi di pietra tenera (tufo, calcarenite, ecc.)"
            },
            
            # Muratura in blocchi laterizi semipieni
            "blocchi_laterizio": {
                "name": "Muratura in blocchi laterizi semipieni",
                "category": "Blocchi",
                "fcm": 5.0,
                "tau0": 0.100,
                "E": 3500,
                "G": 875,
                "w": 12.0,
                "normative": True,
                "reference": "NTC 2018 - Tab. C8.5.I",
                "notes": "Percentuale di foratura φ < 45%"
            },
            
            # Muratura mista
            "muratura_mista": {
                "name": "Muratura mista",
                "category": "Mista",
                "fcm": 1.8,
                "tau0": 0.025,
                "E": 1200,
                "G": 400,
                "w": 18.0,
                "normative": True,
                "reference": "Valori indicativi",
                "notes": "Muratura mista pietra/mattoni"
            }
        })
        
    def load_custom_materials(self):
        """Carica materiali personalizzati da file"""
        try:
            if os.path.exists(self.custom_db_path):
                with open(self.custom_db_path, 'r', encoding='utf-8') as f:
                    custom_materials = json.load(f)
                    self.materials.update(custom_materials)
        except Exception as e:
            print(f"Errore caricamento materiali personalizzati: {e}")
            
    def save_custom_materials(self):
        """Salva materiali personalizzati su file"""
        try:
            # Crea directory se non esiste
            os.makedirs(os.path.dirname(self.custom_db_path), exist_ok=True)
            
            # Filtra solo materiali custom
            custom_materials = {
                k: v for k, v in self.materials.items() 
                if v.get('custom', False)
            }
            
            with open(self.custom_db_path, 'w', encoding='utf-8') as f:
                json.dump(custom_materials, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Errore salvataggio materiali: {e}")
            return False
            
    def get_material(self, key: str) -> Optional[Dict]:
        """Ottiene materiale per chiave"""
        return self.materials.get(key)
        
    def get_material_by_name(self, name: str) -> Optional[Dict]:
        """Ottiene materiale per nome"""
        # Rimuovi indicatore [Personalizzato] se presente
        clean_name = name.replace(" [Personalizzato]", "")
        
        for key, material in self.materials.items():
            if material['name'] == clean_name:
                return material
        return None
        
    def get_all_materials(self) -> Dict:
        """Restituisce tutti i materiali"""
        return self.materials.copy()
        
    def get_categories(self) -> List[str]:
        """Ottiene lista categorie uniche"""
        categories = set()
        for material in self.materials.values():
            if 'category' in material:
                categories.add(material['category'])
        return sorted(list(categories))
        
    def get_display_list(self) -> List[str]:
        """Ottiene lista per visualizzazione in ComboBox"""
        display_list = []
        
        # Prima materiali normativi
        for key, material in sorted(self.materials.items()):
            if material.get('normative', False):
                display_list.append(material['name'])
                
        # Poi materiali custom
        for key, material in sorted(self.materials.items()):
            if material.get('custom', False):
                display_list.append(f"{material['name']} [Personalizzato]")
                
        # Aggiungi opzione per aggiungere nuovo
        display_list.append("--- Aggiungi materiale personalizzato ---")
        
        return display_list
        
    def add_custom_material(self, key: str, material_data: Dict) -> bool:
        """Aggiunge materiale personalizzato"""
        if key in self.materials:
            return False
            
        # Aggiungi flag custom
        material_data['custom'] = True
        material_data['normative'] = False
        
        self.materials[key] = material_data
        
        # Salva su file
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
        return False
        
    def update_custom_material(self, key: str, material_data: Dict) -> bool:
        """Aggiorna materiale personalizzato"""
        if key not in self.materials:
            return False
            
        # Verifica che sia custom
        if not self.materials[key].get('custom', False):
            return False
            
        # Mantieni flag custom
        material_data['custom'] = True
        material_data['normative'] = False
        
        self.materials[key] = material_data
        
        # Salva su file
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
        return False
        
    def delete_custom_material(self, key: str) -> bool:
        """Elimina materiale personalizzato"""
        if key not in self.materials:
            return False
            
        # Verifica che sia custom
        if not self.materials[key].get('custom', False):
            return False
            
        del self.materials[key]
        
        # Salva su file
        if self.save_custom_materials():
            self.database_updated.emit()
            return True
        return False


class MaterialEditorDialog(QDialog):
    """Dialog per creazione/modifica materiale"""
    
    def __init__(self, parent=None, material_data=None, material_key=None):
        super().__init__(parent)
        self.material_data = material_data or {}
        self.material_key = material_key
        self.setWindowTitle("Editor Materiale")
        self.setModal(True)
        self.setup_ui()
        
        if material_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form principale
        form_layout = QFormLayout()
        
        # Nome
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Es. Muratura in blocchi speciali")
        form_layout.addRow("Nome materiale:", self.name_edit)
        
        # Categoria
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(["Pietrame", "Mattoni", "Blocchi", "Mista", "Altro"])
        form_layout.addRow("Categoria:", self.category_combo)
        
        # Parametri meccanici
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        form_layout.addRow(separator1)
        
        form_layout.addRow(QLabel("<b>Parametri meccanici:</b>"))
        
        # fcm
        self.fcm_spin = QDoubleSpinBox()
        self.fcm_spin.setRange(0.1, 20.0)
        self.fcm_spin.setDecimals(1)
        self.fcm_spin.setSingleStep(0.1)
        self.fcm_spin.setSuffix(" MPa")
        self.fcm_spin.setValue(2.0)
        form_layout.addRow("f<sub>cm</sub> - Resistenza compressione:", self.fcm_spin)
        
        # tau0
        self.tau0_spin = QDoubleSpinBox()
        self.tau0_spin.setRange(0.001, 1.0)
        self.tau0_spin.setDecimals(3)
        self.tau0_spin.setSingleStep(0.001)
        self.tau0_spin.setSuffix(" MPa")
        self.tau0_spin.setValue(0.050)
        form_layout.addRow("τ<sub>0</sub> - Resistenza taglio:", self.tau0_spin)
        
        # E
        self.E_spin = QSpinBox()
        self.E_spin.setRange(100, 10000)
        self.E_spin.setSingleStep(10)
        self.E_spin.setSuffix(" MPa")
        self.E_spin.setValue(1500)
        form_layout.addRow("E - Modulo elastico normale:", self.E_spin)
        
        # G
        self.G_spin = QSpinBox()
        self.G_spin.setRange(50, 5000)
        self.G_spin.setSingleStep(10)
        self.G_spin.setSuffix(" MPa")
        self.G_spin.setValue(500)
        form_layout.addRow("G - Modulo elastico tangenziale:", self.G_spin)
        
        # Peso specifico
        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(5.0, 30.0)
        self.w_spin.setDecimals(1)
        self.w_spin.setSingleStep(0.5)
        self.w_spin.setSuffix(" kN/m³")
        self.w_spin.setValue(18.0)
        form_layout.addRow("γ - Peso specifico:", self.w_spin)
        
        # Riferimento normativo
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        form_layout.addRow(separator2)
        
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Es. Prove sperimentali 2024")
        form_layout.addRow("Riferimento/Fonte:", self.reference_edit)
        
        # Note
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Eventuali note aggiuntive...")
        form_layout.addRow("Note:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def validate_and_accept(self):
        """Valida i dati prima di accettare"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Errore", "Inserire il nome del materiale")
            return
            
        if not self.category_combo.currentText().strip():
            QMessageBox.warning(self, "Errore", "Inserire la categoria")
            return
            
        self.accept()
        
    def load_data(self):
        """Carica dati esistenti"""
        self.name_edit.setText(self.material_data.get('name', ''))
        
        # Categoria
        category = self.material_data.get('category', 'Altro')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentText(category)
            
        # Parametri
        self.fcm_spin.setValue(self.material_data.get('fcm', 2.0))
        self.tau0_spin.setValue(self.material_data.get('tau0', 0.050))
        self.E_spin.setValue(self.material_data.get('E', 1500))
        self.G_spin.setValue(self.material_data.get('G', 500))
        self.w_spin.setValue(self.material_data.get('w', 18.0))
        
        # Altri campi
        self.reference_edit.setText(self.material_data.get('reference', ''))
        self.notes_edit.setPlainText(self.material_data.get('notes', ''))
        
    def get_data(self) -> Dict:
        """Restituisce i dati del materiale"""
        return {
            'name': self.name_edit.text().strip(),
            'category': self.category_combo.currentText().strip(),
            'fcm': self.fcm_spin.value(),
            'tau0': self.tau0_spin.value(),
            'E': self.E_spin.value(),
            'G': self.G_spin.value(),
            'w': self.w_spin.value(),
            'reference': self.reference_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }