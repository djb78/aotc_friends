import json, pytest, copy, calendar
from pathlib import Path
from services.config import load_config, prep_schedule, on_schedule
from etl.constants import RAIDS

def test_load_config_success(tmp_path, valid_config):
        """ test: verify the config file exists and
            contains the fields required for core functionality
        """
        # temporary config file
        config_data = valid_config
        config_file = tmp_path / "config.json"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Run the function
        config = load_config(path=str(config_file))

        # required fields
        assert config["guild_id"] == 123456
        assert config["zone_id"] == 35
        assert config["anchor"] == { "name": "Stiff", "server": "Area-52", "region": "US" }
        # derived fields
        assert config["raid"] == RAIDS[config["zone_id"]]
        assert config["cache_path_r"] == Path(".cache") / "123456" / "35"


def test_load_config_missing_file():
     with pytest.raises(FileNotFoundError):
         load_config("missing.json")

# verify config variables
# define test cases: (keys_to_delete, keys_to_make_empty, expected_error_message)
@pytest.mark.parametrize(
     "to_delete, to_empty, expected_error",
     [
         # --- Test Missing Keys ---
         (["zone_id"], [], "zone_id must be defined"),
         (["guild_id"], [], "guild_id must be defined"),
         (["anchor"], [], "anchor must be defined"),
         ([], ["anchor.name"], "missing anchor name"),
         ([], ["anchor.server"], "missing anchor server"),
         ([], ["anchor.region"], "missing anchor region"),
         
         # --- Test Empty Keys ---
         ([], ["zone_id"], "zone_id must be defined"),
         ([], ["guild_id"], "guild_id must be defined"),
         ([], ["anchor"], "anchor must be defined"),
         ([], ["anchor.name"], "missing anchor name"),
         ([], ["anchor.server"], "missing anchor server"),
         ([], ["anchor.region"], "missing anchor region")
     ]
)
def test_load_config_validation_errors(tmp_path, valid_config, to_delete, to_empty, expected_error):
    config_data = copy.deepcopy(valid_config)
     
    # test missing keys
    for key in to_delete:
        config_data.pop(key, None)
         
    # test empty keys
    for key in to_empty:
        if "." in key:  # Nested key (anchor)
            parent, child = key.split(".")
            if config_data.get(parent):
                config_data[parent][child] = ""
        else:
            config_data[key] = ""

    # Write bad config to temp file
    config_file = tmp_path / "config.json"
    with config_file.open("w", encoding="utf-8") as f:
        json.dump(config_data, f)

    # Assert load_config raises ValueError with expected message
    with pytest.raises(ValueError, match=expected_error):
        load_config(path=str(config_file))

# prep_schedule
# =============
def test_prep_schedule_success():
    """ returns a schedule correctly formated for time/date comparison """
    user_schedule = {
        "days": ["tuesday"],
        "start_est": "20:00",
        "end_est": "23:00",
        "moto": "what are these birds doing here?"
    }
    datetime_schedule = prep_schedule(user_schedule)

    assert set(datetime_schedule.keys()) == {"start", "end", "overnight", "days"}
    assert datetime_schedule["days"] == ["Tuesday"]
    assert datetime_schedule["start"].hour == 20
    assert datetime_schedule["end"].hour == 23
    assert datetime_schedule["overnight"] == False

def test_prep_schedule_overnight():
    """ overnight schedule sets flag and increments end day """
    user_schedule = {
        "days": ["FRIDAY"],
        "start_est": "23:00",
        "end_est": "01:00"
    }
    datetime_schedule = prep_schedule(user_schedule)

    assert set(datetime_schedule.keys()) == {"start", "end", "overnight", "days"}
    assert datetime_schedule["overnight"] == True
    assert datetime_schedule["end"].day == 2
    assert datetime_schedule["end"].hour == 1

def test_prep_schedule_format():
    """ invalid time format raises ValueError """
    user_schedule = {
        "days": ["Tuesday"],
        "start_est": "8:00 PM",
        "end_est": "10:00 PM"
    }
    with pytest.raises(ValueError, match='invalid raid time. correct time format "HH:MM" 24hr'):
        prep_schedule(user_schedule)

def test_prep_schedule_invalid():
    """ return empty dict if schedule is not valid """
    invalid_schedules = [{}, None, "tuesdays and thursdays at 7 pm"]
    for invalid in invalid_schedules:
        assert prep_schedule(invalid) == {}


@pytest.mark.parametrize(
        "incomplete_schedule, first_missing_field",
        [
            ({"start": "18:00", "user_key": 42}, "days"),
            ({"days": ["monday"], "start": "18:00"}, "start_est"),
            ({"start_est": "18:00"}, "days"),
            ({"days": ["THURSDAY"], "start_est": "20:00"}, "end_est")
        ]
)
def test_prep_schedule_incomplete(incomplete_schedule, first_missing_field):
    """ handles missing keys with informative error message 
        key check order "days" > "start_est" > "end_est"
    """
    with pytest.raises(ValueError, match=f'schedule must define "{first_missing_field}"'):
        prep_schedule(incomplete_schedule)

def test_prep_schedule_days():
    """ handles invalid keys with an informative error message """
    bad_days = ["Sat", "Sun", "Day", "T", "Th"]
    good_times = {
        "days": ["Tuesday"],
        "start_est": "19:00",
        "end_est": "21:00"
    }
    day_names = set(calendar.day_name)
    for bad_day in bad_days:
        moving_on = copy.deepcopy(good_times)
        moving_on["days"].append(bad_day)
        with pytest.raises(ValueError, match=f'"{bad_day}" not in {day_names}'):
            prep_schedule(moving_on)

# on_schedule
# =============
@pytest.fixture
def valid_schedule(make_dt):
    """ provide a fresh, valid schedule for testing """
    return {
        "days": ["Tuesday"],
        "start": make_dt("Tuesday", "20:00"),
        "end": make_dt("Tuesday", "22:00"),
        "overnight": False
    }

def test_on_schedule_true(make_ms, valid_schedule):
    """ correctly identifies timestamps that
        coincide with schedule days/times
    """
    start_time = make_ms("Tuesday", "20:15")
    assert on_schedule(start_time, valid_schedule) is True

def test_on_schedule_false(make_ms, valid_schedule):
    """ filters out off days and times """
    off_day = make_ms("Wednesday", "20:00")
    wrong_time = make_ms("Tuesday", "08:00")
    assert on_schedule(off_day, valid_schedule) is False
    assert on_schedule(wrong_time, valid_schedule) is False
