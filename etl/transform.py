from services.file_io import load_fights, load_players
from etl.parse import safe_get, parse_fights, parse_players
from domain.constants import ROLE_NAMES
from domain.models import Pull, Alt, Friend
from domain.schema import AppConfig

class Transformer:
    def __init__(self, config: AppConfig):
        self.config = config
        self.log_times = {}  # { code: time }
        self.pulls = []      # [ Pulls ]
        self.alts = {}    # { guid: Alt }
        self.friends = [] # [ Friends ]

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

        print("- deriving friend stats")
        self.transform_alts_friends()
        print(f"    - friends: {len(self.friends)}")

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
        fights_json = load_fights(self.config)
        fight_logs = parse_fights(fights_json)
        if not fight_logs or not isinstance(fight_logs, dict):
            raise ValueError(f"missing fight data, parser returned {fight_logs}")
        
        for code, log  in fight_logs.items():
            # log = { "time": time, "zone_id": id, "fights": [{fights_info}] } }

            # raid filter
            log_zone = safe_get(log, ["zone_id"])
            if log_zone != self.config.zone_id:
                continue

            # schedule filter
            if not self.config.scheduled(log["time"]):
                continue

            # store filtered timestamp
            self.log_times[code] = log["time"]

            # use fights dictionary to create Pull objects
            # [ { "id":, "kill":, ... } ]
            for fight in log["fights"]:
                # difficulty filter
                if fight["difficulty"] != 4:
                    continue
                pull = Pull.from_fight(code, fight)
                self.pulls.append(pull)

    def filter_aotc_prog(self):
        """ determine final boss kill log
            filter out subseqent logs/pulls
        """
        # get boss for kill cutoff
        final_boss_id = safe_get(self.config.raid, ["final_boss", "id"], None)
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
            
            input:
            parsed_data {
                # parsed_report
                code: {  
                    # player_id   
                    id: [
                        # player
                        {"guid": int, "role": str, "specs": [], ...}
                    ]
                }
            }
            # list of pre-filtered Pull objects with player_id rosters
            self.pulls
        """
        # { log_code: { player_id: [ {player}, {},  ] }
        players_json = load_players(self.config)
        parsed_data = parse_players(players_json)

        for pull in self.pulls:
            id_roster = pull.roster 
            if not isinstance(id_roster, list):
                continue
            guid_roster = []

            parsed_report = parsed_data.get(pull.log, {})
            for player_id in id_roster:
                # { code: { id: 
                player_data = parsed_report.get(player_id)
                if not isinstance(player_data, list):
                    continue

                # ensure alt info is represented in self.alts
                guid = None
                for player in player_data:
                    guid = self.update_alt(pull.log, player)
                if not guid or not guid in self.alts:
                    continue

                # increment alt.sightings
                self.alts[guid].sightings += 1
                # add guid to new pull roster
                guid_roster.append(guid)

            # update pull roster to list of guids
            pull.roster = guid_roster

    def update_alt(self, code: str, player: dict):
        """ Add new alt and/or spec info to self.alts
            return alt guid or None if inputs are invalid
            invalid spec info is skipped
            
            player = {"guid", "name", ..., "role", "specs": [ {"spec", "count"} ]}
        """
        if not isinstance(player, dict) or code not in self.log_times:
            return None
        
        guid = player.get("guid")
        if not guid: 
            return None

        # ensure alt exists
        if guid not in self.alts:
            self.alts[guid] = Alt.from_player(guid, player)

        alt = self.alts[guid]
        # update spec counts
        alt.update_specs(code, player)
        # verify alt exists in self.alts
        return alt.guid


    def name_to_guid(self, name_server: str)->int:
        """ find the guid for a name-server string in self.alts  """
        if not isinstance(name_server, str) or "-" not in name_server:
            raise ValueError(f"invalid format: {name_server} != 'name-server'")
        [name, server] = name_server.split("-", maxsplit=1)
        for guid, alt in self.alts.items():
            if alt.name == name and alt.server == server:
                return guid
        return 0


    def transform_alts_friends(self):
        """ guids all in one place for the first time
            clean up alt data
            group related alts (config "has_alts")
            use groups of alts to create friends (list of groups)
        """
        # sort specs to determine main
        for alt in self.alts.values():
            alt.sort_specs()

        # Friend = group of all known player alts
        # default: every alt is a part of it's own friend group
        friend_groups = {guid: {guid} for guid in self.alts}
        # if alts are defined in config, combine them into one group
        for main_name, alts in self.config.has_alts.items():
            alt_names = [f"{alt.name}-{alt.server}" for alt in alts]
            main_guid = self.name_to_guid(main_name)
            if not main_guid:
                # still group alts if main not present
                alt_guids = set()
            else:
                # add main to group
                alt_guids = friend_groups[main_guid]
            for alt_name in alt_names:
                # add alts to group
                alt_guid = self.name_to_guid(alt_name)
                if not alt_guid:
                    continue
                alt_guids.update(friend_groups[alt_guid])
            # copy group to all alts
            for guid in alt_guids:
                friend_groups[guid] = alt_guids

        # remove duplicate groups
        unique_groups = set(frozenset(group) for group in friend_groups.values())
        self.friends = []
        for group in unique_groups:
            unique_alts = [self.alts[guid] for guid in group]
            self.friends.append(Friend(unique_alts))
