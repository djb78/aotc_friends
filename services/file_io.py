import json, logging
from pathlib import Path
from domain.schema import AppConfig

# JSON cache filenames
CODES_CACHE = "codes"
FIGHTS_CACHE = "fights"
PLAYERS_CACHE = "players"

logger = logging.getLogger(__name__)

# CONFIG
# =======================================
# load_config
def load_config(path: str = "config.json")->AppConfig:
    """ Load user settings from config.json """   
    # verify path
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"missing config file: {config_path}")

    # load config.json
    with config_path.open('r', encoding='utf-8') as f:
        config = json.load(f)

    return AppConfig.model_validate(config)

# OUTPUT
# =======================================
# save_output
def save_output(md: str, path="friends.md"):
    """ write a string to a file """
    if not md or not isinstance(md, str):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("  saved to %s", path)

# CACHE
# =======================================
# save_cache
def save_cache(config: AppConfig, cache_name: str, api_response: dict):
    """attempts to write api_response to cache_name"""
    cache_file = config.cache_path / f"{cache_name}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(api_response, f, indent=4)
    logger.info("  saved to %s", cache_file)

# save wrappers
def save_fights(config: AppConfig, api_response: dict):
    """attempts to save api_response to FIGHTS_CACHE"""
    return save_cache(config, FIGHTS_CACHE, api_response)

def save_codes(config: AppConfig, api_response: dict):
    """attempts to save api_response to CODES_CACHE"""
    return save_cache(config, CODES_CACHE, api_response)

def save_players(config: AppConfig, api_response: dict):
    """attempts to save api_response to PLAYERS_CACHE"""
    return save_cache(config, PLAYERS_CACHE, api_response)


# load_cache
def load_cache(config: AppConfig, cache_name: str)->dict:
    """ attempts to load cache_name, {} for no cache
        let main handle exceptions
    """
    cache_file = config.cache_path / f"{cache_name}.json"
    if not cache_file.exists():
        return {}

    with cache_file.open("r", encoding="utf-8") as f:
        cache = json.load(f)

    return cache

# load wrappers
def load_fights(config: AppConfig)->dict:
    """attempts to load FIGHTS_CACHE"""
    return load_cache(config, FIGHTS_CACHE)

def load_codes(config: AppConfig)->dict:
    """attempts to load CODES_CACHE"""
    return load_cache(config, CODES_CACHE)

def load_players(config: AppConfig)->dict:
    """attempts to load PLAYERS_CACHE"""
    return load_cache(config, PLAYERS_CACHE)