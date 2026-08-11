# tools
# =====
def safe_get(clean_json: dict, keys: list, default=None):
    """
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
    """ sanitize raw json input
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

        expected json structure: 
            "reportData" { "reports" { "data" [ {"code": code }, ... ]
            "characterData" { "character" { "recentReports" { "data" [ { "code": code }, ...]
            "characterData" { "character" { "zoneRankings" { "rankings" [ {"report": {"code": code } }, ...]

    [ unique_codes ]
    """
    # verify raw_json
    data = prep_json(codes_json)
    unique_codes = set() 

    # retrieve unique codes
    # guild report codes (reports attributed to the guild)
    for report in safe_get(data, ["reportData", "reports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)
    # recent report codes (last 100 reports uploaded by the anchor character)
    for report in safe_get(data, ["characterData", "character", "recentReports", "data"], []):
        if (code := safe_get(report, ["code"])):
            unique_codes.add(code)
    # zoneRankings (boss kills involving the anchor character)
    for ranking in safe_get(data, ["characterData", "character", "zoneRankings", "rankings"], []):
        if (code := safe_get(ranking, ["report", "code"])):
            unique_codes.add(code)

    return list(sorted(unique_codes))

def parse_fight_ids(fights_json: dict) -> dict:
    """ 
	parse fights json for lists of fight ids
	return a code keyed dictionary of
	lists of fight ids
    
    {"code": [id1, id2, id3, ...], ... }
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

        expected fights_json structure:
            "data": { "reportData": { 
                "ch0_r0: { 
                    "code": code, 
                    "startTime": time,
                    "fights": [fights_info]
                }, ... 
            } }
        
    { code: { "time": time, "fights": [fights_info] } }
    """
    # verify fights_json
    data = prep_json(fights_json)
    fight_reports = {}

    # for each report
    for report in safe_get(data, ["reportData"], {}).values():
        code = safe_get(report, ["code"], None)
        if not code:
            continue  
        # add log info dictionary to output
        fights = safe_get(report, ["fights"], None)
        if fights and isinstance(fights, list):
            fight_reports[code] = {
                "time": safe_get(report, ["startTime"], None),
                "fights": fights }
    
    return fight_reports

def parse_players(players_json: dict) -> dict:
    """ 
	parse players_json for player info
	return a "code" keyed dictionary of
	lists of player info dictionaries (role injected)
        
        expected players_json structure
            "data": { "reportData": { 
                "ch0_r0: { 
                    "code": code, 
                    "playerDetails": { role: [ {player_info}, ... ], ...
                }, ... 
            } }

    { "code": { "player_id": [ {spec_info}, ... ] }
    """
    # verify players_json
    data = prep_json(players_json)
    player_specs = {}    # code { player_id: [{spec_info}, ], },

    # REPORT {
    for report in safe_get(data, ["reportData"], {}).values():
        # retreive playerDetails (role dictionary)
        # player_details = { "tanks": [], "healers": [], "dps": [] }
        player_details = safe_get(report, ["playerDetails"])
        code = safe_get(report, ["code"], None)
        if not code or not isinstance(player_details, dict):
            continue
        if code not in player_specs:
            player_specs[code] = {}  # player_id: [{spec_info}, ], 
        
        # PLAYER [
        for role, player_list in player_details.items():
            if not isinstance(player_list, list):
                continue
            # player_info -> spec_info
            for player_info in player_list:
                if not isinstance(player_info, dict):
                    continue
                # inject role
                spec_info = player_info.copy()
                spec_info["role"] = role

                # update player spec list
                player_id = spec_info.pop("id")
                if player_id not in player_specs[code]:
                    player_specs[code][player_id] = []  # {spec_info},

                player = player_specs[code][player_id]
                if not isinstance(player, list):
                    player = []
                player.append(spec_info)

    return player_specs
 
