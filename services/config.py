from pathlib import Path
import json

def load_config(path: str = "config.json")->dict:    
    # verify path
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"missing config file: {config_path}")

    # load config.json
    config = {}
    with config_path.open('r', encoding='utf-8') as f:
        config = json.load(f)

    # verify config variables
    required_config_keys = ["zone_id", "guild_id", "anchor"]
    for key in required_config_keys:
        if key not in config or not config[key]:
            raise ValueError(f"{key} must be defined in {config_path}")
        
    if not isinstance(config["anchor"], dict):
        raise ValueError("anchor configuration must be a dictionary")
    
    required_anchor_keys = ["name", "server", "region"]
    for key in required_anchor_keys:
        if key not in config["anchor"] or not config["anchor"][key]:
            raise ValueError(f"missing anchor {key}")

    # construct path for JSON cache
    guild_id = str(config['guild_id'])
    zone_id = str(config['zone_id'])
    config["cache_path_r"] = Path(".cache") / guild_id / zone_id
        
    return config

