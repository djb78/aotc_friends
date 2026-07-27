import json
from dotenv import load_dotenv
from client import WCLClient

def main():
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
