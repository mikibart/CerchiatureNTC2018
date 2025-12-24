"""
Generatore Report PDF
Calcolatore Cerchiature NTC 2018
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generatore relazioni di calcolo in PDF"""

    def __init__(self):
        self.page_width, self.page_height = A4 if REPORTLAB_AVAILABLE else (595, 842)
        self.margin = 2 * cm if REPORTLAB_AVAILABLE else 56.7
        self.project_data = {}
        self.results = {}

    def set_data(self, project_data: Dict, results: Dict):
        """Imposta i dati per la generazione del report"""
        self.project_data = project_data
        self.results = results

    def generate_report(self, filepath: str) -> bool:
        """
        Genera relazione completa in PDF

        Args:
            filepath: Percorso del file PDF di destinazione

        Returns:
            True se la generazione ha avuto successo
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab non disponibile. Installare con: pip install reportlab")
            return False

        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )

            styles = getSampleStyleSheet()
            story = []

            # Stili personalizzati
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20
            )

            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            )

            # Titolo
            story.append(Paragraph(
                "RELAZIONE TECNICA DI CALCOLO",
                title_style
            ))
            story.append(Paragraph(
                "Verifica Intervento Locale su Murature Portanti",
                styles['Heading2']
            ))
            story.append(Paragraph(
                f"ai sensi delle NTC 2018 \u00a7 8.4.1",
                styles['Normal']
            ))
            story.append(Spacer(1, 20))

            # Data
            story.append(Paragraph(
                f"Data: {datetime.now().strftime('%d/%m/%Y')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 30))

            # Sezione 1 - Premessa
            story.append(Paragraph("1. PREMESSA", heading_style))
            story.append(Paragraph(
                "La presente relazione illustra le verifiche strutturali relative "
                "all'intervento locale su muratura portante esistente, con particolare "
                "riferimento alla realizzazione di nuove aperture e relativo sistema "
                "di cerchiatura metallica, secondo quanto previsto dalle NTC 2018.",
                normal_style
            ))
            story.append(Spacer(1, 10))

            # Sezione 2 - Normativa
            story.append(Paragraph("2. NORMATIVA DI RIFERIMENTO", heading_style))
            normativa = [
                "- D.M. 17/01/2018 - Norme Tecniche per le Costruzioni (NTC 2018)",
                "- Circolare n. 7/2019 - Istruzioni per l'applicazione delle NTC 2018",
                "- \u00a7 8.4.1 - Interventi locali",
                "- \u00a7 8.7.1 - Costruzioni in muratura"
            ]
            for norm in normativa:
                story.append(Paragraph(norm, normal_style))
            story.append(Spacer(1, 10))

            # Sezione 3 - Geometria
            story.append(Paragraph("3. GEOMETRIA DELLA PARETE", heading_style))

            wall = self.project_data.get('wall', {})
            wall_data = [
                ['Parametro', 'Valore', 'Unit\u00e0'],
                ['Lunghezza', f"{wall.get('length', '-')}", 'cm'],
                ['Altezza', f"{wall.get('height', '-')}", 'cm'],
                ['Spessore', f"{wall.get('thickness', '-')}", 'cm'],
            ]

            wall_table = Table(wall_data, colWidths=[6*cm, 4*cm, 3*cm])
            wall_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(wall_table)
            story.append(Spacer(1, 20))

            # Sezione 4 - Caratteristiche muratura
            story.append(Paragraph("4. CARATTERISTICHE MECCANICHE MURATURA", heading_style))

            masonry = self.project_data.get('masonry', {})
            masonry_data = [
                ['Parametro', 'Valore', 'Unit\u00e0'],
                ['Resistenza a compressione fm', f"{masonry.get('fcm', '-')}", 'MPa'],
                ['Resistenza a taglio \u03c40', f"{masonry.get('tau0', '-')}", 'MPa'],
                ['Modulo elastico E', f"{masonry.get('E', '-')}", 'MPa'],
            ]

            masonry_table = Table(masonry_data, colWidths=[6*cm, 4*cm, 3*cm])
            masonry_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(masonry_table)
            story.append(Spacer(1, 20))

            # Sezione 5 - Risultati
            if self.results:
                story.append(Paragraph("5. RISULTATI DELLE VERIFICHE", heading_style))

                orig = self.results.get('original', {})
                mod = self.results.get('modified', {})

                results_data = [
                    ['Parametro', 'Stato di Fatto', 'Stato di Progetto', 'Unit\u00e0'],
                    ['Rigidezza K', f"{orig.get('K', 0):.1f}", f"{mod.get('K', 0):.1f}", 'kN/m'],
                    ['V_t1 (fessurazione)', f"{orig.get('V_t1', 0):.1f}", f"{mod.get('V_t1', 0):.1f}", 'kN'],
                    ['V_t2 (taglio)', f"{orig.get('V_t2', 0):.1f}", f"{mod.get('V_t2', 0):.1f}", 'kN'],
                    ['V_t3 (pressoflessione)', f"{orig.get('V_t3', 0):.1f}", f"{mod.get('V_t3', 0):.1f}", 'kN'],
                    ['V_min', f"{orig.get('V_min', 0):.1f}", f"{mod.get('V_min', 0):.1f}", 'kN'],
                ]

                results_table = Table(results_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 2*cm])
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(results_table)
                story.append(Spacer(1, 20))

                # Verifica
                verif = self.results.get('verification', {})
                if verif.get('is_local', False):
                    result_text = "L'intervento risulta classificabile come INTERVENTO LOCALE ai sensi delle NTC 2018 \u00a7 8.4.1"
                    story.append(Paragraph(f"<b>{result_text}</b>", normal_style))
                else:
                    result_text = "L'intervento NON risulta classificabile come intervento locale."
                    story.append(Paragraph(f"<b>{result_text}</b>", normal_style))

            # Footer
            story.append(Spacer(1, 40))
            story.append(Paragraph(
                "Il Tecnico",
                ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)
            ))
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                "_" * 40,
                ParagraphStyle('FooterLine', parent=styles['Normal'], alignment=TA_CENTER)
            ))

            # Genera PDF
            doc.build(story)

            logger.info(f"Report generato: {filepath}")
            return True

        except Exception as e:
            logger.exception(f"Errore generazione report: {e}")
            return False

    def generate_simple_report(self, filepath: str) -> bool:
        """
        Genera un report semplice usando solo canvas

        Args:
            filepath: Percorso del file PDF

        Returns:
            True se la generazione ha avuto successo
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab non disponibile")
            return False

        try:
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4

            # Titolo
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, height - 50, "RELAZIONE TECNICA DI CALCOLO")

            c.setFont("Helvetica", 12)
            c.drawCentredString(width/2, height - 70, "Verifica Intervento Locale - NTC 2018")

            # Data
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 100, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

            # Contenuto base
            y = height - 150
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "1. DATI GEOMETRICI")

            wall = self.project_data.get('wall', {})
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(70, y, f"Lunghezza: {wall.get('length', '-')} cm")
            y -= 15
            c.drawString(70, y, f"Altezza: {wall.get('height', '-')} cm")
            y -= 15
            c.drawString(70, y, f"Spessore: {wall.get('thickness', '-')} cm")

            # Risultati
            if self.results:
                y -= 40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "2. RISULTATI")

                orig = self.results.get('original', {})
                mod = self.results.get('modified', {})

                y -= 20
                c.setFont("Helvetica", 10)
                c.drawString(70, y, f"Rigidezza originale: {orig.get('K', 0):.1f} kN/m")
                y -= 15
                c.drawString(70, y, f"Rigidezza modificata: {mod.get('K', 0):.1f} kN/m")
                y -= 15
                c.drawString(70, y, f"Resistenza originale: {orig.get('V_min', 0):.1f} kN")
                y -= 15
                c.drawString(70, y, f"Resistenza modificata: {mod.get('V_min', 0):.1f} kN")

            c.save()

            logger.info(f"Report semplice generato: {filepath}")
            return True

        except Exception as e:
            logger.exception(f"Errore generazione report: {e}")
            return False
