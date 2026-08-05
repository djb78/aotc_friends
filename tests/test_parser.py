import pytest
from etl.parser import safe_get, parse_unique_codes, parse_fight_ids, parse_fights

@pytest.fixture
def mock_fights_json():
    """ sample fights query response """
    return {
        "data": {
            "reportData": {
                "report1": {
                    "code": "multiple",
                    "fights": [
                        {"id": 1, "name": "Gnarlroot", "kill": True, "friendlyPlayers": [1, 2, 3]},
                        {"id": 2, "name": "Igira", "kill": False, "friendlyPlayers": [1, 3, 4, 2]}
                    ]
                },
                "report2": {
                    "code": "single",
                    "fights": [
                        {"id": 10, "name": "Smolderon", "kill": True, "friendlyPlayers": [2, 4, 1, 3]}
                    ]
                },
                "report0": {
                    "code": "missing",
                    "fights": []
                }
            }
        }
    }

def test_safe_get():
    data = {"a": {"b": {"c": 43}}}
    assert safe_get(data, ["a", "b", "c"]) == 43
    assert safe_get(data, ["a", "x", "c"]) is None
    assert safe_get(data, ["a", "b", "c", "d"]) is None

def test_parse_unique_codes_success():
    """parse sample JSON response, remove duplicate codes (all sources)"""
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
                    }
                }
            }
        }
    }
    codes = parse_unique_codes(duplicate_data)
    assert codes == ["GuildRprt", "RecentRpt", "duplicate", "r_missing"]

def test_parse_unique_codes_defensive():
    """Test: no crash on missing/malformed JSON structure"""
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
                    }
                }
            }
        }
    } 
    codes = parse_unique_codes(incomplete_data)
    assert codes == ["r_missing"]

def test_parse_unique_codes_empty():
    assert parse_unique_codes({}) == []
    assert parse_unique_codes(None) == []


# parse_fight_ids
# ===============
def test_parse_fight_ids_success(mock_fights_json):
    """ the correct dictionary is returned in response to json input """
    fight_ids = parse_fight_ids(mock_fights_json)

    assert "multiple" in fight_ids
    assert "single" in fight_ids
    assert "missing" not in fight_ids

    assert 1 in fight_ids["multiple"]
    assert 2 in fight_ids["multiple"]
    assert 10 in fight_ids["single"]

def test_parse_fight_ids_empty():
    """ an empty dict is returned in response to an empty input """
    empties = [{}, None, []]
    for empty in empties:
        fight_ids = parse_fight_ids(empty)
        assert fight_ids == {}

# parse_fights
# ============
def test_parse_fights_success(mock_fights_json):
    """ Test: successfully parse fights data from mock_fights_json 
    
        expected format from parse_fights(mock_fights_json):
            { "multiple": [ { "id": 1, ... }, { "id": 2, ... } ], 
                "single": [ { "id": 10, ... } ] }
    """
    sample_fights = {
        1: {"id": 1, "name": "Gnarlroot", "kill": True, "friendlyPlayers": [ 1, 2, 3 ] },
        2: {"id": 2, "name": "Igira", "kill": False, "friendlyPlayers": [1, 3, 4, 2] },
        10: {"id": 10, "name": "Smolderon", "kill": True, "friendlyPlayers": [2, 4, 1, 3]}
    }
    sample_fields = ["id", "name", "kill", "friendlyPlayers"]

    reports = parse_fights(mock_fights_json)

    assert "multiple" in reports
    assert len(reports["multiple"]) == 2
    assert "single" in reports
    assert len(reports["single"]) == 1
    assert "missing" not in reports

    for report in reports.values():
        for fight in report:
            assert fight["id"] in sample_fights
            sample_fight = sample_fights[fight["id"]]
            for field in sample_fields:
                assert fight[field] == sample_fight[field]

def test_parse_fights_defensive():
    """ Test: skip missing/malformed codes/fights/reports
    """
    missing_samples = [
        None,
        {},
        {"data": None},
        {"data": { "reportData": {"report0": {"code": "no_fights"}}}},
        {"data": { "reportData": {"report0": "no_dict"}}}
    ]

    for sample in missing_samples:
        clean_dict = parse_fights(sample)
        assert isinstance(clean_dict, dict)
        assert len(clean_dict) == 0


