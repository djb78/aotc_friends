import pytest
from etl.parse import safe_get, parse_unique_codes, parse_fight_ids, parse_fights, parse_players

def test_safe_get():
    """ Test: recursive dictionary navigation and safe defaults """
    data = {"a": {"b": {"c": 43}}}
    assert safe_get(data, ["a", "b", "c"]) == 43
    assert safe_get(data, ["a", "x", "c"]) is None
    assert safe_get(data, ["a", "b", "c", "d"]) is None

# codes
# ==============================================

# parse_unique_codes
# ==================
def test_parse_unique_codes_success(mock_codes_cache):
    """ Test: parse unique codes from guild, recent and ranking data """
    codes = parse_unique_codes(mock_codes_cache)
    # don't duplicate "code_1"
    assert codes == ["code_0", "code_1", "code_2", "code_3"]

def test_parse_unique_codes_defensive(mock_codes_cache):
    """ Test: skip missing/malformed structures """
    mock_codes_cache["data"]["reportData"] = None
    recent = mock_codes_cache["data"]["characterData"]["character"]["recentReports"]
    recent["data"][2]["code"] = None

    codes = parse_unique_codes(mock_codes_cache)
    assert codes == ["code_1", "code_2"]

def test_parse_unique_codes_empty():
    """ Test: empty/None inputs return an empty list """
    assert parse_unique_codes({}) == []
    assert parse_unique_codes(None) == []

# fights
# ==============================================

# parse_fight_ids
# ===============
def test_parse_fight_ids_success(mock_fights_cache):
    """ Test: legacy wrapper returns dictionary of fight id lists 
        {code:[fightIDs]} 
    """
    fight_ids = parse_fight_ids(mock_fights_cache)

    assert fight_ids == {
        "code_1": [1, 2],
        "code_2": [1]
    }

def test_parse_fight_ids_empty():
    """ Test: empty dict returned in response to empty input """
    empties = [{}, None, []]
    for empty in empties:
        fight_ids = parse_fight_ids(empty)
        assert fight_ids == {}

# parse_fights
# ============
def test_parse_fights_success(mock_fights_cache):
    """ Test: successfully parse fights data from mock_fights_cache """

    reports = parse_fights(mock_fights_cache)

    assert "code_0" not in reports
    assert "code_1" in reports
    assert "code_2" in reports

    # verify output dictonary structure
    assert reports["code_1"] == { 
        "time": 100,
        "zone_id": 46,
        "fights": [
            {"id": 1, "name": "Boss_100", "kill": False, "friendlyPlayers": [1, 2, 3], "encounterID": 100, "difficulty": 4 },
            {"id": 2, "name": "Boss_100", "kill": True, "friendlyPlayers": [1, 2, 3], "encounterID": 100, "difficulty": 4 }
        ]
    }
    assert reports["code_2"] == {
        "time": 200,
        "zone_id": 46,
        "fights": [
            {"id": 1, "name": "Boss_200", "kill": False, "friendlyPlayers": [40, 20], "encounterID": 200, "difficulty": 4}
        ]
    }

def test_parse_fights_defensive(mock_fights_cache):
    """ Test: skip missing/malformed fights_json elements """
    missing_parents = [ # indicators of missing or corrupted input
        None,                           # nothing
        {},                             # no data
        {"data": None},                 # no reportData
        {"data": { "reportData": {} }}  # no reports
    ]

    bad_reports = [
        # {"code": "112", "fights": [{}]},  # currently adds to fight_logs
        {"code": "112", "fights": []},
        {"code": "112", "fights": "not_list"},
        {"code": None},
        {"not_code": "some_value"},
        {},
        None
    ]
    # mixed good and bad reports, only output good
    goodrpt = mock_fights_cache["data"]["reportData"]["alias_b"]
    fights_json = {"data": { "reportData": {
        "goodrpt": goodrpt, 
    }}}
    for badrpt in bad_reports:
        fights_json["data"]["reportData"]["badrpt"] = badrpt
        clean_dict = parse_fights(fights_json)
        assert isinstance(clean_dict, dict)
        assert len(clean_dict) == 1

# players
# ==============================================

# parse_players
# =============
def test_parse_players_success(mock_players_cache):
    """ Test: parse playerDetails, verify role injection, exclude private/missing logs

        expected format from parse_players:
            { "code": { "id": [ player_role_info, ... ], "id": [ ... ], ... }
    """
    player_reports = parse_players(mock_players_cache)

    assert "code_1" in player_reports
    assert "code_2" in player_reports
    assert "private" not in player_reports

    assert 1 in player_reports["code_1"]
    assert 2 in player_reports["code_1"]
    assert 3 in player_reports["code_1"]

    assert 20 in player_reports["code_2"]
    assert 40 in player_reports["code_2"]

    # cross log/report
    assert player_reports["code_1"][2][0]["guid"] == player_reports["code_2"][20][0]["guid"]
    # multi spec
    assert player_reports["code_1"][2][0]["specs"] == [
        {"spec": "dps_spec_1", "count": 1}, 
        {"spec": "dps_spec_2", "count": 1}
    ]
    # multi role
    assert len(player_reports["code_1"][1]) == 2
    assert player_reports["code_1"][1][0]["role"] == "healers"
    assert player_reports["code_1"][1][1]["role"] == "dps"

