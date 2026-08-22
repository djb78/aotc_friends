import json
from pathlib import Path
from domain.schema import AppConfig

# JSON cache filenames
CODES_CACHE = "codes"
FIGHTS_CACHE = "fights"
PLAYERS_CACHE = "players"

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

def save_cache(config: AppConfig, cache_name: str, json_export: dict):
    cache_file = config.cache_path / f"{cache_name}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(json_export, f, indent=4)

        
def load_cache(config: AppConfig, cache_name: str)->dict:
    cache_file = config.cache_path / f"{cache_name}.json"
    if not cache_file.exists():
        return {}		

    with cache_file.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"{cache_file} corrupted")
            return {}


def save_output(md: str, path="friends.md"):
    """ write a string to a file """
    if not md or not isinstance(md, str):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"report successfully generated at {path}")