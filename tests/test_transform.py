import pytest

@pytest.fixture
def mock_codes_json():
    """sample JSON response"""
    return {
        "data": {
            "reportData": {
                "reports": {
                    "data": [{"code": "GuildRprt"}]
                }
            }
        }
    }