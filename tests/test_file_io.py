import json
import pytest
from services.file_io import load_config, save_cache, load_cache

def test_load_config_success(tmp_path):
        # temporary config file
        config_data = {
            "guild_id": 123456,
            "zone_id": 35
        }
        config_file = tmp_path / "config.json"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Run the function
        config = load_config(path=str(config_file))

        # Assertions
        assert config["guild_id"] == 123456
        assert config["zone_id"] == 35


def test_load_config_missing_file():
     with pytest.raises(FileNotFoundError):
         load_config("missing.json")

def test_save_load_cache(tmp_path):
    config = {
        'guild_id': 123456,
        'zone_id': 35,
        "cache_path_r": tmp_path / "cache"
    }

    cache_name = "test_reports"
    test_data = {"reports": [{'code': "ABC123XYZ"}]}

    save_cache(config, cache_name, test_data)

    expected_file = tmp_path / "cache" / "test_reports.json"
    assert expected_file.exists()

    loaded_data = load_cache(config, cache_name)
    assert loaded_data == test_data

def test_load_cache_missing(tmp_path):
     config = { 'cache_path_r': tmp_path / "cache" }
     assert load_cache(config, "not_here") == {}