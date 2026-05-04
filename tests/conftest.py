"""Test coverage for conftest behavior.

Author: Sarala Biswal
"""

import pytest

from services.data import reset_business_data


@pytest.fixture(autouse=True)
def reset_mock_business_data(tmp_path, monkeypatch) -> None:
    """Verify reset mock business data behavior."""
    monkeypatch.setenv("BUSINESS_DB_PATH", str(tmp_path / "business.sqlite3"))
    reset_business_data()
    yield
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.setenv("BUSINESS_STORE_PROVIDER", "sqlite")
    reset_business_data()
