"""
Generate multiple figures, each with:
- Title
- Filename
- One or more probability distributions
- Legend labels when multiple distributions are plotted
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle


# =====================================================================
# INPUT
# =====================================================================

# All input strings, sorted by Hamming weight.
STRINGS = sorted(
    [tuple(int(c) for c in format(i, "04b")) for i in range(16)],
    key=sum,
)


@dataclass
class FigureSpec:
    title: str
    out_path: str
    probs: list | np.ndarray
    labels: list[str] | None = None


# ---------------------------------------------------------------------
# Uniform prior
# ---------------------------------------------------------------------

UNIFORM = FigureSpec(
    title=(
        "Bob's probability distribution over Alice's strings,\n"
        "prior to receiving any information from Alice."
    ),
    out_path="fig4_uniform.png",
    probs=np.full(16, 1 / 16),
)


# ---------------------------------------------------------------------
# Majority, random on ties
# ---------------------------------------------------------------------

PROBS_MAJ = []

for s in STRINGS:
    if sum(s) < 2:
        PROBS_MAJ.append(0.0)
    elif sum(s) > 2:
        PROBS_MAJ.append(1.0)
    else:
        PROBS_MAJ.append(0.5)

PROBS_MAJ = np.asarray(PROBS_MAJ, dtype=float)
PROBS_MAJ /= PROBS_MAJ.sum()

MAJORITY = FigureSpec(
    title=(
        "Bob's probability distribution over Alice's strings,\n"
        "after receiving 'majority with random on tie' from Alice."
    ),
    out_path="fig4_majority.png",
    probs=PROBS_MAJ,
)


# ---------------------------------------------------------------------
# Majority, first bit on ties
# ---------------------------------------------------------------------

PROBS_FRST = []

for s in STRINGS:
    if sum(s) < 2:
        PROBS_FRST.append(0.0)
    elif sum(s) > 2:
        PROBS_FRST.append(1.0)
    elif s[0] == 1:
        PROBS_FRST.append(1.0)
    else:
        PROBS_FRST.append(0.0)

PROBS_FRST = np.asarray(PROBS_FRST, dtype=float)
PROBS_FRST /= PROBS_FRST.sum()

FIRST_BIT = FigureSpec(
    title=(
        "Bob's probability distribution over Alice's strings,\n"
        "after receiving 'majority with first bit on tie' from Alice."
    ),
    out_path="fig4_first_bit.png",
    probs=PROBS_FRST,
)


# ---------------------------------------------------------------------
# Hybrid
# ---------------------------------------------------------------------

# Majority on prefix bits 0 and 1, quantum box on suffix bits 2 and 3.
#
# Prefix:
#   00 -> Alice sends 0
#   11 -> Alice sends 1
#   01 or 10 -> tie, with uniform marginal
#
# Thus, conditioned on classical message M = 1:
prefix_post = {
    (0, 0): 0.00,
    (1, 1): 0.50,
    (0, 1): 0.25,
    (1, 0): 0.25,
}

s2 = 1 / np.sqrt(2)


def hybrid_posterior(measured_suffix_bit: int) -> np.ndarray:
    """
    Return Bob's posterior when his box targets suffix bit 2 or 3.

    The targeted suffix bit is recovered with probability

        0.5 * (1 + 1/sqrt(2)) ≈ 0.854,

    while the other suffix bit remains uniformly distributed.
    """
    if measured_suffix_bit not in (2, 3):
        raise ValueError("measured_suffix_bit must be 2 or 3.")

    q = {2: 0.5, 3: 0.5}
    q[measured_suffix_bit] = 0.5 * (1 + s2)

    posterior = np.zeros(16, dtype=float)

    for k, s in enumerate(STRINGS):
        a0, a1, a2, a3 = s

        posterior[k] = (
            prefix_post[(a0, a1)]
            * (q[2] if a2 == 1 else 1 - q[2])
            * (q[3] if a3 == 1 else 1 - q[3])
        )

    posterior /= posterior.sum()
    return posterior


HYBRID = FigureSpec(
    title=(
        "Bob's probability distribution over Alice's strings,\n"
        "after receiving 'majority on prefix, box on suffix' from Alice."
    ),
    out_path="fig4_hybrid.png",
    probs=[
        hybrid_posterior(2),
        hybrid_posterior(3),
    ],
    labels=[
        "Bob points box at bit 2",
        "Bob points box at bit 3",
    ],
)


FIGURES = [
    UNIFORM,
    MAJORITY,
    FIRST_BIT,
    HYBRID,
]


# =====================================================================
# OUTPUT AND DISPLAY SETTINGS
# =====================================================================

OUTPUT_DIR = Path("./Quantum Advantage a QSeaBattle Game")

Y_MAX = 0.30
GRID_LINES = [0.10, 0.20]

SHOW_ENTROPY = True
SHOW_PER_BIT = True

SAVE = True
DPI = 200


# =====================================================================
# STYLE
# =====================================================================

INK = "#1A1A1A"
BLUE = "#3D7EC4"
GREYBAR = "#E0E0E0"

ZERO_FACE = "#EDEDED"
ONE_FACE = BLUE

ZERO_TXT = "#7A7A7A"
ONE_TXT = "white"

BAR_WIDTH = 0.85
CELL_GAP_FRAC = 0.18

# Additional colours are automatically taken from Matplotlib's default
# colour cycle for multi-distribution figures.
MULTI_COLORS = [
    BLUE,
    "#A996B9",
    "#E18A35",
    "#5A9E6F",
    "#C85B65",
]


mpl.rcParams.update(
    {
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "mathtext.fontset": "cm",
        "text.color": INK,
        "font.size": 13,
    }
)


# =====================================================================
# CALCULATIONS
# =====================================================================

def normalise_distribution(probs: np.ndarray) -> np.ndarray:
    """Return a validated, normalised probability distribution."""
    probs = np.asarray(probs, dtype=float)

    if probs.shape != (16,):
        raise ValueError(
            f"Each probability distribution must have shape (16,), "
            f"not {probs.shape}."
        )

    if np.any(probs < 0):
        raise ValueError("Probabilities may not be negative.")

    total = probs.sum()

    if total <= 0:
        raise ValueError("Probability distribution has zero total weight.")

    return probs / total


def get_distributions(spec: FigureSpec) -> list[np.ndarray]:
    """
    Convert FigureSpec.probs into a list of normalised distributions.

    Supports either:
    - one 16-element distribution;
    - a list or array of multiple 16-element distributions.
    """
    raw = np.asarray(spec.probs, dtype=float)

    if raw.ndim == 1:
        distributions = [normalise_distribution(raw)]

    elif raw.ndim == 2:
        distributions = [
            normalise_distribution(row)
            for row in raw
        ]

    else:
        raise ValueError(
            f"{spec.out_path}: probs must be one- or two-dimensional."
        )

    if spec.labels is not None and len(spec.labels) != len(distributions):
        raise ValueError(
            f"{spec.out_path}: number of labels must match "
            f"number of distributions."
        )

    return distributions


def shannon(probs: np.ndarray) -> float:
    """Shannon entropy in bits."""
    probs = np.asarray(probs, dtype=float)
    probs = probs[probs > 1e-12]

    return float(-np.sum(probs * np.log2(probs)))


def binary_entropy(q: float) -> float:
    """Binary entropy in bits."""
    if q <= 0 or q >= 1:
        return 0.0

    return float(
        -(q * np.log2(q) + (1 - q) * np.log2(1 - q))
    )


def per_bit(probs: np.ndarray) -> list[tuple[float, float]]:
    """
    For each bit position, return:

        (optimal probability of guessing correctly, binary entropy)
    """
    probs = normalise_distribution(probs)

    output = []

    for j in range(4):
        p1 = sum(
            probs[i]
            for i in range(16)
            if STRINGS[i][j] == 1
        )

        p_correct = max(p1, 1 - p1)
        output.append((p_correct, binary_entropy(p1)))

    return output


# =====================================================================
# DRAWING
# =====================================================================

def draw_string_cells(
    ax,
    figure_width: float,
    figure_height: float,
    axes_width: float,
) -> list[float]:
    """
    Draw the 4 × 16 bit-string grid.

    Returns the vertical centre coordinate of each bit row.
    """
    ax.set_xlim(-0.7, 15.7)

    axes_width_inches = axes_width * figure_width
    axes_height_inches = 0.34 * figure_height

    x_span = 16.4
    inches_per_x = axes_width_inches / x_span

    cell_width = BAR_WIDTH
    cell_inches = cell_width * inches_per_x

    y_range_cells = axes_height_inches / cell_inches
    ax.set_ylim(-y_range_cells * cell_width, 0.0)

    gap = cell_width * CELL_GAP_FRAC
    top = -0.15 * cell_width

    row_centres = []

    for row_index in range(4):
        cell_y = (
            top
            - (row_index + 1) * cell_width
            - row_index * gap
        )
        row_centres.append(cell_y + cell_width / 2)

    for string_index, string in enumerate(STRINGS):
        for row_index, bit in enumerate(string):
            cell_y = (
                top
                - (row_index + 1) * cell_width
                - row_index * gap
            )

            ax.add_patch(
                FancyBboxPatch(
                    (
                        string_index - cell_width / 2,
                        cell_y,
                    ),
                    cell_width,
                    cell_width,
                    boxstyle=(
                        "round,pad=0,"
                        f"rounding_size={cell_width * 0.22}"
                    ),
                    facecolor=ONE_FACE if bit else ZERO_FACE,
                    edgecolor="none",
                    mutation_aspect=1,
                    clip_on=False,
                )
            )

            ax.text(
                string_index,
                cell_y + cell_width / 2,
                str(bit),
                ha="center",
                va="center",
                fontsize=10,
                color=ONE_TXT if bit else ZERO_TXT,
                fontweight="bold",
            )

    ax.axis("off")
    return row_centres


def draw_probability_bars(
    ax,
    distributions: list[np.ndarray],
    labels: list[str] | None,
) -> None:
    """Draw one or more grouped probability distributions."""
    xs = np.arange(16)
    count = len(distributions)

    for grid_level in GRID_LINES:
        ax.axhline(
            grid_level,
            color=INK,
            linewidth=0.8,
            linestyle=(0, (2, 3)),
            alpha=0.5,
            zorder=1,
        )

        ax.text(
            15.7,
            grid_level,
            f"{int(grid_level * 100)}%",
            va="center",
            ha="left",
            fontsize=10,
            color=INK,
            alpha=0.6,
        )

    if count == 1:
        ax.bar(
            xs,
            distributions[0],
            width=BAR_WIDTH,
            color=MULTI_COLORS[0],
            zorder=3,
        )

    else:
        # Together, all bars for one string occupy BAR_WIDTH.
        individual_width = BAR_WIDTH / count

        for distribution_index, probs in enumerate(distributions):
            offset = (
                distribution_index - (count - 1) / 2
            ) * individual_width

            ax.bar(
                xs + offset,
                probs,
                width=individual_width * 0.92,
                color=MULTI_COLORS[distribution_index],
                label=(
                    labels[distribution_index]
                    if labels is not None
                    else f"Distribution {distribution_index + 1}"
                ),
                zorder=3,
            )

        ax.legend(
            loc="upper right",
            frameon=False,
            fontsize=9,
            ncol=1,
        )

    ax.set_xlim(-0.7, 15.7)
    ax.set_ylim(0, Y_MAX)
    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.axhline(0, color=INK, linewidth=1.0)


def draw_per_bit_panel(
    fig,
    ax_left,
    row_centres: list[float],
    distributions: list[np.ndarray],
    labels: list[str] | None,
) -> None:
    """Draw the horizontal per-bit advantage bars."""
    ax_right = fig.add_axes([0.70, 0.04, 0.26, 0.34])

    ax_right.set_ylim(ax_left.get_ylim())
    ax_right.set_xlim(0, 1.55)
    ax_right.axis("off")

    ax_right.text(
        0.0,
        1.0,
        "Bob's advantage for this bit",
        transform=ax_right.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.5,
        color=INK,
    )

    number_of_distributions = len(distributions)
    stats = [per_bit(probs) for probs in distributions]

    track_width = 0.62

    # The complete stack retains approximately the height of the
    # original single-distribution bar.
    total_stack_height = BAR_WIDTH * 0.62
    gap = BAR_WIDTH * 0.06 if number_of_distributions > 1 else 0.0

    available_height = (
        total_stack_height
        - gap * (number_of_distributions - 1)
    )

    individual_height = available_height / number_of_distributions

    for bit_index, row_centre in enumerate(row_centres):
        for distribution_index in range(number_of_distributions):
            p_correct, _ = stats[distribution_index][bit_index]
            advantage = 2 * p_correct - 1

            stack_offset = (
                distribution_index
                - (number_of_distributions - 1) / 2
            ) * (individual_height + gap)

            y_centre = row_centre - stack_offset

            ax_right.add_patch(
                Rectangle(
                    (
                        0,
                        y_centre - individual_height / 2,
                    ),
                    track_width,
                    individual_height,
                    facecolor=GREYBAR,
                    edgecolor="none",
                )
            )

            ax_right.add_patch(
                Rectangle(
                    (
                        0,
                        y_centre - individual_height / 2,
                    ),
                    advantage * track_width,
                    individual_height,
                    facecolor=MULTI_COLORS[distribution_index],
                    edgecolor="none",
                )
            )

            if number_of_distributions == 1:
                text = (
                    f"Advantage: {advantage:.2f} "
                    f"({int(round(p_correct * 100))}% correct)"
                )
                text_size = 10.5

            else:
                label = (
                    labels[distribution_index]
                    if labels is not None
                    else f"Distribution {distribution_index + 1}"
                )

                text = (
                    f"{label}: {advantage:.3f} "
                    f"({int(round(p_correct * 100))}% correct)"
                )
                text_size = 7.8

            ax_right.text(
                track_width + 0.05,
                y_centre,
                text,
                va="center",
                ha="left",
                fontsize=text_size,
                color=INK,
            )


def draw_summary_box(fig, probs: np.ndarray) -> None:
    """
    Draw entropy and mean advantage.

    For multi-distribution figures this receives only the first
    distribution.
    """
    xpos = 0.70
    ypos = 0.43

    ax_summary = fig.add_axes([xpos, ypos, 0.25, 0.45])
    ax_summary.axis("off")

    ax_summary.add_patch(
        Rectangle(
            (0.0, 0.0),
            1.0,
            1.0,
            transform=ax_summary.transAxes,
            facecolor=GREYBAR,
            edgecolor="none",
            zorder=2,
        )
    )

    ax_summary.add_line(
        Line2D(
            [0.0, 1.0],
            [0.0, 1.0],
            transform=ax_summary.transAxes,
            color="white",
            linewidth=2.0,
            zorder=3,
        )
    )

    entropy = shannon(probs)

    bit_statistics = per_bit(probs)
    bit_correct_probabilities = [
        p_correct
        for p_correct, _ in bit_statistics
    ]

    mean_correct = float(np.mean(bit_correct_probabilities))
    mean_advantage = 2 * mean_correct - 1

    fig.text(
        xpos + 0.02,
        ypos + 0.37,
        "Shannon entropy",
        ha="left",
        va="center",
        fontsize=15,
        color=INK,
    )

    fig.text(
        xpos + 0.02,
        ypos + 0.30,
        f"{entropy:.2f}",
        ha="left",
        va="center",
        fontsize=34,
        color=BLUE,
        fontweight="bold",
    )

    fig.text(
        xpos + 0.02,
        ypos + 0.25,
        "bits",
        ha="left",
        va="center",
        fontsize=12,
        color=INK,
    )

    fig.text(
        xpos + 0.12,
        ypos + 0.15,
        "Advantage",
        ha="left",
        va="center",
        fontsize=15,
        color=INK,
    )

    fig.text(
        xpos + 0.12,
        ypos + 0.08,
        f"{mean_advantage:.2f}",
        ha="left",
        va="center",
        fontsize=34,
        color=BLUE,
        fontweight="bold",
    )

    fig.text(
        xpos + 0.12,
        ypos + 0.03,
        f"({int(round(100 * mean_correct))}% correct)",
        ha="left",
        va="center",
        fontsize=12,
        color=INK,
    )


def create_figure(spec: FigureSpec) -> plt.Figure:
    """Create one complete figure from a FigureSpec."""
    distributions = get_distributions(spec)

    figure_width = 12.0
    figure_height = 5.8

    fig = plt.figure(figsize=(figure_width, figure_height))

    left = 0.06
    main_width = 0.60

    ax_bars = fig.add_axes(
        [left, 0.40, main_width, 0.48]
    )

    ax_cells = fig.add_axes(
        [left, 0.04, main_width, 0.34]
    )

    draw_probability_bars(
        ax_bars,
        distributions,
        spec.labels,
    )

    ax_bars.set_title(
        spec.title,
        fontsize=14,
        loc="left",
    )

    row_centres = draw_string_cells(
        ax_cells,
        figure_width,
        figure_height,
        main_width,
    )

    if SHOW_PER_BIT:
        draw_per_bit_panel(
            fig,
            ax_cells,
            row_centres,
            distributions,
            spec.labels,
        )

    if SHOW_ENTROPY:
        # Summary box deliberately uses only the first distribution.
        draw_summary_box(fig, distributions[0])

    return fig


# =====================================================================
# MAIN
# =====================================================================

def main() -> None:
    """Generate every figure listed in FIGURES."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in FIGURES:
        fig = create_figure(spec)
        output_path = OUTPUT_DIR / spec.out_path

        if SAVE:
            fig.savefig(
                output_path,
                dpi=DPI,
                facecolor="white",
                bbox_inches=None,
            )

            distributions = get_distributions(spec)

            entropy_values = [
                round(shannon(probs), 3)
                for probs in distributions
            ]

            print(
                f"Saved {output_path} "
                f"| entropies = {entropy_values}"
            )

            plt.close(fig)

        else:
            plt.show(block=True)


if __name__ == "__main__":
    main()