
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
        self.main = guid            # default to self main
