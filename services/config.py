import zoneinfo
from datetime import time, datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional
from domain.constants import RAIDS

class AltConfig(BaseModel):
    name: str
    server: str
    region: str

class ScheduleConfig(BaseModel):
    days: set[int]
    start_est: time
    end_est: time

    @field_validator("days", mode="before")
    @classmethod
    def days_to_int(cls, v):
        """convert day names to weekday integers (monday=1)"""
        if not isinstance(v, (list, set)):
            raise ValueError("days must be a list/set of day names/numbers(1=mon)")

        day_nums = {
            "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
            "friday": 5, "saturday": 6, "sunday":7
        }
        day_int_set = set()
        for day in v:
            if type(day) is int and day in range(1, 8):
                day_int_set.add(day)
                continue
            if not isinstance(day, str):
                raise ValueError(f"days must be strings, not {type(day)}")
            day_lower = day.strip().lower()
            if day_lower not in day_nums:
                raise ValueError(f"invalid day name: {day}")
            day_int_set.add(day_nums[day_lower])
        return day_int_set

    def includes(self, time_ms: int)->bool:
        """ check if a schedule-duration block of time 
            starting at time_ms overlaps with a 
            scheduled time block
        """
        if not time_ms:
            return False
        
        est = zoneinfo.ZoneInfo("America/New_York")
        time_dt = datetime.fromtimestamp(time_ms / 1000.0, tz=est)

        time_2k = datetime.combine(datetime(2000, 1, 1).date(), time_dt.time())
        start_2k = datetime.combine(datetime(2000, 1, 1).date(), self.start_est)
        end_2k = datetime.combine(datetime(2000, 1, 1).date(), self.end_est)

        log_day = time_dt.date()   # for scheduled day verification
 
        # Handle overnight schedules
        overnight = self.start_est > self.end_est       
        if overnight:
            end_2k += timedelta(days=1)
            # handle time after midnight
            if time_dt.time() < self.end_est:
                log_day -= timedelta(days=1)
                time_2k += timedelta(days=1)

        # verify scheduled day
        if log_day.isoweekday() not in self.days:
            return False

        # verify scheduled time overlap
        duration = end_2k - start_2k
        return ( time_2k < end_2k and (time_2k + duration) > start_2k )


class AppConfig(BaseModel):
    guild_name: Optional[str] = None
    guild_id: int
    region: str = "US"
    zone_id: int
    schedule: Optional[ScheduleConfig] = None
    anchor_alt: AltConfig
    has_alts: dict[str, list[AltConfig]] = Field(default_factory=dict)
    cache_root: Path = Field(default=Path(".cache"))
    chunk_size: int = 10

    @field_validator("region")
    @classmethod
    def check_region(cls, v: str) -> str:
        """confirm valid wow region"""
        v_upper = v.strip().upper()
        wow_regions = ["US", "EU", "KR", "TW", "CN"]
        if v_upper not in wow_regions:
            raise ValueError(f"invalid region '{v}'. Must be one of: {', '.join(wow_regions)}")
        return v_upper

    @field_validator("anchor_alt", mode="before")
    @classmethod
    def name_to_alt(cls, v: str, info: ValidationInfo) -> dict:
        """ convert name-server string into 
            AltConfig compatible dict
        """
        if not isinstance(v, str):
            return v
        if "-" not in v:
            raise ValueError(f"invalid name format: {v} != 'name-server'")
        name, server = v.split("-", maxsplit=1)
        region = info.data.get("region", "US")
        return {"name": name, "server": server, "region": region}

    @field_validator("has_alts", mode="before")
    @classmethod
    def import_alts(cls, v: dict, info: ValidationInfo):
        """validate main name format and convert alt list"""
        if not isinstance(v, dict):
            return {}
        imported = {}
        for main, alt_list in v.items():
            if not isinstance(main, str):
                raise ValueError(f"player name, {main} in config has_alts, is not a string")
            if not isinstance(alt_list, list):
                raise ValueError(f"alts for {main} must be a list of strings")
            imported[main] = [cls.name_to_alt(alt, info) for alt in alt_list]
        return imported

    @field_validator("zone_id")
    @classmethod
    def check_zone(cls, v):
        """make sure zone_id refers to a valid raid tier"""
        if v not in RAIDS:
            raise ValueError("invalid zone_id, see zone reference in README")
        return v

    @property
    def raid(self) -> dict:
        """get raid info from constants.py"""
        return RAIDS[self.zone_id]

    @property
    def cache_path(self) -> Path:
        """get dynamic/resolved path for API response cache"""
        return self.cache_root / str(self.guild_id) / str(self.zone_id)

    def scheduled(self, time_ms: int) -> bool:
        """check the schedule, true if no schedule"""
        if self.schedule is None:
            return True
        return self.schedule.includes(time_ms)
