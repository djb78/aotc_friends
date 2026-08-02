import pytest
from etl.parser import _safe_get, parse_unique_codes, parse_fight_ids

@pytest.fixture
def mock_fights_json():
    """ sample fights query response """
    return {
        "data": {
            "reportData": {
                "report1": {
                    "code": "code1",
                    "fights": [
                        {"id": 1, "name": "Gnarlroot", "kill": True},
                        {"id": 2, "name": "Igira", "kill": False}
                    ]
                },
                "report2": {
                    "code": "code2",
                    "fights": [
                        {"id": 10, "name": "Smolderon", "kill": True}
                    ]
                },
                "report0": {
                    "code": "EMPTY",
                    "fights": []
                }
            }
        }
    }

def test_safe_get():
    data = {"a": {"b": {"c": 43}}}
    assert _safe_get(data, ["a", "b", "c"]) == 43
    assert _safe_get(data, ["a", "x", "c"]) is None
    assert _safe_get(data, ["a", "b", "c", "d"]) is None

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

    assert "code1" in fight_ids
    assert "code2" in fight_ids
    assert "EMPTY" not in fight_ids

    assert 1 in fight_ids["code1"]
    assert 2 in fight_ids["code1"]
    assert 10 in fight_ids["code2"]

def test_parse_fight_ids_empty():
    """ an empty dict is returned in response to an empty input """
    empties = [{}, None, []]
    for empty in empties:
        fight_ids = parse_fight_ids(empty)
        assert fight_ids == {}

