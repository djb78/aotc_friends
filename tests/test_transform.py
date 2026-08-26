import pytest, copy
from datetime import time
from unittest.mock import MagicMock
from services.file_io import FIGHTS_CACHE, PLAYERS_CACHE
from etl.transform import Transformer
from domain.schema import ScheduleConfig, AppConfig
from domain.models import Alt, Pull

class MockPull:
    def __init__(self, log):
        self.log = log
        self.roster = []
        self.boss = {"id": 666}
        self.kill = False

@pytest.fixture
def valid_log_times():
    """ valid log times for tests """
    return {
        "log01": 1000000,
        "log02": 2000000,
        "log03": 3000000
    }

def test_transform_all(valid_config):
    """test: all transform pipeline methods are called"""
    t = Transformer(valid_config)

    t.transform_fights_pulls = MagicMock()
    t.filter_aotc_prog = MagicMock()
    t.transform_pulls_alts = MagicMock()

    t.transform_all()

    t.transform_fights_pulls.assert_called_once()
    t.filter_aotc_prog.assert_called_once()
    t.transform_pulls_alts.assert_called_once()


# transform_fights_pulls
# ======================
def test_transform_fights_pulls_success(valid_config, make_json_cache, mock_fights_cache):
    make_json_cache(valid_config, mock_fights_cache, FIGHTS_CACHE)

    log_b = mock_fights_cache["data"]["reportData"]["alias_b"]
    log_c = mock_fights_cache["data"]["reportData"]["alias_c"]

    t = Transformer(valid_config)
    t.config.schedule = None

    t.transform_fights_pulls()

    assert t.log_times == {
        log_b["code"]: log_b["startTime"],
        log_c["code"]: log_c["startTime"]
    }

    assert len(t.pulls) == len(log_b["fights"]) + len(log_c["fights"])

    first_pull = t.pulls[0]
    assert first_pull.log == "code_1"
    assert first_pull.id == 1


def test_transform_fights_pulls_schedule(valid_config, make_json_cache, mock_fights_cache, make_ms):
    valid_config.schedule = ScheduleConfig(
        days=["tuesday", "saturday"],
        start_est="20:00",
        end_est="22:00"
    )
    on_schedule = make_ms("Tuesday", "20:04")
    off_schedule = make_ms("wednesday", "20:15")

    fights = copy.deepcopy(mock_fights_cache)
    log_b = fights["data"]["reportData"]["alias_b"]
    log_c = fights["data"]["reportData"]["alias_c"]

    two_fights = log_b["code"]
    log_b["startTime"] = on_schedule
    one_fight = log_c["code"]
    log_c["startTime"] = off_schedule

    make_json_cache(valid_config, fights, FIGHTS_CACHE)
    t = Transformer(valid_config)

    t.transform_fights_pulls()

    assert two_fights in t.log_times
    assert t.log_times[two_fights] == on_schedule
    assert one_fight not in t.log_times

    assert len(t.pulls) == 2
    for pull in t.pulls:
        assert pull.log == two_fights

# filter_aotc_prog
def test_filter_prog_success(valid_config, valid_log_times):
    t = Transformer(valid_config)
    t.log_times = valid_log_times
    t.config.raid["final_boss"]["id"] = 666
    pulls = {
    "prog01": MockPull("log01"),
    "prog02": MockPull("log01"),
    "prog03": MockPull("log02"),
    "kill01": MockPull("log02"),
    "wipe01": MockPull("log03"),
    "wipe02": MockPull("log03"),
    "kill02": MockPull("log03") }
    pulls["kill01"].kill = True
    pulls["kill02"].kill = True
    t.pulls.extend(pulls.values())

    t.filter_aotc_prog()

    prog = ["prog01", "prog02", "prog03", "kill01"]
    farm = ["wipe01", "wipe02", "kill02"]
    prog_pulls = []
    for pull in prog:
        assert pulls[pull].log in t.log_times
        prog_pulls.append(pulls[pull])
    for pull in farm:
        assert pulls[pull].log not in t.log_times
    assert t.pulls == prog_pulls

def test_filter_aotc_prog_no_kill(valid_config, valid_log_times):
    t = Transformer(valid_config)
    t.log_times = valid_log_times
    t.config.raid["final_boss"]["id"] = 666
    pulls = {
    "prog01": MockPull("log01"),
    "prog02": MockPull("log01"),
    "prog03": MockPull("log02")   }
    for pull in pulls.values():
        t.pulls.append(pull)

    t.filter_aotc_prog()

    assert len(t.pulls) == 3
    assert len(t.log_times) == 3

# transform_pulls_alts
def test_transform_pulls_alts_success(valid_config, make_json_cache, mock_players_cache):
    """ converts roster to guids, creates alts list """
    make_json_cache(valid_config, mock_players_cache, PLAYERS_CACHE)

    t = Transformer(valid_config)

    t.log_times = {
        "code_1": 100000,
        "code_2": 200000
    }

    pull1 = Pull("code_1", 1)
    pull1.roster = [1, 2, 3]

    pull2 = Pull("code_2", 2)
    pull2.roster = [20, 40]

    t.pulls = [pull1, pull2]

    t.transform_pulls_alts()

    assert pull1.roster == [1000, 2000, 3000]
    assert pull2.roster == [2000, 4000]

    assert 1000 in t.alts
    assert 2000 in t.alts
    assert 3000 in t.alts
    assert 4000 in t.alts

    assert t.alts[1000].sightings == 1
    assert t.alts[2000].sightings == 2
    assert t.alts[3000].sightings == 1
    assert t.alts[4000].sightings == 1


def test_transform_pulls_alts_missing_guid(valid_config, make_json_cache, mock_players_cache):
    alt_roles = mock_players_cache["data"]["reportData"]["alias_a"]["playerDetails"]["data"]["playerDetails"]
    alt_roles["tanks"][0]["guid"] = None    # only guid 3000 spec
    alt_roles["dps"][0]["guid"] = None      # 1/2 guid 1000 specs
    make_json_cache(valid_config, mock_players_cache, PLAYERS_CACHE)

    t = Transformer(valid_config)
    t.log_times = {"code_1": 100000, "code_2": 200000}

    pull1 = Pull("code_1", 1)
    pull1.roster = [1, 2, 3]
    pull2 = Pull("code_2", 2)
    pull2.roster = [20, 40]
    t.pulls = [pull1, pull2]

    t.transform_pulls_alts()

    assert pull1.roster == [1000, 2000]
    assert pull2.roster == [2000, 4000]

    assert 1000 in t.alts
    assert 2000 in t.alts
    assert 4000 in t.alts
    assert None not in t.alts

# update_alt
# ==============
@pytest.fixture
def valid_sighting():
    """ valid base sighting for tests """
    return {
        "guid": 3000,
        "name": "Tank_3000",
        "server": "Server",
        "region": "US",
        "type": "tank_class",
        "role": "tank",
        "specs": [{"spec": "tank_spec", "count": 5}]
    }

def test_update_alt_invalid(valid_config, valid_log_times):
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    invalid_sightings = [{}, "invalid sighting", [], {"name": "Atpar", "type": "Paladin"}]
    for sighting in invalid_sightings:
        guid = t.update_alt("log01", sighting)
        assert guid is None
        assert len(t.pulls) == 0

def test_update_alt_new(valid_config, valid_sighting, valid_log_times):
    """ creates a new alt with metadata and
        increments sightings
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    guid = t.update_alt("log01", valid_sighting)
    assert guid == 3000
    alt = t.alts[guid]
    assert alt.name == "Tank_3000"
    assert alt.server == "Server"
    assert alt.region == "US"
    assert alt.type == "tank_class"
    assert "tank_spec" in alt.specs
    assert alt.specs["tank_spec"] == {"role": "tank", "log_counts": {"log01": 5}}


def test_update_alt_same_spec(valid_config, valid_sighting, valid_log_times):
    """ duplicates are ignored, new log = new count 
        always increment sightings
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)

    guid = t.update_alt("log01", sighting)
    assert guid == 3000
    alt = t.alts[guid]
    assert alt.specs["tank_spec"]["log_counts"]["log01"] == 5

    # same log different fight, just increment sightings
    t.update_alt("log01", sighting)
    assert alt.specs["tank_spec"]["log_counts"]["log01"] == 5

    # same log different fight, different/missing count, ignore
    sighting["specs"] = [{"spec": "tank_spec", "count": None}]
    t.update_alt("log01", sighting)
    assert alt.specs["tank_spec"]["log_counts"]["log01"] == 5

    sighting["specs"] = [{"spec": "tank_spec", "count": 8}]
    t.update_alt("log01", sighting)
    assert alt.specs["tank_spec"]["log_counts"]["log01"] == 5

    # different log = new log_count
    t.update_alt("log02", sighting)
    assert alt.specs["tank_spec"]["log_counts"]["log01"] == 5
    assert alt.specs["tank_spec"]["log_counts"]["log02"] == 8

def test_update_alt_multi_spec(valid_config, valid_sighting, valid_log_times):
    """ new specs are added, """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)
    sighting["name"] = "Flex_1000"
    sighting["guid"] = 1000
    sighting["server"] = "Server"

    sighting["role"] = "healers"
    sighting["specs"] = [{"spec": "heal_spec_1", "count": 1}]

    guid = t.update_alt("log01", sighting)
    assert guid == 1000
    alt = t.alts[guid]

    assert alt.specs["heal_spec_1"]["log_counts"]["log01"] == 1

    sighting["role"] = "dps"
    sighting["specs"] = [{"spec": "dps_spec_1", "count": 1}]

    t.update_alt("log01", sighting)
    assert alt.specs["heal_spec_1"]["log_counts"]["log01"] == 1
    assert alt.specs["dps_spec_1"]["log_counts"]["log01"] == 1

def test_update_alt_missing(valid_config, valid_log_times, valid_sighting):
    """ missing/non-list specs value doesn't alter existing specs
        empty/non-dict spec values are skipped, valid values are processed normally
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)

    # missing spec field
    sighting.pop("specs")
    guid = t.update_alt("log01", sighting)
    assert guid == 3000
    alt = t.alts[guid]
    assert alt.specs == {}

    # specs not a list 
    not_lists = [None, "randomstring", 5, {}]
    for non_list in not_lists:
        sighting["specs"] = non_list
        t.update_alt("log01", sighting)
        assert alt.specs == {}

    # invalid specs
    one_spec = [{}, 4, "tank_spec", [], {"spec": "tank_spec", "count": 5}]
    sighting["specs"] = one_spec
    t.update_alt("log01", sighting)
    assert alt.specs == {"tank_spec": {"role": "tank", "log_counts": {"log01": 5}}}


# transform_alts_friends
# ======================
def test_transform_alts_friends_specs(valid_config):
    """ trigger arrange_specs on all alts """
    t = Transformer(valid_config)

    alt = Alt(1)
    alt.name = "Dps_2000"
    alt.server = "Server"
    alt.specs = {
        "dps_spec_1": {"role": "DPS", "log_counts": {"log1": 10}}
    }
    t.alts = {1: alt}

    t.transform_alts_friends()

    assert "sightings" in alt.specs["dps_spec_1"]
    assert alt.specs["dps_spec_1"]["sightings"] == 10

def test_transform_alts_friends_missing_main(valid_config):
    alt1 = Alt(1)
    alt1.name = "Notmain1_1000"
    alt1.server = "Server"
    alt1.sightings = 10

    alt2 = Alt(2)
    alt2.name = "Notmain2_1000"
    alt2.server = "Server"
    alt2.sightings = 5

    config_dict = valid_config.model_dump()
    config_dict["has_alts"] = { "Main_1000-Server": ["Notmain1_1000-Server", "Notmain2_1000-Server"] }
    alt_config = AppConfig.model_validate(config_dict)

    t = Transformer(alt_config)
    t.alts = {1: alt1, 2: alt2}

    t.transform_alts_friends()

    assert len(t.friends) == 1
    friend = t.friends[0]
    assert friend.sightings == 15
    assert friend.main.name == "Notmain1_1000"
    assert len(friend.alts) == 2