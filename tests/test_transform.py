import pytest
from unittest.mock import MagicMock, patch
from etl.transform import Transformer



def test_transform_all(valid_config):
    t = Transformer(valid_config)

    t.transform_fights_pulls = MagicMock()

    t.transform_all()

    t.transform_fights_pulls.assert_called_once()


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
