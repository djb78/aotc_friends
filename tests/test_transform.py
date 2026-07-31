from unittest.mock import patch
import pytest
from etl.constants import CODES_CACHE_NAME
from etl.transform import Transformer
from etl.models import Report

@pytest.fixture
def mock_codes_json():
    """sample JSON response"""
    return {
        "data": {
            "reportData": {
                "reports": {
                    "data": [{"code": "GuildRprt"}]
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

    mock_load_cache.assert_called_once_with(valid_config, CODES_CACHE_NAME)
    assert len(t.reports) == 1
    assert isinstance(t.reports["GuildRprt"], Report)
    assert t.reports["GuildRprt"].code == "GuildRprt"