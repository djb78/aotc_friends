from services.config import on_schedule
from services.cache import load_cache
from etl.constants import FIGHTS_CACHE_NAME
from etl.parser import parse_fights
from etl.models import Pull

class Transformer:
    def __init__(self, config: dict):
        self.config = config
        self.log_times = {}  # { code: time }
        self.pulls = []      # [ Pulls ]

    def transform_all(self):
        """ coordinator for preping fights and characters for the load phase
            filter raw list of codes for raid_day matches
            exclude logs after the AOTC kill
            populate pulls and characters dictionaries

        """
        print("starting transform phase")
        print("- getting scheduled logs and building pull list")
        self.transform_fights_pulls()
        print(f"    - logs:     {len(self.log_times)}")
        print(f"    - pulls:    {len(self.pulls)}")
        print("- removing logs after aotc kill cutoff")
        print("- building friend dictionary")
        print("transform phase complete")

    def transform_fights_pulls(self):
        """ filter log times based on config schedule
            use filtered log codes to
            populate self.pulls with info from fights 

            log_fights { code:
            log { "time": , "fights": [
            fight {"id": , "kill": , "friendlyPlayers", ... }
        """
        # get dictionary of fight logs
        # log_fights = { log_code: log }
        fights_json = load_cache(self.config, FIGHTS_CACHE_NAME)
        log_fights = parse_fights(fights_json)

        schedule = self.config.get("schedule", None)
        for log_code, log  in log_fights.items():
            # log = { "time": time, "fights": [{fights_info}] } }
            # filter for logs that coincide with schedule
            if schedule and not on_schedule(log["time"], schedule):
                continue
            # store timestamp
            self.log_times[log_code] = log["time"]

            # use fights dictionary to create Pull objects
            # [ { "id":, "kill":, ... } ]
            for fight in log["fights"]:
                pull = Pull(log_code, fight["id"])
                pull.kill = fight["kill"]
                pull.boss["id"] = fight["encounterID"]
                pull.boss["name"] = fight["name"]
                pull.roster = fight["friendlyPlayers"]
                self.pulls.append(pull)
