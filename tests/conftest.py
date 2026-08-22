import pytest, zoneinfo
from datetime import datetime
from domain.schema import AppConfig
from domain.models import Alt, Friend

@pytest.fixture
def user_config():
    """ valid user config dictionary """
    return {
        "guild_name": "The Secret Duck Society",
        "guild_id": 123456,
        "region": "US",
        "zone_id": 35,
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
def sample_friends():
    """ list of sample friend objects """
    rogue = Alt(1)
    rogue.name = "Guccigank"
    rogue.server = "Thrall"
    rogue.type = "Rogue"
    rogue.sightings = 30
    rogue.specs =  {
        "Subtlety": {"role": "DPS", "log_counts": {"log1": 18}},
        "Assassination": {"role": "DPS", "log_counts": {"log1": 12}}
    }
    rogue.sort_specs()
    friend1 = Friend([rogue])

    mage = Alt(2)
    mage.name = "Hopeseller"
    mage.server = "Area52"
    mage.type = "Mage"
    mage.sightings = 5
    mage.specs = {"Arcane": {"role": "DPS", "log_counts": {"log1": 5}}}
    mage.sort_specs()
    friend2 = Friend([mage])

    dk = Alt(3)
    dk.name = "Udderlymad"
    dk.server = "Ursin"
    dk.type = "DeathKnight"
    dk.sightings = 12
    dk.specs = {}
    dk.sort_specs()
    druid = Alt(4)
    druid.name = "Anonymoose"
    druid.server = "Ursin"
    druid.type = "Druid"
    druid.sightings = 10
    druid.specs = {"Guardian": {"role": "Tank", "log_counts": {"log1": 10}}}
    druid.sort_specs()
    friend3 = Friend([dk, druid])

    return [friend1, friend2, friend3]

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