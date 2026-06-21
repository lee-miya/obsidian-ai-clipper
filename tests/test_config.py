import os
from src.config import Settings

def test_settings_loads_api_keys():
    os.environ["API_KEYS"] = "key1,key2"
    os.environ["KIMI_API_KEY"] = "test-key"
    settings = Settings()
    assert settings.api_keys == ["key1", "key2"]
