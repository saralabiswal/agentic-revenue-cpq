from fastapi.testclient import TestClient

from apps.backend.main import app


def test_opportunity_to_quote_integration_flow() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Recommend products and create a quote for SF-OPP-001",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert body["message"] == (
        "Created draft quote ORA-Q-001-001 for USD 1572500.0."
    )
    assert body["oracle_quote_id"] == "ORA-Q-001-001"
    assert [product["sku"] for product in body["products"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]
    assert body["pricing"]["subtotal"] == 1850000.0
    assert body["pricing"]["discount"] == 277500.0
    assert body["pricing"]["total"] == 1572500.0
