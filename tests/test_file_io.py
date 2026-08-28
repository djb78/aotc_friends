import json, pytest
from services.file_io import load_config, save_cache, load_cache, save_output
from domain.schema import AppConfig


# load_config
# ==========================================
def test_load_config_success(tmp_path, user_config):
        """ test: reads a json file and returns AppConfig """
        config_file = tmp_path / "config.json"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(user_config, f)

        # Run the function
        config = load_config(path=str(config_file))

        assert isinstance(config, AppConfig)
        assert config.guild_id == user_config["guild_id"]
        assert config.zone_id == user_config["zone_id"]

def test_load_config_missing_file():
     with pytest.raises(FileNotFoundError):
         load_config("missing.json")

# cache
# ==========================================
def test_save_load_cache(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path

    cache_name = "test_reports"
    test_data = {"reports": [{'code': "ABC123XYZ"}]}

    save_cache(config, cache_name, test_data)

    expected_file = config.cache_path / f"{cache_name}.json"
    assert expected_file.exists()

    loaded_data = load_cache(config, cache_name)
    assert loaded_data == test_data

def test_load_cache_missing(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path
    assert load_cache(config, "not_here") == {}

def test_load_cache_corrupted(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path
    config.cache_path.mkdir(parents=True, exist_ok=True)

    corrupted_file = config.cache_path / "bad_cache.json"
    with corrupted_file.open("w", encoding="utf-8") as f:
        f.write("{ invalid json: 123 }")

    with pytest.raises(json.JSONDecodeError):
        load_cache(config, "bad_cache")

# output
# ==========================================
def test_save_output(tmp_path):
    """ writes markdown file to disk """
    test_file = tmp_path / "test_friends.md"

    save_output("# Test Report", path=str(test_file))

    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "# Test Report"