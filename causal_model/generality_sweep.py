"""Truth-peek-free controlled benchmark for information-guided observation selection.

This is the publication-facing reference surface for the frozen G2 benchmark.
The historical implementation is isolated in ``_compat_generality_sweep`` so the
frozen machine-level policy key can remain reproducible without defining the
current method vocabulary.

The benchmark compares two preregistered policy keys on identical generated
systems, hidden truths, candidate vocabularies and budgets:

``information-guided``
    selects the remaining candidate with maximum current observation information
    value and conditions only after selection;

``random_order``
    selects uniformly among remaining candidates and serves as an uninformed
    observation-ordering baseline.

The frozen JSON stores the information-guided policy under its historical key
``rach_seq``. That string is preserved only for exact protocol/result lookup.
"""
from __future__ import annotations

from . import _compat_generality_sweep as _impl

HISTORICAL_INFORMATION_GUIDED_POLICY_KEY = "rach_seq"
INFORMATION_GUIDED_POLICY = "information_guided"
RANDOM_ORDER_POLICY = "random_order"

Policy = _impl.Policy
SystemRecord = _impl.SystemRecord
SweepResult = _impl.SweepResult
BudgetSummary = _impl.BudgetSummary

# Benchmark-construction helpers retained because the frozen runner and integrity
# tests intentionally exercise the exact generator used to create G2.
_abc_accept = _impl._abc_accept
_candidates_for_system = _impl._candidates_for_system
_make_random_system = _impl._make_random_system
_sample_driver_coefficients = _impl._sample_driver_coefficients
_truth_magnitude = _impl._truth_magnitude
_truth_outcome_overrides = _impl._truth_outcome_overrides
_outcome_by_name = _impl._outcome_by_name
_truth_retained = _impl._truth_retained
_summarize = _impl._summarize
_run_random_order = _impl._run_random_order
_run_information_guided_policy = _impl._run_rach_policy

run_generality_sweep = _impl.run_generality_sweep
run_budget_sweep = _impl.run_budget_sweep
save_budget_table = _impl.save_budget_table
make_figure = _impl.make_figure


def display_policy_name(policy: str) -> str:
    """Translate a frozen machine policy key into current presentation vocabulary."""
    if policy == HISTORICAL_INFORMATION_GUIDED_POLICY_KEY:
        return INFORMATION_GUIDED_POLICY
    return policy


def run_information_guided_sweep(*args, **kwargs):
    """Run the frozen information-guided policy using descriptive caller vocabulary."""
    kwargs = dict(kwargs)
    kwargs["policy"] = HISTORICAL_INFORMATION_GUIDED_POLICY_KEY
    return _impl.run_generality_sweep(*args, **kwargs)


def print_report(result: SweepResult) -> None:
    """Print the controlled benchmark summary with descriptive policy labels."""
    print("=" * 76)
    print(
        "Mechanism-Resolving Observation Design controlled selection benchmark "
        f"— policy={display_policy_name(result.policy)}"
    )
    print("=" * 76)
    print(f"systems run              : {len(result.records)} / {result.n_systems}")
    print(f"systems with >=1 edge    : {result.systems_with_edges}")
    if not result.records:
        print("no systems produced a usable admissible region")
        return
    print(f"fully converged          : {result.frac_converged * 100:.1f}%")
    print(f"edges resolved (mean)    : {result.mean_frac_resolved * 100:.1f}%")
    print(f"resolvability R          : {result.mean_R0:.3f} -> {result.mean_R_final:.3f}")
    print(f"observations taken       : {result.mean_steps:.2f}")
    print(f"nuisance selections      : {result.mean_distractors_selected:.2f}")
    print(f"false exclusion rate     : {result.false_exclusion_rate * 100:.2f}%")


def print_budget_table(summaries) -> None:
    """Print budget summaries with the historical guided key translated for display."""
    print("policy                 budget  converged  resolved  steps  nuisance  false_exclusion")
    for summary in summaries:
        print(
            f"{display_policy_name(summary.policy):22s} {summary.budget:>6d}  "
            f"{summary.frac_converged:>9.3f}  {summary.mean_frac_resolved:>8.3f}  "
            f"{summary.mean_steps:>5.2f}  {summary.mean_distractors_selected:>8.2f}  "
            f"{summary.false_exclusion_rate:>15.3f}"
        )


def __getattr__(name: str):
    """Delegate non-public historical helpers needed by frozen support code."""
    return getattr(_impl, name)


if __name__ == "__main__":  # pragma: no cover - historical CLI compatibility
    _impl.main()
