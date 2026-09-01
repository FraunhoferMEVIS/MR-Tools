"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
Licensed under LICENSE, see LICENSE file for details.

The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

# gradient_grid.py
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow, Rectangle, Polygon
import numpy as np

def make_figure(labels=("65 ms","64 ms","63 ms"), angles_deg=(-55, -15, 60)):
    BG, FG, ARROW = "#5b2a86", "#ffffff", "#f6a04f"
    nrows, ncols = 3, 3
    cell, r, margin, header_h, footer_h = 1.4, 0.48, 0.25, 0.8, 0.45

    fig, ax = plt.subplots(figsize=(5.2, 5.5), dpi=300)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_facecolor(BG); fig.patch.set_facecolor(BG)
    ax.set_xlim(-margin, ncols*cell + margin)
    ax.set_ylim(-footer_h, nrows*cell + header_h)

    # Gradient-Box + Keil
    bx, by, bw, bh = 0.15, nrows*cell + 0.25, 1.6, 0.35
    #ax.add_patch(Rectangle((bx, by), bw, bh, fill=False, edgecolor=FG, linewidth=1.5))
    ax.text(bx + 0.12, by + bh/2, "Gradient field", va="center", ha="left", color=FG, fontsize=9)
    x0, y0, length, thick = bx , by + 0.05, 3.8, 0.30
    pts = [(x0, y0 + thick), (x0, y0), (x0 + length, y0), (x0 + length, y0 + 0.02)]
    ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=FG, linewidth=1.5))

    # Gitter
    angle_grid = np.tile(np.array(angles_deg), (nrows, 1))
    for i in range(nrows):
        for j in range(ncols):
            cx, cy = (j + 0.5) * cell, (i + 0.5) * cell
            ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor=FG, linewidth=1.6))
            ang = np.deg2rad(angle_grid[i, j])
            L = 0.70 * r * 2
            dx, dy = np.cos(ang)*L, np.sin(ang)*L
            sx, sy = cx - 0.35*dx, cy - 0.35*dy
            ax.add_patch(FancyArrow(sx, sy, dx, dy, width=0.06,
                                    head_width=0.18, head_length=0.12,
                                    length_includes_head=True, color=ARROW))
    for j, txt in enumerate(labels):
        cx = (j + 0.5) * cell
        ax.text(cx, -0.22, txt, color=FG, fontsize=8.5, ha="center", va="top")

    return fig