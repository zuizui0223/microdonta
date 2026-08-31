"""Generate the k-channel anchor-dimension figure for the boundary paper.

The figure visualises the theorem

    residual dimension = k - 1 - r,

where k is the number of positive multiplicative channels and r is the number of
independent direct channel anchors.  It is deliberately separate from Figure 1,
which shows the two-channel proxy-calibration Gamma family.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from causal_model.multichannel_identifiability import residual_equivalence_dimension


OUT = Path(__file__).resolve().parent / "figures" / "multichannel_anchor_dimension.png"


def build_figure(output: Path = OUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.4, 4.6), constrained_layout=True)
    for channels in (2, 3, 4, 5):
        anchors = list(range(channels))
        dimensions = [
            residual_equivalence_dimension(
                channels=channels,
                independent_anchors=r,
            ).residual_dimension
            for r in anchors
        ]
        ax.plot(
            anchors,
            dimensions,
            marker="o",
            linewidth=1.8,
            label=f"k={channels}",
        )

    ax.set_xlabel("Independent direct channel anchors, r")
    ax.set_ylabel("Residual unidentified dimension")
    ax.set_title(r"A $k$-channel product leaves $k-1-r$ unresolved dimensions")
    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xlim(-0.1, 4.1)
    ax.set_ylim(-0.1, 4.1)
    ax.legend(title="Chain length")

    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


if __name__ == "__main__":
    print(build_figure())
