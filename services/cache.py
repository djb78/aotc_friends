# from pathlib import Path
import json
from services.config import AppConfig

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