import pytest
from pathlib import Path
from pydantic import ValidationError
from services.config import AppConfig, AltConfig, ScheduleConfig
from domain.constants import RAIDS


# ScheduleConfig
# ==========================================
# days_to_int
# ===========
def test_days_to_int_success():
    """Test: day names converted to correct ints"""
    schedule = ScheduleConfig(
        days=["Tuesday", "Saturday"],
        start_est="20:00",
        end_est="22:00"
    )
    assert schedule.days == set([2, 6])

def test_days_to_int_mix():
    """ Test: case-insensitive
        ints in the range 1-7 are directly added to the list
    """
    schedule = ScheduleConfig(
        days=[1, "Tuesday", "WEDNESDAY", "thursday", 5],
        start_est="20:00",
        end_est="22:00"
    )
    assert schedule.days == set([1, 2, 3, 4, 5])

def test_days_to_int_invalid():
    """Test: invalid day names raise ValidationError"""
    with pytest.raises(ValidationError) as error:
        ScheduleConfig(days=["Noneday"], start_est="20:00", end_est="22:00")

    assert "invalid day name" in str(error)

def test_days_to_int_other():
    """Test: non-string day "names" raise ValidationError"""
    others = [0, 10, {}, [], None, True]
    for other in others:
        with pytest.raises(ValidationError) as error:
            ScheduleConfig(days=[other], start_est="20:00", end_est="22:00")
        assert "days must be strings" in str(error)

# includes
# ========
def test_includes_true(make_ms):
    """Test a standard on-schedule log"""
    schedule = ScheduleConfig(days=[2], start_est="20:00", end_est="22:00")
    true_ms = make_ms("Tuesday", "20:30")
    assert schedule.includes(true_ms) is True

def test_includes_false(make_ms):
    """Test an off-schedule log"""
    schedule = ScheduleConfig(days=[2], start_est="20:00", end_est="22:00")
    false_ms = make_ms("Wednesday", "20:15")
    assert schedule.includes(false_ms) is False

def test_includes_overnight(make_ms):
    """Test an overnight schedule with a late-start (after midnight) log"""
    overnight = ScheduleConfig(days=[2], start_est="23:00", end_est="01:00")
    late_ms = make_ms("Wednesday", "00:05")
    assert overnight.includes(late_ms) is True

def test_includes_early(make_ms):
    """Test an early-start log"""
    schedule = ScheduleConfig(days=[2], start_est="20:00", end_est="22:00")
    early_ms = make_ms("Tuesday", "19:45")
    assert schedule.includes(early_ms) is True

# AppConfig
# ==========================================
# scheduled
# =========
def test_scheduled_none(user_config, make_ms):
    """Test that an undefined schedule returns True"""
    user_config["schedule"] = None
    config = AppConfig.model_validate(user_config)
    anytime_ms = make_ms("Monday", "11:00")
    assert config.scheduled(anytime_ms) is True

# name_to_alt
# ===========
def test_name_to_alt(user_config):
    """Test that "anchor_alt" correctly parses into name, server, and inherits region"""
    user_config["region"] = "EU"
    user_config["anchor_alt"] = "Guccigank-Thrall"
    config = AppConfig.model_validate(user_config)

    assert config.anchor_alt.name == "Guccigank"
    assert config.anchor_alt.server == "Thrall"
    assert config.anchor_alt.region == "EU"

# import_alts
# ===========
def test_import_alts(user_config):
    """Test that alts in has_alts also correctly inherit the top-level region."""
    user_config["region"] = "KR"
    user_config["has_alts"] = {"Stiff-Area52": ["Darkrat-Area52", "Darkbark-Area52"]}
    config = AppConfig.model_validate(user_config)

    alts_list = config.has_alts["Stiff-Area52"]
    assert len(alts_list) == 2
    assert isinstance(alts_list[0], AltConfig)
    assert alts_list[0].name == "Darkrat"
    assert alts_list[0].region == "KR"

# check_region
# ============
def test_check_region_valid(user_config):
    """Test that valid regions are accepted and normalized to uppercase."""
    for region in ["us", "Eu", "CN"]:
        user_config["region"] = region
        config = AppConfig.model_validate(user_config)
        assert config.region == region.upper()

def test_check_region_invalid(user_config):
    """Test that an invalid region raises a ValidationError."""
    user_config["region"] = "OCE"
    with pytest.raises(ValidationError) as error:
        AppConfig.model_validate(user_config)
    assert "invalid region" in str(error)

# check_zone
# ==========
def test_check_zone_valid(user_config):
    """Test that a valid zone_id is accepted."""
    user_config["zone_id"] = 35
    config = AppConfig.model_validate(user_config)
    assert config.zone_id == 35

def test_check_zone_invalid(user_config):
    """Test that an invalid zone_id raises a ValidationError."""
    user_config["zone_id"] = 999
    with pytest.raises(ValidationError) as error:
        AppConfig.model_validate(user_config)
    assert "invalid zone_id" in str(error)

# properties
# ==========
# raid
# ====
def test_raid_config(valid_config):
    """Test that config.raid returns the correct dictionary from constants.py."""
    assert valid_config.raid == RAIDS[valid_config.zone_id]

# cache_path
# ============
def test_cache_path(valid_config):
    """Test that config.cache_path generates the correct nested path."""
    path = Path(".cache") / str(valid_config.guild_id) / str(valid_config.zone_id)
    assert valid_config.cache_path == path
