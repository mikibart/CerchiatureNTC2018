"""
Generatore Report PDF per Relazioni di Calcolo
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from datetime import datetime
from typing import Dict, Optional, List
import os


class ReportGenerator:
    """Generatore relazioni di calcolo in formato PDF"""

    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 2 * cm
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura stili personalizzati"""
        # Titolo principale
        self.styles.add(ParagraphStyle(
            name='TitoloPrincipale',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        ))

        # Sottotitolo
        self.styles.add(ParagraphStyle(
            name='Sottotitolo',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        ))

        # Sezione
        self.styles.add(ParagraphStyle(
            name='Sezione',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2980b9'),
            borderWidth=1,
            borderColor=colors.HexColor('#2980b9'),
            borderPadding=5
        ))

        # Testo normale
        self.styles.add(ParagraphStyle(
            name='TestoNormale',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))

        # Formula
        self.styles.add(ParagraphStyle(
            name='Formula',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=8,
            spaceBefore=8,
            fontName='Courier'
        ))

        # Risultato
        self.styles.add(ParagraphStyle(
            name='Risultato',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold'
        ))

    def generate_report(self, project: Dict, results: Dict, filepath: str) -> bool:
        """
        Genera relazione completa in PDF

        Args:
            project: Dati progetto (geometria, materiali, carichi)
            results: Risultati dei calcoli
            filepath: Percorso file PDF di output

        Returns:
            bool: True se generato con successo
        """
        try:
            # Assicura estensione
            if not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'

            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )

            # Costruisci contenuto
            story = []

            # Intestazione
            story.extend(self._create_header(project))

            # Dati progetto
            story.extend(self._create_project_info(project))

            # Geometria muro
            story.extend(self._create_geometry_section(project))

            # Materiali
            story.extend(self._create_materials_section(project))

            # Aperture
            if project.get('openings'):
                story.extend(self._create_openings_section(project))

            # Carichi
            story.extend(self._create_loads_section(project))

            # Calcoli e verifiche
            story.extend(self._create_calculations_section(results))

            # Conclusioni
            story.extend(self._create_conclusions_section(results))

            # Footer
            story.extend(self._create_footer())

            # Genera PDF
            doc.build(story)
            return True

        except Exception as e:
            print(f"Errore generazione report: {e}")
            return False

    def _create_header(self, project: Dict) -> List:
        """Crea intestazione documento"""
        elements = []

        elements.append(Paragraph(
            "RELAZIONE DI CALCOLO",
            self.styles['TitoloPrincipale']
        ))

        elements.append(Paragraph(
            "Verifica Intervento Locale su Muratura Portante",
            self.styles['Sottotitolo']
        ))

        elements.append(Paragraph(
            "secondo NTC 2018 e Circolare n. 7/2019",
            self.styles['Sottotitolo']
        ))

        elements.append(Spacer(1, 20))

        return elements

    def _create_project_info(self, project: Dict) -> List:
        """Crea sezione informazioni progetto"""
        elements = []

        elements.append(Paragraph("1. DATI GENERALI", self.styles['Sezione']))

        info = project.get('project_info', {})

        data = [
            ['Progetto:', info.get('name', 'Non specificato')],
            ['Localita\':', info.get('location', 'Non specificata')],
            ['Committente:', info.get('client', 'Non specificato')],
            ['Progettista:', info.get('engineer', 'Arch. Michelangelo Bartolotta')],
            ['Data:', datetime.now().strftime('%d/%m/%Y')],
        ]

        table = Table(data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    def _create_geometry_section(self, project: Dict) -> List:
        """Crea sezione geometria muro"""
        elements = []

        elements.append(Paragraph("2. GEOMETRIA PARETE", self.styles['Sezione']))

        wall = project.get('wall_data', {})

        elements.append(Paragraph(
            f"La parete oggetto di verifica presenta le seguenti caratteristiche geometriche:",
            self.styles['TestoNormale']
        ))

        data = [
            ['Parametro', 'Valore', 'Unita\''],
            ['Lunghezza (L)', f"{wall.get('length', 0)}", 'cm'],
            ['Altezza (H)', f"{wall.get('height', 0)}", 'cm'],
            ['Spessore (t)', f"{wall.get('thickness', 0)}", 'cm'],
        ]

        table = Table(data, colWidths=[6*cm, 5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    def _create_materials_section(self, project: Dict) -> List:
        """Crea sezione materiali"""
        elements = []

        elements.append(Paragraph("3. CARATTERISTICHE MECCANICHE MURATURA", self.styles['Sezione']))

        masonry = project.get('masonry_data', {})

        elements.append(Paragraph(
            f"Tipologia muraria: <b>{masonry.get('type', 'Non specificata')}</b>",
            self.styles['TestoNormale']
        ))

        elements.append(Paragraph(
            "Parametri meccanici secondo Tab. C8.5.I della Circolare n. 7/2019:",
            self.styles['TestoNormale']
        ))

        data = [
            ['Parametro', 'Simbolo', 'Valore', 'Unita\''],
            ['Resistenza media compressione', 'f_cm', f"{masonry.get('fcm', 0):.2f}", 'N/mm2'],
            ['Resistenza media taglio', 'tau_0', f"{masonry.get('tau0', 0):.3f}", 'N/mm2'],
            ['Modulo elastico', 'E', f"{masonry.get('E', 0)}", 'N/mm2'],
            ['Fattore di confidenza', 'FC', f"{masonry.get('FC', 1.35):.2f}", '-'],
        ]

        table = Table(data, colWidths=[7*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    def _create_openings_section(self, project: Dict) -> List:
        """Crea sezione aperture"""
        elements = []

        elements.append(Paragraph("4. APERTURE", self.styles['Sezione']))

        openings = project.get('openings', [])

        if not openings:
            elements.append(Paragraph(
                "Nessuna apertura presente nella parete.",
                self.styles['TestoNormale']
            ))
        else:
            elements.append(Paragraph(
                f"La parete presenta n. {len(openings)} apertura/e:",
                self.styles['TestoNormale']
            ))

            data = [['N.', 'Tipo', 'Larghezza (cm)', 'Altezza (cm)', 'Posizione X (cm)', 'Stato']]

            for i, opening in enumerate(openings, 1):
                stato = "Esistente" if opening.get('existing', False) else "Nuova"
                data.append([
                    str(i),
                    opening.get('type', 'Rettangolare'),
                    str(opening.get('width', 0)),
                    str(opening.get('height', 0)),
                    str(opening.get('x', 0)),
                    stato
                ])

            table = Table(data, colWidths=[1.5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))

            elements.append(table)

        elements.append(Spacer(1, 15))
        return elements

    def _create_loads_section(self, project: Dict) -> List:
        """Crea sezione carichi"""
        elements = []

        elements.append(Paragraph("5. CARICHI AGENTI", self.styles['Sezione']))

        loads = project.get('loads', {})

        data = [
            ['Carico', 'Valore', 'Unita\''],
            ['Carico verticale (N)', f"{loads.get('vertical', 0):.1f}", 'kN'],
            ['Eccentricita\' (e)', f"{loads.get('eccentricity', 0):.1f}", 'cm'],
        ]

        table = Table(data, colWidths=[6*cm, 5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    def _create_calculations_section(self, results: Dict) -> List:
        """Crea sezione calcoli e verifiche"""
        elements = []

        elements.append(Paragraph("6. VERIFICHE DI SICUREZZA", self.styles['Sezione']))

        elements.append(Paragraph(
            "Le verifiche sono condotte secondo NTC 2018 par. 8.7.1.5 per la muratura "
            "e par. 8.4.1 per gli interventi locali.",
            self.styles['TestoNormale']
        ))

        # Risultati muratura
        masonry_results = results.get('masonry', {})

        elements.append(Paragraph(
            "<b>6.1 Resistenze muratura</b>",
            self.styles['TestoNormale']
        ))

        data = [
            ['Verifica', 'Valore (kN)', 'Stato'],
            ['V_t1 (fessurazione diagonale)', f"{masonry_results.get('V_t1', 0):.2f}", '-'],
            ['V_t2 (con fattore forma)', f"{masonry_results.get('V_t2', 0):.2f}", '-'],
            ['V_t3 (pressoflessione)', f"{masonry_results.get('V_t3', 0):.2f}", '-'],
            ['V_Rd (resistenza di progetto)', f"{masonry_results.get('V_Rd', 0):.2f}", '-'],
        ]

        table = Table(data, colWidths=[7*cm, 4*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        # Verifica intervento locale
        if results.get('local_verification'):
            local = results['local_verification']

            elements.append(Paragraph(
                "<b>6.2 Verifica intervento locale (NTC 2018 par. 8.4.1)</b>",
                self.styles['TestoNormale']
            ))

            elements.append(Paragraph(
                f"Variazione rigidezza: {local.get('stiffness_ratio', 0):.1f}% "
                f"(limite: {local.get('stiffness_limit', 15)}%)",
                self.styles['TestoNormale']
            ))

            elements.append(Paragraph(
                f"Variazione resistenza: {local.get('strength_ratio', 0):.1f}% "
                f"(limite: {local.get('strength_limit', 15)}%)",
                self.styles['TestoNormale']
            ))

        elements.append(Spacer(1, 15))
        return elements

    def _create_conclusions_section(self, results: Dict) -> List:
        """Crea sezione conclusioni"""
        elements = []

        elements.append(Paragraph("7. CONCLUSIONI", self.styles['Sezione']))

        verification_ok = results.get('verification_passed', False)

        if verification_ok:
            elements.append(Paragraph(
                "Sulla base dei calcoli effettuati, l'intervento proposto risulta <b>VERIFICATO</b> "
                "secondo le prescrizioni delle NTC 2018 e della Circolare applicativa n. 7/2019.",
                self.styles['TestoNormale']
            ))

            elements.append(Paragraph(
                "ESITO: VERIFICA POSITIVA",
                self.styles['Risultato']
            ))
        else:
            elements.append(Paragraph(
                "Sulla base dei calcoli effettuati, l'intervento proposto <b>NON RISULTA VERIFICATO</b>. "
                "Si consiglia di rivedere le dimensioni degli elementi di rinforzo o la geometria dell'apertura.",
                self.styles['TestoNormale']
            ))

            elements.append(Paragraph(
                "ESITO: VERIFICA NEGATIVA - RIVEDERE PROGETTO",
                ParagraphStyle(
                    'RisultatoNegativo',
                    parent=self.styles['Risultato'],
                    textColor=colors.HexColor('#e74c3c')
                )
            ))

        elements.append(Spacer(1, 20))
        return elements

    def _create_footer(self) -> List:
        """Crea footer documento"""
        elements = []

        elements.append(Spacer(1, 30))

        elements.append(Paragraph(
            f"Relazione generata il {datetime.now().strftime('%d/%m/%Y alle ore %H:%M')}",
            ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))

        elements.append(Paragraph(
            "Software: Calcolatore Cerchiature NTC 2018 - Arch. Michelangelo Bartolotta",
            ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))

        return elements

    def generate_summary(self, results: Dict, filepath: str) -> bool:
        """Genera report sintetico (una pagina)"""
        try:
            if not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'

            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4

            # Titolo
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 50, "RIEPILOGO VERIFICA")

            # Data
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 80, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

            # Risultati principali
            y = height - 120
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Risultati calcolo:")

            y -= 25
            c.setFont("Helvetica", 10)

            masonry = results.get('masonry', {})
            c.drawString(70, y, f"V_t1 = {masonry.get('V_t1', 0):.2f} kN")
            y -= 18
            c.drawString(70, y, f"V_t2 = {masonry.get('V_t2', 0):.2f} kN")
            y -= 18
            c.drawString(70, y, f"V_t3 = {masonry.get('V_t3', 0):.2f} kN")
            y -= 18
            c.drawString(70, y, f"V_Rd = {masonry.get('V_Rd', 0):.2f} kN")

            # Esito
            y -= 40
            c.setFont("Helvetica-Bold", 14)
            if results.get('verification_passed', False):
                c.setFillColorRGB(0.15, 0.68, 0.38)  # Verde
                c.drawCentredString(width/2, y, "VERIFICA POSITIVA")
            else:
                c.setFillColorRGB(0.91, 0.30, 0.24)  # Rosso
                c.drawCentredString(width/2, y, "VERIFICA NEGATIVA")

            c.save()
            return True

        except Exception as e:
            print(f"Errore generazione summary: {e}")
            return False
