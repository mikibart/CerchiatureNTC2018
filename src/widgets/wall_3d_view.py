"""
Wall 3D View - Visualizzazione 3D isometrica del muro
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta

Vista 3D semplificata usando proiezione isometrica con QPainter
"""

import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Wall3DView(QWidget):
    """Widget per visualizzazione 3D isometrica del muro"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        # Dati muro
        self.wall_data = None
        self.openings = []

        # Parametri vista
        self.rotation_x = 30  # Rotazione asse X (gradi)
        self.rotation_z = 45  # Rotazione asse Z (gradi)
        self.scale = 0.8
        self.offset = QPointF(0, 0)

        # Interazione mouse
        self.last_mouse_pos = None
        self.is_rotating = False

        # Colori
        self.colors = {
            'wall_front': QColor(220, 180, 140),
            'wall_side': QColor(180, 140, 100),
            'wall_top': QColor(240, 200, 160),
            'opening': QColor(135, 206, 235),
            'opening_frame': QColor(80, 80, 80),
            'reinforcement': QColor(70, 130, 180),
            'grid': QColor(200, 200, 200),
            'background': QColor(245, 245, 250),
        }

    def set_wall_data(self, length: float, height: float, thickness: float):
        """Imposta dimensioni muro"""
        self.wall_data = {
            'length': length,
            'height': height,
            'thickness': thickness
        }
        self.calculate_scale()
        self.update()

    def set_openings(self, openings: list):
        """Imposta lista aperture"""
        self.openings = openings
        self.update()

    def add_opening(self, opening: dict):
        """Aggiunge un'apertura"""
        self.openings.append(opening.copy())
        self.update()

    def clear_openings(self):
        """Rimuove tutte le aperture"""
        self.openings.clear()
        self.update()

    def calculate_scale(self):
        """Calcola scala ottimale"""
        if not self.wall_data:
            return

        # Dimensione massima del muro in proiezione
        max_dim = max(
            self.wall_data['length'],
            self.wall_data['height'],
            self.wall_data['thickness']
        )

        available = min(self.width(), self.height()) - 100
        self.scale = available / max_dim * 0.4

    def project_3d_to_2d(self, x: float, y: float, z: float) -> QPointF:
        """
        Proietta punto 3D in coordinate 2D (proiezione isometrica)

        Args:
            x: Coordinata X (lunghezza muro)
            y: Coordinata Y (spessore muro)
            z: Coordinata Z (altezza muro)

        Returns:
            QPointF con coordinate schermo
        """
        # Angoli in radianti
        rx = math.radians(self.rotation_x)
        rz = math.radians(self.rotation_z)

        # Rotazione attorno all'asse Z
        x1 = x * math.cos(rz) - y * math.sin(rz)
        y1 = x * math.sin(rz) + y * math.cos(rz)
        z1 = z

        # Rotazione attorno all'asse X (tilt)
        y2 = y1 * math.cos(rx) - z1 * math.sin(rx)
        z2 = y1 * math.sin(rx) + z1 * math.cos(rx)

        # Proiezione ortogonale (semplificata)
        screen_x = x1 * self.scale + self.width() / 2 + self.offset.x()
        screen_y = self.height() / 2 - z2 * self.scale + self.offset.y()

        return QPointF(screen_x, screen_y)

    def paintEvent(self, event):
        """Disegna la vista 3D"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Sfondo
        painter.fillRect(self.rect(), self.colors['background'])

        if not self.wall_data:
            # Messaggio se nessun dato
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Inserire dimensioni muro")
            return

        # Disegna griglia di riferimento
        self.draw_grid(painter)

        # Disegna muro (ordine: facce più lontane prima)
        self.draw_wall(painter)

        # Disegna aperture
        for opening in self.openings:
            self.draw_opening_3d(painter, opening)

        # Disegna assi di riferimento
        self.draw_axes(painter)

        # Info vista
        self.draw_view_info(painter)

    def draw_grid(self, painter):
        """Disegna griglia di base"""
        painter.setPen(QPen(self.colors['grid'], 1, Qt.DotLine))

        L = self.wall_data['length']
        s = self.wall_data['thickness']
        step = 50  # cm

        # Griglia sul piano XY (base)
        for x in range(0, int(L) + 1, step):
            p1 = self.project_3d_to_2d(x, 0, 0)
            p2 = self.project_3d_to_2d(x, s, 0)
            painter.drawLine(p1, p2)

        for y in range(0, int(s) + 1, int(step/2)):
            p1 = self.project_3d_to_2d(0, y, 0)
            p2 = self.project_3d_to_2d(L, y, 0)
            painter.drawLine(p1, p2)

    def draw_wall(self, painter):
        """Disegna il muro 3D"""
        L = self.wall_data['length']
        H = self.wall_data['height']
        s = self.wall_data['thickness']

        # Facce del muro (ordinate per visibilità in base alla rotazione)
        # Faccia posteriore (retro)
        if self.rotation_z < 90:
            self.draw_face(painter, [
                (0, s, 0), (L, s, 0), (L, s, H), (0, s, H)
            ], self.colors['wall_side'])

        # Faccia sinistra
        if self.rotation_z > 0:
            self.draw_face(painter, [
                (0, 0, 0), (0, s, 0), (0, s, H), (0, 0, H)
            ], self.colors['wall_side'])

        # Faccia frontale
        self.draw_face(painter, [
            (0, 0, 0), (L, 0, 0), (L, 0, H), (0, 0, H)
        ], self.colors['wall_front'])

        # Faccia destra
        if self.rotation_z < 90:
            self.draw_face(painter, [
                (L, 0, 0), (L, s, 0), (L, s, H), (L, 0, H)
            ], self.colors['wall_side'])

        # Faccia superiore
        self.draw_face(painter, [
            (0, 0, H), (L, 0, H), (L, s, H), (0, s, H)
        ], self.colors['wall_top'])

    def draw_face(self, painter, vertices_3d: list, color: QColor):
        """Disegna una faccia del muro"""
        # Converti vertici in 2D
        polygon = QPolygonF()
        for v in vertices_3d:
            p = self.project_3d_to_2d(v[0], v[1], v[2])
            polygon.append(p)

        # Riempi e disegna bordo
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawPolygon(polygon)

    def draw_opening_3d(self, painter, opening: dict):
        """Disegna un'apertura in 3D"""
        x = opening.get('x', 0)
        y = 0  # Frontale
        z = opening.get('y', 0)  # y in 2D diventa z in 3D
        w = opening.get('width', 100)
        h = opening.get('height', 200)
        s = self.wall_data['thickness']

        # Foro passante (apertura nel muro)
        # Faccia frontale (vetro/vuoto)
        self.draw_face(painter, [
            (x, 0, z), (x + w, 0, z), (x + w, 0, z + h), (x, 0, z + h)
        ], self.colors['opening'])

        # Spessore del foro (lati interni)
        # Lato sinistro interno
        painter.setBrush(QBrush(self.colors['opening'].darker(110)))
        self.draw_face(painter, [
            (x, 0, z), (x, s, z), (x, s, z + h), (x, 0, z + h)
        ], self.colors['opening'].darker(120))

        # Lato destro interno
        self.draw_face(painter, [
            (x + w, 0, z), (x + w, s, z), (x + w, s, z + h), (x + w, 0, z + h)
        ], self.colors['opening'].darker(120))

        # Architrave (sopra)
        self.draw_face(painter, [
            (x, 0, z + h), (x + w, 0, z + h), (x + w, s, z + h), (x, s, z + h)
        ], self.colors['opening'].darker(110))

        # Se ha rinforzo, disegna cerchiatura
        if opening.get('rinforzo'):
            self.draw_reinforcement_3d(painter, x, z, w, h, s)

    def draw_reinforcement_3d(self, painter, x: float, z: float, w: float, h: float, s: float):
        """Disegna cerchiatura 3D"""
        t = 8  # Spessore profilo cm

        painter.setBrush(QBrush(self.colors['reinforcement']))
        painter.setPen(QPen(self.colors['reinforcement'].darker(130), 1))

        # Montante sinistro
        self.draw_face(painter, [
            (x - t, -t, z), (x, -t, z), (x, -t, z + h), (x - t, -t, z + h)
        ], self.colors['reinforcement'])
        self.draw_face(painter, [
            (x - t, -t, z), (x - t, s + t, z), (x - t, s + t, z + h), (x - t, -t, z + h)
        ], self.colors['reinforcement'].darker(110))

        # Montante destro
        self.draw_face(painter, [
            (x + w, -t, z), (x + w + t, -t, z), (x + w + t, -t, z + h), (x + w, -t, z + h)
        ], self.colors['reinforcement'])
        self.draw_face(painter, [
            (x + w + t, -t, z), (x + w + t, s + t, z), (x + w + t, s + t, z + h), (x + w + t, -t, z + h)
        ], self.colors['reinforcement'].darker(110))

        # Traverso superiore
        self.draw_face(painter, [
            (x - t, -t, z + h), (x + w + t, -t, z + h), (x + w + t, -t, z + h + t), (x - t, -t, z + h + t)
        ], self.colors['reinforcement'])
        self.draw_face(painter, [
            (x - t, -t, z + h + t), (x + w + t, -t, z + h + t), (x + w + t, s + t, z + h + t), (x - t, s + t, z + h + t)
        ], self.colors['reinforcement'].lighter(110))

    def draw_axes(self, painter):
        """Disegna assi di riferimento"""
        origin = self.project_3d_to_2d(0, 0, 0)
        length = 40

        # Asse X (rosso)
        px = self.project_3d_to_2d(length / self.scale * 50, 0, 0)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(origin, px)
        painter.drawText(px.toPoint() + QPoint(5, 5), "X")

        # Asse Y (verde)
        py = self.project_3d_to_2d(0, length / self.scale * 50, 0)
        painter.setPen(QPen(QColor(0, 200, 0), 2))
        painter.drawLine(origin, py)
        painter.drawText(py.toPoint() + QPoint(5, 5), "Y")

        # Asse Z (blu)
        pz = self.project_3d_to_2d(0, 0, length / self.scale * 50)
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawLine(origin, pz)
        painter.drawText(pz.toPoint() + QPoint(5, -5), "Z")

    def draw_view_info(self, painter):
        """Disegna info sulla vista"""
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont('Arial', 9))

        info = f"Rotazione: {self.rotation_z:.0f}° | Tilt: {self.rotation_x:.0f}°"
        painter.drawText(10, self.height() - 10, info)

        # Istruzioni
        painter.drawText(10, 20, "Trascina: ruota | Rotella: zoom")

    def mousePressEvent(self, event):
        """Gestisce click mouse"""
        if event.button() == Qt.LeftButton:
            self.is_rotating = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Gestisce movimento mouse"""
        if self.is_rotating and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.rotation_z += delta.x() * 0.5
            self.rotation_x += delta.y() * 0.3

            # Limita rotazione X
            self.rotation_x = max(10, min(80, self.rotation_x))

            # Normalizza rotazione Z
            self.rotation_z = self.rotation_z % 360

            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Gestisce rilascio mouse"""
        if event.button() == Qt.LeftButton:
            self.is_rotating = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """Gestisce zoom con rotella"""
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        self.scale *= factor
        self.scale = max(0.1, min(3.0, self.scale))
        self.update()

    def reset_view(self):
        """Ripristina vista predefinita"""
        self.rotation_x = 30
        self.rotation_z = 45
        self.offset = QPointF(0, 0)
        self.calculate_scale()
        self.update()

    def resizeEvent(self, event):
        """Ricalcola scala al ridimensionamento"""
        self.calculate_scale()
        super().resizeEvent(event)
