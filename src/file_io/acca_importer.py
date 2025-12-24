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

    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.filepath: Optional[Path] = None

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
        """Importa aperture (fori)"""
        openings = []
        rows = self._fetch_all('Fori')

        for row in rows:
            opening = Opening.from_acca(row)
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
