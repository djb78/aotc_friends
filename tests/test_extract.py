import pytest
from unittest.mock import MagicMock, patch
from etl.extract import Extractor

@pytest.fixture
def mock_client():
    """Fixture to mock the warcraftlogs API client"""
    client = MagicMock()
    client.query.return_value= {
        "data": {
            "reportData":{
                "reports": {"data": [{"code": "GuildReport123"}]}
            }
        }
    }
    return client

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_codes_success(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """Test: queries the API with config variables, calls save_cache correctly"""
    mock_load_cache.return_value = None
    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()
    mock_load_cache.assert_called_once_with(
        valid_config, 
        Extractor.CACHE_NAME_CODES
    )
    assert mock_client.query.called

    called_query = mock_client.query.call_args[0][0]
    assert str(valid_config['guild_id']) in called_query
    assert str(valid_config['zone_id']) in called_query
    assert valid_config["anchor"]["name"] in called_query

    mock_save_cache.assert_called_once_with(
        valid_config,
        Extractor.CACHE_NAME_CODES,
        mock_client.query.return_value
    )

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_codes_cached(mock_load_cache, mock_save_cache, mock_client, valid_config):
    mock_load_cache.return_value = {'data': "cached"}
    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()

    mock_load_cache.assert_called_once_with(
        valid_config,
        Extractor.CACHE_NAME_CODES
    )

    assert not mock_client.query.called