from services.file_io import save_cache, load_cache
from etl.constants import CODES_CACHE_NAME, FIGHTS_CACHE_NAME
from etl.parser import parse_unique_codes

class Extractor:
    def __init__(self, client, config: dict):
        self.client = client
        self.config = config

    def extract_query(self, query: str, cache_name: str):
        """ wrapper for querying API and saving to cache """
        response = self.client.query(query)
        save_cache(self.config, cache_name, response)

    def extract_all(self):
        """ coordinator for extraction pipeline """
        print("starting extraction phase")
        self.extract_codes()
        self.extract_fights()
        print("extraction phase complete")

    def extract_codes(self):
        """ uses config data to extract and cache report codes
            requires valid config data
                guild_id
                zone_id
                anchor(name, server, region)

            query format:
                query { 
                reportData { reports(guildID: guild_id, zoneID: zone_id) { 
                    data: { code }
                }}
                characterData { character(name: name, serverSlug: server, serverRegion: region) {
                    recentReports(limit:100) { data { code } }
                    zoneRankings(zoneID: zone_id, difficulty: 4)
                }}
                }
        """
        # check for existing cache
        if load_cache(self.config, CODES_CACHE_NAME):
            return 

        # use config data to construct GraphQL query
        query = "query { "

        # Guild Report Codes
        query += "reportData { reports( "
        query += f"guildID: {self.config['guild_id']}, "
        query += f"zoneID: {self.config['zone_id']}){{"
        query += "data { code } }"
        query += "} "

        # Anchor Character Report Codes & zoneRankings
        query += "characterData{ character( "
        query += f"name: \"{self.config['anchor']['name']}\", "
        query += f"serverSlug: \"{self.config['anchor']['server']}\", "
        query += f"serverRegion: \"{self.config['anchor']['region']}\"){{ "
        query += "recentReports(limit: 100) { data { code } } "
        query += f"zoneRankings(zoneID: {self.config['zone_id']}, difficulty: 4)"
        query += "} } "
        
        query += "}"	

        # query API and cache response       
        self.extract_query(query, CODES_CACHE_NAME)

    def extract_fights(self):
        """ uses codes from extract_codes cache
            extracts and caches fight information 
            
            query format (multi-aliased):
                query { reportData { 
                    report0: report(code: <code>) {
                        code
                        fights(difficulty: 4) { id name kill friendlyPlayers }
                    },
                    report1: report(code: <code>) { ... }, ... 
                }}
        """
        # check for existing fight info cache
        if load_cache(self.config, FIGHTS_CACHE_NAME):
            return

        # load the cache created by extract_codes
        codes_json = load_cache(self.config, CODES_CACHE_NAME)
        if not codes_json:
            return
        # retrieve list of codes
        codes = parse_unique_codes(codes_json)

        # use codes to construct multi-aliased GraphQL query
        query = "query { reportData { " 
        for i, code in enumerate(codes):
            query += f"report{i}: report(code: \"{code}\") {{ "
            query += "code "
            query += "fights(difficulty: 4) { id name kill friendlyPlayers } "
            query += "} "
        query += "}}"

        # query API and cache response
        self.extract_query(query, FIGHTS_CACHE_NAME)