"""
Database Profili Metallici - Catalogo profili standard
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta

Contiene profili: HEA, HEB, HEM, IPE, UPN, L (angolari), tubolari
Dati geometrici secondo norme europee EN 10034, EN 10279
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SteelProfile:
    """Rappresenta un profilo metallico"""
    name: str           # Nome profilo (es. "HEA 200")
    category: str       # Categoria (HEA, HEB, IPE, UPN, L, etc.)
    h: float           # Altezza [mm]
    b: float           # Larghezza ala [mm]
    tw: float          # Spessore anima [mm]
    tf: float          # Spessore ala [mm]
    r: float           # Raggio raccordo [mm]
    A: float           # Area sezione [cm²]
    Iy: float          # Momento inerzia asse forte [cm⁴]
    Iz: float          # Momento inerzia asse debole [cm⁴]
    Wy: float          # Modulo resistenza asse forte [cm³]
    Wz: float          # Modulo resistenza asse debole [cm³]
    iy: float          # Raggio giratore asse forte [cm]
    iz: float          # Raggio giratore asse debole [cm]
    mass: float        # Massa per unità di lunghezza [kg/m]

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'category': self.category,
            'h': self.h,
            'b': self.b,
            'tw': self.tw,
            'tf': self.tf,
            'r': self.r,
            'A': self.A,
            'Iy': self.Iy,
            'Iz': self.Iz,
            'Wy': self.Wy,
            'Wz': self.Wz,
            'iy': self.iy,
            'iz': self.iz,
            'mass': self.mass
        }


class ProfilesDatabase:
    """Database profili metallici standard"""

    def __init__(self):
        self.profiles: Dict[str, SteelProfile] = {}
        self._load_standard_profiles()

    def _load_standard_profiles(self):
        """Carica profili standard"""
        self._load_hea_profiles()
        self._load_heb_profiles()
        self._load_hem_profiles()
        self._load_ipe_profiles()
        self._load_upn_profiles()
        self._load_angular_profiles()
        self._load_tubular_profiles()

    def _load_hea_profiles(self):
        """Carica profili HEA (ali larghe leggeri)"""
        # Formato: (h, b, tw, tf, r, A, Iy, Iz, Wy, Wz, iy, iz, mass)
        hea_data = {
            'HEA 100': (96, 100, 5.0, 8.0, 12, 21.2, 349, 134, 72.8, 26.8, 4.06, 2.51, 16.7),
            'HEA 120': (114, 120, 5.0, 8.0, 12, 25.3, 606, 231, 106, 38.5, 4.89, 3.02, 19.9),
            'HEA 140': (133, 140, 5.5, 8.5, 12, 31.4, 1033, 389, 155, 55.6, 5.73, 3.52, 24.7),
            'HEA 160': (152, 160, 6.0, 9.0, 15, 38.8, 1673, 616, 220, 77.0, 6.57, 3.98, 30.4),
            'HEA 180': (171, 180, 6.0, 9.5, 15, 45.3, 2510, 925, 294, 103, 7.45, 4.52, 35.5),
            'HEA 200': (190, 200, 6.5, 10.0, 18, 53.8, 3692, 1336, 389, 134, 8.28, 4.98, 42.3),
            'HEA 220': (210, 220, 7.0, 11.0, 18, 64.3, 5410, 1955, 515, 178, 9.17, 5.51, 50.5),
            'HEA 240': (230, 240, 7.5, 12.0, 21, 76.8, 7763, 2769, 675, 231, 10.1, 6.00, 60.3),
            'HEA 260': (250, 260, 7.5, 12.5, 24, 86.8, 10450, 3668, 836, 282, 11.0, 6.50, 68.2),
            'HEA 280': (270, 280, 8.0, 13.0, 24, 97.3, 13670, 4763, 1013, 340, 11.9, 7.00, 76.4),
            'HEA 300': (290, 300, 8.5, 14.0, 27, 112, 18260, 6310, 1260, 421, 12.7, 7.49, 88.3),
            'HEA 320': (310, 300, 9.0, 15.5, 27, 124, 22930, 6985, 1479, 466, 13.6, 7.49, 97.6),
            'HEA 340': (330, 300, 9.5, 16.5, 27, 133, 27690, 7436, 1678, 496, 14.4, 7.46, 105),
            'HEA 360': (350, 300, 10.0, 17.5, 27, 143, 33090, 7887, 1891, 526, 15.2, 7.43, 112),
            'HEA 400': (390, 300, 11.0, 19.0, 27, 159, 45070, 8564, 2311, 571, 16.8, 7.34, 125),
            'HEA 450': (440, 300, 11.5, 21.0, 27, 178, 63720, 9465, 2896, 631, 18.9, 7.29, 140),
            'HEA 500': (490, 300, 12.0, 23.0, 27, 198, 86970, 10370, 3550, 691, 21.0, 7.24, 155),
        }

        for name, data in hea_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='HEA',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_heb_profiles(self):
        """Carica profili HEB (ali larghe normali)"""
        heb_data = {
            'HEB 100': (100, 100, 6.0, 10.0, 12, 26.0, 450, 167, 89.9, 33.5, 4.16, 2.53, 20.4),
            'HEB 120': (120, 120, 6.5, 11.0, 12, 34.0, 864, 318, 144, 52.9, 5.04, 3.06, 26.7),
            'HEB 140': (140, 140, 7.0, 12.0, 12, 43.0, 1509, 550, 216, 78.5, 5.93, 3.58, 33.7),
            'HEB 160': (160, 160, 8.0, 13.0, 15, 54.3, 2492, 889, 311, 111, 6.78, 4.05, 42.6),
            'HEB 180': (180, 180, 8.5, 14.0, 15, 65.3, 3831, 1363, 426, 151, 7.66, 4.57, 51.2),
            'HEB 200': (200, 200, 9.0, 15.0, 18, 78.1, 5696, 2003, 570, 200, 8.54, 5.07, 61.3),
            'HEB 220': (220, 220, 9.5, 16.0, 18, 91.0, 8091, 2843, 736, 258, 9.43, 5.59, 71.5),
            'HEB 240': (240, 240, 10.0, 17.0, 21, 106, 11260, 3923, 938, 327, 10.3, 6.08, 83.2),
            'HEB 260': (260, 260, 10.0, 17.5, 24, 118, 14920, 5135, 1148, 395, 11.2, 6.58, 93.0),
            'HEB 280': (280, 280, 10.5, 18.0, 24, 131, 19270, 6595, 1376, 471, 12.1, 7.09, 103),
            'HEB 300': (300, 300, 11.0, 19.0, 27, 149, 25170, 8563, 1678, 571, 13.0, 7.58, 117),
            'HEB 320': (320, 300, 11.5, 20.5, 27, 161, 30820, 9239, 1926, 616, 13.8, 7.57, 127),
            'HEB 340': (340, 300, 12.0, 21.5, 27, 171, 36660, 9690, 2156, 646, 14.6, 7.53, 134),
            'HEB 360': (360, 300, 12.5, 22.5, 27, 181, 43190, 10140, 2400, 676, 15.4, 7.49, 142),
            'HEB 400': (400, 300, 13.5, 24.0, 27, 198, 57680, 10820, 2884, 721, 17.1, 7.40, 155),
            'HEB 450': (450, 300, 14.0, 26.0, 27, 218, 79890, 11720, 3551, 781, 19.1, 7.33, 171),
            'HEB 500': (500, 300, 14.5, 28.0, 27, 239, 107200, 12620, 4287, 842, 21.2, 7.27, 187),
        }

        for name, data in heb_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='HEB',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_hem_profiles(self):
        """Carica profili HEM (ali larghe pesanti)"""
        hem_data = {
            'HEM 100': (120, 106, 12.0, 20.0, 12, 53.2, 1143, 399, 190, 75.3, 4.63, 2.74, 41.8),
            'HEM 120': (140, 126, 12.5, 21.0, 12, 66.4, 2018, 703, 288, 112, 5.51, 3.25, 52.1),
            'HEM 140': (160, 146, 13.0, 22.0, 12, 80.6, 3291, 1144, 411, 157, 6.39, 3.77, 63.2),
            'HEM 160': (180, 166, 14.0, 23.0, 15, 97.1, 5098, 1759, 566, 212, 7.24, 4.26, 76.2),
            'HEM 180': (200, 186, 14.5, 24.0, 15, 113, 7483, 2580, 748, 277, 8.13, 4.77, 88.9),
            'HEM 200': (220, 206, 15.0, 25.0, 18, 131, 10640, 3651, 967, 354, 9.00, 5.28, 103),
            'HEM 220': (240, 226, 15.5, 26.0, 18, 149, 14600, 5012, 1217, 444, 9.89, 5.80, 117),
            'HEM 240': (270, 248, 18.0, 32.0, 21, 200, 24290, 8153, 1799, 657, 11.0, 6.37, 157),
            'HEM 260': (290, 268, 18.0, 32.5, 24, 220, 31310, 10450, 2159, 780, 11.9, 6.89, 172),
            'HEM 280': (310, 288, 18.5, 33.0, 24, 240, 39550, 13160, 2551, 914, 12.8, 7.40, 189),
            'HEM 300': (340, 310, 21.0, 39.0, 27, 303, 59200, 19400, 3482, 1252, 14.0, 8.00, 238),
            'HEM 320': (359, 309, 21.0, 40.0, 27, 312, 68130, 19710, 3796, 1276, 14.8, 7.95, 245),
            'HEM 340': (377, 309, 21.0, 40.0, 27, 316, 76370, 19710, 4052, 1276, 15.6, 7.90, 248),
            'HEM 360': (395, 308, 21.0, 40.0, 27, 319, 84870, 19520, 4298, 1267, 16.3, 7.82, 250),
            'HEM 400': (432, 307, 21.0, 40.0, 27, 326, 104100, 19340, 4820, 1260, 17.9, 7.70, 256),
        }

        for name, data in hem_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='HEM',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_ipe_profiles(self):
        """Carica profili IPE (profili a I europei)"""
        ipe_data = {
            'IPE 80': (80, 46, 3.8, 5.2, 5, 7.64, 80.1, 8.49, 20.0, 3.69, 3.24, 1.05, 6.0),
            'IPE 100': (100, 55, 4.1, 5.7, 7, 10.3, 171, 15.9, 34.2, 5.79, 4.07, 1.24, 8.1),
            'IPE 120': (120, 64, 4.4, 6.3, 7, 13.2, 318, 27.7, 53.0, 8.65, 4.90, 1.45, 10.4),
            'IPE 140': (140, 73, 4.7, 6.9, 7, 16.4, 541, 44.9, 77.3, 12.3, 5.74, 1.65, 12.9),
            'IPE 160': (160, 82, 5.0, 7.4, 9, 20.1, 869, 68.3, 109, 16.7, 6.58, 1.84, 15.8),
            'IPE 180': (180, 91, 5.3, 8.0, 9, 23.9, 1317, 101, 146, 22.2, 7.42, 2.05, 18.8),
            'IPE 200': (200, 100, 5.6, 8.5, 12, 28.5, 1943, 142, 194, 28.5, 8.26, 2.24, 22.4),
            'IPE 220': (220, 110, 5.9, 9.2, 12, 33.4, 2772, 205, 252, 37.3, 9.11, 2.48, 26.2),
            'IPE 240': (240, 120, 6.2, 9.8, 15, 39.1, 3892, 284, 324, 47.3, 9.97, 2.69, 30.7),
            'IPE 270': (270, 135, 6.6, 10.2, 15, 45.9, 5790, 420, 429, 62.2, 11.2, 3.02, 36.1),
            'IPE 300': (300, 150, 7.1, 10.7, 15, 53.8, 8356, 604, 557, 80.5, 12.5, 3.35, 42.2),
            'IPE 330': (330, 160, 7.5, 11.5, 18, 62.6, 11770, 788, 713, 98.5, 13.7, 3.55, 49.1),
            'IPE 360': (360, 170, 8.0, 12.7, 18, 72.7, 16270, 1043, 904, 123, 15.0, 3.79, 57.1),
            'IPE 400': (400, 180, 8.6, 13.5, 21, 84.5, 23130, 1318, 1156, 146, 16.5, 3.95, 66.3),
            'IPE 450': (450, 190, 9.4, 14.6, 21, 98.8, 33740, 1676, 1500, 176, 18.5, 4.12, 77.6),
            'IPE 500': (500, 200, 10.2, 16.0, 21, 116, 48200, 2142, 1928, 214, 20.4, 4.31, 90.7),
            'IPE 550': (550, 210, 11.1, 17.2, 24, 134, 67120, 2668, 2441, 254, 22.3, 4.45, 106),
            'IPE 600': (600, 220, 12.0, 19.0, 24, 156, 92080, 3387, 3069, 308, 24.3, 4.66, 122),
        }

        for name, data in ipe_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='IPE',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_upn_profiles(self):
        """Carica profili UPN (profili a U)"""
        upn_data = {
            'UPN 50': (50, 38, 5.0, 7.0, 7, 7.12, 26.4, 9.12, 10.6, 3.75, 1.92, 1.13, 5.59),
            'UPN 65': (65, 42, 5.5, 7.5, 8, 9.03, 57.5, 14.1, 17.7, 5.07, 2.52, 1.25, 7.09),
            'UPN 80': (80, 45, 6.0, 8.0, 8, 11.0, 106, 19.4, 26.5, 6.36, 3.10, 1.33, 8.64),
            'UPN 100': (100, 50, 6.0, 8.5, 9, 13.5, 206, 29.3, 41.2, 8.49, 3.91, 1.47, 10.6),
            'UPN 120': (120, 55, 7.0, 9.0, 9, 17.0, 364, 43.2, 60.7, 11.1, 4.62, 1.59, 13.4),
            'UPN 140': (140, 60, 7.0, 10.0, 10, 20.4, 605, 62.7, 86.4, 14.8, 5.45, 1.75, 16.0),
            'UPN 160': (160, 65, 7.5, 10.5, 11, 24.0, 925, 85.3, 116, 18.3, 6.21, 1.89, 18.8),
            'UPN 180': (180, 70, 8.0, 11.0, 11, 28.0, 1350, 114, 150, 22.4, 6.95, 2.02, 22.0),
            'UPN 200': (200, 75, 8.5, 11.5, 12, 32.2, 1910, 148, 191, 27.0, 7.70, 2.14, 25.3),
            'UPN 220': (220, 80, 9.0, 12.5, 12, 37.4, 2690, 197, 245, 33.6, 8.48, 2.30, 29.4),
            'UPN 240': (240, 85, 9.5, 13.0, 13, 42.3, 3600, 248, 300, 39.6, 9.22, 2.42, 33.2),
            'UPN 260': (260, 90, 10.0, 14.0, 14, 48.3, 4820, 317, 371, 47.7, 9.99, 2.56, 37.9),
            'UPN 280': (280, 95, 10.0, 15.0, 15, 53.3, 6280, 399, 448, 57.2, 10.9, 2.74, 41.8),
            'UPN 300': (300, 100, 10.0, 16.0, 16, 58.8, 8030, 495, 535, 67.8, 11.7, 2.90, 46.2),
            'UPN 320': (320, 100, 14.0, 17.5, 18, 75.8, 10870, 597, 679, 80.6, 12.1, 2.81, 59.5),
            'UPN 350': (350, 100, 14.0, 16.0, 16, 77.3, 12840, 570, 734, 75.0, 12.9, 2.72, 60.6),
            'UPN 380': (380, 102, 13.5, 16.0, 16, 80.4, 15760, 615, 829, 78.7, 14.0, 2.77, 63.1),
            'UPN 400': (400, 110, 14.0, 18.0, 18, 91.5, 20350, 846, 1020, 102, 14.9, 3.04, 71.8),
        }

        for name, data in upn_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='UPN',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_angular_profiles(self):
        """Carica profili angolari a L (lati uguali)"""
        angular_data = {
            'L 30x30x3': (30, 30, 3.0, 3.0, 5, 1.74, 1.20, 1.20, 0.57, 0.57, 0.83, 0.83, 1.36),
            'L 40x40x4': (40, 40, 4.0, 4.0, 6, 3.08, 3.72, 3.72, 1.30, 1.30, 1.10, 1.10, 2.42),
            'L 50x50x5': (50, 50, 5.0, 5.0, 7, 4.80, 9.04, 9.04, 2.53, 2.53, 1.37, 1.37, 3.77),
            'L 60x60x6': (60, 60, 6.0, 6.0, 8, 6.91, 18.4, 18.4, 4.29, 4.29, 1.63, 1.63, 5.42),
            'L 70x70x7': (70, 70, 7.0, 7.0, 9, 9.40, 34.7, 34.7, 6.93, 6.93, 1.92, 1.92, 7.38),
            'L 80x80x8': (80, 80, 8.0, 8.0, 10, 12.3, 57.5, 57.5, 10.0, 10.0, 2.16, 2.16, 9.63),
            'L 90x90x9': (90, 90, 9.0, 9.0, 11, 15.5, 90.4, 90.4, 14.0, 14.0, 2.41, 2.41, 12.2),
            'L 100x100x10': (100, 100, 10.0, 10.0, 12, 19.2, 138, 138, 19.2, 19.2, 2.68, 2.68, 15.0),
            'L 120x120x12': (120, 120, 12.0, 12.0, 13, 27.5, 286, 286, 33.2, 33.2, 3.22, 3.22, 21.6),
            'L 150x150x15': (150, 150, 15.0, 15.0, 16, 43.0, 694, 694, 64.5, 64.5, 4.02, 4.02, 33.8),
        }

        for name, data in angular_data.items():
            self.profiles[name] = SteelProfile(
                name=name, category='L',
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def _load_tubular_profiles(self):
        """Carica profili tubolari quadri e rettangolari"""
        tubular_data = {
            'SHS 40x40x3': (40, 40, 3.0, 3.0, 3, 4.25, 7.62, 7.62, 3.81, 3.81, 1.34, 1.34, 3.34),
            'SHS 50x50x3': (50, 50, 3.0, 3.0, 3, 5.41, 15.3, 15.3, 6.14, 6.14, 1.68, 1.68, 4.25),
            'SHS 60x60x4': (60, 60, 4.0, 4.0, 4, 8.55, 32.4, 32.4, 10.8, 10.8, 1.95, 1.95, 6.71),
            'SHS 80x80x4': (80, 80, 4.0, 4.0, 4, 11.7, 79.8, 79.8, 20.0, 20.0, 2.61, 2.61, 9.22),
            'SHS 100x100x5': (100, 100, 5.0, 5.0, 5, 18.4, 186, 186, 37.1, 37.1, 3.18, 3.18, 14.4),
            'SHS 120x120x6': (120, 120, 6.0, 6.0, 6, 26.4, 371, 371, 61.9, 61.9, 3.75, 3.75, 20.7),
            'SHS 150x150x8': (150, 150, 8.0, 8.0, 8, 43.2, 857, 857, 114, 114, 4.45, 4.45, 33.9),
            'RHS 60x40x3': (60, 40, 3.0, 3.0, 3, 5.41, 18.7, 9.61, 6.24, 4.80, 1.86, 1.33, 4.25),
            'RHS 80x40x4': (80, 40, 4.0, 4.0, 4, 8.55, 48.4, 16.2, 12.1, 8.10, 2.38, 1.38, 6.71),
            'RHS 100x50x5': (100, 50, 5.0, 5.0, 5, 13.4, 114, 36.3, 22.7, 14.5, 2.91, 1.65, 10.5),
            'RHS 120x60x6': (120, 60, 6.0, 6.0, 6, 19.2, 223, 69.7, 37.1, 23.2, 3.41, 1.90, 15.1),
            'RHS 150x100x6': (150, 100, 6.0, 6.0, 6, 27.4, 544, 275, 72.5, 55.0, 4.45, 3.17, 21.5),
            'RHS 200x100x8': (200, 100, 8.0, 8.0, 8, 43.2, 1330, 441, 133, 88.2, 5.55, 3.19, 33.9),
        }

        for name, data in tubular_data.items():
            category = 'SHS' if name.startswith('SHS') else 'RHS'
            self.profiles[name] = SteelProfile(
                name=name, category=category,
                h=data[0], b=data[1], tw=data[2], tf=data[3], r=data[4],
                A=data[5], Iy=data[6], Iz=data[7], Wy=data[8], Wz=data[9],
                iy=data[10], iz=data[11], mass=data[12]
            )

    def get_profile(self, name: str) -> Optional[SteelProfile]:
        """Restituisce un profilo per nome"""
        return self.profiles.get(name)

    def get_profiles_by_category(self, category: str) -> List[SteelProfile]:
        """Restituisce tutti i profili di una categoria"""
        return [p for p in self.profiles.values() if p.category == category]

    def get_all_profiles(self) -> List[SteelProfile]:
        """Restituisce tutti i profili"""
        return list(self.profiles.values())

    def get_categories(self) -> List[str]:
        """Restituisce le categorie disponibili"""
        return list(set(p.category for p in self.profiles.values()))

    def search_profiles(self, min_Wy: float = 0, max_mass: float = float('inf'),
                       categories: List[str] = None) -> List[SteelProfile]:
        """
        Cerca profili che soddisfano i criteri

        Args:
            min_Wy: Modulo resistenza minimo [cm³]
            max_mass: Massa massima [kg/m]
            categories: Lista categorie da includere

        Returns:
            Lista profili che soddisfano i criteri
        """
        results = []
        for profile in self.profiles.values():
            if categories and profile.category not in categories:
                continue
            if profile.Wy >= min_Wy and profile.mass <= max_mass:
                results.append(profile)
        return sorted(results, key=lambda p: p.mass)

    def suggest_profile(self, required_Wy: float, categories: List[str] = None) -> Optional[SteelProfile]:
        """
        Suggerisce il profilo più leggero che soddisfa il requisito

        Args:
            required_Wy: Modulo resistenza richiesto [cm³]
            categories: Categorie da considerare (default: HEA, HEB, IPE)

        Returns:
            Profilo ottimale o None
        """
        if categories is None:
            categories = ['HEA', 'HEB', 'IPE']

        candidates = self.search_profiles(min_Wy=required_Wy, categories=categories)
        return candidates[0] if candidates else None

    def export_to_json(self, filepath: str):
        """Esporta database in JSON"""
        data = {name: profile.to_dict() for name, profile in self.profiles.items()}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Singleton per accesso globale
_profiles_db = None

def get_profiles_database() -> ProfilesDatabase:
    """Restituisce l'istanza singleton del database profili"""
    global _profiles_db
    if _profiles_db is None:
        _profiles_db = ProfilesDatabase()
    return _profiles_db
