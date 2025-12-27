"""
UI Enhancements - Componenti avanzati per l'interfaccia grafica
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class WorkflowIndicator(QWidget):
    """Indicatore visivo del progresso nel workflow"""

    step_clicked = pyqtSignal(int)  # Emesso quando si clicca su uno step

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        self.steps = [
            ("Struttura", "Definisci geometria muro e materiali"),
            ("Aperture", "Aggiungi aperture e rinforzi"),
            ("Calcolo", "Esegui verifica NTC 2018"),
            ("Relazione", "Genera documentazione")
        ]
        self.step_widgets = []
        self.step_states = [False, False, False, False]
        self.current_step = 0

        for i, (name, tooltip) in enumerate(self.steps):
            # Container per step
            step_container = QWidget()
            step_layout = QHBoxLayout()
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(2)

            # Numero step
            num_label = QLabel(f"{i+1}")
            num_label.setFixedSize(24, 24)
            num_label.setAlignment(Qt.AlignCenter)
            num_label.setObjectName(f"step_num_{i}")

            # Nome step
            name_label = QPushButton(name)
            name_label.setFlat(True)
            name_label.setCursor(Qt.PointingHandCursor)
            name_label.setToolTip(tooltip)
            name_label.setObjectName(f"step_name_{i}")
            name_label.clicked.connect(lambda checked, idx=i: self.step_clicked.emit(idx))

            step_layout.addWidget(num_label)
            step_layout.addWidget(name_label)
            step_container.setLayout(step_layout)

            self.step_widgets.append({
                'container': step_container,
                'num': num_label,
                'name': name_label
            })

            layout.addWidget(step_container)

            # Freccia tra step (eccetto ultimo)
            if i < len(self.steps) - 1:
                arrow = QLabel("  ›  ")
                arrow.setObjectName("step_arrow")
                layout.addWidget(arrow)

        layout.addStretch()
        self.setLayout(layout)
        self.update_styles()

    def set_step_complete(self, step_index, complete=True):
        """Segna uno step come completato"""
        if 0 <= step_index < len(self.step_states):
            self.step_states[step_index] = complete
            self.update_styles()

    def set_current_step(self, step_index):
        """Imposta lo step corrente"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.update_styles()

    def update_styles(self):
        """Aggiorna gli stili di tutti gli step"""
        for i, widgets in enumerate(self.step_widgets):
            num_label = widgets['num']
            name_label = widgets['name']

            if self.step_states[i]:
                # Completato
                num_label.setStyleSheet("""
                    QLabel {
                        background: #27ae60;
                        color: white;
                        border-radius: 12px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
                name_label.setStyleSheet("""
                    QPushButton {
                        color: #27ae60;
                        font-weight: bold;
                        border: none;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        color: #1e8449;
                    }
                """)
            elif i == self.current_step:
                # Corrente
                num_label.setStyleSheet("""
                    QLabel {
                        background: #3498db;
                        color: white;
                        border-radius: 12px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
                name_label.setStyleSheet("""
                    QPushButton {
                        color: #3498db;
                        font-weight: bold;
                        border: none;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        color: #2980b9;
                    }
                """)
            else:
                # Non ancora raggiunto
                num_label.setStyleSheet("""
                    QLabel {
                        background: #bdc3c7;
                        color: white;
                        border-radius: 12px;
                        font-size: 11px;
                    }
                """)
                name_label.setStyleSheet("""
                    QPushButton {
                        color: #7f8c8d;
                        border: none;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        color: #566573;
                    }
                """)


class ValidatedSpinBox(QSpinBox):
    """SpinBox con validazione visiva in tempo reale"""

    validation_changed = pyqtSignal(bool, str)  # (is_valid, message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.warning_min = None
        self.warning_max = None
        self.error_min = None
        self.error_max = None
        self.help_text = ""
        self.valueChanged.connect(self._validate)

    def set_validation_range(self, warning_min=None, warning_max=None,
                            error_min=None, error_max=None):
        """Imposta i range di validazione"""
        self.warning_min = warning_min
        self.warning_max = warning_max
        self.error_min = error_min
        self.error_max = error_max
        self._validate()

    def set_help_text(self, text):
        """Imposta il testo di aiuto"""
        self.help_text = text
        self._update_tooltip()

    def _validate(self):
        """Esegue la validazione e aggiorna lo stile"""
        value = self.value()
        message = ""
        is_valid = True
        style = ""

        # Controlla errori
        if self.error_min is not None and value < self.error_min:
            style = "border: 2px solid #e74c3c; background: #fdf2f2;"
            message = f"Valore troppo basso (minimo: {self.error_min})"
            is_valid = False
        elif self.error_max is not None and value > self.error_max:
            style = "border: 2px solid #e74c3c; background: #fdf2f2;"
            message = f"Valore troppo alto (massimo: {self.error_max})"
            is_valid = False
        # Controlla warning
        elif self.warning_min is not None and value < self.warning_min:
            style = "border: 2px solid #f39c12; background: #fef9e7;"
            message = f"Valore basso (consigliato >= {self.warning_min})"
        elif self.warning_max is not None and value > self.warning_max:
            style = "border: 2px solid #f39c12; background: #fef9e7;"
            message = f"Valore alto (consigliato <= {self.warning_max})"
        else:
            style = ""

        self.setStyleSheet(style)
        self._update_tooltip(message)
        self.validation_changed.emit(is_valid, message)

    def _update_tooltip(self, warning_msg=""):
        """Aggiorna il tooltip"""
        tooltip_parts = []
        if self.help_text:
            tooltip_parts.append(self.help_text)
        if warning_msg:
            tooltip_parts.append(f"\n⚠️ {warning_msg}")
        self.setToolTip("\n".join(tooltip_parts))


class ValidatedDoubleSpinBox(QDoubleSpinBox):
    """DoubleSpinBox con validazione visiva in tempo reale"""

    validation_changed = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.warning_min = None
        self.warning_max = None
        self.error_min = None
        self.error_max = None
        self.help_text = ""
        self.valueChanged.connect(self._validate)

    def set_validation_range(self, warning_min=None, warning_max=None,
                            error_min=None, error_max=None):
        self.warning_min = warning_min
        self.warning_max = warning_max
        self.error_min = error_min
        self.error_max = error_max
        self._validate()

    def set_help_text(self, text):
        self.help_text = text
        self._update_tooltip()

    def _validate(self):
        value = self.value()
        message = ""
        is_valid = True
        style = ""

        if self.error_min is not None and value < self.error_min:
            style = "border: 2px solid #e74c3c; background: #fdf2f2;"
            message = f"Valore troppo basso (minimo: {self.error_min})"
            is_valid = False
        elif self.error_max is not None and value > self.error_max:
            style = "border: 2px solid #e74c3c; background: #fdf2f2;"
            message = f"Valore troppo alto (massimo: {self.error_max})"
            is_valid = False
        elif self.warning_min is not None and value < self.warning_min:
            style = "border: 2px solid #f39c12; background: #fef9e7;"
            message = f"Valore basso (consigliato >= {self.warning_min})"
        elif self.warning_max is not None and value > self.warning_max:
            style = "border: 2px solid #f39c12; background: #fef9e7;"
            message = f"Valore alto (consigliato <= {self.warning_max})"

        self.setStyleSheet(style)
        self._update_tooltip(message)
        self.validation_changed.emit(is_valid, message)

    def _update_tooltip(self, warning_msg=""):
        tooltip_parts = []
        if self.help_text:
            tooltip_parts.append(self.help_text)
        if warning_msg:
            tooltip_parts.append(f"\n⚠️ {warning_msg}")
        self.setToolTip("\n".join(tooltip_parts))


class HelpLabel(QWidget):
    """Label con icona help che mostra tooltip ricco"""

    def __init__(self, text, help_text="", parent=None):
        super().__init__(parent)
        self.help_text = help_text
        self.setup_ui(text)

    def setup_ui(self, text):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label principale
        self.label = QLabel(text)
        layout.addWidget(self.label)

        # Pulsante help
        if self.help_text:
            self.help_btn = QPushButton("?")
            self.help_btn.setFixedSize(16, 16)
            self.help_btn.setCursor(Qt.WhatsThisCursor)
            self.help_btn.setToolTip(self.help_text)
            self.help_btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
            layout.addWidget(self.help_btn)

        layout.addStretch()
        self.setLayout(layout)

    def set_help_text(self, text):
        """Aggiorna il testo di aiuto"""
        self.help_text = text
        if hasattr(self, 'help_btn'):
            self.help_btn.setToolTip(text)


class ToastNotification(QFrame):
    """Notifica toast non bloccante"""

    closed = pyqtSignal()

    def __init__(self, message, type_="info", duration=3000, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.opacity = 1.0
        self.setup_ui(message, type_)

    def setup_ui(self, message, type_):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        colors = {
            "success": ("#27ae60", "#d4efdf"),
            "error": ("#e74c3c", "#fadbd8"),
            "warning": ("#f39c12", "#fef9e7"),
            "info": ("#3498db", "#d6eaf8")
        }
        icons = {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ"
        }

        main_color, bg_color = colors.get(type_, colors['info'])
        icon_text = icons.get(type_, "ℹ")

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: 2px solid {main_color};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)

        # Icona
        icon = QLabel(icon_text)
        icon.setStyleSheet(f"color: {main_color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(icon)

        # Messaggio
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: #2c3e50; font-size: 13px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        # Pulsante chiudi
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {main_color};
                font-size: 16px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                color: #2c3e50;
            }}
        """)
        close_btn.clicked.connect(self.close_toast)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.adjustSize()

    def show_toast(self, parent_widget=None):
        """Mostra la notifica"""
        if parent_widget:
            # Posiziona in alto a destra del parent
            parent_rect = parent_widget.geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 60
            self.move(x, y)

        self.show()

        # Timer per auto-chiusura
        if self.duration > 0:
            QTimer.singleShot(self.duration, self.fade_out)

    def fade_out(self):
        """Effetto fade out"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close_toast)
        self.animation.start()

    def close_toast(self):
        """Chiude la notifica"""
        self.closed.emit()
        self.close()
        self.deleteLater()


class ToastManager:
    """Gestisce le notifiche toast per evitare sovrapposizioni"""

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.active_toasts = []
        self.toast_spacing = 10

    def show_toast(self, message, type_="info", duration=3000):
        """Mostra una nuova notifica"""
        toast = ToastNotification(message, type_, duration, self.parent)
        toast.closed.connect(lambda: self._remove_toast(toast))

        # Calcola posizione
        self._position_toast(toast)

        self.active_toasts.append(toast)
        toast.show_toast(self.parent)

        return toast

    def _position_toast(self, toast):
        """Posiziona la notifica evitando sovrapposizioni"""
        if self.parent:
            parent_rect = self.parent.geometry()
            x = parent_rect.width() - toast.width() - 20
            y = 60

            # Offset per toast esistenti
            for existing in self.active_toasts:
                if existing.isVisible():
                    y += existing.height() + self.toast_spacing

            toast.move(self.parent.mapToGlobal(QPoint(x, y)))

    def _remove_toast(self, toast):
        """Rimuove un toast dalla lista"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)

    def success(self, message, duration=3000):
        return self.show_toast(message, "success", duration)

    def error(self, message, duration=5000):
        return self.show_toast(message, "error", duration)

    def warning(self, message, duration=4000):
        return self.show_toast(message, "warning", duration)

    def info(self, message, duration=3000):
        return self.show_toast(message, "info", duration)


class SummaryDock(QDockWidget):
    """Dock widget con riepilogo progetto sempre visibile"""

    def __init__(self, parent=None):
        super().__init__("Riepilogo Progetto", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setup_ui()

    def setup_ui(self):
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Stile generale
        content.setStyleSheet("""
            QLabel {
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)

        # Sezione Muro
        wall_group = QGroupBox("Geometria Muro")
        wall_layout = QVBoxLayout()
        self.wall_dims_label = QLabel("Dimensioni: -")
        self.wall_area_label = QLabel("Area: -")
        wall_layout.addWidget(self.wall_dims_label)
        wall_layout.addWidget(self.wall_area_label)
        wall_group.setLayout(wall_layout)
        layout.addWidget(wall_group)

        # Sezione Muratura
        masonry_group = QGroupBox("Muratura")
        masonry_layout = QVBoxLayout()
        self.masonry_type_label = QLabel("Tipo: -")
        self.masonry_fc_label = QLabel("FC: -")
        masonry_layout.addWidget(self.masonry_type_label)
        masonry_layout.addWidget(self.masonry_fc_label)
        masonry_group.setLayout(masonry_layout)
        layout.addWidget(masonry_group)

        # Sezione Aperture
        openings_group = QGroupBox("Aperture")
        openings_layout = QVBoxLayout()
        self.openings_count_label = QLabel("Numero: 0")
        self.openings_area_label = QLabel("Area totale: -")
        self.openings_ratio_label = QLabel("Rapporto: -")
        openings_layout.addWidget(self.openings_count_label)
        openings_layout.addWidget(self.openings_area_label)
        openings_layout.addWidget(self.openings_ratio_label)
        openings_group.setLayout(openings_layout)
        layout.addWidget(openings_group)

        # Sezione Verifica
        self.verification_group = QGroupBox("Verifica NTC 2018")
        verif_layout = QVBoxLayout()
        self.verification_status = QLabel("Non eseguita")
        self.verification_status.setAlignment(Qt.AlignCenter)
        self.verification_status.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
            background: #ecf0f1;
            color: #7f8c8d;
        """)
        self.stiffness_label = QLabel("ΔK: -")
        self.resistance_label = QLabel("ΔV: -")
        verif_layout.addWidget(self.verification_status)
        verif_layout.addWidget(self.stiffness_label)
        verif_layout.addWidget(self.resistance_label)
        self.verification_group.setLayout(verif_layout)
        layout.addWidget(self.verification_group)

        layout.addStretch()

        # Pulsante aggiorna
        refresh_btn = QPushButton("Aggiorna")
        refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_btn.clicked.connect(self.request_update)
        layout.addWidget(refresh_btn)

        content.setLayout(layout)
        self.setWidget(content)

    def request_update(self):
        """Richiede aggiornamento dati"""
        parent = self.parent()
        if parent and hasattr(parent, 'update_summary_dock'):
            parent.update_summary_dock()

    def update_wall_data(self, wall_data):
        """Aggiorna dati muro"""
        if wall_data:
            L = wall_data.get('length', 0)
            H = wall_data.get('height', 0)
            s = wall_data.get('thickness', 0)
            self.wall_dims_label.setText(f"Dimensioni: {L}×{H}×{s} cm")
            area = L * H / 10000
            self.wall_area_label.setText(f"Area: {area:.2f} m²")

    def update_masonry_data(self, masonry_data):
        """Aggiorna dati muratura"""
        if masonry_data:
            type_name = masonry_data.get('type', '-')
            # Tronca nome lungo
            if len(type_name) > 30:
                type_name = type_name[:27] + "..."
            self.masonry_type_label.setText(f"Tipo: {type_name}")

            kl = masonry_data.get('knowledge_level', '-')
            self.masonry_fc_label.setText(f"Livello: {kl}")

    def update_openings_data(self, openings, wall_area):
        """Aggiorna dati aperture"""
        n = len(openings) if openings else 0
        self.openings_count_label.setText(f"Numero: {n}")

        if openings:
            total_area = sum(o.get('width', 0) * o.get('height', 0) / 10000
                           for o in openings)
            self.openings_area_label.setText(f"Area totale: {total_area:.2f} m²")

            if wall_area > 0:
                ratio = (total_area / wall_area) * 100
                self.openings_ratio_label.setText(f"Rapporto: {ratio:.1f}%")
        else:
            self.openings_area_label.setText("Area totale: 0 m²")
            self.openings_ratio_label.setText("Rapporto: 0%")

    def update_verification(self, results):
        """Aggiorna stato verifica"""
        if results and 'verification' in results:
            verif = results['verification']

            if verif.get('is_local'):
                self.verification_status.setText("✓ INTERVENTO LOCALE")
                self.verification_status.setStyleSheet("""
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    background: #27ae60;
                    color: white;
                """)
            else:
                self.verification_status.setText("✗ NON LOCALE")
                self.verification_status.setStyleSheet("""
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    background: #e74c3c;
                    color: white;
                """)

            stiff_var = verif.get('stiffness_variation', 0)
            stiff_ok = verif.get('stiffness_ok', False)
            stiff_color = "green" if stiff_ok else "red"
            self.stiffness_label.setText(
                f'<span style="color: {stiff_color};">ΔK: {stiff_var:.1f}%</span>'
            )

            res_var = verif.get('resistance_variation', 0)
            res_ok = verif.get('resistance_ok', False)
            res_color = "green" if res_ok else "red"
            self.resistance_label.setText(
                f'<span style="color: {res_color};">ΔV: {res_var:.1f}%</span>'
            )
        else:
            self.verification_status.setText("Non eseguita")
            self.verification_status.setStyleSheet("""
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                background: #ecf0f1;
                color: #7f8c8d;
            """)
            self.stiffness_label.setText("ΔK: -")
            self.resistance_label.setText("ΔV: -")


class CollapsibleGroupBox(QGroupBox):
    """GroupBox collassabile"""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.is_collapsed = False
        self.toggle_btn = None
        self.content_widget = None
        self.original_title = title
        self.setup_collapsible()

    def setup_collapsible(self):
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.toggle_content)

    def toggle_content(self, checked):
        self.is_collapsed = not checked

        # Trova tutti i widget figli e nascondili/mostrali
        for child in self.findChildren(QWidget):
            if child != self:
                child.setVisible(checked)

        if checked:
            self.setTitle(self.original_title)
        else:
            self.setTitle(f"{self.original_title} [+]")


class StatusIndicator(QLabel):
    """Indicatore di stato con colori"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.set_status("neutral")

    def set_status(self, status):
        """Imposta lo stato: 'ok', 'warning', 'error', 'neutral'"""
        colors = {
            'ok': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'neutral': '#bdc3c7'
        }
        color = colors.get(status, colors['neutral'])
        self.setStyleSheet(f"""
            background: {color};
            border-radius: 6px;
        """)


class ClickableLabel(QLabel):
    """Label cliccabile"""

    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AnimatedButton(QPushButton):
    """Pulsante con effetti animati"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation = None
        self._setup_animation()

    def _setup_animation(self):
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(1.0)

    def flash(self, color="#27ae60"):
        """Effetto flash quando si clicca"""
        original_style = self.styleSheet()
        self.setStyleSheet(f"background-color: {color}; color: white;")
        QTimer.singleShot(150, lambda: self.setStyleSheet(original_style))


class ProgressButton(QPushButton):
    """Pulsante con indicatore di progresso integrato"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.progress = 0
        self.is_loading = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_loading)
        self.dots = 0

    def start_loading(self, text=None):
        """Avvia animazione di caricamento"""
        self.is_loading = True
        self.original_text = self.text() if text is None else text
        self.setEnabled(False)
        self.timer.start(300)

    def stop_loading(self, success=True):
        """Ferma animazione"""
        self.timer.stop()
        self.is_loading = False
        self.setEnabled(True)

        if success:
            self.setText("✓ " + self.original_text)
            QTimer.singleShot(1500, lambda: self.setText(self.original_text))
        else:
            self.setText("✗ " + self.original_text)
            QTimer.singleShot(1500, lambda: self.setText(self.original_text))

    def _update_loading(self):
        """Aggiorna animazione dots"""
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.setText(f"{self.original_text}{dots_text}")


# Utility functions
def create_separator():
    """Crea una linea separatrice"""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("background: #bdc3c7;")
    return line


def create_spacer(height=10):
    """Crea uno spacer verticale"""
    spacer = QWidget()
    spacer.setFixedHeight(height)
    return spacer
