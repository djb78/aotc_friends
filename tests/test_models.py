import pytest
from domain.models import Alt, Friend, Pull

def test_pull_from_fight():
    """ correctly maps parsed fight dictionary """
    fight = {
        "id": 1,
        "encounterID": 100,
        "name": "Boss_100",
        "kill": False,
        "friendlyPlayers": [1, 2, 3]
    }
    pull = Pull.from_fight("code_1", fight)

    assert pull.log == "code_1"
    assert pull.id == 1
    assert pull.kill is False
    assert pull.boss == {"id": 100, "name": "Boss_100"}
    assert pull.roster == [1, 2, 3]

def test_alt_from_player():
    """ correctly maps parsed player dictionary """
    player = {
        "name": "player",
        "server": "realm",
        "region": "US",
        "type": "class"
    }
    alt = Alt.from_player(1000, player)

    assert alt.guid == 1000
    assert alt.name == "player"
    assert alt.server == "realm"
    assert alt.region == "US"
    assert alt.type == "class"
    assert alt.specs == {}
    assert alt.sightings == 0

def test_alt_update_specs():
    """ adds a new log spec count to specs """
    player = {
        "name": "player", 
        "server": "realm", 
        "region": "US", 
        "type": "class",
        "role": "tank",
        "specs": [ {"spec": "spec1", "count": 2 } ]
    }
    alt = Alt.from_player(1000, player)

    assert alt.specs == {}

    alt.update_specs("code_1", player)

    assert "spec1" in alt.specs
    spec = alt.specs["spec1"]
    assert spec["role"] == "tank"
    assert spec["log_counts"] == {"code_1": 2}

def test_alt_update_specs_defensive():
    """ skip improperly formatted spec data """
    player = {
        "name": "player",
        "role": "dps",
        "specs": [
            "no_dict",
            {"spec": "bad_count", "count": "no_int"},
            {"spec": "no_count"},
            {"spec": "valid_spec", "count": 5}
        ]
    }
    alt = Alt.from_player(1000, player)
    alt.update_specs("code_1", player)

    assert "valid_spec" in alt.specs
    assert "bad_count" not in alt.specs
    assert "no_count" not in alt.specs

def test_update_specs_duplicate():
    """ don't overwrite or duplicate log count data """
    player = {
        "name": "player",
        "role": "dps",
        "specs": [{"spec": "spec1", "count": 2}]
    }
    # base alt
    alt = Alt.from_player(1000, player)

    # specs
    alt.update_specs("code_1", player)
    # duplicate spec data
    alt.update_specs("code_1", player)
    # different count
    player["specs"][0]["count"] = 3
    alt.update_specs("code_1", player)

    assert alt.specs["spec1"]["log_counts"] == {"code_1": 2}

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