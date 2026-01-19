"""
Widget Canvas per visualizzazione muro
Disegna il muro con aperture e quote
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math

class WallCanvas(QWidget):
    """Canvas per disegno muro con aperture"""
    
    # Segnali
    opening_selected = pyqtSignal(int)  # Emesso quando si clicca su un'apertura
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
        # Dati
        self.wall_data = None
        self.openings = []
        self.selected_opening = -1
        
        # Visualizzazione
        self.scale = 1.0
        self.offset_x = 50
        self.offset_y = 50
        self.show_grid = True
        self.show_dimensions = True
        self.show_opening_labels = True
        
        # Colori
        self.colors = {
            'background': QColor(250, 250, 250),
            'grid': QColor(240, 240, 240),
            'wall': QColor(200, 200, 200),
            'wall_border': QColor(50, 50, 50),
            'opening_new': QColor(255, 255, 255),
            'opening_new_border': QColor(255, 0, 0),
            'opening_existing': QColor(255, 255, 255),
            'opening_existing_border': QColor(255, 165, 0),
            'dimension': QColor(100, 100, 100),
            'text': QColor(0, 0, 0),
            'selection': QColor(0, 120, 215)
        }
        
        # Font
        self.font_small = QFont('Arial', 9)
        self.font_normal = QFont('Arial', 10)
        self.font_bold = QFont('Arial', 10, QFont.Bold)
        
    def set_wall_data(self, length, height, thickness):
        """Imposta dimensioni muro"""
        self.wall_data = {
            'length': length,
            'height': height,
            'thickness': thickness
        }
        self.calculate_scale()
        self.update()
        
    def add_opening(self, opening_data):
        """Aggiunge un'apertura"""
        self.openings.append(opening_data.copy())
        self.update()
        
    def remove_opening(self, index):
        """Rimuove un'apertura"""
        if 0 <= index < len(self.openings):
            self.openings.pop(index)
            if self.selected_opening == index:
                self.selected_opening = -1
            elif self.selected_opening > index:
                self.selected_opening -= 1
            self.update()
            
    def clear_openings(self):
        """Rimuove tutte le aperture"""
        self.openings.clear()
        self.selected_opening = -1
        self.update()
        
    def calculate_scale(self):
        """Calcola scala ottimale per visualizzazione"""
        if not self.wall_data:
            return
            
        # Margini disponibili
        margin = 100
        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin
        
        # Calcola scala per adattare il muro
        if available_width > 0 and available_height > 0:
            scale_x = available_width / self.wall_data['length']
            scale_y = available_height / self.wall_data['height']
            self.scale = min(scale_x, scale_y) * 0.9  # 90% per lasciare spazio
            
    def wall_to_screen(self, x, y):
        """Converte coordinate muro in coordinate schermo (ritorna interi)"""
        screen_x = int(self.offset_x + x * self.scale)
        screen_y = int(self.height() - self.offset_y - y * self.scale)
        return screen_x, screen_y
        
    def screen_to_wall(self, x, y):
        """Converte coordinate schermo in coordinate muro"""
        wall_x = (x - self.offset_x) / self.scale
        wall_y = (self.height() - self.offset_y - y) / self.scale
        return wall_x, wall_y
        
    def paintEvent(self, event):
        """Disegna muro e aperture"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Sfondo
        painter.fillRect(self.rect(), self.colors['background'])
        
        if not self.wall_data:
            # Messaggio se non ci sono dati
            painter.setPen(self.colors['text'])
            painter.setFont(self.font_normal)
            painter.drawText(self.rect(), Qt.AlignCenter, 
                           "Inserire le dimensioni del muro")
            return
            
        # Disegna griglia
        if self.show_grid:
            self.draw_grid(painter)
            
        # Disegna muro
        self.draw_wall(painter)
        
        # Disegna aperture
        for i, opening in enumerate(self.openings):
            self.draw_opening(painter, opening, i)
            
        # Disegna quote
        if self.show_dimensions:
            self.draw_dimensions(painter)
            
        # Disegna maschi murari
        self.draw_maschi_labels(painter)
        
    def draw_grid(self, painter):
        """Disegna griglia di sfondo"""
        painter.setPen(QPen(self.colors['grid'], 1))
        
        # Griglia ogni 50cm
        grid_spacing = 50  # cm
        
        # Linee verticali
        x = 0
        while x <= self.wall_data['length']:
            screen_x, _ = self.wall_to_screen(x, 0)
            painter.drawLine(screen_x, 0, screen_x, self.height())
            x += grid_spacing
            
        # Linee orizzontali
        y = 0
        while y <= self.wall_data['height']:
            _, screen_y = self.wall_to_screen(0, y)
            painter.drawLine(0, screen_y, self.width(), screen_y)
            y += grid_spacing
            
    def draw_wall(self, painter):
        """Disegna il muro"""
        # Coordinate muro
        x1, y1 = self.wall_to_screen(0, 0)
        x2, y2 = self.wall_to_screen(self.wall_data['length'], self.wall_data['height'])
        
        # Riempimento
        wall_rect = QRect(x1, y2, x2 - x1, y1 - y2)
        painter.fillRect(wall_rect, self.colors['wall'])
        
        # Bordo
        painter.setPen(QPen(self.colors['wall_border'], 2))
        painter.drawRect(wall_rect)
        
    def draw_opening(self, painter, opening, index):
        """Disegna un'apertura"""
        # Coordinate apertura
        x1, y1 = self.wall_to_screen(opening['x'], opening['y'])
        x2, y2 = self.wall_to_screen(
            opening['x'] + opening['width'],
            opening['y'] + opening['height']
        )
        
        # Rettangolo apertura
        opening_rect = QRect(x1, y2, x2 - x1, y1 - y2)
        
        # Colori in base al tipo
        if opening.get('existing', False):
            fill_color = self.colors['opening_existing']
            border_color = self.colors['opening_existing_border']
        else:
            fill_color = self.colors['opening_new']
            border_color = self.colors['opening_new_border']
            
        # Se selezionata
        if index == self.selected_opening:
            border_color = self.colors['selection']
            pen_width = 3
        else:
            pen_width = 2
            
        # Disegna apertura
        painter.fillRect(opening_rect, fill_color)
        painter.setPen(QPen(border_color, pen_width))
        
        # Tipo di apertura
        if opening.get('type') == 'Ad arco':
            # Disegna arco superiore
            arc_width = x2 - x1
            arc_height = arc_width // 2
            arc_rect = QRect(x1, y2 - arc_height, arc_width, arc_height * 2)
            painter.drawArc(arc_rect, 0 * 16, 180 * 16)
            painter.drawLine(x1, y1, x1, y2 + arc_height // 2)
            painter.drawLine(x2, y1, x2, y2 + arc_height // 2)
        else:
            # Rettangolare normale
            painter.drawRect(opening_rect)
            
        # Etichetta apertura
        if self.show_opening_labels:
            painter.setPen(self.colors['text'])
            painter.setFont(self.font_bold)
            label = f"A{index + 1}"
            painter.drawText(opening_rect, Qt.AlignCenter, label)
            
            # Dimensioni apertura
            painter.setFont(self.font_small)
            dim_text = f"{opening['width']}×{opening['height']}"
            label_rect = QRect(x1, y2 + 20, x2 - x1, 20)
            painter.drawText(label_rect, Qt.AlignCenter, dim_text)
            
    def draw_dimensions(self, painter):
        """Disegna le quote del muro"""
        painter.setPen(QPen(self.colors['dimension'], 1))
        painter.setFont(self.font_normal)
        
        # Quota orizzontale (lunghezza)
        x1, y1 = self.wall_to_screen(0, -30)
        x2, y2 = self.wall_to_screen(self.wall_data['length'], -30)
        
        # Linea quota
        painter.drawLine(x1, y1, x2, y1)
        
        # Terminali
        painter.drawLine(x1, y1 - 5, x1, y1 + 5)
        painter.drawLine(x2, y1 - 5, x2, y1 + 5)
        
        # Testo
        text = f"{self.wall_data['length']} cm"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = (x1 + x2) // 2 - text_rect.width() // 2
        painter.drawText(text_x, y1 + 20, text)
        
        # Quota verticale (altezza)
        x1, y1 = self.wall_to_screen(-30, 0)
        x2, y2 = self.wall_to_screen(-30, self.wall_data['height'])
        
        # Linea quota
        painter.drawLine(x1, y1, x1, y2)
        
        # Terminali
        painter.drawLine(x1 - 5, y1, x1 + 5, y1)
        painter.drawLine(x1 - 5, y2, x1 + 5, y2)
        
        # Testo (ruotato)
        painter.save()
        painter.translate(x1 - 10, (y1 + y2) // 2)
        painter.rotate(-90)
        text = f"{self.wall_data['height']} cm"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(-text_rect.width() // 2, 0, text)
        painter.restore()
        
    def draw_maschi_labels(self, painter):
        """Disegna etichette dei maschi murari"""
        if not self.openings:
            return
            
        painter.setPen(self.colors['text'])
        painter.setFont(self.font_small)
        
        # Ordina aperture per posizione X
        sorted_openings = sorted(self.openings, key=lambda o: o['x'])
        
        # Maschio iniziale
        if sorted_openings[0]['x'] > 0:
            x_center = sorted_openings[0]['x'] / 2
            x_screen, y_screen = self.wall_to_screen(x_center, -50)
            text = f"M1\n{sorted_openings[0]['x']}cm"
            rect = QRect(x_screen - 30, y_screen, 60, 30)
            painter.drawText(rect, Qt.AlignCenter, text)
        
        # Maschi intermedi
        for i in range(len(sorted_openings) - 1):
            x1 = sorted_openings[i]['x'] + sorted_openings[i]['width']
            x2 = sorted_openings[i + 1]['x']
            if x2 > x1:
                x_center = (x1 + x2) / 2
                x_screen, y_screen = self.wall_to_screen(x_center, -50)
                text = f"M{i + 2}\n{int(x2 - x1)}cm"
                rect = QRect(x_screen - 30, y_screen, 60, 30)
                painter.drawText(rect, Qt.AlignCenter, text)
        
        # Maschio finale
        last_opening = sorted_openings[-1]
        x_end = last_opening['x'] + last_opening['width']
        if x_end < self.wall_data['length']:
            x_center = (x_end + self.wall_data['length']) / 2
            x_screen, y_screen = self.wall_to_screen(x_center, -50)
            text = f"M{len(sorted_openings) + 1}\n{int(self.wall_data['length'] - x_end)}cm"
            rect = QRect(x_screen - 30, y_screen, 60, 30)
            painter.drawText(rect, Qt.AlignCenter, text)
            
    def mousePressEvent(self, event):
        """Gestisce click del mouse"""
        if event.button() == Qt.LeftButton and self.wall_data:
            # Converti coordinate
            wall_x, wall_y = self.screen_to_wall(event.x(), event.y())
            
            # Verifica click su aperture
            for i, opening in enumerate(self.openings):
                if (opening['x'] <= wall_x <= opening['x'] + opening['width'] and
                    opening['y'] <= wall_y <= opening['y'] + opening['height']):
                    self.selected_opening = i
                    self.opening_selected.emit(i)
                    self.update()
                    return
                    
            # Nessuna apertura cliccata
            self.selected_opening = -1
            self.update()
            
    def mouseMoveEvent(self, event):
        """Gestisce movimento del mouse"""
        if self.wall_data:
            wall_x, wall_y = self.screen_to_wall(event.x(), event.y())
            
            # Verifica se sopra un'apertura
            for opening in self.openings:
                if (opening['x'] <= wall_x <= opening['x'] + opening['width'] and
                    opening['y'] <= wall_y <= opening['y'] + opening['height']):
                    self.setCursor(Qt.PointingHandCursor)
                    return
                    
            self.setCursor(Qt.ArrowCursor)
            
    def wheelEvent(self, event):
        """Gestisce zoom con rotella mouse"""
        # Punto centrale dello zoom
        center_x = event.x()
        center_y = event.y()
        
        # Fattore di zoom
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        
        # Applica zoom
        new_scale = self.scale * zoom_factor
        
        # Limiti zoom
        if 0.1 < new_scale < 10:
            self.scale = new_scale
            self.update()
            
    def resizeEvent(self, event):
        """Ricalcola scala quando la finestra viene ridimensionata"""
        self.calculate_scale()
        super().resizeEvent(event)
        
    def contextMenuEvent(self, event):
        """Menu contestuale"""
        menu = QMenu(self)
        
        # Opzioni visualizzazione
        grid_action = menu.addAction("Mostra griglia")
        grid_action.setCheckable(True)
        grid_action.setChecked(self.show_grid)
        grid_action.triggered.connect(lambda: self.toggle_option('grid'))
        
        dim_action = menu.addAction("Mostra quote")
        dim_action.setCheckable(True)
        dim_action.setChecked(self.show_dimensions)
        dim_action.triggered.connect(lambda: self.toggle_option('dimensions'))
        
        labels_action = menu.addAction("Mostra etichette aperture")
        labels_action.setCheckable(True)
        labels_action.setChecked(self.show_opening_labels)
        labels_action.triggered.connect(lambda: self.toggle_option('labels'))
        
        menu.addSeparator()
        
        # Zoom
        zoom_fit_action = menu.addAction("Adatta alla finestra")
        zoom_fit_action.triggered.connect(self.zoom_fit)
        
        zoom_in_action = menu.addAction("Zoom +")
        zoom_in_action.triggered.connect(lambda: self.zoom(1.2))
        
        zoom_out_action = menu.addAction("Zoom -")
        zoom_out_action.triggered.connect(lambda: self.zoom(0.8))
        
        menu.exec_(event.globalPos())
        
    def toggle_option(self, option):
        """Attiva/disattiva opzione visualizzazione"""
        if option == 'grid':
            self.show_grid = not self.show_grid
        elif option == 'dimensions':
            self.show_dimensions = not self.show_dimensions
        elif option == 'labels':
            self.show_opening_labels = not self.show_opening_labels
        self.update()
        
    def zoom(self, factor):
        """Applica zoom"""
        new_scale = self.scale * factor
        if 0.1 < new_scale < 10:
            self.scale = new_scale
            self.update()
            
    def zoom_fit(self):
        """Adatta zoom alla finestra"""
        self.calculate_scale()
        self.update()