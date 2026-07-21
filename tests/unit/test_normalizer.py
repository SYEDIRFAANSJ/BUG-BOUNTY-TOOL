import pytest
from scope_parser.normalizer import detect_scope_type, normalize_scope_item, is_in_scope

def test_detect_wildcard_domain():
    assert detect_scope_type("*.example.com") == "wildcard_domain"
    assert detect_scope_type("*.api.example.com") == "wildcard_domain"

def test_detect_domain():
    assert detect_scope_type("example.com") == "domain"
    assert detect_scope_type("api.example.com") == "domain"

def test_detect_ip():
    assert detect_scope_type("192.168.1.1") == "ip"
    assert detect_scope_type("10.0.0.1") == "ip"

def test_detect_ip_range():
    assert detect_scope_type("10.0.0.0/24") == "ip_range"
    assert detect_scope_type("192.168.1.0/16") == "ip_range"

def test_detect_android():
    assert detect_scope_type("com.example.app.apk") == "android"

def test_detect_ios():
    assert detect_scope_type("com.example.app.ipa") == "ios"

def test_detect_api():
    assert detect_scope_type("https://example.com/api/v1") == "api"

def test_detect_other():
    assert detect_scope_type("something random") == "other"

def test_normalize_hackerone_scope_item():
    item = {
        "asset_identifier": "*.example.com",
        "instruction": "Test this domain.",
        "max_severity": "high",
        "eligible_for_submission": True,
        "eligible_for_bounty": True
    }
    normalized = normalize_scope_item(item, "hackerone")
    assert normalized["target"] == "*.example.com"
    assert normalized["type"] == "wildcard_domain"
    assert normalized["instruction"] == "Test this domain."
    assert normalized["in_scope"] == True

def test_normalize_bugcrowd_scope_item():
    item = {
        "target": "example.com",
        "category": "domain",
        "tags": ["bounty"],
        "in_scope": True
    }
    normalized = normalize_scope_item(item, "bugcrowd")
    assert normalized["target"] == "example.com"
    assert normalized["type"] == "domain"
    assert normalized["in_scope"] == True

def test_in_scope_from_platform_flag():
    # Only checks if the in_scope flag works securely
    assert is_in_scope(True) is True
    assert is_in_scope(False) is False
    assert is_in_scope("True") is True
    assert is_in_scope("False") is False
    assert is_in_scope(1) is True
    assert is_in_scope(0) is False
    assert is_in_scope("yes") is True
    assert is_in_scope("no") is False
