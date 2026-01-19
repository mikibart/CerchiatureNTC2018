"""
Formatter per risultati calcolo
Gestisce la formattazione di stringhe e HTML per i risultati
"""

class ResultFormatter:
    """Formatta i risultati del calcolo per la visualizzazione"""

    @staticmethod
    def format_verification_label(is_local: bool) -> str:
        """Formatta etichetta verifica intervento locale"""
        if is_local:
            return '<span style="color: green;">✓ VERIFICATO</span>'
        else:
            return '<span style="color: red;">✗ NON VERIFICATO</span>'

    @staticmethod
    def format_variation(value: float, limit: float, is_ok: bool,
                        is_stiffness: bool = True) -> str:
        """
        Formatta variazione percentuale con colore

        Args:
            value: Valore percentuale
            limit: Limite normativo (valore assoluto)
            is_ok: Se la verifica è superata
            is_stiffness: True se rigidezza (±), False se resistenza (≥)
        """
        color = "green" if is_ok else "red"

        if is_stiffness:
            relation = "≤" if is_ok else ">"
            return f'<span style="color: {color};">{value:.1f}% ({relation} {limit:.0f}%)</span>'
        else:
            # Resistenza: limite è -20%
            relation = "≤" if is_ok else ">"
            return f'<span style="color: {color};">{value:.1f}% ({relation} {limit:.0f}%)</span>'

    @staticmethod
    def format_stiffness_label(K_masonry: float, K_frames: float) -> str:
        """Formatta etichetta rigidezza modificata"""
        sign = "+" if K_frames >= 0 else "-"
        return f"{K_masonry + K_frames:.1f} kN/m (cerch: {sign}{abs(K_frames):.1f})"

    @staticmethod
    def generate_notes(results: dict, project_data: dict) -> str:
        """Genera il testo per le note e avvertimenti"""
        notes = []

        # Fattore di confidenza
        if 'FC' in results:
            notes.append(f"Fattore di confidenza FC = {results['FC']}")

        # Verifica intervento locale
        verif = results.get('verification', {})
        if not verif.get('is_local', False):
            notes.append("\n⚠️ ATTENZIONE: L'intervento NON può essere classificato "
                        "come LOCALE secondo NTC 2018 § 8.4.1")

            if not verif.get('stiffness_ok', False):
                notes.append(f"- La variazione di rigidezza ({verif.get('stiffness_variation', 0):.1f}%) "
                           f"supera il limite del 15%")

            if not verif.get('resistance_ok', False):
                notes.append(f"- La riduzione di resistenza ({verif.get('resistance_variation', 0):.1f}%) "
                           f"supera il limite del 20%")

            notes.append("\nSi consiglia di:\n"
                        "• Aumentare le sezioni delle cerchiature\n"
                        "• Ridurre il numero/dimensione delle aperture\n"
                        "• Valutare un intervento di miglioramento/adeguamento")
        else:
            notes.append("\n✓ L'intervento può essere classificato come LOCALE")

        # Resistenza critica
        orig = results.get('original', {})
        mod = results.get('modified', {})

        resistances = [
            ('V_t1', 'taglio puro'),
            ('V_t2', 'taglio con fattore di forma'),
            ('V_t3', 'presso-flessione')
        ]

        if 'V_min' in orig:
            for key, desc in resistances:
                if orig.get(key) == orig['V_min']:
                    notes.append(f"\nStato di fatto: resistenza critica per {desc}")
                    break

        if 'V_min' in mod:
            for key, desc in resistances:
                if mod.get(key) == mod['V_min']:
                    notes.append(f"Stato di progetto: resistenza critica per {desc}")
                    break

        # Contributo cerchiature
        if mod.get('K_cerchiature', 0) > 0 and mod.get('K', 0) > 0:
            contrib_k_percent = (mod['K_cerchiature'] / mod['K']) * 100
            notes.append(f"\nLe cerchiature contribuiscono per il {contrib_k_percent:.1f}% "
                        f"alla rigidezza totale")

        if mod.get('V_cerchiature', 0) > 0:
            V_cerch = mod['V_cerchiature'] * 0.7  # con fattore collaborazione
            notes.append(f"\nContributo resistenza cerchiature: +{V_cerch:.1f} kN")

            if orig.get('V_min', 0) > 0:
                incremento_res = (mod['V_min'] - orig['V_min']) / orig['V_min'] * 100
                notes.append(f"Incremento resistenza totale: +{incremento_res:.1f}%")

        # Analisi tipo di cerchiature
        openings_module = project_data.get('openings_module', {})
        openings = openings_module.get('openings', [])

        n_acciaio = 0
        n_ca = 0
        n_profili_multipli = 0
        n_calandrate = 0
        n_archi = 0
        n_non_calandrabili = 0

        for opening in openings:
            if opening.get('type') == 'Ad arco':
                n_archi += 1

            if 'rinforzo' in opening:
                rinforzo = opening['rinforzo']
                if rinforzo.get('materiale') == 'acciaio':
                    n_acciaio += 1
                    if 'architrave' in rinforzo and rinforzo['architrave'].get('n_profili', 1) > 1:
                        n_profili_multipli += 1
                    if 'calandrat' in rinforzo.get('tipo', '').lower() or opening.get('type') == 'Ad arco':
                        n_calandrate += 1
                elif rinforzo.get('materiale') == 'ca':
                    n_ca += 1

        # Avvisi calandratura da risultati frame
        frame_results = results.get('frame_results', {})
        for frame_data in frame_results.values():
            if 'bending_info' in frame_data and not frame_data['bending_info'].get('bendable', True):
                n_non_calandrabili += 1

        if n_archi > 0:
            notes.append(f"\n📐 {n_archi} aperture ad arco rilevate")
            if n_non_calandrabili > 0:
                notes.append(f"  ⚠️ {n_non_calandrabili} profili NON calandrabili con metodo standard")
                notes.append("  Valutare soluzioni alternative:")
                notes.append("  - Profili segmentati saldati")
                notes.append("  - Cambio sezione profilo")
                notes.append("  - Calandratura a caldo specializzata")

        if n_acciaio > 0:
            notes.append(f"\n• {n_acciaio} cerchiature in acciaio")
            if n_profili_multipli > 0:
                notes.append(f"  - {n_profili_multipli} con profili multipli accoppiati")
            if n_calandrate > 0:
                notes.append(f"  - {n_calandrate} cerchiature curve/calandrate")
                notes.append("  📋 Verificare preventivi officine specializzate")

        if n_ca > 0:
            notes.append(f"• {n_ca} cerchiature in C.A.")
            notes.append("  Verificare armature minime secondo NTC 2018")

        # Avvisi critici calandratura
        critical_warnings = []
        for opening_id, frame_data in frame_results.items():
            if frame_data.get('warnings'):
                for warning in frame_data['warnings']:
                    if 'non calandrabile' in warning.lower():
                        critical_warnings.append(f"{opening_id}: {warning}")

        if critical_warnings:
            notes.append("\n🔴 AVVISI CRITICI CALANDRATURA:")
            for warning in critical_warnings:
                notes.append(f"  {warning}")

        # Vincoli avanzati
        has_advanced = False
        for opening in openings:
            if 'rinforzo' in opening:
                rinforzo = opening['rinforzo']
                if 'vincoli' in rinforzo and 'avanzate' in rinforzo['vincoli']:
                    has_advanced = True
                    break

        if has_advanced:
            notes.append("\n⚠️ Sono state utilizzate opzioni di analisi avanzate")
            notes.append("  Verificare l'applicabilità delle ipotesi adottate")

        return '\n'.join(notes)

    @staticmethod
    def generate_export_text(results: dict, project_data: dict) -> str:
        """Genera il testo per l'esportazione"""
        from PyQt5.QtCore import QDateTime

        lines = []
        lines.append("RISULTATI CALCOLO CERCHIATURE NTC 2018")
        lines.append("=" * 70)
        lines.append("")

        lines.append(f"Data calcolo: {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm:ss')}")
        lines.append(f"Progettista: Arch. Michelangelo Bartolotta\n")

        # Verifica
        verif = results.get('verification', {})
        lines.append("VERIFICA INTERVENTO LOCALE")
        lines.append("-" * 30)
        lines.append(f"Esito: {'VERIFICATO' if verif.get('is_local') else 'NON VERIFICATO'}")
        lines.append(f"Variazione rigidezza: {verif.get('stiffness_variation', 0):.1f}%")
        lines.append(f"Variazione resistenza: {verif.get('resistance_variation', 0):.1f}%\n")

        # Stato di fatto
        orig = results.get('original', {})
        lines.append("STATO DI FATTO")
        lines.append("-" * 30)
        lines.append(f"Rigidezza K: {orig.get('K', 0):.1f} kN/m")
        lines.append(f"V_t1 (taglio): {orig.get('V_t1', 0):.1f} kN")
        lines.append(f"V_t2 (taglio f.f.): {orig.get('V_t2', 0):.1f} kN")
        lines.append(f"V_t3 (presso-flex): {orig.get('V_t3', 0):.1f} kN")
        lines.append(f"V_min: {orig.get('V_min', 0):.1f} kN\n")

        # Stato di progetto
        mod = results.get('modified', {})
        lines.append("STATO DI PROGETTO")
        lines.append("-" * 30)
        lines.append(f"Rigidezza K totale: {mod.get('K', 0):.1f} kN/m")
        k_cerch = mod.get('K_cerchiature', 0)
        lines.append(f"Rigidezza muratura: {mod.get('K', 0) - k_cerch:.1f} kN/m")
        lines.append(f"Contributo cerchiature: {k_cerch:.1f} kN/m")
        lines.append(f"V_t1 (taglio): {mod.get('V_t1', 0):.1f} kN")
        lines.append(f"V_t2 (taglio f.f.): {mod.get('V_t2', 0):.1f} kN")
        lines.append(f"V_t3 (presso-flex): {mod.get('V_t3', 0):.1f} kN")
        lines.append(f"V_min: {mod.get('V_min', 0):.1f} kN\n")

        # Dettaglio cerchiature
        frame_results = results.get('frame_results', {})
        if frame_results:
            lines.append("DETTAGLIO CERCHIATURE")
            lines.append("-" * 30)

            openings_module = project_data.get('openings_module', {})
            openings = openings_module.get('openings', [])

            from src.core.engine.arch_reinforcement import ArchReinforcementManager

            for i, (opening_id, frame_data) in enumerate(frame_results.items()):
                lines.append(f"\n{opening_id}:")

                if i < len(openings):
                    opening = openings[i]
                    lines.append(f"  Tipo apertura: {opening.get('type', 'Rettangolare')}")

                    if 'rinforzo' in opening:
                        rinforzo = opening['rinforzo']
                        lines.append(f"  Tipo rinforzo: {rinforzo.get('tipo', 'N.D.')}")
                        lines.append(f"  Materiale: {rinforzo.get('materiale', 'N.D.')}")

                        if rinforzo.get('materiale') == 'acciaio':
                            arch = rinforzo.get('architrave', {})
                            lines.append(f"  Architrave: {arch.get('n_profili', 1)}x {arch.get('profilo', 'N.D.')}")

                            if 'piedritti' in rinforzo:
                                pied = rinforzo['piedritti']
                                lines.append(f"  Piedritti: {pied.get('n_profili', 1)}x {pied.get('profilo', 'N.D.')}")

                    if opening.get('type') == 'Ad arco':
                        lines.append("\n  PARAMETRI ARCO:")
                        if 'arch_radius' in frame_data:
                            lines.append(f"    Raggio: {frame_data['arch_radius']:.1f} cm")
                        if 'arch_length' in frame_data:
                            lines.append(f"    Lunghezza sviluppata: {frame_data['arch_length']:.1f} cm")

                        if 'bending_info' in frame_data:
                            bend = frame_data['bending_info']
                            lines.append(f"\n  VERIFICA CALANDRATURA:")
                            lines.append(f"    Rapporto r/h: {bend.get('r_h_ratio', 0):.1f}")
                            lines.append(f"    Metodo: {bend.get('method', 'N.D.')}")
                            lines.append(f"    Tensioni residue: {bend.get('residual_stress', 0):.0f} MPa")

                            if bend.get('warnings'):
                                lines.append("    Avvisi:")
                                for warning in bend['warnings']:
                                    lines.append(f"      - {warning}")

                        if 'rinforzo' in opening:
                            report = ArchReinforcementManager.generate_bending_report(
                                opening, opening['rinforzo']
                            )
                            lines.append("\n" + report)

                lines.append(f"  K_cerchiatura: {frame_data.get('K_frame', 0):.1f} kN/m")

                if frame_data.get('V_resistance', 0) > 0:
                    lines.append(f"  V_resistenza: {frame_data.get('V_resistance', 0):.1f} kN")

                if frame_data.get('warnings'):
                    lines.append("  Avvertimenti:")
                    for warning in frame_data['warnings']:
                        lines.append(f"    - {warning}")

                if 'connections' in frame_data:
                    conn = frame_data['connections']
                    lines.append(f"  Verifica ancoraggi: {'OK' if conn.get('verified') else 'NON VERIFICATO'}")

        # Maschi murari
        if 'maschi' in results:
            lines.append("\nMASCHI MURARI")
            lines.append("-" * 30)
            for maschio in results['maschi']:
                lines.append(f"{maschio['id']}: L = {maschio['length']} cm ({maschio['position']})")

        return '\n'.join(lines)
