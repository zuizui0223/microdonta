# Correction note: compensation threshold

Earlier versions of this repository described

```text
R_replace = B(z*)
```

as the *exact* compensation threshold for preventing the upper viable edge from
receding after relationship loss, where `z* = z_max(1, 0)`.

That statement was too strong.

For

```text
s_before(z) = B(z) - C(z) + K
s_after(z; R) = -C(z) + K + R,
```

the exact minimum compensation that retains the existing edge trait is

```text
R_keep = max(0, C(z*) - K).
```

On a fixed ordered trait grid with non-decreasing cost, this is also the exact
threshold for preventing the upper edge from receding:

```text
R >= R_keep  iff  z* remains viable after loss.
```

The former quantity is a sufficient replacement bound, because prior viability
of `z*` implies

```text
C(z*) - K <= B(z*).
```

It need not be minimal. Equality occurs only when the prior edge lies exactly on
the invasion boundary, `s_before(z*) = 0`.

The correction is deliberately retained as a separate note because the next
phase of the repository treats mathematical assumptions and proofs as primary;
randomised tests are implementation checks, not a substitute for a valid theorem.
