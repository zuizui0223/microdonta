# Migration-safe refuge allele bound

The simulator migration update is

```text
p_j^mig = (1-m) p_j^sel + m p_bar^sel,
```

where `p_bar^sel` is the census-weighted mean selected allele frequency.

If the focal selected frequency has lower bound `a` and the source mean has
lower bound `b`, then exactly

```text
p_j^mig >= (1-m)a + mb.
```

This gives a sharp criterion for whether migration preserves a refuge allele
threshold `p_min`.

```text
(1-m)a + mb >= p_min.
```

Consequences:

- if every patch shares the same selected lower bound `p_min`, migration cannot
  reduce that common bound;
- a low source mean can erode a high focal refuge;
- a high source mean can rescue a low focal patch.

This lemma removes neither the high-trait recruitment risk nor the need for a
metapopulation source-mean lower bound. It is the exact migration component
needed to extend the no-migration refuge theorem to a declared network region.
