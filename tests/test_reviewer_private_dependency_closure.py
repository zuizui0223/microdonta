from pathlib import Path

from paper.build_reviewer_bundle import scientific_module_closure


def test_reviewer_closure_includes_private_facade_implementations():
    paths = {path.as_posix() for path in scientific_module_closure()}
    assert any(path.endswith("causal_model/_compat_mechanism_region.py") for path in paths)
    assert any(path.endswith("causal_model/_compat_sequential_observation.py") for path in paths)
