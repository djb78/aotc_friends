
class Pull:
    def __init__(self, code: str, id: int):
        self.log = code
        self.id = id
        self.boss = {}      # { "id": encounterID, "name": name }
        self.kill = False
        self.roster = []    # list of guids

class Alt:
    """ a specific alt/character """
    def __init__(self, guid: int):
        self.guid = guid
        self.name: str = ""
        self.server: str = ""
        self.region = ""
        self.type: str = ""  # class
        self.specs = { 
            str: {  # spec name
                "name": str, # spec name
                "role": str, # "tank", "healer", "dps"
                "sightings": int,   # sum of all log counts
                "log_counts": {str: int} }} # { code: count }
        self.sightings = 0

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