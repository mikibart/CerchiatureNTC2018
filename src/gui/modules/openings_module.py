"""
Modulo Aperture e Rinforzi
Gestisce la configurazione dettagliata di aperture e cerchiature
Versione aggiornata con gestione profili multipli e vincoli avanzati
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
from typing import Dict, List, Optional

# Import del widget canvas avanzato
try:
    from src.widgets.wall_canvas_advanced import AdvancedWallCanvas
except ImportError:
    # Fallback se l'import fallisce
    class AdvancedWallCanvas(QWidget):
        opening_selected = pyqtSignal(int)
        def __init__(self): super().__init__()
        def set_wall_data(self, *args): pass
        def add_opening(self, *args): pass
        def clear_openings(self): pass
        def update(self): pass

# Import dialog aperture avanzato se disponibile
try:
    from src.gui.dialogs.opening_dialog_advanced import AdvancedOpeningDialog
except ImportError:
    AdvancedOpeningDialog = None


class RinforzoCerchiaturaDialog(QDialog):
    """Dialog per configurazione rinforzo cerchiatura con opzioni avanzate"""
    
    def __init__(self, parent=None, rinforzo_data=None, wall_thickness=30):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Rinforzo Cerchiatura")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.rinforzo_data = rinforzo_data or {}
        self.wall_thickness = wall_thickness
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tipo di rinforzo
        tipo_group = QGroupBox("Tipo di Rinforzo")
        tipo_layout = QVBoxLayout()
        
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems([
            "Telaio completo in acciaio",
            "Solo architrave in acciaio", 
            "Telaio in C.A.",
            "Solo architrave in C.A.",
            "Rinforzo ad arco in acciaio",
            "Rinforzo calandrato nell'arco",
            "Nessun rinforzo"
        ])
        self.tipo_combo.currentIndexChanged.connect(self.on_tipo_changed)
        tipo_layout.addWidget(self.tipo_combo)
        
        tipo_group.setLayout(tipo_layout)
        layout.addWidget(tipo_group)
        
        # Stack widget per configurazioni specifiche
        self.stack = QStackedWidget()
        
        # Pagina acciaio
        self.acciaio_page = self.create_acciaio_page()
        self.stack.addWidget(self.acciaio_page)
        
        # Pagina C.A.
        self.ca_page = self.create_ca_page()
        self.stack.addWidget(self.ca_page)
        
        # Pagina vuota per "Nessun rinforzo"
        self.stack.addWidget(QWidget())
        
        layout.addWidget(self.stack)
        
        # Note
        note_group = QGroupBox("Note")
        note_layout = QVBoxLayout()
        self.note_text = QTextEdit()
        self.note_text.setMaximumHeight(80)
        self.note_text.setPlaceholderText("Eventuali note sul rinforzo...")
        note_layout.addWidget(self.note_text)
        note_group.setLayout(note_layout)
        layout.addWidget(note_group)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Inizializza i profili disponibili
        self.update_profili_disponibili()
        
        # Carica dati esistenti
        if self.rinforzo_data:
            self.load_data()
            
    def create_acciaio_page(self):
        """Crea pagina configurazione acciaio con opzioni avanzate"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Tab widget principale
        self.main_tabs = QTabWidget()
        
        # TAB 1: Profili e Materiali
        profili_tab = self.create_profili_tab()
        self.main_tabs.addTab(profili_tab, "Profili")
        
        # TAB 2: Collegamenti
        collegamenti_tab = self.create_collegamenti_tab()
        self.main_tabs.addTab(collegamenti_tab, "Collegamenti")
        
        # TAB 3: Vincoli
        vincoli_tab = self.create_vincoli_tab()
        self.main_tabs.addTab(vincoli_tab, "Vincoli")
        
        # TAB 4: Ancoraggi
        ancoraggi_tab = self.create_ancoraggi_tab()
        self.main_tabs.addTab(ancoraggi_tab, "Ancoraggi")
        
        layout.addWidget(self.main_tabs)
        page.setLayout(layout)
        return page
        
    def create_profili_tab(self):
        """Tab profili e materiali"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Classe acciaio
        acciaio_group = QGroupBox("Proprietà Acciaio")
        acciaio_layout = QGridLayout()
        
        acciaio_layout.addWidget(QLabel("Classe acciaio:"), 0, 0)
        self.classe_acciaio = QComboBox()
        self.classe_acciaio.addItems(["S235", "S275", "S355", "S450"])
        acciaio_layout.addWidget(self.classe_acciaio, 0, 1)
        
        acciaio_layout.addWidget(QLabel("Tipo profili:"), 1, 0)
        self.tipo_profilo = QComboBox()
        self.tipo_profilo.addItems(["HEA", "HEB", "HEM", "IPE", "UNP", "L", "Tubolare"])
        self.tipo_profilo.currentIndexChanged.connect(self.update_profili_disponibili)
        acciaio_layout.addWidget(self.tipo_profilo, 1, 1)
        
        acciaio_group.setLayout(acciaio_layout)
        scroll_layout.addWidget(acciaio_group)
        
        # Profili per elemento
        profili_group = QGroupBox("Assegnazione Profili")
        profili_layout = QGridLayout()
        
        # Architrave
        profili_layout.addWidget(QLabel("<b>Architrave:</b>"), 0, 0)
        self.architrave_profilo = QComboBox()
        profili_layout.addWidget(self.architrave_profilo, 0, 1)
        
        profili_layout.addWidget(QLabel("N° profili:"), 0, 2)
        self.architrave_n_profili = QSpinBox()
        self.architrave_n_profili.setRange(1, 6)
        self.architrave_n_profili.setValue(1)
        self.architrave_n_profili.valueChanged.connect(self.on_architrave_n_profili_changed)
        profili_layout.addWidget(self.architrave_n_profili, 0, 3)
        
        profili_layout.addWidget(QLabel("Interasse [cm]:"), 0, 4)
        self.architrave_interasse = QSpinBox()
        self.architrave_interasse.setRange(0, 100)
        self.architrave_interasse.setValue(0)
        self.architrave_interasse.setToolTip("0 = profili accoppiati a contatto")
        self.architrave_interasse.setEnabled(False)
        profili_layout.addWidget(self.architrave_interasse, 0, 5)
        
        profili_layout.addWidget(QLabel("Disposizione:"), 0, 6)
        self.architrave_disposizione = QComboBox()
        self.architrave_disposizione.addItems([
            "In linea",
            "Sfalsati",
            "Accoppiati 2+2",
            "Accoppiati 3+3"
        ])
        self.architrave_disposizione.setEnabled(False)
        profili_layout.addWidget(self.architrave_disposizione, 0, 7)
        
        self.architrave_ruotato = QCheckBox("Ruotato 90°")
        self.architrave_ruotato.setToolTip("Appoggio sullo spigolo delle ali")
        profili_layout.addWidget(self.architrave_ruotato, 0, 8)
        
        # Piedritti (se telaio completo)
        self.piedritto_label = QLabel("<b>Piedritti:</b>")
        profili_layout.addWidget(self.piedritto_label, 1, 0)
        self.piedritti_profilo = QComboBox()
        profili_layout.addWidget(self.piedritti_profilo, 1, 1)
        
        profili_layout.addWidget(QLabel("N° profili:"), 1, 2)
        self.piedritti_n_profili = QSpinBox()
        self.piedritti_n_profili.setRange(1, 6)
        self.piedritti_n_profili.setValue(1)
        self.piedritti_n_profili.valueChanged.connect(self.on_piedritti_n_profili_changed)
        profili_layout.addWidget(self.piedritti_n_profili, 1, 3)
        
        profili_layout.addWidget(QLabel("Interasse [cm]:"), 1, 4)
        self.piedritti_interasse = QSpinBox()
        self.piedritti_interasse.setRange(0, 100)
        self.piedritti_interasse.setValue(0)
        self.piedritti_interasse.setEnabled(False)
        profili_layout.addWidget(self.piedritti_interasse, 1, 5)
        
        profili_layout.addWidget(QLabel("Disposizione:"), 1, 6)
        self.piedritti_disposizione = QComboBox()
        self.piedritti_disposizione.addItems([
            "In linea",
            "Sfalsati",
            "Accoppiati 2+2",
            "Accoppiati 3+3"
        ])
        self.piedritti_disposizione.setEnabled(False)
        profili_layout.addWidget(self.piedritti_disposizione, 1, 7)
        
        self.piedritti_ruotato = QCheckBox("Ruotato 90°")
        profili_layout.addWidget(self.piedritti_ruotato, 1, 8)
        
        # Irrigidimenti
        profili_layout.addWidget(QLabel("Irrigidimenti trasversali:"), 2, 0)
        self.irrigidimenti = QSpinBox()
        self.irrigidimenti.setRange(0, 10)
        self.irrigidimenti.setValue(0)
        profili_layout.addWidget(self.irrigidimenti, 2, 1)
        
        profili_group.setLayout(profili_layout)
        scroll_layout.addWidget(profili_group)
        
        # Parametri arco calandrato (nascosto inizialmente)
        self.arco_group = QGroupBox("Parametri Cerchiatura Calandrata")
        arco_layout = QGridLayout()
        
        # Tipo di apertura curva
        arco_layout.addWidget(QLabel("Tipo apertura:"), 0, 0)
        self.tipo_apertura_curva = QComboBox()
        self.tipo_apertura_curva.addItems([
            "Arco a tutto sesto",
            "Arco ribassato", 
            "Arco a sesto acuto",
            "Arco ellittico",
            "Apertura personalizzata"
        ])
        arco_layout.addWidget(self.tipo_apertura_curva, 0, 1)
        
        arco_layout.addWidget(QLabel("Raggio interno [cm]:"), 1, 0)
        self.raggio_arco = QSpinBox()
        self.raggio_arco.setRange(50, 500)
        self.raggio_arco.setValue(150)
        arco_layout.addWidget(self.raggio_arco, 1, 1)
        
        arco_layout.addWidget(QLabel("Freccia dell'arco [cm]:"), 1, 2)
        self.freccia_arco = QSpinBox()
        self.freccia_arco.setRange(10, 100)
        self.freccia_arco.setValue(30)
        arco_layout.addWidget(self.freccia_arco, 1, 3)
        
        # Profilo calandrato
        arco_layout.addWidget(QLabel("Profilo calandrato:"), 2, 0)
        self.profilo_calandrato = QComboBox()
        arco_layout.addWidget(self.profilo_calandrato, 2, 1)
        
        arco_layout.addWidget(QLabel("N° profili:"), 2, 2)
        self.calandrato_n_profili = QSpinBox()
        self.calandrato_n_profili.setRange(1, 4)
        self.calandrato_n_profili.setValue(1)
        arco_layout.addWidget(self.calandrato_n_profili, 2, 3)
        
        # Metodo di calandratura
        arco_layout.addWidget(QLabel("Calandratura:"), 3, 0)
        self.metodo_calandratura = QComboBox()
        self.metodo_calandratura.addItems([
            "A freddo",
            "A caldo",
            "Preformato"
        ])
        arco_layout.addWidget(self.metodo_calandratura, 3, 1)
        
        self.arco_group.setLayout(arco_layout)
        self.arco_group.setVisible(False)
        scroll_layout.addWidget(self.arco_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        tab.setLayout(layout)
        return tab
        
    def create_collegamenti_tab(self):
        """Tab collegamenti profili multipli"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Collegamenti profili multipli
        profili_group = QGroupBox("Collegamenti Profili Accoppiati")
        profili_layout = QGridLayout()
        
        profili_layout.addWidget(QLabel("Tipo collegamento:"), 0, 0)
        self.tipo_collegamento_profili = QComboBox()
        self.tipo_collegamento_profili.addItems([
            "Bulloni passanti",
            "Calastrelli saldati",
            "Piastre di collegamento",
            "Imbottiture continue",
            "Sistema misto"
        ])
        self.tipo_collegamento_profili.currentIndexChanged.connect(self.on_tipo_collegamento_changed)
        profili_layout.addWidget(self.tipo_collegamento_profili, 0, 1, 1, 2)
        
        # Dettagli bulloni passanti
        self.bulloni_group = QGroupBox("Bulloni passanti")
        bulloni_layout = QGridLayout()
        
        bulloni_layout.addWidget(QLabel("Classe bulloni:"), 0, 0)
        self.classe_bulloni = QComboBox()
        self.classe_bulloni.addItems(["4.6", "5.6", "6.8", "8.8", "10.9"])
        self.classe_bulloni.setCurrentIndex(3)  # 8.8 default
        bulloni_layout.addWidget(self.classe_bulloni, 0, 1)
        
        bulloni_layout.addWidget(QLabel("Diametro [mm]:"), 0, 2)
        self.diametro_bulloni = QComboBox()
        self.diametro_bulloni.addItems(["M12", "M14", "M16", "M18", "M20", "M22", "M24", "M27", "M30"])
        self.diametro_bulloni.setCurrentIndex(2)  # M16 default
        bulloni_layout.addWidget(self.diametro_bulloni, 0, 3)
        
        bulloni_layout.addWidget(QLabel("Interasse long. [cm]:"), 1, 0)
        self.interasse_long = QSpinBox()
        self.interasse_long.setRange(10, 100)
        self.interasse_long.setValue(30)
        bulloni_layout.addWidget(self.interasse_long, 1, 1)
        
        bulloni_layout.addWidget(QLabel("N° file:"), 1, 2)
        self.n_file_bulloni = QSpinBox()
        self.n_file_bulloni.setRange(1, 4)
        self.n_file_bulloni.setValue(2)
        bulloni_layout.addWidget(self.n_file_bulloni, 1, 3)
        
        bulloni_layout.addWidget(QLabel("Precarico:"), 2, 0)
        self.precarico = QCheckBox("Con precarico controllato")
        bulloni_layout.addWidget(self.precarico, 2, 1)
        
        self.bulloni_group.setLayout(bulloni_layout)
        profili_layout.addWidget(self.bulloni_group, 1, 0, 1, 3)
        
        # Dettagli calastrelli
        self.calastrelli_group = QGroupBox("Calastrelli")
        calastrelli_layout = QGridLayout()
        
        calastrelli_layout.addWidget(QLabel("Tipo calastrello:"), 0, 0)
        self.tipo_calastrello = QComboBox()
        self.tipo_calastrello.addItems(["Piatto", "Angolare", "UPN"])
        calastrelli_layout.addWidget(self.tipo_calastrello, 0, 1)
        
        calastrelli_layout.addWidget(QLabel("Dimensioni:"), 0, 2)
        self.dim_calastrello = QLineEdit("80x8")
        calastrelli_layout.addWidget(self.dim_calastrello, 0, 3)
        
        calastrelli_layout.addWidget(QLabel("Passo [cm]:"), 1, 0)
        self.passo_calastrelli = QSpinBox()
        self.passo_calastrelli.setRange(30, 150)
        self.passo_calastrelli.setValue(60)
        calastrelli_layout.addWidget(self.passo_calastrelli, 1, 1)
        
        self.calastrelli_group.setLayout(calastrelli_layout)
        self.calastrelli_group.setVisible(False)
        profili_layout.addWidget(self.calastrelli_group, 2, 0, 1, 3)
        
        profili_group.setLayout(profili_layout)
        scroll_layout.addWidget(profili_group)
        
        # Giunzioni strutturali
        giunzioni_group = QGroupBox("Giunzioni Strutturali")
        giunzioni_layout = QGridLayout()
        
        # Giunzione architrave-piedritto
        giunzioni_layout.addWidget(QLabel("<b>Giunzione architrave-piedritto:</b>"), 0, 0, 1, 4)
        
        giunzioni_layout.addWidget(QLabel("Tipo giunzione:"), 1, 0)
        self.tipo_giunzione_nodo = QComboBox()
        self.tipo_giunzione_nodo.addItems([
            "Saldatura diretta",
            "Piastra di nodo bullonata",
            "Piastra di nodo saldata",
            "Squadrette d'angolo",
            "Giunzione a flangia",
            "Incastro con irrigidimenti"
        ])
        self.tipo_giunzione_nodo.currentIndexChanged.connect(self.on_tipo_giunzione_changed)
        giunzioni_layout.addWidget(self.tipo_giunzione_nodo, 1, 1, 1, 3)
        
        # Dettagli saldatura
        self.saldatura_group = QGroupBox("Dettagli saldatura")
        saldatura_layout = QGridLayout()
        
        saldatura_layout.addWidget(QLabel("Tipo saldatura:"), 0, 0)
        self.tipo_saldatura = QComboBox()
        self.tipo_saldatura.addItems([
            "A cordone d'angolo",
            "A completa penetrazione",
            "A parziale penetrazione",
            "Mista"
        ])
        saldatura_layout.addWidget(self.tipo_saldatura, 0, 1)
        
        saldatura_layout.addWidget(QLabel("Altezza cordone [mm]:"), 0, 2)
        self.altezza_cordone = QSpinBox()
        self.altezza_cordone.setRange(3, 20)
        self.altezza_cordone.setValue(6)
        saldatura_layout.addWidget(self.altezza_cordone, 0, 3)
        
        saldatura_layout.addWidget(QLabel("Controllo:"), 1, 0)
        self.controllo_saldatura = QComboBox()
        self.controllo_saldatura.addItems([
            "Visivo",
            "Liquidi penetranti",
            "Ultrasuoni",
            "Radiografico"
        ])
        saldatura_layout.addWidget(self.controllo_saldatura, 1, 1)
        
        self.saldatura_group.setLayout(saldatura_layout)
        giunzioni_layout.addWidget(self.saldatura_group, 2, 0, 1, 4)
        
        # Dettagli piastra di nodo
        self.piastra_nodo_group = QGroupBox("Piastra di nodo")
        piastra_layout = QGridLayout()
        
        piastra_layout.addWidget(QLabel("Spessore piastra [mm]:"), 0, 0)
        self.spessore_piastra_nodo = QSpinBox()
        self.spessore_piastra_nodo.setRange(10, 50)
        self.spessore_piastra_nodo.setValue(20)
        piastra_layout.addWidget(self.spessore_piastra_nodo, 0, 1)
        
        piastra_layout.addWidget(QLabel("Dimensioni [mm]:"), 0, 2)
        self.dim_piastra_nodo = QLineEdit("300x400")
        piastra_layout.addWidget(self.dim_piastra_nodo, 0, 3)
        
        piastra_layout.addWidget(QLabel("N° bulloni lato:"), 1, 0)
        self.n_bulloni_lato = QSpinBox()
        self.n_bulloni_lato.setRange(2, 12)
        self.n_bulloni_lato.setValue(4)
        piastra_layout.addWidget(self.n_bulloni_lato, 1, 1)
        
        piastra_layout.addWidget(QLabel("Diametro bulloni:"), 1, 2)
        self.diam_bulloni_piastra = QComboBox()
        self.diam_bulloni_piastra.addItems(["M16", "M20", "M24", "M27", "M30"])
        self.diam_bulloni_piastra.setCurrentIndex(1)  # M20
        piastra_layout.addWidget(self.diam_bulloni_piastra, 1, 3)
        
        self.piastra_nodo_group.setLayout(piastra_layout)
        self.piastra_nodo_group.setVisible(False)
        giunzioni_layout.addWidget(self.piastra_nodo_group, 3, 0, 1, 4)
        
        # Irrigidimenti nodo
        giunzioni_layout.addWidget(QLabel("<b>Irrigidimenti:</b>"), 4, 0)
        self.irrigidimenti_nodo = QCheckBox("Prevedi irrigidimenti di nodo")
        giunzioni_layout.addWidget(self.irrigidimenti_nodo, 4, 1)
        
        self.tipo_irrigidimento = QComboBox()
        self.tipo_irrigidimento.addItems([
            "Piatti verticali",
            "Piatti orizzontali",
            "Diagonali",
            "Combinati"
        ])
        self.tipo_irrigidimento.setEnabled(False)
        giunzioni_layout.addWidget(self.tipo_irrigidimento, 4, 2, 1, 2)
        
        self.irrigidimenti_nodo.toggled.connect(self.tipo_irrigidimento.setEnabled)
        
        giunzioni_group.setLayout(giunzioni_layout)
        scroll_layout.addWidget(giunzioni_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        tab.setLayout(layout)
        return tab
        
    def create_vincoli_tab(self):
        """Tab vincoli strutturali dettagliati"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sub-tabs per vincoli
        self.vincoli_tabs = QTabWidget()
        
        # TAB 1: Vincoli alla base
        base_tab = QWidget()
        base_tab_layout = QGridLayout()
        
        # Vincolo piedritto sinistro
        base_tab_layout.addWidget(QLabel("<b>Piedritto sinistro:</b>"), 0, 0, 1, 2)
        base_tab_layout.addWidget(QLabel("Tipo vincolo:"), 1, 0)
        self.vincolo_base_sx = QComboBox()
        self.vincolo_base_sx.addItems([
            "Incastro perfetto",
            "Cerniera",
            "Appoggio semplice", 
            "Semincastro elastico",
            "Vincolo elastico",
            "Carrello verticale",
            "Carrello orizzontale"
        ])
        self.vincolo_base_sx.currentIndexChanged.connect(
            lambda: self.on_vincolo_changed(
                self.vincolo_base_sx, 
                self.k_trasl_base_sx, 
                self.k_rot_base_sx
            )
        )
        base_tab_layout.addWidget(self.vincolo_base_sx, 1, 1)
        
        # Rigidezza per vincoli elastici
        base_tab_layout.addWidget(QLabel("K traslazione [kN/m]:"), 2, 0)
        self.k_trasl_base_sx = QDoubleSpinBox()
        self.k_trasl_base_sx.setRange(0, 1000000)
        self.k_trasl_base_sx.setValue(100000)
        self.k_trasl_base_sx.setEnabled(False)
        base_tab_layout.addWidget(self.k_trasl_base_sx, 2, 1)
        
        base_tab_layout.addWidget(QLabel("K rotazione [kNm/rad]:"), 2, 2)
        self.k_rot_base_sx = QDoubleSpinBox()
        self.k_rot_base_sx.setRange(0, 1000000)
        self.k_rot_base_sx.setValue(50000)
        self.k_rot_base_sx.setEnabled(False)
        base_tab_layout.addWidget(self.k_rot_base_sx, 2, 3)
        
        # Vincolo piedritto destro
        base_tab_layout.addWidget(QLabel("<b>Piedritto destro:</b>"), 3, 0, 1, 2)
        base_tab_layout.addWidget(QLabel("Tipo vincolo:"), 4, 0)
        self.vincolo_base_dx = QComboBox()
        self.vincolo_base_dx.addItems([
            "Incastro perfetto",
            "Cerniera",
            "Appoggio semplice",
            "Semincastro elastico", 
            "Vincolo elastico",
            "Carrello verticale",
            "Carrello orizzontale"
        ])
        self.vincolo_base_dx.currentIndexChanged.connect(
            lambda: self.on_vincolo_changed(
                self.vincolo_base_dx, 
                self.k_trasl_base_dx, 
                self.k_rot_base_dx
            )
        )
        base_tab_layout.addWidget(self.vincolo_base_dx, 4, 1)
        
        # Rigidezza dx
        base_tab_layout.addWidget(QLabel("K traslazione [kN/m]:"), 5, 0)
        self.k_trasl_base_dx = QDoubleSpinBox()
        self.k_trasl_base_dx.setRange(0, 1000000)
        self.k_trasl_base_dx.setValue(100000)
        self.k_trasl_base_dx.setEnabled(False)
        base_tab_layout.addWidget(self.k_trasl_base_dx, 5, 1)
        
        base_tab_layout.addWidget(QLabel("K rotazione [kNm/rad]:"), 5, 2)
        self.k_rot_base_dx = QDoubleSpinBox()
        self.k_rot_base_dx.setRange(0, 1000000)
        self.k_rot_base_dx.setValue(50000)
        self.k_rot_base_dx.setEnabled(False)
        base_tab_layout.addWidget(self.k_rot_base_dx, 5, 3)
        
        # Checkbox per vincoli simmetrici
        self.vincoli_base_simmetrici = QCheckBox("Vincoli simmetrici")
        self.vincoli_base_simmetrici.setChecked(True)
        self.vincoli_base_simmetrici.toggled.connect(self.on_vincoli_simmetrici_changed)
        base_tab_layout.addWidget(self.vincoli_base_simmetrici, 6, 0, 1, 2)
        
        base_tab.setLayout(base_tab_layout)
        self.vincoli_tabs.addTab(base_tab, "Base Piedritti")
        
        # TAB 2: Vincoli nodo architrave-piedritto
        nodo_tab = QWidget()
        nodo_tab_layout = QGridLayout()
        
        # Nodo sinistro
        nodo_tab_layout.addWidget(QLabel("<b>Nodo sinistro:</b>"), 0, 0, 1, 2)
        nodo_tab_layout.addWidget(QLabel("Tipo collegamento:"), 1, 0)
        self.vincolo_nodo_sx = QComboBox()
        self.vincolo_nodo_sx.addItems([
            "Incastro (continuità)",
            "Cerniera",
            "Semincastro con riduzione",
            "Giunzione bullonata",
            "Giunzione saldata parziale"
        ])
        self.vincolo_nodo_sx.currentIndexChanged.connect(
            lambda: self.on_vincolo_nodo_changed(self.vincolo_nodo_sx, self.riduzione_nodo_sx)
        )
        nodo_tab_layout.addWidget(self.vincolo_nodo_sx, 1, 1)
        
        # Fattore di riduzione rigidezza
        nodo_tab_layout.addWidget(QLabel("Fattore riduzione (0-1):"), 2, 0)
        self.riduzione_nodo_sx = QDoubleSpinBox()
        self.riduzione_nodo_sx.setRange(0, 1)
        self.riduzione_nodo_sx.setValue(1.0)
        self.riduzione_nodo_sx.setSingleStep(0.1)
        self.riduzione_nodo_sx.setEnabled(False)
        nodo_tab_layout.addWidget(self.riduzione_nodo_sx, 2, 1)
        
        # Nodo destro
        nodo_tab_layout.addWidget(QLabel("<b>Nodo destro:</b>"), 3, 0, 1, 2)
        nodo_tab_layout.addWidget(QLabel("Tipo collegamento:"), 4, 0)
        self.vincolo_nodo_dx = QComboBox()
        self.vincolo_nodo_dx.addItems([
            "Incastro (continuità)",
            "Cerniera",
            "Semincastro con riduzione",
            "Giunzione bullonata",
            "Giunzione saldata parziale"
        ])
        self.vincolo_nodo_dx.currentIndexChanged.connect(
            lambda: self.on_vincolo_nodo_changed(self.vincolo_nodo_dx, self.riduzione_nodo_dx)
        )
        nodo_tab_layout.addWidget(self.vincolo_nodo_dx, 4, 1)
        
        nodo_tab_layout.addWidget(QLabel("Fattore riduzione (0-1):"), 5, 0)
        self.riduzione_nodo_dx = QDoubleSpinBox()
        self.riduzione_nodo_dx.setRange(0, 1)
        self.riduzione_nodo_dx.setValue(1.0)
        self.riduzione_nodo_dx.setSingleStep(0.1)
        self.riduzione_nodo_dx.setEnabled(False)
        nodo_tab_layout.addWidget(self.riduzione_nodo_dx, 5, 1)
        
        # Vincoli simmetrici nodi
        self.vincoli_nodi_simmetrici = QCheckBox("Vincoli nodi simmetrici")
        self.vincoli_nodi_simmetrici.setChecked(True)
        self.vincoli_nodi_simmetrici.toggled.connect(self.on_vincoli_nodi_simmetrici_changed)
        nodo_tab_layout.addWidget(self.vincoli_nodi_simmetrici, 6, 0, 1, 2)
        
        nodo_tab.setLayout(nodo_tab_layout)
        self.vincoli_tabs.addTab(nodo_tab, "Nodi Architrave")
        
        # TAB 3: Vincoli con muratura/arco
        muratura_tab = QWidget()
        muratura_tab_layout = QGridLayout()
        
        # Interazione con muratura
        muratura_tab_layout.addWidget(QLabel("<b>Interazione con muratura:</b>"), 0, 0, 1, 2)
        
        muratura_tab_layout.addWidget(QLabel("Collaborazione laterale:"), 1, 0)
        self.collaborazione_muratura = QComboBox()
        self.collaborazione_muratura.addItems([
            "Nessuna collaborazione",
            "Collaborazione parziale",
            "Collaborazione totale",
            "Definita dall'utente"
        ])
        self.collaborazione_muratura.currentIndexChanged.connect(self.on_collaborazione_changed)
        muratura_tab_layout.addWidget(self.collaborazione_muratura, 1, 1)
        
        muratura_tab_layout.addWidget(QLabel("Larghezza collaborante [cm]:"), 2, 0)
        self.larghezza_collab = QSpinBox()
        self.larghezza_collab.setRange(0, 100)
        self.larghezza_collab.setValue(0)
        self.larghezza_collab.setEnabled(False)
        muratura_tab_layout.addWidget(self.larghezza_collab, 2, 1)
        
        # Vincoli arco (se presente)
        muratura_tab_layout.addWidget(QLabel("<b>Vincoli imposta arco:</b>"), 3, 0, 1, 2)
        
        muratura_tab_layout.addWidget(QLabel("Imposta sinistra:"), 4, 0)
        self.vincolo_arco_sx = QComboBox()
        self.vincolo_arco_sx.addItems([
            "Cerniera ideale",
            "Incastro",
            "Appoggio con attrito",
            "Vincolo elastico"
        ])
        muratura_tab_layout.addWidget(self.vincolo_arco_sx, 4, 1)
        
        muratura_tab_layout.addWidget(QLabel("Imposta destra:"), 5, 0)
        self.vincolo_arco_dx = QComboBox()
        self.vincolo_arco_dx.addItems([
            "Cerniera ideale",
            "Incastro",
            "Appoggio con attrito",
            "Vincolo elastico"
        ])
        muratura_tab_layout.addWidget(self.vincolo_arco_dx, 5, 1)
        
        # Pressione di contatto
        muratura_tab_layout.addWidget(QLabel("Pressione contatto [MPa]:"), 6, 0)
        self.pressione_contatto = QDoubleSpinBox()
        self.pressione_contatto.setRange(0, 10)
        self.pressione_contatto.setValue(1.0)
        self.pressione_contatto.setSingleStep(0.1)
        muratura_tab_layout.addWidget(self.pressione_contatto, 6, 1)
        
        muratura_tab.setLayout(muratura_tab_layout)
        self.vincoli_tabs.addTab(muratura_tab, "Muratura/Arco")
        
        # TAB 4: Opzioni avanzate
        avanzate_tab = QWidget()
        avanzate_tab_layout = QGridLayout()
        
        avanzate_tab_layout.addWidget(QLabel("<b>Modellazione avanzata:</b>"), 0, 0, 1, 2)
        
        # Effetti del secondo ordine
        self.secondo_ordine = QCheckBox("Considera effetti II ordine (P-Δ)")
        avanzate_tab_layout.addWidget(self.secondo_ordine, 1, 0, 1, 2)
        
        # Non linearità geometrica
        self.non_linearita = QCheckBox("Non linearità geometrica")
        avanzate_tab_layout.addWidget(self.non_linearita, 2, 0, 1, 2)
        
        # Imperfezioni
        avanzate_tab_layout.addWidget(QLabel("Imperfezione iniziale [cm]:"), 3, 0)
        self.imperfezione = QDoubleSpinBox()
        self.imperfezione.setRange(0, 5)
        self.imperfezione.setValue(0)
        self.imperfezione.setSingleStep(0.1)
        avanzate_tab_layout.addWidget(self.imperfezione, 3, 1)
        
        # Ridistribuzione
        avanzate_tab_layout.addWidget(QLabel("Ridistribuzione plastica:"), 4, 0)
        self.ridistribuzione = QSpinBox()
        self.ridistribuzione.setRange(0, 30)
        self.ridistribuzione.setValue(0)
        self.ridistribuzione.setSuffix(" %")
        avanzate_tab_layout.addWidget(self.ridistribuzione, 4, 1)
        
        avanzate_tab.setLayout(avanzate_tab_layout)
        self.vincoli_tabs.addTab(avanzate_tab, "Avanzate")
        
        layout.addWidget(self.vincoli_tabs)
        tab.setLayout(layout)
        return tab
        
    def create_ancoraggi_tab(self):
        """Tab ancoraggi alla muratura"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Sistema di ancoraggio
        ancoraggio_group = QGroupBox("Sistema di Ancoraggio alla Muratura")
        ancoraggio_layout = QGridLayout()
        
        ancoraggio_layout.addWidget(QLabel("Sistema principale:"), 0, 0)
        self.sistema_ancoraggio = QComboBox()
        self.sistema_ancoraggio.addItems([
            "Tasselli chimici ad iniezione",
            "Barre filettate con resina epossidica",
            "Zanche/Staffe murate",
            "Piastre con tasselli meccanici",
            "Barre passanti con piastra",
            "Sistema misto"
        ])
        self.sistema_ancoraggio.currentIndexChanged.connect(self.on_sistema_ancoraggio_changed)
        ancoraggio_layout.addWidget(self.sistema_ancoraggio, 0, 1, 1, 3)
        
        ancoraggio_group.setLayout(ancoraggio_layout)
        scroll_layout.addWidget(ancoraggio_group)
        
        # Dettagli tasselli chimici
        self.chimici_group = QGroupBox("Tasselli chimici/Barre con resina")
        chimici_layout = QGridLayout()
        
        chimici_layout.addWidget(QLabel("Tipo resina:"), 0, 0)
        self.tipo_resina = QComboBox()
        self.tipo_resina.addItems([
            "Epossidica pura",
            "Epossi-acrilata", 
            "Vinilestere",
            "Poliestere"
        ])
        chimici_layout.addWidget(self.tipo_resina, 0, 1)
        
        chimici_layout.addWidget(QLabel("Diametro barra [mm]:"), 0, 2)
        self.diametro_barra = QComboBox()
        self.diametro_barra.addItems(["M12", "M16", "M20", "M24", "M27", "M30"])
        self.diametro_barra.setCurrentIndex(1)  # M16
        chimici_layout.addWidget(self.diametro_barra, 0, 3)
        
        chimici_layout.addWidget(QLabel("Profondità [cm]:"), 1, 0)
        self.profondita_ancoraggio = QSpinBox()
        self.profondita_ancoraggio.setRange(10, 50)
        self.profondita_ancoraggio.setValue(20)
        chimici_layout.addWidget(self.profondita_ancoraggio, 1, 1)
        
        chimici_layout.addWidget(QLabel("N° per nodo:"), 1, 2)
        self.n_ancoraggi_nodo = QSpinBox()
        self.n_ancoraggi_nodo.setRange(2, 12)
        self.n_ancoraggi_nodo.setValue(4)
        chimici_layout.addWidget(self.n_ancoraggi_nodo, 1, 3)
        
        chimici_layout.addWidget(QLabel("Disposizione:"), 2, 0)
        self.disposizione_ancoraggi = QComboBox()
        self.disposizione_ancoraggi.addItems([
            "Quadrata",
            "Circolare",
            "In linea",
            "Sfalsata"
        ])
        chimici_layout.addWidget(self.disposizione_ancoraggi, 2, 1)
        
        self.chimici_group.setLayout(chimici_layout)
        scroll_layout.addWidget(self.chimici_group)
        
        # Dettagli zanche
        self.zanche_group = QGroupBox("Zanche/Staffe murate")
        zanche_layout = QGridLayout()
        
        zanche_layout.addWidget(QLabel("Tipo zanca:"), 0, 0)
        self.tipo_zanca = QComboBox()
        self.tipo_zanca.addItems([
            "Zanca a L",
            "Zanca a U",
            "Staffa chiusa",
            "Zanca con piastra"
        ])
        zanche_layout.addWidget(self.tipo_zanca, 0, 1)
        
        zanche_layout.addWidget(QLabel("Dimensioni [mm]:"), 0, 2)
        self.dim_zanca = QLineEdit("200x100x10")
        zanche_layout.addWidget(self.dim_zanca, 0, 3)
        
        zanche_layout.addWidget(QLabel("N° zanche/m:"), 1, 0)
        self.n_zanche_metro = QSpinBox()
        self.n_zanche_metro.setRange(2, 10)
        self.n_zanche_metro.setValue(4)
        zanche_layout.addWidget(self.n_zanche_metro, 1, 1)
        
        zanche_layout.addWidget(QLabel("Ammorsamento [cm]:"), 1, 2)
        self.ammorsamento_zanche = QSpinBox()
        self.ammorsamento_zanche.setRange(10, 40)
        self.ammorsamento_zanche.setValue(20)
        zanche_layout.addWidget(self.ammorsamento_zanche, 1, 3)
        
        self.zanche_group.setLayout(zanche_layout)
        self.zanche_group.setVisible(False)
        scroll_layout.addWidget(self.zanche_group)
        
        # Base cerchiatura
        base_group = QGroupBox("Base Cerchiatura")
        base_layout = QGridLayout()
        
        base_layout.addWidget(QLabel("Tipo di base:"), 0, 0)
        self.tipo_base = QComboBox()
        self.tipo_base.addItems([
            "Senza collegamento alla base",
            "Trave di collegamento",
            "Piastre puntuali sotto i pilastri",
            "Piastra continua di collegamento",
            "Plinto isolato per ogni piedritto"
        ])
        self.tipo_base.currentIndexChanged.connect(self.on_tipo_base_changed)
        base_layout.addWidget(self.tipo_base, 0, 1, 1, 2)
        
        # Dettagli piastra di base
        self.piastra_base_group = QGroupBox("Piastra di base")
        piastra_base_layout = QGridLayout()
        
        piastra_base_layout.addWidget(QLabel("Dimensioni [mm]:"), 0, 0)
        self.dim_piastra_base = QLineEdit("400x400x30")
        piastra_base_layout.addWidget(self.dim_piastra_base, 0, 1)
        
        piastra_base_layout.addWidget(QLabel("N° tirafondi:"), 0, 2)
        self.n_tirafondi = QSpinBox()
        self.n_tirafondi.setRange(2, 8)
        self.n_tirafondi.setValue(4)
        piastra_base_layout.addWidget(self.n_tirafondi, 0, 3)
        
        piastra_base_layout.addWidget(QLabel("Diametro tirafondi:"), 1, 0)
        self.diam_tirafondi = QComboBox()
        self.diam_tirafondi.addItems(["M16", "M20", "M24", "M27", "M30", "M36"])
        self.diam_tirafondi.setCurrentIndex(2)  # M24
        piastra_base_layout.addWidget(self.diam_tirafondi, 1, 1)
        
        piastra_base_layout.addWidget(QLabel("Lunghezza [cm]:"), 1, 2)
        self.lungh_tirafondi = QSpinBox()
        self.lungh_tirafondi.setRange(30, 100)
        self.lungh_tirafondi.setValue(50)
        piastra_base_layout.addWidget(self.lungh_tirafondi, 1, 3)
        
        piastra_base_layout.addWidget(QLabel("Malta di livellamento:"), 2, 0)
        self.malta_livellamento = QComboBox()
        self.malta_livellamento.addItems([
            "Malta cementizia antiritiro",
            "Malta epossidica",
            "Senza malta (fresatura)",
            "Neoprene"
        ])
        piastra_base_layout.addWidget(self.malta_livellamento, 2, 1)
        
        piastra_base_layout.addWidget(QLabel("Spessore [mm]:"), 2, 2)
        self.spessore_malta = QSpinBox()
        self.spessore_malta.setRange(10, 50)
        self.spessore_malta.setValue(30)
        piastra_base_layout.addWidget(self.spessore_malta, 2, 3)
        
        self.piastra_base_group.setLayout(piastra_base_layout)
        self.piastra_base_group.setVisible(False)
        base_layout.addWidget(self.piastra_base_group, 1, 0, 1, 3)
        
        # Dettagli trave di base
        self.trave_base_group = QGroupBox("Trave di collegamento")
        trave_base_layout = QGridLayout()
        
        trave_base_layout.addWidget(QLabel("Profilo trave:"), 0, 0)
        self.trave_base_profilo = QComboBox()
        trave_base_layout.addWidget(self.trave_base_profilo, 0, 1)
        
        trave_base_layout.addWidget(QLabel("N° profili:"), 0, 2)
        self.trave_base_n_profili = QSpinBox()
        self.trave_base_n_profili.setRange(1, 4)
        self.trave_base_n_profili.setValue(1)
        trave_base_layout.addWidget(self.trave_base_n_profili, 0, 3)
        
        self.trave_base_group.setLayout(trave_base_layout)
        self.trave_base_group.setVisible(False)
        base_layout.addWidget(self.trave_base_group, 2, 0, 1, 3)
        
        base_group.setLayout(base_layout)
        scroll_layout.addWidget(base_group)
        
        # Rinforzo locale muratura
        rinforzo_group = QGroupBox("Rinforzo Locale Muratura")
        rinforzo_layout = QGridLayout()
        
        self.rinforzo_locale = QCheckBox("Prevedi rinforzo locale zona ancoraggio")
        rinforzo_layout.addWidget(self.rinforzo_locale, 0, 0, 1, 2)
        
        rinforzo_layout.addWidget(QLabel("Tipo rinforzo:"), 1, 0)
        self.tipo_rinforzo_locale = QComboBox()
        self.tipo_rinforzo_locale.addItems([
            "Iniezioni di malta",
            "Placcaggio con rete",
            "FRP",
            "Betoncino armato"
        ])
        self.tipo_rinforzo_locale.setEnabled(False)
        rinforzo_layout.addWidget(self.tipo_rinforzo_locale, 1, 1)
        
        self.rinforzo_locale.toggled.connect(self.tipo_rinforzo_locale.setEnabled)
        
        rinforzo_group.setLayout(rinforzo_layout)
        scroll_layout.addWidget(rinforzo_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        tab.setLayout(layout)
        return tab
        
    def create_ca_page(self):
        """Crea pagina configurazione C.A."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Calcestruzzo
        cls_group = QGroupBox("Calcestruzzo")
        cls_layout = QGridLayout()
        
        cls_layout.addWidget(QLabel("Classe calcestruzzo:"), 0, 0)
        self.classe_cls = QComboBox()
        self.classe_cls.addItems([
            "C20/25", "C25/30", "C28/35", "C32/40", "C35/45"
        ])
        self.classe_cls.setCurrentIndex(1)  # C25/30 default
        cls_layout.addWidget(self.classe_cls, 0, 1)
        
        cls_layout.addWidget(QLabel("Copriferro [mm]:"), 1, 0)
        self.copriferro = QSpinBox()
        self.copriferro.setRange(20, 50)
        self.copriferro.setValue(30)
        cls_layout.addWidget(self.copriferro, 1, 1)
        
        cls_group.setLayout(cls_layout)
        scroll_layout.addWidget(cls_group)
        
        # Dimensioni sezioni
        dim_group = QGroupBox("Dimensioni Sezioni")
        dim_layout = QGridLayout()
        
        # Architrave
        dim_layout.addWidget(QLabel("<b>Architrave:</b>"), 0, 0, 1, 2)
        dim_layout.addWidget(QLabel("Base [cm]:"), 1, 0)
        self.arch_base = QSpinBox()
        self.arch_base.setRange(20, 100)
        self.arch_base.setValue(30)
        dim_layout.addWidget(self.arch_base, 1, 1)
        
        dim_layout.addWidget(QLabel("Altezza [cm]:"), 1, 2)
        self.arch_altezza = QSpinBox()
        self.arch_altezza.setRange(20, 100)
        self.arch_altezza.setValue(40)
        dim_layout.addWidget(self.arch_altezza, 1, 3)
        
        # Piedritti (se telaio)
        self.piedritti_ca_label = QLabel("<b>Piedritti:</b>")
        dim_layout.addWidget(self.piedritti_ca_label, 2, 0, 1, 2)
        
        dim_layout.addWidget(QLabel("Base [cm]:"), 3, 0)
        self.pied_base = QSpinBox()
        self.pied_base.setRange(20, 100)
        self.pied_base.setValue(30)
        dim_layout.addWidget(self.pied_base, 3, 1)
        
        dim_layout.addWidget(QLabel("Spessore [cm]:"), 3, 2)
        self.pied_spessore = QSpinBox()
        self.pied_spessore.setRange(20, 100)
        self.pied_spessore.setValue(30)
        dim_layout.addWidget(self.pied_spessore, 3, 3)
        
        dim_group.setLayout(dim_layout)
        scroll_layout.addWidget(dim_group)
        
        # Armatura
        arm_group = QGroupBox("Armatura")
        arm_layout = QGridLayout()
        
        arm_layout.addWidget(QLabel("Tipo acciaio:"), 0, 0)
        self.tipo_acciaio_ca = QComboBox()
        self.tipo_acciaio_ca.addItems(["B450C", "B450A"])
        arm_layout.addWidget(self.tipo_acciaio_ca, 0, 1)
        
        # Armatura architrave
        arm_layout.addWidget(QLabel("<b>Armatura architrave:</b>"), 1, 0, 1, 4)
        
        arm_layout.addWidget(QLabel("Superiore:"), 2, 0)
        self.arch_arm_sup = QSpinBox()
        self.arch_arm_sup.setRange(2, 8)
        self.arch_arm_sup.setValue(3)
        arm_layout.addWidget(self.arch_arm_sup, 2, 1)
        
        arm_layout.addWidget(QLabel("φ"), 2, 2)
        self.arch_diam_sup = QComboBox()
        self.arch_diam_sup.addItems(["12", "14", "16", "18", "20", "22", "24"])
        self.arch_diam_sup.setCurrentIndex(2)  # φ16
        arm_layout.addWidget(self.arch_diam_sup, 2, 3)
        
        arm_layout.addWidget(QLabel("Inferiore:"), 3, 0)
        self.arch_arm_inf = QSpinBox()
        self.arch_arm_inf.setRange(2, 8)
        self.arch_arm_inf.setValue(3)
        arm_layout.addWidget(self.arch_arm_inf, 3, 1)
        
        arm_layout.addWidget(QLabel("φ"), 3, 2)
        self.arch_diam_inf = QComboBox()
        self.arch_diam_inf.addItems(["12", "14", "16", "18", "20", "22", "24"])
        self.arch_diam_inf.setCurrentIndex(2)  # φ16
        arm_layout.addWidget(self.arch_diam_inf, 3, 3)
        
        arm_layout.addWidget(QLabel("Staffe φ:"), 4, 0)
        self.arch_staffe = QComboBox()
        self.arch_staffe.addItems(["8", "10", "12"])
        arm_layout.addWidget(self.arch_staffe, 4, 1)
        
        arm_layout.addWidget(QLabel("passo [cm]:"), 4, 2)
        self.arch_passo_staffe = QSpinBox()
        self.arch_passo_staffe.setRange(10, 30)
        self.arch_passo_staffe.setValue(20)
        arm_layout.addWidget(self.arch_passo_staffe, 4, 3)
        
        arm_group.setLayout(arm_layout)
        scroll_layout.addWidget(arm_group)
        
        # Collegamenti C.A.
        coll_ca_group = QGroupBox("Collegamenti e Riprese")
        coll_ca_layout = QGridLayout()
        
        coll_ca_layout.addWidget(QLabel("Tipo di ripresa con muratura:"), 0, 0)
        self.ripresa_ca = QComboBox()
        self.ripresa_ca.addItems([
            "Barre di ripresa",
            "Connettori a taglio",
            "Rete elettrosaldata",
            "Ripresa chimica"
        ])
        coll_ca_layout.addWidget(self.ripresa_ca, 0, 1)
        
        coll_ca_layout.addWidget(QLabel("Profondità ammorsamento [cm]:"), 1, 0)
        self.ammorsamento = QSpinBox()
        self.ammorsamento.setRange(10, 50)
        self.ammorsamento.setValue(20)
        coll_ca_layout.addWidget(self.ammorsamento, 1, 1)
        
        coll_ca_group.setLayout(coll_ca_layout)
        scroll_layout.addWidget(coll_ca_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        page.setLayout(layout)
        return page
        
    # Metodi di callback
    def on_tipo_changed(self, index):
        """Gestisce cambio tipo rinforzo"""
        if index < 2:  # Acciaio telaio completo o solo architrave
            self.stack.setCurrentIndex(0)
            show_piedritti = (index == 0)
            self.piedritto_label.setVisible(show_piedritti)
            self.piedritti_profilo.setVisible(show_piedritti)
            self.piedritti_n_profili.setVisible(show_piedritti)
            self.piedritti_interasse.setVisible(show_piedritti)
            self.piedritti_disposizione.setVisible(show_piedritti)
            self.piedritti_ruotato.setVisible(show_piedritti)
            self.vincoli_tabs.setTabEnabled(0, show_piedritti)  # Tab base piedritti
            self.vincoli_tabs.setTabEnabled(1, show_piedritti)  # Tab nodi
            self.arco_group.setVisible(False)
            
        elif index < 4:  # C.A. telaio completo o solo architrave
            self.stack.setCurrentIndex(1)
            show_piedritti = (index == 2)
            self.piedritti_ca_label.setVisible(show_piedritti)
            self.pied_base.setVisible(show_piedritti)
            self.pied_spessore.setVisible(show_piedritti)
            
        elif index == 4:  # Rinforzo ad arco in acciaio
            self.stack.setCurrentIndex(0)
            self.piedritto_label.setVisible(True)
            self.piedritti_profilo.setVisible(True)
            self.piedritti_n_profili.setVisible(True)
            self.piedritti_interasse.setVisible(True)
            self.piedritti_disposizione.setVisible(True)
            self.piedritti_ruotato.setVisible(True)
            self.vincoli_tabs.setTabEnabled(0, True)
            self.vincoli_tabs.setTabEnabled(1, True)
            self.vincoli_tabs.setTabEnabled(2, True)  # Tab muratura/arco
            self.arco_group.setVisible(False)
            
        elif index == 5:  # Rinforzo calandrato nell'arco
            self.stack.setCurrentIndex(0)
            self.piedritto_label.setVisible(False)
            self.piedritti_profilo.setVisible(False)
            self.piedritti_n_profili.setVisible(False)
            self.piedritti_interasse.setVisible(False)
            self.piedritti_disposizione.setVisible(False)
            self.piedritti_ruotato.setVisible(False)
            self.vincoli_tabs.setTabEnabled(0, False)
            self.vincoli_tabs.setTabEnabled(1, False)
            self.arco_group.setVisible(True)
            
        else:  # Nessun rinforzo
            self.stack.setCurrentIndex(2)
            
    def on_architrave_n_profili_changed(self, value):
        """Gestisce cambio numero profili architrave"""
        multi = value > 1
        self.architrave_interasse.setEnabled(multi)
        self.architrave_disposizione.setEnabled(multi)
        
    def on_piedritti_n_profili_changed(self, value):
        """Gestisce cambio numero profili piedritti"""
        multi = value > 1
        self.piedritti_interasse.setEnabled(multi)
        self.piedritti_disposizione.setEnabled(multi)
        
    def on_tipo_collegamento_changed(self, index):
        """Mostra/nasconde opzioni in base al tipo di collegamento profili"""
        self.bulloni_group.setVisible(index == 0)
        self.calastrelli_group.setVisible(index == 1)
        
    def on_sistema_ancoraggio_changed(self, index):
        """Mostra/nasconde opzioni ancoraggio"""
        self.chimici_group.setVisible(index in [0, 1])
        self.zanche_group.setVisible(index == 2)
        
    def on_tipo_giunzione_changed(self, index):
        """Mostra/nasconde opzioni giunzione"""
        self.saldatura_group.setVisible(index in [0, 2, 5])
        self.piastra_nodo_group.setVisible(index in [1, 2])
        
    def on_tipo_base_changed(self, index):
        """Gestisce cambio tipo base"""
        self.piastra_base_group.setVisible(index in [2, 3, 4])
        self.trave_base_group.setVisible(index == 1)
        
    def on_vincolo_changed(self, combo, k_trasl, k_rot):
        """Abilita rigidezze per vincoli elastici"""
        is_elastic = "elastico" in combo.currentText().lower()
        k_trasl.setEnabled(is_elastic)
        k_rot.setEnabled(is_elastic)
        
    def on_vincoli_simmetrici_changed(self, checked):
        """Gestisce cambio vincoli simmetrici"""
        if checked:
            # Copia vincoli sx su dx
            self.vincolo_base_dx.setCurrentIndex(self.vincolo_base_sx.currentIndex())
            self.k_trasl_base_dx.setValue(self.k_trasl_base_sx.value())
            self.k_rot_base_dx.setValue(self.k_rot_base_sx.value())
            
        # Abilita/disabilita controlli dx
        self.vincolo_base_dx.setEnabled(not checked)
        is_elastic = "elastico" in self.vincolo_base_dx.currentText().lower()
        self.k_trasl_base_dx.setEnabled(not checked and is_elastic)
        self.k_rot_base_dx.setEnabled(not checked and is_elastic)
        
    def on_vincolo_nodo_changed(self, combo, riduzione):
        """Abilita riduzione per semincastri"""
        needs_reduction = "riduzione" in combo.currentText().lower()
        riduzione.setEnabled(needs_reduction)
        
    def on_vincoli_nodi_simmetrici_changed(self, checked):
        """Gestisce vincoli nodi simmetrici"""
        if checked:
            self.vincolo_nodo_dx.setCurrentIndex(self.vincolo_nodo_sx.currentIndex())
            self.riduzione_nodo_dx.setValue(self.riduzione_nodo_sx.value())
            
        self.vincolo_nodo_dx.setEnabled(not checked)
        needs_reduction = "riduzione" in self.vincolo_nodo_dx.currentText().lower()
        self.riduzione_nodo_dx.setEnabled(not checked and needs_reduction)
        
    def on_collaborazione_changed(self, index):
        """Gestisce cambio collaborazione muratura"""
        self.larghezza_collab.setEnabled(index == 3)  # Definita dall'utente
        
    def update_profili_disponibili(self):
        """Aggiorna lista profili disponibili"""
        tipo = self.tipo_profilo.currentText()
        
        # Database profili
        profili = {
            "HEA": ["100", "120", "140", "160", "180", "200", "220", "240", "260", "280", "300"],
            "HEB": ["100", "120", "140", "160", "180", "200", "220", "240", "260", "280", "300"],
            "HEM": ["100", "120", "140", "160", "180", "200", "220", "240", "260", "280", "300"],
            "IPE": ["80", "100", "120", "140", "160", "180", "200", "220", "240", "270", "300"],
            "UNP": ["50", "65", "80", "100", "120", "140", "160", "180", "200", "220", "240"],
            "L": ["50x50x5", "60x60x6", "70x70x7", "80x80x8", "90x90x9", "100x100x10"],
            "Tubolare": ["60x60x3", "80x80x4", "100x100x5", "120x120x5", "140x140x6", "160x160x6"]
        }
        
        profili_list = profili.get(tipo, [])
        
        # Aggiorna combo box
        for combo in [self.architrave_profilo, self.piedritti_profilo, 
                     self.trave_base_profilo, self.profilo_calandrato]:
            combo.clear()
            for profilo in profili_list:
                combo.addItem(f"{tipo} {profilo}")
                
    def get_data(self):
        """Restituisce i dati del rinforzo"""
        tipo_index = self.tipo_combo.currentIndex()
        
        if tipo_index >= 6:  # Nessun rinforzo
            return None
            
        data = {
            'tipo': self.tipo_combo.currentText(),
            'note': self.note_text.toPlainText()
        }
        
        if tipo_index < 2 or tipo_index in [4, 5]:  # Acciaio
            data.update({
                'materiale': 'acciaio',
                'classe_acciaio': self.classe_acciaio.currentText(),
                'architrave': {
                    'profilo': self.architrave_profilo.currentText(),
                    'n_profili': self.architrave_n_profili.value(),
                    'interasse': self.architrave_interasse.value(),
                    'disposizione': self.architrave_disposizione.currentText(),
                    'ruotato': self.architrave_ruotato.isChecked()
                },
                'irrigidimenti': self.irrigidimenti.value()
            })
            
            # Collegamenti profili
            if self.architrave_n_profili.value() > 1:
                data['collegamenti_profili'] = {
                    'tipo': self.tipo_collegamento_profili.currentText()
                }
                if self.tipo_collegamento_profili.currentIndex() == 0:  # Bulloni
                    data['collegamenti_profili']['bulloni'] = {
                        'classe': self.classe_bulloni.currentText(),
                        'diametro': self.diametro_bulloni.currentText(),
                        'interasse': self.interasse_long.value(),
                        'n_file': self.n_file_bulloni.value(),
                        'precarico': self.precarico.isChecked()
                    }
                elif self.tipo_collegamento_profili.currentIndex() == 1:  # Calastrelli
                    data['collegamenti_profili']['calastrelli'] = {
                        'tipo': self.tipo_calastrello.currentText(),
                        'dimensioni': self.dim_calastrello.text(),
                        'passo': self.passo_calastrelli.value()
                    }
                    
            # Giunzioni
            data['giunzioni'] = {
                'tipo_nodo': self.tipo_giunzione_nodo.currentText()
            }
            if self.saldatura_group.isVisible():
                data['giunzioni']['saldatura'] = {
                    'tipo': self.tipo_saldatura.currentText(),
                    'altezza_cordone': self.altezza_cordone.value(),
                    'controllo': self.controllo_saldatura.currentText()
                }
            if self.piastra_nodo_group.isVisible():
                data['giunzioni']['piastra'] = {
                    'spessore': self.spessore_piastra_nodo.value(),
                    'dimensioni': self.dim_piastra_nodo.text(),
                    'n_bulloni': self.n_bulloni_lato.value(),
                    'diametro_bulloni': self.diam_bulloni_piastra.currentText()
                }
            if self.irrigidimenti_nodo.isChecked():
                data['giunzioni']['irrigidimenti'] = self.tipo_irrigidimento.currentText()
                
            # Vincoli
            data['vincoli'] = {}
            
            # Vincoli base (solo se telaio)
            if tipo_index in [0, 4]:
                data['vincoli']['base_sx'] = {
                    'tipo': self.vincolo_base_sx.currentText()
                }
                if "elastico" in self.vincolo_base_sx.currentText().lower():
                    data['vincoli']['base_sx']['k_trasl'] = self.k_trasl_base_sx.value()
                    data['vincoli']['base_sx']['k_rot'] = self.k_rot_base_sx.value()
                    
                if not self.vincoli_base_simmetrici.isChecked():
                    data['vincoli']['base_dx'] = {
                        'tipo': self.vincolo_base_dx.currentText()
                    }
                    if "elastico" in self.vincolo_base_dx.currentText().lower():
                        data['vincoli']['base_dx']['k_trasl'] = self.k_trasl_base_dx.value()
                        data['vincoli']['base_dx']['k_rot'] = self.k_rot_base_dx.value()
                else:
                    data['vincoli']['base_dx'] = data['vincoli']['base_sx'].copy()
                    
                # Vincoli nodo
                data['vincoli']['nodo_sx'] = {
                    'tipo': self.vincolo_nodo_sx.currentText()
                }
                if "riduzione" in self.vincolo_nodo_sx.currentText().lower():
                    data['vincoli']['nodo_sx']['riduzione'] = self.riduzione_nodo_sx.value()
                    
                if not self.vincoli_nodi_simmetrici.isChecked():
                    data['vincoli']['nodo_dx'] = {
                        'tipo': self.vincolo_nodo_dx.currentText()
                    }
                    if "riduzione" in self.vincolo_nodo_dx.currentText().lower():
                        data['vincoli']['nodo_dx']['riduzione'] = self.riduzione_nodo_dx.value()
                else:
                    data['vincoli']['nodo_dx'] = data['vincoli']['nodo_sx'].copy()
                    
            # Interazione muratura
            data['vincoli']['collaborazione'] = {
                'tipo': self.collaborazione_muratura.currentText()
            }
            if self.collaborazione_muratura.currentIndex() == 3:
                data['vincoli']['collaborazione']['larghezza'] = self.larghezza_collab.value()
                
            # Vincoli arco (se presente)
            if tipo_index == 4:
                data['vincoli']['arco_sx'] = self.vincolo_arco_sx.currentText()
                data['vincoli']['arco_dx'] = self.vincolo_arco_dx.currentText()
                data['vincoli']['pressione_contatto'] = self.pressione_contatto.value()
                
            # Opzioni avanzate
            if self.secondo_ordine.isChecked() or self.non_linearita.isChecked() or \
               self.imperfezione.value() > 0 or self.ridistribuzione.value() > 0:
                data['vincoli']['avanzate'] = {
                    'secondo_ordine': self.secondo_ordine.isChecked(),
                    'non_linearita': self.non_linearita.isChecked(),
                    'imperfezione': self.imperfezione.value(),
                    'ridistribuzione': self.ridistribuzione.value()
                }
                
            # Ancoraggi
            data['ancoraggio'] = {
                'sistema': self.sistema_ancoraggio.currentText()
            }
            
            if self.chimici_group.isVisible():
                data['ancoraggio']['chimici'] = {
                    'tipo_resina': self.tipo_resina.currentText(),
                    'diametro': self.diametro_barra.currentText(),
                    'profondita': self.profondita_ancoraggio.value(),
                    'n_per_nodo': self.n_ancoraggi_nodo.value(),
                    'disposizione': self.disposizione_ancoraggi.currentText()
                }
            elif self.zanche_group.isVisible():
                data['ancoraggio']['zanche'] = {
                    'tipo': self.tipo_zanca.currentText(),
                    'dimensioni': self.dim_zanca.text(),
                    'n_per_metro': self.n_zanche_metro.value(),
                    'ammorsamento': self.ammorsamento_zanche.value()
                }
                
            # Base
            data['base'] = {
                'tipo': self.tipo_base.currentText()
            }
            if self.piastra_base_group.isVisible():
                data['base']['piastra'] = {
                    'dimensioni': self.dim_piastra_base.text(),
                    'n_tirafondi': self.n_tirafondi.value(),
                    'diam_tirafondi': self.diam_tirafondi.currentText(),
                    'lungh_tirafondi': self.lungh_tirafondi.value(),
                    'malta': self.malta_livellamento.currentText(),
                    'spessore_malta': self.spessore_malta.value()
                }
            elif self.trave_base_group.isVisible():
                data['base']['trave'] = {
                    'profilo': self.trave_base_profilo.currentText(),
                    'n_profili': self.trave_base_n_profili.value()
                }
                
            # Rinforzo locale
            if self.rinforzo_locale.isChecked():
                data['rinforzo_locale'] = self.tipo_rinforzo_locale.currentText()
                
            # Piedritti (se telaio)
            if tipo_index in [0, 4]:
                data['piedritti'] = {
                    'profilo': self.piedritti_profilo.currentText(),
                    'n_profili': self.piedritti_n_profili.value(),
                    'interasse': self.piedritti_interasse.value(),
                    'disposizione': self.piedritti_disposizione.currentText(),
                    'ruotato': self.piedritti_ruotato.isChecked()
                }
                
            # Arco calandrato
            if tipo_index == 5:
                data['arco'] = {
                    'tipo_apertura': self.tipo_apertura_curva.currentText(),
                    'raggio': self.raggio_arco.value(),
                    'freccia': self.freccia_arco.value(),
                    'profilo': self.profilo_calandrato.currentText(),
                    'n_profili': self.calandrato_n_profili.value(),
                    'metodo': self.metodo_calandratura.currentText()
                }
                
        else:  # C.A.
            data.update({
                'materiale': 'ca',
                'classe_cls': self.classe_cls.currentText(),
                'copriferro': self.copriferro.value(),
                'tipo_acciaio': self.tipo_acciaio_ca.currentText(),
                'architrave': {
                    'base': self.arch_base.value(),
                    'altezza': self.arch_altezza.value(),
                    'armatura_sup': f"{self.arch_arm_sup.value()}φ{self.arch_diam_sup.currentText()}",
                    'armatura_inf': f"{self.arch_arm_inf.value()}φ{self.arch_diam_inf.currentText()}",
                    'staffe': f"φ{self.arch_staffe.currentText()}/{self.arch_passo_staffe.value()}"
                },
                'collegamenti': {
                    'tipo': self.ripresa_ca.currentText(),
                    'ammorsamento': self.ammorsamento.value()
                }
            })
            
            if tipo_index == 2:  # Telaio completo
                data['piedritti'] = {
                    'base': self.pied_base.value(),
                    'spessore': self.pied_spessore.value()
                }
                
        return data
        
    def load_data(self):
        """Carica dati esistenti"""
        if not self.rinforzo_data:
            return
            
        # Trova indice del tipo
        tipo = self.rinforzo_data.get('tipo', '')
        index = self.tipo_combo.findText(tipo)
        if index >= 0:
            self.tipo_combo.setCurrentIndex(index)
            
        # Carica dati specifici per materiale
        if self.rinforzo_data.get('materiale') == 'acciaio':
            # Classe acciaio
            classe = self.rinforzo_data.get('classe_acciaio', 'S235')
            index = self.classe_acciaio.findText(classe)
            if index >= 0:
                self.classe_acciaio.setCurrentIndex(index)
                
            # Tipo profilo
            if 'architrave' in self.rinforzo_data:
                profilo = self.rinforzo_data['architrave'].get('profilo', '')
                # Estrai tipo profilo (es. "HEA" da "HEA 200")
                tipo_profilo = profilo.split()[0] if profilo else 'HEA'
                index = self.tipo_profilo.findText(tipo_profilo)
                if index >= 0:
                    self.tipo_profilo.setCurrentIndex(index)
                    
            # Dopo aver impostato il tipo, aggiorna i profili disponibili
            self.update_profili_disponibili()
            
            # Ora carica i profili specifici
            if 'architrave' in self.rinforzo_data:
                arch = self.rinforzo_data['architrave']
                profilo = arch.get('profilo', '')
                index = self.architrave_profilo.findText(profilo)
                if index >= 0:
                    self.architrave_profilo.setCurrentIndex(index)
                self.architrave_n_profili.setValue(arch.get('n_profili', 1))
                self.architrave_interasse.setValue(arch.get('interasse', 0))
                
                disp = arch.get('disposizione', 'In linea')
                index = self.architrave_disposizione.findText(disp)
                if index >= 0:
                    self.architrave_disposizione.setCurrentIndex(index)
                    
                self.architrave_ruotato.setChecked(arch.get('ruotato', False))
                
            if 'piedritti' in self.rinforzo_data:
                pied = self.rinforzo_data['piedritti']
                profilo = pied.get('profilo', '')
                index = self.piedritti_profilo.findText(profilo)
                if index >= 0:
                    self.piedritti_profilo.setCurrentIndex(index)
                self.piedritti_n_profili.setValue(pied.get('n_profili', 1))
                self.piedritti_interasse.setValue(pied.get('interasse', 0))
                
                disp = pied.get('disposizione', 'In linea')
                index = self.piedritti_disposizione.findText(disp)
                if index >= 0:
                    self.piedritti_disposizione.setCurrentIndex(index)
                    
                self.piedritti_ruotato.setChecked(pied.get('ruotato', False))
                
            # Collegamenti profili
            if 'collegamenti_profili' in self.rinforzo_data:
                coll = self.rinforzo_data['collegamenti_profili']
                tipo = coll.get('tipo', '')
                index = self.tipo_collegamento_profili.findText(tipo)
                if index >= 0:
                    self.tipo_collegamento_profili.setCurrentIndex(index)
                    
                if 'bulloni' in coll:
                    bull = coll['bulloni']
                    self.classe_bulloni.setCurrentText(bull.get('classe', '8.8'))
                    self.diametro_bulloni.setCurrentText(bull.get('diametro', 'M16'))
                    self.interasse_long.setValue(bull.get('interasse', 30))
                    self.n_file_bulloni.setValue(bull.get('n_file', 2))
                    self.precarico.setChecked(bull.get('precarico', False))
                    
                elif 'calastrelli' in coll:
                    cal = coll['calastrelli']
                    self.tipo_calastrello.setCurrentText(cal.get('tipo', 'Piatto'))
                    self.dim_calastrello.setText(cal.get('dimensioni', '80x8'))
                    self.passo_calastrelli.setValue(cal.get('passo', 60))
                    
            # Giunzioni
            if 'giunzioni' in self.rinforzo_data:
                giun = self.rinforzo_data['giunzioni']
                tipo_nodo = giun.get('tipo_nodo', '')
                index = self.tipo_giunzione_nodo.findText(tipo_nodo)
                if index >= 0:
                    self.tipo_giunzione_nodo.setCurrentIndex(index)
                    
                if 'saldatura' in giun:
                    sald = giun['saldatura']
                    self.tipo_saldatura.setCurrentText(sald.get('tipo', 'A cordone d\'angolo'))
                    self.altezza_cordone.setValue(sald.get('altezza_cordone', 6))
                    self.controllo_saldatura.setCurrentText(sald.get('controllo', 'Visivo'))
                    
                if 'piastra' in giun:
                    pias = giun['piastra']
                    self.spessore_piastra_nodo.setValue(pias.get('spessore', 20))
                    self.dim_piastra_nodo.setText(pias.get('dimensioni', '300x400'))
                    self.n_bulloni_lato.setValue(pias.get('n_bulloni', 4))
                    self.diam_bulloni_piastra.setCurrentText(pias.get('diametro_bulloni', 'M20'))
                    
                if 'irrigidimenti' in giun:
                    self.irrigidimenti_nodo.setChecked(True)
                    self.tipo_irrigidimento.setCurrentText(giun['irrigidimenti'])
                    
            # Vincoli
            if 'vincoli' in self.rinforzo_data:
                vinc = self.rinforzo_data['vincoli']
                
                # Base
                if 'base_sx' in vinc:
                    base_sx = vinc['base_sx']
                    tipo = base_sx.get('tipo', '')
                    index = self.vincolo_base_sx.findText(tipo)
                    if index >= 0:
                        self.vincolo_base_sx.setCurrentIndex(index)
                    if 'k_trasl' in base_sx:
                        self.k_trasl_base_sx.setValue(base_sx['k_trasl'])
                    if 'k_rot' in base_sx:
                        self.k_rot_base_sx.setValue(base_sx['k_rot'])
                        
                if 'base_dx' in vinc:
                    self.vincoli_base_simmetrici.setChecked(False)
                    base_dx = vinc['base_dx']
                    tipo = base_dx.get('tipo', '')
                    index = self.vincolo_base_dx.findText(tipo)
                    if index >= 0:
                        self.vincolo_base_dx.setCurrentIndex(index)
                    if 'k_trasl' in base_dx:
                        self.k_trasl_base_dx.setValue(base_dx['k_trasl'])
                    if 'k_rot' in base_dx:
                        self.k_rot_base_dx.setValue(base_dx['k_rot'])
                        
                # Nodi
                if 'nodo_sx' in vinc:
                    nodo_sx = vinc['nodo_sx']
                    tipo = nodo_sx.get('tipo', '')
                    index = self.vincolo_nodo_sx.findText(tipo)
                    if index >= 0:
                        self.vincolo_nodo_sx.setCurrentIndex(index)
                    if 'riduzione' in nodo_sx:
                        self.riduzione_nodo_sx.setValue(nodo_sx['riduzione'])
                        
                if 'nodo_dx' in vinc:
                    self.vincoli_nodi_simmetrici.setChecked(False)
                    nodo_dx = vinc['nodo_dx']
                    tipo = nodo_dx.get('tipo', '')
                    index = self.vincolo_nodo_dx.findText(tipo)
                    if index >= 0:
                        self.vincolo_nodo_dx.setCurrentIndex(index)
                    if 'riduzione' in nodo_dx:
                        self.riduzione_nodo_dx.setValue(nodo_dx['riduzione'])
                        
                # Collaborazione
                if 'collaborazione' in vinc:
                    coll = vinc['collaborazione']
                    tipo = coll.get('tipo', '')
                    index = self.collaborazione_muratura.findText(tipo)
                    if index >= 0:
                        self.collaborazione_muratura.setCurrentIndex(index)
                    if 'larghezza' in coll:
                        self.larghezza_collab.setValue(coll['larghezza'])
                        
                # Arco
                if 'arco_sx' in vinc:
                    self.vincolo_arco_sx.setCurrentText(vinc['arco_sx'])
                if 'arco_dx' in vinc:
                    self.vincolo_arco_dx.setCurrentText(vinc['arco_dx'])
                if 'pressione_contatto' in vinc:
                    self.pressione_contatto.setValue(vinc['pressione_contatto'])
                    
                # Avanzate
                if 'avanzate' in vinc:
                    av = vinc['avanzate']
                    self.secondo_ordine.setChecked(av.get('secondo_ordine', False))
                    self.non_linearita.setChecked(av.get('non_linearita', False))
                    self.imperfezione.setValue(av.get('imperfezione', 0))
                    self.ridistribuzione.setValue(av.get('ridistribuzione', 0))
                    
            # Ancoraggi
            if 'ancoraggio' in self.rinforzo_data:
                anc = self.rinforzo_data['ancoraggio']
                sistema = anc.get('sistema', '')
                index = self.sistema_ancoraggio.findText(sistema)
                if index >= 0:
                    self.sistema_ancoraggio.setCurrentIndex(index)
                    
                if 'chimici' in anc:
                    chim = anc['chimici']
                    self.tipo_resina.setCurrentText(chim.get('tipo_resina', 'Epossidica pura'))
                    self.diametro_barra.setCurrentText(chim.get('diametro', 'M16'))
                    self.profondita_ancoraggio.setValue(chim.get('profondita', 20))
                    self.n_ancoraggi_nodo.setValue(chim.get('n_per_nodo', 4))
                    self.disposizione_ancoraggi.setCurrentText(chim.get('disposizione', 'Quadrata'))
                    
                elif 'zanche' in anc:
                    zan = anc['zanche']
                    self.tipo_zanca.setCurrentText(zan.get('tipo', 'Zanca a L'))
                    self.dim_zanca.setText(zan.get('dimensioni', '200x100x10'))
                    self.n_zanche_metro.setValue(zan.get('n_per_metro', 4))
                    self.ammorsamento_zanche.setValue(zan.get('ammorsamento', 20))
                    
            # Base
            if 'base' in self.rinforzo_data:
                base = self.rinforzo_data['base']
                tipo_base = base.get('tipo', '')
                index = self.tipo_base.findText(tipo_base)
                if index >= 0:
                    self.tipo_base.setCurrentIndex(index)
                    
                if 'piastra' in base:
                    pias = base['piastra']
                    self.dim_piastra_base.setText(pias.get('dimensioni', '400x400x30'))
                    self.n_tirafondi.setValue(pias.get('n_tirafondi', 4))
                    self.diam_tirafondi.setCurrentText(pias.get('diam_tirafondi', 'M24'))
                    self.lungh_tirafondi.setValue(pias.get('lungh_tirafondi', 50))
                    self.malta_livellamento.setCurrentText(pias.get('malta', 'Malta cementizia antiritiro'))
                    self.spessore_malta.setValue(pias.get('spessore_malta', 30))
                    
                elif 'trave' in base:
                    trave = base['trave']
                    profilo = trave.get('profilo', '')
                    index = self.trave_base_profilo.findText(profilo)
                    if index >= 0:
                        self.trave_base_profilo.setCurrentIndex(index)
                    self.trave_base_n_profili.setValue(trave.get('n_profili', 1))
                    
            # Rinforzo locale
            if 'rinforzo_locale' in self.rinforzo_data:
                self.rinforzo_locale.setChecked(True)
                self.tipo_rinforzo_locale.setCurrentText(self.rinforzo_data['rinforzo_locale'])
                
            # Irrigidimenti
            self.irrigidimenti.setValue(self.rinforzo_data.get('irrigidimenti', 0))
            
            # Arco calandrato
            if 'arco' in self.rinforzo_data:
                arco = self.rinforzo_data['arco']
                self.tipo_apertura_curva.setCurrentText(arco.get('tipo_apertura', 'Arco a tutto sesto'))
                self.raggio_arco.setValue(arco.get('raggio', 150))
                self.freccia_arco.setValue(arco.get('freccia', 30))
                
                profilo = arco.get('profilo', '')
                index = self.profilo_calandrato.findText(profilo)
                if index >= 0:
                    self.profilo_calandrato.setCurrentIndex(index)
                    
                self.calandrato_n_profili.setValue(arco.get('n_profili', 1))
                self.metodo_calandratura.setCurrentText(arco.get('metodo', 'A freddo'))
                
        elif self.rinforzo_data.get('materiale') == 'ca':
            # Dati C.A.
            self.classe_cls.setCurrentText(
                self.rinforzo_data.get('classe_cls', 'C25/30')
            )
            self.copriferro.setValue(
                self.rinforzo_data.get('copriferro', 30)
            )
            self.tipo_acciaio_ca.setCurrentText(
                self.rinforzo_data.get('tipo_acciaio', 'B450C')
            )
            
            # Dimensioni architrave
            if 'architrave' in self.rinforzo_data:
                arch = self.rinforzo_data['architrave']
                self.arch_base.setValue(arch.get('base', 30))
                self.arch_altezza.setValue(arch.get('altezza', 40))
                
                # Armature (parsing delle stringhe tipo "3φ16")
                arm_sup = arch.get('armatura_sup', '3φ16')
                if 'φ' in arm_sup:
                    n_ferri = int(arm_sup.split('φ')[0])
                    diam = arm_sup.split('φ')[1]
                    self.arch_arm_sup.setValue(n_ferri)
                    index = self.arch_diam_sup.findText(diam)
                    if index >= 0:
                        self.arch_diam_sup.setCurrentIndex(index)
                        
                arm_inf = arch.get('armatura_inf', '3φ16')
                if 'φ' in arm_inf:
                    n_ferri = int(arm_inf.split('φ')[0])
                    diam = arm_inf.split('φ')[1]
                    self.arch_arm_inf.setValue(n_ferri)
                    index = self.arch_diam_inf.findText(diam)
                    if index >= 0:
                        self.arch_diam_inf.setCurrentIndex(index)
                        
                # Staffe (parsing "φ8/20")
                staffe = arch.get('staffe', 'φ8/20')
                if 'φ' in staffe and '/' in staffe:
                    diam = staffe.split('φ')[1].split('/')[0]
                    passo = int(staffe.split('/')[1])
                    index = self.arch_staffe.findText(diam)
                    if index >= 0:
                        self.arch_staffe.setCurrentIndex(index)
                    self.arch_passo_staffe.setValue(passo)
                    
            # Dimensioni piedritti
            if 'piedritti' in self.rinforzo_data:
                pied = self.rinforzo_data['piedritti']
                self.pied_base.setValue(pied.get('base', 30))
                self.pied_spessore.setValue(pied.get('spessore', 30))
                
            # Collegamenti
            if 'collegamenti' in self.rinforzo_data:
                coll = self.rinforzo_data['collegamenti']
                self.ripresa_ca.setCurrentText(coll.get('tipo', 'Barre di ripresa'))
                self.ammorsamento.setValue(coll.get('ammorsamento', 20))
                
        # Note
        self.note_text.setPlainText(self.rinforzo_data.get('note', ''))


# Resto del file OpeningsModule rimane invariato...
class OpeningDetailWidget(QWidget):
    """Widget per visualizzare dettagli di un'apertura"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Info apertura
        info_group = QGroupBox("Informazioni Apertura")
        info_layout = QFormLayout()
        
        self.tipo_label = QLabel("-")
        info_layout.addRow("Tipo:", self.tipo_label)
        
        self.dim_label = QLabel("-")
        info_layout.addRow("Dimensioni:", self.dim_label)
        
        self.pos_label = QLabel("-")
        info_layout.addRow("Posizione:", self.pos_label)
        
        self.area_label = QLabel("-")
        info_layout.addRow("Area:", self.area_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Info rinforzo
        rinforzo_group = QGroupBox("Rinforzo Applicato")
        rinforzo_layout = QFormLayout()
        
        self.rinforzo_tipo_label = QLabel("Nessuno")
        rinforzo_layout.addRow("Tipo:", self.rinforzo_tipo_label)
        
        self.rinforzo_mat_label = QLabel("-")
        rinforzo_layout.addRow("Materiale:", self.rinforzo_mat_label)
        
        self.rinforzo_desc_label = QLabel("-")
        self.rinforzo_desc_label.setWordWrap(True)
        rinforzo_layout.addRow("Descrizione:", self.rinforzo_desc_label)
        
        # Aggiungi info vincoli
        self.vincoli_label = QLabel("-")
        self.vincoli_label.setWordWrap(True)
        rinforzo_layout.addRow("Vincoli:", self.vincoli_label)
        
        rinforzo_group.setLayout(rinforzo_layout)
        layout.addWidget(rinforzo_group)
        
        # Maschi murari residui
        maschi_group = QGroupBox("Maschi Murari")
        maschi_layout = QFormLayout()
        
        self.maschio_sx_label = QLabel("-")
        maschi_layout.addRow("Maschio sx:", self.maschio_sx_label)
        
        self.maschio_dx_label = QLabel("-")
        maschi_layout.addRow("Maschio dx:", self.maschio_dx_label)
        
        maschi_group.setLayout(maschi_layout)
        layout.addWidget(maschi_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_opening(self, opening_data, index, wall_data=None, all_openings=None):
        """Aggiorna visualizzazione con dati apertura"""
        if not opening_data:
            return
            
        # Info base
        self.tipo_label.setText(opening_data.get('type', 'Rettangolare'))
        self.dim_label.setText(f"{opening_data['width']} × {opening_data['height']} cm")
        self.pos_label.setText(f"X: {opening_data['x']} cm, Y: {opening_data['y']} cm")
        
        # Area
        area = opening_data['width'] * opening_data['height'] / 10000
        self.area_label.setText(f"{area:.2f} m²")
        
        # Rinforzo
        rinforzo = opening_data.get('rinforzo')
        if rinforzo:
            self.rinforzo_tipo_label.setText(rinforzo['tipo'])
            self.rinforzo_mat_label.setText(rinforzo.get('materiale', '-').upper())
            
            # Descrizione dettagliata - CORREZIONE QUI
            if rinforzo['materiale'] == 'acciaio':
                desc = f"Classe {rinforzo['classe_acciaio']}\n"
                # Usa .get() per evitare KeyError
                desc += f"Architrave: {rinforzo['architrave'].get('n_profili', 1)}x {rinforzo['architrave'].get('profilo', 'N.D.')}"
                if rinforzo['architrave'].get('ruotato'):
                    desc += " - Ruotato 90°"
                    
                if 'piedritti' in rinforzo:
                    desc += f"\nPiedritti: {rinforzo['piedritti'].get('n_profili', 1)}x {rinforzo['piedritti'].get('profilo', 'N.D.')}"
                    if rinforzo['piedritti'].get('ruotato'):
                        desc += " - Ruotato 90°"
                        
                # Base
                if 'base' in rinforzo:
                    desc += f"\nBase: {rinforzo['base']['tipo']}"
                    
                self.rinforzo_desc_label.setText(desc)
                
                # Vincoli
                vincoli_text = ""
                if 'vincoli' in rinforzo:
                    vinc = rinforzo['vincoli']
                    if 'base_sx' in vinc:
                        vincoli_text = f"Base SX: {vinc['base_sx']['tipo']}"
                        if 'base_dx' in vinc and vinc['base_dx']['tipo'] != vinc['base_sx']['tipo']:
                            vincoli_text += f"\nBase DX: {vinc['base_dx']['tipo']}"
                    if 'nodo_sx' in vinc:
                        vincoli_text += f"\nNodo SX: {vinc['nodo_sx']['tipo']}"
                        if 'nodo_dx' in vinc and vinc['nodo_dx']['tipo'] != vinc['nodo_sx']['tipo']:
                            vincoli_text += f"\nNodo DX: {vinc['nodo_dx']['tipo']}"
                self.vincoli_label.setText(vincoli_text if vincoli_text else "-")
                
            else:  # C.A.
                desc = f"Cls {rinforzo['classe_cls']}\n"
                desc += f"Architrave: {rinforzo['architrave']['base']}×{rinforzo['architrave']['altezza']} cm"
                self.rinforzo_desc_label.setText(desc)
                self.vincoli_label.setText("-")
        else:
            self.rinforzo_tipo_label.setText("Nessuno")
            self.rinforzo_mat_label.setText("-")
            self.rinforzo_desc_label.setText("-")
            self.vincoli_label.setText("-")
            
        # Maschi murari (se disponibili i dati del muro)
        if wall_data and all_openings:
            # Calcola maschi murari adiacenti
            sorted_openings = sorted(all_openings, key=lambda o: o['x'])
            opening_index = sorted_openings.index(opening_data)
            
            # Maschio sinistro
            if opening_index == 0:
                maschio_sx = opening_data['x']
            else:
                prev_opening = sorted_openings[opening_index - 1]
                maschio_sx = opening_data['x'] - (prev_opening['x'] + prev_opening['width'])
            
            # Maschio destro
            if opening_index == len(sorted_openings) - 1:
                maschio_dx = wall_data['length'] - (opening_data['x'] + opening_data['width'])
            else:
                next_opening = sorted_openings[opening_index + 1]
                maschio_dx = next_opening['x'] - (opening_data['x'] + opening_data['width'])
                
            self.maschio_sx_label.setText(f"{maschio_sx} cm")
            self.maschio_dx_label.setText(f"{maschio_dx} cm")


class OpeningsModule(QWidget):
    """Modulo per configurazione aperture e rinforzi con canvas avanzato"""
    
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.wall_data = None
        self.openings = []
        self.current_opening_index = -1
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Costruisce interfaccia aperture"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pannello sinistro - Lista aperture
        left_panel = self.create_left_panel()
        
        # Pannello centrale - Dettagli
        center_panel = self.create_center_panel()
        
        # Pannello destro - Visualizzazione
        right_panel = self.create_right_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)  # Lista stretta
        splitter.setStretchFactor(1, 2)  # Dettagli medio
        splitter.setStretchFactor(2, 3)  # Visualizzazione grande
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def create_left_panel(self):
        """Crea pannello sinistro con lista aperture"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Titolo
        title = QLabel("<h3>Aperture</h3>")
        layout.addWidget(title)
        
        # Nota informativa
        info_label = QLabel("<small><i>Le aperture devono essere prima create nel modulo 'Struttura'</i></small>")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Lista aperture
        self.openings_tree = QTreeWidget()
        self.openings_tree.setHeaderLabels(["Apertura", "Tipo", "Rinforzo"])
        self.openings_tree.setRootIsDecorated(False)
        self.openings_tree.setAlternatingRowColors(True)
        layout.addWidget(self.openings_tree)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Aggiungi")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOkButton))
        self.add_btn.setEnabled(False)
        self.add_btn.setToolTip("Aggiungi apertura dal modulo Struttura")
        buttons_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Rimuovi")
        self.remove_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.remove_btn.setEnabled(False)
        buttons_layout.addWidget(self.remove_btn)
        
        layout.addLayout(buttons_layout)
        
        # Riepilogo
        summary_group = QGroupBox("Riepilogo")
        summary_layout = QFormLayout()
        
        self.n_aperture_label = QLabel("0")
        summary_layout.addRow("N° aperture:", self.n_aperture_label)
        
        self.n_rinforzi_label = QLabel("0")
        summary_layout.addRow("N° con rinforzo:", self.n_rinforzi_label)
        
        self.area_totale_label = QLabel("0.00 m²")
        summary_layout.addRow("Area totale aperture:", self.area_totale_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        panel.setLayout(layout)
        return panel
        
    def create_center_panel(self):
        """Crea pannello centrale con dettagli"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Titolo
        title = QLabel("<h3>Dettagli Apertura</h3>")
        layout.addWidget(title)
        
        # Widget dettagli
        self.detail_widget = OpeningDetailWidget()
        layout.addWidget(self.detail_widget)
        
        # Pulsanti azioni
        actions_group = QGroupBox("Azioni")
        actions_layout = QVBoxLayout()
        
        self.edit_geometry_btn = QPushButton("Modifica Geometria")
        self.edit_geometry_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_geometry_btn)
        
        self.configure_rinforzo_btn = QPushButton("Configura Rinforzo")
        self.configure_rinforzo_btn.setEnabled(False)
        actions_layout.addWidget(self.configure_rinforzo_btn)
        
        self.remove_rinforzo_btn = QPushButton("Rimuovi Rinforzo")
        self.remove_rinforzo_btn.setEnabled(False)
        actions_layout.addWidget(self.remove_rinforzo_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self):
        """Crea pannello destro con visualizzazione"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Titolo
        title = QLabel("<h3>Visualizzazione</h3>")
        layout.addWidget(title)
        
        # Canvas avanzato
        self.wall_canvas = AdvancedWallCanvas()
        self.wall_canvas.setMinimumSize(400, 300)
        layout.addWidget(self.wall_canvas)
        
        # Legenda
        legend_group = QGroupBox("Legenda")
        legend_layout = QGridLayout()
        
        # Colori aperture
        colors = [
            ("Apertura nuova", QColor(255, 0, 0)),
            ("Apertura esistente", QColor(255, 165, 0)),
            ("Con rinforzo acciaio", QColor(0, 0, 255)),
            ("Con rinforzo C.A.", QColor(128, 0, 128)),
            ("Selezionata", QColor(0, 120, 215))
        ]
        
        for i, (label, color) in enumerate(colors):
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            legend_layout.addWidget(color_label, i // 2, (i % 2) * 2)
            legend_layout.addWidget(QLabel(label), i // 2, (i % 2) * 2 + 1)
            
        legend_group.setLayout(legend_layout)
        layout.addWidget(legend_group)
        
        panel.setLayout(layout)
        return panel
        
    def connect_signals(self):
        """Connette i segnali"""
        self.openings_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.openings_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        self.remove_btn.clicked.connect(self.remove_opening)
        self.edit_geometry_btn.clicked.connect(self.edit_geometry)
        self.configure_rinforzo_btn.clicked.connect(self.configure_rinforzo)
        self.remove_rinforzo_btn.clicked.connect(self.remove_rinforzo)
        
        # Canvas signals
        self.wall_canvas.opening_selected.connect(self.select_opening)
        
    def set_wall_data(self, wall_data):
        """Imposta dati del muro"""
        self.wall_data = wall_data
        if wall_data:
            self.wall_canvas.set_wall_data(
                wall_data['length'],
                wall_data['height'],
                wall_data['thickness']
            )
            self.add_btn.setEnabled(True)
        else:
            self.add_btn.setEnabled(False)
            
    def set_openings(self, openings):
        """Imposta lista aperture"""
        self.openings = openings
        self.refresh_all()
        
    def refresh_all(self):
        """Aggiorna tutta l'interfaccia"""
        self.refresh_tree()
        self.refresh_canvas()
        self.update_summary()
        
    def refresh_tree(self):
        """Aggiorna albero aperture"""
        self.openings_tree.clear()
        
        for i, opening in enumerate(self.openings):
            # Testo elementi
            name = f"A{i+1}"
            tipo = opening.get('type', 'Rettangolare')
            if opening.get('existing'):
                tipo += " (esistente)"
                
            rinforzo = "Nessuno"
            if 'rinforzo' in opening and opening['rinforzo']:
                rinforzo = opening['rinforzo']['materiale'].upper()
                
            # Crea item
            item = QTreeWidgetItem([name, tipo, rinforzo])
            
            # Colora in base al rinforzo
            if rinforzo == "ACCIAIO":
                item.setForeground(2, QBrush(QColor(0, 0, 255)))
            elif rinforzo == "CA":
                item.setForeground(2, QBrush(QColor(128, 0, 128)))
                
            self.openings_tree.addTopLevelItem(item)
            
    def refresh_canvas(self):
        """Aggiorna canvas"""
        self.wall_canvas.clear_openings()
        
        # Modifica colori aperture in base al rinforzo
        for opening in self.openings:
            opening_copy = opening.copy()
            
            # Colora diversamente se ha rinforzo
            if 'rinforzo' in opening and opening['rinforzo']:
                if opening['rinforzo']['materiale'] == 'acciaio':
                    opening_copy['color'] = QColor(0, 0, 255)
                else:  # C.A.
                    opening_copy['color'] = QColor(128, 0, 128)
                    
            self.wall_canvas.add_opening(opening_copy)
            
        # Seleziona apertura corrente
        if 0 <= self.current_opening_index < len(self.openings):
            self.wall_canvas.selected_opening = self.current_opening_index
            
        self.wall_canvas.update()
        
    def update_summary(self):
        """Aggiorna riepilogo"""
        n_aperture = len(self.openings)
        n_rinforzi = sum(1 for op in self.openings if op.get('rinforzo'))
        area_totale = sum(op['width'] * op['height'] / 10000 for op in self.openings)
        
        self.n_aperture_label.setText(str(n_aperture))
        self.n_rinforzi_label.setText(str(n_rinforzi))
        self.area_totale_label.setText(f"{area_totale:.2f} m²")
        
    def on_selection_changed(self):
        """Gestisce cambio selezione"""
        items = self.openings_tree.selectedItems()
        if items:
            index = self.openings_tree.indexOfTopLevelItem(items[0])
            self.select_opening(index)
        else:
            self.current_opening_index = -1
            self.update_buttons()
            
    def on_item_double_clicked(self, item):
        """Gestisce doppio click su apertura"""
        self.edit_geometry()
        
    def select_opening(self, index):
        """Seleziona un'apertura"""
        if 0 <= index < len(self.openings):
            self.current_opening_index = index
            
            # Aggiorna albero
            self.openings_tree.setCurrentItem(
                self.openings_tree.topLevelItem(index)
            )
            
            # Aggiorna dettagli
            opening = self.openings[index]
            self.detail_widget.update_opening(
                opening, index, self.wall_data, self.openings
            )
            
            # Aggiorna canvas
            self.wall_canvas.selected_opening = index
            self.wall_canvas.update()
            
            self.update_buttons()
            
    def update_buttons(self):
        """Aggiorna stato pulsanti"""
        has_selection = self.current_opening_index >= 0
        self.remove_btn.setEnabled(has_selection)
        self.edit_geometry_btn.setEnabled(has_selection)
        self.configure_rinforzo_btn.setEnabled(has_selection)
        
        if has_selection:
            has_rinforzo = bool(self.openings[self.current_opening_index].get('rinforzo'))
            self.remove_rinforzo_btn.setEnabled(has_rinforzo)
        else:
            self.remove_rinforzo_btn.setEnabled(False)
            
    def edit_geometry(self):
        """Modifica geometria apertura selezionata"""
        if self.current_opening_index < 0:
            return
            
        # Usa il dialog avanzato se disponibile
        if AdvancedOpeningDialog:
            DialogClass = AdvancedOpeningDialog
        else:
            # Fallback al dialog standard
            from src.gui.modules.input_module import OpeningDialog
            DialogClass = OpeningDialog
        
        opening = self.openings[self.current_opening_index]
        dialog = DialogClass(self, opening)
        
        if dialog.exec_():
            new_data = dialog.get_data()
            # Mantieni il rinforzo esistente
            if 'rinforzo' in opening:
                new_data['rinforzo'] = opening['rinforzo']
                
            self.openings[self.current_opening_index] = new_data
            self.refresh_all()
            self.data_changed.emit()
            
    def configure_rinforzo(self):
        """Configura rinforzo per apertura selezionata"""
        if self.current_opening_index < 0:
            return
            
        opening = self.openings[self.current_opening_index]
        rinforzo_data = opening.get('rinforzo')
        
        # Passa anche lo spessore del muro se disponibile
        wall_thickness = self.wall_data.get('thickness', 30) if self.wall_data else 30
        
        dialog = RinforzoCerchiaturaDialog(self, rinforzo_data, wall_thickness)
        if dialog.exec_():
            rinforzo = dialog.get_data()
            if rinforzo:  # Solo se non è "Nessun rinforzo"
                self.openings[self.current_opening_index]['rinforzo'] = rinforzo
                self.refresh_all()
                self.data_changed.emit()
                # Aggiorna dettagli immediatamente
                self.detail_widget.update_opening(
                    self.openings[self.current_opening_index], 
                    self.current_opening_index, 
                    self.wall_data, 
                    self.openings
                )
            
    def remove_rinforzo(self):
        """Rimuove rinforzo da apertura selezionata"""
        if self.current_opening_index < 0:
            return
            
        reply = QMessageBox.question(
            self, "Conferma",
            "Rimuovere il rinforzo dall'apertura selezionata?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if 'rinforzo' in self.openings[self.current_opening_index]:
                del self.openings[self.current_opening_index]['rinforzo']
                self.refresh_all()
                self.data_changed.emit()
                
    def remove_opening(self):
        """Rimuove apertura selezionata"""
        if self.current_opening_index < 0:
            return
            
        reply = QMessageBox.question(
            self, "Conferma",
            "Rimuovere l'apertura selezionata?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.openings.pop(self.current_opening_index)
            self.current_opening_index = -1
            self.refresh_all()
            self.data_changed.emit()
            
    def collect_data(self):
        """Raccoglie dati del modulo"""
        return {
            'openings': self.openings
        }
        
    def load_data(self, data):
        """Carica dati nel modulo"""
        self.openings = data.get('openings', [])
        self.refresh_all()
        
    def reset(self):
        """Reset del modulo"""
        self.openings = []
        self.current_opening_index = -1
        self.wall_canvas.clear_openings()
        self.refresh_all()