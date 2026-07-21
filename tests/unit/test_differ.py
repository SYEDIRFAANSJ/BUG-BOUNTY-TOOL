import pytest
from monitor.differ import compute_scope_hash, diff_scopes

def test_compute_scope_hash_deterministic():
    scope1 = [{"target": "a.com"}, {"target": "b.com"}]
    scope2 = [{"target": "b.com"}, {"target": "a.com"}]
    assert compute_scope_hash(scope1) == compute_scope_hash(scope2)

def test_compute_scope_hash_different_data():
    scope1 = [{"target": "a.com"}]
    scope2 = [{"target": "b.com"}]
    assert compute_scope_hash(scope1) != compute_scope_hash(scope2)

def test_diff_new_program():
    new_scope = [{"target": "a.com"}]
    diff = diff_scopes([], new_scope)
    assert diff["type"] == "new"
    assert len(diff["added"]) == 1
    assert len(diff["removed"]) == 0

def test_diff_unchanged():
    old_scope = [{"target": "a.com"}]
    new_scope = [{"target": "a.com"}]
    diff = diff_scopes(old_scope, new_scope)
    assert diff["type"] == "unchanged"

def test_diff_scope_changed():
    old_scope = [{"target": "a.com"}, {"target": "b.com"}]
    new_scope = [{"target": "b.com"}, {"target": "c.com"}]
    diff = diff_scopes(old_scope, new_scope)
    assert diff["type"] == "scope_changed"
    assert "a.com" in [s["target"] for s in diff["removed"]]
    assert "c.com" in [s["target"] for s in diff["added"]]
