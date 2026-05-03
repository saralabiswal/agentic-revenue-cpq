# LangGraph Workflow Diagrams

This document explains the main LangGraph workflows used by the Enterprise AI Agent Platform.

Use the Markdown/Mermaid version for GitHub-friendly documentation. Use
[`langgraph-workflow-diagram.html`](langgraph-workflow-diagram.html) for a
browser-rendered SVG version that does not depend on Mermaid support.

## Full Chat-To-Quote Graph

This is built by `build_agent_graph()` in `services/agent/graph.py`.

```mermaid
flowchart LR
    START_NODE([START])
    ANALYZE[analyze<br/>_analyze_intent]
    RETRIEVE[retrieve_context<br/>_retrieve_context]
    GET_OPP[get_opportunity<br/>_get_opportunity]
    RECOMMEND[recommend_products<br/>_recommend_products]
    PRICE[get_pricing<br/>_get_pricing]
    CREATE[create_quote<br/>_create_quote]
    RESPOND[respond<br/>_respond]
    END_NODE([END])

    START_NODE --> ANALYZE
    ANALYZE --> RETRIEVE
    RETRIEVE --> GET_OPP
    GET_OPP --> RECOMMEND
    RECOMMEND --> PRICE
    PRICE --> CREATE
    CREATE --> RESPOND
    RESPOND --> END_NODE

    RETRIEVE -. MCP tool .-> SEARCH_TOOL[search_knowledge]
    GET_OPP -. MCP tool .-> OPP_TOOL[get_opportunity]
    RECOMMEND -. MCP tool .-> REC_TOOL[recommend_products]
    PRICE -. MCP tool .-> PRICE_TOOL[get_pricing]
    CREATE -. MCP tool .-> QUOTE_TOOL[create_quote]
```

### What Each Node Does

| Graph node | Function | Main job |
| --- | --- | --- |
| `analyze` | `_analyze_intent` | Extract user input and selected Salesforce opportunity id into graph state. |
| `retrieve_context` | `_retrieve_context` | Optionally retrieve RAG knowledge snippets through MCP. |
| `get_opportunity` | `_get_opportunity` | Load Salesforce opportunity data through MCP. |
| `recommend_products` | `_recommend_products` | Ask CPQ recommendation logic for products through MCP. |
| `get_pricing` | `_get_pricing` | Ask CPQ pricing logic for line items, discounts, and totals through MCP. |
| `create_quote` | `_create_quote` | Create a CPQ quote through MCP. |
| `respond` | `_respond` | Build the final user-facing response using an LLM client or fallback message. |

## Recommendation-Only Graph

This is built by `build_recommendation_graph()`.

```mermaid
flowchart TD
    START_NODE([START])
    ANALYZE[analyze]
    RETRIEVE[retrieve_context]
    GET_OPP[get_opportunity]
    RECOMMEND[recommend_products]
    PRICE[get_pricing]
    RESPOND[respond<br/>_respond_recommendation]
    END_NODE([END])

    START_NODE --> ANALYZE
    ANALYZE --> RETRIEVE
    RETRIEVE --> GET_OPP
    GET_OPP --> RECOMMEND
    RECOMMEND --> PRICE
    PRICE --> RESPOND
    RESPOND --> END_NODE
```

Use this when the sales rep wants recommended products and pricing for review, but has not created a quote yet.

## Pricing-Only Graph

This is built by `build_pricing_graph()`.

```mermaid
flowchart TD
    START_NODE([START])
    PREPARE[prepare_selection<br/>_prepare_selection_recommendation]
    PRICE[get_pricing<br/>_get_pricing]
    RESPOND[respond<br/>_respond_pricing]
    END_NODE([END])

    START_NODE --> PREPARE
    PREPARE --> PRICE
    PRICE --> RESPOND
    RESPOND --> END_NODE
```

Use this when the user has already selected products and only wants the current selection repriced.

## Quote-Creation Graph

This is built by `build_quote_creation_graph()`.

```mermaid
flowchart TD
    START_NODE([START])
    PREPARE[prepare_selection<br/>_prepare_selection_recommendation]
    PRICE[get_pricing<br/>_get_pricing]
    CREATE[create_quote<br/>_create_quote]
    RESPOND[respond<br/>_respond_quote_creation]
    END_NODE([END])

    START_NODE --> PREPARE
    PREPARE --> PRICE
    PRICE --> CREATE
    CREATE --> RESPOND
    RESPOND --> END_NODE
```

Use this when the sales rep has reviewed product selections and explicitly creates a persisted quote.

## Layer View

```mermaid
flowchart LR
    UI[Next.js UI]
    API[FastAPI Backend]
    GRAPH[LangGraph Workflow]
    MCP[MCPExecutionEngine]
    TOOLS[Tool Handlers]
    SF[Salesforce Mock]
    CPQ[Oracle CPQ Mock]
    RAG[RAG Retriever]
    DB[(SQLite)]
    CHROMA[(ChromaDB)]

    UI --> API
    API --> GRAPH
    GRAPH --> MCP
    MCP --> TOOLS
    TOOLS --> SF
    TOOLS --> CPQ
    TOOLS --> RAG
    TOOLS --> DB
    RAG --> CHROMA
```
