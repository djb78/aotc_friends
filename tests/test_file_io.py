from services.file_io import save_cache, load_cache

# cache
def test_save_load_cache(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path

    cache_name = "test_reports"
    test_data = {"reports": [{'code': "ABC123XYZ"}]}

    save_cache(config, cache_name, test_data)

    expected_file = config.cache_path / f"{cache_name}.json"
    assert expected_file.exists()

    loaded_data = load_cache(config, cache_name)
    assert loaded_data == test_data

def test_load_cache_missing(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path
    assert load_cache(config, "not_here") == {}

def test_load_cache_corrupted(tmp_path, valid_config):
    config = valid_config
    config.cache_root = tmp_path
    config.cache_path.mkdir(parents=True, exist_ok=True)

    corrupted_file = config.cache_path / "bad_cache.json"
    with corrupted_file.open("w", encoding="utf-8") as f:
        f.write("{ invalid json: 123 }")

    assert load_cache(config, "bad_cache") == {}