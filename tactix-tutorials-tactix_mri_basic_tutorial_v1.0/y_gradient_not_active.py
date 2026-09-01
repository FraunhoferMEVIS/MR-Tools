"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
Licensed under LICENSE, see LICENSE file for details.

The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

# arrows_grid.py
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow

BG = "#5b2a86"        # Violett
CIRCLE = "#ffffff"    # Weiß
ARROW = "#f6a04f"     # Orange

def make_figure(n=3, cell=1.0, r=0.38, margin=0.2):
    fig, ax = plt.subplots(figsize=(5, 5), dpi=300)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)

    ax.set_xlim(-margin, n * cell + margin)
    ax.set_ylim(-margin, n * cell + margin)

    for i in range(n):
        for j in range(n):
            cx = (j + 0.5) * cell
            cy = (i + 0.5) * cell

            ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor=CIRCLE, linewidth=2.0))

            shaft_len = 0.45
            start_y = cy - shaft_len / 10
            ax.add_patch(
                FancyArrow(
                    cx, start_y,
                    0.0, shaft_len * 0.9,
                    width=0.06,
                    head_width=0.18,
                    head_length=0.12,
                    length_includes_head=True,
                    color=ARROW
                )
            )
    return fig