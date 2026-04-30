from fastapi.testclient import TestClient

from apps.backend.main import app
from services.llm import create_llm_client
from services.llm import OllamaClient


def test_chat_endpoint_creates_quote_from_message() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"message": "Recommend products and create a quote for SF-OPP-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["oracle_quote_id"] == "ORA-Q-001-001"
    assert "Created draft quote ORA-Q-001-001" in body["message"]
    assert body["pricing"]["total"] == 1572500.0
    assert [product["sku"] for product in body["products"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]


def test_chat_endpoint_accepts_explicit_opportunity_id() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Recommend products and create a quote",
            "sf_opportunity_id": "SF-OPP-001",
        },
    )

    assert response.status_code == 200
    assert response.json()["oracle_quote_id"] == "ORA-Q-001-001"


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(app)

    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_endpoint_returns_400_for_unknown_opportunity() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Recommend products and create a quote",
            "sf_opportunity_id": "SF-OPP-404",
        },
    )

    assert response.status_code == 400


def test_backend_uses_fallback_response_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert create_llm_client() is None


def test_backend_can_enable_ollama_llm_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")

    llm_client = create_llm_client()

    assert isinstance(llm_client, OllamaClient)
    assert llm_client.base_url == "http://ollama.test"
    llm_client.close()


def test_recommendation_endpoint_prepares_products_for_review() -> None:
    client = TestClient(app)

    response = client.post(
        "/quote/recommendations",
        json={
            "sf_opportunity_id": "SF-OPP-001",
            "message": "Recommend NetApp products for telecom 5G edge storage.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready_for_review"
    assert body["opportunity"]["account"]["name"] == "Northstar Telecom"
    assert body["products"][0]["sku"] == "NTAP-AFF-A-SERIES"
    assert body["pricing"]["total"] == 1572500.0
    assert body["run_steps"][0]["layer"] == "Agent"


def test_account_and_opportunity_endpoints_support_portfolio_flow() -> None:
    client = TestClient(app)

    accounts = client.get("/accounts")
    opportunities = client.get("/opportunities", params={"sf_account_id": "SF-ACC-001"})

    assert accounts.status_code == 200
    assert accounts.json()["accounts"][0]["name"] == "Northstar Telecom"
    assert opportunities.status_code == 200
    assert [item["sf_opportunity_id"] for item in opportunities.json()["opportunities"]] == [
        "SF-OPP-002",
        "SF-OPP-001",
        "SF-OPP-003",
    ]


def test_pricing_endpoint_reprices_selected_products() -> None:
    client = TestClient(app)
    recommendation = client.post(
        "/quote/recommendations",
        json={"sf_opportunity_id": "SF-OPP-001"},
    ).json()
    products = recommendation["products"]
    products[1]["selected"] = False

    response = client.post(
        "/quote/pricing",
        json={
            "sf_opportunity_id": "SF-OPP-001",
            "currency": "USD",
            "products": products,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "priced"
    assert "NTAP-ASA-A-SERIES" not in [
        item["sku"] for item in body["pricing"]["line_items"]
    ]
    assert body["pricing"]["total"] < recommendation["pricing"]["total"]


def test_quote_create_endpoint_creates_quote_from_selection() -> None:
    client = TestClient(app)
    recommendation = client.post(
        "/quote/recommendations",
        json={"sf_opportunity_id": "SF-OPP-001"},
    ).json()

    response = client.post(
        "/quote/create",
        json={
            "sf_opportunity_id": "SF-OPP-001",
            "currency": "USD",
            "products": recommendation["products"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["oracle_quote_id"] == "ORA-Q-001-001"
    assert body["quote"]["selected_product_count"] == 7


def test_quote_history_and_finalize_endpoints_place_order() -> None:
    client = TestClient(app)
    recommendation = client.post(
        "/quote/recommendations",
        json={"sf_opportunity_id": "SF-OPP-001"},
    ).json()
    created = client.post(
        "/quote/create",
        json={
            "sf_opportunity_id": "SF-OPP-001",
            "currency": "USD",
            "products": recommendation["products"],
        },
    ).json()

    history = client.get("/opportunities/SF-OPP-001/quotes")
    finalized = client.post(
        "/quote/finalize",
        json={"oracle_quote_id": created["oracle_quote_id"]},
    )

    assert history.status_code == 200
    assert created["oracle_quote_id"] in [
        quote["oracle_quote_id"] for quote in history.json()["quotes"]
    ]
    assert finalized.status_code == 200
    assert finalized.json()["status"] == "order_placed"
    assert finalized.json()["order"]["oracle_quote_id"] == created["oracle_quote_id"]

    order = client.get(f"/orders/{finalized.json()['order']['oracle_order_id']}")

    assert order.status_code == 200
    assert order.json()["oracle_quote_id"] == created["oracle_quote_id"]


def test_agent_run_history_endpoints_capture_business_actions() -> None:
    client = TestClient(app)

    client.post(
        "/quote/recommendations",
        json={"sf_opportunity_id": "SF-OPP-001"},
    )

    history = client.get("/agent-runs", params={"sf_opportunity_id": "SF-OPP-001"})

    assert history.status_code == 200
    run = history.json()["runs"][0]
    assert run["intent"] == "recommendation"
    assert run["sf_opportunity_id"] == "SF-OPP-001"
    assert run["step_count"] == 5

    detail = client.get(f"/agent-runs/{run['run_id']}")

    assert detail.status_code == 200
    assert [step["id"] for step in detail.json()["steps"]] == [
        "analyze",
        "retrieve_context",
        "get_opportunity",
        "recommend_products",
        "get_pricing",
    ]
