import pytest, zoneinfo, json
from datetime import datetime
from domain.schema import AppConfig

@pytest.fixture
def user_config():
    """ valid user config dictionary """
    return {
        "guild_name": "The Secret Duck Society",
        "guild_id": 123456,
        "region": "US",
        "zone_id": 46,
        "anchor_alt": "Stiff-Area52",
        "schedule": {
            "days": ["tuesday", "saturday"],
            "start_est": "20:00",
            "end_est": "22:00"
        },
        "has_alts": {
            "Stiff-Area52": ["Darkrat-Area52"]
        }
    }

@pytest.fixture
def valid_config(user_config):
    """valid AppConfig object based on user_config"""
    return AppConfig.model_validate(user_config)

@pytest.fixture
def make_dt():
    """ factory fixture, returns function to 
        generate datetime objects for a weekday and time
        Known Monday: 26/08/03
    """
    def _make_dt(weekday: str, time_str: str, tz: str="America/New_York")->float:
        weekdays = {"Monday": 3, "Tuesday": 4, "Wednesday": 5,
                    "Thursday": 6, "Friday": 7, "Saturday": 8, "Sunday": 9}
        day = weekdays.get(weekday.capitalize())
        if not day:
            raise ValueError(f"Invalid day name: {day}")
        date = f"2026-08-0{day} {time_str}"
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M")
        dt = dt.replace(tzinfo=zoneinfo.ZoneInfo(tz))

        return dt

    return _make_dt

@pytest.fixture
def make_ms(make_dt):
    """ factory fixture, returns function to
        convert datetime objects from make_dt into
        millisecond timestamps
    """
    def _make_ms(weekday: str, time_str: str, tz: str="America/New_York")->float:
        return make_dt(weekday, time_str).timestamp() * 1000

    return _make_ms

@pytest.fixture
def make_json_cache(tmp_path):
    """ factory fixture, dumps cache_json to tmp_path for testing """
    def _make_json_cache(config: AppConfig, cache_json: dict, cache_name: str):
        config.cache_root = tmp_path
        cache_file = config.cache_path / f"{cache_name}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_json, f)

    return _make_json_cache

# mock json caches
# ================
@pytest.fixture
def mock_codes_cache():
    """ sample structure from actual API response 
        QoL values
    """
    return {
    "data": {
        "reportData": {
            "reports": { "data": [
                    { "code": "code_0" },
                    { "code": "code_1" } ]
        } },
        "characterData": {
            "character": { "recentReports": { "data": [
                    { "code": "code_1" },
                    { "code": "code_2" },
                    { "code": "code_3" } ]
        } } }
    } }

@pytest.fixture
def mock_fights_cache():
    """ sample structure from actual API response 
        QoL values
    """
    return {
    "data": {
        "reportData": {
            "alias_a": {
                "code": "code_0",
                "zone": { "id": 46 },
                "startTime": 0,
                "fights": []
            },
            "alias_b": {
                "code": "code_1",
                "zone": { "id": 46 },
                "startTime": 100,
                "fights": [
                    {   "id": 1,
                        "encounterID": 100,
                        "name": "Boss_100",
                        "kill": False,
                        "friendlyPlayers": [1, 2, 3],
                        "difficulty": 4
                    },
                    {   "id": 2,
                        "encounterID": 100,
                        "name": "Boss_100",
                        "kill": True,
                        "friendlyPlayers": [1, 2, 3],
                        "difficulty": 4
                    } ]
            },
            "alias_c": {
                "code": "code_2",
                "zone": { "id": 46 },
                "startTime": 200,
                "fights": [
                    {
                        "id": 1,
                        "encounterID": 200,
                        "name": "Boss_200",
                        "kill": False,
                        "friendlyPlayers": [40, 20],
                        "difficulty": 4
                    } ]
            }
    } } }

@pytest.fixture
def mock_players_cache():
    """ sample structure from actual API response 
        QoL values
    """
    return { "data": { "reportData": {
        "alias_a": {
            "code": "code_1",
            "playerDetails": { "data": { "playerDetails": {
                "healers": [
                    {   "name": "flex_1000",
                        "id": 1,
                        "guid": 1000,
                        "type": "flex_class",
                        "server": "Server",
                        "region": "US",
                        "icon": "class-spec",
                        "specs": [{ "spec": "heal_spec_1", "count": 1 }] }
                ],
                "dps": [
                    {   "name": "flex_1000",
                        "id": 1,
                        "guid": 1000,
                        "type": "flex_class",
                        "server": "Server",
                        "region": "US",
                        "icon": "class-spec",
                        "specs": [{ "spec": "dps_spec_1", "count": 1 }] 
                    },
                    {   "name": "dps_2000",
                        "id": 2,
                        "guid": 2000,
                        "type": "dps_class",
                        "server": "Server",
                        "region": "US",
                        "icon": "class-spec",
                        "specs": [
                                { "spec": "dps_spec_1", "count": 1 },
                                { "spec": "dps_spec_2", "count": 1 }] 
                    }
                ],
                "tanks": [
                    {   "name": "tank_3000",
                        "id": 3,
                        "guid": 3000,
                        "type": "tank_class",
                        "server": "Server",
                        "region": "US",
                        "icon": "class-spec",
                        "specs": [{ "spec": "tank_spec_1", "count": 2 }] }
                ] } } } },
        "alias_b": {
            "code": "code_2",
            "playerDetails": { "data": { 
                "playerDetails": {
                    "healers": [
                        {   "name": "heal_4000",
                            "id": 40,
                            "guid": 4000,
                            "type": "heal_class",
                            "server": "Server",
                            "region": "US",
                            "icon": "class-spec",
                            "specs": [{ "spec": "heal_spec_1", "count": 1 }] } 
                    ], 
                    "tanks": [], 
                    "dps": [
                        {   "name": "dps_2000",
                            "id": 20,
                            "guid": 2000,
                            "type": "dps_class",
                            "server": "Server",
                            "region": "US",
                            "icon": "class-spec",
                            "specs": [{ "spec": "dps_spec_1", "count": 1 }] }
                    ] 
        } } } },
        "alias_c": {
            "code": "private",
            "playerDetails": None
        }
    } } }

