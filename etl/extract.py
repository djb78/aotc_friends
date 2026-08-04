from services.file_io import save_cache, load_cache
from etl.constants import CODES_CACHE_NAME, FIGHTS_CACHE_NAME, PLAYERS_CACHE_NAME
from etl.parser import parse_unique_codes, parse_fight_ids, safe_get

class Extractor:
    def __init__(self, client, config: dict):
        self.client = client
        self.config = config
        self.chunk_size = config.get("chunk_size", 10)

    def extract_query(self, query: str, cache_name: str):
        """ wrapper for querying API and saving to cache """
        response = self.client.query(query)
        save_cache(self.config, cache_name, response)

    def extract_all(self):
        """ coordinator for extraction pipeline """
        print("starting extraction phase")
        self.extract_codes()
        self.extract_fights()
        self.extract_players()
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

    def extract_players(self):
        """ uses codes and ids from extract_fights cache 
            extracts and caches playerDetails

            query format (multi-aliased, chunked):
                query { reportData {
                    report0: report(code: <code0>) {
                        playerDetails(fightIDs=[<id1>, <id2>, ...])
                    },
                    report1: report(code: <code1>) { ... }, ...
                }}
        """
        # check for existing cache
        if load_cache(self.config, PLAYERS_CACHE_NAME):
            return

        # losd the cache created by extract_fights
        fights_json = load_cache(self.config, FIGHTS_CACHE_NAME)
        if not fights_json:
            return 
        # retrieve codes and fight ids
        code_ids = parse_fight_ids(fights_json)
        if not isinstance(code_ids, dict):
            return

        # create chunks
        # default self.chunk_size = 10
        unchunked = list(code_ids.items())
        chunks = [ unchunked[i:i+self.chunk_size] 
                  for i in range(0, len(unchunked), self.chunk_size)]

        # collect responses to chunk queryies
        chunk_responses = {}
        for i, chunk in enumerate(chunks):
            # construct multi-aliased GraphQL query
            query = "query { reportData { "
            for j, (code, ids) in enumerate(chunk):
                query += f"report{i}_{j}: report(code: \"{code}\") {{ "
                query += "code "
                query += "playerDetails(fightIDs: ["
                query += ", ".join(map(str, ids))
                query += "]) "
                query += "} "
            query += "} } "

            # query API and add response to chunk_responses
            chunk_response = self.client.query(query)
            chunk_reports = safe_get(chunk_response, ["data", "reportData"])
            if isinstance(chunk_reports, dict):
                chunk_responses.update(chunk_reports)

        # cache merged chunk responses
        merged_response = {"data": {"reportData": chunk_responses}}
        save_cache(self.config, PLAYERS_CACHE_NAME, merged_response)