# Logical Architecture Diagram

Author: Sarala Biswal

![Cloud-agnostic logical architecture](../assets/logical-architecture.png)

This diagram shows the stable cloud-agnostic architecture:

- `AgentOrchestrator` owns orchestration and can be implemented by LangGraph, native Python, or future provider-managed adapters.
- MCP remains the execution boundary for tools, RAG, and integration access.
- RAG remains reachable only through MCP `search_knowledge`.
- LLM reasoning remains behind `LLMClient`.
- Provider selection is controlled by backend deployment configuration, not the frontend.
- Local, OCI, GCP, and generic Kubernetes provider profiles map infrastructure without changing API payloads or source-owned identifiers.

Regenerate the image with:

```bash
swift scripts/generate_logical_architecture_diagram.swift
```
