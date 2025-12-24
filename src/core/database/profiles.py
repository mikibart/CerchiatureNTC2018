"""
Database Profili Metallici
"""

# Database profili (HEA, HEB, IPE, UNP, etc.)
STEEL_PROFILES = {
    # HEA
    'HEA100': {'Wx': 72.8, 'Ix': 349, 'A': 21.2, 'h': 96, 'b': 100},
    'HEA120': {'Wx': 106.3, 'Ix': 606, 'A': 25.3, 'h': 114, 'b': 120},
    # TODO: Aggiungere tutti i profili
}

# Classi acciaio
STEEL_GRADES = {
    'S235': {'fyk': 235, 'ftk': 360, 'E': 210000},
    'S275': {'fyk': 275, 'ftk': 430, 'E': 210000},
    'S355': {'fyk': 355, 'ftk': 510, 'E': 210000},
}
