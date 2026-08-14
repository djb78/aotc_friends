import pytest
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

    t.transform_all()

    t.transform_fights_pulls.assert_called_once()
    t.filter_aotc_prog.assert_called_once()


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
            "fights": [
                { "id": 1, 
                  "kill": False, 
                  "encounterID": 101, 
                  "name": "Eranog", 
                  "friendlyPlayers": [5001, 5002] },
                { "id": 2,
                  "kill": True,
                  "encounterID": 101,
                  "name": "Eranog",
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
            "fights": [
                { "id": 1, 
                  "kill": False, 
                  "encounterID": 101, 
                  "name": "Eranog", 
                  "friendlyPlayers": [5001, 5002] }
            ] },
        "log02": {
            "time": 2000000,
            "fights": [
                { "id": 2,
                  "kill": True,
                  "encounterID": 101,
                  "name": "Eranog",
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

