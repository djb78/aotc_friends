from unittest.mock import patch
import pytest
from etl.constants import CACHE_NAME_CODES
from etl.transform import Transformer
from etl.models import Report

@pytest.fixture
def mock_codes_json():
    """sample JSON response, duplicate codes in all sources"""
    return {
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

@patch("etl.transform.load_cache")
def test_transform_codes_reports_success(mock_load_cache, mock_codes_json, valid_config):
    """Test: extract and de-duplicate codes, instantiate Report objects"""
    mock_load_cache.return_value = mock_codes_json
    t = Transformer(valid_config)
    t.transform_codes_reports()

    mock_load_cache.assert_called_once_with(valid_config, CACHE_NAME_CODES)
    assert len(t.reports) == 4
    assert all(isinstance(r, Report) for r in t.reports.values())

    expected_codes = ["GuildRprt", "RecentRpt", "duplicate", "r_missing"]

    assert list(t.reports.keys()) == expected_codes

@patch("etl.transform.load_cache")
def test_transform_codes_reports_defensive_parsing(mock_load_cache, valid_config):
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
    mock_load_cache.return_value = incomplete_data

    t = Transformer(valid_config)
    t.transform_codes_reports()

    assert len(t.reports) == 1
    assert "r_missing" in t.reports