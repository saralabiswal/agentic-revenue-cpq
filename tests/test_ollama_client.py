import json

import httpx
import pytest

from services.llm import OllamaClient, OllamaClientError


def test_ollama_client_posts_chat_request_and_returns_message() -> None:
    captured_payload: dict | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content)

        assert request.method == "POST"
        assert str(request.url) == "http://ollama.test/api/chat"

        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "Quote draft is ready.",
                }
            },
        )

    client = OllamaClient(
        model="quote-model",
        base_url="http://ollama.test/",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.chat(
        [
            {
                "role": "user",
                "content": "Recommend products and create a quote",
            }
        ]
    )

    assert captured_payload == {
        "model": "quote-model",
        "messages": [
            {
                "role": "user",
                "content": "Recommend products and create a quote",
            }
        ],
        "stream": False,
    }
    assert response == {
        "role": "assistant",
        "content": "Quote draft is ready.",
    }


def test_ollama_client_raises_for_missing_message() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    client = OllamaClient(
        base_url="http://ollama.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OllamaClientError, match="did not include a message"):
        client.chat([{"role": "user", "content": "Hello"}])


def test_ollama_client_raises_for_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model failed"})

    client = OllamaClient(
        base_url="http://ollama.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.chat([{"role": "user", "content": "Hello"}])
