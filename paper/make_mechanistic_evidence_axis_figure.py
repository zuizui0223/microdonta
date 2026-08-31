"""Generate the conceptual mechanistic-evidence figure for the boundary paper.

The figure separates biological measurement level / mechanistic proximity from
identification strength. Example positions are illustrative and explicitly
conditional on the declared candidate mechanisms and observation map.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


OUT = Path(__file__).resolve().parent / "figures" / "mechanistic_evidence_axes.png"


def build_figure(output: Path = OUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.4, 5.4), constrained_layout=True)

    examples = [
        (0.16, 0.18, "Net field pattern /\naggregate endpoint"),
        (0.78, 0.24, "Direct channel anchor /\ndiscriminating field observation"),
        (0.24, 0.80, "Molecular or genomic signature\nshared by several mechanisms"),
        (0.82, 0.84, "Proximal intervention or measurement\nthat uniquely separates alternatives"),
    ]

    for x, y, label in examples:
        ax.scatter([x], [y], s=55, zorder=3)
        ax.annotate(label, (x, y), xytext=(8, 7), textcoords="offset points", fontsize=9)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([0.08, 0.50, 0.92], ["non-identifying", "partially identifying", "point-identifying"])
    ax.set_yticks([0.12, 0.50, 0.88], ["field / endpoint", "organismal / physiological", "genomic / molecular"])
    ax.set_xlabel("Identification strength among declared competing mechanisms")
    ax.set_ylabel("Biological measurement level / mechanistic proximity")
    ax.set_title("Measurement level and identification strength are different axes")
    ax.grid(True, linewidth=0.5, alpha=0.35)

    fig.text(
        0.5,
        0.01,
        "Illustrative positions only: identification strength is conditional on the candidate mechanism set and observation map.",
        ha="center",
        fontsize=8.5,
    )

    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


if __name__ == "__main__":
    print(build_figure())
