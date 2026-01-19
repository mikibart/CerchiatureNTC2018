"""
Dialog per visualizzare dettagli avanzati del calcolo
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class AdvancedDetailsDialog(QDialog):
    """Dialog per visualizzare dettagli avanzati del calcolo"""

    def __init__(self, parent=None, results=None, project_data=None):
        super().__init__(parent)
        self.results = results or {}
        self.project_data = project_data or {}
        self.setWindowTitle("Dettagli Avanzati Calcolo")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Tab widget per organizzare i dettagli
        tabs = QTabWidget()

        # Tab vincoli
        vincoli_tab = self.create_vincoli_tab()
        tabs.addTab(vincoli_tab, "Vincoli e Modellazione")

        # Tab collegamenti
        collegamenti_tab = self.create_collegamenti_tab()
        tabs.addTab(collegamenti_tab, "Collegamenti e Giunzioni")

        # Tab verifiche locali
        verifiche_tab = self.create_verifiche_tab()
        tabs.addTab(verifiche_tab, "Verifiche Locali")

        # Nuovo: Tab calandratura
        calandratura_tab = self.create_calandratura_tab()
        tabs.addTab(calandratura_tab, "Calandratura Profili")

        layout.addWidget(tabs)

        # Pulsanti
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def create_vincoli_tab(self):
        """Crea tab con dettagli vincoli"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Analizza vincoli per ogni apertura
        openings_module = self.project_data.get('openings_module', {})
        openings = openings_module.get('openings', [])

        for i, opening in enumerate(openings):
            if 'rinforzo' in opening and 'vincoli' in opening['rinforzo']:
                group = QGroupBox(f"Apertura A{i+1}")
                group_layout = QFormLayout()

                vincoli = opening['rinforzo']['vincoli']

                # Vincoli base
                if 'base_sx' in vincoli:
                    group_layout.addRow("Base SX:", QLabel(vincoli['base_sx'].get('tipo', 'N.D.')))
                if 'base_dx' in vincoli:
                    group_layout.addRow("Base DX:", QLabel(vincoli['base_dx'].get('tipo', 'N.D.')))

                # Vincoli nodi
                if 'nodo_sx' in vincoli:
                    group_layout.addRow("Nodo SX:", QLabel(vincoli['nodo_sx'].get('tipo', 'N.D.')))
                if 'nodo_dx' in vincoli:
                    group_layout.addRow("Nodo DX:", QLabel(vincoli['nodo_dx'].get('tipo', 'N.D.')))

                # Opzioni avanzate
                if 'avanzate' in vincoli:
                    av = vincoli['avanzate']
                    if av.get('secondo_ordine'):
                        group_layout.addRow("", QLabel("✓ Effetti II ordine"))
                    if av.get('non_linearita'):
                        group_layout.addRow("", QLabel("✓ Non linearità geometrica"))

                group.setLayout(group_layout)
                content_layout.addWidget(group)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def create_collegamenti_tab(self):
        """Crea tab con dettagli collegamenti"""
        widget = QWidget()
        layout = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)

        # Genera report testuale
        report = []
        frame_results = self.results.get('frame_results', {})

        for opening_id, frame_data in frame_results.items():
            report.append(f"\n{opening_id}:")

            if 'connections' in frame_data:
                conn = frame_data['connections']
                report.append(f"  Verifica ancoraggi: {'OK' if conn.get('verified') else 'NON VERIFICATO'}")

                if 'anchor_force' in conn:
                    report.append(f"  Forza max ancoraggio: {conn['anchor_force']:.1f} kN")
                if 'safety_factor' in conn:
                    report.append(f"  Coefficiente sicurezza: {conn['safety_factor']:.2f}")

        text.setPlainText('\n'.join(report))
        layout.addWidget(text)

        widget.setLayout(layout)
        return widget

    def create_verifiche_tab(self):
        """Crea tab con verifiche locali dettagliate"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tabella verifiche
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Elemento", "Sollecitazione", "Resistenza", "Verifica"])

        # Popola con dati esempio
        frame_results = self.results.get('frame_results', {})
        row = 0

        for opening_id, frame_data in frame_results.items():
            if 'verifications' in frame_data:
                for verif_type, verif_data in frame_data['verifications'].items():
                    table.insertRow(row)
                    table.setItem(row, 0, QTableWidgetItem(opening_id))
                    table.setItem(row, 1, QTableWidgetItem(verif_type))
                    table.setItem(row, 2, QTableWidgetItem(f"{verif_data.get('demand', 0):.1f}"))
                    table.setItem(row, 3, QTableWidgetItem(f"{verif_data.get('capacity', 0):.1f}"))
                    row += 1

        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def create_calandratura_tab(self):
        """Crea tab con dettagli calandratura"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Analizza aperture con calandratura
        frame_results = self.results.get('frame_results', {})
        openings_module = self.project_data.get('openings_module', {})
        openings = openings_module.get('openings', [])

        has_curved = False

        for i, (opening_id, frame_data) in enumerate(frame_results.items()):
            if i >= len(openings):
                continue

            opening = openings[i]

            # Verifica se è ad arco o calandrata
            if opening.get('type') == 'Ad arco' or 'bending_info' in frame_data:
                has_curved = True

                group = QGroupBox(f"Apertura {opening_id}")
                group_layout = QFormLayout()

                # Info apertura
                group_layout.addRow("Tipo:", QLabel(opening.get('type', 'Rettangolare')))

                if 'arch_radius' in frame_data:
                    group_layout.addRow("Raggio arco:",
                                      QLabel(f"{frame_data['arch_radius']:.1f} cm"))
                if 'arch_length' in frame_data:
                    group_layout.addRow("Lunghezza sviluppata:",
                                      QLabel(f"{frame_data['arch_length']:.1f} cm"))

                # Info calandratura
                if 'bending_info' in frame_data:
                    bend = frame_data['bending_info']

                    # Rapporto r/h con colore
                    rh_label = QLabel(f"{bend['r_h_ratio']:.1f}")
                    if bend['r_h_ratio'] < 15:
                        rh_label.setStyleSheet("color: red; font-weight: bold;")
                    elif bend['r_h_ratio'] < 30:
                        rh_label.setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        rh_label.setStyleSheet("color: green; font-weight: bold;")
                    group_layout.addRow("Rapporto r/h:", rh_label)

                    group_layout.addRow("Metodo:", QLabel(bend['method']))
                    group_layout.addRow("Tensioni residue:",
                                      QLabel(f"{bend['residual_stress']:.0f} MPa"))

                    # Calandrabile o no
                    if not bend.get('bendable', True):
                        status_label = QLabel("⚠️ NON CALANDRABILE CON METODI STANDARD")
                        status_label.setStyleSheet("color: red; font-weight: bold;")
                        group_layout.addRow("Stato:", status_label)

                    # Avvisi
                    if bend.get('warnings'):
                        warnings_text = '\n'.join(bend['warnings'])
                        warnings_label = QLabel(warnings_text)
                        warnings_label.setStyleSheet("color: red;")
                        warnings_label.setWordWrap(True)
                        group_layout.addRow("Avvisi:", warnings_label)

                # Avvisi aggiuntivi dal frame
                if frame_data.get('warnings'):
                    frame_warnings = '\n'.join(f"⚠️ {w}" for w in frame_data['warnings'])
                    frame_warnings_label = QLabel(frame_warnings)
                    frame_warnings_label.setStyleSheet("color: orange;")
                    frame_warnings_label.setWordWrap(True)
                    group_layout.addRow("Note calcolo:", frame_warnings_label)

                group.setLayout(group_layout)
                content_layout.addWidget(group)

        if not has_curved:
            label = QLabel("Nessuna apertura con calandratura rilevata")
            label.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(label)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
