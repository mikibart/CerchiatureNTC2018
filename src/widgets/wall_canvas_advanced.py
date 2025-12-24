"""
Widget Canvas Avanzato per visualizzazione muro con aperture complesse
Supporta: archi dettagliati, forme circolari/ellittiche, nicchie, chiusure
Arch. Michelangelo Bartolotta
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math

class AdvancedWallCanvas(QWidget):
    """Canvas avanzato per disegno muro con aperture complesse"""
    
    # Segnali
    opening_selected = pyqtSignal(int)
    
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
        self.show_niche_depth = True
        
        # Colori estesi
        self.colors = {
            'background': QColor(250, 250, 250),
            'grid': QColor(240, 240, 240),
            'wall': QColor(200, 200, 200),
            'wall_border': QColor(50, 50, 50),
            'opening_new': QColor(255, 255, 255),
            'opening_new_border': QColor(255, 0, 0),
            'opening_existing': QColor(255, 255, 255),
            'opening_existing_border': QColor(255, 165, 0),
            'niche': QColor(230, 230, 250),
            'niche_border': QColor(100, 100, 200),
            'closure': QColor(180, 180, 180),
            'closure_border': QColor(100, 100, 100),
            'dimension': QColor(100, 100, 100),
            'text': QColor(0, 0, 0),
            'selection': QColor(0, 120, 215),
            'arch_construction': QColor(150, 150, 150),
            'center_point': QColor(255, 0, 0)
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
            
        margin = 100
        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin
        
        if available_width > 0 and available_height > 0:
            scale_x = available_width / self.wall_data['length']
            scale_y = available_height / self.wall_data['height']
            self.scale = min(scale_x, scale_y) * 0.9
            
    def wall_to_screen(self, x, y):
        """Converte coordinate muro in coordinate schermo"""
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
            self.draw_opening_advanced(painter, opening, i)
            
        # Disegna quote
        if self.show_dimensions:
            self.draw_dimensions(painter)
            
        # Disegna maschi murari
        self.draw_maschi_labels(painter)
        
    def draw_opening_advanced(self, painter, opening, index):
        """Disegna apertura con supporto forme avanzate"""
        opening_type = opening.get('type', 'Rettangolare')
        
        # Determina colori base
        if opening.get('closure_data'):
            fill_color = self.colors['closure']
            border_color = self.colors['closure_border']
        elif opening.get('niche_data'):
            fill_color = self.colors['niche']
            border_color = self.colors['niche_border']
        elif opening.get('existing', False):
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
            
        # Disegna in base al tipo
        if opening_type == 'Rettangolare':
            self.draw_rectangular_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Ad arco':
            self.draw_arch_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Circolare':
            self.draw_circular_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Ovale':
            self.draw_oval_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Ellittica':
            self.draw_elliptical_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Nicchia':
            self.draw_niche_opening(painter, opening, fill_color, border_color, pen_width)
        elif opening_type == 'Chiusura vano esistente':
            self.draw_closure_opening(painter, opening, fill_color, border_color, pen_width)
            
        # Etichetta apertura
        if self.show_opening_labels:
            self.draw_opening_label(painter, opening, index)
            
    def draw_rectangular_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna apertura rettangolare"""
        x1, y1 = self.wall_to_screen(opening['x'], opening['y'])
        x2, y2 = self.wall_to_screen(
            opening['x'] + opening['width'],
            opening['y'] + opening['height']
        )
        
        rect = QRect(x1, y2, x2 - x1, y1 - y2)
        painter.fillRect(rect, fill_color)
        painter.setPen(QPen(border_color, pen_width))
        painter.drawRect(rect)
        
    def draw_arch_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna apertura ad arco con parametri dettagliati - VERSIONE DEFINITIVA"""
        if 'arch_data' not in opening:
            # Fallback a disegno semplice
            self.draw_rectangular_opening(painter, opening, fill_color, border_color, pen_width)
            return
            
        arch_data = opening['arch_data']
        
        # Coordinate base
        x = opening['x']
        y = opening['y']
        width = opening['width']
        
        # Parametri arco
        impost_height = arch_data.get('impost_height', 180)
        arch_rise = arch_data.get('arch_rise', 60)
        arch_type = arch_data.get('arch_type', 'Tutto sesto')
        
        # Disegna piedritti - coordinate schermo corrette
        x1, y1 = self.wall_to_screen(x, y)
        x2, y2 = self.wall_to_screen(x + width, y)
        x3, y3 = self.wall_to_screen(x, y + impost_height)
        x4, y4 = self.wall_to_screen(x + width, y + impost_height)
        
        # Path per l'apertura completa
        path = QPainterPath()
        path.moveTo(x1, y1)
        path.lineTo(x1, y3)
        
        # Disegna l'arco in base al tipo
        if arch_type == 'Tutto sesto':
            # Per arco a tutto sesto, usiamo cubicTo per controllo completo
            # Punto di controllo per l'arco (sopra il centro)
            ctrl_x = x + width / 2
            ctrl_y = y + impost_height + width / 2  # Altezza = raggio per semicerchio
            ctrl_x_screen, ctrl_y_screen = self.wall_to_screen(ctrl_x, ctrl_y)
            
            # Disegna l'arco con due curve di Bezier
            # Prima metà dell'arco (da sinistra al centro)
            mid_x = x + width / 2
            mid_y = y + impost_height + width / 2
            mid_x_screen, mid_y_screen = self.wall_to_screen(mid_x, mid_y)
            
            # Punti di controllo per prima curva
            ctrl1_x, ctrl1_y = self.wall_to_screen(x, y + impost_height + width / 2)
            path.cubicTo(x3, ctrl1_y, ctrl1_x, mid_y_screen, mid_x_screen, mid_y_screen)
            
            # Seconda metà dell'arco (dal centro a destra)
            ctrl2_x, ctrl2_y = self.wall_to_screen(x + width, y + impost_height + width / 2)
            path.cubicTo(ctrl2_x, mid_y_screen, x4, ctrl2_y, x4, y4)
            
        elif arch_type == 'Ribassato':
            # Arco ribassato con punti intermedi
            n_points = 20  # Numero di punti per l'arco
            for i in range(n_points + 1):
                angle = math.pi * i / n_points  # Da 0 a pi
                px = x + width / 2 - (width / 2) * math.cos(angle)
                py = y + impost_height + arch_rise * math.sin(angle)
                px_screen, py_screen = self.wall_to_screen(px, py)
                if i == 0:
                    path.lineTo(px_screen, py_screen)
                else:
                    path.lineTo(px_screen, py_screen)
                    
        elif arch_type == 'Rialzato (ogivale)':
            # Arco ogivale con due archi che si intersecano
            # Primo arco (parte sinistra)
            n_points = 10
            radius = width * 0.75
            
            # Centro del primo arco a sinistra
            for i in range(n_points + 1):
                angle = math.pi/2 - math.acos(width/(2*radius)) * i / n_points
                px = x + radius * math.cos(angle)
                py = y + impost_height + radius * math.sin(angle)
                px_screen, py_screen = self.wall_to_screen(px, py)
                path.lineTo(px_screen, py_screen)
                
            # Secondo arco (parte destra)
            for i in range(n_points, -1, -1):
                angle = math.pi/2 + math.acos(width/(2*radius)) * i / n_points
                px = x + width - radius * math.cos(angle)
                py = y + impost_height + radius * math.sin(angle)
                px_screen, py_screen = self.wall_to_screen(px, py)
                path.lineTo(px_screen, py_screen)
            
        # Completa il path
        path.lineTo(x2, y2)
        path.lineTo(x2, y1)
        path.closeSubpath()
        
        # Riempi e disegna bordo
        painter.fillPath(path, fill_color)
        painter.setPen(QPen(border_color, pen_width))
        painter.drawPath(path)
        
        # Disegna linee di costruzione per archi complessi
        if self.show_grid and arch_type != 'Rettangolare':
            # Linea imposta - ora visibile
            painter.setPen(QPen(self.colors['arch_construction'], 2, Qt.DashLine))
            painter.drawLine(int(x1), int(y3), int(x4), int(y4))
            
            # Aggiungi indicazione testuale dell'imposta
            painter.setPen(QPen(self.colors['text'], 1))
            painter.setFont(self.font_small)
            
            # Testo "Imposta" sulla linea dell'imposta
            mid_x = int((x1 + x4) / 2)
            painter.drawText(mid_x - 25, int(y3 - 5), "Imposta")
            
            # Quota altezza imposta sul lato
            if impost_height > 0:
                # Linea verticale per quota
                quota_x = int(x1 - 20)
                painter.setPen(QPen(self.colors['dimension'], 1))
                painter.drawLine(quota_x, int(y1), quota_x, int(y3))
                painter.drawLine(quota_x - 3, int(y1), quota_x + 3, int(y1))
                painter.drawLine(quota_x - 3, int(y3), quota_x + 3, int(y3))
                
                # Testo quota
                painter.save()
                painter.translate(int(quota_x - 10), int((y1 + y3) / 2))
                painter.rotate(-90)
                painter.drawText(-20, 0, f"{impost_height} cm")
                painter.restore()
                
            # Se arco a tutto sesto, mostra il centro
            if arch_type == 'Tutto sesto' and self.show_grid:
                cx_screen, cy_screen = self.wall_to_screen(x + width/2, y + impost_height)
                painter.setPen(QPen(self.colors['center_point'], 5))
                painter.drawPoint(int(cx_screen), int(cy_screen))
                
                # Raggio di costruzione
                painter.setPen(QPen(self.colors['arch_construction'], 1, Qt.DotLine))
                painter.drawLine(int(cx_screen), int(cy_screen), int(x3), int(y3))
                
            # Quota freccia dell'arco
            if arch_rise > 0:
                # Punto più alto dell'arco
                top_x = x + width / 2
                top_y = y + impost_height + arch_rise
                top_x_screen, top_y_screen = self.wall_to_screen(top_x, top_y)
                
                # Linea verticale per freccia
                painter.setPen(QPen(self.colors['dimension'], 1, Qt.DashLine))
                painter.drawLine(int(top_x_screen), int(y3), int(top_x_screen), int(top_y_screen))
                
                # Testo freccia
                painter.setPen(QPen(self.colors['text'], 1))
                painter.drawText(int(top_x_screen + 5), int((y3 + top_y_screen) / 2), f"f={arch_rise}cm")
            
    def draw_circular_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna apertura circolare"""
        if 'circular_data' not in opening:
            return
            
        circ_data = opening['circular_data']
        diameter = circ_data.get('diameter', 100)
        
        # Centro
        if circ_data.get('custom_center'):
            cx = opening['x'] + opening['width']/2 + circ_data.get('center_x_offset', 0)
            cy = opening['y'] + opening['height']/2 + circ_data.get('center_y_offset', 0)
        else:
            cx = opening['x'] + diameter/2
            cy = opening['y'] + diameter/2
            
        # Converti in coordinate schermo
        screen_cx, screen_cy = self.wall_to_screen(cx, cy)
        radius = diameter * self.scale / 2
        
        # Disegna cerchio
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_color, pen_width))
        painter.drawEllipse(QPointF(screen_cx, screen_cy), radius, radius)
        
        # Punto centrale (se visualizzazione dettagliata attiva)
        if self.show_grid:
            painter.setPen(QPen(self.colors['center_point'], 3))
            painter.drawPoint(int(screen_cx), int(screen_cy))
            
    def draw_oval_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna apertura ovale"""
        if 'oval_data' not in opening:
            return
            
        oval_data = opening['oval_data']
        orientation = oval_data.get('orientation', 'Verticale')
        axis_ratio = oval_data.get('axis_ratio', 1.5)
        
        # Centro
        cx = opening['x'] + opening['width']/2
        cy = opening['y'] + opening['height']/2
        
        # Assi
        if orientation == 'Verticale':
            major_axis = opening['height'] / 2
            minor_axis = major_axis / axis_ratio
        else:
            major_axis = opening['width'] / 2
            minor_axis = major_axis / axis_ratio
            
        # Converti in coordinate schermo
        screen_cx, screen_cy = self.wall_to_screen(cx, cy)
        
        # Disegna ovale
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_color, pen_width))
        
        if orientation == 'Verticale':
            painter.drawEllipse(
                QPointF(screen_cx, screen_cy),
                minor_axis * self.scale,
                major_axis * self.scale
            )
        else:
            painter.drawEllipse(
                QPointF(screen_cx, screen_cy),
                major_axis * self.scale,
                minor_axis * self.scale
            )
            
    def draw_elliptical_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna apertura ellittica con rotazione"""
        if 'ellipse_data' not in opening:
            return
            
        ell_data = opening['ellipse_data']
        semi_major = ell_data.get('semi_major', 80)
        semi_minor = ell_data.get('semi_minor', 60)
        rotation = ell_data.get('rotation', 0)
        
        # Centro
        cx = opening['x'] + opening['width']/2
        cy = opening['y'] + opening['height']/2
        screen_cx, screen_cy = self.wall_to_screen(cx, cy)
        
        # Salva stato e ruota
        painter.save()
        painter.translate(screen_cx, screen_cy)
        painter.rotate(rotation)
        
        # Disegna ellisse
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_color, pen_width))
        painter.drawEllipse(
            QPointF(0, 0),
            semi_major * self.scale,
            semi_minor * self.scale
        )
        
        painter.restore()
        
    def draw_niche_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna nicchia con indicazione profondità"""
        # Disegna come rettangolo con pattern speciale
        self.draw_rectangular_opening(painter, opening, fill_color, border_color, pen_width)
        
        if 'niche_data' in opening and self.show_niche_depth:
            niche_data = opening['niche_data']
            depth = niche_data.get('depth', 15)
            
            # Coordinate
            x1, y1 = self.wall_to_screen(opening['x'], opening['y'])
            x2, y2 = self.wall_to_screen(
                opening['x'] + opening['width'],
                opening['y'] + opening['height']
            )
            
            # Disegna linee diagonali per indicare profondità
            painter.setPen(QPen(border_color, 1, Qt.DashLine))
            offset = min(10, depth * self.scale / 3)
            
            # Angoli
            painter.drawLine(int(x1), int(y1), int(x1 + offset), int(y1 - offset))
            painter.drawLine(int(x2), int(y1), int(x2 - offset), int(y1 - offset))
            painter.drawLine(int(x1), int(y2), int(x1 + offset), int(y2 + offset))
            painter.drawLine(int(x2), int(y2), int(x2 - offset), int(y2 + offset))
            
            # Testo profondità
            painter.setFont(self.font_small)
            painter.setPen(self.colors['text'])
            rect = QRect(int(x1), int(y2), int(x2 - x1), int(y1 - y2))
            painter.drawText(rect, Qt.AlignCenter | Qt.AlignBottom, 
                           f"Prof. {depth} cm")
                           
            # Se ha mensole, disegnale
            if niche_data.get('has_shelves'):
                n_shelves = niche_data.get('n_shelves', 4)
                shelf_spacing = (y1 - y2) / (n_shelves + 1)
                painter.setPen(QPen(border_color, 1))
                
                for i in range(1, n_shelves + 1):
                    shelf_y = int(y2 + i * shelf_spacing)
                    painter.drawLine(int(x1 + 5), shelf_y, int(x2 - 5), shelf_y)
                    
    def draw_closure_opening(self, painter, opening, fill_color, border_color, pen_width):
        """Disegna chiusura vano con pattern"""
        # Disegna rettangolo base
        self.draw_rectangular_opening(painter, opening, fill_color, border_color, pen_width)
        
        if 'closure_data' in opening:
            closure_data = opening['closure_data']
            
            # Coordinate
            x1, y1 = self.wall_to_screen(opening['x'], opening['y'])
            x2, y2 = self.wall_to_screen(
                opening['x'] + opening['width'],
                opening['y'] + opening['height']
            )
            
            # Pattern in base al tipo di chiusura
            closure_type = closure_data.get('type', 'Muratura piena')
            
            painter.setPen(QPen(border_color, 1))
            
            if 'Muratura' in closure_type:
                # Pattern mattoni
                brick_height = 10
                brick_width = 20
                
                for row in range(0, int((y1 - y2) / brick_height)):
                    y = int(y2 + row * brick_height)
                    offset = (row % 2) * brick_width / 2
                    
                    for col in range(0, int((x2 - x1) / brick_width) + 1):
                        x = int(x1 + col * brick_width + offset)
                        if x < x2:
                            painter.drawLine(x, y, x, y + brick_height)
                            
                    if row > 0:
                        painter.drawLine(int(x1), y, int(x2), y)
                        
            elif closure_type == 'Tamponamento leggero':
                # Pattern diagonale
                spacing = 15
                for i in range(0, int((x2 - x1 + y1 - y2) / spacing)):
                    x = int(x1 + i * spacing)
                    if x < x2:
                        painter.drawLine(x, int(y1), min(int(x + (y1 - y2)), int(x2)), int(y2))
                    else:
                        y_start = int(y1 - (x - x2))
                        if y_start > y2:
                            painter.drawLine(int(x2), y_start, int(x1), max(int(y_start - (x2 - x1)), int(y2)))
                            
            # Testo tipo chiusura
            painter.setFont(self.font_small)
            painter.setPen(self.colors['text'])
            rect = QRect(int(x1), int(y2), int(x2 - x1), int(y1 - y2))
            painter.drawText(rect, Qt.AlignCenter, closure_data.get('material', 'Chiusura'))
            
    def draw_opening_label(self, painter, opening, index):
        """Disegna etichetta per apertura"""
        painter.setPen(self.colors['text'])
        painter.setFont(self.font_bold)
        
        # Determina centro apertura
        cx = opening['x'] + opening['width'] / 2
        cy = opening['y'] + opening['height'] / 2
        screen_cx, screen_cy = self.wall_to_screen(cx, cy)
        
        # Etichetta base
        if opening.get('closure_data'):
            label = f"C{index + 1}"
        elif opening.get('niche_data'):
            label = f"N{index + 1}"
        else:
            label = f"A{index + 1}"
            
        # Dimensioni
        painter.setFont(self.font_small)
        opening_type = opening.get('type', 'Rettangolare')
        
        if opening_type == 'Circolare':
            if 'circular_data' in opening:
                dim_text = f"Ø{opening['circular_data']['diameter']}"
            else:
                dim_text = f"{opening['width']}×{opening['height']}"
        else:
            dim_text = f"{opening['width']}×{opening['height']}"
            
        # Disegna etichetta centrata
        painter.setFont(self.font_bold)
        painter.drawText(int(screen_cx - 20), int(screen_cy), label)
        
        # Dimensioni sotto
        painter.setFont(self.font_small)
        _, y_bottom = self.wall_to_screen(cx, opening['y'])
        painter.drawText(int(screen_cx - 30), int(y_bottom + 20), dim_text)
        
    def draw_grid(self, painter):
        """Disegna griglia di sfondo"""
        painter.setPen(QPen(self.colors['grid'], 1))
        
        # Griglia ogni 50cm
        grid_spacing = 50  # cm
        
        # Linee verticali
        x = 0
        while x <= self.wall_data['length']:
            screen_x, _ = self.wall_to_screen(x, 0)
            painter.drawLine(int(screen_x), 0, int(screen_x), self.height())
            x += grid_spacing
            
        # Linee orizzontali
        y = 0
        while y <= self.wall_data['height']:
            _, screen_y = self.wall_to_screen(0, y)
            painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
            y += grid_spacing
            
    def draw_wall(self, painter):
        """Disegna il muro"""
        x1, y1 = self.wall_to_screen(0, 0)
        x2, y2 = self.wall_to_screen(self.wall_data['length'], self.wall_data['height'])
        
        wall_rect = QRect(x1, y2, x2 - x1, y1 - y2)
        painter.fillRect(wall_rect, self.colors['wall'])
        painter.setPen(QPen(self.colors['wall_border'], 2))
        painter.drawRect(wall_rect)
        
    def draw_dimensions(self, painter):
        """Disegna le quote del muro"""
        painter.setPen(QPen(self.colors['dimension'], 1))
        painter.setFont(self.font_normal)
        
        # Quota orizzontale
        x1, y1 = self.wall_to_screen(0, -30)
        x2, y2 = self.wall_to_screen(self.wall_data['length'], -30)
        
        painter.drawLine(int(x1), int(y1), int(x2), int(y1))
        painter.drawLine(int(x1), int(y1 - 5), int(x1), int(y1 + 5))
        painter.drawLine(int(x2), int(y1 - 5), int(x2), int(y1 + 5))
        
        text = f"{self.wall_data['length']} cm"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = int((x1 + x2) // 2 - text_rect.width() // 2)
        painter.drawText(text_x, int(y1 + 20), text)
        
        # Quota verticale
        x1, y1 = self.wall_to_screen(-30, 0)
        x2, y2 = self.wall_to_screen(-30, self.wall_data['height'])
        
        painter.drawLine(x1, y1, x1, y2)
        painter.drawLine(x1 - 5, y1, x1 + 5, y1)
        painter.drawLine(x1 - 5, y2, x1 + 5, y2)
        
        painter.save()
        painter.translate(int(x1 - 10), int((y1 + y2) // 2))
        painter.rotate(-90)
        text = f"{self.wall_data['height']} cm"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(int(-text_rect.width() // 2), 0, text)
        painter.restore()
        
    def draw_maschi_labels(self, painter):
        """Disegna etichette dei maschi murari"""
        if not self.openings:
            return
            
        painter.setPen(self.colors['text'])
        painter.setFont(self.font_small)
        
        # Filtra solo aperture passanti (non nicchie)
        passanti = [op for op in self.openings 
                   if not op.get('niche_data', {}).get('is_niche', False)]
        
        if not passanti:
            return
            
        # Ordina per posizione X
        sorted_openings = sorted(passanti, key=lambda o: o['x'])
        
        # Maschio iniziale
        if sorted_openings[0]['x'] > 0:
            x_center = sorted_openings[0]['x'] / 2
            x_screen, y_screen = self.wall_to_screen(x_center, -50)
            text = f"M1\n{sorted_openings[0]['x']}cm"
            rect = QRect(int(x_screen - 30), int(y_screen), 60, 30)
            painter.drawText(rect, Qt.AlignCenter, text)
        
        # Maschi intermedi
        for i in range(len(sorted_openings) - 1):
            x1 = sorted_openings[i]['x'] + sorted_openings[i]['width']
            x2 = sorted_openings[i + 1]['x']
            if x2 > x1:
                x_center = (x1 + x2) / 2
                x_screen, y_screen = self.wall_to_screen(x_center, -50)
                text = f"M{i + 2}\n{int(x2 - x1)}cm"
                rect = QRect(int(x_screen - 30), int(y_screen), 60, 30)
                painter.drawText(rect, Qt.AlignCenter, text)
        
        # Maschio finale
        last_opening = sorted_openings[-1]
        x_end = last_opening['x'] + last_opening['width']
        if x_end < self.wall_data['length']:
            x_center = (x_end + self.wall_data['length']) / 2
            x_screen, y_screen = self.wall_to_screen(x_center, -50)
            text = f"M{len(sorted_openings) + 1}\n{int(self.wall_data['length'] - x_end)}cm"
            rect = QRect(int(x_screen - 30), int(y_screen), 60, 30)
            painter.drawText(rect, Qt.AlignCenter, text)
            
    def mousePressEvent(self, event):
        """Gestisce click del mouse"""
        if event.button() == Qt.LeftButton and self.wall_data:
            wall_x, wall_y = self.screen_to_wall(event.x(), event.y())
            
            for i, opening in enumerate(self.openings):
                if self.is_point_in_opening(wall_x, wall_y, opening):
                    self.selected_opening = i
                    self.opening_selected.emit(i)
                    self.update()
                    return
                    
            self.selected_opening = -1
            self.update()
            
    def is_point_in_opening(self, x, y, opening):
        """Verifica se un punto è dentro un'apertura - VERSIONE CORRETTA"""
        opening_type = opening.get('type', 'Rettangolare')
        
        if opening_type in ['Rettangolare', 'Nicchia', 'Chiusura vano esistente']:
            return (opening['x'] <= x <= opening['x'] + opening['width'] and
                   opening['y'] <= y <= opening['y'] + opening['height'])
                   
        elif opening_type == 'Ad arco':
            # Verifica prima se è fuori dal bounding box
            if not (opening['x'] <= x <= opening['x'] + opening['width'] and
                    opening['y'] <= y <= opening['y'] + opening['height']):
                return False
                
            if 'arch_data' in opening:
                arch_data = opening['arch_data']
                impost = arch_data.get('impost_height', 180)
                arch_rise = arch_data.get('arch_rise', 60)
                arch_type = arch_data.get('arch_type', 'Tutto sesto')
                
                # Se sotto l'imposta, è dentro la parte rettangolare
                if y <= opening['y'] + impost:
                    return True
                    
                # Sopra l'imposta, verifica se è dentro l'arco
                rel_x = x - opening['x']  # Posizione relativa nell'apertura
                rel_y = y - (opening['y'] + impost)  # Altezza sopra l'imposta
                
                if arch_type == 'Tutto sesto':
                    # Arco semicircolare
                    radius = opening['width'] / 2
                    center_x = opening['width'] / 2
                    
                    # Distanza dal centro dell'arco
                    dist = math.sqrt((rel_x - center_x)**2 + rel_y**2)
                    return dist <= radius
                    
                elif arch_type == 'Ribassato':
                    # Formula per arco ribassato
                    radius = (arch_rise**2 + (opening['width']/2)**2) / (2 * arch_rise)
                    center_x = opening['width'] / 2
                    center_y = -(radius - arch_rise)  # Centro sotto l'imposta
                    
                    dist = math.sqrt((rel_x - center_x)**2 + (rel_y - center_y)**2)
                    return dist <= radius and rel_y <= arch_rise
                    
                elif arch_type == 'Rialzato (ogivale)':
                    # Arco ogivale - verifica con entrambi i centri
                    radius = opening['width'] * 0.75
                    
                    # Verifica arco sinistro
                    dist1 = math.sqrt(rel_x**2 + rel_y**2)
                    if dist1 <= radius and rel_x <= opening['width'] / 2:
                        return True
                        
                    # Verifica arco destro
                    dist2 = math.sqrt((rel_x - opening['width'])**2 + rel_y**2)
                    if dist2 <= radius and rel_x >= opening['width'] / 2:
                        return True
                        
                    return False
                    
                else:
                    # Per altri tipi, usa il bounding box
                    return rel_y <= arch_rise
            else:
                # Senza dati arco, usa il rettangolo
                return True
                
        elif opening_type == 'Circolare' and 'circular_data' in opening:
            circ = opening['circular_data']
            diameter = circ['diameter']
            cx = opening['x'] + diameter/2
            cy = opening['y'] + diameter/2
            
            if circ.get('custom_center'):
                cx += circ.get('center_x_offset', 0)
                cy += circ.get('center_y_offset', 0)
                
            distance = math.sqrt((x - cx)**2 + (y - cy)**2)
            return distance <= diameter/2
            
        else:
            # Per altre forme, usa il bounding box
            return (opening['x'] <= x <= opening['x'] + opening['width'] and
                   opening['y'] <= y <= opening['y'] + opening['height'])
                   
    def wheelEvent(self, event):
        """Gestisce zoom con rotella mouse"""
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        new_scale = self.scale * zoom_factor
        
        if 0.1 < new_scale < 10:
            self.scale = new_scale
            self.update()
            
    def resizeEvent(self, event):
        """Ricalcola scala quando la finestra viene ridimensionata"""
        self.calculate_scale()
        super().resizeEvent(event)