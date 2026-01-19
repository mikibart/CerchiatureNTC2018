"""
Validazione Input Muratura
==========================

Modulo per la validazione dei dati di input per calcoli muratura.
Verifica parametri geometrici e meccanici secondo NTC 2018.

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

from src.data.ntc2018_constants import NTC2018

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Risultato della validazione"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Aggiunge un errore"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Aggiunge un warning (non invalida)"""
        self.warnings.append(message)


class MasonryValidator:
    """Validatore per dati muratura secondo NTC 2018"""

    # Limiti geometrici ragionevoli
    MIN_LENGTH_CM = 10      # cm
    MAX_LENGTH_CM = 2000    # cm (20 m)
    MIN_HEIGHT_CM = 50      # cm
    MAX_HEIGHT_CM = 1000    # cm (10 m)
    MIN_THICKNESS_CM = 10   # cm
    MAX_THICKNESS_CM = 200  # cm (2 m)

    # Limiti parametri meccanici (da Tab. C8.5.I)
    MIN_FCM_MPA = 0.5
    MAX_FCM_MPA = 20.0
    MIN_TAU0_MPA = 0.01
    MAX_TAU0_MPA = 0.5
    MIN_E_MPA = 100
    MAX_E_MPA = 10000

    @classmethod
    def validate_wall_geometry(cls, wall_data: Dict) -> ValidationResult:
        """
        Valida i dati geometrici della parete

        Args:
            wall_data: Dict con 'length', 'height', 'thickness' in cm

        Returns:
            ValidationResult con esito e messaggi
        """
        result = ValidationResult(is_valid=True)

        # Verifica presenza campi obbligatori
        required_fields = ['length', 'height', 'thickness']
        for field_name in required_fields:
            if field_name not in wall_data:
                result.add_error(f"Campo obbligatorio mancante: {field_name}")
                return result

        length = wall_data['length']
        height = wall_data['height']
        thickness = wall_data['thickness']

        # Validazione lunghezza
        if length <= 0:
            result.add_error(f"Lunghezza non valida: {length} cm (deve essere > 0)")
        elif length < cls.MIN_LENGTH_CM:
            result.add_warning(f"Lunghezza molto piccola: {length} cm")
        elif length > cls.MAX_LENGTH_CM:
            result.add_warning(f"Lunghezza molto grande: {length} cm")

        # Validazione altezza
        if height <= 0:
            result.add_error(f"Altezza non valida: {height} cm (deve essere > 0)")
        elif height < cls.MIN_HEIGHT_CM:
            result.add_warning(f"Altezza molto piccola: {height} cm")
        elif height > cls.MAX_HEIGHT_CM:
            result.add_warning(f"Altezza molto grande: {height} cm")

        # Validazione spessore
        if thickness <= 0:
            result.add_error(f"Spessore non valido: {thickness} cm (deve essere > 0)")
        elif thickness < cls.MIN_THICKNESS_CM:
            result.add_warning(f"Spessore molto piccolo: {thickness} cm")
        elif thickness > cls.MAX_THICKNESS_CM:
            result.add_warning(f"Spessore molto grande: {thickness} cm")

        # Controllo snellezza (NTC 2018 § 8.7.1)
        if result.is_valid and thickness > 0:
            h_m = height / 100
            t_m = thickness / 100
            snellezza = h_m / t_m

            if snellezza > NTC2018.Muratura.SNELLEZZA_MAX:
                result.add_warning(
                    f"Snellezza λ = {snellezza:.1f} > {NTC2018.Muratura.SNELLEZZA_MAX} - "
                    "Verifica elementi snelli richiesta (NTC 2018 § 8.7.1)"
                )

        return result

    @classmethod
    def validate_masonry_properties(cls, masonry_data: Dict) -> ValidationResult:
        """
        Valida i parametri meccanici della muratura

        Args:
            masonry_data: Dict con 'fcm', 'tau0', 'E', 'G' (opzionale)

        Returns:
            ValidationResult con esito e messaggi
        """
        result = ValidationResult(is_valid=True)

        # fcm - Resistenza a compressione
        fcm = masonry_data.get('fcm', 0)
        if fcm <= 0:
            result.add_error(f"fcm non valido: {fcm} MPa (deve essere > 0)")
        elif fcm < cls.MIN_FCM_MPA:
            result.add_warning(f"fcm molto basso: {fcm} MPa (min tipico: {cls.MIN_FCM_MPA})")
        elif fcm > cls.MAX_FCM_MPA:
            result.add_warning(f"fcm molto alto: {fcm} MPa (max tipico: {cls.MAX_FCM_MPA})")

        # tau0 - Resistenza a taglio
        tau0 = masonry_data.get('tau0', 0)
        if tau0 <= 0:
            result.add_error(f"tau0 non valido: {tau0} MPa (deve essere > 0)")
        elif tau0 < cls.MIN_TAU0_MPA:
            result.add_warning(f"tau0 molto basso: {tau0} MPa")
        elif tau0 > cls.MAX_TAU0_MPA:
            result.add_warning(f"tau0 molto alto: {tau0} MPa")

        # E - Modulo elastico (opzionale ma consigliato)
        E = masonry_data.get('E', None)
        if E is not None:
            if E <= 0:
                result.add_error(f"E non valido: {E} MPa (deve essere > 0)")
            elif E < cls.MIN_E_MPA:
                result.add_warning(f"E molto basso: {E} MPa")
            elif E > cls.MAX_E_MPA:
                result.add_warning(f"E molto alto: {E} MPa")

        # Coerenza fcm/tau0 (rapporto tipico)
        if fcm > 0 and tau0 > 0:
            ratio = fcm / tau0
            if ratio < 10 or ratio > 100:
                result.add_warning(
                    f"Rapporto fcm/tau0 = {ratio:.1f} insolito (tipico: 20-50)"
                )

        return result

    @classmethod
    def validate_loads(cls, loads: Dict, wall_data: Dict) -> ValidationResult:
        """
        Valida i carichi applicati

        Args:
            loads: Dict con 'vertical' (kN), 'eccentricity' (cm)
            wall_data: Dict con geometria parete

        Returns:
            ValidationResult con esito e messaggi
        """
        result = ValidationResult(is_valid=True)

        # Carico verticale
        N = loads.get('vertical', 0)
        if N < 0:
            result.add_warning(f"Carico verticale negativo: {N} kN (trazione)")

        # Eccentricità
        e = loads.get('eccentricity', 0)
        thickness = wall_data.get('thickness', 100)  # cm

        # Limite eccentricità per sezione interamente compressa
        t_m = thickness / 100
        e_m = e / 100
        e_limite = t_m * NTC2018.Muratura.ECCENTRICITA_LIMITE_RATIO

        if abs(e_m) > e_limite:
            result.add_warning(
                f"Eccentricità e = {e:.1f} cm > t/6 = {e_limite*100:.1f} cm - "
                "Sezione parzializzata"
            )

        if abs(e_m) > t_m / 2:
            result.add_error(
                f"Eccentricità e = {e:.1f} cm > t/2 = {t_m*50:.1f} cm - "
                "Carico fuori dalla sezione"
            )

        return result

    @classmethod
    def validate_all(cls, wall_data: Dict, masonry_data: Dict,
                    loads: Optional[Dict] = None) -> ValidationResult:
        """
        Esegue tutte le validazioni

        Args:
            wall_data: Dati geometrici parete
            masonry_data: Parametri meccanici muratura
            loads: Carichi applicati (opzionale)

        Returns:
            ValidationResult aggregato
        """
        result = ValidationResult(is_valid=True)

        # Validazione geometria
        geom_result = cls.validate_wall_geometry(wall_data)
        result.errors.extend(geom_result.errors)
        result.warnings.extend(geom_result.warnings)
        if not geom_result.is_valid:
            result.is_valid = False

        # Validazione proprietà meccaniche
        prop_result = cls.validate_masonry_properties(masonry_data)
        result.errors.extend(prop_result.errors)
        result.warnings.extend(prop_result.warnings)
        if not prop_result.is_valid:
            result.is_valid = False

        # Validazione carichi (se forniti)
        if loads:
            load_result = cls.validate_loads(loads, wall_data)
            result.errors.extend(load_result.errors)
            result.warnings.extend(load_result.warnings)
            if not load_result.is_valid:
                result.is_valid = False

        # Log risultato
        if result.is_valid:
            if result.warnings:
                logger.info(f"Validazione OK con {len(result.warnings)} warning")
            else:
                logger.info("Validazione OK")
        else:
            logger.error(f"Validazione FALLITA: {len(result.errors)} errori")

        return result
