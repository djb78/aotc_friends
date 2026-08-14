
class Pull:
    def __init__(self, code: str, id: int):
        self.log = code
        self.id = id
        self.boss = {}      # { "id": encounterID, "name": name }
        self.kill = False
        self.roster = []    # list of guids

class Friend:
    def __init__(self, guid: int):
        self.guid = guid
        self.name: str = ""
        self.server: str = ""
        self.region: str = ""
        self.type: str = ""         # class
        self.specs = {}             # { spec: { "role": role, "counts": { code: count }
        self.sightings = 0
        self.main = guid            # default to self main
