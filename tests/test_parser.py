import pytest
from etl.parser import _safe_get, parse_unique_codes

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