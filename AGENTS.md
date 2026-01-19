# AGENTS.md - Guida per AI Coding Assistants

## Panoramica Progetto

**CerchiatureNTC2018** è un software di calcolo strutturale per la progettazione di cerchiature (rinforzi) su pareti in muratura secondo la normativa italiana NTC 2018 (D.M. 17/01/2018).

- **Versione:** 2.0.0-MODULAR
- **Linguaggio:** Python 3.10+
- **GUI:** PyQt5
- **Test:** 432 test unitari e E2E

## Architettura

```
src/
├── data/                    # Data Layer - Costanti normative
│   └── ntc2018_constants.py # Coefficienti NTC 2018
├── core/                    # Domain Layer
│   ├── database/            # Database profili e materiali
│   ├── engine/              # Motore di calcolo
│   │   ├── masonry/         # Calcoli muratura (suddiviso)
│   │   ├── steel_frame.py   # Cerchiature acciaio
│   │   ├── concrete_frame.py # Cerchiature C.A.
│   │   ├── verifications.py # Verifiche NTC 2018
│   │   └── reinforcement_*.py # Plugin system
│   └── models/              # Modelli dati (Wall, Opening, Project)
├── services/                # Service Layer
│   ├── calculation_service.py
│   ├── frame_service.py
│   └── project_service.py
├── gui/                     # Presentation Layer
│   ├── modules/             # Moduli GUI (View)
│   ├── presenters/          # MVP Presenters
│   └── main_window.py
└── widgets/                 # Widget riutilizzabili
```

## Convenzioni Codice

### Stile
- **PEP 8** per formattazione
- **Docstring** in italiano (software per professionisti italiani)
- **Type hints** preferiti ma non obbligatori
- **Nomi variabili** tecnici in italiano (es. `architrave`, `piedritti`, `maschio`)

### Unità di Misura
- Geometria: **centimetri (cm)**
- Forze: **kN**
- Momenti: **kNm**
- Tensioni: **MPa** (N/mm²)
- Rigidezze: **kN/m**

### Pattern Utilizzati
- **MVP** (Model-View-Presenter) per GUI
- **Strategy/Plugin** per calcolatori rinforzo
- **Registry** con auto-discovery via decoratori
- **Service Layer** per orchestrazione

## Aree di Ottimizzazione Prioritarie

### 1. Moduli GUI Troppo Grandi
I seguenti file superano 200 LOC e andrebbero suddivisi:

| File | LOC | Suggerimento |
|------|-----|--------------|
| `src/gui/modules/calc_module.py` | ~800 | Separare logica UI da formattazione risultati |
| `src/gui/modules/openings_module.py` | ~600 | Estrarre dialog in file separati |
| `src/gui/modules/input_module.py` | ~500 | Separare validazione da UI |
| `src/gui/main_window.py` | ~700 | Estrarre menu e toolbar |

### 2. Type Hints Mancanti
Aggiungere type hints a:
- `src/core/engine/*.py`
- `src/services/*.py`
- `src/gui/presenters/*.py`

### 3. Caching
Implementare caching per:
- `ProfilesDatabase.get_profile()` - chiamato frequentemente
- `MaterialsDatabase.get_material()` - dati statici
- Risultati calcoli intermedi in `MasonryCalculator`

### 4. Error Handling
Migliorare gestione errori in:
- `src/services/calculation_service.py` - eccezioni più specifiche
- `src/gui/modules/calc_module.py` - feedback utente migliore

### 5. Test Coverage
Aumentare copertura test per:
- `src/gui/modules/` - attualmente ~30%
- `src/widgets/` - attualmente ~20%
- `src/report/generator.py` - non testato

## File Critici - Non Modificare Senza Test

- `src/data/ntc2018_constants.py` - Costanti normative certificate
- `src/core/engine/verifications.py` - Verifiche di sicurezza strutturale
- `src/core/engine/steel_frame.py` - Formule certificate
- `src/core/engine/concrete_frame.py` - Formule certificate

## Comandi Utili

```bash
# Esegui tutti i test
python -m unittest discover -s tests -v

# Test specifici
python -m unittest tests.test_domain_layer -v
python -m unittest tests.test_integration_e2e -v

# Avvia applicazione
python main.py

# Verifica import circolari
python -c "from src.core.engine import steel_frame, concrete_frame, verifications"
```

## Dipendenze

```
PyQt5>=5.15.0
numpy>=1.21.0
reportlab>=3.6.0 (per PDF)
python-docx>=0.8.11 (per Word)
```

## Normativa di Riferimento

- **NTC 2018** - D.M. 17/01/2018 "Norme Tecniche per le Costruzioni"
- **Circolare 2019** - n. 7/2019 "Istruzioni per l'applicazione NTC 2018"
- **EN 10365** - Profili metallici laminati a caldo
- **§8.4.1** - Interventi locali su edifici esistenti

## Note per AI Assistants

1. **Preservare compatibilità** con progetti `.cerch` esistenti
2. **Non modificare formule** senza validazione ingegneristica
3. **Mantenere retrocompatibilità** API pubblica in `docs/API.md`
4. **Testare sempre** dopo modifiche al domain layer
5. **Documentazione** in italiano per utenti finali
6. **Commit message** in inglese per convenzione

## Contatti

- **Autore:** Arch. Michelangelo Bartolotta
- **Repository:** https://github.com/mikibart/CerchiatureNTC2018
