import pytest, copy
from unittest.mock import MagicMock, patch
from etl.transform import Transformer

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
    t = Transformer(valid_config)

    t.transform_fights_pulls = MagicMock()
    t.filter_aotc_prog = MagicMock()
    t.transform_roster = MagicMock()

    t.transform_all()

    t.transform_fights_pulls.assert_called_once()
    t.filter_aotc_prog.assert_called_once()
    t.transform_roster.assert_called_once()


# transform_fights_pulls
# ======================
@patch("etl.transform.on_schedule")
@patch("etl.transform.parse_fights")
@patch("etl.transform.load_cache")
def test_transform_fights_pulls_success(mock_load_cache, mock_parse_fights, mock_on_schedule, valid_config):
    mock_on_schedule.return_value = True
    mock_parse_fights.return_value = {
        "log01": {
            "time": 1000000,
            "zone_id": 35,
            "fights": [
                { "id": 1, 
                  "kill": False, 
                  "encounterID": 101, 
                  "name": "Eranog", 
                  "difficulty": 4,
                  "friendlyPlayers": [5001, 5002] },
                { "id": 2,
                  "kill": True,
                  "encounterID": 101,
                  "name": "Eranog",
                  "difficulty": 4,
                  "friendlyPlayers": [5001, 5002, 5003] }
            ] } }
    t = Transformer(valid_config)
    t.config["schedule"] = { "fake_time": 1111111111 }

    t.transform_fights_pulls()

    assert t.log_times == {"log01": 1000000}
    assert len(t.pulls) == 2

    pull = t.pulls[0]
    assert pull.log == "log01"
    assert pull.id == 1
    assert pull.kill is False
    assert pull.boss == {"id": 101, "name": "Eranog"}
    assert pull.roster == [5001, 5002]

    pull = t.pulls[1]
    assert pull.log == "log01"
    assert pull.id == 2
    assert pull.kill is True
    assert pull.boss == {"id": 101, "name": "Eranog"}
    assert pull.roster == [5001, 5002, 5003]

@patch("etl.transform.on_schedule")
@patch("etl.transform.parse_fights")
@patch("etl.transform.load_cache")
def test_transform_fights_pulls_schedule(mock_load_cache, mock_parse_fights, mock_on_schedule, valid_config):
    mock_parse_fights.return_value = {
        "log01": {
            "time": 1000000,
            "zone_id": 35,
            "fights": [
                { "id": 1, 
                  "kill": False, 
                  "encounterID": 101, 
                  "name": "Eranog", 
                  "difficulty": 4,
                  "friendlyPlayers": [5001, 5002] }
            ] },
        "log02": {
            "time": 2000000,
            "zone_id": 35,
            "fights": [
                { "id": 2,
                  "kill": True,
                  "encounterID": 101,
                  "name": "Eranog",
                  "difficulty": 4,
                  "friendlyPlayers": [5001, 5002, 5003] }
            ] } } 
    mock_on_schedule.side_effect =  lambda time, schedule: time == 1000000
    t = Transformer(valid_config)
    t.config["schedule"] = { "fake_time": 1111111111 }

    t.transform_fights_pulls()

    assert "log01" in t.log_times
    assert "log02" not in t.log_times

    assert len(t.pulls) == 1
    assert t.pulls[0].log == "log01"

# filter_aotc_prog
def test_filter_aotc_prog_success(valid_config, valid_log_times):
    t = Transformer(valid_config)
    t.log_times = valid_log_times
    t.config["raid"] = {"final_boss": {"id": 666}}
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
    t.config["raid"] = {"final_boss": {"id": 666}}
    pulls = {
    "prog01": MockPull("log01"),
    "prog02": MockPull("log01"),
    "prog03": MockPull("log02")   }
    for pull in pulls.values():
        t.pulls.append(pull)

    t.filter_aotc_prog()

    assert len(t.pulls) == 3
    assert len(t.log_times) == 3

# transform_roster
@patch("etl.transform.parse_players")
@patch("etl.transform.load_cache")
def test_transform_roster_success(mock_load_cache, mock_parse_players, valid_config):
    mock_parse_players.return_value = {
        "log01": {
            10: [{"guid": 5003, "name": "Nightroud"}],
            20: [{"guid": 5005, "name": "Joefutofu"}]
        }
    }

    t = Transformer(valid_config)
    def mock_friend_spotted(log, sighting):
        guid = sighting.get("guid")
        if guid:
            mock_friend = MagicMock()
            mock_friend.sightings = 0
            t.friends[guid] = mock_friend
        return guid
    t.friend_spotted = MagicMock(side_effect=mock_friend_spotted)

    pull01 = MockPull("log01")
    pull01.roster = [10, 20]
    t.pulls = [pull01]
    t.transform_roster()

    assert t.friend_spotted.call_count == 2
    assert pull01.roster == [5003, 5005]

@patch("etl.transform.parse_players")
@patch("etl.transform.load_cache")
def test_transform_roster_missing_guid(mock_load_cache, mock_parse_players, valid_config):
    mock_parse_players.return_value = {
        "log01": {
            10: [{"guid": None}],
            20: [{"guid": 5005}]
        }
    }
    t = Transformer(valid_config)
    def mock_friend_spotted(log, sighting):
        guid = sighting.get("guid")
        if guid:
            mock_friend = MagicMock()
            mock_friend.sightings = 0
            t.friends[guid] = mock_friend
        return guid
    t.friend_spotted = MagicMock(side_effect=mock_friend_spotted)

    pull01 = MockPull("log01")
    pull01.roster = [10, 20]
    t.pulls = [pull01]
    t.transform_roster()

    assert t.friend_spotted.call_count == 2
    assert pull01.roster == [5005]

# friend_spotted
# ==============
@pytest.fixture
def valid_sighting():
    """ valid base sighting for tests """
    return {
        "guid": 5001,
        "name": "Upsetdruid",
        "server": "Area-52",
        "region": "US",
        "type": "Druid",
        "role": "healer",
        "specs": [{"spec": "Restoration", "count": 5}]
    }

def test_friend_spotted_invalid(valid_config, valid_log_times):
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    invalid_sightings = [{}, "invalid sighting", [], {"name": "Atpar", "type": "Paladin"}]
    for sighting in invalid_sightings:
        guid = t.friend_spotted("log01", sighting)
        assert guid is None
        assert len(t.pulls) == 0

def test_friend_spotted_new(valid_config, valid_sighting, valid_log_times):
    """ creates a new Friend with metadata and
        increments sightings
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    guid = t.friend_spotted("log01", valid_sighting)
    assert guid == 5001
    friend = t.friends[guid]
    assert friend.name == "Upsetdruid"
    assert friend.server == "Area-52"
    assert friend.region == "US"
    assert friend.type == "Druid"
    assert "Restoration" in friend.specs
    assert friend.specs["Restoration"] == {"role": "healer", "log_counts": {"log01": 5}}


def test_friend_spotted_same_spec(valid_config, valid_sighting, valid_log_times):
    """ duplicates are ignored, new log = new count 
        always increment sightings
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)

    guid = t.friend_spotted("log01", sighting)
    assert guid == 5001
    friend = t.friends[guid]
    assert friend.specs["Restoration"]["log_counts"]["log01"] == 5

    # same log different fight, just increment sightings
    t.friend_spotted("log01", sighting)
    assert friend.specs["Restoration"]["log_counts"]["log01"] == 5

    # same log different fight, different/missing count, ignore
    sighting["specs"] = [{"spec": "Restoration", "count": None}]
    t.friend_spotted("log01", sighting)
    assert friend.specs["Restoration"]["log_counts"]["log01"] == 5

    sighting["specs"] = [{"spec": "Restoration", "count": 8}]
    t.friend_spotted("log01", sighting)
    assert friend.specs["Restoration"]["log_counts"]["log01"] == 5

    # different log = new log_count
    t.friend_spotted("log02", sighting)
    assert friend.specs["Restoration"]["log_counts"]["log01"] == 5
    assert friend.specs["Restoration"]["log_counts"]["log02"] == 8

def test_friend_spotted_multi_spec(valid_config, valid_sighting, valid_log_times):
    """ new specs are added, """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)
    sighting["name"] = "Anonymoose"
    sighting["guid"] = 5002
    sighting["server"] = "Ursin"
    sighting["role"] = "tanks"
    sighting["specs"] = [{"spec": "Guardian", "count": 4}]

    guid = t.friend_spotted("log01", sighting)
    assert guid == 5002
    friend = t.friends[guid]
    assert friend.specs["Guardian"]["log_counts"]["log01"] == 4

    sighting["role"] = "dps"
    sighting["specs"] = [{"spec": "Feral", "count": 3}]
    t.friend_spotted("log01", sighting)
    assert friend.specs["Guardian"]["log_counts"]["log01"] == 4
    assert friend.specs["Feral"]["log_counts"]["log01"] == 3

    sighting["role"] = "healers"
    sighting["specs"] = [{"spec": "Restoration", "count": 6}]
    t.friend_spotted("log02", sighting)
    assert friend.specs["Guardian"]["log_counts"]["log01"] == 4
    assert friend.specs["Feral"]["log_counts"]["log01"] == 3
    assert friend.specs["Restoration"]["log_counts"]["log02"] == 6

def test_friend_spotted_missing(valid_config, valid_log_times, valid_sighting):
    """ missing/non-list specs value doesn't alter existing specs
        empty/non-dict spec values are skipped, valid values are processed normally
    """
    t = Transformer(valid_config)
    t.log_times = valid_log_times

    sighting = copy.deepcopy(valid_sighting)

    # missing spec field
    sighting.pop("specs")
    guid = t.friend_spotted("log01", sighting)
    assert guid == 5001
    friend = t.friends[guid]
    assert friend.specs == {}

    # specs not a list 
    not_lists = [None, "randomstring", 5, {}]
    for non_list in not_lists:
        sighting["specs"] = non_list
        t.friend_spotted("log01", sighting)
        assert friend.specs == {}

    # invalid specs
    one_spec = [{}, 4, "Restoration", [], {"spec": "Restoration", "count": 5}]
    sighting["specs"] = one_spec
    t.friend_spotted("log01", sighting)
    assert friend.specs == {"Restoration": {"role": "healer", "log_counts": {"log01": 5}}}

    # invalid log_counts
    # sighting["specs"] = [{ "Unholy": None }]
    # sighting["specs"] = [{ "Unholy": {} }]

    # invalid count
    # sighting["specs"] = [{ "Unholy": {"log01": None} }]
