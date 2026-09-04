# Applications

No interactive application is part of the active **Mechanism-Resolving Observation Design** submission or public package API.

The former exploratory Streamlit interface was tied to retired pre-rename terminology and provisional worked examples. It has been moved to `legacy/` for provenance rather than maintained as an active interface.

Use the publication-facing Python API instead:

```python
from causal_model import (
    compute_admissible_mechanisms,
    observation_information_value,
    sequential_observation_design,
)
```

Applications added here in the future must use the current method vocabulary and remain outside the manuscript evidence bundle unless explicitly promoted by the submission manifest.
