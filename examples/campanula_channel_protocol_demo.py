"""Show why the published Campanula record is not channel-identifying yet.

Run with:

    python -m examples.campanula_channel_protocol_demo
"""
from __future__ import annotations

import json

from causal_model.campanula_channel_protocol import (
    assessment_as_dict,
    planned_recruitment_protocol,
    published_campanula_protocol,
)


def main() -> None:
    payload = {
        "published_record": assessment_as_dict(published_campanula_protocol()),
        "prospective_design": assessment_as_dict(planned_recruitment_protocol()),
        "interpretation": {
            "current": (
                "Published selfing/flower-size gradients and a pollinator transition retain competing "
                "mechanisms but do not identify local reproduction F versus establishment E."
            ),
            "after_collection": (
                "A trait-specific W plus direct total local reproduction F can identify F/E change "
                "within the declared life-cycle factorisation."
            ),
            "separate_requirement": (
                "Attributing a component of F specifically to pollinator service requires a separately "
                "declared and validated component experiment."
            ),
        },
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
