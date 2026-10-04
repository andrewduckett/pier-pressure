"""The per-rank target sensors, Target 1 to Target TOP_N (spec ha-delivery).

Each rank of the target list gets its own sensor on the pier's device. A filled
rank's state is the target's display name, and its attributes carry the rank and
the target's fields. An empty rank publishes an ``available: false`` marker that
its discovery availability turns into ``unavailable``. Every publish writes every
rank, so a shrinking list never leaves an earlier target retained.
"""

from __future__ import annotations

import json

from pierpressure.delivery.mqtt import (
    rank_target_attributes_topic,
    rank_target_state_topic,
)

BASE = "pierpressure"


# --------------------------------------------------------------------------- #
# Topics (design D1)
# --------------------------------------------------------------------------- #


def test_rank_topics_derive_from_pier_and_rank() -> None:
    assert rank_target_state_topic(BASE, "backyard", 3) == "pierpressure/backyard/target_3/state"
    assert (
        rank_target_attributes_topic(BASE, "backyard", 3)
        == "pierpressure/backyard/target_3/attributes"
    )
