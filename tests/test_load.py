import pytest
from etl.load import Loader
from domain.models import Alt, Friend

def test_sort_friends(valid_config, sample_friends):
    """ sort friends by sightings, fallback to fav_spec """
    l = Loader(valid_config, sample_friends)
    order = l.sort_friends()

    assert order[0].sightings == 25
    assert order[0].main.name == "alt1"
    assert order[1].main.name == "alt3"
    assert order[2].main.name == "alt2"

def test_to_markdown(valid_config, sample_friends):
    """ generates correctly formatted markdown """
    l = Loader(valid_config, sample_friends)
    order = l.sort_friends()
    md = l.to_markdown(order)

    assert "# The Secret Duck Society" in md
    assert "**alt3** | 22" in md
    assert "  12 | alt3-Server | class" in md
    assert "  10 | alt4-Server | spec1 | class" in md

    assert "**alt1** | 25" in md
    assert "13 spec2 - 12 spec1" in md

    assert "**alt2**" not in md
    assert "5 | alt2-Server | spec1 | class" in md

@pytest.fixture
def sample_friends():
    """ list of sample friend objects """
    alt1 = Alt(1)
    alt1.name = "alt1"
    alt1.server = "Server"
    alt1.type = "class"
    alt1.sightings = 25
    alt1.specs =  {
        "spec1": {"role": "DPS", "log_counts": {"log1": 12}},
        "spec2": {"role": "DPS", "log_counts": {"log1": 13}}
    }
    alt1.sort_specs()
    friend1 = Friend([alt1])

    alt2 = Alt(2)
    alt2.name = "alt2"
    alt2.server = "Server"
    alt2.type = "class"
    alt2.sightings = 5
    alt2.specs = {"spec1": {"role": "DPS", "log_counts": {"log1": 5}}}
    alt2.sort_specs()
    friend2 = Friend([alt2])

    alt3 = Alt(3)
    alt3.name = "alt3"
    alt3.server = "Server"
    alt3.type = "class"
    alt3.sightings = 12
    alt3.specs = {}
    alt3.sort_specs()

    alt4 = Alt(4)
    alt4.name = "alt4"
    alt4.server = "Server"
    alt4.type = "class"
    alt4.sightings = 10
    alt4.specs = {"spec1": {"role": "Tank", "log_counts": {"log1": 10}}}
    alt4.sort_specs()
    friend3 = Friend([alt3, alt4])

    return [friend1, friend2, friend3]
