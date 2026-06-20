"""Ensure the repository root is importable when pytest is invoked as a bare
``pytest`` command (CI) rather than ``python -m pytest``.

With pytest's default ``prepend`` import mode, the directory inserted onto
``sys.path`` is the one containing the first collected test (``tests/``), not
the repository root — so ``import causal_model`` fails under bare ``pytest``
unless the package is installed (``pip install -e .``). The mere presence of
this file at the repository root makes pytest add the root to ``sys.path``,
fixing imports for every invocation style without requiring an editable install.
"""
