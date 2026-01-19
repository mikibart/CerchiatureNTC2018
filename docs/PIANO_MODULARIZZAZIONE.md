# Piano di Modularizzazione - CerchiatureNTC2018

**Data creazione:** 2026-01-19
**Autore:** Arch. Michelangelo Bartolotta
**Versione:** 1.0

---

## 1. Stato Attuale - Analisi Criticità

### Struttura Esistente
Il progetto ha già una struttura di base organizzata in:
- `src/core/` - Motore di calcolo
- `src/gui/` - Interfaccia utente PyQt5
- `src/widgets/` - Componenti personalizzati
- `src/report/` - Generazione PDF
- `src/io/` - Input/Output progetti
- `data/` - Database materiali e profili

### Criticità Identificate

| Problema | File interessati | Impatto |
|----------|------------------|---------|
| Moduli troppo grandi (500-800 linee) | `masonry.py`, `main_window.py`, `calc_module.py` | Difficile manutenzione |
| Accoppiamento GUI↔Calcolo | I moduli GUI chiamano direttamente i calculator | Difficile testing |
| Nessuna interfaccia formale | I moduli dipendono da implementazioni concrete | Difficile sostituzione |
| Costanti sparse | Parametri NTC 2018 ripetuti in più file | Rischio inconsistenza |
| Test insufficienti | Solo `test_masonry.py` presente | Rischio regressioni |

---

## 2. Architettura Target

### Diagramma a Livelli

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Input   │ │Openings │ │ Calc    │ │ Report  │  (GUI)    │
│  │ View    │ │ View    │ │ View    │ │ View    │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼──────────┼──────────┼──────────┼───────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ ProjectSvc   │ │ CalcService  │ │ ReportSvc    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Masonry  │ │Steel    │ │Concrete │ │Arch     │ Engines  │
│  │Calc     │ │Calc     │ │Calc     │ │Calc     │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │Verifier │ │Models   │ │Results  │                      │
│  └─────────┘ └─────────┘ └─────────┘                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Materials│ │Profiles │ │NTC2018  │ │Project  │          │
│  │ DB      │ │ DB      │ │Constants│ │ IO      │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Principi Guida

1. **Singola Responsabilità**: Ogni modulo fa UNA cosa bene
2. **Dipendenze verso il basso**: GUI → Service → Domain → Data
3. **Inversione dipendenze**: Usare interfacce/protocolli
4. **Moduli piccoli**: Target <200 LOC per file
5. **Testabilità**: Ogni modulo testabile in isolamento

---

## 3. Moduli Proposti

### 3.1 Data Layer (nessuna dipendenza)

| Modulo | File | Responsabilità | LOC target |
|--------|------|----------------|------------|
| Costanti NTC | `ntc2018_constants.py` | Tutte le costanti normative | ~100 |
| Repository Materiali | `materials_repository.py` | CRUD materiali (JSON) | ~150 |
| Repository Profili | `profiles_repository.py` | CRUD profili acciaio | ~150 |
| Repository Progetti | `project_repository.py` | Salvataggio/caricamento .cerch | ~150 |

### 3.2 Domain Layer (dipende solo da Data)

| Modulo | File | Responsabilità | LOC target |
|--------|------|----------------|------------|
| Geometria | `geometry_calculator.py` | Calcoli geometrici puri | ~100 |
| Resistenza Muratura | `masonry_resistance.py` | V_t1, V_t2, V_t3 | ~200 |
| Validazione Muratura | `masonry_validation.py` | Validazione input | ~100 |
| Rigidezza Acciaio | `steel_rigidity.py` | Rigidezza telai acciaio | ~150 |
| Rigidezza C.A. | `concrete_rigidity.py` | Rigidezza telai C.A. | ~150 |
| Geometria Archi | `arch_geometry.py` | Calcoli archi | ~100 |
| Verificatore NTC | `ntc2018_verifier.py` | Verifica §8.4.1 | ~100 |
| Aggregatore Risultati | `result_aggregator.py` | Aggregazione output | ~100 |

### 3.3 Service Layer (dipende da Domain)

| Modulo | File | Responsabilità | LOC target |
|--------|------|----------------|------------|
| Servizio Calcolo | `calculation_service.py` | Orchestrazione calcoli | ~200 |
| Servizio Report | `report_service.py` | Orchestrazione report | ~200 |
| Servizio Progetto | `project_service.py` | Gestione ciclo vita | ~150 |

### 3.4 Presentation Layer (dipende solo da Service)

| Modulo | File | Responsabilità | LOC target |
|--------|------|----------------|------------|
| Vista Input | `input_view.py` | Visualizzazione input | ~200 |
| Presenter Input | `input_presenter.py` | Logica input | ~150 |
| Vista Aperture | `openings_view.py` | Visualizzazione aperture | ~200 |
| Presenter Aperture | `openings_presenter.py` | Logica aperture | ~150 |
| Vista Calcoli | `calc_view.py` | Visualizzazione calcoli | ~200 |
| Presenter Calcoli | `calc_presenter.py` | Logica calcoli | ~150 |
| Vista Report | `report_view.py` | Visualizzazione report | ~200 |
| Widget riutilizzabili | `widgets/` | Componenti UI | ~100 cad. |

---

## 4. Struttura Directory Target

```
CerchiatureNTC2018/
├── main.py                          # Entry point
├── requirements.txt
├── README.md
│
├── data/                            # Database JSON
│   ├── materials.json
│   └── profiles.json
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/                        # DATA LAYER
│   │   ├── __init__.py
│   │   ├── ntc2018_constants.py     # Costanti normative
│   │   ├── materials_repository.py  # CRUD materiali
│   │   ├── profiles_repository.py   # CRUD profili
│   │   └── project_repository.py    # CRUD progetti
│   │
│   ├── domain/                      # DOMAIN LAYER
│   │   ├── __init__.py
│   │   ├── models/                  # Modelli dati
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── wall.py
│   │   │   ├── opening.py
│   │   │   └── reinforcement.py
│   │   │
│   │   ├── calculators/             # Calcolatori puri
│   │   │   ├── __init__.py
│   │   │   ├── geometry_calculator.py
│   │   │   ├── masonry_resistance.py
│   │   │   ├── masonry_validation.py
│   │   │   ├── steel_rigidity.py
│   │   │   ├── concrete_rigidity.py
│   │   │   └── arch_geometry.py
│   │   │
│   │   ├── verifiers/               # Verificatori normativi
│   │   │   ├── __init__.py
│   │   │   └── ntc2018_verifier.py
│   │   │
│   │   └── results/                 # Gestione risultati
│   │       ├── __init__.py
│   │       └── result_aggregator.py
│   │
│   ├── services/                    # SERVICE LAYER
│   │   ├── __init__.py
│   │   ├── calculation_service.py
│   │   ├── report_service.py
│   │   └── project_service.py
│   │
│   ├── presentation/                # PRESENTATION LAYER
│   │   ├── __init__.py
│   │   ├── main_window.py           # Finestra principale (snella)
│   │   │
│   │   ├── views/                   # Viste (solo UI)
│   │   │   ├── __init__.py
│   │   │   ├── input_view.py
│   │   │   ├── openings_view.py
│   │   │   ├── calc_view.py
│   │   │   └── report_view.py
│   │   │
│   │   ├── presenters/              # Presenter (logica UI)
│   │   │   ├── __init__.py
│   │   │   ├── input_presenter.py
│   │   │   ├── openings_presenter.py
│   │   │   ├── calc_presenter.py
│   │   │   └── report_presenter.py
│   │   │
│   │   ├── widgets/                 # Widget riutilizzabili
│   │   │   ├── __init__.py
│   │   │   ├── wall_canvas.py
│   │   │   └── profile_selector.py
│   │   │
│   │   └── dialogs/                 # Dialog
│   │       ├── __init__.py
│   │       └── opening_dialog.py
│   │
│   └── report/                      # Generazione PDF
│       ├── __init__.py
│       ├── pdf_generator.py
│       └── templates/
│
├── tests/                           # Test unitari
│   ├── __init__.py
│   ├── data/
│   ├── domain/
│   ├── services/
│   └── presentation/
│
├── docs/                            # Documentazione
│   ├── PIANO_MODULARIZZAZIONE.md    # Questo file
│   └── API.md
│
├── projects/                        # Progetti salvati
└── reports/                         # Report generati
```

---

## 5. Piano di Implementazione

### Fase 1: Fondamenta (Priorità ALTA) ✅ COMPLETATA
- [x] Creare `src/data/ntc2018_constants.py` con tutte le costanti
- [x] Migrare costanti sparse dai file esistenti
- [x] Creare test per le costanti (37 test passati)

### Fase 2: Separazione Calcoli Muratura (Priorità ALTA) ✅ COMPLETATA
- [x] Estrarre `masonry_validation.py` da `masonry.py`
- [x] Estrarre `masonry_resistance.py` da `masonry.py`
- [x] Estrarre `masonry_geometry.py` (maschi murari, geometria)
- [x] Estrarre `masonry_stiffness.py` (rigidezza laterale)
- [x] Creare `masonry_calculator.py` (orchestratore)
- [x] Creare test unitari (68 test passati)
- [x] Verificare che i calcoli diano stessi risultati

### Fase 3: Service Layer (Priorità ALTA) ✅ COMPLETATA
- [x] Creare `calculation_service.py` - orchestratore principale
- [x] Creare `frame_service.py` - calcolo cerchiature
- [x] Creare `project_service.py` - gestione ciclo vita progetto
- [x] Creare `services_bridge.py` - ponte GUI-Service per migrazione graduale
- [x] Creare test unitari per i service (71 test)

### Fase 4: Pattern MVP per GUI (Priorità MEDIA) ✅ COMPLETATA
- [x] Creare `base_presenter.py` - classe base con eventi e validazione
- [x] Separare logica `input_module.py` → `input_presenter.py`
- [x] Separare logica `openings_module.py` → `openings_presenter.py`
- [x] Separare logica `calc_module.py` → `calc_presenter.py`
- [x] Creare test unitari per presenter (37 test)
- [x] Aggiornare MainWindow per integrare presenter MVP
- [x] Connettere eventi presenter con view
- [ ] Separare `report_module.py` → view + presenter (opzionale)

### Fase 5: Sistema Plugin Rinforzi (Priorità MEDIA) ✅ COMPLETATA
- [x] Definire interfaccia `ReinforcementCalculator` (ABC)
- [x] Creare `ReinforcementRegistry` (singleton, auto-discovery)
- [x] Creare adapter `SteelFramePlugin` per calcolatore acciaio
- [x] Creare adapter `ConcreteFramePlugin` per calcolatore c.a.
- [x] Sistema di registrazione automatica tramite decoratore
- [x] Creare test unitari (33 test)

### Fase 6: Test Completi (Priorità ALTA) ✅ COMPLETATA
- [x] Test per ogni modulo del Data Layer (57 test)
- [x] Test per ogni calcolatore del Domain Layer (57 test)
- [x] Test per Models (50 test)
- [x] Test integrazione end-to-end (21 test)
- [x] Corretto bug in verifications.py (RESISTANCE_LIMIT)

### Fase 7: Finalizzazione e Documentazione ✅ COMPLETATA
- [x] Verificare metriche di successo
- [x] Verificare assenza import circolari
- [x] Verificare dipendenze corrette tra layer
- [x] Creare documentazione API (`docs/API.md`)
- [x] Aggiornare piano di modularizzazione

---

## 6. Benefici Attesi

| Aspetto | Prima | Dopo |
|---------|-------|------|
| **Testabilità** | Solo `masonry.py` testato | 100% moduli testabili |
| **LOC per file** | 500-800 | <200 |
| **Tempo fix bug** | Alto (codice intrecciato) | Basso (modulo isolato) |
| **Aggiunta feature** | Modifica multipli file | Nuovo modulo + registrazione |
| **Comprensione codice** | Difficile | Facile (singola responsabilità) |
| **Riuso** | Solo GUI | Calcoli usabili da CLI/API |

---

## 7. Rischi e Mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Regressioni durante refactoring | Alta | Alto | Test prima di ogni modifica |
| Tempi più lunghi del previsto | Media | Medio | Procedere per fasi incrementali |
| Over-engineering | Media | Medio | YAGNI - solo ciò che serve ora |
| Perdita funzionalità | Bassa | Alto | Commit frequenti, backup |

---

## 8. Metriche di Successo

- [~] Tutti i file <200 LOC (esclusi test) - 20/47 file OK, GUI legacy ancora grandi
- [x] Copertura test significativa - 432 test unitari
- [x] Zero import circolari - verificato
- [x] Ogni layer dipende solo da quello sottostante - verificato
- [x] Tempo di build test <30 secondi - ~0.1 secondi
- [x] Documentazione API per ogni modulo pubblico - vedi `docs/API.md`

---

## 9. Note e Decisioni

### 2026-01-19 - Fase 6 Completata
- Creati test completi per tutti i layer:
  - `tests/test_database.py` - Test Data Layer (57 test)
    - ProfilesDatabase: profili metallici HEA/HEB/IPE/UPN
    - MaterialsDatabase: materiali murari NTC 2018, custom materials
  - `tests/test_domain_layer.py` - Test Domain Layer (57 test)
    - SteelFrameCalculator: rigidezza e capacità telai acciaio
    - ConcreteFrameCalculator: rigidezza e capacità telai C.A.
    - FrameResult: risultati standardizzati
    - NTC2018Verifier: verifiche interventi locali
  - `tests/test_models.py` - Test Models (50 test)
    - Wall, Opening, Reinforcement, Project, ProjectInfo
  - `tests/test_integration_e2e.py` - Test E2E (21 test)
    - Scenario nuova apertura con cerchiatura acciaio
    - Scenario cerchiatura C.A.
    - Confronto materiali via registry
    - Pipeline completa input → calcolo → verifica
- Corretto bug in `verifications.py:56`:
  - Il confronto `delta_V_check <= RESISTANCE_LIMIT` non funzionava
    con RESISTANCE_LIMIT negativo (-0.2)
  - Fix: usa `abs(self.RESISTANCE_LIMIT)` per confronto corretto
- Verificate metriche di successo:
  - Zero import circolari ✓
  - Dipendenze layer corrette ✓
  - Tempo test ~0.1 secondi ✓
- Totale test progetto: 432 (tutti passati)

### 2026-01-19 - Fase 5 Completata
- Creato sistema plugin per calcolatori di rinforzo in `src/core/engine/`:
  - `reinforcement_interface.py` - Interfaccia base con:
    - `ReinforcementCalculator` (ABC) con metodi astratti
    - `CalculationInput/Output` dataclass standardizzate
    - `ReinforcementCapability` per descrivere capacità plugin
    - Enum per materiali e tipi supportati
  - `reinforcement_registry.py` - Registry singleton con:
    - Registrazione automatica via decoratore `@register`
    - Selezione automatica calcolatore per materiale
    - Helper functions `get_registry()`, `get_calculator_for()`
  - `reinforcement_plugins.py` - Adapter per calcolatori esistenti:
    - `SteelFramePlugin` wrappa `SteelFrameCalculator`
    - `ConcreteFramePlugin` wrappa `ConcreteFrameCalculator`
- Creato `tests/test_reinforcement_plugins.py` con 33 test unitari
- Benefici:
  - Architettura estensibile per nuovi tipi di rinforzo
  - Interfaccia uniforme per tutti i calcolatori
  - Registrazione automatica dei plugin
  - Retrocompatibilità con codice esistente
- Totale test progetto: 247 (tutti passati)

### 2026-01-19 - Fase 4 Completata
- Creato package `src/gui/presenters/` con pattern MVP:
  - `base_presenter.py` - Classe astratta con sistema eventi, validazione, dirty tracking
  - `input_presenter.py` - Logica per geometria parete, muratura, aperture, vincoli
  - `openings_presenter.py` - Logica per gestione aperture e rinforzi
  - `calc_presenter.py` - Orchestrazione calcoli via CalculationService
- Creato package `src/gui/views/` (struttura predisposta per view pure)
- Creato suite test `tests/gui/test_presenters.py` con 37 test unitari
- Corretto riferimento `masonry_types` nel database materiali
- **Aggiornato `main_window.py`** per integrare pattern MVP:
  - Inizializzazione presenter in `_init_presenters()`
  - Connessione eventi presenter-view in `_connect_presenter_events()`
  - Handler per eventi: wall_updated, masonry_updated, calculation_completed, etc.
  - Sincronizzazione dati via presenter in `_sync_via_presenters()`
  - Calcolo via `CalcPresenter` con validazione pre-calcolo
  - Salvataggio/caricamento progetti con supporto presenter
  - Fallback legacy quando presenter non disponibili
- Benefici: View e logica separati, eventi per comunicazione, logica testabile
- Totale test progetto: 214 (tutti passati)

### 2026-01-19 - Fase 3 Completata
- Creato package `src/services/` con Service Layer completo:
  - `calculation_service.py` - Orchestrazione calcoli (CalculationService, CalculationResult)
  - `frame_service.py` - Calcolo cerchiature (FrameService, FrameResult)
  - `project_service.py` - Gestione progetti (ProjectService, salvataggio/caricamento)
- Creato `src/gui/services_bridge.py` - Ponte per integrazione graduale GUI
- Creato suite test `tests/services/` con 71 test unitari
- Aggiunto `GAMMA_COLLABORAZIONE` alle costanti NTC2018
- Corretto segno `DELTA_V_MAX` a -0.20 per chiarezza semantica
- Benefici: GUI disaccoppiata dai calculator, calcoli testabili, riusabili da CLI/API

### 2026-01-19 - Fase 2 Completata
- Creato package `src/core/engine/masonry/` con struttura modulare:
  - `validation.py` - Validazione input (ValidationResult, MasonryValidator)
  - `geometry.py` - Geometria e maschi murari (Maschio, MaschiMurari, MasonryGeometry)
  - `resistance.py` - Calcolo resistenze (ResistanceResult, MasonryResistance)
  - `stiffness.py` - Rigidezza laterale (StiffnessResult, MasonryStiffness)
  - `calculator.py` - Orchestratore (MasonryCalculator v2.0.0-MODULAR)
- Aggiornato `src/core/engine/masonry.py` come facade per retrocompatibilità
- Creato suite test `tests/masonry/` con 68 test unitari:
  - `test_validation.py` - 12 test
  - `test_geometry.py` - 13 test
  - `test_resistance.py` - 16 test
  - `test_stiffness.py` - 18 test
  - `test_integration.py` - 9 test (verifica valori, retrocompatibilità)
- Benefici: moduli piccoli (<200 LOC), testabili in isolamento, formula verificata

### 2026-01-19 - Fase 1 Completata
- Creato `src/data/ntc2018_constants.py` (~300 LOC) con tutte le costanti NTC 2018
- Aggiornati 5 file di calcolo per usare le costanti centralizzate:
  - `masonry.py` - coefficienti muratura, vincoli, limiti
  - `steel_frame.py` - proprietà acciaio, moduli elastici
  - `concrete_frame.py` - proprietà cls e armatura, coefficienti sicurezza
  - `verifications.py` - limiti interventi locali
  - `arch_reinforcement.py` - limiti calandratura, proprietà acciaio
- Creato `tests/test_ntc2018_constants.py` con 37 test unitari (tutti passati)
- Beneficio immediato: nessuna più duplicazione delle costanti normative

### 2026-01-19 - Creazione piano iniziale
- Analisi codebase esistente completata
- Identificate 5 criticità principali
- Definita architettura a 4 layer
- Priorità: costanti → calcoli → service → GUI

---

## 10. Changelog

| Data | Versione | Modifiche |
|------|----------|-----------|
| 2026-01-19 | 1.8 | Fase 7 completata - Verifica metriche, API docs |
| 2026-01-19 | 1.7 | Fase 6 completata - Test Completi (185 nuovi test, tot. 432) |
| 2026-01-19 | 1.6 | Fase 5 completata - Sistema Plugin Rinforzi (33 test, tot. 247) |
| 2026-01-19 | 1.5 | Fase 4 completata - MVP in MainWindow (37 test, tot. 214) |
| 2026-01-19 | 1.4 | Fase 4 parziale - Presenter Layer creato |
| 2026-01-19 | 1.3 | Fase 3 completata - Service Layer (71 test) |
| 2026-01-19 | 1.2 | Fase 2 completata - Moduli muratura separati (68 test) |
| 2026-01-19 | 1.1 | Fase 1 completata - Costanti NTC 2018 centralizzate |
| 2026-01-19 | 1.0 | Creazione documento |

