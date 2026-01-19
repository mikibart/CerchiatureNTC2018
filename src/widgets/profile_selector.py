"""
Widget per selezione profili metallici
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from typing import Optional, Dict

# Import database profili centralizzato
try:
    from src.core.database.profiles import profiles_db, STEEL_PROFILES, STEEL_GRADES
except ImportError:
    from ..core.database.profiles import profiles_db, STEEL_PROFILES, STEEL_GRADES


class ProfileSelector(QWidget):
    """Selettore profili con filtri e anteprima proprietà"""

    # Segnale emesso quando viene selezionato un profilo
    profile_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_profile = None
        self.setup_ui()
        self.connect_signals()
        self.update_sizes()

    def setup_ui(self):
        """Costruisce interfaccia selettore"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Gruppo selezione profilo
        profile_group = QGroupBox("Selezione Profilo")
        profile_layout = QFormLayout()

        # Tipo profilo (HEA, HEB, IPE, UPN)
        self.type_combo = QComboBox()
        self.type_combo.addItems(profiles_db.get_available_types())
        profile_layout.addRow("Tipo:", self.type_combo)

        # Dimensione profilo
        self.size_combo = QComboBox()
        profile_layout.addRow("Dimensione:", self.size_combo)

        # Classe acciaio
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(profiles_db.get_available_grades())
        self.grade_combo.setCurrentText('S275')  # Default
        profile_layout.addRow("Acciaio:", self.grade_combo)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        # Gruppo proprietà profilo
        props_group = QGroupBox("Proprietà Profilo")
        props_layout = QGridLayout()

        # Labels proprietà
        self.prop_labels = {}
        props = [
            ('h', 'Altezza (h)', 'mm'),
            ('b', 'Larghezza (b)', 'mm'),
            ('A', 'Area (A)', 'cm²'),
            ('Ix', 'Mom. Inerzia X (Ix)', 'cm⁴'),
            ('Iy', 'Mom. Inerzia Y (Iy)', 'cm⁴'),
            ('Wx', 'Mod. Resist. X (Wx)', 'cm³'),
            ('Wy', 'Mod. Resist. Y (Wy)', 'cm³'),
        ]

        for i, (key, label, unit) in enumerate(props):
            row = i // 2
            col = (i % 2) * 2

            name_label = QLabel(f"{label}:")
            name_label.setStyleSheet("font-weight: bold; font-size: 10px;")
            props_layout.addWidget(name_label, row, col)

            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 10px;")
            self.prop_labels[key] = (value_label, unit)
            props_layout.addWidget(value_label, row, col + 1)

        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

        # Gruppo proprietà acciaio
        steel_group = QGroupBox("Proprietà Acciaio")
        steel_layout = QFormLayout()

        self.fyk_label = QLabel("-")
        steel_layout.addRow("fyk:", self.fyk_label)

        self.E_label = QLabel("210000 N/mm²")
        steel_layout.addRow("E:", self.E_label)

        steel_group.setLayout(steel_layout)
        layout.addWidget(steel_group)

        # Pulsante conferma
        self.confirm_btn = QPushButton("Conferma Selezione")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        layout.addWidget(self.confirm_btn)

        layout.addStretch()
        self.setLayout(layout)

    def connect_signals(self):
        """Connette segnali"""
        self.type_combo.currentTextChanged.connect(self.update_sizes)
        self.size_combo.currentTextChanged.connect(self.update_properties)
        self.grade_combo.currentTextChanged.connect(self.update_steel_properties)
        self.confirm_btn.clicked.connect(self.emit_selection)

    def update_sizes(self):
        """Aggiorna dimensioni disponibili per il tipo selezionato"""
        profile_type = self.type_combo.currentText()
        sizes = profiles_db.get_available_sizes(profile_type)

        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        self.size_combo.addItems(sizes)
        self.size_combo.blockSignals(False)

        # Seleziona dimensione intermedia come default
        if sizes:
            mid_idx = len(sizes) // 2
            self.size_combo.setCurrentIndex(mid_idx)

        self.update_properties()

    def update_properties(self):
        """Aggiorna visualizzazione proprietà profilo"""
        profile_type = self.type_combo.currentText()
        size = self.size_combo.currentText()

        if not size:
            return

        profile = profiles_db.get_profile(profile_type, size)

        if not profile:
            return

        self.current_profile = {
            'type': profile_type,
            'size': size,
            'name': f"{profile_type} {size}",
            **profile
        }

        # Aggiorna labels
        for key, (label, unit) in self.prop_labels.items():
            value = profile.get(key, '-')
            if isinstance(value, (int, float)):
                label.setText(f"{value} {unit}")
            else:
                label.setText(str(value))

        self.update_steel_properties()

    def update_steel_properties(self):
        """Aggiorna proprietà acciaio"""
        grade = self.grade_combo.currentText()
        steel = profiles_db.get_steel_grade(grade)

        if steel:
            self.fyk_label.setText(f"{steel['fyk']} N/mm²")
            self.E_label.setText(f"{steel['E']} N/mm²")

            if self.current_profile:
                self.current_profile['steel_grade'] = grade
                self.current_profile['fyk'] = steel['fyk']
                self.current_profile['E'] = steel['E']

    def emit_selection(self):
        """Emette segnale con profilo selezionato"""
        if self.current_profile:
            self.profile_selected.emit(self.current_profile)

    def get_selected_profile(self) -> Optional[Dict]:
        """Restituisce profilo attualmente selezionato"""
        return self.current_profile

    def set_profile(self, profile_type: str, size: str, grade: str = 'S275'):
        """Imposta profilo programmaticamente"""
        # Tipo
        idx = self.type_combo.findText(profile_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        # Dimensione
        idx = self.size_combo.findText(size)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)

        # Acciaio
        idx = self.grade_combo.findText(grade)
        if idx >= 0:
            self.grade_combo.setCurrentIndex(idx)


class ProfileSelectorDialog(QDialog):
    """Dialog per selezione profilo con anteprima"""

    def __init__(self, parent=None, current_profile: Optional[Dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Seleziona Profilo Metallico")
        self.setModal(True)
        self.setMinimumSize(400, 500)

        self.selected_profile = None
        self.setup_ui()

        if current_profile:
            self.selector.set_profile(
                current_profile.get('type', 'HEA'),
                current_profile.get('size', '100'),
                current_profile.get('steel_grade', 'S275')
            )

    def setup_ui(self):
        layout = QVBoxLayout()

        # Selettore profilo
        self.selector = ProfileSelector()
        layout.addWidget(self.selector)

        # Pulsanti dialog
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def accept_selection(self):
        self.selected_profile = self.selector.get_selected_profile()
        self.accept()

    def get_selected_profile(self) -> Optional[Dict]:
        return self.selected_profile


class CompactProfileSelector(QWidget):
    """Versione compatta del selettore per uso inline"""

    profile_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Tipo
        self.type_combo = QComboBox()
        self.type_combo.addItems(profiles_db.get_available_types())
        self.type_combo.setFixedWidth(70)
        layout.addWidget(self.type_combo)

        # Dimensione
        self.size_combo = QComboBox()
        self.size_combo.setFixedWidth(70)
        layout.addWidget(self.size_combo)

        # Acciaio
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(profiles_db.get_available_grades())
        self.grade_combo.setCurrentText('S275')
        self.grade_combo.setFixedWidth(60)
        layout.addWidget(self.grade_combo)

        # Info button
        self.info_btn = QPushButton("...")
        self.info_btn.setFixedWidth(30)
        self.info_btn.setToolTip("Mostra dettagli profilo")
        layout.addWidget(self.info_btn)

        layout.addStretch()
        self.setLayout(layout)

        # Connessioni
        self.type_combo.currentTextChanged.connect(self.update_sizes)
        self.size_combo.currentTextChanged.connect(self.emit_change)
        self.grade_combo.currentTextChanged.connect(self.emit_change)
        self.info_btn.clicked.connect(self.show_details)

        self.update_sizes()

    def update_sizes(self):
        profile_type = self.type_combo.currentText()
        sizes = profiles_db.get_available_sizes(profile_type)

        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        self.size_combo.addItems(sizes)
        if sizes:
            self.size_combo.setCurrentIndex(len(sizes) // 2)
        self.size_combo.blockSignals(False)

        self.emit_change()

    def emit_change(self):
        profile = self.get_profile()
        if profile:
            self.profile_changed.emit(profile)

    def get_profile(self) -> Optional[Dict]:
        profile_type = self.type_combo.currentText()
        size = self.size_combo.currentText()
        grade = self.grade_combo.currentText()

        if not size:
            return None

        data = profiles_db.get_profile(profile_type, size)
        if not data:
            return None

        steel = profiles_db.get_steel_grade(grade) or {}

        return {
            'type': profile_type,
            'size': size,
            'name': f"{profile_type} {size}",
            'steel_grade': grade,
            'fyk': steel.get('fyk', 275),
            'E': steel.get('E', 210000),
            **data
        }

    def set_profile(self, profile_type: str, size: str, grade: str = 'S275'):
        self.type_combo.setCurrentText(profile_type)
        self.size_combo.setCurrentText(size)
        self.grade_combo.setCurrentText(grade)

    def show_details(self):
        profile = self.get_profile()
        if not profile:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Dettagli {profile['name']}")
        msg.setIcon(QMessageBox.Information)

        text = f"""<b>{profile['name']}</b><br><br>
        <table>
        <tr><td>Altezza h:</td><td>{profile.get('h', '-')} mm</td></tr>
        <tr><td>Larghezza b:</td><td>{profile.get('b', '-')} mm</td></tr>
        <tr><td>Area A:</td><td>{profile.get('A', '-')} cm²</td></tr>
        <tr><td>Ix:</td><td>{profile.get('Ix', '-')} cm⁴</td></tr>
        <tr><td>Wx:</td><td>{profile.get('Wx', '-')} cm³</td></tr>
        <tr><td>Acciaio:</td><td>{profile.get('steel_grade', '-')}</td></tr>
        <tr><td>fyk:</td><td>{profile.get('fyk', '-')} N/mm²</td></tr>
        </table>
        """

        msg.setText(text)
        msg.exec_()
