from services.file_io import save_cache, load_cache
from services.client import WCLClient

class Extractor:
    def __init__(self, client, config: dict):
        self.client = client
        self.config = config

    def extract_query(self,  query: str, cache_name: str):
        response = self.client.query(query)
        save_cache(self.config, cache_name, response)

    def extract_codes(self):
        cache_name = "codes_and_zoneranks"
        if load_cache(self.config, cache_name):
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
                
        self.extract_query(query, cache_name)