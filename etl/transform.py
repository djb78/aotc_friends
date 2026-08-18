from services.config import on_schedule
from services.cache import load_cache
from etl.constants import FIGHTS_CACHE_NAME, PLAYERS_CACHE_NAME, ROLE_NAMES
from etl.parser import safe_get, parse_fights, parse_players
from etl.models import Pull, Alt

class Transformer:
    def __init__(self, config: dict):
        self.config = config
        self.log_times = {}  # { code: time }
        self.pulls = []      # [ Pulls ]
        self.alts = {}    # { guid: Alt }

    def transform_all(self):
        """ coordinator for preping fights and characters for the load phase
            filter raw list of codes for raid_day matches
            exclude logs after the AOTC kill
            populate pulls and characters dictionaries

            parse_players() = { "code": [ {player_role_info} ] }
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

        print("- building alt dictionary")
        self.transform_pulls_alts()
        print(f"    - logs:     {len(self.log_times)}")
        print(f"    - pulls:    {len(self.pulls)}")
        if len(self.pulls) > 0:
            pull = self.pulls[0]
            print(f"    - sample roster: {pull.roster}")
        print(f"    - alts:  {len(self.alts)}")

        print("transform phase complete")

    def transform_fights_pulls(self):
        """ filter log times based on config schedule
            use filtered log codes to
            populate self.pulls with info from fights 

            log_fights { code:
            log { "time": , "zone", "fights": [
            fight {"id": , "kill": , "friendlyPlayers", ... }
        """
        # get dictionary of fight logs
        # log_fights = { log_code: log }
        fights_json = load_cache(self.config, FIGHTS_CACHE_NAME)
        fight_logs = parse_fights(fights_json)
        if not fight_logs or not isinstance(fight_logs, dict):
            raise ValueError(f"missing fight data, parser returned {fight_logs}")

        config_zone = safe_get(self.config, ["zone_id"])
        schedule = safe_get(self.config, ["schedule"])
        for code, log  in fight_logs.items():
            # log = { "time": time, "zone_id": id, "fights": [{fights_info}] } }

            # raid filter
            log_zone = safe_get(log, ["zone_id"])
            if log_zone != config_zone:
                continue

            # schedule filter
            if schedule and not on_schedule(log["time"], schedule):
                continue

            # store filtered timestamp
            self.log_times[code] = log["time"]

            # use fights dictionary to create Pull objects
            # [ { "id":, "kill":, ... } ]
            for fight in log["fights"]:
                # difficulty filter
                if fight["difficulty"] != 4:
                    continue
                pull = Pull(code, fight["id"])
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

    def transform_pulls_alts(self):
        """ use the base roster of log specific player ids to
            create a guid roster to replace it.

            acquire guid from self.update_alt to 
            populate/update self.alts

            increment sightings for each alt confirmed

            report - log_players:        { code: 
            player_ids:                  { id: 
            fights - alt_sightings:   [ 
            sighting:                    {"guid", "role", "specs", ...
        """
        # { log_code: { player_id: [ {spec_sighting}, {},  ] }
        players_json = load_cache(self.config, PLAYERS_CACHE_NAME)
        parsed_data = parse_players(players_json)

        for pull in self.pulls:
            log_data = parsed_data.get(pull.log, {})
            
            guid_roster = []        # create list of unique guids
            id_roster = pull.roster # use list of log specific player ids
            if not isinstance(id_roster, list):
                continue
            # use player_ids to count alt sightings
            for player_id in id_roster:
                # { code: { id: 
                player_seen = log_data.get(player_id)
                if not isinstance(player_seen, list):
                    continue

                # ensure alt info is represented in self.alts
                guid = None
                for spec_sighting in player_seen:
                    # { "guid", "name", "role", "specs": [ {"spec", "count"} ], ... }
                    guid = self.update_alt(pull.log, spec_sighting)
                if not guid or not guid in self.alts:
                    continue

                # increment alt.sightings
                self.alts[guid].sightings += 1
                # add guid to new pull roster
                guid_roster.append(guid)

            # update pull roster to list of guids
            pull.roster = guid_roster

    def update_alt(self, code: str, sighting: dict) -> int:
        """ Add new alt and/or spec info to self.alts
            return alt guid or None if inputs are invalid
            invalid spec info is skipped
            
            sighting = {"guid", "name", ..., "role", "specs": [ {"spec", "count"} ]}
        """
        if not isinstance(sighting, dict) or code not in self.log_times:
            return None
        guid_seen = sighting.get("guid")
        if not guid_seen: return None

        # ensure alt exists
        if guid_seen not in self.alts:
            alt_seen = Alt(guid_seen)
            alt_seen.name = sighting.get("name")
            alt_seen.server = sighting.get("server")
            alt_seen.region = sighting.get("region")
            alt_seen.type = sighting.get("type")
            alt_seen.sightings = 0
            alt_seen.specs = {}   # { spec: { "role": role, "counts": { code: count }
            self.alts[guid_seen] = alt_seen
        alt = self.alts[guid_seen]

        # update existing alt spec info
        specs_seen = sighting.get("specs", [])   # [ {"spec", "count"} ]
        if not isinstance(specs_seen, list):
            # guid still spotted and self.alts[guid] exists
            specs_seen = [] 

        for seen_spec in specs_seen:  # {"spec", "count"}
            # skip missing/bad info for update, alt was still spotted
            if not isinstance(seen_spec, dict) or "spec" not in seen_spec:
                continue

            spec_name = seen_spec.get("spec")
            spec_count = seen_spec.get("count")
            if not spec_count or not isinstance(spec_count, int):
                continue

            # ensure spec exists
            if spec_name not in alt.specs:
                role_seen = sighting.get("role")
                role_name = ROLE_NAMES.get(role_seen, role_seen)
                alt.specs[spec_name] = { "role": role_name, "log_counts": {}}
            alt_spec = alt.specs[spec_name]   # { "role": role, "log_counts": { code: count }

            # add count to log_counts (should always be the same)
            if code not in alt_spec["log_counts"]:
                alt_spec["log_counts"][code] = spec_count

        # verify alt exists in self.alts
        return alt.guid

