
def safe_get(clean_json: dict, keys: list, default=None):
    """
    confirms clean_json is a dict and the key exists (recursive)
    returns the value associated with the last key
        default/None if clean_json is bad or any key is missing
    """
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
    for report in safe_get(clean_json, ["reportData", "reports", "data"], []):
        if isinstance(report, dict) and (code := report.get("code")):
            unique_codes.add(code)
    # recent report codes
    for report in safe_get(clean_json, ["characterData", "character", "recentReports", "data"], []):
        if isinstance(report, dict) and (code := report.get("code")):
            unique_codes.add(code)
    # zoneRankings
    for ranking in safe_get(clean_json, ["characterData", "character", "zoneRankings", "rankings"], []):
        if isinstance(ranking, dict):
            report = ranking.get("report")
            if isinstance(report, dict) and (code := report.get("code")):
                unique_codes.add(code)

    return list(sorted(unique_codes))


def parse_fight_ids(fights_json: dict) -> dict:
    """ legacy wrapper
        retrieve codes and associated fight ids for extract_players
        refactored original parse_fight_ids into parse_fights for transform phase
        return dict {"code": [id1, id2, id3, ...], ... }
    """
    fight_details = parse_fights(fights_json)
    if not isinstance(fight_details, dict):
        return {}
    
    fight_ids = {}
    for code, fights_list in fight_details.items():
        if not code or not isinstance(fights_list, list): 
            continue

        ids = []
        for fight in fights_list:
            if isinstance(fight, dict) and "id" in fight:
                ids.append(fight["id"])
        if ids:
            fight_ids[code] = ids
            
    return fight_ids

def parse_fights(fights_json: dict) -> dict:
    """ parse fights_json for fight details
        return a "code" keyed dictionary of "fights"

        expected fights_json structure:
            "data": { "reportData": { 
                "report0_0: { 
                    "code": code, 
                    "fights": fights_list
                }, ... 
            } }
        expected output:
            fights = { code: fights_list, ... }
    """
    # verify fights_json
    if not fights_json:
        return {}

    # input/output prep
    clean_json = clean_raw_json(fights_json)
    fights = {}

    # parse each report
    for report in safe_get(clean_json, ["reportData"], {}).values():
        # retrieve report code
        if not isinstance(report, dict) or not (code := report.get("code")):
            continue  

        # add {code: fights_list} to fights
        fights_list = safe_get(report, ["fights"], None)
        if fights_list and isinstance(fights_list, list):
            fights[code] = fights_list
    
    return fights




