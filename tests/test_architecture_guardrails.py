"""Test coverage for architecture guardrails behavior.

Author: Sarala Biswal
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_agent_does_not_import_integrations_directly() -> None:
    """Verify agent does not import integrations directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "from integrations" not in source
        assert "import integrations" not in source


def test_agent_does_not_call_llm_providers_directly() -> None:
    """Verify agent does not call llm providers directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "OllamaClient" not in source
        assert "httpx" not in source
        assert "/api/chat" not in source


def test_agent_does_not_import_rag_directly() -> None:
    """Verify agent does not import rag directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "from services.rag" not in source
        assert "import services.rag" not in source
        assert "chromadb" not in source
        assert "/api/embeddings" not in source


def test_backend_routes_through_agent_not_tools_or_integrations() -> None:
    """Verify backend routes through agent not tools or integrations behavior."""
    source = (PROJECT_ROOT / "apps" / "backend" / "main.py").read_text()

    assert "from services.agent" in source
    assert "from integrations" not in source
    assert "from services.tools" not in source
    assert "OllamaClient" not in source


def test_tool_wrappers_are_the_integration_boundary() -> None:
    """Verify tool wrappers are the integration boundary behavior."""
    source = (PROJECT_ROOT / "services" / "tools" / "opportunity_quote.py").read_text()

    assert "from integrations.cpq" in source
    assert "from integrations.salesforce" in source
    assert "ToolDefinition" in source


def test_rag_is_exposed_only_through_mcp_tool() -> None:
    """Verify rag is exposed only through mcp tool behavior."""
    source = (PROJECT_ROOT / "services" / "mcp" / "tools" / "rag_tools.py").read_text()

    assert "from services.rag" in source
    assert 'name="search_knowledge"' in source
