"""
Geometria Muratura
==================

Modulo per calcoli geometrici su pareti in muratura.
- Identificazione maschi murari tra aperture
- Calcolo aree e proprietà geometriche
- Ripartizione carichi tra maschi

Arch. Michelangelo Bartolotta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class Maschio:
    """Rappresenta un maschio murario"""
    start: float      # Posizione iniziale [cm]
    end: float        # Posizione finale [cm]
    length: float     # Lunghezza [cm]
    index: int = 0    # Indice progressivo

    @property
    def length_m(self) -> float:
        """Lunghezza in metri"""
        return self.length / 100

    @property
    def center(self) -> float:
        """Centro del maschio [cm]"""
        return (self.start + self.end) / 2


@dataclass
class MaschiMurari:
    """Collezione di maschi murari con metadati"""
    maschi: List[Maschio] = field(default_factory=list)
    wall_length: float = 0      # Lunghezza totale parete [cm]
    total_length: float = 0     # Lunghezza totale maschi [cm]
    opening_length: float = 0   # Lunghezza totale aperture [cm]

    def __len__(self) -> int:
        return len(self.maschi)

    def __iter__(self):
        return iter(self.maschi)

    def __getitem__(self, index: int) -> Maschio:
        return self.maschi[index]

    @property
    def foratura_ratio(self) -> float:
        """Rapporto di foratura (aperture/parete)"""
        if self.wall_length > 0:
            return self.opening_length / self.wall_length
        return 0

    @property
    def maschi_ratio(self) -> float:
        """Rapporto maschi/parete"""
        if self.wall_length > 0:
            return self.total_length / self.wall_length
        return 0


class MasonryGeometry:
    """Calcoli geometrici per muratura"""

    @staticmethod
    def calculate_area(length_cm: float, thickness_cm: float) -> float:
        """
        Calcola l'area della sezione

        Args:
            length_cm: Lunghezza in cm
            thickness_cm: Spessore in cm

        Returns:
            Area in m²
        """
        return (length_cm / 100) * (thickness_cm / 100)

    @staticmethod
    def calculate_moment_of_inertia(length_cm: float, thickness_cm: float) -> float:
        """
        Calcola il momento d'inerzia della sezione (asse forte)

        Args:
            length_cm: Lunghezza in cm
            thickness_cm: Spessore in cm

        Returns:
            Momento d'inerzia in m⁴
        """
        t_m = thickness_cm / 100
        L_m = length_cm / 100
        return t_m * L_m**3 / 12

    @staticmethod
    def calculate_section_modulus(area_m2: float, length_cm: float) -> float:
        """
        Calcola il modulo di resistenza della sezione

        Args:
            area_m2: Area in m²
            length_cm: Lunghezza in cm

        Returns:
            Modulo di resistenza in m³
        """
        L_m = length_cm / 100
        return area_m2 * L_m / 6

    @staticmethod
    def identify_maschi(wall_data: Dict, openings: List[Dict]) -> MaschiMurari:
        """
        Identifica i maschi murari tra le aperture

        Args:
            wall_data: Dict con 'length' (lunghezza parete in cm)
            openings: Lista di aperture con 'x', 'width' in cm

        Returns:
            MaschiMurari con lista di maschi identificati
        """
        wall_length = wall_data.get('length', 0)

        result = MaschiMurari(wall_length=wall_length)

        if not openings:
            # Nessuna apertura: tutta la parete è un maschio
            if wall_length > 0:
                result.maschi.append(Maschio(
                    start=0,
                    end=wall_length,
                    length=wall_length,
                    index=0
                ))
                result.total_length = wall_length
            return result

        # Ordina aperture per posizione X
        sorted_openings = sorted(openings, key=lambda o: o.get('x', 0))

        maschi = []
        index = 0

        # Maschio iniziale (prima della prima apertura)
        first_opening_x = sorted_openings[0].get('x', 0)
        if first_opening_x > 0:
            maschi.append(Maschio(
                start=0,
                end=first_opening_x,
                length=first_opening_x,
                index=index
            ))
            index += 1
            logger.debug(f"Maschio iniziale: 0 - {first_opening_x} cm")

        # Maschi intermedi (tra le aperture)
        for i in range(len(sorted_openings) - 1):
            current = sorted_openings[i]
            next_op = sorted_openings[i + 1]

            x1 = current.get('x', 0) + current.get('width', 0)
            x2 = next_op.get('x', 0)

            if x2 > x1:
                maschi.append(Maschio(
                    start=x1,
                    end=x2,
                    length=x2 - x1,
                    index=index
                ))
                index += 1
                logger.debug(f"Maschio intermedio: {x1} - {x2} cm")

        # Maschio finale (dopo l'ultima apertura)
        last_opening = sorted_openings[-1]
        x_end = last_opening.get('x', 0) + last_opening.get('width', 0)
        if x_end < wall_length:
            maschi.append(Maschio(
                start=x_end,
                end=wall_length,
                length=wall_length - x_end,
                index=index
            ))
            logger.debug(f"Maschio finale: {x_end} - {wall_length} cm")

        # Calcola totali
        result.maschi = maschi
        result.total_length = sum(m.length for m in maschi)
        result.opening_length = wall_length - result.total_length

        logger.info(f"Identificati {len(maschi)} maschi murari, "
                   f"foratura: {result.foratura_ratio*100:.1f}%")

        return result

    @staticmethod
    def distribute_load(total_load: float, maschi: MaschiMurari,
                       wall_length: float) -> List[float]:
        """
        Ripartisce il carico verticale tra i maschi in proporzione alla lunghezza

        Args:
            total_load: Carico totale [kN]
            maschi: MaschiMurari con i maschi identificati
            wall_length: Lunghezza totale parete [cm]

        Returns:
            Lista di carichi per ciascun maschio [kN]
        """
        if wall_length <= 0 or len(maschi) == 0:
            return []

        loads = []
        for maschio in maschi:
            # Ripartizione proporzionale alla lunghezza
            load_ratio = maschio.length / wall_length
            loads.append(total_load * load_ratio)

        return loads

    @staticmethod
    def get_effective_height(wall_height_cm: float, opening_data: Dict) -> float:
        """
        Calcola l'altezza efficace del maschio considerando l'apertura

        Args:
            wall_height_cm: Altezza totale parete [cm]
            opening_data: Dict con 'y' e 'height' dell'apertura [cm]

        Returns:
            Altezza efficace del maschio [cm]
        """
        # L'altezza efficace è l'altezza della parete se l'apertura
        # non arriva fino in alto, altrimenti è l'altezza dell'apertura
        opening_y = opening_data.get('y', 0)
        opening_height = opening_data.get('height', 0)
        opening_top = opening_y + opening_height

        # Se l'apertura arriva fino al solaio
        if opening_top >= wall_height_cm * 0.95:  # Tolleranza 5%
            return wall_height_cm

        # Altrimenti l'altezza efficace potrebbe essere diversa
        # Per semplicità, usiamo l'altezza della parete
        return wall_height_cm

    @staticmethod
    def calculate_slenderness(height_cm: float, thickness_cm: float) -> float:
        """
        Calcola la snellezza della parete

        Args:
            height_cm: Altezza [cm]
            thickness_cm: Spessore [cm]

        Returns:
            Snellezza λ = h/t
        """
        if thickness_cm <= 0:
            return float('inf')
        return (height_cm / 100) / (thickness_cm / 100)

    @staticmethod
    def calculate_aspect_ratio(height_cm: float, length_cm: float) -> float:
        """
        Calcola il rapporto h/L per il fattore di forma

        Args:
            height_cm: Altezza [cm]
            length_cm: Lunghezza [cm]

        Returns:
            Rapporto h/L
        """
        if length_cm <= 0:
            return float('inf')
        return (height_cm / 100) / (length_cm / 100)
