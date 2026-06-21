import pytest
from src.core.security import verify_api_key

def test_valid_key():
    assert verify_api_key("Bearer valid-key", ["valid-key"]) == "valid-key"

def test_missing_header():
    with pytest.raises(ValueError):
        verify_api_key(None, ["valid-key"])

def test_invalid_key():
    with pytest.raises(ValueError):
        verify_api_key("Bearer wrong-key", ["valid-key"])
