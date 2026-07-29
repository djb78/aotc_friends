import pytest

@pytest.fixture
def valid_config():
    """Provides a fresh, valid configuration dictionary for tests"""
    return {
        "zone_id": 35,
        "guild_id": 123456,
        "anchor": {
            "name": "Stiff",
            "server": "area-52",
            "region": "US"
        }
    }