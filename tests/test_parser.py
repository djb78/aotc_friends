import pytest
from etl.parser import safe_get, parse_unique_codes, parse_fight_ids, parse_fights, parse_players

@pytest.fixture
def mock_fights_json():
    """ sample fights_json 
        multiple, single and empty report variations
    """
    return {
        "data": {
            "reportData": {
                "ch0_r0": {
                    "code": "multiple",
                    "fights": [
                        {"id": 1, "name": "Gnarlroot", "kill": True, "friendlyPlayers": [1, 2, 3]},
                        {"id": 2, "name": "Igira", "kill": False, "friendlyPlayers": [1, 3, 4, 2]}
                    ]
                },
                "ch0_r1": {
                    "code": "single",
                    "fights": [
                        {"id": 10, "name": "Smolderon", "kill": True, "friendlyPlayers": [2, 4, 1, 3]}
                    ]
                },
                "ch0_r2": {
                    "code": "missing",
                    "fights": []
    } } } }

@pytest.fixture
def mock_players_json():
    """ sample players_json
        solo, group with role-swapping, private log variants
    """
    return { "data": { "reportData": {
                "ch0_r0": {
                    "code": "flex_role",
                    "playerDetails": {
                        "tanks": [
                            {"id": 1, "name": "tank", "specs": ["tank_spec"]},
                            {"id": 4, "name": "flex", "specs": ["tank_spec"]} ], 
                        "healers": [
                            {"id": 2, "name": "healer", "specs": ["healer_spec"]} ],
                        "dps": [ 
                            {"id": 4, "name": "flex", "specs": ["dps_spec"]} ]
                    }
                },
                "ch0_r1": {
                    "code": "solo",
                    "playerDetails": {
                        "tanks": [ {"id": 1, "name": "tank", "specs": ["tank_spec"]} ]
                    } 
                },
                "ch0_r2": {
                    "code": "private",
                    "playerDetails": None
                } 
    } } }

def test_safe_get():
    """ Test: recursive dictionary navigation and safe defaults """
    data = {"a": {"b": {"c": 43}}}
    assert safe_get(data, ["a", "b", "c"]) == 43
    assert safe_get(data, ["a", "x", "c"]) is None
    assert safe_get(data, ["a", "b", "c", "d"]) is None

def test_parse_unique_codes_success():
    """ Test: parse unique codes from guild, recent and ranking data """
    duplicate_data = {
        "data": {
            "reportData": {
                "reports": {
                    "data": [
                        {"code": "GuildRprt"},
                        {"code": "duplicate"}
                    ]
                }
            },
            "characterData": {
                "character": {
                    "recentReports": {
                        "data": [
                            {"code": "RecentRpt"},
                            {"code": "duplicate"}
                        ]
                    },
                    "zoneRankings": {
                        "rankings": [
                            {"report": {"code": "r_missing"}},
                            {"report": {"code": "duplicate"}}
                        ]
                    } } } } }
    codes = parse_unique_codes(duplicate_data)
    assert codes == ["GuildRprt", "RecentRpt", "duplicate", "r_missing"]

def test_parse_unique_codes_defensive():
    """ Test: skip missing/malformed structures """
    incomplete_data = {
        "data": {
            "reportData": None, # reports missing
            "characterData": {
                "character": {
                    # recent reports missing
                    "zoneRankings": {
                        "rankings": [
                            {"report": None},
                            {"report": {"code": "r_missing"}}
                        ]
                    } } } } } 
    codes = parse_unique_codes(incomplete_data)
    assert codes == ["r_missing"]

def test_parse_unique_codes_empty():
    """ Test: empty/None inputs return an empty list """
    assert parse_unique_codes({}) == []
    assert parse_unique_codes(None) == []


# parse_fight_ids
# ===============
def test_parse_fight_ids_success(mock_fights_json):
    """ Test: legacy wrapper returns dictionary of fight id lists 
        {code:[fightIDs]} 
    """
    fight_ids = parse_fight_ids(mock_fights_json)

    assert fight_ids == {
        "multiple": [1, 2],
        "single": [10]
    }

def test_parse_fight_ids_empty():
    """ Test: empty dict returned in response to empty input """
    empties = [{}, None, []]
    for empty in empties:
        fight_ids = parse_fight_ids(empty)
        assert fight_ids == {}

# parse_fights
# ============
def test_parse_fights_success(mock_fights_json):
    """ Test: successfully parse fights data from mock_fights_json """

    reports = parse_fights(mock_fights_json)

    assert "multiple" in reports
    assert "single" in reports
    assert "missing" not in reports

    assert reports["multiple"] == {
        "fights": [
            {"id": 1, "name": "Gnarlroot", "kill": True, "friendlyPlayers": [ 1, 2, 3 ] },
            {"id": 2, "name": "Igira", "kill": False, "friendlyPlayers": [1, 3, 4, 2] }
        ]
    }
    assert reports["single"] == {
        "fights": [
            {"id": 10, "name": "Smolderon", "kill": True, "friendlyPlayers": [2, 4, 1, 3]}
        ]
    }

def test_parse_fights_defensive():
    """ Test: skip missing/malformed fights_json elements """
    missing_samples = [
        None,
        {},
        {"data": None},
        {"data": { "reportData": {"ch0_r0": {"code": "no_fights"}}}},
        {"data": { "reportData": {"ch0_r0": "no_dict"}}}
    ]

    for sample in missing_samples:
        clean_dict = parse_fights(sample)
        assert isinstance(clean_dict, dict)
        assert len(clean_dict) == 0


# parse_players 
# ==============================================
def test_parse_players_success(mock_players_json):
    """ Test: parse playerDetails, verify role injection, exclude private/missing logs

        expected format from parse_players:
            { "code": [ player_role_info, ... ], "code": [ ... ], ... }
    """
    player_reports = parse_players(mock_players_json)

    assert "flex_role" in player_reports
    assert "solo" in player_reports
    assert "private" not in player_reports

    assert player_reports["flex_role"] == [
        {"id": 1, "name": "tank", "specs": ["tank_spec"], "role": "tanks"},
        {"id": 4, "name": "flex", "specs": ["tank_spec"], "role": "tanks"},
        {"id": 2, "name": "healer", "specs": ["healer_spec"], "role": "healers"},
        {"id": 4, "name": "flex", "specs": ["dps_spec"], "role": "dps"}
    ]
    assert player_reports["solo"] == [
        {"id": 1, "name": "tank", "specs": ["tank_spec"], "role": "tanks"}
    ]

def test_parse_players_defensive():
    """ Test: handle missing/malformed players_json """
    missing_samples = [
        None,
        {},
        {"data": None},
        {"data": {"reportData": {"ch0_r0": {"code": "no_details"}}}},
        {"data": {"reportData": {"ch0_r0": {"code": "bad_details", "playerDetails": "no_dict"}}}}
    ]

    for sample in missing_samples:
        clean_dict = parse_players(sample)
        assert isinstance(clean_dict, dict)
        assert len(clean_dict) == 0
