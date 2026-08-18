import pytest
from etl.models import Alt

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
