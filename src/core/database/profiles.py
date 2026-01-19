"""
Database Profili Metallici secondo EN 10365
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta

Valori caratteristici da tabelle europee EN 10365.
Unita':
- h, b, tw, tf: mm
- A: cm2
- Ix, Iy: cm4
- Wx, Wy: cm3
- ix, iy: cm
"""

from typing import Dict, Optional, List
import functools


# Database completo profili HEA
HEA_PROFILES = {
    '100': {'h': 96, 'b': 100, 'tw': 5.0, 'tf': 8.0, 'A': 21.2, 'Ix': 349, 'Iy': 134, 'Wx': 72.8, 'Wy': 26.8, 'ix': 4.06, 'iy': 2.51},
    '120': {'h': 114, 'b': 120, 'tw': 5.0, 'tf': 8.0, 'A': 25.3, 'Ix': 606, 'Iy': 231, 'Wx': 106.3, 'Wy': 38.5, 'ix': 4.89, 'iy': 3.02},
    '140': {'h': 133, 'b': 140, 'tw': 5.5, 'tf': 8.5, 'A': 31.4, 'Ix': 1033, 'Iy': 389, 'Wx': 155.4, 'Wy': 55.6, 'ix': 5.73, 'iy': 3.52},
    '160': {'h': 152, 'b': 160, 'tw': 6.0, 'tf': 9.0, 'A': 38.8, 'Ix': 1673, 'Iy': 616, 'Wx': 220.1, 'Wy': 77.0, 'ix': 6.57, 'iy': 3.98},
    '180': {'h': 171, 'b': 180, 'tw': 6.0, 'tf': 9.5, 'A': 45.3, 'Ix': 2510, 'Iy': 925, 'Wx': 293.6, 'Wy': 102.7, 'ix': 7.45, 'iy': 4.52},
    '200': {'h': 190, 'b': 200, 'tw': 6.5, 'tf': 10.0, 'A': 53.8, 'Ix': 3692, 'Iy': 1336, 'Wx': 388.6, 'Wy': 133.6, 'ix': 8.28, 'iy': 4.98},
    '220': {'h': 210, 'b': 220, 'tw': 7.0, 'tf': 11.0, 'A': 64.3, 'Ix': 5410, 'Iy': 1955, 'Wx': 515.2, 'Wy': 177.7, 'ix': 9.17, 'iy': 5.51},
    '240': {'h': 230, 'b': 240, 'tw': 7.5, 'tf': 12.0, 'A': 76.8, 'Ix': 7763, 'Iy': 2769, 'Wx': 675.1, 'Wy': 230.7, 'ix': 10.05, 'iy': 6.00},
    '260': {'h': 250, 'b': 260, 'tw': 7.5, 'tf': 12.5, 'A': 86.8, 'Ix': 10450, 'Iy': 3668, 'Wx': 836.4, 'Wy': 282.1, 'ix': 10.97, 'iy': 6.50},
    '280': {'h': 270, 'b': 280, 'tw': 8.0, 'tf': 13.0, 'A': 97.3, 'Ix': 13670, 'Iy': 4763, 'Wx': 1013, 'Wy': 340.2, 'ix': 11.86, 'iy': 7.00},
    '300': {'h': 290, 'b': 300, 'tw': 8.5, 'tf': 14.0, 'A': 112.5, 'Ix': 18260, 'Iy': 6310, 'Wx': 1260, 'Wy': 420.6, 'ix': 12.74, 'iy': 7.49},
    '320': {'h': 310, 'b': 300, 'tw': 9.0, 'tf': 15.5, 'A': 124.4, 'Ix': 22930, 'Iy': 6985, 'Wx': 1479, 'Wy': 465.7, 'ix': 13.58, 'iy': 7.49},
    '340': {'h': 330, 'b': 300, 'tw': 9.5, 'tf': 16.5, 'A': 133.5, 'Ix': 27690, 'Iy': 7436, 'Wx': 1678, 'Wy': 495.7, 'ix': 14.40, 'iy': 7.46},
    '360': {'h': 350, 'b': 300, 'tw': 10.0, 'tf': 17.5, 'A': 142.8, 'Ix': 33090, 'Iy': 7887, 'Wx': 1891, 'Wy': 525.8, 'ix': 15.22, 'iy': 7.43},
    '400': {'h': 390, 'b': 300, 'tw': 11.0, 'tf': 19.0, 'A': 159.0, 'Ix': 45070, 'Iy': 8564, 'Wx': 2311, 'Wy': 570.9, 'ix': 16.84, 'iy': 7.34},
    '450': {'h': 440, 'b': 300, 'tw': 11.5, 'tf': 21.0, 'A': 178.0, 'Ix': 63720, 'Iy': 9465, 'Wx': 2896, 'Wy': 631.0, 'ix': 18.92, 'iy': 7.29},
    '500': {'h': 490, 'b': 300, 'tw': 12.0, 'tf': 23.0, 'A': 197.5, 'Ix': 86970, 'Iy': 10370, 'Wx': 3550, 'Wy': 691.1, 'ix': 20.98, 'iy': 7.24},
}

# Database completo profili HEB
HEB_PROFILES = {
    '100': {'h': 100, 'b': 100, 'tw': 6.0, 'tf': 10.0, 'A': 26.0, 'Ix': 450, 'Iy': 167, 'Wx': 89.9, 'Wy': 33.5, 'ix': 4.16, 'iy': 2.53},
    '120': {'h': 120, 'b': 120, 'tw': 6.5, 'tf': 11.0, 'A': 34.0, 'Ix': 864, 'Iy': 318, 'Wx': 144.1, 'Wy': 52.9, 'ix': 5.04, 'iy': 3.06},
    '140': {'h': 140, 'b': 140, 'tw': 7.0, 'tf': 12.0, 'A': 43.0, 'Ix': 1509, 'Iy': 550, 'Wx': 215.6, 'Wy': 78.5, 'ix': 5.93, 'iy': 3.58},
    '160': {'h': 160, 'b': 160, 'tw': 8.0, 'tf': 13.0, 'A': 54.3, 'Ix': 2492, 'Iy': 889, 'Wx': 311.5, 'Wy': 111.2, 'ix': 6.78, 'iy': 4.05},
    '180': {'h': 180, 'b': 180, 'tw': 8.5, 'tf': 14.0, 'A': 65.3, 'Ix': 3831, 'Iy': 1363, 'Wx': 425.7, 'Wy': 151.4, 'ix': 7.66, 'iy': 4.57},
    '200': {'h': 200, 'b': 200, 'tw': 9.0, 'tf': 15.0, 'A': 78.1, 'Ix': 5696, 'Iy': 2003, 'Wx': 569.6, 'Wy': 200.3, 'ix': 8.54, 'iy': 5.07},
    '220': {'h': 220, 'b': 220, 'tw': 9.5, 'tf': 16.0, 'A': 91.0, 'Ix': 8091, 'Iy': 2843, 'Wx': 735.5, 'Wy': 258.5, 'ix': 9.43, 'iy': 5.59},
    '240': {'h': 240, 'b': 240, 'tw': 10.0, 'tf': 17.0, 'A': 106.0, 'Ix': 11260, 'Iy': 3923, 'Wx': 938.3, 'Wy': 326.9, 'ix': 10.31, 'iy': 6.08},
    '260': {'h': 260, 'b': 260, 'tw': 10.0, 'tf': 17.5, 'A': 118.4, 'Ix': 14920, 'Iy': 5135, 'Wx': 1148, 'Wy': 395.0, 'ix': 11.22, 'iy': 6.58},
    '280': {'h': 280, 'b': 280, 'tw': 10.5, 'tf': 18.0, 'A': 131.4, 'Ix': 19270, 'Iy': 6595, 'Wx': 1376, 'Wy': 471.1, 'ix': 12.11, 'iy': 7.09},
    '300': {'h': 300, 'b': 300, 'tw': 11.0, 'tf': 19.0, 'A': 149.1, 'Ix': 25170, 'Iy': 8563, 'Wx': 1678, 'Wy': 570.9, 'ix': 13.00, 'iy': 7.58},
    '320': {'h': 320, 'b': 300, 'tw': 11.5, 'tf': 20.5, 'A': 161.3, 'Ix': 30820, 'Iy': 9239, 'Wx': 1926, 'Wy': 615.9, 'ix': 13.82, 'iy': 7.57},
    '340': {'h': 340, 'b': 300, 'tw': 12.0, 'tf': 21.5, 'A': 170.9, 'Ix': 36660, 'Iy': 9690, 'Wx': 2156, 'Wy': 646.0, 'ix': 14.65, 'iy': 7.53},
    '360': {'h': 360, 'b': 300, 'tw': 12.5, 'tf': 22.5, 'A': 180.6, 'Ix': 43190, 'Iy': 10140, 'Wx': 2400, 'Wy': 676.1, 'ix': 15.46, 'iy': 7.49},
    '400': {'h': 400, 'b': 300, 'tw': 13.5, 'tf': 24.0, 'A': 197.8, 'Ix': 57680, 'Iy': 10820, 'Wx': 2884, 'Wy': 721.3, 'ix': 17.08, 'iy': 7.40},
    '450': {'h': 450, 'b': 300, 'tw': 14.0, 'tf': 26.0, 'A': 218.0, 'Ix': 79890, 'Iy': 11720, 'Wx': 3551, 'Wy': 781.4, 'ix': 19.14, 'iy': 7.33},
    '500': {'h': 500, 'b': 300, 'tw': 14.5, 'tf': 28.0, 'A': 238.6, 'Ix': 107200, 'Iy': 12620, 'Wx': 4287, 'Wy': 841.6, 'ix': 21.19, 'iy': 7.27},
}

# Database completo profili IPE
IPE_PROFILES = {
    '80': {'h': 80, 'b': 46, 'tw': 3.8, 'tf': 5.2, 'A': 7.64, 'Ix': 80.1, 'Iy': 8.49, 'Wx': 20.0, 'Wy': 3.69, 'ix': 3.24, 'iy': 1.05},
    '100': {'h': 100, 'b': 55, 'tw': 4.1, 'tf': 5.7, 'A': 10.3, 'Ix': 171, 'Iy': 15.9, 'Wx': 34.2, 'Wy': 5.79, 'ix': 4.07, 'iy': 1.24},
    '120': {'h': 120, 'b': 64, 'tw': 4.4, 'tf': 6.3, 'A': 13.2, 'Ix': 318, 'Iy': 27.7, 'Wx': 53.0, 'Wy': 8.65, 'ix': 4.90, 'iy': 1.45},
    '140': {'h': 140, 'b': 73, 'tw': 4.7, 'tf': 6.9, 'A': 16.4, 'Ix': 541, 'Iy': 44.9, 'Wx': 77.3, 'Wy': 12.3, 'ix': 5.74, 'iy': 1.65},
    '160': {'h': 160, 'b': 82, 'tw': 5.0, 'tf': 7.4, 'A': 20.1, 'Ix': 869, 'Iy': 68.3, 'Wx': 108.7, 'Wy': 16.7, 'ix': 6.58, 'iy': 1.84},
    '180': {'h': 180, 'b': 91, 'tw': 5.3, 'tf': 8.0, 'A': 23.9, 'Ix': 1317, 'Iy': 101, 'Wx': 146.3, 'Wy': 22.2, 'ix': 7.42, 'iy': 2.05},
    '200': {'h': 200, 'b': 100, 'tw': 5.6, 'tf': 8.5, 'A': 28.5, 'Ix': 1943, 'Iy': 142, 'Wx': 194.3, 'Wy': 28.5, 'ix': 8.26, 'iy': 2.24},
    '220': {'h': 220, 'b': 110, 'tw': 5.9, 'tf': 9.2, 'A': 33.4, 'Ix': 2772, 'Iy': 205, 'Wx': 252.0, 'Wy': 37.3, 'ix': 9.11, 'iy': 2.48},
    '240': {'h': 240, 'b': 120, 'tw': 6.2, 'tf': 9.8, 'A': 39.1, 'Ix': 3892, 'Iy': 284, 'Wx': 324.3, 'Wy': 47.3, 'ix': 9.97, 'iy': 2.69},
    '270': {'h': 270, 'b': 135, 'tw': 6.6, 'tf': 10.2, 'A': 45.9, 'Ix': 5790, 'Iy': 420, 'Wx': 429.0, 'Wy': 62.2, 'ix': 11.23, 'iy': 3.02},
    '300': {'h': 300, 'b': 150, 'tw': 7.1, 'tf': 10.7, 'A': 53.8, 'Ix': 8356, 'Iy': 604, 'Wx': 557.1, 'Wy': 80.5, 'ix': 12.46, 'iy': 3.35},
    '330': {'h': 330, 'b': 160, 'tw': 7.5, 'tf': 11.5, 'A': 62.6, 'Ix': 11770, 'Iy': 788, 'Wx': 713.1, 'Wy': 98.5, 'ix': 13.71, 'iy': 3.55},
    '360': {'h': 360, 'b': 170, 'tw': 8.0, 'tf': 12.7, 'A': 72.7, 'Ix': 16270, 'Iy': 1043, 'Wx': 903.6, 'Wy': 122.8, 'ix': 14.95, 'iy': 3.79},
    '400': {'h': 400, 'b': 180, 'tw': 8.6, 'tf': 13.5, 'A': 84.5, 'Ix': 23130, 'Iy': 1318, 'Wx': 1156, 'Wy': 146.4, 'ix': 16.55, 'iy': 3.95},
    '450': {'h': 450, 'b': 190, 'tw': 9.4, 'tf': 14.6, 'A': 98.8, 'Ix': 33740, 'Iy': 1676, 'Wx': 1500, 'Wy': 176.4, 'ix': 18.48, 'iy': 4.12},
    '500': {'h': 500, 'b': 200, 'tw': 10.2, 'tf': 16.0, 'A': 116.0, 'Ix': 48200, 'Iy': 2142, 'Wx': 1928, 'Wy': 214.2, 'ix': 20.43, 'iy': 4.31},
    '550': {'h': 550, 'b': 210, 'tw': 11.1, 'tf': 17.2, 'A': 134.4, 'Ix': 67120, 'Iy': 2668, 'Wx': 2441, 'Wy': 254.1, 'ix': 22.35, 'iy': 4.45},
    '600': {'h': 600, 'b': 220, 'tw': 12.0, 'tf': 19.0, 'A': 156.0, 'Ix': 92080, 'Iy': 3387, 'Wx': 3069, 'Wy': 307.9, 'ix': 24.30, 'iy': 4.66},
}

# Database completo profili UPN (UNP)
UPN_PROFILES = {
    '80': {'h': 80, 'b': 45, 'tw': 6.0, 'tf': 8.0, 'A': 11.0, 'Ix': 106, 'Iy': 19.4, 'Wx': 26.5, 'Wy': 6.36, 'ix': 3.10, 'iy': 1.33},
    '100': {'h': 100, 'b': 50, 'tw': 6.0, 'tf': 8.5, 'A': 13.5, 'Ix': 206, 'Iy': 29.3, 'Wx': 41.2, 'Wy': 8.49, 'ix': 3.91, 'iy': 1.47},
    '120': {'h': 120, 'b': 55, 'tw': 7.0, 'tf': 9.0, 'A': 17.0, 'Ix': 364, 'Iy': 43.2, 'Wx': 60.7, 'Wy': 11.1, 'ix': 4.62, 'iy': 1.59},
    '140': {'h': 140, 'b': 60, 'tw': 7.0, 'tf': 10.0, 'A': 20.4, 'Ix': 605, 'Iy': 62.7, 'Wx': 86.4, 'Wy': 14.8, 'ix': 5.45, 'iy': 1.75},
    '160': {'h': 160, 'b': 65, 'tw': 7.5, 'tf': 10.5, 'A': 24.0, 'Ix': 925, 'Iy': 85.3, 'Wx': 116, 'Wy': 18.3, 'ix': 6.21, 'iy': 1.89},
    '180': {'h': 180, 'b': 70, 'tw': 8.0, 'tf': 11.0, 'A': 28.0, 'Ix': 1350, 'Iy': 114, 'Wx': 150, 'Wy': 22.4, 'ix': 6.95, 'iy': 2.02},
    '200': {'h': 200, 'b': 75, 'tw': 8.5, 'tf': 11.5, 'A': 32.2, 'Ix': 1910, 'Iy': 148, 'Wx': 191, 'Wy': 27.0, 'ix': 7.70, 'iy': 2.14},
    '220': {'h': 220, 'b': 80, 'tw': 9.0, 'tf': 12.5, 'A': 37.4, 'Ix': 2690, 'Iy': 197, 'Wx': 245, 'Wy': 33.6, 'ix': 8.48, 'iy': 2.30},
    '240': {'h': 240, 'b': 85, 'tw': 9.5, 'tf': 13.0, 'A': 42.3, 'Ix': 3600, 'Iy': 248, 'Wx': 300, 'Wy': 39.6, 'ix': 9.22, 'iy': 2.42},
    '260': {'h': 260, 'b': 90, 'tw': 10.0, 'tf': 14.0, 'A': 48.3, 'Ix': 4820, 'Iy': 317, 'Wx': 371, 'Wy': 47.7, 'ix': 9.99, 'iy': 2.56},
    '280': {'h': 280, 'b': 95, 'tw': 10.0, 'tf': 15.0, 'A': 53.3, 'Ix': 6280, 'Iy': 399, 'Wx': 448, 'Wy': 57.2, 'ix': 10.85, 'iy': 2.74},
    '300': {'h': 300, 'b': 100, 'tw': 10.0, 'tf': 16.0, 'A': 58.8, 'Ix': 8030, 'Iy': 495, 'Wx': 535, 'Wy': 67.8, 'ix': 11.69, 'iy': 2.90},
}

# Classi acciaio secondo NTC 2018
STEEL_GRADES = {
    'S235': {'fyk': 235, 'ftk': 360, 'E': 210000, 'G': 80769, 'gamma_m0': 1.05},
    'S275': {'fyk': 275, 'ftk': 430, 'E': 210000, 'G': 80769, 'gamma_m0': 1.05},
    'S355': {'fyk': 355, 'ftk': 510, 'E': 210000, 'G': 80769, 'gamma_m0': 1.05},
    'S450': {'fyk': 450, 'ftk': 550, 'E': 210000, 'G': 80769, 'gamma_m0': 1.05},
}

# Dizionario unificato dei profili
STEEL_PROFILES = {
    'HEA': HEA_PROFILES,
    'HEB': HEB_PROFILES,
    'IPE': IPE_PROFILES,
    'UPN': UPN_PROFILES,
}


class ProfilesDatabase:
    """Gestore centralizzato database profili metallici"""

    def __init__(self):
        self.profiles = STEEL_PROFILES
        self.steel_grades = STEEL_GRADES

    @functools.lru_cache(maxsize=128)
    def get_profile(self, profile_type: str, size: str) -> Optional[Dict]:
        """
        Restituisce dati profilo specifico

        Args:
            profile_type: Tipo profilo (HEA, HEB, IPE, UPN)
            size: Dimensione (es. '100', '200')

        Returns:
            Dict con proprietà profilo o None se non trovato
        """
        if profile_type not in self.profiles:
            return None

        return self.profiles[profile_type].get(size)

    def get_available_types(self) -> List[str]:
        """Restituisce tipi profilo disponibili"""
        return list(self.profiles.keys())

    def get_available_sizes(self, profile_type: str) -> List[str]:
        """Restituisce dimensioni disponibili per un tipo"""
        if profile_type not in self.profiles:
            return []

        # Ordina numericamente
        sizes = list(self.profiles[profile_type].keys())
        return sorted(sizes, key=lambda x: int(x))

    def get_steel_grade(self, grade: str) -> Optional[Dict]:
        """Restituisce proprietà classe acciaio"""
        return self.steel_grades.get(grade)

    def get_available_grades(self) -> List[str]:
        """Restituisce classi acciaio disponibili"""
        return list(self.steel_grades.keys())

    def get_profile_display_name(self, profile_type: str, size: str) -> str:
        """Restituisce nome visualizzato profilo"""
        return f"{profile_type} {size}"

    def search_profiles(self, min_Wx: float = 0, min_Ix: float = 0,
                        profile_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Cerca profili che soddisfano requisiti minimi

        Args:
            min_Wx: Modulo resistenza minimo (cm3)
            min_Ix: Momento inerzia minimo (cm4)
            profile_types: Lista tipi da cercare (default: tutti)

        Returns:
            Lista profili ordinati per Wx
        """
        results = []
        types_to_search = profile_types or self.get_available_types()

        for ptype in types_to_search:
            if ptype not in self.profiles:
                continue

            for size, data in self.profiles[ptype].items():
                if data.get('Wx', 0) >= min_Wx and data.get('Ix', 0) >= min_Ix:
                    results.append({
                        'type': ptype,
                        'size': size,
                        'name': f"{ptype} {size}",
                        **data
                    })

        # Ordina per Wx crescente
        return sorted(results, key=lambda x: x.get('Wx', 0))

    def get_optimal_profile(self, required_Wx: float, required_Ix: float,
                            profile_types: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Trova profilo ottimale (minimo che soddisfa requisiti)

        Args:
            required_Wx: Modulo resistenza richiesto (cm3)
            required_Ix: Momento inerzia richiesto (cm4)
            profile_types: Lista tipi da considerare

        Returns:
            Profilo ottimale o None
        """
        candidates = self.search_profiles(required_Wx, required_Ix, profile_types)

        if not candidates:
            return None

        # Il primo e' gia' il minimo per Wx
        return candidates[0]


# Istanza globale per accesso rapido
profiles_db = ProfilesDatabase()
