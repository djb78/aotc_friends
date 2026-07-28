import json
from dotenv import load_dotenv
from services.client import WCLClient
from services.file_io import load_config, save_cache, load_cache

def main():
    # configuration test
    print("loading config.json...")
    config = load_config()
    print(f"guild id: {config['guild_id']}")
    print(f"zone id: {config['zone_id']}")

    # JSON cache test
    save_cache(config, "config", {'test': 1, 'two': '3'})
    print(load_cache(config, "config"))

    # client test
    load_dotenv()
    client = WCLClient()

    test_query = """
    query {
        rateLimitData {
            limitPerHour
            pointsSpentThisHour    
        }  
    }
    """

    try:
        print("Connecting to warcraftlogs...")
        result = client.query(test_query)
        print("\nConnected")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()