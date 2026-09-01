"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
Licensed under LICENSE, see LICENSE file for details.

The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

# spin_panel_ab.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow, Wedge, Polygon

BG = "#5b2a86"     # Hintergrund (violett)
FG = "#ffffff"     # Linien/Text (weiß)
ARROW = "#f6a04f"  # Orange

def make_figure():
    fig, ax = plt.subplots(figsize=(5.6, 6.0), dpi=300)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)

    # Layout
    r = 0.85                    # Kreisradius
    x_left, x_right = 1.6, 4.4  # Spaltenzentren
    ys = [4.8, 3.1, 1.4]        # Zeilenzentren

    # Kreise + Inhalte
    # Linke Spalte: identischer Pfeilwinkel pro Kreis (leicht nach rechts unten)
    left_angles = [-55, -55, -55]  # Grad
    # Rechte Spalte: Sektoren (obere–rechte Quadranten bis nach unten)
    wedge_ranges = [(-160, -55), (-120, -55), (-90, -55)]  # (theta1, theta2) in Grad

    for i, cy in enumerate(ys):
        # Kreise
        ax.add_patch(Circle((x_left,  cy), r, fill=False, edgecolor=FG, linewidth=2.0))
        ax.add_patch(Circle((x_right, cy), r, fill=False, edgecolor=FG, linewidth=2.0))

        # Linker Pfeil
        ang = np.deg2rad(left_angles[i])
        L = 1.4 * r
        dx, dy = np.cos(ang) * L, np.sin(ang) * L
        sx, sy = x_left - 0.35 * dx, cy - 0.35 * dy  # Start etwas hinter dem Zentrum
        ax.add_patch(FancyArrow(
            sx, sy, dx, dy,
            width=0.18 * r, head_width=0.44 * r, head_length=0.28 * r,
            length_includes_head=True, color=ARROW
        ))

        # Rechter orangefarbener „Sektor“
        th1, th2 = wedge_ranges[i]
        ax.add_patch(Wedge((x_right, cy), r * 0.96, th1, th2,
                           facecolor=ARROW, edgecolor="none", alpha=0.95))

    # Großer Pfeil zwischen den Spalten
    ax.annotate(
        "", xy=(x_right - r - 0.25, np.mean(ys)), xytext=(x_left + r + 0.25, np.mean(ys)),
        arrowprops=dict(arrowstyle="->", color=FG, lw=2.4)
    )

    # "Gradient field" Keil rechts
    x0, y0 = 6.2, 0.8
    height, spread = 4.9, 1.0
    ax.add_patch(Polygon(
        [(x0, y0), (x0 + spread, y0 + height), (x0, y0 + height)],
        closed=True, fill=False, edgecolor=FG, linewidth=1.6
    ))
    ax.text(x0 + 0.08, y0 + height - 0.2, "Gradient\nfield", color=FG,
            fontsize=9, ha="left", va="top")

    # Untere Labels
    ax.text(x_left, 0.4, "65 ms", color=FG, fontsize=9, ha="center", va="center")
    ax.text(x_left, 0.15, "a", color=FG, fontsize=11, ha="center", va="top")
    ax.text(x_right, 0.15, "b", color=FG, fontsize=11, ha="center", va="top")

    # Grenzen
    ax.set_xlim(0.2, 7.2)
    ax.set_ylim(0.0, 6.2)
    return fig

