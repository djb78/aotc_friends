import json
import pytest
import copy
from services.config import load_config
from pathlib import Path
from etl.constants import RAIDS

def test_load_config_success(tmp_path, valid_config):
        """ test: verify the config file exists and
            contains the fields required for core functionality
        """
        # temporary config file
        config_data = valid_config
        config_file = tmp_path / "config.json"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Run the function
        config = load_config(path=str(config_file))

        # required fields
        assert config["guild_id"] == 123456
        assert config["zone_id"] == 35
        assert config["anchor"] == { "name": "Stiff", "server": "Area-52", "region": "US" }
        # derived fields
        assert config["raid"] == RAIDS[config["zone_id"]]
        assert config["cache_path_r"] == Path(".cache") / "123456" / "35"


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