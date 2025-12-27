"""
Project Templates - Template progetti preconfigurati
Calcolatore Cerchiature NTC 2018
Arch. Michelangelo Bartolotta
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ProjectTemplate:
    """Rappresenta un template di progetto"""
    name: str
    description: str
    category: str
    wall_data: dict
    masonry_data: dict
    openings: List[dict]
    reinforcement: dict
    icon: str = ''


# Template predefiniti
TEMPLATES = {
    # ===== APERTURE PORTE =====
    'porta_interna': ProjectTemplate(
        name="Porta Interna Standard",
        description="Apertura porta interna 80x210 cm in muratura esistente",
        category="Porte",
        wall_data={
            'length': 300,
            'height': 300,
            'thickness': 30
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 110,
            'y': 0,
            'width': 80,
            'height': 210,
            'existing': False
        }],
        reinforcement={
            'profilo': 'HEA 120',
            'tipo_acciaio': 'S275'
        },
        icon='door'
    ),

    'porta_esterna': ProjectTemplate(
        name="Porta Esterna / Ingresso",
        description="Apertura porta ingresso 100x220 cm",
        category="Porte",
        wall_data={
            'length': 400,
            'height': 300,
            'thickness': 45
        },
        masonry_data={
            'type': 'Muratura in pietra a spacco con buona tessitura',
            'fcm': 2.0,
            'tau0': 0.056,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 150,
            'y': 0,
            'width': 100,
            'height': 220,
            'existing': False
        }],
        reinforcement={
            'profilo': 'HEA 140',
            'tipo_acciaio': 'S275'
        },
        icon='door_front'
    ),

    'portafinestra': ProjectTemplate(
        name="Porta-Finestra",
        description="Apertura porta-finestra 120x230 cm per accesso balcone/terrazzo",
        category="Porte",
        wall_data={
            'length': 400,
            'height': 300,
            'thickness': 35
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 140,
            'y': 0,
            'width': 120,
            'height': 230,
            'existing': False
        }],
        reinforcement={
            'profilo': 'HEA 160',
            'tipo_acciaio': 'S275'
        },
        icon='door_sliding'
    ),

    # ===== APERTURE FINESTRE =====
    'finestra_standard': ProjectTemplate(
        name="Finestra Standard",
        description="Apertura finestra 120x120 cm",
        category="Finestre",
        wall_data={
            'length': 350,
            'height': 300,
            'thickness': 30
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 115,
            'y': 90,
            'width': 120,
            'height': 120,
            'existing': False
        }],
        reinforcement={
            'profilo': 'HEA 100',
            'tipo_acciaio': 'S275'
        },
        icon='window'
    ),

    'finestra_grande': ProjectTemplate(
        name="Finestra Grande",
        description="Apertura finestra 180x140 cm per soggiorno",
        category="Finestre",
        wall_data={
            'length': 450,
            'height': 300,
            'thickness': 35
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 135,
            'y': 80,
            'width': 180,
            'height': 140,
            'existing': False
        }],
        reinforcement={
            'profilo': 'HEA 160',
            'tipo_acciaio': 'S275'
        },
        icon='window_maximize'
    ),

    'finestra_arco': ProjectTemplate(
        name="Finestra ad Arco",
        description="Apertura finestra con arco a tutto sesto",
        category="Finestre",
        wall_data={
            'length': 400,
            'height': 350,
            'thickness': 40
        },
        masonry_data={
            'type': 'Muratura in pietra a spacco con buona tessitura',
            'fcm': 2.0,
            'tau0': 0.056,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Ad arco',
            'x': 140,
            'y': 80,
            'width': 120,
            'height': 200,
            'existing': False,
            'arch_data': {
                'arch_type': 'Tutto sesto',
                'impost_height': 140,
                'arch_rise': 60
            }
        }],
        reinforcement={
            'profilo': 'HEA 140',
            'tipo_acciaio': 'S275'
        },
        icon='arch'
    ),

    # ===== APERTURE MULTIPLE =====
    'due_finestre': ProjectTemplate(
        name="Due Finestre Affiancate",
        description="Due aperture finestra 100x120 cm",
        category="Multiple",
        wall_data={
            'length': 500,
            'height': 300,
            'thickness': 30
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[
            {
                'type': 'Rettangolare',
                'x': 80,
                'y': 90,
                'width': 100,
                'height': 120,
                'existing': False
            },
            {
                'type': 'Rettangolare',
                'x': 320,
                'y': 90,
                'width': 100,
                'height': 120,
                'existing': False
            }
        ],
        reinforcement={
            'profilo': 'HEA 100',
            'tipo_acciaio': 'S275'
        },
        icon='columns'
    ),

    'porta_finestra_affiancate': ProjectTemplate(
        name="Porta e Finestra",
        description="Porta 90x210 e finestra 100x120 affiancate",
        category="Multiple",
        wall_data={
            'length': 500,
            'height': 300,
            'thickness': 35
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[
            {
                'type': 'Rettangolare',
                'x': 80,
                'y': 0,
                'width': 90,
                'height': 210,
                'existing': False
            },
            {
                'type': 'Rettangolare',
                'x': 310,
                'y': 90,
                'width': 100,
                'height': 120,
                'existing': False
            }
        ],
        reinforcement={
            'profilo': 'HEA 120',
            'tipo_acciaio': 'S275'
        },
        icon='layout'
    ),

    # ===== CASI SPECIALI =====
    'allargamento_porta': ProjectTemplate(
        name="Allargamento Porta Esistente",
        description="Allargamento porta da 70 a 90 cm",
        category="Modifiche",
        wall_data={
            'length': 300,
            'height': 300,
            'thickness': 30
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Rettangolare',
            'x': 105,
            'y': 0,
            'width': 90,
            'height': 210,
            'existing': True  # Modificata da esistente
        }],
        reinforcement={
            'profilo': 'HEA 120',
            'tipo_acciaio': 'S275'
        },
        icon='resize'
    ),

    'nicchia_armadio': ProjectTemplate(
        name="Nicchia per Armadio a Muro",
        description="Nicchia 120x250 profondità 60 cm",
        category="Nicchie",
        wall_data={
            'length': 350,
            'height': 300,
            'thickness': 65
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Nicchia',
            'x': 115,
            'y': 0,
            'width': 120,
            'height': 250,
            'existing': False,
            'niche_data': {
                'depth': 60,
                'is_niche': True,
                'has_shelves': True,
                'n_shelves': 4
            }
        }],
        reinforcement={
            'profilo': 'L 80x80x8',
            'tipo_acciaio': 'S275'
        },
        icon='archive'
    ),

    'chiusura_vano': ProjectTemplate(
        name="Chiusura Vano Esistente",
        description="Chiusura porta esistente 90x210 cm",
        category="Chiusure",
        wall_data={
            'length': 300,
            'height': 300,
            'thickness': 30
        },
        masonry_data={
            'type': 'Muratura in mattoni pieni e malta di calce',
            'fcm': 2.4,
            'tau0': 0.06,
            'E': 1500,
            'G': 500,
            'knowledge_level': 'LC2',
            'FC': 1.20
        },
        openings=[{
            'type': 'Chiusura vano esistente',
            'x': 105,
            'y': 0,
            'width': 90,
            'height': 210,
            'existing': True,
            'closure_data': {
                'type': 'Muratura piena',
                'material': 'Mattoni forati',
                'connection': 'Ammorsamento'
            }
        }],
        reinforcement={},
        icon='door_closed'
    ),
}


def get_all_templates() -> Dict[str, ProjectTemplate]:
    """Restituisce tutti i template disponibili"""
    return TEMPLATES


def get_template(template_id: str) -> ProjectTemplate:
    """Restituisce un template specifico"""
    return TEMPLATES.get(template_id)


def get_templates_by_category(category: str) -> Dict[str, ProjectTemplate]:
    """Restituisce template di una categoria"""
    return {k: v for k, v in TEMPLATES.items() if v.category == category}


def get_categories() -> List[str]:
    """Restituisce le categorie disponibili"""
    return list(set(t.category for t in TEMPLATES.values()))


def template_to_project_data(template: ProjectTemplate) -> dict:
    """Converte un template in dati progetto"""
    return {
        'wall': template.wall_data.copy(),
        'masonry': template.masonry_data.copy(),
        'openings': [op.copy() for op in template.openings],
        'reinforcement': template.reinforcement.copy(),
        'template_name': template.name
    }
