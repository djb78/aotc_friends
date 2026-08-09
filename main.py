from dotenv import load_dotenv
from services.config import load_config
from services.client import WCLClient
from etl.extract import Extractor
from etl.transform import Transformer

def main():
    config = load_config()
    load_dotenv()

    client = WCLClient()

    e = Extractor(client, config)
    e.extract_all()

    t = Transformer(config)
    t.transform_codes_reports()


if __name__ == "__main__":
    main()