import pytest
from unittest.mock import MagicMock
from etl.extract import Extractor
from services.file_io import CODES_CACHE, FIGHTS_CACHE, PLAYERS_CACHE

@pytest.fixture
def mock_client():
    """Fixture to mock the warcraftlogs API client"""
    client = MagicMock()
    client.query.return_value= {
        "data": {
            "reportData":{
                "reports": {"data": [{"code": "ReportCode00"}]}
    } } }
    return client

# chunk_list
# ==========
def test_chunk_list(mock_client, valid_config):
    """ Test: correctly slices lists 
        based on config chunk_size
    """
    valid_config.chunk_size = 3
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
    e.extract_players.assert_called_once()

# extract_codes tests
# ===================
def test_extract_codes_success(mock_client, valid_config, tmp_path):
    """ Test: queries the API with config variables, 
        calls save_codes correctly
    """
    valid_config.cache_root = tmp_path

    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()

    assert mock_client.query.called
    called_query = mock_client.query.call_args[0][0]
    assert str(valid_config.guild_id) in called_query
    assert str(valid_config.zone_id) in called_query
    assert valid_config.anchor_alt.name in called_query

    codes_cache_file =  valid_config.cache_path / f"{CODES_CACHE}.json"
    assert codes_cache_file.exists()

def test_extract_codes_cached(mock_client, valid_config, make_json_cache, mock_codes_cache):
    """ Test: if cache exists, return. 
        no query, no save.
    """
    make_json_cache(valid_config, mock_codes_cache, CODES_CACHE)   

    ex = Extractor(mock_client, valid_config)
    ex.extract_codes()

    assert not mock_client.query.called


# extract_fights tests
# ====================
def test_extract_fights_success(mock_client, valid_config, make_json_cache, mock_codes_cache):
    """ Test: saves correctly formatted response
        to query constructed with data from CODES_CACHE
    """
    make_json_cache(valid_config, mock_codes_cache, CODES_CACHE)

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    assert mock_client.query.called
    called_query = mock_client.query.call_args[0][0]
    checks = ["ch0_r0", "fights(difficulty: 4)", "code", "startTime", "zone"]
    for check in checks:
        assert check in called_query

    fights_cache_file = valid_config.cache_path / f"{FIGHTS_CACHE}.json"
    assert fights_cache_file.exists()


def test_extract_fights_cached(mock_client, valid_config, make_json_cache, mock_fights_cache):
    """ Test: no query if valid fights cache exists """
    make_json_cache(valid_config, mock_fights_cache, FIGHTS_CACHE)

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    assert not mock_client.query.called

def test_extract_fights_no_codes(mock_client, valid_config, tmp_path):
    """ Test: no fights cache but codes cache is empty/missing
        do nothing 
    """
    valid_config.cache_root = tmp_path

    e = Extractor(mock_client, valid_config)
    e.extract_fights()

    assert not mock_client.query.called


# extract players
# ===============
def test_extract_players_success(mock_client, valid_config, make_json_cache, mock_fights_cache):
    """ Test: load fights cache, 
        chunk data, query, 
        merge and cache responses
    """
    batches = {
        "first": {"data": {"reportData": {"alias_a": "valid data"} }},
        "second": {"data": {"reportData": {"alias_b": "valid data"} }},
        "merged": {"data": {"reportData": {"alias_a": "valid data", "alias_b": "valid data"} }}
    }
    make_json_cache(valid_config, mock_fights_cache, FIGHTS_CACHE)
    mock_client.query.side_effect = [batches["first"], batches["second"]]

    e = Extractor(mock_client, valid_config)
    e.chunk_size = 1
    e.extract_players()

    assert mock_client.query.call_count == 2

    players_cache_file = valid_config.cache_path / f"{PLAYERS_CACHE}.json"
    assert players_cache_file.exists()


def test_extract_players_cached(mock_client, valid_config, make_json_cache, mock_players_cache):
    """ Test: return if players cache exists """
    make_json_cache(valid_config, mock_players_cache, PLAYERS_CACHE)

    e = Extractor(mock_client, valid_config)
    e.extract_players()

    assert not mock_client.query.called

def test_extract_players_no_fights(mock_client, valid_config, tmp_path):
    """ Test: fights and players caches are empty, 
        check PLAYERS_CACHE, doesn't exist, continue.
        check FIGHTS_CACHE, doedn't exist, can't continue.
        do nothing 
    """
    valid_config.cache_root = tmp_path

    e = Extractor(mock_client, valid_config)
    e.extract_players()

    assert not mock_client.query.called

@pytest.mark.parametrize("bad_batch", [
        None, 
        { "data": None },
        { "data": { "reportData": None } },
        "502 Bad Gateway (HTML string)",
        502,
        [],
        {}
    ])
def test_extract_players_bad_batch(mock_client, valid_config, make_json_cache, mock_fights_cache, bad_batch):
    """ Test: malformed API response
        if the API response is invalid skip the batch
        cache merged valid responses normally
    """
    make_json_cache(valid_config, mock_fights_cache, FIGHTS_CACHE)

    good_batch = {"data": {"reportData": {"alias_b": "valid data"} }}
    players_cache_file = valid_config.cache_path / f"{PLAYERS_CACHE}.json"

    e = Extractor(mock_client, valid_config)
    e.chunk_size = 1

    mock_client.query.side_effect = [bad_batch, good_batch]
    e.extract_players()

    assert mock_client.query.call_count == 2
    assert players_cache_file.exists()


