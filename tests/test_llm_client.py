"""Test coverage for llm client behavior.

Author: Sarala Biswal
"""

import pytest

from services.llm import LLMClient


class EchoLLMClient(LLMClient):
    """Verify echo l l m client behavior."""
    def chat(self, messages: list[dict]) -> dict:
        """Run the full chat-driven opportunity-to-quote workflow."""
        return {
            "role": "assistant",
            "content": messages[-1]["content"],
        }


def test_llm_client_requires_chat_implementation() -> None:
    """Verify llm client requires chat implementation behavior."""
    with pytest.raises(TypeError):
        LLMClient()


def test_llm_client_subclass_returns_response_dict() -> None:
    """Verify llm client subclass returns response dict behavior."""
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
