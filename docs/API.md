# API Reference - CerchiatureNTC2018

**Versione:** 2.0.0-MODULAR
**Data:** 2026-01-19
**Autore:** Arch. Michelangelo Bartolotta

---

## Indice

1. [Data Layer](#data-layer)
2. [Domain Layer](#domain-layer)
3. [Service Layer](#service-layer)
4. [Plugin System](#plugin-system)

---

## Data Layer

### NTC2018 Constants

**Modulo:** `src.data.ntc2018_constants`

Costanti normative centralizzate secondo NTC 2018 (D.M. 17/01/2018).

```python
from src.data.ntc2018_constants import NTC2018

# Coefficienti di sicurezza
gamma_m = NTC2018.Sicurezza.GAMMA_M      # 2.0 - muratura
gamma_c = NTC2018.Sicurezza.GAMMA_C      # 1.5 - calcestruzzo
gamma_s = NTC2018.Sicurezza.GAMMA_S      # 1.15 - acciaio armatura
gamma_m0 = NTC2018.Sicurezza.GAMMA_M0    # 1.05 - acciaio strutturale

# Acciaio strutturale
s235 = NTC2018.Acciaio.CLASSI['S235']    # fyk=235, ftk=360
E_acciaio = NTC2018.Acciaio.E            # 210000 MPa

# Calcestruzzo
c25 = NTC2018.Cls.CLASSI['C25/30']       # fck=25, Ecm=31476
fattore_fess = NTC2018.Cls.FATTORE_INERZIA_FESSURATA  # 0.5

# Acciaio per armature
b450c = NTC2018.AcciaioArm.TIPI['B450C']  # fyk=450, ftk=540

# Livelli di conoscenza
fc_lc1 = NTC2018.LivelliConoscenza.LC1    # FC=1.35
fc_lc2 = NTC2018.LivelliConoscenza.LC2    # FC=1.20
fc_lc3 = NTC2018.LivelliConoscenza.LC3    # FC=1.00

# Interventi locali (§8.4.1)
delta_k_max = NTC2018.InterventiLocali.DELTA_K_MAX  # 0.15 (±15%)
delta_v_max = NTC2018.InterventiLocali.DELTA_V_MAX  # -0.20 (max -20%)
```

---

### ProfilesDatabase

**Modulo:** `src.core.database.profiles`

Database profili metallici secondo EN 10365.

```python
from src.core.database.profiles import ProfilesDatabase, profiles_db

# Istanza globale
db = profiles_db

# Ottieni profilo
profile = db.get_profile('HEA', '160')
# Returns: {'h': 152, 'b': 160, 'tw': 6.0, 'tf': 9.0, 'A': 38.8,
#           'Ix': 1673, 'Iy': 616, 'Wx': 220.1, 'Wy': 77.0, ...}

# Tipi disponibili
types = db.get_available_types()  # ['HEA', 'HEB', 'IPE', 'UPN']

# Dimensioni disponibili per tipo
sizes = db.get_available_sizes('HEA')  # ['100', '120', '140', ...]

# Classe acciaio
grade = db.get_steel_grade('S235')  # {'fyk': 235, 'ftk': 360, 'E': 210000, ...}

# Ricerca profili per requisiti
results = db.search_profiles(min_Wx=200, min_Ix=3000, profile_types=['HEA', 'HEB'])
# Returns: lista profili ordinati per Wx crescente

# Profilo ottimale
optimal = db.get_optimal_profile(required_Wx=200, required_Ix=3000)
# Returns: profilo minimo che soddisfa requisiti
```

---

### MaterialsDatabase

**Modulo:** `src.core.database.materials_database`

Database materiali murari secondo NTC 2018 Tab. C8.5.I.

```python
from src.core.database.materials_database import MaterialsDatabase

db = MaterialsDatabase()

# Ottieni materiale
material = db.get_material('mattoni_pieni_calce')
# Returns: {'name': 'Muratura in mattoni pieni e malta di calce',
#           'category': 'Mattoni', 'fcm': 2.4, 'tau0': 0.060,
#           'E': 1500, 'G': 500, 'w': 18.0, 'normative': True, ...}

# Tutti i materiali
all_materials = db.get_all_materials()

# Categorie
categories = db.get_categories()  # ['Blocchi', 'Mattoni', 'Mista', 'Pietrame']

# Lista per ComboBox
display_list = db.get_display_list()

# Aggiungi materiale personalizzato
db.add_custom_material('my_material', {
    'name': 'Materiale Custom',
    'category': 'Custom',
    'fcm': 3.0, 'tau0': 0.070, 'E': 2000, 'G': 666, 'w': 19.0
})
```

---

## Domain Layer

### Models

**Package:** `src.core.models`

#### Wall

```python
from src.core.models.wall import Wall

wall = Wall(
    length=400,        # cm
    height=300,        # cm
    thickness=30,      # cm
    material_type="mattoni_pieni_calce",
    knowledge_level="LC1"
)

area = wall.area  # cm² (length * thickness)
```

#### Opening

```python
from src.core.models.opening import Opening

opening = Opening(
    width=100,         # cm
    height=200,        # cm
    x=50,              # posizione da sinistra
    y=0,               # posizione dal basso (0 = porta)
    opening_type="rectangular",
    is_existing=False,
    reinforcement=None  # opzionale
)
```

#### Project

```python
from src.core.models.project import Project, ProjectInfo

project = Project(
    info=ProjectInfo(
        name="Progetto Test",
        location="Roma",
        client="Cliente",
        engineer="Arch. Bartolotta"
    )
)
project.wall = Wall(...)
project.openings.append(Opening(...))
project.materials = {...}
project.results = {...}
```

---

### Calculators

#### SteelFrameCalculator

**Modulo:** `src.core.engine.steel_frame`

```python
from src.core.engine.steel_frame import SteelFrameCalculator

calc = SteelFrameCalculator()

# Dati apertura
opening_data = {'width': 100, 'height': 200}  # cm

# Dati rinforzo
rinforzo = {
    'materiale': 'acciaio',
    'tipo': 'Telaio completo in acciaio',
    'classe_acciaio': 'S235',
    'architrave': {'profilo': 'HEA 160', 'doppio': False, 'ruotato': False},
    'piedritti': {'profilo': 'HEA 160', 'doppio': False, 'ruotato': False},
    'vincoli': {'base': 'Incastro', 'nodo': 'Incastro (continuità)'}
}

# Calcolo rigidezza
result = calc.calculate_frame_stiffness(opening_data, rinforzo)
# Returns: {'K_frame': float, 'L': float, 'h': float, 'tipo': str,
#           'materiale': 'acciaio', 'extra_data': {...}, ...}

# Calcolo capacità
capacity = calc.calculate_frame_capacity(opening_data, rinforzo, {})
# Returns: {'M_Rd_beam': float, 'V_Rd_beam': float,
#           'M_Rd_column': float, 'N_Rd_column': float}
```

#### ConcreteFrameCalculator

**Modulo:** `src.core.engine.concrete_frame`

```python
from src.core.engine.concrete_frame import ConcreteFrameCalculator

calc = ConcreteFrameCalculator()

rinforzo = {
    'materiale': 'ca',
    'tipo': 'Telaio in C.A.',
    'classe_cls': 'C25/30',
    'tipo_acciaio': 'B450C',
    'copriferro': 30,  # mm
    'architrave': {
        'base': 30,           # cm
        'altezza': 40,        # cm
        'armatura_sup': '3φ16',
        'armatura_inf': '3φ16',
        'staffe': 'φ8/20'
    },
    'piedritti': {
        'base': 30,
        'spessore': 30,
        'armatura': '4φ16'
    }
}

# Rigidezza
result = calc.calculate_frame_stiffness(opening_data, rinforzo)

# Capacità
capacity = calc.calculate_frame_capacity(opening_data, rinforzo, {})

# Verifica armature minime
verif = calc.verify_minimum_reinforcement(rinforzo)
# Returns: {'all_ok': bool, 'messages': [...]}

# Apertura fessure
w_k = calc.calculate_crack_width(M_Ed=20.0, rinforzo_data=rinforzo)
# Returns: float (mm)
```

---

### NTC2018Verifier

**Modulo:** `src.core.engine.verifications`

```python
from src.core.engine.verifications import NTC2018Verifier

verifier = NTC2018Verifier()

# Verifica intervento locale (§8.4.1)
result = verifier.verify_local_intervention(
    K_original=1000,    # kN/m - rigidezza originale
    K_modified=1100,    # kN/m - rigidezza modificata
    V_original=100,     # kN - resistenza originale
    V_modified=100      # kN - resistenza modificata
)
# Returns: {
#   'is_local': bool,
#   'stiffness_variation': float,  # %
#   'stiffness_ok': bool,
#   'resistance_variation': float,  # %
#   'resistance_ok': bool,
#   'stiffness_ratio': float,
#   'resistance_ratio': float
# }

# Verifica limiti aperture
result = verifier.verify_opening_limits(
    wall_data={'length': 500, 'height': 300},  # cm
    openings=[{'x': 100, 'y': 0, 'width': 100, 'height': 200}]
)
# Returns: {
#   'opening_ratio': float,  # %
#   'opening_ratio_ok': bool,
#   'min_maschio_ok': bool,
#   'min_maschio_width': float  # cm
# }

# Coefficienti di sicurezza
safety = verifier.calculate_safety_factors(
    V_design=150, V_demand=100,
    K_provided=1200, K_required=1000
)
# Returns: {'safety_resistance': float, 'safety_stiffness': float,
#           'global_safety': float, 'is_safe': bool}

# Riepilogo verifiche
summary = verifier.get_verification_summary(result)
# Returns: stringa formattata con esito verifiche
```

---

### FrameResult

**Modulo:** `src.core.engine.frame_result`

```python
from src.core.engine.frame_result import FrameResult

result = FrameResult(
    K_frame=1500.0,    # kN/m
    M_max=50.0,        # kNm
    V_max=25.0,        # kN
    N_max=100.0,       # kN
    L=2.0,             # m
    h=1.8,             # m
    tipo="Telaio completo",
    materiale="acciaio",
    extra_data={'profilo': 'HEA 160'}
)

# Metodi
result.add_warning("Attenzione...")
result.set_error("Errore critico")
is_valid = result.is_valid()  # True se no error e K_frame >= 0
summary = result.get_summary()  # Riepilogo testuale
data = result.to_dict()  # Conversione a dizionario
```

---

## Service Layer

### CalculationService

**Modulo:** `src.services.calculation_service`

```python
from src.services.calculation_service import CalculationService

service = CalculationService()

# Calcolo completo
result = service.calculate(
    wall_data={
        'length': 400, 'height': 300, 'thickness': 30,
        'material': 'mattoni_pieni_calce'
    },
    openings=[
        {'x': 50, 'y': 0, 'width': 100, 'height': 200, 'rinforzo': {...}}
    ],
    options={'knowledge_level': 'LC1'}
)
# Returns: CalculationResult
#   .success: bool
#   .wall_stiffness: float
#   .wall_resistance: float
#   .frames: List[FrameResult]
#   .verification: Dict
#   .errors: List[str]
#   .warnings: List[str]
```

### FrameService

**Modulo:** `src.services.frame_service`

```python
from src.services.frame_service import FrameService

service = FrameService()

# Calcolo singola cerchiatura
result = service.calculate_frame(
    opening_data={'width': 100, 'height': 200},
    reinforcement_data={
        'materiale': 'acciaio',
        'tipo': 'Telaio completo in acciaio',
        'architrave': {'profilo': 'HEA 160'},
        'piedritti': {'profilo': 'HEA 160'}
    }
)
# Returns: FrameResult
```

### ProjectService

**Modulo:** `src.services.project_service`

```python
from src.services.project_service import ProjectService

service = ProjectService()

# Salvataggio
success = service.save_project(project_data, filepath='progetto.cerch')

# Caricamento
project_data = service.load_project('progetto.cerch')

# Validazione
errors = service.validate_project(project_data)
```

---

## Plugin System

### ReinforcementRegistry

**Modulo:** `src.core.engine.reinforcement_registry`

```python
from src.core.engine.reinforcement_registry import get_registry
from src.core.engine import reinforcement_plugins  # Importa per registrare

registry = get_registry()

# Seleziona calcolatore per materiale
calc = registry.get_calculator_for({'materiale': 'acciaio'})

# Calcolo diretto via registry
result = registry.calculate(
    reinforcement_data={'materiale': 'acciaio', 'tipo': '...', ...},
    opening_data={'width': 100, 'height': 200}
)
# Returns: CalculationOutput

# Info registry
print(registry.get_info())
materials = registry.get_available_materials()
capabilities = registry.get_capabilities()
```

### Creare un Plugin Personalizzato

```python
from src.core.engine.reinforcement_interface import (
    ReinforcementCalculator,
    ReinforcementCapability,
    ReinforcementMaterial,
    ReinforcementType,
    CalculationInput,
    CalculationOutput
)
from src.core.engine.reinforcement_registry import ReinforcementRegistry

@ReinforcementRegistry.register
class MyCustomPlugin(ReinforcementCalculator):

    def get_capability(self) -> ReinforcementCapability:
        return ReinforcementCapability(
            name="My Custom Calculator",
            description="Descrizione...",
            materials=[ReinforcementMaterial.WOOD],
            types=[ReinforcementType.PORTAL_FRAME],
            supports_arch=False,
            version="1.0.0"
        )

    def can_handle(self, reinforcement_data: dict) -> bool:
        return reinforcement_data.get('materiale') == 'legno'

    def calculate_stiffness(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()
        # Implementazione...
        output.K_frame = 500.0
        return output

    def calculate_capacity(self, input_data: CalculationInput) -> CalculationOutput:
        output = CalculationOutput()
        # Implementazione...
        return output
```

---

## Test

Eseguire tutti i test:

```bash
cd CerchiatureNTC2018
python -m unittest discover -s tests -v
```

Test specifici:

```bash
# Test database
python -m unittest tests.test_database -v

# Test domain layer
python -m unittest tests.test_domain_layer -v

# Test models
python -m unittest tests.test_models -v

# Test E2E
python -m unittest tests.test_integration_e2e -v

# Test plugin system
python -m unittest tests.test_reinforcement_plugins -v
```

---

## Note

- Tutti i valori geometrici sono in **centimetri (cm)** salvo diversa indicazione
- Le forze sono in **kN**, i momenti in **kNm**
- Le tensioni sono in **MPa** (N/mm²)
- I moduli elastici sono in **MPa**
