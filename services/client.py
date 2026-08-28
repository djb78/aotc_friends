import os, requests, logging

logger = logging.getLogger(__name__)

class WCLClient:
    def __init__(self):
        self.client_id = os.getenv("WCL_CLIENT_ID")
        self.client_secret = os.getenv("WCL_CLIENT_SECRET")
        self.token_url = "https://www.warcraftlogs.com/oauth/token"
        self.api_url = "https://www.warcraftlogs.com/api/v2/client"
        self.access_token = None

        if not self.client_id or not self.client_secret:
            raise ValueError("Please set WCL ClientID and Client Secret in .env")

    def fetch_token(self):
        logger.debug("Fetching OAuth2 access token...")
        response = requests.post(
            self.token_url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret)
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to retrieve access token: {response.status_code} - {response.text}"
            )

        self.access_token = response.json().get("access_token")

    def query(self, query_str: str, variables: dict=None) -> dict:
        if not self.access_token:
            self.fetch_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = { "query": query_str.strip() }
        if variables:
            payload["variables"] = variables

        logger.debug("sending api query (length: %d chars)...", len(query_str))

        response = requests.post(self.api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Query failed with status code {response.status_code} - {response.text}")

        return response.json()