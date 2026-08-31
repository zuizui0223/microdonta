from math import isclose

import pytest

from causal_model.multichannel_identifiability import (
    channel_ratio_dimension,
    log_gauge_basis,
    reconstruct_final_channel,
    residual_equivalence_dimension,
    residual_product,
)


def test_net_only_k_channel_equivalence_dimension_is_k_minus_one():
    for k in (2, 3, 4, 7):
        result = residual_equivalence_dimension(channels=k, independent_anchors=0)
        assert result.residual_dimension == k - 1
        assert result.identification == "non_identified"


def test_each_independent_channel_anchor_removes_one_dimension():
    k = 5
    expected = {
        0: (4, "non_identified"),
        1: (3, "partially_identified"),
        2: (2, "partially_identified"),
        3: (1, "partially_identified"),
        4: (0, "point_identified"),
    }
    for anchors, (dimension, state) in expected.items():
        result = residual_equivalence_dimension(
            channels=k,
            independent_anchors=anchors,
        )
        assert result.residual_dimension == dimension
        assert result.identification == state


def test_log_gauge_basis_has_k_minus_one_product_preserving_directions():
    basis = log_gauge_basis(4)
    assert len(basis) == 3
    assert all(len(vector) == 4 for vector in basis)
    assert all(isclose(sum(vector), 0.0) for vector in basis)


def test_k_minus_one_anchors_reconstruct_the_final_channel():
    value = reconstruct_final_channel(
        net_product=120.0,
        anchored_values=(2.0, 3.0, 4.0),
        channels=4,
    )
    assert isclose(value, 5.0)


def test_residual_product_describes_the_unanchored_subchain():
    assert isclose(
        residual_product(net_product=60.0, anchored_values=(2.0, 3.0)),
        10.0,
    )


def test_before_after_ratio_corollary_has_same_dimension_rule():
    result = channel_ratio_dimension(channels=4, observed_channel_ratios=2)
    assert result.residual_dimension == 1
    assert result.identification == "partially_identified"


def test_invalid_anchor_counts_are_rejected():
    with pytest.raises(ValueError):
        residual_equivalence_dimension(channels=3, independent_anchors=3)
    with pytest.raises(ValueError):
        reconstruct_final_channel(
            net_product=12.0,
            anchored_values=(2.0,),
            channels=3,
        )
