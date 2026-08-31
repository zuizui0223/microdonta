"""Generate the boundary-paper identification geometry figure.

The figure is intentionally deterministic and uses only the closed-form bounded
proxy-drift result. It visualises the same joint identified set in ratio and
log-ratio coordinates and marks the directional breakdown point.
"""
from __future__ import annotations

from math import log
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from causal_model.bounded_proxy_drift import identify_under_bounded_proxy_drift


OUT = Path(__file__).resolve().parent / "figures" / "boundary_identification_geometry.png"


def build_figure(output: Path = OUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    rho_e_hat = 1.0 / 1.34
    rho_x = 0.80
    rho_w = rho_x * rho_e_hat
    delta = 0.20
    result = identify_under_bounded_proxy_drift(
        net_ratio=rho_w,
        proxy_ratio=rho_x,
        delta=delta,
        proxy_channel="fecundity",
    )

    kappas = np.linspace(1.0 - delta, 1.0 + delta, 300)
    rho_f = rho_x / kappas
    rho_e = rho_e_hat * kappas

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), constrained_layout=True)

    ax = axes[0]
    ax.plot(rho_f, rho_e, linewidth=2.2)
    ax.scatter([rho_x], [rho_e_hat], zorder=3)
    ax.axvline(1.0, linewidth=0.8, linestyle="--")
    ax.axhline(1.0, linewidth=0.8, linestyle="--")
    ax.set_xlabel(r"fecundity ratio $\rho_F$")
    ax.set_ylabel(r"establishment ratio $\rho_E$")
    ax.set_title("Joint identified set in ratio space")
    ax.annotate("N3: stable calibration", (rho_x, rho_e_hat), xytext=(8, 8), textcoords="offset points")

    ax = axes[1]
    log_f = np.log(rho_f)
    log_e = np.log(rho_e)
    ax.plot(log_f, log_e, linewidth=2.2)
    ax.scatter([log(rho_x)], [log(rho_e_hat)], zorder=3)
    ax.axvline(0.0, linewidth=0.8, linestyle="--")
    ax.axhline(0.0, linewidth=0.8, linestyle="--")
    ax.set_xlabel(r"$\log \rho_F$")
    ax.set_ylabel(r"$\log \rho_E$")
    ax.set_title("Same set in log-ratio space: slope = -1")

    # Mark the calibration-drift breakdown for the complementary channel.
    delta_star = 0.34
    kappa_star = 1.0 + delta_star
    f_star = rho_x / kappa_star
    e_star = rho_e_hat * kappa_star
    ax.scatter([log(f_star)], [log(e_star)], zorder=4)
    ax.annotate(
        r"breakdown: $\delta^*=0.34$, $\rho_E=1$",
        (log(f_star), log(e_star)),
        xytext=(-95, 18),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->"},
    )

    assert result.joint_log_segment.slope == -1.0
    assert result.joint_log_segment.satisfies_net_constraint()

    fig.suptitle("N3 → bounded partial identification → N4")
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


if __name__ == "__main__":
    print(build_figure())
