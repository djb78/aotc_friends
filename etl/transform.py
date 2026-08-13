
class Transformer:
    def __init__(self, config: dict):
        self.config = config

    def transform_all(self):
        """ coordinator for preping fights and characters for the load phase
            filter raw list of codes for raid_day matches
            exclude logs after the AOTC kill
            populate pulls and characters dictionaries

        """
        print("starting transform phase")
        print("- getting scheduled logs and building pull list")
        print("- removing logs after aotc kill cutoff")
        print("- building friend dictionary")
        print("transform phase complete")
