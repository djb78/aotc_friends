# tools
# =====
def safe_get(clean_json: dict, keys: list, default=None):
    """ helper
    confirms clean_json is a dict and the key exists (recursive)
    returns the value associated with the last key
        default/None if clean_json or any key is bad/missing
    """
    current_json = clean_json
    for key in keys:
        if not isinstance(current_json, dict):
            return default
        current_json = current_json.get(key)
        if current_json is None:
            return default
    return current_json

def prep_json(raw_json: dict) -> dict:
    """ helper
    sanitize raw json input
    handles potential top level "data" key 
    guarantees return -> dict
    """
    if not isinstance(raw_json, dict):
        return {}
    contents = safe_get(raw_json, ["data"], raw_json)
    return contents if isinstance(contents, dict) else {}

# Extract parsers
# ===============
def parse_unique_codes(codes_json: dict) -> list:
    """ 
    parse codes_json for a list of unique codes
	return sorted list of unique codes

    input: response from extract_codes query 
        "reportData" { "reports" { "data" [ {"code": code }, ... ]
        "characterData" { "character" { "recentReports" { "data" [ { "code": code }, ...]
    output: list of unique codes
    
    extract_codes -> parse_unique_codes -> extract_fights
    """
    # verify raw_json
    data = prep_json(codes_json)
    unique_codes = set() 

    # retrieve unique codes
    # guild report codes (reports attributed to the guild)
    for report in safe_get(data, ["reportData", "reports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)
    # recent report codes (last 100 reports uploaded by the 'regular' character)
    for report in safe_get(data, ["characterData", "character", "recentReports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)

    return list(sorted(unique_codes))

def parse_fight_ids(fights_json: dict) -> dict:
    """ 
	parse fights json for lists of fight ids
	return a code keyed dictionary of
	lists of fight ids

    input: response from extract_fights query
    output: {"code": [id1, id2, id3, ...], ... }

    extract_fights -> parse_fight_ids -> extract_players
    """
    data = prep_json(fights_json)
    fight_ids = {}

    # for each report
    for report in safe_get(data, ["reportData"], {}).values():
        fights = safe_get(report, ["fights"], None)
        if not isinstance(fights, list):
            continue

        code = safe_get(report, ["code"], None)
        ids = [f["id"] for f in fights if isinstance(f, dict) and "id" in f]
        if code and ids:
            fight_ids[code] = ids
           
    return fight_ids

# Transform parsers
# =================
def parse_fights(fights_json: dict) -> dict:
    """ 
    parse fights_json for fight info
	return a code keyed dictionary of
	report info, including startTime and a
	list of fight info dictionaries

    input: response from extract_fights query
        "data": { "reportData": { 
            "alias": { 
                "code": code, 
                "startTime": time, 
                "zone": { "id": id } 
                "fights": [fights_info]
    output: { code: { "time": time, "zone_id": id, "fights": [fights_info] } }

    extract_fights -> parse_fights -> transform_fights_pulls
    """
    # verify fights_json
    data = prep_json(fights_json)
    fight_logs = {}
    
    reports = safe_get(data, ["reportData"], {})
    if not reports or not isinstance(reports, dict):
        # not a dictionary or empty = no cached data
        raise ValueError(f'missing fight data: "reportData": {reports}')
    # for each report
    for report in reports.values():
        if not report or not isinstance(report, dict):
            continue
        code = safe_get(report, ["code"], None)
        if not code:
            continue  
        fights = safe_get(report, ["fights"], None)
        if not fights or not isinstance(fights, list):
            continue

        # add log info dictionary to output
        fight_logs[code] = {
            "time": safe_get(report, ["startTime"]),
            "zone_id": safe_get(report, ["zone", "id"]),
            "fights": fights }

    if not fight_logs:
        # no valid fights in non-empty dictionary
        raise ValueError(f'bad report data: "reportData": {reports}')
    return fight_logs

def parse_players(players_json: dict) -> dict:
    """ 
	parse players_json for player info
	return a "code" keyed dictionary of
	lists of player info dictionaries (role injected)
        
    input: response from extract_players query
            "data": { "reportData": { 
                "alias: { 
                    "code": code, 
                    "playerDetails": { "data": { "playerDetails": { 
                        role: [ {player_info} ]
    output: { "code": { "player_id": [ {spec_info}, ... ] }

    extract_players -> parse_players -> transform_roster
    """
    # verify players_json
    data = prep_json(players_json)
    player_specs = {}    # code { player_id: [{spec_info}, ], },

    # { "code": code, "playerDetails": {"data": {"playerDetails": {} }}}
    for report in safe_get(data, ["reportData"], {}).values():
        # get code
        code = safe_get(report, ["code"], None)
        # retreive playerDetails (role dictionary)
        player_details = safe_get(report, ["playerDetails", "data", "playerDetails"])
        if not code or not isinstance(player_details, dict):
            continue
        if code not in player_specs:
            player_specs[code] = {}  # player_id: [{spec_info}, ], 
        
        # { "tanks": [{spec_info}], "healers": [{spec_info}], "dps": [{spec_info}] }
        for role, player_list in player_details.items():
            if not isinstance(player_list, list) or not player_list:
                continue
            # player_info -> spec_info
            for player_info in player_list:
                if not isinstance(player_info, dict) or not player_info:
                    continue
                # inject role
                spec_info = player_info.copy()
                spec_info["role"] = role
                # remove report/log specific id
                player_id = spec_info.pop("id")

                # verify player spec list exists for code
                if player_id not in player_specs[code]:
                    player_specs[code][player_id] = []  # {spec_info},
                player = player_specs[code][player_id]
                # if the existing player_id value is not a list (of specs)
                if not isinstance(player, list):    # neccessary? eliminate player variable?
                    player = []

                # add spec_info to output
                player_specs[code][player_id].append(spec_info)

    return player_specs
 
