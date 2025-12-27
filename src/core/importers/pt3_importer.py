"""
Importatore file PT3 (Particolare 3)
Importa file progetto da software cerchiature PT3

Formato PT3 v34:
- Linea 1: Commento versione
- Linea 2: Numero versione
- Linea 3: Tipologia (cerchiatura vano)
- Linea 4: Dimensioni parete (L, H, t, ...)
- Linea 10: Tipo muratura
- Linee 11-28: Proprietà meccaniche muratura
- Linee 128+: Aperture e profili
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PT3WallData:
    """Dati parete da file PT3."""
    length: float  # cm
    height: float  # cm
    thickness: float  # cm


@dataclass
class PT3MasonryData:
    """Dati muratura da file PT3."""
    type_name: str
    fcd: float  # MPa - resistenza a compressione
    tau0: float  # MPa - resistenza a taglio
    E: float  # MPa - modulo elastico
    G: float  # MPa - modulo taglio
    gamma_m: float  # coefficiente parziale


@dataclass
class PT3OpeningData:
    """Dati apertura da file PT3."""
    x: float  # posizione x (cm)
    y: float  # posizione y dal basso (cm)
    width: float  # larghezza (cm)
    height: float  # altezza (cm)
    opening_type: str  # Rettangolare, Circolare, Arco
    profile: str  # es. HE120A
    n_profiles: int  # numero profili per lato


@dataclass
class PT3ProjectData:
    """Dati completi progetto PT3."""
    version: int
    wall: PT3WallData
    masonry: PT3MasonryData
    openings: List[PT3OpeningData]
    # Risultati originali per confronto
    original_results: Dict[str, float]


class PT3Importer:
    """Importatore file PT3."""

    # Mappatura tipi muratura PT3 -> CerchiatureNTC2018
    MASONRY_MAP = {
        'in mattoni pieni e malta di calce': 'Muratura in mattoni pieni e malta di calce',
        'in mattoni semipieni': 'Muratura in mattoni semipieni',
        'in blocchi di tufo': 'Muratura in blocchi di tufo',
        'in pietra a spacco': 'Muratura a conci sbozzati',
        'in blocchi di cls': 'Muratura in blocchi di calcestruzzo',
    }

    def __init__(self):
        self.lines: List[str] = []
        self.current_line: int = 0

    def parse_file(self, filepath: str) -> PT3ProjectData:
        """
        Legge e parsa un file PT3.

        Args:
            filepath: Percorso del file PT3

        Returns:
            PT3ProjectData con tutti i dati del progetto
        """
        with open(filepath, 'r', encoding='latin-1') as f:
            self.lines = [line.rstrip() for line in f.readlines()]

        self.current_line = 0

        # Parse header
        version = self._parse_version()

        # Parse wall dimensions
        wall = self._parse_wall()

        # Parse masonry data
        masonry = self._parse_masonry()

        # Parse openings
        openings = self._parse_openings()

        # Parse original results if available
        original_results = self._parse_results()

        return PT3ProjectData(
            version=version,
            wall=wall,
            masonry=masonry,
            openings=openings,
            original_results=original_results
        )

    def _parse_version(self) -> int:
        """Legge la versione del file."""
        # Linea 1: /Versione file/
        # Linea 2: numero versione
        self.current_line = 1  # Salta commento
        version_str = self.lines[self.current_line].strip()
        return int(version_str)

    def _parse_wall(self) -> PT3WallData:
        """Legge i dati della parete."""
        # Linea 4: L H t ... (6 valori separati da spazi)
        self.current_line = 3
        values = self._parse_floats(self.lines[self.current_line])

        return PT3WallData(
            length=values[0],
            height=values[1],
            thickness=values[2]
        )

    def _parse_masonry(self) -> PT3MasonryData:
        """Legge i dati della muratura."""
        # Linea 10: tipo muratura (stringa)
        # Linee 11-28: proprietà meccaniche
        # Struttura PT3 v34:
        #   Linea 11: fcd (resistenza a compressione di calcolo)
        #   Linea 12: fcm (resistenza media a compressione)
        #   Linea 13: E (modulo elastico normale)
        #   Linea 14: G (modulo elastico tangenziale) - NOTA: in PT3 G > E è possibile
        #   Linea 15: tau0d (resistenza a taglio di calcolo)
        #   Linea 16: tau0m (resistenza media a taglio)

        self.current_line = 9
        type_name = self.lines[self.current_line].strip()

        # Proprietà meccaniche - leggi con attenzione le righe corrette
        # NOTA: Nel PT3 i valori sono in daN/cm² (1 daN/cm² = 0.1 MPa)
        # E i campi E e G sembrano essere invertiti
        try:
            fcd = float(self.lines[10].strip())   # Linea 11: fcd in MPa
            # Linea 12 sembra essere un valore calcolato, non fcm
            G_raw = float(self.lines[12].strip()) # Linea 13: G in daN/cm²
            E_raw = float(self.lines[13].strip()) # Linea 14: E in daN/cm²
            tau0 = float(self.lines[14].strip())  # Linea 15: tau0 in MPa

            # Converti da daN/cm² a MPa (divide per 10)
            E_val = E_raw / 10  # 15000 daN/cm² -> 1500 MPa
            G_val = G_raw / 10  # 5000 daN/cm² -> 500 MPa

            # fcm non è direttamente nel file, usa valore NTC per il tipo
            fcm = 2.4  # Valore tipico NTC per mattoni pieni

        except (IndexError, ValueError) as e:
            print(f"Errore parsing proprietà muratura: {e}")
            fcd, fcm, E_val, G_val, tau0 = 0.5, 2.4, 1500, 500, 0.06

        # Gamma_m è tipicamente alla linea 36 o simile
        gamma_m = 2.0  # Default
        try:
            gamma_m = float(self.lines[35].strip())
        except (IndexError, ValueError):
            pass

        # Mappa il tipo muratura
        mapped_type = self._map_masonry_type(type_name)

        print(f"PT3 Muratura: tipo='{type_name}'")
        print(f"PT3 Parametri: fcd={fcd}, fcm={fcm}, E={E_val:.0f} MPa, G={G_val:.0f} MPa, tau0={tau0}")

        return PT3MasonryData(
            type_name=mapped_type,
            fcd=fcd,
            tau0=tau0,
            E=E_val,
            G=G_val,
            gamma_m=gamma_m
        )

    def _parse_openings(self) -> List[PT3OpeningData]:
        """Legge i dati delle aperture."""
        # Per file PT3 v34, usa il parsing avanzato
        return self._parse_openings_v34()

    def _parse_openings_v34(self) -> List[PT3OpeningData]:
        """
        Parsing avanzato per PT3 v34 con supporto multi-apertura.

        Struttura file PT3:
        - Linea 131: numero aperture
        - Linea 132: prima apertura (y, h, w, ?, existing_flag)
        - Linea 137: profilo prima apertura
        - Linea 307: seconda apertura (h, w, x, y, existing_flag)
        """
        openings = []

        # Dimensioni parete
        wall_values = self._parse_floats(self.lines[3])
        wall_length = wall_values[0]
        wall_height = wall_values[1]

        # Numero aperture (linea 131)
        try:
            num_openings = int(self.lines[130].strip())
            print(f"PT3: Trovate {num_openings} aperture")
        except (IndexError, ValueError):
            num_openings = 1

        # === PRIMA APERTURA (linea 132) ===
        # Formato PT3: width, height, x, y, existing_flag
        # NOTA: Nel PT3, flag 0 = esistente, flag 1 = nuova (da creare con cerchiatura)
        try:
            line_132 = self.lines[131]  # 0-indexed
            values = self._parse_floats(line_132)

            if len(values) >= 4:
                # Formato: width, height, x, y, [existing_flag]
                width = values[0]
                height = values[1]
                x_pos = values[2]
                y_pos = values[3] if values[3] > 0 else 0  # y=0 per porte
                # Nel PT3: 0 = esistente, 1 = nuova
                pt3_flag = int(values[4]) if len(values) >= 5 else 0
                existing = (pt3_flag == 0)  # Inverti: 0 nel PT3 significa esistente

                # Profilo alla linea 137 (solo se nuova apertura)
                profile = ''
                if not existing and len(self.lines) > 136:
                    profile = self.lines[136].strip()
                    if not (profile.startswith('HE') or profile.startswith('IPE') or profile.startswith('UPN')):
                        profile = 'HEA 120'

                print(f"PT3 Apertura 1: {width}x{height} @ ({x_pos:.0f}, {y_pos:.0f}), "
                      f"{'ESISTENTE' if existing else 'NUOVA con ' + profile}")

                opening = PT3OpeningData(
                    x=x_pos,
                    y=y_pos,
                    width=width,
                    height=height,
                    opening_type='Rettangolare',
                    profile=profile if not existing else '',
                    n_profiles=1 if not existing else 0
                )
                opening.existing = existing
                openings.append(opening)

        except (IndexError, ValueError) as e:
            print(f"Errore parsing apertura 1: {e}")

        # === SECONDA APERTURA (cerca linea con pattern corretto) ===
        if num_openings >= 2:
            try:
                # Cerca la seconda apertura - tipicamente dopo linea 305
                # Pattern: 5 valori con ultimo = 0 o 1
                for line_idx in range(300, min(320, len(self.lines))):
                    line = self.lines[line_idx]
                    values = self._parse_floats(line)

                    # Cerca linea con 5 valori e ultimo valore 0 o 1
                    if len(values) == 5 and values[4] in [0, 1]:
                        # Formato: width, height, x, y, existing_flag
                        width = values[0]
                        height = values[1]
                        x_pos = values[2]
                        y_pos = values[3]
                        # Nel PT3: 0 = esistente, 1 = nuova
                        pt3_flag = int(values[4])
                        existing = (pt3_flag == 0)

                        # Trova profilo nelle linee successive (se nuova apertura)
                        profile = ''
                        if not existing:
                            for prof_idx in range(line_idx + 1, min(line_idx + 10, len(self.lines))):
                                prof_line = self.lines[prof_idx].strip()
                                if prof_line.startswith('HE') or prof_line.startswith('IPE') or prof_line.startswith('UPN'):
                                    profile = prof_line
                                    break
                            if not profile:
                                profile = 'HEA 120'

                        print(f"PT3 Apertura 2: {width}x{height} @ ({x_pos:.0f}, {y_pos:.0f}), "
                              f"{'ESISTENTE' if existing else 'NUOVA con ' + profile}")

                        opening = PT3OpeningData(
                            x=x_pos,
                            y=y_pos,
                            width=width,
                            height=height,
                            opening_type='Rettangolare',
                            profile=profile,
                            n_profiles=1 if not existing else 0
                        )
                        opening.existing = existing
                        openings.append(opening)
                        break

            except (IndexError, ValueError) as e:
                print(f"Errore parsing apertura 2: {e}")

        return openings

    def _parse_openings_direct(self) -> List[PT3OpeningData]:
        """Metodo legacy per retrocompatibilità."""
        return self._parse_openings_v34()

    def _parse_results(self) -> Dict[str, float]:
        """Legge i risultati originali se presenti nel file."""
        # I risultati sono tipicamente alla fine del file
        # o nel file RTF associato
        return {}

    def _parse_floats(self, line: str) -> List[float]:
        """Estrae tutti i numeri float da una linea."""
        values = []
        parts = line.split()
        for part in parts:
            try:
                values.append(float(part))
            except ValueError:
                continue
        return values

    def _map_masonry_type(self, pt3_type: str) -> str:
        """Mappa il tipo muratura PT3 al formato CerchiatureNTC2018."""
        pt3_type_lower = pt3_type.lower().strip()

        for key, value in self.MASONRY_MAP.items():
            if key in pt3_type_lower:
                return value

        # Default
        return 'Muratura in mattoni pieni e malta di calce'

    def to_project_dict(self, data: PT3ProjectData) -> Dict[str, Any]:
        """
        Converte i dati PT3 in formato dizionario per CerchiatureNTC2018.

        Args:
            data: Dati PT3 parsati

        Returns:
            Dizionario compatibile con CerchiatureNTC2018
        """
        # Converti aperture
        openings = []
        for op in data.openings:
            # Verifica se l'apertura è esistente (attributo aggiunto dal parser)
            is_existing = getattr(op, 'existing', False)

            opening = {
                'x': op.x,
                'y': op.y,
                'width': op.width,
                'height': op.height,
                'type': op.opening_type,
                'existing': is_existing,
            }

            # Aggiungi rinforzo solo se non è un'apertura esistente
            if not is_existing and op.profile:
                opening['rinforzo'] = {
                    'tipo': 'telaio_chiuso',
                    'profilo': self._normalize_profile(op.profile),
                    'n_profili': op.n_profiles,
                    'metodo': 'A freddo'
                }
            else:
                opening['rinforzo'] = None

            openings.append(opening)

        return {
            'wall': {
                'length': data.wall.length,
                'height': data.wall.height,
                'thickness': data.wall.thickness
            },
            'masonry': {
                'type': data.masonry.type_name,
                'fcd': data.masonry.fcd,
                'tau0': data.masonry.tau0,
                'E': data.masonry.E,
                'G': data.masonry.G,
                'gamma_m': data.masonry.gamma_m
            },
            'openings': openings
        }

    def _normalize_profile(self, profile: str) -> str:
        """Normalizza il nome del profilo al formato CerchiatureNTC2018."""
        # HE120A -> HEA 120
        match = re.match(r'^HE(\d+)([AB]?)$', profile.strip())
        if match:
            size = match.group(1)
            series = match.group(2) or 'A'
            return f"HE{series} {size}"

        # IPE120 -> IPE 120
        match = re.match(r'^IPE(\d+)$', profile.strip())
        if match:
            size = match.group(1)
            return f"IPE {size}"

        # UPN120 -> UPN 120
        match = re.match(r'^UPN(\d+)$', profile.strip())
        if match:
            size = match.group(1)
            return f"UPN {size}"

        return profile


def import_pt3(filepath: str) -> Dict[str, Any]:
    """
    Funzione helper per importare un file PT3.

    Args:
        filepath: Percorso del file PT3

    Returns:
        Dizionario con dati progetto
    """
    importer = PT3Importer()
    data = importer.parse_file(filepath)
    return importer.to_project_dict(data)


if __name__ == '__main__':
    # Test import
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        data = import_pt3(filepath)
        print("Dati importati:")
        print(f"  Parete: {data['wall']['length']} x {data['wall']['height']} x {data['wall']['thickness']} cm")
        print(f"  Muratura: {data['masonry']['type']}")
        print(f"  Aperture: {len(data['openings'])}")
        for i, op in enumerate(data['openings']):
            print(f"    {i+1}. {op['width']}x{op['height']} @ ({op['x']}, {op['y']})")
            if 'rinforzo' in op:
                print(f"       Rinforzo: {op['rinforzo']['profilo']}")
