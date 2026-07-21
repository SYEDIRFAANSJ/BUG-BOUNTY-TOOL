import pytest
from recon.pipeline_guard import verify_in_scope, ReconAbortedError
from unittest.mock import MagicMock

def test_recon_aborts_on_out_of_scope():
    mock_db = MagicMock()
    mock_scope = MagicMock()
    mock_scope.in_scope = False
    mock_db.query().filter_by().first.return_value = mock_scope

    with pytest.raises(ReconAbortedError):
        verify_in_scope(mock_db, target="example.com")

def test_recon_proceeds_on_in_scope():
    mock_db = MagicMock()
    mock_scope = MagicMock()
    mock_scope.in_scope = True
    mock_db.query().filter_by().first.return_value = mock_scope

    # Should not raise
    verify_in_scope(mock_db, target="example.com")
