from services.config import on_schedule
from services.cache import load_cache
from etl.models import Pull
from etl.constants import FIGHTS_CACHE_NAME, PLAYERS_CACHE_NAME
from etl.parser import safe_get, parse_fights, parse_players

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
        self.filter_aotc_prog()
        print(f"    - logs:     {len(self.log_times)}")
        print(f"    - pulls:    {len(self.pulls)}")
        if len(self.pulls) > 0:
            pull = self.pulls[0]
            print(f"    - sample roster: {pull.roster}")

        print("- building friend dictionary")
        self.transform_roster()
        print(f"    - logs:     {len(self.log_times)}")
        print(f"    - pulls:    {len(self.pulls)}")
        if len(self.pulls) > 0:
            pull = self.pulls[0]
            print(f"    - sample roster: {pull.roster}")

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

    def filter_aotc_prog(self):
        """ determine final boss kill log
            filter out subseqent logs/pulls
        """
        # get boss for kill cutoff
        final_boss_id = safe_get(self.config, ["raid", "final_boss", "id"], None)
        if not final_boss_id:
            return
        
        # find the first kill (cutoff)
        cutoff = None
        for pull in self.pulls:
            if pull.boss["id"] != final_boss_id or not pull.kill:
                continue
            if (not cutoff or 
                self.log_times[pull.log] < self.log_times[cutoff]):
                    cutoff = pull.log
        if not cutoff:
            return

        # reconstruct log_times and pulls to reflect cutoff
        cutoff_time = self.log_times[cutoff]
        self.log_times = {
            code: time for code, time in self.log_times.items()
            if time <= cutoff_time
        }
        self.pulls = [
            pull for pull in self.pulls
            if pull.log in self.log_times
        ]

    def transform_roster(self):
        """ use the base roster of log specific player ids to
            create a guid roster to replace it.

            acquire guid from self.friend_spotted to 
            populate/update self.friends

            report - log_players:        { code: 
            player_ids:                  { id: 
            fights - friend_sightings:   [ 
            sighting:                    {"guid", "role", "specs", ...
        """
        # { "code": { "id": [ {player_role_info} ] }
        players_json = load_cache(self.config, PLAYERS_CACHE_NAME)
        log_players = parse_players(players_json)

        for pull in self.pulls:
            # use list of log specific player ids
            player_ids = pull.roster
            if not isinstance(player_ids, list):
                continue
            # create list of unique guids
            guid_roster = []
            missing_id_lists = 0
            for id in player_ids:
                # { code: { id: 
                # friend_sightings = safe_get(log_players, [pull.log, id], None)
                log_data = log_players.get(pull.log, [])
                friend_sightings = log_data.get(id, log_data.get(str(id), None))
                if not isinstance(friend_sightings, list):
                    missing_id_lists += 1
                    continue
                # [
                for sighting in friend_sightings:
                    # { "guid", "name", "role", "specs"[ {"spec", "count"} ], ... }
                    # update self.friends and get guid
                    guid = sighting.get("guid")
                    if guid and guid not in guid_roster:
                        # add guid to new list
                        guid_roster.append(guid)
            # update pull roster to list of guids
            pull.roster = guid_roster

