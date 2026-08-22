from dotenv import load_dotenv
from services.file_io import load_config, save_output
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
    output = l.load_friends()

    save_output(output)


if __name__ == "__main__":
    main()