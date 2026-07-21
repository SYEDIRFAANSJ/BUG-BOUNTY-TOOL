import pytest
from recon.tagger import tag_endpoint, calculate_priority

def test_open_redirect_tag():
    endpoint = {"url": "https://example.com/login?redirect=https://evil.com", "params": {"redirect": "1"}}
    tags = tag_endpoint(endpoint)
    assert "open_redirect" in tags

def test_ssrf_tag():
    endpoint = {"url": "https://example.com/api?webhook=http://test.com", "params": {"webhook": "1"}}
    tags = tag_endpoint(endpoint)
    assert "ssrf" in tags

def test_idor_tag():
    endpoint = {"url": "https://example.com/user?user_id=123", "params": {"user_id": "123"}}
    tags = tag_endpoint(endpoint)
    assert "idor" in tags

def test_file_upload_tag():
    endpoint = {"url": "https://example.com/upload/image", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "file_upload_rce" in tags

def test_sqli_tag():
    endpoint = {"url": "https://example.com/search?q=test", "params": {"search": "test", "id": "1"}}
    tags = tag_endpoint(endpoint)
    assert "sqli_candidate" in tags

def test_xxe_tag():
    endpoint = {"url": "https://example.com/api/xml", "content_type": "application/xml", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "xxe" in tags

def test_graphql_tag():
    endpoint = {"url": "https://example.com/graphql", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "graphql_introspection" in tags

def test_admin_panel_tag():
    endpoint = {"url": "https://example.com/admin/login", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "auth_bypass_candidate" in tags

def test_cors_tag():
    endpoint = {"url": "https://api.example.com/v1/users", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "cors_misconfig" in tags

def test_jwt_tag():
    endpoint = {"url": "https://example.com/api?token=abc", "params": {"token": "abc"}}
    tags = tag_endpoint(endpoint)
    assert "jwt_vuln_candidate" in tags

def test_lfi_tag():
    endpoint = {"url": "https://example.com/page?file=index.html", "params": {"file": "index.html"}}
    tags = tag_endpoint(endpoint)
    assert "lfi_candidate" in tags

def test_exposed_git_tag():
    endpoint = {"url": "https://example.com/.git/config", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "source_disclosure" in tags

def test_exposed_env_tag():
    endpoint = {"url": "https://example.com/.env", "params": {}}
    tags = tag_endpoint(endpoint)
    assert "secret_exposure" in tags

def test_risk_priority_highest():
    tags = ["sqli_candidate", "cors_misconfig"]
    priority = calculate_priority(tags)
    assert priority == "high"

def test_multiple_tags():
    endpoint = {"url": "https://example.com/admin/upload?webhook=test&user_id=1", "params": {"webhook": "test", "user_id": "1"}}
    tags = tag_endpoint(endpoint)
    assert "auth_bypass_candidate" in tags
    assert "file_upload_rce" in tags
    assert "ssrf" in tags
    assert "idor" in tags

def test_no_match():
    endpoint = {"url": "https://example.com/index.html", "params": {}}
    tags = tag_endpoint(endpoint)
    assert len(tags) == 0
    assert calculate_priority(tags) == "low"
