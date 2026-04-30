import pytest

from services.llm import LLMClient


class EchoLLMClient(LLMClient):
    def chat(self, messages: list[dict]) -> dict:
        return {
            "role": "assistant",
            "content": messages[-1]["content"],
        }


def test_llm_client_requires_chat_implementation() -> None:
    with pytest.raises(TypeError):
        LLMClient()


def test_llm_client_subclass_returns_response_dict() -> None:
    client = EchoLLMClient()

    response = client.chat(
        [
            {
                "role": "user",
                "content": "Recommend products and create a quote",
            }
        ]
    )

    assert response == {
        "role": "assistant",
        "content": "Recommend products and create a quote",
    }
