"""
DXF Exporter - Esportazione disegni in formato DXF/CAD
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta

Genera file DXF compatibili con AutoCAD, LibreCAD, etc.
"""

import math
from datetime import datetime
from typing import List, Tuple, Optional


class DXFExporter:
    """Esportatore disegni in formato DXF"""

    def __init__(self):
        self.scale = 1.0  # Scala disegno (1:1 = cm)
        self.layers = {}
        self.entities = []
        self._setup_layers()

    def _setup_layers(self):
        """Configura layer standard"""
        self.layers = {
            'MURO': {'color': 7, 'linetype': 'CONTINUOUS'},
            'APERTURE': {'color': 1, 'linetype': 'CONTINUOUS'},
            'APERTURE_ESISTENTI': {'color': 3, 'linetype': 'DASHED'},
            'CERCHIATURE': {'color': 4, 'linetype': 'CONTINUOUS'},
            'QUOTE': {'color': 2, 'linetype': 'CONTINUOUS'},
            'TESTI': {'color': 7, 'linetype': 'CONTINUOUS'},
            'ASSI': {'color': 8, 'linetype': 'CENTER'},
            'TRATTEGGI': {'color': 8, 'linetype': 'CONTINUOUS'},
        }

    def export(self, filepath: str, project_data: dict, results: dict = None):
        """
        Esporta progetto in formato DXF

        Args:
            filepath: Percorso file di destinazione
            project_data: Dati progetto (wall, openings, etc.)
            results: Risultati calcolo (opzionale)
        """
        self.entities = []

        # Disegna elementi
        wall = project_data.get('wall', {})
        openings = project_data.get('openings', [])

        # Se openings vuoto, prova in openings_module
        if not openings:
            openings_data = project_data.get('openings_module', {})
            openings = openings_data.get('openings', [])

        self._draw_wall(wall)
        self._draw_openings(openings)
        self._draw_dimensions(wall, openings)
        self._draw_title_block(project_data)

        # Se ci sono risultati, aggiungi tabella
        if results:
            self._draw_results_table(wall, results)

        # Genera file DXF
        if not filepath.endswith('.dxf'):
            filepath += '.dxf'

        self._write_dxf(filepath)
        return filepath

    def _draw_wall(self, wall: dict):
        """Disegna il muro"""
        if not wall:
            return

        L = wall.get('length', 0)
        H = wall.get('height', 0)
        H_left = wall.get('height_left', H)
        H_right = wall.get('height_right', H)

        # Contorno muro
        if abs(H_left - H_right) < 0.1:
            # Muro rettangolare
            self._add_rectangle(0, 0, L, H, 'MURO')
        else:
            # Muro trapezoidale
            points = [(0, 0), (0, H_left), (L, H_right), (L, 0), (0, 0)]
            self._add_polyline(points, 'MURO')

        # Tratteggio muro (pattern mattoni semplificato)
        self._add_hatch_pattern(0, 0, L, H, 'MURO')

    def _draw_openings(self, openings: List[dict]):
        """Disegna le aperture"""
        for i, opening in enumerate(openings):
            x = opening.get('x', 0)
            y = opening.get('y', 0)
            w = opening.get('width', 100)
            h = opening.get('height', 200)
            op_type = opening.get('type', 'Rettangolare')
            existing = opening.get('existing', False)

            layer = 'APERTURE_ESISTENTI' if existing else 'APERTURE'

            if op_type == 'Rettangolare':
                self._add_rectangle(x, y, x + w, y + h, layer)

            elif op_type == 'Ad arco':
                arch_data = opening.get('arch_data', {})
                impost = arch_data.get('impost_height', h * 0.8)
                arch_rise = arch_data.get('arch_rise', w / 2)

                # Parte rettangolare
                self._add_line(x, y, x, y + impost, layer)
                self._add_line(x + w, y, x + w, y + impost, layer)
                self._add_line(x, y, x + w, y, layer)

                # Arco
                self._add_arc(x + w/2, y + impost, w/2, 0, 180, layer)

            elif op_type == 'Circolare':
                circ_data = opening.get('circular_data', {})
                diameter = circ_data.get('diameter', min(w, h))
                cx = x + w / 2
                cy = y + h / 2
                self._add_circle(cx, cy, diameter / 2, layer)

            # Etichetta apertura
            label = f"A{i+1}\n{w}x{h}"
            self._add_text(x + w/2, y + h/2, label, 'TESTI', height=8, halign='center')

            # Se ha rinforzo, disegna cerchiatura
            if opening.get('rinforzo'):
                self._draw_reinforcement(x, y, w, h, opening['rinforzo'])

    def _draw_reinforcement(self, x: float, y: float, w: float, h: float, rinforzo: dict):
        """Disegna la cerchiatura metallica"""
        profilo = rinforzo.get('profilo', 'HEA 120')

        # Spessore approssimativo del profilo (per visualizzazione)
        t = 10  # cm

        # Montanti (piatti)
        self._add_rectangle(x - t, y, x, y + h, 'CERCHIATURE')
        self._add_rectangle(x + w, y, x + w + t, y + h, 'CERCHIATURE')

        # Traverso superiore
        self._add_rectangle(x - t, y + h, x + w + t, y + h + t, 'CERCHIATURE')

        # Traverso inferiore (se porta, solo architrave)
        if y > 0:  # Non è una porta
            self._add_rectangle(x - t, y - t, x + w + t, y, 'CERCHIATURE')

        # Etichetta profilo
        self._add_text(x + w/2, y + h + t + 5, profilo, 'CERCHIATURE', height=6, halign='center')

    def _draw_dimensions(self, wall: dict, openings: List[dict]):
        """Disegna le quote"""
        L = wall.get('length', 0)
        H = wall.get('height', 0)

        offset = 30  # Distanza quote dal muro

        # Quota orizzontale totale
        self._add_dimension(0, -offset, L, -offset, L, 'QUOTE')

        # Quota verticale totale
        self._add_dimension(-offset, 0, -offset, H, H, 'QUOTE', vertical=True)

        # Quote aperture
        for i, opening in enumerate(openings):
            x = opening.get('x', 0)
            y = opening.get('y', 0)
            w = opening.get('width', 100)
            h = opening.get('height', 200)

            # Posizione X
            y_quota = -offset - 15 * (i + 1)
            self._add_dimension(x, y_quota, x + w, y_quota, w, 'QUOTE')

            # Altezza
            x_quota = L + offset + 15 * i
            self._add_dimension(x_quota, y, x_quota, y + h, h, 'QUOTE', vertical=True)

    def _draw_title_block(self, project_data: dict):
        """Disegna cartiglio"""
        wall = project_data.get('wall', {})
        L = wall.get('length', 0)

        # Posizione cartiglio (in basso a destra)
        x = L + 50
        y = -100

        # Riquadro
        self._add_rectangle(x, y, x + 150, y + 80, 'TESTI')

        # Testi
        self._add_text(x + 75, y + 70, "CALCOLO CERCHIATURE NTC 2018", 'TESTI', height=6, halign='center')
        self._add_text(x + 5, y + 55, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 'TESTI', height=4)

        project_info = project_data.get('project_info', {})
        self._add_text(x + 5, y + 45, f"Progetto: {project_info.get('name', '-')}", 'TESTI', height=4)
        self._add_text(x + 5, y + 35, f"Scala: 1:{int(1/self.scale)}", 'TESTI', height=4)
        self._add_text(x + 5, y + 15, "Arch. M. Bartolotta", 'TESTI', height=3)

    def _draw_results_table(self, wall: dict, results: dict):
        """Disegna tabella risultati"""
        L = wall.get('length', 0)

        # Posizione tabella
        x = L + 50
        y = 0

        # Header
        self._add_rectangle(x, y, x + 150, y + 20, 'TESTI')
        self._add_text(x + 75, y + 12, "RISULTATI VERIFICA", 'TESTI', height=5, halign='center')

        # Righe
        verification = results.get('verification', {})
        rows = [
            f"ΔK = {verification.get('stiffness_variation', 0):.1f}% (limite ±15%)",
            f"ΔV = {verification.get('resistance_variation', 0):.1f}% (limite ±15%)",
            f"Esito: {'LOCALE' if verification.get('is_local') else 'NON LOCALE'}"
        ]

        for i, row in enumerate(rows):
            row_y = y + 30 + i * 12
            self._add_text(x + 5, row_y, row, 'TESTI', height=4)

    # ===== Metodi helper per entità DXF =====

    def _add_line(self, x1: float, y1: float, x2: float, y2: float, layer: str):
        """Aggiunge una linea"""
        self.entities.append({
            'type': 'LINE',
            'layer': layer,
            'start': (x1, y1),
            'end': (x2, y2)
        })

    def _add_rectangle(self, x1: float, y1: float, x2: float, y2: float, layer: str):
        """Aggiunge un rettangolo"""
        points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
        self._add_polyline(points, layer)

    def _add_polyline(self, points: List[Tuple[float, float]], layer: str, closed: bool = False):
        """Aggiunge una polilinea"""
        self.entities.append({
            'type': 'POLYLINE',
            'layer': layer,
            'points': points,
            'closed': closed
        })

    def _add_circle(self, cx: float, cy: float, radius: float, layer: str):
        """Aggiunge un cerchio"""
        self.entities.append({
            'type': 'CIRCLE',
            'layer': layer,
            'center': (cx, cy),
            'radius': radius
        })

    def _add_arc(self, cx: float, cy: float, radius: float, start_angle: float, end_angle: float, layer: str):
        """Aggiunge un arco"""
        self.entities.append({
            'type': 'ARC',
            'layer': layer,
            'center': (cx, cy),
            'radius': radius,
            'start_angle': start_angle,
            'end_angle': end_angle
        })

    def _add_text(self, x: float, y: float, text: str, layer: str,
                  height: float = 5, halign: str = 'left', rotation: float = 0):
        """Aggiunge un testo"""
        self.entities.append({
            'type': 'TEXT',
            'layer': layer,
            'position': (x, y),
            'text': text,
            'height': height,
            'halign': halign,
            'rotation': rotation
        })

    def _add_dimension(self, x1: float, y1: float, x2: float, y2: float,
                       value: float, layer: str, vertical: bool = False):
        """Aggiunge una quota"""
        # Per semplicità, disegniamo quota come linee + testo
        self._add_line(x1, y1, x2, y2, layer)

        # Frecce (semplificate come linee)
        if vertical:
            self._add_line(x1 - 3, y1, x1 + 3, y1, layer)
            self._add_line(x1 - 3, y2, x1 + 3, y2, layer)
            text_x = x1 - 10
            text_y = (y1 + y2) / 2
            rotation = 90
        else:
            self._add_line(x1, y1 - 3, x1, y1 + 3, layer)
            self._add_line(x2, y1 - 3, x2, y1 + 3, layer)
            text_x = (x1 + x2) / 2
            text_y = y1 - 5
            rotation = 0

        self._add_text(text_x, text_y, f"{value:.0f}", layer, height=4,
                      halign='center', rotation=rotation)

    def _add_hatch_pattern(self, x1: float, y1: float, x2: float, y2: float, layer: str):
        """Aggiunge tratteggio semplificato (linee diagonali)"""
        spacing = 20
        for i in range(int((x2 - x1 + y2 - y1) / spacing) + 1):
            start_x = x1 + i * spacing
            start_y = y1
            end_x = x1
            end_y = y1 + i * spacing

            # Limita ai bordi del rettangolo
            if start_x > x2:
                start_y = y1 + (start_x - x2)
                start_x = x2
            if end_y > y2:
                end_x = x1 + (end_y - y2)
                end_y = y2

            if start_x >= x1 and end_x <= x2 and start_y <= y2 and end_y >= y1:
                self._add_line(start_x, start_y, end_x, end_y, 'TRATTEGGI')

    def _write_dxf(self, filepath: str):
        """Scrive il file DXF"""
        with open(filepath, 'w') as f:
            # Header
            f.write("0\nSECTION\n2\nHEADER\n")
            f.write("9\n$ACADVER\n1\nAC1014\n")  # AutoCAD R14 format
            f.write("9\n$INSUNITS\n70\n4\n")     # Unità: centimetri
            f.write("0\nENDSEC\n")

            # Tables (layer definitions)
            f.write("0\nSECTION\n2\nTABLES\n")
            f.write("0\nTABLE\n2\nLAYER\n")

            for layer_name, layer_props in self.layers.items():
                f.write("0\nLAYER\n")
                f.write(f"2\n{layer_name}\n")
                f.write("70\n0\n")
                f.write(f"62\n{layer_props['color']}\n")
                f.write(f"6\n{layer_props['linetype']}\n")

            f.write("0\nENDTAB\n")
            f.write("0\nENDSEC\n")

            # Entities
            f.write("0\nSECTION\n2\nENTITIES\n")

            for entity in self.entities:
                if entity['type'] == 'LINE':
                    f.write("0\nLINE\n")
                    f.write(f"8\n{entity['layer']}\n")
                    f.write(f"10\n{entity['start'][0]}\n")
                    f.write(f"20\n{entity['start'][1]}\n")
                    f.write("30\n0\n")
                    f.write(f"11\n{entity['end'][0]}\n")
                    f.write(f"21\n{entity['end'][1]}\n")
                    f.write("31\n0\n")

                elif entity['type'] == 'POLYLINE':
                    f.write("0\nLWPOLYLINE\n")
                    f.write(f"8\n{entity['layer']}\n")
                    f.write(f"90\n{len(entity['points'])}\n")
                    f.write("70\n1\n" if entity['closed'] else "70\n0\n")
                    for px, py in entity['points']:
                        f.write(f"10\n{px}\n20\n{py}\n")

                elif entity['type'] == 'CIRCLE':
                    f.write("0\nCIRCLE\n")
                    f.write(f"8\n{entity['layer']}\n")
                    f.write(f"10\n{entity['center'][0]}\n")
                    f.write(f"20\n{entity['center'][1]}\n")
                    f.write("30\n0\n")
                    f.write(f"40\n{entity['radius']}\n")

                elif entity['type'] == 'ARC':
                    f.write("0\nARC\n")
                    f.write(f"8\n{entity['layer']}\n")
                    f.write(f"10\n{entity['center'][0]}\n")
                    f.write(f"20\n{entity['center'][1]}\n")
                    f.write("30\n0\n")
                    f.write(f"40\n{entity['radius']}\n")
                    f.write(f"50\n{entity['start_angle']}\n")
                    f.write(f"51\n{entity['end_angle']}\n")

                elif entity['type'] == 'TEXT':
                    f.write("0\nTEXT\n")
                    f.write(f"8\n{entity['layer']}\n")
                    f.write(f"10\n{entity['position'][0]}\n")
                    f.write(f"20\n{entity['position'][1]}\n")
                    f.write("30\n0\n")
                    f.write(f"40\n{entity['height']}\n")
                    f.write(f"1\n{entity['text']}\n")
                    if entity.get('rotation', 0) != 0:
                        f.write(f"50\n{entity['rotation']}\n")

            f.write("0\nENDSEC\n")
            f.write("0\nEOF\n")


def export_to_dxf(filepath: str, project_data: dict, results: dict = None) -> str:
    """Funzione helper per esportazione rapida"""
    exporter = DXFExporter()
    return exporter.export(filepath, project_data, results)
