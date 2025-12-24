"""
Modello Progetto
Contenitore principale di tutti i dati
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class ProjectInfo:
    """Informazioni progetto estese"""
    # Identificazione
    name: str = ""
    description: str = ""

    # Localizzazione
    municipality: str = ""      # Comune
    province: str = ""          # Provincia
    location: str = ""          # Ubicazione/Indirizzo
    cap: str = ""               # CAP

    # Soggetti
    client: str = ""            # Committente
    engineer: str = ""          # Tecnico
    engineer_address: str = ""  # Indirizzo tecnico

    # Metadati
    date: datetime = field(default_factory=datetime.now)
    calculation_state: int = 0  # Stato del calcolo (0=non calcolato, 1=calcolato)

    @classmethod
    def from_acca(cls, data: dict) -> 'ProjectInfo':
        """Crea da dati ACCA"""
        return cls(
            name=data.get('Oggetto', ''),
            municipality=data.get('Comune', ''),
            province=data.get('Provincia', ''),
            location=data.get('Ubicazione', ''),
            client=data.get('Committente', ''),
            engineer=data.get('Tecnico', ''),
            engineer_address=data.get('IndirizzoTecnico', ''),
            cap=data.get('CAPComuneProvinciaTecnico', ''),
            calculation_state=data.get('StatoDelCalcolo', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'name': self.name,
            'description': self.description,
            'municipality': self.municipality,
            'province': self.province,
            'location': self.location,
            'cap': self.cap,
            'client': self.client,
            'engineer': self.engineer,
            'engineer_address': self.engineer_address,
            'date': self.date.isoformat() if self.date else None,
            'calculation_state': self.calculation_state
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        """Deserializza da dizionario"""
        date_str = data.get('date')
        date = datetime.fromisoformat(date_str) if date_str else datetime.now()

        return cls(
            name=data.get('name', data.get('Oggetto', '')),
            description=data.get('description', ''),
            municipality=data.get('municipality', data.get('Comune', '')),
            province=data.get('province', data.get('Provincia', '')),
            location=data.get('location', ''),
            cap=data.get('cap', ''),
            client=data.get('client', ''),
            engineer=data.get('engineer', 'Arch. Michelangelo Bartolotta'),
            engineer_address=data.get('engineer_address', ''),
            date=date,
            calculation_state=data.get('calculation_state', 0)
        )


@dataclass
class CalculationSettings:
    """Impostazioni di calcolo"""
    mesh_refinement: int = 1         # Infittimento mesh
    min_pier_height: int = 30        # Altezza minima maschio (cm)
    min_pier_length: int = 30        # Lunghezza minima maschio (cm)
    capacity_curve_on_first: bool = False  # Curva capacità sul primo maschio
    pier_height_angle: int = 0       # Angolo diffusione altezza maschi
    base_restraint: int = 0          # Vincolo piede (0=incastro, 1=cerniera)
    top_restraint: int = 0           # Vincolo testa
    user_restraint: int = 100        # Rigidezza vincolo utente (%)
    top_wall_restraint: int = 0      # Vincolo testa muro
    stiffness_tolerance: int = 15    # Tolleranza rigidezza ammissibile (%)
    auto_ductility: bool = True      # Calcolo automatico duttilità
    pier_height_wall_height: bool = True  # H maschi = H muro

    @classmethod
    def from_acca(cls, data: dict) -> 'CalculationSettings':
        """Crea da dati ACCA"""
        return cls(
            mesh_refinement=data.get('InfittimentoMesh', 1),
            min_pier_height=data.get('MaschioHmin', 30),
            min_pier_length=data.get('MaschioLmin', 30),
            capacity_curve_on_first=bool(data.get('CrvCpctOnFirst', 0)),
            pier_height_angle=data.get('AngDffsForAltMaschi', 0),
            base_restraint=data.get('VincoloPiede', 0),
            top_restraint=data.get('VincoloTesta', 0),
            user_restraint=data.get('VincoloUser', 100),
            top_wall_restraint=data.get('VincoloTestaMuro', 0),
            stiffness_tolerance=data.get('PercRgdzzAmm', 15),
            auto_ductility=bool(data.get('ClcAutoDuttilita', 1)),
            pier_height_wall_height=bool(data.get('ClcHMaschiHMuro', 1))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'mesh_refinement': self.mesh_refinement,
            'min_pier_height': self.min_pier_height,
            'min_pier_length': self.min_pier_length,
            'capacity_curve_on_first': self.capacity_curve_on_first,
            'pier_height_angle': self.pier_height_angle,
            'base_restraint': self.base_restraint,
            'top_restraint': self.top_restraint,
            'user_restraint': self.user_restraint,
            'top_wall_restraint': self.top_wall_restraint,
            'stiffness_tolerance': self.stiffness_tolerance,
            'auto_ductility': self.auto_ductility,
            'pier_height_wall_height': self.pier_height_wall_height
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationSettings':
        """Deserializza da dizionario"""
        return cls(**data)


@dataclass
class Project:
    """
    Progetto completo con tutti i dati
    Supporta formato ACCA iEM
    """
    # Informazioni progetto
    info: ProjectInfo = field(default_factory=ProjectInfo)

    # Impostazioni calcolo
    settings: CalculationSettings = field(default_factory=CalculationSettings)

    # Geometria
    wall: Optional[Any] = None  # Wall object
    openings: List[Any] = field(default_factory=list)  # Lista Opening

    # Maschi murari
    masonry_piers: Optional[Any] = None  # MasonryPierCollection

    # Materiali (dizionario ID -> dati materiale)
    materials: Dict[int, Dict] = field(default_factory=dict)

    # Carichi
    loads: Optional[Any] = None  # LoadCollection

    # Risultati verifiche
    verification_results: Optional[Any] = None  # VerificationResults

    # Elementi FEM (per analisi avanzata)
    fem_nodes: List[Dict] = field(default_factory=list)
    fem_beams: List[Dict] = field(default_factory=list)
    fem_shells: List[Dict] = field(default_factory=list)

    # Metadati
    version: str = "2.0"
    source_file: str = ""  # File sorgente (es. .iEM ACCA)

    def to_dict(self) -> Dict[str, Any]:
        """Serializza progetto in dizionario"""
        from .wall import Wall
        from .opening import Opening
        from .masonry_pier import MasonryPierCollection
        from .loads import LoadCollection
        from .verifications import VerificationResults

        return {
            'version': self.version,
            'source_file': self.source_file,
            'info': self.info.to_dict(),
            'settings': self.settings.to_dict(),
            'wall': self.wall.to_dict() if self.wall else None,
            'openings': [o.to_dict() if hasattr(o, 'to_dict') else o for o in self.openings],
            'masonry_piers': self.masonry_piers.to_dict() if self.masonry_piers else None,
            'materials': self.materials,
            'loads': self.loads.to_dict() if self.loads else None,
            'verification_results': self.verification_results.to_dict() if self.verification_results else None,
            'fem_nodes': self.fem_nodes,
            'fem_beams': self.fem_beams,
            'fem_shells': self.fem_shells
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Deserializza progetto da dizionario"""
        from .wall import Wall
        from .opening import Opening
        from .masonry_pier import MasonryPierCollection
        from .loads import LoadCollection
        from .verifications import VerificationResults

        project = cls()
        project.version = data.get('version', '1.0')
        project.source_file = data.get('source_file', '')

        # Info
        if data.get('info'):
            project.info = ProjectInfo.from_dict(data['info'])

        # Settings
        if data.get('settings'):
            project.settings = CalculationSettings.from_dict(data['settings'])

        # Wall
        if data.get('wall'):
            project.wall = Wall.from_dict(data['wall'])

        # Openings
        for op_data in data.get('openings', []):
            if isinstance(op_data, dict):
                project.openings.append(Opening.from_dict(op_data))
            else:
                project.openings.append(op_data)

        # Masonry piers
        if data.get('masonry_piers'):
            project.masonry_piers = MasonryPierCollection.from_dict(data['masonry_piers'])

        # Materials
        project.materials = data.get('materials', {})

        # Loads
        if data.get('loads'):
            project.loads = LoadCollection.from_dict(data['loads'])

        # Verification results
        if data.get('verification_results'):
            project.verification_results = VerificationResults.from_dict(data['verification_results'])

        # FEM data
        project.fem_nodes = data.get('fem_nodes', [])
        project.fem_beams = data.get('fem_beams', [])
        project.fem_shells = data.get('fem_shells', [])

        return project

    @property
    def is_calculated(self) -> bool:
        """Verifica se il progetto è stato calcolato"""
        return self.info.calculation_state > 0 or self.verification_results is not None

    @property
    def has_openings(self) -> bool:
        """Verifica se ci sono aperture"""
        return len(self.openings) > 0

    @property
    def has_wall(self) -> bool:
        """Verifica se è definito un muro"""
        return self.wall is not None

    def get_summary(self) -> Dict[str, Any]:
        """Restituisce un riepilogo del progetto"""
        summary = {
            'name': self.info.name or 'Progetto senza nome',
            'location': f"{self.info.municipality} ({self.info.province})" if self.info.municipality else '',
            'client': self.info.client,
            'engineer': self.info.engineer,
            'num_openings': len(self.openings),
            'is_calculated': self.is_calculated
        }

        if self.wall:
            summary['wall_dimensions'] = f"{self.wall.length:.0f} x {self.wall.height:.0f} x {self.wall.thickness:.0f} cm"

        if self.verification_results:
            summary['all_verified'] = self.verification_results.all_verified
            summary['min_safety_factor'] = self.verification_results.min_safety_factor

        return summary
