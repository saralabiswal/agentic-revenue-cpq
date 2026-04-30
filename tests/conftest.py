import pytest

from services.data import reset_business_data


@pytest.fixture(autouse=True)
def reset_mock_business_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BUSINESS_DB_PATH", str(tmp_path / "business.sqlite3"))
    reset_business_data()
    yield
    reset_business_data()
