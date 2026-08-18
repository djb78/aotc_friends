from dotenv import load_dotenv
from services.config import load_config
from services.client import WCLClient
from etl.extract import Extractor
from etl.transform import Transformer
from etl.load import Loader

def main():
    config = load_config()
    load_dotenv()

    client = WCLClient()

    e = Extractor(client, config)
    e.extract_all()

    t = Transformer(config)
    t.transform_all()

    l = Loader(config, t.friends)
    l.load_friends()


if __name__ == "__main__":
    main()