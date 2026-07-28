from pathlib import Path
import json

def load_config(path: str = "config.json")->dict:
	# config path
	config_path = Path(path)
	if not config_path.exists():
		raise FileNotFoundError(f"missing config file: {config_path}")

    # load json
	config = {}
	with config_path.open('r', encoding='utf-8') as f:
		config = json.load(f)

	return config