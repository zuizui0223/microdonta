"""Generate the boundary-paper identification geometry figure.

The figure is deterministic and uses the canonical multiplicatively symmetric
calibration-transport family. It shows the same sharp joint identified set in
ratio and log-ratio coordinates, with stable calibration as the Gamma=1 point,
finite Gamma as partial identification, and the reference-invariant breakdown
factor for the worked 1.34-fold example.
"""
from __future__ import annotations

from math import log
from pathlib import Path
import sys

# Support the documented direct invocation `python paper/make_...py` as well as
# import-based use in tests.  Direct script execution otherwise places `paper/`
# rather than the repository root on sys.path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from causal_model.calibration_transport_family import breakdown_factor, symmetric_interval


OUT = Path(__file__).resolve().parent / "figures" / "boundary_identification_geometry.png"


def _joint_curve(*, rho_x: float, rho_e_hat: float, gamma: float, n: int = 300):
    kappas = np.geomspace(1.0 / gamma, gamma, n)
    rho_f = rho_x / kappas
    rho_e = rho_e_hat * kappas
    return kappas, rho_f, rho_e


def build_figure(output: Path = OUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    rho_e_hat = 1.0 / 1.34
    rho_x = 0.80
    rho_w = rho_x * rho_e_hat

    # A finite transport tolerance used only to illustrate partial identification.
    gamma = 1.20
    _, rho_f, rho_e = _joint_curve(rho_x=rho_x, rho_e_hat=rho_e_hat, gamma=gamma)

    gamma_star, eta_star = breakdown_factor(rho_e_hat)
    _, f_break, e_break = _joint_curve(
        rho_x=rho_x,
        rho_e_hat=rho_e_hat,
        gamma=gamma_star,
        n=300,
    )
    # The upper-kappa endpoint reaches rho_E=1 at the directional breakdown.
    f_star = rho_x / gamma_star
    e_star = rho_e_hat * gamma_star

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3), constrained_layout=True)

    ax = axes[0]
    ax.plot(f_break, e_break, linewidth=1.1, linestyle="--", label=r"to breakdown $\Gamma^*=1.34$")
    ax.plot(rho_f, rho_e, linewidth=2.3, label=r"finite bound $\Gamma=1.20$")
    ax.scatter([rho_x], [rho_e_hat], zorder=4, label=r"stable endpoint $\Gamma=1$")
    ax.scatter([f_star], [e_star], zorder=4, label="directional breakdown")
    ax.axvline(1.0, linewidth=0.8, linestyle=":")
    ax.axhline(1.0, linewidth=0.8, linestyle=":")
    ax.set_xlabel(r"fecundity ratio $\rho_F$")
    ax.set_ylabel(r"establishment ratio $\rho_E$")
    ax.set_title("Sharp joint set in ratio space")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    log_f = np.log(rho_f)
    log_e = np.log(rho_e)
    log_f_break = np.log(f_break)
    log_e_break = np.log(e_break)
    ax.plot(log_f_break, log_e_break, linewidth=1.1, linestyle="--")
    ax.plot(log_f, log_e, linewidth=2.3)
    ax.scatter([log(rho_x)], [log(rho_e_hat)], zorder=4)
    ax.scatter([log(f_star)], [log(e_star)], zorder=4)
    ax.axvline(0.0, linewidth=0.8, linestyle=":")
    ax.axhline(0.0, linewidth=0.8, linestyle=":")
    ax.set_xlabel(r"$\log \rho_F$")
    ax.set_ylabel(r"$\log \rho_E$")
    ax.set_title("Log-ratio geometry: exact slope = -1")
    ax.annotate(
        rf"breakdown $\Gamma^*=1.34$\n$\eta^*={eta_star:.3f}$, $\rho_E=1$",
        (log(f_star), log(e_star)),
        xytext=(-108, 18),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->"},
    )

    # Machine-check the quantities used by the figure.
    interval = symmetric_interval(rho_e_hat, gamma=gamma)
    assert interval.lower < rho_e_hat < interval.upper
    assert np.allclose(rho_f * rho_e, rho_w)
    assert np.allclose(log_f + log_e, log(rho_w))
    assert np.isclose(e_star, 1.0)
    assert np.isclose(gamma_star, 1.34)

    fig.suptitle(r"Calibration transport: $\Gamma=1$ point ID $\rightarrow$ finite $\Gamma$ partial ID $\rightarrow$ unrestricted non-ID")
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


if __name__ == "__main__":
    print(build_figure())
