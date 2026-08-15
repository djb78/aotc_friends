import pytest, zoneinfo
from datetime import datetime

@pytest.fixture
def valid_config():
    """Provides a fresh, valid configuration dictionary for tests"""
    return {
        "guild_name": "The Secret Duck Society",
        "guild_id": 123456,
        "region": "US",
        "zone_id": 35,
        "regular": "Stiff-Area52",
        "schedule": {
            "days": ["tuesday", "saturday"],
            "start_est": "20:00",
            "end_est": "22:00"
        }
    }

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