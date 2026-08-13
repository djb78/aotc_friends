
class Pull:
    def __init__(self, code: str, id: int):
        self.log = code
        self.id = id
        self.boss = {}      # { "id": encounterID, "name": name }
        self.kill = False
        self.roster = []    # list of guids

