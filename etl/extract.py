from services.file_io import save_codes, load_codes, save_fights, load_fights, save_players, load_players
from domain.schema import AppConfig, AltConfig
from etl.parse import parse_unique_codes, parse_fight_ids, safe_get

class Extractor:
    def __init__(self, client, config: AppConfig):
        self.client = client
        self.config = config
        self.chunk_size = config.chunk_size


    def chunk_list(self, unchunked: list) -> list[list]:
        """ turns a list into chunk_size chunks """
        if not unchunked or not isinstance(unchunked, list):
            return []
        return [unchunked[i:i + self.chunk_size] 
                for i in range(0, len(unchunked), self.chunk_size)]


    def extract_all(self):
        """ coordinator for extraction pipeline """
        print("starting extraction phase")
        print(" extracting codes...")
        self.extract_codes()
        print(" extracting fight data...")
        self.extract_fights()
        print(" extracting player data...")
        self.extract_players()
        print("extraction phase complete")

    def extract_codes(self):
        """ uses config data to extract and cache report codes
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
        if load_codes(self.config):
            print(f"    cache exists, extraction aborted.")
            return 

        # use config data to construct GraphQL query
        query = "query { "

        # Guild Report Codes
        query += "reportData { reports( "
        query += f"guildID: {self.config.guild_id}, "
        query += f"zoneID: {self.config.zone_id}) {{"
        query += "data { code } "
        query += "} }"

        # anchor_alt Report Codes
        query += "characterData{ character( "
        query += f"name: \"{self.config.anchor_alt.name}\", "
        query += f"serverSlug: \"{self.config.anchor_alt.server}\", "
        query += f"serverRegion: \"{self.config.anchor_alt.region}\") {{ "
        query += "recentReports(limit: 100) { data { code } } "
        query += "} } "
        
        query += "}"	

        # query API and cache response
        response = self.client.query(query)
        save_codes(self.config, response)
        print(f"    extraction complete, saved to cache")

    def extract_fights(self):
        """ uses codes from extract_codes cache
            extracts and caches fight information 
            
            query format (multi-aliased, chunked):
                query { reportData { 
                    ch0_r0: report(code: <code>) {
                        code
                        startTime
                        zone { id }
                        fights(difficulty: 4) { <fight_data> }
                    },
                    ch0_r1: report(code: <code>) { ... }, ... 
                }}
        """
        fight_data = """
            id
            encounterID
            name
            kill
            friendlyPlayers
            difficulty
        """
        # check for existing fight info cache
        if load_fights(self.config):
            print(f"    cache exists, extraction aborted.")
            return

        # load the cache created by extract_codes
        codes_json = load_codes(self.config)
        if not codes_json:
            return
        # retrieve list of codes
        codes = parse_unique_codes(codes_json)
        if not isinstance(codes, list):
            return
        # chunk data to avoid complexity limits
        chunks = self.chunk_list(codes)
        # extract chunk responses
        chunk_responses = {}
        for i, chunk in enumerate(chunks):

            # construct multi-aliased GraphQL query
            query = "query { reportData { " 
            for j, code in enumerate(chunk):
                query += f"ch{i}_r{j}: report(code: \"{code}\") {{ "
                query += "code "
                query += "zone { id }"
                query += "startTime "
                query += f"fights(difficulty: 4) {{ {fight_data} }} "
                query += "} "
            query += "} } "

            # query API and add response to chunk_responses
            chunk_response = self.client.query(query)
            chunk_reports = safe_get(chunk_response, ["data", "reportData"])
            if isinstance(chunk_reports, dict):
                chunk_responses.update(chunk_reports)

        # cache merged chunk responses
        merged_response = {"data": {"reportData": chunk_responses}}
        save_fights(self.config, merged_response)
        print(f"    extraction complete, saved to cache")


    def extract_players(self):
        """ uses codes and ids from extract_fights cache 
            extracts and caches playerDetails

            query format (multi-aliased, chunked):
                query { reportData {
                    ch0_r0: report(code: <code0>) {
                        playerDetails(fightIDs=[<id1>, <id2>, ...])
                    },
                    ch0_r1: report(code: <code1>) { ... }, ...
                }}
        """
        # check for existing cache
        if load_players(self.config):
            print(f"    cache exists, extraction aborted.")
            return

        # losd the cache created by extract_fights
        fights_json = load_fights(self.config)
        if not fights_json:
            return 
        # retrieve codes and fight ids
        fight_ids = parse_fight_ids(fights_json)
        if not isinstance(fight_ids, dict):
            return

        # create chunks
        chunks = self.chunk_list(list(fight_ids.items()))
        
        # collect responses to chunk queryies
        chunk_responses = {}
        for i, chunk in enumerate(chunks):
            # construct multi-aliased GraphQL query
            query = "query { reportData { "
            for j, (code, ids) in enumerate(chunk):
                query += f"ch{i}_r{j}: report(code: \"{code}\") {{ "
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
        save_players(self.config, merged_response)
        print(f"    extraction complete, saved to cache")