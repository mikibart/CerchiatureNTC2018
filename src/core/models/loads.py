"""
Modelli Carichi NTC 2018
Gestione carichi e combinazioni secondo normativa
Compatibile con formato ACCA iEM
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class LoadCategory(Enum):
    """Categorie di carico secondo NTC 2018 Tab. 2.5.I"""
    PERMANENT_STRUCTURAL = 0      # G1 - Permanenti strutturali
    PERMANENT_NON_STRUCTURAL = 1  # G2 - Permanenti non strutturali
    RESIDENTIAL = 2               # Cat. A - Abitazioni
    OFFICES = 3                   # Cat. B - Uffici
    ASSEMBLY_C1 = 4               # Cat. C1 - Scuole, caffè
    ASSEMBLY_C2 = 5               # Cat. C2 - Teatri, cinema
    COMMERCIAL = 6                # Cat. D - Negozi
    STORAGE = 7                   # Cat. E - Magazzini, archivi
    GARAGE_LIGHT = 8              # Cat. F - Autorimesse <= 30 kN
    GARAGE_HEAVY = 9              # Cat. G - Autorimesse > 30 kN
    ROOF = 10                     # Cat. H - Coperture
    SNOW_LOW = 11                 # Neve <= 1000 m
    SNOW_HIGH = 12                # Neve > 1000 m
    WIND = 13                     # Vento
    SEISMIC = 14                  # Sisma


# Coefficienti di combinazione NTC 2018 Tab. 2.5.I
LOAD_COEFFICIENTS = {
    LoadCategory.PERMANENT_STRUCTURAL: {
        'gamma_min': 1.0, 'gamma_max': 1.3, 'psi0': 1.0, 'psi1': 1.0, 'psi2': 1.0
    },
    LoadCategory.PERMANENT_NON_STRUCTURAL: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 1.0, 'psi1': 1.0, 'psi2': 1.0
    },
    LoadCategory.RESIDENTIAL: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.5, 'psi2': 0.3
    },
    LoadCategory.OFFICES: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.5, 'psi2': 0.3
    },
    LoadCategory.ASSEMBLY_C1: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.7, 'psi2': 0.6
    },
    LoadCategory.ASSEMBLY_C2: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.7, 'psi2': 0.6
    },
    LoadCategory.COMMERCIAL: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.7, 'psi2': 0.6
    },
    LoadCategory.STORAGE: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 1.0, 'psi1': 0.9, 'psi2': 0.8
    },
    LoadCategory.GARAGE_LIGHT: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.7, 'psi2': 0.6
    },
    LoadCategory.GARAGE_HEAVY: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.5, 'psi2': 0.3
    },
    LoadCategory.ROOF: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.0, 'psi1': 0.0, 'psi2': 0.0
    },
    LoadCategory.SNOW_LOW: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.5, 'psi1': 0.2, 'psi2': 0.0
    },
    LoadCategory.SNOW_HIGH: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.7, 'psi1': 0.5, 'psi2': 0.2
    },
    LoadCategory.WIND: {
        'gamma_min': 0.0, 'gamma_max': 1.5, 'psi0': 0.6, 'psi1': 0.2, 'psi2': 0.0
    },
    LoadCategory.SEISMIC: {
        'gamma_min': 1.0, 'gamma_max': 1.0, 'psi0': 1.0, 'psi1': 1.0, 'psi2': 1.0
    }
}

# Mapping da descrizione ACCA a categoria
ACCA_CATEGORY_MAP = {
    'Carico Permanente': LoadCategory.PERMANENT_STRUCTURAL,
    'Permanenti NON Strutturali': LoadCategory.PERMANENT_NON_STRUCTURAL,
    'Abitazioni': LoadCategory.RESIDENTIAL,
    'Scale': LoadCategory.RESIDENTIAL,
    'Coperture': LoadCategory.ROOF,
    'Uffici': LoadCategory.OFFICES,
    'Negozi': LoadCategory.COMMERCIAL,
    'Scuole': LoadCategory.ASSEMBLY_C1,
    'Locali Pubblici': LoadCategory.ASSEMBLY_C2,
    'Autorimesse (<= 30kN)': LoadCategory.GARAGE_LIGHT,
    'Autorimesse (> 30kN)': LoadCategory.GARAGE_HEAVY,
    'Magazzini Archivi': LoadCategory.STORAGE,
    'Neve (<= 1000 m s.l.m.)': LoadCategory.SNOW_LOW,
    'Neve (> 1000 m s.l.m.)': LoadCategory.SNOW_HIGH
}


@dataclass
class LoadCase:
    """
    Caso di carico singolo
    """
    id: int = 0
    description: str = ""
    category: LoadCategory = LoadCategory.PERMANENT_STRUCTURAL

    # Coefficienti di combinazione
    gamma_min: float = 1.0
    gamma_max: float = 1.3
    psi0: float = 1.0
    psi1: float = 1.0
    psi2: float = 1.0

    # Valori di carico (per unità di lunghezza o puntuali)
    Qi: float = 0.0   # kN/m - Carico iniziale
    Qf: float = 0.0   # kN/m - Carico finale
    Fz: float = 0.0   # kN - Forza verticale
    Mx: float = 0.0   # kNm - Momento X
    My: float = 0.0   # kNm - Momento Y
    Mz: float = 0.0   # kNm - Momento Z

    def __post_init__(self):
        """Imposta coefficienti di default dalla categoria"""
        if self.category in LOAD_COEFFICIENTS:
            coeffs = LOAD_COEFFICIENTS[self.category]
            if self.gamma_min == 1.0 and self.gamma_max == 1.3:  # Valori default
                self.gamma_min = coeffs['gamma_min']
                self.gamma_max = coeffs['gamma_max']
                self.psi0 = coeffs['psi0']
                self.psi1 = coeffs['psi1']
                self.psi2 = coeffs['psi2']

    @classmethod
    def from_acca(cls, data: dict) -> 'LoadCase':
        """Crea da dati ACCA"""
        description = data.get('Descrizione', '')
        category = ACCA_CATEGORY_MAP.get(description, LoadCategory.PERMANENT_STRUCTURAL)

        return cls(
            id=data.get('Id', 0),
            description=description,
            category=category,
            Qi=data.get('Qi', 0),
            Qf=data.get('Qf', 0),
            Fz=data.get('Fz', 0),
            Mx=data.get('Mx', 0),
            My=data.get('My', 0),
            Mz=data.get('Mz', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'description': self.description,
            'category': self.category.value,
            'gamma_min': self.gamma_min,
            'gamma_max': self.gamma_max,
            'psi0': self.psi0,
            'psi1': self.psi1,
            'psi2': self.psi2,
            'Qi': self.Qi,
            'Qf': self.Qf,
            'Fz': self.Fz,
            'Mx': self.Mx,
            'My': self.My,
            'Mz': self.Mz
        }


@dataclass
class NodalLoad:
    """
    Carico applicato a un nodo
    """
    id: int = 0
    node_id: int = 0
    load_type: LoadCategory = LoadCategory.PERMANENT_STRUCTURAL

    # Coefficienti
    gamma_min: float = 1.0
    gamma_max: float = 1.3
    psi0: float = 1.0
    psi1: float = 1.0
    psi2: float = 1.0

    # Forze e momenti
    Fx: float = 0.0  # N
    Fy: float = 0.0  # N
    Fz: float = 0.0  # N
    Mx: float = 0.0  # Nmm
    My: float = 0.0  # Nmm
    Mz: float = 0.0  # Nmm

    @classmethod
    def from_acca(cls, data: dict) -> 'NodalLoad':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            node_id=data.get('NodoID', 0),
            load_type=LoadCategory(data.get('Tipo', 0)),
            gamma_min=data.get('GammaMin', 1.0),
            gamma_max=data.get('GammaMax', 1.3),
            psi0=data.get('Psi0', 1.0),
            psi1=data.get('Psi1', 1.0),
            psi2=data.get('Psi2', 1.0),
            Fx=data.get('Fx', 0),
            Fy=data.get('Fy', 0),
            Fz=data.get('Fz', 0),
            Mx=data.get('Mx', 0),
            My=data.get('My', 0),
            Mz=data.get('Mz', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'load_type': self.load_type.value,
            'gamma_min': self.gamma_min,
            'gamma_max': self.gamma_max,
            'psi0': self.psi0,
            'psi1': self.psi1,
            'psi2': self.psi2,
            'Fx': self.Fx,
            'Fy': self.Fy,
            'Fz': self.Fz,
            'Mx': self.Mx,
            'My': self.My,
            'Mz': self.Mz
        }


@dataclass
class LinearLoad:
    """
    Carico lineare distribuito
    """
    id: int = 0
    description: str = ""
    condition_idx: int = 0  # Indice condizione di carico

    # Carichi iniziali e finali (per carichi trapezoidali)
    Qix: float = 0.0  # N/mm - Carico iniziale direzione X
    Qiy: float = 0.0  # N/mm - Carico iniziale direzione Y
    Qiz: float = 0.0  # N/mm - Carico iniziale direzione Z
    Qfx: float = 0.0  # N/mm - Carico finale direzione X
    Qfy: float = 0.0  # N/mm - Carico finale direzione Y
    Qfz: float = 0.0  # N/mm - Carico finale direzione Z

    load_type_desc: str = ""  # Descrizione tipo carico

    @classmethod
    def from_acca(cls, data: dict) -> 'LinearLoad':
        """Crea da dati ACCA"""
        return cls(
            id=data.get('Id', 0),
            description=data.get('Descrizione', ''),
            condition_idx=data.get('IdxCnd', 0),
            Qix=data.get('Qix', 0),
            Qiy=data.get('Qiy', 0),
            Qiz=data.get('Qiz', 0),
            Qfx=data.get('Qfx', 0),
            Qfy=data.get('Qfy', 0),
            Qfz=data.get('Qfz', 0),
            load_type_desc=data.get('DescTipologiaCrc', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'id': self.id,
            'description': self.description,
            'condition_idx': self.condition_idx,
            'Qix': self.Qix,
            'Qiy': self.Qiy,
            'Qiz': self.Qiz,
            'Qfx': self.Qfx,
            'Qfy': self.Qfy,
            'Qfz': self.Qfz,
            'load_type_desc': self.load_type_desc
        }


@dataclass
class LoadCollection:
    """
    Collezione di tutti i carichi del progetto
    """
    load_cases: List[LoadCase] = field(default_factory=list)
    nodal_loads: List[NodalLoad] = field(default_factory=list)
    linear_loads: List[LinearLoad] = field(default_factory=list)

    def add_load_case(self, load_case: LoadCase):
        """Aggiunge un caso di carico"""
        self.load_cases.append(load_case)

    def add_nodal_load(self, nodal_load: NodalLoad):
        """Aggiunge un carico nodale"""
        self.nodal_loads.append(nodal_load)

    def add_linear_load(self, linear_load: LinearLoad):
        """Aggiunge un carico lineare"""
        self.linear_loads.append(linear_load)

    def get_permanent_loads(self) -> List[LoadCase]:
        """Restituisce i carichi permanenti"""
        return [lc for lc in self.load_cases
                if lc.category in [LoadCategory.PERMANENT_STRUCTURAL,
                                   LoadCategory.PERMANENT_NON_STRUCTURAL]]

    def get_variable_loads(self) -> List[LoadCase]:
        """Restituisce i carichi variabili"""
        permanent = [LoadCategory.PERMANENT_STRUCTURAL,
                     LoadCategory.PERMANENT_NON_STRUCTURAL]
        return [lc for lc in self.load_cases if lc.category not in permanent]

    def to_dict(self) -> Dict[str, Any]:
        """Serializza in dizionario"""
        return {
            'load_cases': [lc.to_dict() for lc in self.load_cases],
            'nodal_loads': [nl.to_dict() for nl in self.nodal_loads],
            'linear_loads': [ll.to_dict() for ll in self.linear_loads]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoadCollection':
        """Deserializza da dizionario"""
        collection = cls()

        for lc_data in data.get('load_cases', []):
            lc = LoadCase(**lc_data)
            collection.load_cases.append(lc)

        for nl_data in data.get('nodal_loads', []):
            nl = NodalLoad(**nl_data)
            collection.nodal_loads.append(nl)

        for ll_data in data.get('linear_loads', []):
            ll = LinearLoad(**ll_data)
            collection.linear_loads.append(ll)

        return collection
