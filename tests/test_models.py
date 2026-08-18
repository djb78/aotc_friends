import pytest
from etl.models import Alt, Friend

def test_alt_sort_specs_empty():
    """ handles friend with no specs """
    alt = Alt(1)
    alt.specs = {}

    alt.sort_specs()
    assert alt.specs == {}

def test_alt_sort_specs():
    alt = Alt(1)
    alt.specs = {
        "Assassination": {
            "role": "DPS",
            "log_counts": {"log1": 2, "log2": 3}
        },
        "Subtlety": {
            "role": "DPS",
            "log_counts": {"log1": 10}
        },
        "Outlaw": {
            "role": "DPS",
            "log_counts": {"log1": "corrupted", "log2": 1}
        }
    }
    alt.sort_specs()

    assert alt.specs["Subtlety"]["sightings"] == 10
    assert alt.specs["Assassination"]["sightings"] == 5
    assert alt.specs["Outlaw"]["sightings"] == 1

    specs_order = list(alt.specs.keys())
    assert specs_order == ["Subtlety", "Assassination", "Outlaw"]

def test_friend_init():
    """ calculate friend sightings and choose main """
    alt1 = Alt(1)
    alt1.name = "Stiff"
    alt1.sightings = 10

    alt2 = Alt(2)
    alt2.name = "Darkbark"
    alt2.sightings = 25

    shape = Friend([alt1, alt2])

    assert shape.sightings == 35
    assert shape.alts[0].name == "Darkbark"
    assert shape.alts[1].name == "Stiff"
    assert shape.main.name == "Darkbark"