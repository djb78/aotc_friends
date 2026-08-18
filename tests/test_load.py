import pytest
from pathlib import Path
from etl.load import Loader

def test_sort_friends(valid_config, sample_friends):
    """ sort friends by sightings, fallback to fav_spec """
    l = Loader(valid_config, sample_friends)
    order = l.sort_friends()

    assert order[0].sightings == 30
    assert order[0].main.name == "Guccigank"
    assert order[1].main.name == "Udderlymad"
    assert order[2].main.name == "Hopeseller"

def test_to_markdown(valid_config, sample_friends):
    """ generates correctly formatted markdown """
    l = Loader(valid_config, sample_friends)
    order = l.sort_friends()
    md = l.to_markdown(order)

    assert "# The Secret Duck Society" in md
    assert "**Udderlymad** | 22" in md
    assert "  12 | Udderlymad-Ursin | DeathKnight" in md
    assert "  10 | Anonymoose-Ursin | Guardian | Druid" in md

    assert "**Guccigank** | 30" in md
    assert "18 Subtlety - 12 Assassination" in md

    assert "**Hopeseller**" not in md
    assert "  5 | Hopeseller-Area52 | Arcane | Mage"


def test_save_output(tmp_path, valid_config, sample_friends):
    """ writes markdown file to disk """
    l = Loader(valid_config, sample_friends)
    test_file = tmp_path / "test_friends.md"

    l.save_output("# Test Report", path=str(test_file))

    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "# Test Report"
