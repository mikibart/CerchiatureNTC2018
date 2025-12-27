"""
Modern Style - Tema moderno per l'interfaccia grafica
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

# Palette colori
COLORS = {
    # Primari
    'primary': '#3498db',
    'primary_dark': '#2980b9',
    'primary_light': '#5dade2',

    # Accento
    'accent': '#e74c3c',
    'accent_dark': '#c0392b',

    # Successo/Errore/Warning
    'success': '#27ae60',
    'success_light': '#d4efdf',
    'error': '#e74c3c',
    'error_light': '#fadbd8',
    'warning': '#f39c12',
    'warning_light': '#fef9e7',
    'info': '#3498db',
    'info_light': '#d6eaf8',

    # Neutri
    'background': '#f5f6fa',
    'surface': '#ffffff',
    'border': '#dcdde1',
    'border_light': '#ecf0f1',

    # Testo
    'text_primary': '#2c3e50',
    'text_secondary': '#7f8c8d',
    'text_disabled': '#bdc3c7',
    'text_on_primary': '#ffffff',
}

# Stylesheet principale dell'applicazione
MODERN_STYLESHEET = f"""
/* ========== FINESTRA PRINCIPALE ========== */
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    color: {COLORS['text_primary']};
}}

/* ========== MENU BAR ========== */
QMenuBar {{
    background-color: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['text_on_primary']};
}}

QMenu {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

/* ========== TOOLBAR ========== */
QToolBar {{
    background-color: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px;
    spacing: 4px;
}}

QToolBar::separator {{
    width: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    margin: 2px;
}}

QToolButton:hover {{
    background-color: {COLORS['border_light']};
}}

QToolButton:pressed {{
    background-color: {COLORS['border']};
}}

/* ========== TAB WIDGET ========== */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 0 0 8px 8px;
    background: {COLORS['surface']};
    top: -1px;
}}

QTabBar::tab {{
    background: {COLORS['border_light']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    margin-right: 2px;
    color: {COLORS['text_secondary']};
}}

QTabBar::tab:selected {{
    background: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background: {COLORS['primary_light']};
    color: {COLORS['text_on_primary']};
}}

/* ========== PULSANTI ========== */
QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['text_disabled']};
    color: {COLORS['surface']};
}}

/* Pulsante secondario */
QPushButton[secondary="true"] {{
    background-color: {COLORS['surface']};
    color: {COLORS['primary']};
    border: 2px solid {COLORS['primary']};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
}}

/* Pulsante danger */
QPushButton[danger="true"] {{
    background-color: {COLORS['error']};
}}

QPushButton[danger="true"]:hover {{
    background-color: {COLORS['accent_dark']};
}}

/* Pulsante success */
QPushButton[success="true"] {{
    background-color: {COLORS['success']};
}}

/* ========== GROUP BOX ========== */
QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: {COLORS['primary']};
    background-color: {COLORS['surface']};
}}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['surface']};
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['primary']};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS['border_light']};
    color: {COLORS['text_disabled']};
}}

/* ========== SPINBOX ========== */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['surface']};
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 4px;
    background: {COLORS['border_light']};
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border-left: 1px solid {COLORS['border']};
    border-bottom-right-radius: 4px;
    background: {COLORS['border_light']};
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {COLORS['primary_light']};
}}

/* ========== COMBOBOX ========== */
QComboBox {{
    background-color: {COLORS['surface']};
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background: {COLORS['border_light']};
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: {COLORS['primary']};
    selection-color: {COLORS['text_on_primary']};
}}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {{
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 20px;
    height: 20px;
}}

QCheckBox::indicator {{
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background: {COLORS['surface']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary']};
}}

QCheckBox::indicator:checked {{
    background: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
}}

QRadioButton::indicator {{
    border: 2px solid {COLORS['border']};
    border-radius: 10px;
    background: {COLORS['surface']};
}}

QRadioButton::indicator:checked {{
    background: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

/* ========== SCROLL AREA ========== */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS['border_light']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['text_disabled']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS['border_light']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['text_disabled']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['text_secondary']};
}}

/* ========== LIST & TABLE ========== */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    alternate-background-color: {COLORS['border_light']};
}}

QListWidget::item, QTreeWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
}}

QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{
    background-color: {COLORS['info_light']};
}}

QHeaderView::section {{
    background-color: {COLORS['border_light']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px;
    font-weight: bold;
}}

/* ========== SPLITTER ========== */
QSplitter::handle {{
    background: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 4px;
}}

QSplitter::handle:vertical {{
    height: 4px;
}}

QSplitter::handle:hover {{
    background: {COLORS['primary']};
}}

/* ========== STATUS BAR ========== */
QStatusBar {{
    background-color: {COLORS['surface']};
    border-top: 1px solid {COLORS['border']};
    padding: 4px;
}}

QStatusBar::item {{
    border: none;
}}

/* ========== DOCK WIDGET ========== */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
    padding: 8px;
    font-weight: bold;
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
}}

/* ========== TOOLTIP ========== */
QToolTip {{
    background-color: {COLORS['text_primary']};
    color: {COLORS['text_on_primary']};
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 11px;
}}

/* ========== PROGRESS BAR ========== */
QProgressBar {{
    background-color: {COLORS['border_light']};
    border: none;
    border-radius: 8px;
    height: 16px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 8px;
}}

/* ========== SLIDER ========== */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {COLORS['border']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['primary']};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS['primary_dark']};
}}

/* ========== DATE EDIT ========== */
QDateEdit {{
    background-color: {COLORS['surface']};
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
}}

QDateEdit:focus {{
    border-color: {COLORS['primary']};
}}

QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}}

QCalendarWidget {{
    background-color: {COLORS['surface']};
}}

QCalendarWidget QToolButton {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['surface']};
    border-radius: 4px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['text_on_primary']};
}}

/* ========== LABEL SPECIALI ========== */
QLabel[heading="true"] {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel[subheading="true"] {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

QLabel[success="true"] {{
    color: {COLORS['success']};
    font-weight: bold;
}}

QLabel[error="true"] {{
    color: {COLORS['error']};
    font-weight: bold;
}}

QLabel[warning="true"] {{
    color: {COLORS['warning']};
    font-weight: bold;
}}

/* ========== DIALOG ========== */
QDialog {{
    background-color: {COLORS['background']};
}}

QDialogButtonBox {{
    button-layout: 2;
}}

/* ========== MESSAGE BOX ========== */
QMessageBox {{
    background-color: {COLORS['surface']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}
"""

# Palette colori tema scuro
DARK_COLORS = {
    # Primari
    'primary': '#5dade2',
    'primary_dark': '#3498db',
    'primary_light': '#85c1e9',

    # Accento
    'accent': '#e74c3c',
    'accent_dark': '#c0392b',

    # Successo/Errore/Warning
    'success': '#2ecc71',
    'success_light': '#1e3d2f',
    'error': '#e74c3c',
    'error_light': '#3d1e1e',
    'warning': '#f39c12',
    'warning_light': '#3d3a1e',
    'info': '#5dade2',
    'info_light': '#1e2d3d',

    # Neutri
    'background': '#1a1a2e',
    'surface': '#16213e',
    'border': '#0f3460',
    'border_light': '#1f4068',

    # Testo
    'text_primary': '#eaecee',
    'text_secondary': '#aab7c4',
    'text_disabled': '#5d6d7e',
    'text_on_primary': '#ffffff',
}

# Stylesheet per tema scuro
DARK_STYLESHEET = f"""
/* ========== DARK THEME ========== */
QMainWindow {{
    background-color: {DARK_COLORS['background']};
}}

QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    color: {DARK_COLORS['text_primary']};
}}

/* ========== MENU BAR ========== */
QMenuBar {{
    background-color: {DARK_COLORS['surface']};
    border-bottom: 1px solid {DARK_COLORS['border']};
    padding: 2px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
    color: {DARK_COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
}}

QMenu {{
    background-color: {DARK_COLORS['surface']};
    border: 1px solid {DARK_COLORS['border']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
    color: {DARK_COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
}}

QMenu::separator {{
    height: 1px;
    background: {DARK_COLORS['border']};
    margin: 4px 8px;
}}

/* ========== TOOLBAR ========== */
QToolBar {{
    background-color: {DARK_COLORS['surface']};
    border-bottom: 1px solid {DARK_COLORS['border']};
    padding: 4px;
    spacing: 4px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    color: {DARK_COLORS['text_primary']};
}}

QToolButton:hover {{
    background-color: {DARK_COLORS['border_light']};
}}

/* ========== TAB WIDGET ========== */
QTabWidget::pane {{
    border: 1px solid {DARK_COLORS['border']};
    border-radius: 0 0 8px 8px;
    background: {DARK_COLORS['surface']};
}}

QTabBar::tab {{
    background: {DARK_COLORS['border']};
    border: 1px solid {DARK_COLORS['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    margin-right: 2px;
    color: {DARK_COLORS['text_secondary']};
}}

QTabBar::tab:selected {{
    background: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background: {DARK_COLORS['primary_dark']};
    color: {DARK_COLORS['text_on_primary']};
}}

/* ========== PULSANTI ========== */
QPushButton {{
    background-color: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {DARK_COLORS['primary_light']};
}}

QPushButton:disabled {{
    background-color: {DARK_COLORS['text_disabled']};
}}

/* ========== GROUP BOX ========== */
QGroupBox {{
    background-color: {DARK_COLORS['surface']};
    border: 1px solid {DARK_COLORS['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
    font-weight: bold;
    color: {DARK_COLORS['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: {DARK_COLORS['primary']};
    background-color: {DARK_COLORS['surface']};
}}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {DARK_COLORS['background']};
    border: 2px solid {DARK_COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {DARK_COLORS['text_primary']};
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {DARK_COLORS['primary']};
}}

/* ========== SPINBOX ========== */
QSpinBox, QDoubleSpinBox {{
    background-color: {DARK_COLORS['background']};
    border: 2px solid {DARK_COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {DARK_COLORS['text_primary']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {DARK_COLORS['primary']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {DARK_COLORS['border']};
}}

/* ========== COMBOBOX ========== */
QComboBox {{
    background-color: {DARK_COLORS['background']};
    border: 2px solid {DARK_COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {DARK_COLORS['text_primary']};
}}

QComboBox:focus {{
    border-color: {DARK_COLORS['primary']};
}}

QComboBox::drop-down {{
    background: {DARK_COLORS['border']};
}}

QComboBox QAbstractItemView {{
    background-color: {DARK_COLORS['surface']};
    border: 1px solid {DARK_COLORS['border']};
    color: {DARK_COLORS['text_primary']};
    selection-background-color: {DARK_COLORS['primary']};
}}

/* ========== SCROLL AREA ========== */
QScrollBar:vertical {{
    background: {DARK_COLORS['background']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background: {DARK_COLORS['border']};
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {DARK_COLORS['primary']};
}}

/* ========== LIST & TABLE ========== */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {DARK_COLORS['surface']};
    border: 1px solid {DARK_COLORS['border']};
    border-radius: 6px;
    color: {DARK_COLORS['text_primary']};
    alternate-background-color: {DARK_COLORS['background']};
}}

QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
}}

QHeaderView::section {{
    background-color: {DARK_COLORS['border']};
    color: {DARK_COLORS['text_primary']};
    border: none;
    padding: 8px;
    font-weight: bold;
}}

/* ========== STATUS BAR ========== */
QStatusBar {{
    background-color: {DARK_COLORS['surface']};
    border-top: 1px solid {DARK_COLORS['border']};
    color: {DARK_COLORS['text_secondary']};
}}

/* ========== DOCK WIDGET ========== */
QDockWidget::title {{
    background: {DARK_COLORS['primary']};
    color: {DARK_COLORS['text_on_primary']};
    padding: 8px;
    font-weight: bold;
}}

/* ========== TOOLTIP ========== */
QToolTip {{
    background-color: {DARK_COLORS['surface']};
    color: {DARK_COLORS['text_primary']};
    border: 1px solid {DARK_COLORS['border']};
    border-radius: 4px;
    padding: 8px 12px;
}}

/* ========== PROGRESS BAR ========== */
QProgressBar {{
    background-color: {DARK_COLORS['background']};
    border: none;
    border-radius: 8px;
    height: 16px;
    color: {DARK_COLORS['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {DARK_COLORS['primary']};
    border-radius: 8px;
}}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {{
    color: {DARK_COLORS['text_primary']};
}}

QCheckBox::indicator {{
    border: 2px solid {DARK_COLORS['border']};
    border-radius: 4px;
    background: {DARK_COLORS['background']};
}}

QCheckBox::indicator:hover {{
    border-color: {DARK_COLORS['primary']};
}}

QCheckBox::indicator:checked {{
    background: {DARK_COLORS['primary']};
    border-color: {DARK_COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
}}

/* ========== LABELS ========== */
QLabel {{
    color: {DARK_COLORS['text_primary']};
}}

QLabel[success="true"] {{
    color: {DARK_COLORS['success']};
}}

QLabel[error="true"] {{
    color: {DARK_COLORS['error']};
}}
"""

# Variabile per tema corrente
_current_theme = 'light'


def apply_modern_style(app, theme='light'):
    """Applica lo stile moderno all'applicazione

    Args:
        app: QApplication
        theme: 'light' o 'dark'
    """
    global _current_theme
    _current_theme = theme

    if theme == 'dark':
        app.setStyleSheet(DARK_STYLESHEET)
    else:
        app.setStyleSheet(MODERN_STYLESHEET)

    # Imposta font di sistema se disponibile
    try:
        font = app.font()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        app.setFont(font)
    except:
        pass


def toggle_theme(app):
    """Alterna tra tema chiaro e scuro"""
    global _current_theme
    new_theme = 'dark' if _current_theme == 'light' else 'light'
    apply_modern_style(app, new_theme)
    return new_theme


def get_current_theme():
    """Restituisce il tema corrente"""
    return _current_theme


def get_color(color_name):
    """Ottiene un colore dalla palette corrente"""
    if _current_theme == 'dark':
        return DARK_COLORS.get(color_name, DARK_COLORS['text_primary'])
    return COLORS.get(color_name, COLORS['text_primary'])


def create_colored_icon(icon_type, color=None):
    """Crea un'icona colorata (placeholder per future implementazioni)"""
    pass
