import pytest
from src.utils.url import validate_public_url

def test_valid_https_url():
    assert validate_public_url("https://example.com") == "https://example.com"

def test_rejects_localhost():
    with pytest.raises(ValueError):
        validate_public_url("http://localhost:8000")

def test_rejects_private_ip():
    with pytest.raises(ValueError):
        validate_public_url("http://192.168.1.1")

def test_rejects_non_http_protocol():
    with pytest.raises(ValueError):
        validate_public_url("ftp://example.com")
