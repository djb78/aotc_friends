import json, calendar, zoneinfo
from datetime import datetime, timedelta
from pathlib import Path
from domain.constants import RAIDS

def load_config(path: str = "config.json")->dict: 
    """ Load user settings from config.json 
        verify required fields
        create derivitave fields 
            regular = { "name": name, "server": server, "region": region }
            raid = { "name": raid_name, "final_boss": {"id": id, "name": boss_name }}
            schedule datetime info
            cache_path_r
    """   
    # verify path
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"missing config file: {config_path}")

    # load config.json
    with config_path.open('r', encoding='utf-8') as f:
        config = json.load(f)

    # verify config fields exist
    # required for current "clean sweep" code retrieval in extract_codes
    config_fields = ["zone_id", "guild_id", "regular"]
    for field in config_fields:
        if field not in config or not config[field]:
            raise ValueError(f"'{field}' must be defined in {config_path}")

    # verify valid 'regular' format (name-server)
    name_server = config.get("regular")
    if not isinstance(name_server, str) or "-" not in name_server:
        raise ValueError(f"invalid 'regular' format {name_server} != 'name-server'")
    # replace with valid dictionary version
    [name, server] = name_server.split("-", maxsplit=2)
    config["regular"] = {"name": name, "server": server, "region": config.get("region")}
        
    # verify valid guild_id?

    # verify valid zone_id
    zone_id = config["zone_id"]
    if zone_id not in RAIDS:
        raise ValueError("invalid zone_id, see zone:raid key in README")
    # add raid info to config
    config["raid"] = RAIDS[zone_id]
    
    # check schedule and convert to datetime format
    if "schedule" in config:
        config["schedule"] = prep_schedule(config["schedule"])

    # add path for JSON cache
    guild_id = str(config['guild_id'])
    zone_id = str(config['zone_id'])
    config["cache_path_r"] = Path(".cache") / guild_id / zone_id
        
    return config

def prep_schedule(schedule: dict)->dict:
    """ return prepped schedule with 
        normalized values for date/time comparison
        generic datetimes, no date info, no timezone 

        schedule = {"days": [ weekday_string_list ], "start_est": "HH:MM", "end_est": "HH:MM"}
        prep = {"days": [ Weekday_String_List ], "start": datetime, "end": datetime, "overnight": bool}
    """
    if not schedule or not isinstance(schedule, dict):
        return {}
    needed_fields = ["days", "start_est", "end_est"]
    for field in needed_fields:
        if field not in schedule or not schedule[field]:
            raise ValueError(f'schedule must define "{field}"')
    
    prep = {}
    try:
        # create datetime objects for start and end times
        prep["start"] = datetime.strptime(schedule["start_est"], "%H:%M")
        prep["end"] = datetime.strptime(schedule["end_est"], "%H:%M")
    except ValueError:
        raise ValueError('invalid raid time. correct time format "HH:MM" 24hr')

    # increment end day if schedule goes overnight
    prep["overnight"] = prep["end"] < prep["start"]
    if prep["overnight"]:
        prep["end"] += timedelta(days=1)

    # normalize and validate day names
    if not isinstance(schedule["days"], list):
        raise ValueError('"days" must be a list[ of "day", "names"]')
    day_names = set(calendar.day_name)
    prep["days"] = []
    for name in schedule["days"]:
        name = name.capitalize()
        if name not in day_names:
            raise ValueError(f'"{name}" not in {day_names}')
        prep["days"].append(name)
    
    return prep


def on_schedule(start_ms: float, schedule: dict)->bool:
    """ check if start_ms coincides with 
        scheduled days and times
        no time -> False
        no schedule -> True

        schedule = {
            "days":      [ "MONDAY", "TUESDAY", ... ],
            "start":     datetime, 
            "end":       datetime, 
            "overnight": bool
    """
    if not start_ms:
        return False
    if not schedule or not isinstance(schedule, dict):
        return True
    
    est = zoneinfo.ZoneInfo("America/New_York")
    start = datetime.fromtimestamp(start_ms / 1000.0, tz=est)
    schedule_start = schedule.get("start")
    schedule_end = schedule.get("end")

    # Handle overnight schedules
    start_day = start.date()            # for scheduled day verification
    schedule_day = schedule_start.day   # for time comparison
    if schedule.get("overnight") and start.time() < schedule_end.time():
        # if start was after midnight but still within schedule
        start_day -= timedelta(days=1)
        schedule_day += 1

    # verify scheduled day
    day_name = start_day.strftime("%A")
    on_schedule_day = day_name in schedule.get("days", [])

    # verify scheduled time overlap
    duration = schedule_end - schedule_start
    start_time = start.replace(day=schedule_day, 
                                month=schedule_start.month, 
                                year=schedule_start.year, 
                                tzinfo=schedule_start.tzinfo)
    end_time = start_time + duration
    at_schedule_time = ( start_time < schedule_end and 
                        end_time > schedule_start )

    return on_schedule_day and at_schedule_time