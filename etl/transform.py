from etl.constants import CODES_CACHE_NAME
from etl.models import Report
from etl.parser import parse_unique_codes
from services.file_io import load_cache

class Transformer:
    def __init__(self, config: dict):
        self.config = config
        self.reports = {}

    def transform_codes_reports(self):
        """
        Load codes json from cache, parse codes and instantiate Report objects
        """
        # load json
        raw_json = load_cache(self.config, CODES_CACHE_NAME)

        # parse codes from raw_json
        unique_codes = parse_unique_codes(raw_json)

        # instantiate report objects
        for code in unique_codes:
            if code not in self.reports:
                self.reports[code] = Report(code)