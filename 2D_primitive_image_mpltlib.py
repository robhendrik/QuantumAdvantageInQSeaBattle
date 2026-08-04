"""
2D RAC advantage-space figure (n=2), styled to match the 3D PyVista figure.

  * Quantum boundary : unit circle   c0^2 + c1^2 = 1
  * Classical region : diamond       |c0| + |c1| <= 1
  * They touch only at the four axis poles; the crescent between them is the
    quantum-only region.
  * majority (n=2)   : (1/2,1/2) on the (1,1) diagonal -- the 50/50 mix of
                       'send index 0' and 'send index 1', ON the diamond edge.
  * quantum on (1,1) : (1/sqrt2,1/sqrt2) on the circle -- reaches past majority
                       along the same diagonal (mirrors the 3D (1,1,1) point).

Outputs ONE image to OUT_PATH.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, PathPatch, Circle
from matplotlib.path import Path

# =====================================================================
#  TUNABLE SETTINGS  (palette kept identical to the 3D script)
# =====================================================================
OUT_PATH = "fig1_advantage_2d.png"
IMG_SIZE = (6.6, 6.6)
DPI      = 200

C_SPHERE   = "#F5C543"     # quantum circle (yellow)
C_POLY     = "#3D7EC4"     # classical diamond (blue)
C_AXIS     = "#1A1A1A"     # ink
C_MAJORITY = "#E05B49"     # majority marker  (RED -- same as 3D)
C_QUANTUM  = "#B8901E"     # quantum-on-diagonal point (GOLD -- same as 3D)
C_GREY     = "#8A8A8A"

SPHERE_FILL_ALPHA  = 0.12  # faint yellow disk fill, echoes the 3D translucent sphere
CRESCENT_ALPHA     = 0.30
DIAMOND_FACE_ALPHA = 0.16

SHOW_DIAGONAL   = True      # the (1,1) diagonal callout, matching 3D (1,1,1)
SHOW_MAJORITY   = True
SHOW_QUANTUM    = True
SHOW_LABELS     = True
AXIS_LABELS     = ("index_0", "index_1")
LIM = 1.5
AXIS_LEN = 1.5
# =====================================================================


def main():
    plt.rcParams["mathtext.fontset"] = "cm"
    fig, ax = plt.subplots(figsize=IMG_SIZE)

    th = np.linspace(0, 2*np.pi, 400)
    circle_pts = np.column_stack([np.cos(th), np.sin(th)])
    diamond = np.array([[1,0],[0,1],[-1,0],[0,-1]])

    # faint disk fill (echoes 3D translucent sphere)
    ax.add_patch(Circle((0,0), 1.0, facecolor=C_SPHERE, edgecolor="none",
                        alpha=SPHERE_FILL_ALPHA, zorder=0))

    # crescent = inside circle AND outside diamond
    verts = np.vstack([circle_pts, circle_pts[0], diamond, diamond[0]])
    codes = ([Path.MOVETO] + [Path.LINETO]*(len(circle_pts)-1) + [Path.CLOSEPOLY]
             + [Path.MOVETO] + [Path.LINETO]*(len(diamond)-1) + [Path.CLOSEPOLY])
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=C_SPHERE,
                           edgecolor="none", alpha=CRESCENT_ALPHA, zorder=1))

    # classical diamond -- single polygon, NO internal diagonals
    ax.add_patch(Polygon(diamond, closed=True, facecolor=C_POLY,
                         alpha=DIAMOND_FACE_ALPHA, edgecolor=C_POLY,
                         linewidth=2.6, zorder=2))

    # quantum circle
    ax.add_patch(Circle((0,0), 1.0, fill=False, edgecolor=C_SPHERE,
                        linewidth=3.0, zorder=3))

    # axes through origin, extended past the circle
    for u, lab in [((1,0), AXIS_LABELS[0]), ((0,1), AXIS_LABELS[1])]:
        u = np.array(u, float)
        ax.plot([-AXIS_LEN*u[0], AXIS_LEN*u[0]],
                [-AXIS_LEN*u[1], AXIS_LEN*u[1]], color=C_AXIS, lw=1.2, zorder=4)
        lp = 1.60*u
        ax.text(lp[0], lp[1], lab, color=C_AXIS, fontsize=15,
                ha="center", va="center", zorder=6)

    # four touch points
    for p in diamond:
        ax.plot(*p, 'o', color=C_AXIS, markersize=7, zorder=5)

    # (1,1) diagonal callout, matching the 3D (1,1,1) line
    if SHOW_DIAGONAL:
        d = np.array([1,1])/np.sqrt(2)
        ax.plot([0, 1.42*d[0]], [0, 1.42*d[1]], color=C_GREY,
                lw=1.3, ls=(0,(4,3)), zorder=4)
        if SHOW_LABELS:
            ax.annotate("(1,1) diagonal", (1.30*d[0], 1.30*d[1]),
                        xytext=(6, 12), textcoords="offset points",
                        color=C_AXIS, fontsize=13)

    # quantum-on-diagonal point (1/sqrt2, 1/sqrt2) -- ON the circle, gold
    if SHOW_QUANTUM:
        q = 1/np.sqrt(2)
        ax.plot(q, q, 'o', color=C_QUANTUM, markersize=11, zorder=7)
        if SHOW_LABELS:
            ax.annotate("quantum", (q, q), xytext=(12, -6),
                        textcoords="offset points", color=C_QUANTUM, fontsize=13)

    # majority at (1/2,1/2) -- RED, matching 3D
    if SHOW_MAJORITY:
        ax.plot(0.5, 0.5, 'o', color=C_MAJORITY, markersize=11, zorder=7)
        if SHOW_LABELS:
            ax.annotate("majority", (0.5, 0.5), xytext=(-4, -20),
                        textcoords="offset points", color=C_MAJORITY,
                        fontsize=13, ha="center")

    if SHOW_LABELS:
        ax.text(0.86, 0.86, "quantum\n(the box)", color=C_QUANTUM,
                fontsize=13, ha="center", va="center")
        ax.text(0.30, -0.30, "classical", color=C_POLY,
                fontsize=13, ha="center", va="center")

    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=DPI, bbox_inches="tight", facecolor="white")
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()