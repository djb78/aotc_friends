import json
import pytest
from services.file_io import load_config

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