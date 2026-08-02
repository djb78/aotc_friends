from services.file_io import save_cache, load_cache
from etl.constants import CODES_CACHE_NAME, FIGHTS_CACHE_NAME
from etl.parser import parse_unique_codes

class Extractor:
    def __init__(self, client, config: dict):
        self.client = client
        self.config = config

    def extract_query(self,  query: str, cache_name: str):
        response = self.client.query(query)
        save_cache(self.config, cache_name, response)

    def extract_all(self):
        """ coordinator for extraction pipeline """
        print("starting extraction phase")
        self.extract_codes()
        self.extract_fights()
        print("extraction phase complete")

    def extract_codes(self):
        if load_cache(self.config, CODES_CACHE_NAME):
            return 

        query = "query { "

        # Guild Report Codes
        query += "reportData { reports( "
        query += f"guildID: {self.config['guild_id']}, "
        query += f"zoneID: {self.config['zone_id']}){{"
        query += "data { code } }"
        query += "} "

        # Anchor Character Report Codes & Ranks
        query += "characterData{ character( "
        query += f"name: \"{self.config['anchor']['name']}\", "
        query += f"serverSlug: \"{self.config['anchor']['server']}\", "
        query += f"serverRegion: \"{self.config['anchor']['region']}\"){{ "
        query += "recentReports(limit: 100) { data { code } } "
        query += f"zoneRankings(zoneID: {self.config['zone_id']}, difficulty: 4)"
        query += "} } "
        
        query += "}"	
                
        self.extract_query(query, CODES_CACHE_NAME)

    def extract_fights(self):
        """query wcl for each reports fight/player details"""
        if load_cache(self.config, FIGHTS_CACHE_NAME):
            return

        codes_json = load_cache(self.config, CODES_CACHE_NAME)
        if not codes_json:
            return
        codes = parse_unique_codes(codes_json)

        query = "query { reportData { " 
        for i, code in enumerate(codes):
            query += f"report{i}: report(code: \"{code}\") {{ "
            query += "code "
            query += "fights(difficulty: 4) { id name kill friendlyPlayers } "
            query += "} "
        query += "}}"

        self.extract_query(query, FIGHTS_CACHE_NAME)