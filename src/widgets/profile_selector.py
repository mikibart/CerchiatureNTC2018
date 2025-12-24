"""
Widget per selezione profili metallici
Calcolatore Cerchiature NTC 2018
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import pyqtSignal, Qt
import logging

logger = logging.getLogger(__name__)

# Database profili standard
STEEL_PROFILES = {
    'IPE': {
        'IPE 80': {'h': 80, 'b': 46, 'tw': 3.8, 's': 5.2, 'A': 7.64, 'Ix': 80.1, 'Wx': 20.0, 'fy': 275},
        'IPE 100': {'h': 100, 'b': 55, 'tw': 4.1, 's': 5.7, 'A': 10.3, 'Ix': 171, 'Wx': 34.2, 'fy': 275},
        'IPE 120': {'h': 120, 'b': 64, 'tw': 4.4, 's': 6.3, 'A': 13.2, 'Ix': 318, 'Wx': 53.0, 'fy': 275},
        'IPE 140': {'h': 140, 'b': 73, 'tw': 4.7, 's': 6.9, 'A': 16.4, 'Ix': 541, 'Wx': 77.3, 'fy': 275},
        'IPE 160': {'h': 160, 'b': 82, 'tw': 5.0, 's': 7.4, 'A': 20.1, 'Ix': 869, 'Wx': 109, 'fy': 275},
        'IPE 180': {'h': 180, 'b': 91, 'tw': 5.3, 's': 8.0, 'A': 23.9, 'Ix': 1317, 'Wx': 146, 'fy': 275},
        'IPE 200': {'h': 200, 'b': 100, 'tw': 5.6, 's': 8.5, 'A': 28.5, 'Ix': 1943, 'Wx': 194, 'fy': 275},
        'IPE 220': {'h': 220, 'b': 110, 'tw': 5.9, 's': 9.2, 'A': 33.4, 'Ix': 2772, 'Wx': 252, 'fy': 275},
        'IPE 240': {'h': 240, 'b': 120, 'tw': 6.2, 's': 9.8, 'A': 39.1, 'Ix': 3892, 'Wx': 324, 'fy': 275},
        'IPE 270': {'h': 270, 'b': 135, 'tw': 6.6, 's': 10.2, 'A': 45.9, 'Ix': 5790, 'Wx': 429, 'fy': 275},
        'IPE 300': {'h': 300, 'b': 150, 'tw': 7.1, 's': 10.7, 'A': 53.8, 'Ix': 8356, 'Wx': 557, 'fy': 275},
    },
    'HEA': {
        'HEA 100': {'h': 96, 'b': 100, 'tw': 5.0, 's': 8.0, 'A': 21.2, 'Ix': 349, 'Wx': 72.8, 'fy': 275},
        'HEA 120': {'h': 114, 'b': 120, 'tw': 5.0, 's': 8.0, 'A': 25.3, 'Ix': 606, 'Wx': 106, 'fy': 275},
        'HEA 140': {'h': 133, 'b': 140, 'tw': 5.5, 's': 8.5, 'A': 31.4, 'Ix': 1033, 'Wx': 155, 'fy': 275},
        'HEA 160': {'h': 152, 'b': 160, 'tw': 6.0, 's': 9.0, 'A': 38.8, 'Ix': 1673, 'Wx': 220, 'fy': 275},
        'HEA 180': {'h': 171, 'b': 180, 'tw': 6.0, 's': 9.5, 'A': 45.3, 'Ix': 2510, 'Wx': 294, 'fy': 275},
        'HEA 200': {'h': 190, 'b': 200, 'tw': 6.5, 's': 10.0, 'A': 53.8, 'Ix': 3692, 'Wx': 389, 'fy': 275},
        'HEA 220': {'h': 210, 'b': 220, 'tw': 7.0, 's': 11.0, 'A': 64.3, 'Ix': 5410, 'Wx': 515, 'fy': 275},
        'HEA 240': {'h': 230, 'b': 240, 'tw': 7.5, 's': 12.0, 'A': 76.8, 'Ix': 7763, 'Wx': 675, 'fy': 275},
        'HEA 260': {'h': 250, 'b': 260, 'tw': 7.5, 's': 12.5, 'A': 86.8, 'Ix': 10450, 'Wx': 836, 'fy': 275},
        'HEA 280': {'h': 270, 'b': 280, 'tw': 8.0, 's': 13.0, 'A': 97.3, 'Ix': 13670, 'Wx': 1013, 'fy': 275},
        'HEA 300': {'h': 290, 'b': 300, 'tw': 8.5, 's': 14.0, 'A': 112.5, 'Ix': 18260, 'Wx': 1260, 'fy': 275},
    },
    'HEB': {
        'HEB 100': {'h': 100, 'b': 100, 'tw': 6.0, 's': 10.0, 'A': 26.0, 'Ix': 450, 'Wx': 89.9, 'fy': 275},
        'HEB 120': {'h': 120, 'b': 120, 'tw': 6.5, 's': 11.0, 'A': 34.0, 'Ix': 864, 'Wx': 144, 'fy': 275},
        'HEB 140': {'h': 140, 'b': 140, 'tw': 7.0, 's': 12.0, 'A': 43.0, 'Ix': 1509, 'Wx': 216, 'fy': 275},
        'HEB 160': {'h': 160, 'b': 160, 'tw': 8.0, 's': 13.0, 'A': 54.3, 'Ix': 2492, 'Wx': 311, 'fy': 275},
        'HEB 180': {'h': 180, 'b': 180, 'tw': 8.5, 's': 14.0, 'A': 65.3, 'Ix': 3831, 'Wx': 426, 'fy': 275},
        'HEB 200': {'h': 200, 'b': 200, 'tw': 9.0, 's': 15.0, 'A': 78.1, 'Ix': 5696, 'Wx': 570, 'fy': 275},
        'HEB 220': {'h': 220, 'b': 220, 'tw': 9.5, 's': 16.0, 'A': 91.0, 'Ix': 8091, 'Wx': 736, 'fy': 275},
        'HEB 240': {'h': 240, 'b': 240, 'tw': 10.0, 's': 17.0, 'A': 106.0, 'Ix': 11260, 'Wx': 938, 'fy': 275},
        'HEB 260': {'h': 260, 'b': 260, 'tw': 10.0, 's': 17.5, 'A': 118.4, 'Ix': 14920, 'Wx': 1148, 'fy': 275},
        'HEB 280': {'h': 280, 'b': 280, 'tw': 10.5, 's': 18.0, 'A': 131.4, 'Ix': 19270, 'Wx': 1376, 'fy': 275},
        'HEB 300': {'h': 300, 'b': 300, 'tw': 11.0, 's': 19.0, 'A': 149.1, 'Ix': 25170, 'Wx': 1678, 'fy': 275},
    },
    'UPN': {
        'UPN 80': {'h': 80, 'b': 45, 'tw': 6.0, 's': 8.0, 'A': 11.0, 'Ix': 106, 'Wx': 26.5, 'fy': 275},
        'UPN 100': {'h': 100, 'b': 50, 'tw': 6.0, 's': 8.5, 'A': 13.5, 'Ix': 206, 'Wx': 41.2, 'fy': 275},
        'UPN 120': {'h': 120, 'b': 55, 'tw': 7.0, 's': 9.0, 'A': 17.0, 'Ix': 364, 'Wx': 60.7, 'fy': 275},
        'UPN 140': {'h': 140, 'b': 60, 'tw': 7.0, 's': 10.0, 'A': 20.4, 'Ix': 605, 'Wx': 86.4, 'fy': 275},
        'UPN 160': {'h': 160, 'b': 65, 'tw': 7.5, 's': 10.5, 'A': 24.0, 'Ix': 925, 'Wx': 116, 'fy': 275},
        'UPN 180': {'h': 180, 'b': 70, 'tw': 8.0, 's': 11.0, 'A': 28.0, 'Ix': 1350, 'Wx': 150, 'fy': 275},
        'UPN 200': {'h': 200, 'b': 75, 'tw': 8.5, 's': 11.5, 'A': 32.2, 'Ix': 1910, 'Wx': 191, 'fy': 275},
    },
    'L (angolari)': {
        'L 50x50x5': {'h': 50, 'b': 50, 'tw': 5.0, 'A': 4.80, 'Ix': 11.0, 'Wx': 3.05, 'fy': 275},
        'L 60x60x6': {'h': 60, 'b': 60, 'tw': 6.0, 'A': 6.91, 'Ix': 22.8, 'Wx': 5.29, 'fy': 275},
        'L 70x70x7': {'h': 70, 'b': 70, 'tw': 7.0, 'A': 9.40, 'Ix': 42.4, 'Wx': 8.41, 'fy': 275},
        'L 80x80x8': {'h': 80, 'b': 80, 'tw': 8.0, 'A': 12.3, 'Ix': 72.2, 'Wx': 12.6, 'fy': 275},
        'L 90x90x9': {'h': 90, 'b': 90, 'tw': 9.0, 'A': 15.5, 'Ix': 115, 'Wx': 17.8, 'fy': 275},
        'L 100x100x10': {'h': 100, 'b': 100, 'tw': 10.0, 'A': 19.2, 'Ix': 177, 'Wx': 24.6, 'fy': 275},
    }
}


class ProfileSelector(QWidget):
    """Selettore profili metallici con filtri e anteprima"""

    profile_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_profile = None
        self.setup_ui()

    def setup_ui(self):
        """Costruisce interfaccia selettore"""
        layout = QVBoxLayout(self)

        # Gruppo selezione tipo
        type_group = QGroupBox("Tipo Profilo")
        type_layout = QHBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(STEEL_PROFILES.keys()))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(QLabel("Famiglia:"))
        type_layout.addWidget(self.type_combo)

        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        type_layout.addWidget(QLabel("Profilo:"))
        type_layout.addWidget(self.profile_combo)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Gruppo caratteristiche
        props_group = QGroupBox("Caratteristiche Geometriche")
        props_layout = QFormLayout()

        self.h_label = QLabel("-")
        self.b_label = QLabel("-")
        self.tw_label = QLabel("-")
        self.area_label = QLabel("-")
        self.ix_label = QLabel("-")
        self.wx_label = QLabel("-")
        self.fy_label = QLabel("-")

        props_layout.addRow("Altezza h [mm]:", self.h_label)
        props_layout.addRow("Larghezza b [mm]:", self.b_label)
        props_layout.addRow("Spessore anima tw [mm]:", self.tw_label)
        props_layout.addRow("Area A [cm\u00b2]:", self.area_label)
        props_layout.addRow("Momento Ix [cm\u2074]:", self.ix_label)
        props_layout.addRow("Modulo Wx [cm\u00b3]:", self.wx_label)
        props_layout.addRow("fy [MPa]:", self.fy_label)

        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

        # Pulsante conferma
        self.confirm_btn = QPushButton("Conferma Selezione")
        self.confirm_btn.clicked.connect(self.confirm_selection)
        layout.addWidget(self.confirm_btn)

        # Inizializza lista profili
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, profile_type: str):
        """Aggiorna lista profili quando cambia il tipo"""
        self.profile_combo.clear()
        if profile_type in STEEL_PROFILES:
            self.profile_combo.addItems(list(STEEL_PROFILES[profile_type].keys()))

    def on_profile_changed(self, profile_name: str):
        """Aggiorna caratteristiche quando cambia il profilo"""
        profile_type = self.type_combo.currentText()

        if profile_type in STEEL_PROFILES and profile_name in STEEL_PROFILES[profile_type]:
            props = STEEL_PROFILES[profile_type][profile_name]
            self.current_profile = {
                'type': profile_type,
                'name': profile_name,
                **props
            }

            self.h_label.setText(f"{props.get('h', '-')}")
            self.b_label.setText(f"{props.get('b', '-')}")
            self.tw_label.setText(f"{props.get('tw', '-')}")
            self.area_label.setText(f"{props.get('A', '-')}")
            self.ix_label.setText(f"{props.get('Ix', '-')}")
            self.wx_label.setText(f"{props.get('Wx', '-')}")
            self.fy_label.setText(f"{props.get('fy', '-')}")
        else:
            self.current_profile = None
            self.h_label.setText("-")
            self.b_label.setText("-")
            self.tw_label.setText("-")
            self.area_label.setText("-")
            self.ix_label.setText("-")
            self.wx_label.setText("-")
            self.fy_label.setText("-")

    def confirm_selection(self):
        """Conferma la selezione del profilo"""
        if self.current_profile:
            self.profile_selected.emit(self.current_profile)
            logger.debug(f"Profilo selezionato: {self.current_profile['name']}")

    def get_selected_profile(self) -> dict:
        """Restituisce il profilo attualmente selezionato"""
        return self.current_profile

    def set_profile(self, profile_type: str, profile_name: str):
        """Imposta il profilo selezionato"""
        if profile_type in STEEL_PROFILES:
            index = self.type_combo.findText(profile_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            if profile_name in STEEL_PROFILES[profile_type]:
                index = self.profile_combo.findText(profile_name)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
