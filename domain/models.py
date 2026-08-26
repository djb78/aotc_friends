from domain.constants import ROLE_NAMES

class Pull:
    def __init__(self, code: str, id: int):
        self.log = code
        self.id = id
        self.boss = {}      # { "id": encounterID, "name": name }
        self.kill = False
        self.roster = []    # list of guids

    @classmethod
    def from_fight(cls, code: str, fight: dict)->"Pull":
        """ factory method
            create a Pull object from parsed fight data
        """
        pull = cls(code, fight["id"])
        pull.kill = fight["kill"]
        pull.boss["id"] = fight["encounterID"]
        pull.boss["name"] = fight["name"]
        pull.roster = fight["friendlyPlayers"]
        return pull


class Alt:
    """ a specific alt/character """
    def __init__(self, guid: int):
        self.guid = guid
        self.name: str = ""
        self.server: str = ""
        self.region = ""
        self.type: str = ""  # class
        self.specs = {}
        self.sightings = 0

    @classmethod
    def from_player(cls, guid, player):
        """ factory method
            create an Alt object from parsed player data
        """
        new_alt = cls(guid)
        new_alt.name = player.get("name")
        new_alt.server = player.get("server")
        new_alt.region = player.get("region")
        new_alt.type = player.get("type")   # { spec: { "role": role, "counts": { code: count }
        return new_alt

    def update_specs(self, code: str, player: dict):
        """ update spec counts with player_data from a specific log code 
            player["specs"] = [{"spec": "spec name", "count": count}]
            self.specs = {
                str: {  # spec name
                    "name": str, # spec name
                    "role": str, # "tank", "healer", "dps"
                    "sightings": int,   # sum of all log counts
                    "log_counts": {str: int} }} # { code: count }
        """
        specs = player.get("specs", [])   # [ {"spec": spec_name, "count": count} ]
        if not isinstance(specs, list):
            return 

        for count_data in specs:  # {"spec", "count"}
            # skip missing/bad info
            if not isinstance(count_data, dict) or "spec" not in count_data:
                continue

            spec_name = count_data.get("spec")
            spec_count = count_data.get("count")
            if not spec_count or not isinstance(spec_count, int):
                continue

            # ensure spec exists
            if spec_name not in self.specs:
                role_seen = player.get("role")
                role_name = ROLE_NAMES.get(role_seen, role_seen)
                self.specs[spec_name] = { "role": role_name, "log_counts": {}}

            # set log_count for code on first sighting
            if code not in self.specs[spec_name]["log_counts"]:
                self.specs[spec_name]["log_counts"][code] = spec_count

    def sort_specs(self)->dict:
        """ calculate overall spec sightings and 
            arrange specs from most to least sightings
        """
        if not self.specs or not isinstance(self.specs, dict):
            return
        # calculate total spec sightings
        for spec_info in self.specs.values():
            log_counts = spec_info.get("log_counts", {})
            spec_info["sightings"] = sum(count for count in log_counts.values() 
                                            if isinstance(count, int))
        # sort by sightings highest to lowest
        spec_preference = sorted(self.specs.items(), 
                                    key=lambda item: item[1].get("sightings", 0), 
                                    reverse=True)
        self.specs = dict(spec_preference)
       

class Friend:
    """ collection of all a players known alts """
    def __init__(self, alts: list):
        self.alts = sorted(alts, key=lambda a: a.sightings, reverse=True)
        self.sightings = sum(a.sightings for a in alts)
        self.main = self.alts[0] if self.alts else None