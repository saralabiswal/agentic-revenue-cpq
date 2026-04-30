import logging

from services.mcp.registry import ToolInput, ToolOutput, ToolRegistry


class ToolExecutionError(RuntimeError):
    """Raised when a registered MCP tool cannot be executed cleanly."""


class MCPExecutionEngine:
    def __init__(
        self,
        registry: ToolRegistry,
        logger: logging.Logger | None = None,
    ) -> None:
        self._registry = registry
        self._logger = logger or logging.getLogger(__name__)

    def execute(self, tool_name: str, payload: ToolInput | None = None) -> ToolOutput:
        tool_payload = payload or {}
        if not isinstance(tool_payload, dict):
            raise ToolExecutionError("Tool payload must be a dictionary.")

        tool = self._registry.get(tool_name)
        payload_keys = sorted(tool_payload.keys())
        self._logger.info(
            "Executing MCP tool: %s payload_keys=%s",
            tool.name,
            payload_keys,
        )

        try:
            result = tool.handler(tool_payload)
        except Exception as exc:
            self._logger.exception(
                "MCP tool failed: %s payload_keys=%s",
                tool.name,
                payload_keys,
            )
            raise ToolExecutionError(f"Tool execution failed: {tool.name}") from exc

        if not isinstance(result, dict):
            self._logger.error(
                "MCP tool returned invalid result: %s result_type=%s",
                tool.name,
                type(result).__name__,
            )
            raise ToolExecutionError("Tool result must be a dictionary.")

        self._logger.info(
            "MCP tool completed: %s result_keys=%s",
            tool.name,
            sorted(result.keys()),
        )
        return result
