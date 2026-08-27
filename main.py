import sys, logging
from dotenv import load_dotenv
from services.file_io import load_config, save_output
from services.client import WCLClient
from etl.extract import Extractor
from etl.transform import Transformer
from etl.load import Loader

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s")

    try:
        config = load_config()
        logger.info("config loaded")

        load_dotenv()
        client = WCLClient()

        e = Extractor(client, config)
        e.extract_all()

        t = Transformer(config)
        t.transform_all()

        l = Loader(config, t.friends)
        output = l.load_output()

        save_output(output)

    except FileNotFoundError as e:
        logger.critical("configuration error: %s", e)
        sys.exit(1)
    except ValueError as e:
        logger.critical("validation error: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.critical("unexpected error: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()