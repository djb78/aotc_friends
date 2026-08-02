
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

def clean_raw_json(raw_json: dict) -> dict:
    """ handles potential top level "data" key """
    if isinstance(raw_json, dict):
        clean_json = raw_json.get("data", raw_json)
    else:
        clean_json = raw_json
    if not isinstance(clean_json, dict):
        return {}
    return clean_json

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
    
    clean_json = clean_raw_json(raw_json)

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

def parse_fight_ids(fights_json: dict) -> dict:
    """ parse fight_json for each codes fight_ids
        return dict {"code": [id1, id2, id3, ...]}
        expected json structure:
            "data": { "reportData": { "report0": { "code": code }
            "data": { "reportData": { "report0": { "fights": [ {"id1": id1 }, { "id2": id2 }, ...]
        expected return value
            {   "code1": [ "id1", "id2", ... ], 
                "code2": [ "id1", "id2", ... ], ... }
    """
    if not fights_json:
        return {}

    clean_json = clean_raw_json(fights_json)

    report_data = _safe_get(clean_json, ["reportData"], {})
    report_fights = {}
    for report in report_data.values():
        code = _safe_get(report, ["code"], [])
        fights = _safe_get(report, ["fights"], [])

        fight_ids = []
        for fight in fights:
            if isinstance(fight, dict) and "id" in fight:
                fight_ids.append(fight["id"])

        if code and fight_ids:
            report_fights[code] = fight_ids

    return report_fights


