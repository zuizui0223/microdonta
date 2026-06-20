"""Tests for the mechanism equivalence structure recovered from A_e."""
from causal_model.mechanism_equivalence import (
    mechanism_equivalence_structure,
    ConfoundingEdge,
    EquivalenceStructure,
)


class _SW:
    def __init__(self, name):
        self.name = name


def _switches(names):
    return [_SW(n) for n in names]


def test_empty_region_is_handled():
    es = mechanism_equivalence_structure([], _switches(["A", "B"]))
    assert es.n_accepted == 0
    assert es.n_total_configs == 4
    assert es.free == ["A", "B"]
    assert es.edges == []


def test_disjunction_edge_is_detected():
    # Construct an A_e where the data require (A OR B) but leave which free,
    # and C is pinned ON, D pinned OFF — the canonical confound signature.
    rows = []
    for a, b in [(1, 0), (0, 1), (1, 1)]:          # (0,0) never admissible
        for _ in range(20):
            rows.append({"A": a, "B": b, "C": True, "D": False})
    es = mechanism_equivalence_structure(rows, _switches(["A", "B", "C", "D"]))

    assert "C" in es.pinned_on
    assert "D" in es.pinned_off
    assert set(es.free) == {"A", "B"}

    # exactly one confounding edge, A-B, and it is a disjunction
    assert len(es.edges) == 1
    e = es.edges[0]
    assert {e.a, e.b} == {"A", "B"}
    assert e.relation == "disjunction"
    assert e.phi < 0                                # substitutable => negative
    assert es.substitutable_groups == [["A", "B"]]


def test_mutual_exclusion_is_detected():
    rows = []
    for a, b in [(1, 0), (0, 1), (0, 0)]:          # (1,1) never admissible
        for _ in range(20):
            rows.append({"A": a, "B": b})
    es = mechanism_equivalence_structure(rows, _switches(["A", "B"]))
    assert len(es.edges) == 1
    assert es.edges[0].relation == "mutual_exclusion"


def test_independent_switches_have_no_edges():
    # A and B independent and balanced -> no coupling edge.
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            for _ in range(25):
                rows.append({"A": a, "B": b})
    es = mechanism_equivalence_structure(rows, _switches(["A", "B"]))
    assert es.edges == []
    assert es.substitutable_groups == []


def test_describe_runs():
    rows = [{"A": 1, "B": 0}, {"A": 0, "B": 1}, {"A": 1, "B": 1}] * 10
    es = mechanism_equivalence_structure(rows, _switches(["A", "B"]))
    text = es.describe()
    assert "Mechanism equivalence structure" in text
    assert isinstance(es, EquivalenceStructure)
    assert all(isinstance(e, ConfoundingEdge) for e in es.edges)
