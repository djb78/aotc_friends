import json
import pytest
import copy
from services.file_io import load_config, save_cache, load_cache

def test_load_config_success(tmp_path, valid_config):
        # temporary config file
        config_data = valid_config
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

# verify config variables
# define test cases: (keys_to_delete, keys_to_make_empty, expected_error_message)
@pytest.mark.parametrize(
     "to_delete, to_empty, expected_error",
     [
         # --- Test Missing Keys ---
         (["zone_id"], [], "zone_id must be defined"),
         (["guild_id"], [], "guild_id must be defined"),
         (["anchor"], [], "anchor must be defined"),
         ([], ["anchor.name"], "missing anchor name"),
         ([], ["anchor.server"], "missing anchor server"),
         ([], ["anchor.region"], "missing anchor region"),
         
         # --- Test Empty Keys ---
         ([], ["zone_id"], "zone_id must be defined"),
         ([], ["guild_id"], "guild_id must be defined"),
         ([], ["anchor"], "anchor must be defined"),
         ([], ["anchor.name"], "missing anchor name"),
         ([], ["anchor.server"], "missing anchor server"),
         ([], ["anchor.region"], "missing anchor region")
     ]
)
def test_load_config_validation_errors(tmp_path, valid_config, to_delete, to_empty, expected_error):
    config_data = copy.deepcopy(valid_config)
     
    # test missing keys
    for key in to_delete:
        config_data.pop(key, None)
         
    # test empty keys
    for key in to_empty:
        if "." in key:  # Nested key (anchor)
            parent, child = key.split(".")
            if config_data.get(parent):
                config_data[parent][child] = ""
        else:
            config_data[key] = ""

    # Write bad config to temp file
    config_file = tmp_path / "config.json"
    with config_file.open("w", encoding="utf-8") as f:
        json.dump(config_data, f)

    # Assert load_config raises ValueError with expected message
    with pytest.raises(ValueError, match=expected_error):
        load_config(path=str(config_file))


# cache
def test_save_load_cache(tmp_path, valid_config):
    config = valid_config.copy()
    config['cache_path_r'] = tmp_path / "cache"

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

def test_load_cache_corrupted(tmp_path):
    config = { 'cache_path_r': tmp_path / "cache" }
    config["cache_path_r"].mkdir(parents=True, exist_ok=True)

    corrupted_file = config["cache_path_r"] / "bad_cache.json"
    with corrupted_file.open("w", encoding="utf-8") as f:
        f.write("{ invalid json: 123 }")

    assert load_cache(config, "bad_cache") == {}