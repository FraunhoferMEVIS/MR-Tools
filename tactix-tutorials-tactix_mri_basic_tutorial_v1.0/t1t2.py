"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
Licensed under LICENSE, see LICENSE file for details.

The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import numpy as np
import matplotlib.pyplot as plt

def make_figure():
    # Schriftart für einen mathematischen Look anpassen
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['mathtext.fontset'] = 'cm'

    # Feste Parameter
    T1 = 2.5
    T2 = 0.6
    M0 = 1.0
    t = np.linspace(0, 10, 500)

    # Plot und Achsen erstellen
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.subplots_adjust(bottom=0.2, top=0.85, left=0.15, right=0.85)

    # Kurven berechnen
    M_xy = M0 * np.exp(-t / T2)        # T2-Decay
    M_z = M0 * (1 - np.exp(-t / T1))   # T1-Recovery

    # Kurven zeichnen
    line_t2, = ax.plot(t, M_xy, color='#CC0000', linewidth=1.5)  # Rote Kurve (T2)
    line_t1, = ax.plot(t, M_z, color='#333399', linewidth=1.5)   # Blaue Kurve (T1)

    # Hilfslinien für T1 (Hellblau)
    line_color_t1 = '#D0D0F0'
    ax.axhline(M0, color=line_color_t1, linestyle='solid', linewidth=1.5)
    ax.axhline(0.63 * M0, color=line_color_t1, linestyle='solid', linewidth=1.5)
    ax.plot([T1, T1], [0, 0.63 * M0], color=line_color_t1, linestyle='solid', linewidth=1.5)

    # Hilfslinien für T2 (Grau)
    line_color_t2 = '#A0A0A0'
    ax.plot([0, T2], [0.37 * M0, 0.37 * M0], color=line_color_t2, linestyle='solid', linewidth=1.5)
    ax.plot([T2, T2], [0, 0.37 * M0], color=line_color_t2, linestyle='solid', linewidth=1.5)

    # Achsengrenzen
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.05)

    # Zweite Y-Achse für die rechte Seite
    ax2 = ax.twinx()
    ax2.set_ylim(0, 1.05)

    # Spines (Rahmenlinien) anpassen
    ax.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1)
    ax.spines['left'].set_linewidth(1)
    ax2.spines['right'].set_linewidth(1)

    # X-Achsen-Ticks
    ax.tick_params(axis='x', direction='in', length=7, bottom=True, top=False)
    ax.set_xticks([T2, T1, 4.5, 6.5, 8.5])
    ax.set_xticklabels(['T$_2$', 'T$_1$', '', '', ''], fontsize=14)

    # Linke Y-Achsen-Ticks
    ax.tick_params(axis='y', direction='in', length=7, left=True, right=False)
    ax.set_yticks([0.37 * M0])
    ax.set_yticklabels(['0.37$M_0$'], fontsize=14)

    # Rechte Y-Achsen-Ticks
    ax2.tick_params(axis='y', direction='in', length=7, left=False, right=True)
    ax2.set_yticks([0.63 * M0, M0])
    ax2.set_yticklabels(['0.63$M_0$', '$M_0$'], fontsize=14)

    # Feste Beschriftungen
    ax.text(T2 + 0.1, 0.65, '$T_2\\ decay$', color='#CC0000',
            fontsize=16, fontstyle='italic')
    ax.text(T1 + 3.0, 0.8, '$T_1\\ recovery$', color='#333399',
            fontsize=16, fontstyle='italic')

    ax.text(0, 1.03, 'M$_{xy}$', transform=ax.transAxes,
            fontsize=16, ha='center', va='bottom')
    ax2.text(1, 1.03, 'M$_z$', transform=ax2.transAxes,
            fontsize=16, ha='center', va='bottom')
    ax.text(1, -0.05, 'Time', transform=ax.transAxes,
            fontsize=14, ha='center', va='top')

    # Pfeilspitzen (für Mxy und Mz nach oben)
    ax.plot(0, 1.0, '^k', transform=ax.transAxes, clip_on=False, markersize=6)
    ax2.plot(1, 1.0, '^k', transform=ax2.transAxes, clip_on=False, markersize=6)

    return fig