from etl.constants import CODES_CACHE_NAME
from etl.models import Report
from services.file_io import load_cache

class Transformer:
    def __init__(self, config: dict):
        self.config = config
        self.reports = {}

    def _safe_get(self, clean_json: dict, keys: list, default=None):
        """navigate nested dictionary, return default if key is missing/None"""
        current_json = clean_json
        for key in keys:
            if not isinstance(current_json, dict):
                return default
            current_json = current_json.get(key)
            if current_json is None:
                return default
        return current_json

    def transform_codes_reports(self):
        """
        Load codes json from cache and instantiate Report objects
        json structure: 
            "reportData" { "reports" { "data" [ {"code": code }, ... ]
            "characterData" { "character" { "recentReports" { "data" [ { "code": code }, ...]
            "characterData" { "character" { "zoneRankings" { "rankings" [ {"report": {"code": code } }, ...]
        """
        raw_json = load_cache(self.config, CODES_CACHE_NAME)
        if not raw_json:
            return []

        # handle potential top level "data" key
        if isinstance(raw_json, dict):
            clean_json = raw_json.get("data", raw_json)
        else:
            clean_json = raw_json
        if not isinstance(clean_json, dict):
            return []

        # retrieve codes
        unique_codes = set() 
        # guild report codes
        for report in self._safe_get(clean_json, ["reportData", "reports", "data"], []):
            if isinstance(report, dict) and (code := report.get("code")):
                unique_codes.add(code)
        # recent report codes
        for report in self._safe_get(clean_json, ["characterData", "character", "recentReports", "data"], []):
            if isinstance(report, dict) and (code := report.get("code")):
                unique_codes.add(code)
        # zoneRankings
        for ranking in self._safe_get(clean_json, ["characterData", "character", "zoneRankings", "rankings"], []):
            if isinstance(ranking, dict):
                report = ranking.get("report")
                if isinstance(report, dict) and (code := report.get("code")):
                    unique_codes.add(code)

        # instantiate report objects
        for code in sorted(unique_codes):
            if code not in self.reports:
                self.reports[code] = Report(code)