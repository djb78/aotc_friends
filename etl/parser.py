
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

def parse_unique_codes(codes_json: dict) -> list:
    """ Recieve raw_json (loaded from cache) and retrieve a list of unique codes
        return sorted list of unique codes

        expected json structure: 
            "reportData" { "reports" { "data" [ {"code": code }, ... ]
            "characterData" { "character" { "recentReports" { "data" [ { "code": code }, ...]
            "characterData" { "character" { "zoneRankings" { "rankings" [ {"report": {"code": code } }, ...]
    """
    # verify raw_json
    if not codes_json:
        return []

    # input/output prep
    clean_json = clean_raw_json(codes_json)
    unique_codes = set() 

    # retrieve codes
    # guild report codes (reports attributed to the guild)
    for report in safe_get(clean_json, ["reportData", "reports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)
    # recent report codes (last 100 reports uploaded by the anchor character)
    for report in safe_get(clean_json, ["characterData", "character", "recentReports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)
    # zoneRankings (boss kills involving the anchor character)
    for ranking in safe_get(clean_json, ["characterData", "character", "zoneRankings", "rankings"], []):
        if (code := safe_get(ranking, ["report", "code"])):
            unique_codes.add(code)

    return list(sorted(unique_codes))


def parse_fight_ids(fights_json: dict) -> dict:
    """ legacy wrapper
        retrieve codes and associated fight ids for extract_players
        refactored original parse_fight_ids into parse_fights for transform phase
        return dict {"code": [id1, id2, id3, ...], ... }
    """
    # retrieve code keyed fights dictionary
    fight_details = parse_fights(fights_json)
    if not isinstance(fight_details, dict):
        return {}
    
    fight_ids = {}
    # for each code/report/log
    for code, report in fight_details.items():
        fights = safe_get(report, ["fights"], None)
        if not code or not isinstance(fights, list):
            continue

        report_ids = []
        # make a list of fight ids in the report
        for fight in fights:
            if isinstance(fight, dict) and "id" in fight:
                report_ids.append(fight["id"])

        if not report_ids:
            continue
        # construct code keyed dictionary of id lists
        fight_ids[code] = report_ids
            
    return fight_ids

def parse_fights(fights_json: dict) -> dict:
    """ parse fights_json for fight details
        return a report code keyed 
        dictionary of fight information

        expected fights_json structure:
            "data": { "reportData": { 
                "ch0_r0: { 
                    "code": code, 
                    "fights": fights_list
                }, ... 
            } }
        expected output: code keyed dictionary of
            report dictionaries (fights: list)
            fight_reports = { 
                code: {
                    "fights": fights_list}, 
                code: { ... }, ... }
    """
    # verify fights_json
    if not fights_json:
        return {}

    # input/output prep
    clean_json = clean_raw_json(fights_json)
    fight_reports = {}

    # parse each report
    for report in safe_get(clean_json, ["reportData"], {}).values():
        # retrieve report code
        code = safe_get(report, ["code"], None)
        if not code:
            continue  
        # add {code: fights_list} to fights
        fights_list = safe_get(report, ["fights"], None)
        if fights_list and isinstance(fights_list, list):
            fight_reports[code] = {
                "fights": fights_list }
    
    return fight_reports

def parse_players(players_json: dict) -> dict:
    """ parse players_json for character appearances
        return a "code" keyed dictionary of "playerDetails" 
            with role layer injected into player_info dictionaries
        
        expected input: players_json
            "data": { "reportData": { 
                "ch0_r0: { 
                    "code": code, 
                    "playerDetails": { role: [ player_info, ... ], ...
                }, ... 
            } }
        expected output: code keyed dictionary of lists of player info
            { "code": [ player_role_info, ... ], "code": [ ... ], ... }
    """
    # verify players_json
    if not players_json:
        return {}

    # input/output prep
    clean_json = clean_raw_json(players_json)
    players = {}

    # retrieve reportData
    report_data = safe_get(clean_json, ["reportData"])
    if not isinstance(report_data, dict):
        return {}
    # parse each report
    for report in report_data.values():
        # retreive report code
        code = safe_get(report, ["code"], None)
        if not code:
            continue

        # retreive playerDetails (role dictionary)
        # player_details = { "tanks": [], "healers": [], "dps": [] }
        player_details = safe_get(report, ["playerDetails"])
        if not isinstance(player_details, dict):
            continue
        if code not in players:
            players[code] = []

        # parse the list of player_info for each role (tank, healer, dps)
        for role, player_list in player_details.items():
            if not isinstance(player_list, list):
                continue
            for player_info in player_list:
                if isinstance(player_info, dict):
                    player_role_info = player_info.copy()
                    player_role_info["role"] = role
                    players[code].append(player_role_info)
    return players
 
