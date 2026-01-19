"""
Widget per visualizzazione grafici risultati
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class ResultsCanvas(FigureCanvas):
    """Canvas per visualizzazione grafici risultati"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 6), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)

    def plot_capacity_curves(self, results):
        """Traccia curve di capacità fisicamente corrette per muratura"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)
        ax.set_xlabel('Spostamento [mm]')
        ax.set_ylabel('Taglio [kN]')
        ax.set_title('Curve di Capacità - Confronto Stato di Fatto/Progetto')
        ax.grid(True, alpha=0.3)

        # Parametri base per comportamento muratura
        mu_ductility_base = 2.5  # Duttilità tipica muratura (2-3)
        beta_degradation_base = 0.3  # Fattore di degrado post-picco (0.2-0.4)

        # Stato di fatto
        if 'original' in results:
            K_orig = results['original']['K']  # Rigidezza [kN/m]
            V_max_orig = results['original']['V_min']  # Resistenza [kN]

            # Determina il meccanismo di rottura critico
            if results['original']['V_t1'] == results['original']['V_min']:
                mechanism = 'shear'  # Taglio puro - comportamento più fragile
                mu_ductility = 2.0
                beta_degradation = 0.4
            elif results['original']['V_t3'] == results['original']['V_min']:
                mechanism = 'flexure'  # Presso-flessione - più duttile
                mu_ductility = 3.0
                beta_degradation = 0.2
            else:
                mechanism = 'mixed'  # Misto
                mu_ductility = mu_ductility_base
                beta_degradation = beta_degradation_base

            # Calcola spostamenti caratteristici
            d_yield_orig = V_max_orig / K_orig * 1000  # [mm] spostamento al limite elastico
            d_max_orig = d_yield_orig * mu_ductility  # [mm] spostamento ultimo

            # Genera punti curva
            d = np.linspace(0, d_max_orig * 1.2, 200)
            V = np.zeros_like(d)

            for i, di in enumerate(d):
                if di <= d_yield_orig:
                    # Tratto elastico lineare
                    V[i] = K_orig * di / 1000  # K in kN/m, d in mm
                elif di <= d_max_orig:
                    # Tratto post-picco con degrado
                    V[i] = V_max_orig * (1 - beta_degradation *
                                        (di - d_yield_orig) / (d_max_orig - d_yield_orig))
                else:
                    # Residuo minimo (20% della resistenza)
                    V[i] = V_max_orig * (1 - beta_degradation)

            ax.plot(d, V, 'b-', linewidth=2, label='Stato di fatto')

            # Marca punto di snervamento
            ax.plot(d_yield_orig, V_max_orig, 'bo', markersize=8)

            # Aggiungi annotazione per meccanismo
            ax.annotate(f'Meccanismo: {mechanism}',
                       xy=(d_yield_orig, V_max_orig),
                       xytext=(d_yield_orig + 5, V_max_orig * 0.9),
                       fontsize=8, style='italic')

        # Stato di progetto
        if 'modified' in results:
            K_mod = results['modified']['K']  # Rigidezza [kN/m]
            V_max_mod = results['modified']['V_min']  # Resistenza [kN]

            # Determina il meccanismo di rottura critico per stato modificato
            if results['modified']['V_t1'] == results['modified']['V_min']:
                mechanism_mod = 'shear'
                mu_ductility_mod = 2.0
                beta_degradation_mod = 0.4
            elif results['modified']['V_t3'] == results['modified']['V_min']:
                mechanism_mod = 'flexure'
                mu_ductility_mod = 3.0
                beta_degradation_mod = 0.2
            else:
                mechanism_mod = 'mixed'
                mu_ductility_mod = mu_ductility_base
                beta_degradation_mod = beta_degradation_base

            # La presenza di cerchiature può aumentare la duttilità
            if 'K_cerchiature' in results['modified'] and results['modified']['K_cerchiature'] > 0:
                frame_contribution = results['modified']['K_cerchiature'] / results['modified']['K']
                if frame_contribution > 0.3:  # Contributo significativo delle cerchiature
                    mu_ductility_mod *= 1.3  # Aumento duttilità del 30%
                    beta_degradation_mod *= 0.8  # Degrado più graduale

            # Calcola spostamenti caratteristici
            d_yield_mod = V_max_mod / K_mod * 1000  # [mm]
            d_max_mod = d_yield_mod * mu_ductility_mod  # [mm]

            # Genera punti curva
            d = np.linspace(0, d_max_mod * 1.2, 200)
            V = np.zeros_like(d)

            for i, di in enumerate(d):
                if di <= d_yield_mod:
                    # Tratto elastico
                    V[i] = K_mod * di / 1000
                elif di <= d_max_mod:
                    # Tratto post-picco
                    V[i] = V_max_mod * (1 - beta_degradation_mod *
                                       (di - d_yield_mod) / (d_max_mod - d_yield_mod))
                else:
                    # Residuo
                    V[i] = V_max_mod * (1 - beta_degradation_mod)

            ax.plot(d, V, 'r--', linewidth=2, label='Stato di progetto')

            # Marca punto di snervamento
            ax.plot(d_yield_mod, V_max_mod, 'ro', markersize=8)

            # Annotazione
            ax.annotate(f'Meccanismo: {mechanism_mod}',
                       xy=(d_yield_mod, V_max_mod),
                       xytext=(d_yield_mod + 5, V_max_mod * 0.9),
                       fontsize=8, style='italic')

        # Aggiungi informazioni aggiuntive
        if 'original' in results and 'modified' in results:
            # Box con informazioni riassuntive
            textstr = f'Rigidezza:\nOriginale: {K_orig:.0f} kN/m\nProgetto: {K_mod:.0f} kN/m\n\n'
            textstr += f'Resistenza:\nOriginale: {V_max_orig:.1f} kN\nProgetto: {V_max_mod:.1f} kN\n\n'
            textstr += f'Duttilità:\nOriginale: μ={mu_ductility:.1f}\nProgetto: μ={mu_ductility_mod:.1f}'

            if 'K_cerchiature' in results['modified'] and results['modified']['K_cerchiature'] > 0:
                contrib_percent = (results['modified']['K_cerchiature'] / results['modified']['K']) * 100
                textstr += f'\n\nContributo cerchiature: {contrib_percent:.0f}%'

            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.65, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', bbox=props)

        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper right')
        self.draw()

    def analyze_capacity_parameters(self, results):
        """Analizza parametri di capacità per comportamento non lineare"""
        params = {}

        if 'original' in results:
            # Analisi stato originale
            K = results['original']['K']
            V_min = results['original']['V_min']

            # Identifica meccanismo
            if results['original']['V_t1'] == V_min:
                params['original_mechanism'] = 'taglio'
                params['original_ductility'] = 2.0
            elif results['original']['V_t3'] == V_min:
                params['original_mechanism'] = 'pressoflessione'
                params['original_ductility'] = 3.0
            else:
                params['original_mechanism'] = 'misto'
                params['original_ductility'] = 2.5

            # Spostamento al limite elastico
            params['original_dy'] = V_min / K * 1000  # mm

        if 'modified' in results:
            # Analisi stato modificato
            K = results['modified']['K']
            V_min = results['modified']['V_min']

            # Meccanismo modificato
            if results['modified']['V_t1'] == V_min:
                params['modified_mechanism'] = 'taglio'
                base_ductility = 2.0
            elif results['modified']['V_t3'] == V_min:
                params['modified_mechanism'] = 'pressoflessione'
                base_ductility = 3.0
            else:
                params['modified_mechanism'] = 'misto'
                base_ductility = 2.5

            # Incremento duttilità per cerchiature
            if 'K_cerchiature' in results['modified']:
                frame_ratio = results['modified']['K_cerchiature'] / K
                ductility_factor = 1 + 0.3 * min(frame_ratio / 0.3, 1.0)
                params['modified_ductility'] = base_ductility * ductility_factor
            else:
                params['modified_ductility'] = base_ductility

            params['modified_dy'] = V_min / K * 1000  # mm

        return params

    def plot_stiffness_comparison(self, results):
        """Grafico confronto rigidezze"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        if 'original' in results and 'modified' in results:
            labels = ['Stato di fatto', 'Stato di progetto']
            values = [results['original']['K'], results['modified']['K']]
            colors = ['blue', 'red']

            bars = ax.bar(labels, values, color=colors, alpha=0.7)

            # Aggiungi valori sopra le barre
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}',
                       ha='center', va='bottom')

            # Linea limite variazione 15%
            K_original = results['original']['K']
            ax.axhline(y=K_original * 1.15, color='g', linestyle='--',
                      label='Limite +15%', alpha=0.5)
            ax.axhline(y=K_original * 0.85, color='g', linestyle='--',
                      label='Limite -15%', alpha=0.5)

            ax.set_ylabel('Rigidezza [kN/m]')
            ax.set_title('Confronto Rigidezze')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

        self.draw()

    def plot_resistance_comparison(self, results):
        """Grafico confronto resistenze"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        if 'original' in results and 'modified' in results:
            categories = ['V_t1\n(Taglio)', 'V_t2\n(Taglio con\nfattore forma)',
                         'V_t3\n(Presso-\nflessione)']

            x = np.arange(len(categories))
            width = 0.35

            values_original = [
                results['original']['V_t1'],
                results['original']['V_t2'],
                results['original']['V_t3']
            ]
            values_modified = [
                results['modified']['V_t1'],
                results['modified']['V_t2'],
                results['modified']['V_t3']
            ]

            bars1 = ax.bar(x - width/2, values_original, width,
                          label='Stato di fatto', color='blue', alpha=0.7)
            bars2 = ax.bar(x + width/2, values_modified, width,
                          label='Stato di progetto', color='red', alpha=0.7)

            # Valori sopra le barre
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=9)

            ax.set_ylabel('Resistenza [kN]')
            ax.set_title('Confronto Resistenze')
            ax.set_xticks(x)
            ax.set_xticklabels(categories)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

        self.draw()

    def plot_frame_details(self, frame_results):
        """Grafico dettagli cerchiature"""
        self.figure.clear()

        if not frame_results:
            return

        # Crea subplot per ogni cerchiatura
        n_frames = len(frame_results)
        rows = int(np.ceil(np.sqrt(n_frames)))
        cols = int(np.ceil(n_frames / rows))

        for i, (opening_id, frame_data) in enumerate(frame_results.items()):
            ax = self.figure.add_subplot(rows, cols, i+1)

            # Dati da plottare
            categories = ['K_frame', 'N_max', 'M_max', 'V_max']
            values = [
                frame_data.get('K_frame', 0) / 1000,  # in MN/m
                frame_data.get('N_max', 0),  # kN
                frame_data.get('M_max', 0),  # kNm
                frame_data.get('V_max', 0)   # kN
            ]

            bars = ax.bar(categories, values, color=['blue', 'red', 'green', 'orange'])
            ax.set_title(f'Apertura {opening_id}')
            ax.set_ylabel('Valore')

            # Valori sopra le barre
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{value:.1f}',
                       ha='center', va='bottom', fontsize=8)

        self.figure.tight_layout()
        self.draw()
