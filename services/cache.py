# from pathlib import Path
import json

def save_cache(config: dict, cache_name: str, json_export: dict):
    cache_path = config['cache_path_r'] / f"{cache_name}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(json_export, f, indent=4)

        
def load_cache(config: dict, cache_name: str)->dict:
    cache_path = config['cache_path_r'] / f"{cache_name}.json"
    if not cache_path.exists():
        return {}		

    with cache_path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"{cache_path} corrupted")
            return {}