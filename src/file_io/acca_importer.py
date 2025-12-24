"""
Importatore file ACCA iEM
Legge file .iEM (database SQLite) di ACCA Calcolus-Cerchiatura
e li converte nel formato interno del software
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from core.models.project import Project, ProjectInfo, CalculationSettings
from core.models.wall import Wall, WallGeometry, WallMaterials
from core.models.opening import Opening
from core.models.masonry_pier import (
    MasonryPier, MasonryPierCollection, CapacityCurve, CapacityCurvePoint
)
from core.models.verifications import (
    VerificationResults, ResistanceVerification, StiffnessVerification,
    DisplacementVerification, BendingVerification, ShearVerification
)
from core.models.loads import LoadCollection, LoadCase, NodalLoad, LinearLoad

logger = logging.getLogger(__name__)


class ACCAImporter:
    """
    Importatore per file ACCA iEM (SQLite database)

    Supporta l'importazione completa di:
    - Dati generali progetto
    - Geometria muro e setti
    - Aperture (fori) con cerchiature
    - Materiali
    - Maschi murari
    - Curve di capacità
    - Carichi
    - Verifiche
    - Elementi FEM (nodi, beam, shell)
    """

    # Mappatura TipologiaPrflt ACCA -> serie profili
    ACCA_PROFILE_SERIES = {
        11001: 'HEA',   # Serie HEA
        11002: 'HEB',   # Serie HEB
        11003: 'HEM',   # Serie HEM
        11004: 'IPE',   # Serie IPE
        11005: 'IPN',   # Serie IPN
        11006: 'UPN',   # Serie UPN
        11007: 'UPE',   # Serie UPE
        11008: 'L',     # Angolari
        11009: 'T',     # Profili T
        11010: 'RHS',   # Tubolari rettangolari
        11011: 'CHS',   # Tubolari circolari
    }

    # Profili HEA comuni con proprietà (Ix in cm⁴, Wpl in cm³)
    HEA_PROFILES = {
        100: {'name': 'HEA 100', 'Ix': 349, 'Wpl': 83.0, 'h': 96},
        120: {'name': 'HEA 120', 'Ix': 606, 'Wpl': 119.5, 'h': 114},
        140: {'name': 'HEA 140', 'Ix': 1033, 'Wpl': 173.5, 'h': 133},
        160: {'name': 'HEA 160', 'Ix': 1673, 'Wpl': 245.0, 'h': 152},
        180: {'name': 'HEA 180', 'Ix': 2510, 'Wpl': 325.0, 'h': 171},
        200: {'name': 'HEA 200', 'Ix': 3692, 'Wpl': 429.5, 'h': 190},
        220: {'name': 'HEA 220', 'Ix': 5410, 'Wpl': 568.5, 'h': 210},
        240: {'name': 'HEA 240', 'Ix': 7763, 'Wpl': 744.6, 'h': 230},
        260: {'name': 'HEA 260', 'Ix': 10450, 'Wpl': 919.8, 'h': 250},
        280: {'name': 'HEA 280', 'Ix': 13670, 'Wpl': 1112, 'h': 270},
        300: {'name': 'HEA 300', 'Ix': 18260, 'Wpl': 1383, 'h': 290},
    }

    # Profili HEB comuni con proprietà (Ix in cm⁴, Wpl in cm³)
    HEB_PROFILES = {
        100: {'name': 'HEB 100', 'Ix': 450, 'Wpl': 104.2, 'h': 100},
        120: {'name': 'HEB 120', 'Ix': 864, 'Wpl': 165.2, 'h': 120},
        140: {'name': 'HEB 140', 'Ix': 1509, 'Wpl': 245.4, 'h': 140},
        160: {'name': 'HEB 160', 'Ix': 2492, 'Wpl': 354.0, 'h': 160},
        180: {'name': 'HEB 180', 'Ix': 3831, 'Wpl': 481.4, 'h': 180},
        200: {'name': 'HEB 200', 'Ix': 5696, 'Wpl': 642.5, 'h': 200},
        220: {'name': 'HEB 220', 'Ix': 8091, 'Wpl': 827.0, 'h': 220},
        240: {'name': 'HEB 240', 'Ix': 11260, 'Wpl': 1053, 'h': 240},
        260: {'name': 'HEB 260', 'Ix': 14920, 'Wpl': 1283, 'h': 260},
        280: {'name': 'HEB 280', 'Ix': 19270, 'Wpl': 1534, 'h': 280},
        300: {'name': 'HEB 300', 'Ix': 25170, 'Wpl': 1869, 'h': 300},
    }

    # Profili IPE comuni con proprietà (Ix in cm⁴, Wpl in cm³)
    IPE_PROFILES = {
        100: {'name': 'IPE 100', 'Ix': 171, 'Wpl': 39.4, 'h': 100},
        120: {'name': 'IPE 120', 'Ix': 318, 'Wpl': 60.7, 'h': 120},
        140: {'name': 'IPE 140', 'Ix': 541, 'Wpl': 88.3, 'h': 140},
        160: {'name': 'IPE 160', 'Ix': 869, 'Wpl': 124, 'h': 160},
        180: {'name': 'IPE 180', 'Ix': 1317, 'Wpl': 166, 'h': 180},
        200: {'name': 'IPE 200', 'Ix': 1943, 'Wpl': 221, 'h': 200},
        220: {'name': 'IPE 220', 'Ix': 2772, 'Wpl': 285, 'h': 220},
        240: {'name': 'IPE 240', 'Ix': 3892, 'Wpl': 367, 'h': 240},
        270: {'name': 'IPE 270', 'Ix': 5790, 'Wpl': 484, 'h': 270},
        300: {'name': 'IPE 300', 'Ix': 8356, 'Wpl': 628, 'h': 300},
        330: {'name': 'IPE 330', 'Ix': 11770, 'Wpl': 804, 'h': 330},
        360: {'name': 'IPE 360', 'Ix': 16270, 'Wpl': 1019, 'h': 360},
    }

    # Profili UPN comuni con proprietà (Ix in cm⁴, Wpl in cm³)
    UPN_PROFILES = {
        80: {'name': 'UPN 80', 'Ix': 106, 'Wpl': 31.4, 'h': 80},
        100: {'name': 'UPN 100', 'Ix': 206, 'Wpl': 49.2, 'h': 100},
        120: {'name': 'UPN 120', 'Ix': 364, 'Wpl': 72.4, 'h': 120},
        140: {'name': 'UPN 140', 'Ix': 605, 'Wpl': 103, 'h': 140},
        160: {'name': 'UPN 160', 'Ix': 925, 'Wpl': 138, 'h': 160},
        180: {'name': 'UPN 180', 'Ix': 1350, 'Wpl': 179, 'h': 180},
        200: {'name': 'UPN 200', 'Ix': 1910, 'Wpl': 228, 'h': 200},
        220: {'name': 'UPN 220', 'Ix': 2690, 'Wpl': 292, 'h': 220},
        240: {'name': 'UPN 240', 'Ix': 3600, 'Wpl': 358, 'h': 240},
        260: {'name': 'UPN 260', 'Ix': 4820, 'Wpl': 442, 'h': 260},
        280: {'name': 'UPN 280', 'Ix': 6280, 'Wpl': 535, 'h': 280},
        300: {'name': 'UPN 300', 'Ix': 8030, 'Wpl': 638, 'h': 300},
    }

    # Dizionario per selezionare la serie giusta
    PROFILE_DATABASES = {
        'HEA': HEA_PROFILES,
        'HEB': HEB_PROFILES,
        'IPE': IPE_PROFILES,
        'UPN': UPN_PROFILES,
    }

    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.filepath: Optional[Path] = None

    def _map_acca_profile(self, profile_id: int, tipologia_prflt: int = 11001) -> Dict[str, Any]:
        """
        Converte un ID profilo ACCA in nome profilo standard e proprietà.

        ACCA usa un sistema di codifica dove:
        - TipologiaPrflt indica la serie (11001=HEA, 11002=HEB, etc.)
        - L'ID profilo è un riferimento interno al catalogo ACCA

        Strategia di mappatura:
        1. Determina la serie dal TipologiaPrflt
        2. Cerca il profilo con altezza corrispondente (es. 217 -> h~200mm)
        3. Se non trovato, usa il profilo più vicino

        Args:
            profile_id: ID profilo ACCA (es. 217)
            tipologia_prflt: Tipo serie ACCA (es. 11001 per HEA)

        Returns:
            Dizionario con name, Ix, Wpl, h del profilo
        """
        # Determina la serie
        series_name = self.ACCA_PROFILE_SERIES.get(tipologia_prflt, 'HEA')
        profile_db = self.PROFILE_DATABASES.get(series_name, self.HEA_PROFILES)

        # Cerca prima per altezza esatta (ACCA spesso usa l'altezza come ID)
        # Es: ID 217 potrebbe indicare altezza ~200mm
        estimated_height = (profile_id // 10) * 10  # Arrotonda alle decine

        # Cerca il profilo più vicino per altezza
        best_match = None
        min_diff = float('inf')

        for size, props in profile_db.items():
            diff = abs(size - estimated_height)
            if diff < min_diff:
                min_diff = diff
                best_match = props

        if best_match:
            logger.debug(f"Profilo ACCA {profile_id} mappato a {best_match['name']}")
            return best_match.copy()

        # Fallback: primo profilo disponibile
        first_profile = next(iter(profile_db.values()))
        logger.warning(f"Profilo ACCA {profile_id} non mappato, uso default {first_profile['name']}")
        return first_profile.copy()

    def _get_profile_from_sezioni(self, sezione_id: int) -> Optional[Dict[str, Any]]:
        """
        Cerca le proprietà del profilo nella tabella Sezioni di ACCA.

        Args:
            sezione_id: ID della sezione nella tabella Sezioni

        Returns:
            Dizionario con proprietà o None se non trovato
        """
        if not self._table_exists('Sezioni'):
            return None

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Sezioni WHERE ID = ?", (sezione_id,))
        columns = [d[0] for d in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        data = dict(zip(columns, row))

        # Estrai proprietà rilevanti
        return {
            'name': data.get('Sigla', f'Sezione {sezione_id}'),
            'Ix': data.get('Ix', 0),  # Momento d'inerzia asse forte (cm⁴)
            'Iy': data.get('Iy', 0),  # Momento d'inerzia asse debole (cm⁴)
            'Wpl': data.get('Wpl', 0),  # Modulo resistente plastico (cm³)
            'A': data.get('A', 0),  # Area sezione (cm²)
            'h': data.get('H', 0),  # Altezza profilo (mm)
            'b': data.get('B', 0),  # Larghezza profilo (mm)
            'tipologia': data.get('TipologiaPrflt', 11001)
        }

    def _resolve_profile(self, profile_id: int, tipologia_prflt: int = 11001) -> Dict[str, Any]:
        """
        Risolve un profilo ACCA cercando prima in Sezioni, poi usando la mappatura.

        Args:
            profile_id: ID profilo ACCA
            tipologia_prflt: Tipo serie ACCA

        Returns:
            Dizionario con proprietà del profilo
        """
        # Prima prova dalla tabella Sezioni
        sezioni_props = self._get_profile_from_sezioni(profile_id)
        if sezioni_props and sezioni_props.get('Ix', 0) > 0:
            logger.info(f"Profilo {profile_id} trovato in tabella Sezioni: {sezioni_props['name']}")
            return sezioni_props

        # Altrimenti usa la mappatura interna
        return self._map_acca_profile(profile_id, tipologia_prflt)

    def import_file(self, filepath: str) -> Optional[Project]:
        """
        Importa un file ACCA iEM e restituisce un oggetto Project

        Args:
            filepath: Percorso del file .iEM

        Returns:
            Project importato o None in caso di errore
        """
        self.filepath = Path(filepath)

        if not self.filepath.exists():
            logger.error(f"File non trovato: {filepath}")
            return None

        try:
            # Apri connessione SQLite
            self.conn = sqlite3.connect(str(self.filepath))
            self.conn.row_factory = sqlite3.Row  # Accesso per nome colonna

            # Importa tutti i dati
            project = Project()
            project.source_file = str(self.filepath)
            project.version = "2.0"

            # 1. Dati generali
            project.info = self._import_project_info()

            # 2. Impostazioni calcolo
            project.settings = self._import_settings()

            # 3. Materiali
            project.materials = self._import_materials()

            # 4. Muro e setti
            project.wall = self._import_wall()

            # 5. Aperture
            project.openings = self._import_openings()

            # 6. Maschi murari e curve di capacità
            project.masonry_piers = self._import_masonry_piers()

            # 7. Carichi
            project.loads = self._import_loads()

            # 8. Verifiche
            project.verification_results = self._import_verifications()

            # 9. Elementi FEM
            project.fem_nodes = self._import_nodes()
            project.fem_beams = self._import_beams()
            project.fem_shells = self._import_shells()

            self.conn.close()
            logger.info(f"Importazione completata: {filepath}")

            return project

        except sqlite3.Error as e:
            logger.error(f"Errore database SQLite: {e}")
            if self.conn:
                self.conn.close()
            return None
        except Exception as e:
            logger.exception(f"Errore importazione: {e}")
            if self.conn:
                self.conn.close()
            return None

    def _table_exists(self, table_name: str) -> bool:
        """Verifica se una tabella esiste nel database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def _fetch_all(self, table_name: str) -> List[Dict]:
        """Legge tutti i record di una tabella"""
        if not self._table_exists(table_name):
            return []

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def _fetch_one(self, table_name: str) -> Optional[Dict]:
        """Legge il primo record di una tabella"""
        if not self._table_exists(table_name):
            return None

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()

        return dict(zip(columns, row)) if row else None

    def _import_project_info(self) -> ProjectInfo:
        """Importa informazioni progetto"""
        data = self._fetch_one('DatiGenerali')
        if data:
            return ProjectInfo.from_acca(data)
        return ProjectInfo()

    def _import_settings(self) -> CalculationSettings:
        """Importa impostazioni di calcolo"""
        data = self._fetch_one('Impostazioni')
        if data:
            return CalculationSettings.from_acca(data)
        return CalculationSettings()

    def _import_materials(self) -> Dict[int, Dict]:
        """Importa materiali"""
        materials = {}
        rows = self._fetch_all('Materiali')

        for row in rows:
            mat_id = row.get('ID', 0)
            mat_type = row.get('Tipo', 0)

            material = {
                'id': mat_id,
                'type': mat_type,  # 0=CA, 1=Acciaio, 3=Muratura
                'name': row.get('Sigla', ''),
                'density': row.get('Ps', 0) / 1000,  # N/m³ -> kN/m³
                'poisson': row.get('Nu', 0.2),
                'elastic_modulus': row.get('ME', 0),  # N/mm²
                'safety_factor': row.get('CS', 1.0)
            }

            # Parametri specifici per tipo
            if mat_type == 0:  # Calcestruzzo
                material.update({
                    'fck': row.get('Fck', 0),
                    'eps_cu': row.get('EpsCu', 0.0035),
                    'fcd': row.get('Fcd', 0)
                })
            elif mat_type == 1:  # Acciaio
                material.update({
                    'fyk': row.get('Fyk', 0),
                    'ftk': row.get('Ftk', 0),
                    'gamma_m2': row.get('GammaM2', 1.05)
                })
            elif mat_type == 3:  # Muratura
                material.update({
                    'fmk': row.get('Fmk', 0),      # Resistenza a compressione
                    'fvk0': row.get('Fvk0', 0),    # Resistenza a taglio base
                    'tau0': row.get('Tau0', 0),   # Tensione tangenziale
                    'ductility': row.get('KDttlt', 1.5),
                    'shear_failure': row.get('RotturaTgMsc', 3)
                })

            materials[mat_id] = material

        return materials

    def _import_wall(self) -> Optional[Wall]:
        """Importa geometria muro"""
        setti = self._fetch_all('SettiMuri')
        dati_muro = self._fetch_one('DatiGeneraliMuro')

        if not setti and not dati_muro:
            return None

        return Wall.from_acca(setti, dati_muro or {})

    def _import_openings(self) -> List[Opening]:
        """Importa aperture (fori) con risoluzione profili"""
        openings = []
        rows = self._fetch_all('Fori')

        for row in rows:
            opening = Opening.from_acca(row)

            # Risolvi profili piattabanda
            lintel_type = row.get('TipologiaPrfltPittabanda', 11001)
            lintel_id = row.get('ProfilatoPiattabanda', 0)
            if lintel_id > 0:
                lintel_props = self._resolve_profile(lintel_id, lintel_type)
                opening.profiles.lintel_profile_name = lintel_props.get('name', '')
                opening.profiles.lintel_Ix = lintel_props.get('Ix', 0)
                opening.profiles.lintel_Wpl = lintel_props.get('Wpl', 0)
                logger.info(f"Apertura {opening.id}: piattabanda -> {opening.profiles.lintel_profile_name}")

            # Risolvi profili piedritti
            jamb_type = row.get('TipologiaPrfltPiedritti', 11001)
            jamb_id = row.get('ProfilatoPiedritti', 0)
            if jamb_id > 0:
                jamb_props = self._resolve_profile(jamb_id, jamb_type)
                opening.profiles.jamb_profile_name = jamb_props.get('name', '')
                opening.profiles.jamb_Ix = jamb_props.get('Ix', 0)
                opening.profiles.jamb_Wpl = jamb_props.get('Wpl', 0)
                logger.info(f"Apertura {opening.id}: piedritti -> {opening.profiles.jamb_profile_name}")

            # Risolvi profili base
            base_type = row.get('TipologiaPrfltBase', 11001)
            base_id = row.get('ProfilatoBase', 0)
            if base_id > 0:
                base_props = self._resolve_profile(base_id, base_type)
                opening.profiles.base_profile_name = base_props.get('name', '')

            openings.append(opening)

        return openings

    def _import_masonry_piers(self) -> MasonryPierCollection:
        """Importa maschi murari e curve di capacità"""
        collection = MasonryPierCollection()

        # Maschi
        maschi_rows = self._fetch_all('Maschi')
        for row in maschi_rows:
            pier = MasonryPier.from_acca(row)
            collection.add_pier(pier)

        # Curve di capacità
        curve_rows = self._fetch_all('CurvaDiCapacita')

        # Raggruppa per IDCurva
        curves_by_id = defaultdict(list)
        for row in curve_rows:
            curve_id = row.get('IDCurva', 0)
            curves_by_id[curve_id].append(row)

        for curve_id, points in curves_by_id.items():
            curve = CapacityCurve.from_acca(points)
            collection.add_capacity_curve(curve)

        return collection

    def _import_loads(self) -> LoadCollection:
        """Importa carichi"""
        collection = LoadCollection()

        # Casi di carico
        carichi_rows = self._fetch_all('Carichi')
        for row in carichi_rows:
            load_case = LoadCase.from_acca(row)
            collection.add_load_case(load_case)

        # Carichi nodali
        nodal_rows = self._fetch_all('CarichiNodi')
        for row in nodal_rows:
            nodal_load = NodalLoad.from_acca(row)
            collection.add_nodal_load(nodal_load)

        # Carichi lineari
        linear_rows = self._fetch_all('ForzeLineari')
        for row in linear_rows:
            linear_load = LinearLoad.from_acca(row)
            collection.add_linear_load(linear_load)

        return collection

    def _import_verifications(self) -> VerificationResults:
        """Importa risultati verifiche"""
        results = VerificationResults()

        # Verifica resistenza globale
        res_data = self._fetch_one('VerificaResistenza')
        if res_data:
            results.resistance = ResistanceVerification.from_acca(res_data)

        # Verifica rigidezza
        stiff_data = self._fetch_one('VerifcaRigidezza')
        if stiff_data:
            results.stiffness = StiffnessVerification.from_acca(stiff_data)

        # Verifica spostamento
        disp_data = self._fetch_one('VerificaSpostamento')
        if disp_data:
            results.displacement = DisplacementVerification.from_acca(disp_data)

        # Verifiche pressoflessione
        bending_rows = self._fetch_all('VerificaPressoflessione')
        for row in bending_rows:
            results.bending_verifications.append(
                BendingVerification.from_acca(row)
            )

        # Verifiche taglio
        shear_rows = self._fetch_all('VerificaTaglio')
        for row in shear_rows:
            results.shear_verifications.append(
                ShearVerification.from_acca(row)
            )

        return results

    def _import_nodes(self) -> List[Dict]:
        """Importa nodi FEM"""
        nodes = []
        rows = self._fetch_all('Nodi')

        for row in rows:
            nodes.append({
                'id': row.get('Id', 0),
                'x': row.get('Px', 0),
                'y': row.get('Py', 0),
                'z': row.get('Pz', 0)
            })

        return nodes

    def _import_beams(self) -> List[Dict]:
        """Importa elementi beam FEM"""
        beams = []
        rows = self._fetch_all('Beam')

        for row in rows:
            beams.append({
                'id': row.get('Id', 0),
                'opening_id': row.get('ForoID', 0),
                'type': row.get('Tipo', 0),
                'material_id': row.get('Materiale', 0),
                'section_id': row.get('Sezione', 0),
                'reinforcement_id': row.get('ArmaturaBeam'),
                'capacity_curve_id': row.get('IdCurvaCapacita')
            })

        return beams

    def _import_shells(self) -> List[Dict]:
        """Importa elementi shell FEM"""
        shells = []
        rows = self._fetch_all('Shell')

        for row in rows:
            shells.append({
                'id': row.get('Id', 0),
                'material_id': row.get('Materiale', 0),
                'node1': row.get('Nodo1', 0),
                'node2': row.get('Nodo2', 0),
                'node3': row.get('Nodo3', 0)
            })

        return shells

    def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene informazioni su un file senza importarlo completamente

        Args:
            filepath: Percorso del file .iEM

        Returns:
            Dizionario con informazioni base del progetto
        """
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()

            info = {
                'filepath': filepath,
                'filename': Path(filepath).name,
                'is_valid': True
            }

            # Dati generali
            cursor.execute("SELECT * FROM DatiGenerali LIMIT 1")
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            if row:
                data = dict(zip(columns, row))
                info['project_name'] = data.get('Oggetto', 'N/D')
                info['municipality'] = data.get('Comune', '')
                info['province'] = data.get('Provincia', '')

            # Conta elementi
            cursor.execute("SELECT COUNT(*) FROM Fori")
            info['num_openings'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM SettiMuri")
            info['num_wall_segments'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Maschi")
            info['num_piers'] = cursor.fetchone()[0]

            # Versione
            cursor.execute("SELECT * FROM VersionInfo LIMIT 1")
            row = cursor.fetchone()
            if row:
                info['app_version'] = row[0]
                info['doc_version'] = row[1]

            conn.close()
            return info

        except Exception as e:
            logger.error(f"Errore lettura info file: {e}")
            return {'filepath': filepath, 'is_valid': False, 'error': str(e)}


def import_acca_file(filepath: str) -> Optional[Project]:
    """
    Funzione helper per importazione rapida

    Args:
        filepath: Percorso del file .iEM ACCA

    Returns:
        Project importato o None
    """
    importer = ACCAImporter()
    return importer.import_file(filepath)
