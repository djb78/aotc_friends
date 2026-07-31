
def _safe_get(clean_json: dict, keys: list, default=None):
    """navigate nested dictionary, return default if key is missing/None"""
    current_json = clean_json
    for key in keys:
        if not isinstance(current_json, dict):
            return default
        current_json = current_json.get(key)
        if current_json is None:
            return default
    return current_json

def parse_unique_codes(raw_json: dict) -> list:
    """ Recieve raw_json (loaded from cache) and retrieve a list of unique codes
        return sorted list of unique codes
        expected json structure: 
            "reportData" { "reports" { "data" [ {"code": code }, ... ]
            "characterData" { "character" { "recentReports" { "data" [ { "code": code }, ...]
            "characterData" { "character" { "zoneRankings" { "rankings" [ {"report": {"code": code } }, ...]
    """
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
    for report in _safe_get(clean_json, ["reportData", "reports", "data"], []):
        if isinstance(report, dict) and (code := report.get("code")):
            unique_codes.add(code)
    # recent report codes
    for report in _safe_get(clean_json, ["characterData", "character", "recentReports", "data"], []):
        if isinstance(report, dict) and (code := report.get("code")):
            unique_codes.add(code)
    # zoneRankings
    for ranking in _safe_get(clean_json, ["characterData", "character", "zoneRankings", "rankings"], []):
        if isinstance(ranking, dict):
            report = ranking.get("report")
            if isinstance(report, dict) and (code := report.get("code")):
                unique_codes.add(code)

    return list(sorted(unique_codes))