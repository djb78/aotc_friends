import pytest
from unittest.mock import MagicMock, patch
from etl.extract import Extractor
from etl.constants import CODES_CACHE_NAME, FIGHTS_CACHE_NAME, PLAYERS_CACHE_NAME

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
    """ sample codes.json (good) """
    return {
        "data": {
            "reportData": {
                "reports": {"data": [{"code": "ReportCode01"}]}
    } } }

@pytest.fixture
def mock_fights_json():
    """ sample fights.json (good) """
    return {
        "data": {
            "reportData": {
                "ch0_r0": {
                    "code": "CODE1",
                    "fights": [{"id": 1}, {"id": 2}]
                },
                "ch0_r1": {
                    "code": "CODE2",
                    "fights": [{"id": 3}]
    } } } }

# extract_query

# chunk_list
# ==========
def test_chunk_list(mock_client, valid_config):
    """ Test: correctly slices lists 
        based on config chunk_size
    """
    valid_config["chunk_size"] = 3
    e = Extractor(mock_client, valid_config)

    data = [1, 2, 3, 4, 5, 6, 7]
    chunks = e.chunk_list(data)
    assert chunks == [[1, 2, 3], [4, 5, 6], [7]]

    assert e.chunk_list([]) == []
    assert e.chunk_list(None) == []
    

    



# extract_all test
# ================
def test_extract_all(mock_client, valid_config):
    e = Extractor(mock_client, valid_config)

    e.extract_codes = MagicMock()
    e.extract_fights = MagicMock()
    e.extract_players = MagicMock()

    e.extract_all()

    e.extract_codes.assert_called_once()
    e.extract_fights.assert_called_once()
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
    assert "ch0_r0" in called_query
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

# extract players
# ===============
@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_players_success(mock_load_cache, mock_save_cache, mock_client, valid_config, mock_fights_json):
    """ Test: load fights cache, 
        chunk data and query, 
        merge and cache responses
    """
    # mock API responses
    mock_response_1 = {
        "data": {
            "reportData": {
                "report0_0": {
                    "code": "CODE1",
                    "playerDetails": {"tanks": [], "healers": [], "dps": []}
    } } } }
    mock_response_2 = {
        "data": {
            "reportData": {
                "report1_0": {
                    "code": "CODE2",
                    "playerDetails": {"tanks": [], "healers": [], "dps": []}
    } } } }
    mock_response_merged = {
        "data": {
            "reportData": {
                "report0_0": {
                    "code": "CODE1",
                    "playerDetails": {"tanks": [], "healers": [], "dps": []}
                }, 
                "report1_0": {
                    "code": "CODE2",
                    "playerDetails": {"tanks": [], "healers": [], "dps": []}
    } } } }

    mock_load_cache.side_effect = [None, mock_fights_json]
    mock_client.query.side_effect = [mock_response_1, mock_response_2]

    e = Extractor(mock_client, valid_config)
    e.chunk_size = 1
    e.extract_players()

    assert mock_load_cache.call_count == 2
    assert mock_client.query.call_count == 2
    mock_save_cache.assert_called_once_with(valid_config, PLAYERS_CACHE_NAME, mock_response_merged)

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_players_cached(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: return if players cache exists """
    mock_load_cache.return_value = { "data": "cached" }

    e = Extractor(mock_client, valid_config)
    e.extract_players()

    mock_load_cache.assert_called_once_with(
        valid_config, 
        PLAYERS_CACHE_NAME
    )
    assert not mock_client.query.called
    assert not mock_save_cache.called

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_players_no_fights(mock_load_cache, mock_save_cache, mock_client, valid_config):
    """ Test: fights and players caches are empty, 
        check PLAYERS_CACHE_NAME, doesn't exist, continue.
        check FIGHTS_CACHE_NAME, doedn't exist, can't continue.
        do nothing 
    """
    mock_load_cache.side_effect = [None, {}]

    e = Extractor(mock_client, valid_config)
    e.extract_players()

    assert mock_load_cache.call_count == 2
    assert not mock_client.query.called
    assert not mock_save_cache.called

@patch("etl.extract.save_cache")
@patch("etl.extract.load_cache")
def test_extract_players_bad_batch(mock_load_cache, mock_save_cache, mock_client, valid_config, mock_fights_json):
    """ Test: malformed API response
        if the API response is invalid skip the batch
        cache merged valid responses normally
    """
    e = Extractor(mock_client, valid_config)
    e.chunk_size = 1

    good_batch = {
        "data": { "reportData": {
            "report1_0": {
                "code": "CODE2",
                "playerDetails": {"tanks": [], "healers": [], "dps": []}
    } } } }
    bad_batches = [
        None, 
        { "data": None },
        { "data": { "reportData": None } },
        "502 Bad Gateway (HTML string)",
        502,
        [],
        {}
    ]

    for bad_batch in bad_batches:
        mock_load_cache.side_effect = [None, mock_fights_json]
        mock_client.query.side_effect = [bad_batch, good_batch]
        e.extract_players()

        assert mock_client.query.call_count == 2
        mock_save_cache.assert_called_once_with(valid_config, PLAYERS_CACHE_NAME, good_batch)

        mock_client.reset_mock()
        mock_save_cache.reset_mock()
