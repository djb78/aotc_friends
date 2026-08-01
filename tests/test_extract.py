import pytest
from unittest.mock import MagicMock, patch
from etl.extract import Extractor
from etl.constants import CODES_CACHE_NAME, FIGHTS_CACHE_NAME

@pytest.fixture
def mock_client():
    """Fixture to mock the warcraftlogs API client"""
    client = MagicMock()
    client.query.return_value= {
        "data": {
            "reportData":{
                "reports": {"data": [{"code": "ReportCode00"}]}
            }
        }
    }
    return client

@pytest.fixture
def mock_codes_json():
    """sample codes.json with one report code"""
    return {
        "data": {
            "reportData": {
                "reports": {"data": [{"code": "ReportCode01"}]}
            }
        }
    }

# extract_all test
# ================
def test_extract_all(mock_client, valid_config):
    e = Extractor(mock_client, valid_config)

    e.extract_codes = MagicMock()
    e.extract_fights = MagicMock()

    e.extract_all()

    e.extract_codes.assert_called_once()
    e.extract_fights.assert_called_once()


# extract_codes tests
# ===================
@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_codes_success(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: queries the API with config variables, 
        calls save_cache correctly
    """
    mock_load_cache.return_value = None
    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()
    mock_load_cache.assert_called_once_with(
        valid_config, 
        CODES_CACHE_NAME
    )
    assert mock_client.query.called

    called_query = mock_client.query.call_args[0][0]
    assert str(valid_config['guild_id']) in called_query
    assert str(valid_config['zone_id']) in called_query
    assert valid_config["anchor"]["name"] in called_query

    mock_save_cache.assert_called_once_with(
        valid_config,
        CODES_CACHE_NAME,
        mock_client.query.return_value
    )

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_codes_cached(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: if cache exists, return. 
        no query, no save.
    """
    mock_load_cache.return_value = {'data': "cached"}
    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()

    mock_load_cache.assert_called_once_with(
        valid_config,
        CODES_CACHE_NAME
    )

    assert not mock_client.query.called
    assert not mock_save_cache.called

# extract_fights tests
# ====================
@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_fights_success(mock_load_cache, mock_save_cache, mock_client, valid_config, mock_codes_json):
    """Test: load json from CODES_CACHE_NAME,
    parse codes from json, 
    query WSL with aliased fights queries for each code, 
    save response to FIGHTS_CACHE_NAME"""
    mock_load_cache.side_effect = [None, mock_codes_json]

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    assert mock_load_cache.call_count == 2
    mock_load_cache.assert_any_call(valid_config, FIGHTS_CACHE_NAME)
    mock_load_cache.assert_any_call(valid_config, CODES_CACHE_NAME)

    assert mock_client.query.called
    called_query = mock_client.query.call_args[0][0]
    assert "report0" in called_query
    assert "fights(difficulty: 4)" in called_query

    mock_save_cache.assert_called_once_with(
        valid_config,
        FIGHTS_CACHE_NAME,
        mock_client.query.return_value
    )

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_fights_cached(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: return if fights cache exists """
    mock_load_cache.return_value = { "data": "cached" }

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    mock_load_cache.assert_called_once_with(
        valid_config, 
        FIGHTS_CACHE_NAME
    )
    assert not mock_client.query.called
    assert not mock_save_cache.called

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_fights_no_codes(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: codes and fights caches are empty, 
        check FIGHTS_CACHE_NAME, doesn't exist, continue.
        check CODES_CACHE_NAME, doedn't exist, can't continue.
        do nothing 
    """
    mock_load_cache.side_effect = [None, {}]

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    assert mock_load_cache.call_count == 2
    assert not mock_client.query.called
    assert not mock_save_cache.called