from pathlib import Path
import json
from etl.constants import RAIDS

def load_config(path: str = "config.json")->dict: 
    """ Load user settings from config.json 
        verify required fields
        create derivitave fields 
            schedule datetime info
            raid = { "name": raid_name, "final_boss": {"id": id, "name": boss_name }}
            cache_path_r
    """   
    # verify path
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"missing config file: {config_path}")

    # load config.json
    with config_path.open('r', encoding='utf-8') as f:
        config = json.load(f)

    # "zone_id", "guild_id" and "anchor" {"name", "server", "region"}
    # required for current "clean sweep" code retrieval in extract_codes
    # ==================================================================
    config_fields = ["zone_id", "guild_id", "anchor"]
    anchor_fields = ["name", "server", "region"]
    # verify config fields exist
    for field in config_fields:
        if field not in config or not config[field]:
            raise ValueError(f"{field} must be defined in {config_path}")
    # verify valid anchor format
    anchor = config.get("anchor")
    if not isinstance(anchor, dict):
        raise ValueError("invalid anchor, should be dictionary")
    for field in anchor_fields:
        if field not in anchor or not anchor[field]:
            raise ValueError(f"missing anchor {field}")
        
    # verify valid guild_id?

    # verify valid zone_id
    zone_id = config["zone_id"]
    if zone_id not in RAIDS:
        raise ValueError("invalid zone_id, see zone:raid key in README")
    # add raid info to config
    config["raid"] = RAIDS[zone_id]
    

    # construct path for JSON cache
    guild_id = str(config['guild_id'])
    zone_id = str(config['zone_id'])
    config["cache_path_r"] = Path(".cache") / guild_id / zone_id
        
    return config

