# OCI Deployment Architecture

This document maps the current Enterprise AI Agent Platform codebase to a target Oracle Cloud Infrastructure deployment.

## Recommended OCI Target

The first production-style OCI deployment should keep the project architecture intact:

- Keep Next.js as the frontend application.
- Keep FastAPI as the backend API.
- Keep LangGraph, MCP, and tool handlers inside the backend service.
- Replace local runtime stores and local Ollama with managed OCI services.
- Replace mock Salesforce and Oracle CPQ modules with real enterprise API integrations.

## High-Level Architecture

```mermaid
flowchart LR
    USER[Sales Rep Browser]
    DNS[OCI DNS / Public Endpoint]
    WAF[OCI WAF]
    LB[OCI Load Balancer]
    UI[Next.js Frontend<br/>OKE Service]
    APIGW[OCI API Gateway]
    API[FastAPI Backend<br/>OKE Service]

    subgraph BACKEND_CODE["Backend Container Code"]
        LG[LangGraph Workflows<br/>services/agent]
        MCP[MCPExecutionEngine<br/>services/mcp]
        TOOLS[Tool Handlers<br/>services/tools]
    end

    GENAI[OCI Generative AI<br/>chat + embeddings]
    ADB[(Autonomous Database<br/>business data + audit)]
    VDB[(Oracle Database 23ai<br/>AI Vector Search)]
    SF[Salesforce APIs]
    CPQ[Oracle CPQ APIs]
    VAULT[OCI Vault<br/>secrets + keys]
    LOG[OCI Logging]
    MON[OCI Monitoring<br/>alarms + metrics]

    USER --> DNS --> WAF --> LB --> UI
    UI --> APIGW --> API
    API --> LG --> MCP --> TOOLS
    TOOLS --> SF
    TOOLS --> CPQ
    TOOLS --> ADB
    TOOLS --> VDB
    API --> GENAI
    VDB --> GENAI
    API --> VAULT
    TOOLS --> VAULT
    API --> LOG
    API --> MON
```

## Build And Deploy Flow

```mermaid
flowchart LR
    GH[GitHub Repository]
    DEVOPS[OCI DevOps<br/>build pipeline]
    OCIR[OCI Container Registry]
    OKE[OCI Kubernetes Engine]
    FRONT[Frontend Pod]
    BACK[Backend Pod]

    GH --> DEVOPS
    DEVOPS --> OCIR
    OCIR --> OKE
    OKE --> FRONT
    OKE --> BACK
```

## Component Mapping

| Project component | Current local implementation | OCI target component | Notes |
| --- | --- | --- | --- |
| Frontend UI | `apps/frontend` Next.js container | OKE deployment behind OCI Load Balancer | Keep as containerized Next.js app. |
| Backend API | `apps/backend/main.py` FastAPI container | OKE deployment behind OCI API Gateway | API Gateway fronts backend routes and can add auth, throttling, CORS, and validation. |
| Container images | Local Docker build / Docker Compose | OCI Container Registry | Store frontend and backend container images in OCIR. |
| CI/CD | Manual local build or GitHub workflow later | OCI DevOps | Build, test, push images, and deploy to OKE. |
| Agent workflow | `services/agent/graph.py` LangGraph | Runs inside FastAPI backend pod | LangGraph remains application code, not an OCI service. |
| MCP boundary | `services/mcp` | Runs inside FastAPI backend pod | MCP remains the controlled tool execution boundary in code. |
| Business tools | `services/tools/opportunity_quote.py` | Runs inside FastAPI backend pod | Tool handlers call real services instead of mocks. |
| Salesforce mock | `integrations/salesforce/mock.py` | Salesforce REST APIs | Replace mock with real Salesforce integration and credentials from OCI Vault. |
| Oracle CPQ mock | `integrations/cpq/*` | Oracle CPQ / Fusion APIs | Replace mock CPQ logic with real CPQ APIs where available. |
| SQLite business DB | `app_data/business.sqlite3` | Autonomous Database Transaction Processing | Store accounts, opportunities, quotes, orders, activity, and agent runs. |
| ChromaDB vector DB | `chroma_db/` | Oracle Database 23ai AI Vector Search | Store embeddings with enterprise data using native vector search. |
| Ollama chat model | `ollama` Docker service | OCI Generative AI chat models | Replace `OllamaClient` with an OCI Generative AI client implementation. |
| Ollama embeddings | `nomic-embed-text` through Ollama | OCI Generative AI embeddings | Use managed embedding models for RAG ingestion/search. |
| Secrets | Local env vars | OCI Vault | Store Salesforce, CPQ, database, and AI service credentials. |
| Logs | Python logs / container output | OCI Logging | Centralize backend, OKE, API Gateway, and application logs. |
| Metrics and alarms | Local test output | OCI Monitoring | Track latency, errors, pod health, API metrics, and alarms. |
| Runtime files | Local volumes | Object Storage where needed | Use for exported artifacts, backups, and generated documents if needed. |

## Core Application Runtime: LangGraph And MCP

LangGraph and the MCP engine are not OCI-managed services in this architecture. They are Python application logic that should run inside the backend container.

The OCI decision is therefore not "which OCI service replaces LangGraph or MCP?" The decision is "which OCI compute service should host the backend container that runs LangGraph and MCP?"

```mermaid
flowchart TD
    CORE[Core Python Runtime<br/>LangGraph + MCP + Tool Handlers]

    CORE --> Q{How should the backend runtime be hosted?}

    Q --> OKE[Recommended<br/>OCI Kubernetes Engine]
    Q --> CI[Simple Alternative<br/>OCI Container Instances]
    Q --> FN[Limited Fit<br/>OCI Functions]
    Q --> VM[Fallback<br/>OCI Compute VM]

    OKE --> OKEWHY[Best fit for this project<br/>FastAPI service, frontend/backend containers,<br/>autoscaling, rolling deploys, private networking]
    CI --> CIWHY[Good for demo or small deployment<br/>run backend container without Kubernetes<br/>less orchestration control]
    FN --> FNWHY[Use for isolated event jobs only<br/>not ideal for long-lived FastAPI API service<br/>or full agent runtime]
    VM --> VMWHY[Works but more ops burden<br/>you manage OS, process supervisor,<br/>patching, scaling]
```

### Recommended Runtime Shape

```mermaid
flowchart LR
    APIGW[OCI API Gateway]

    subgraph OKE["OCI Kubernetes Engine"]
        SVC[backend Kubernetes Service]
        POD1[Backend Pod A<br/>FastAPI + LangGraph + MCP]
        POD2[Backend Pod B<br/>FastAPI + LangGraph + MCP]
        HPA[Horizontal Pod Autoscaler]
    end

    OCIR[OCI Container Registry]
    VAULT[OCI Vault]
    GENAI[OCI Generative AI]
    ADB[(Autonomous Database)]
    VDB[(Oracle DB 23ai Vector Search)]
    EXT[Salesforce / Oracle CPQ APIs]

    APIGW --> SVC
    SVC --> POD1
    SVC --> POD2
    HPA --> POD1
    HPA --> POD2
    OCIR --> POD1
    OCIR --> POD2
    POD1 --> VAULT
    POD2 --> VAULT
    POD1 --> GENAI
    POD2 --> GENAI
    POD1 --> ADB
    POD2 --> ADB
    POD1 --> VDB
    POD2 --> VDB
    POD1 --> EXT
    POD2 --> EXT
```

### What Runs Inside The Backend Pod

```mermaid
flowchart TB
    FASTAPI[FastAPI Routes<br/>apps/backend/main.py]

    subgraph POD["Backend Container / Pod"]
        FASTAPI --> GRAPH[LangGraph Workflows<br/>services/agent/graph.py]
        GRAPH --> MCP[MCPExecutionEngine<br/>services/mcp/engine.py]
        MCP --> REG[ToolRegistry<br/>services/mcp/registry.py]
        MCP --> TOOLS[Tool Handlers<br/>services/tools/opportunity_quote.py]
    end

    TOOLS --> SF[Salesforce API Client]
    TOOLS --> CPQ[Oracle CPQ API Client]
    TOOLS --> DB[Autonomous DB Repository]
    TOOLS --> RAG[RAG Retriever / Vector Search]
    GRAPH --> LLM[OCI Generative AI Client]
```

### Component Choice For LangGraph

| Choice | Fit | Why |
| --- | --- | --- |
| Run inside FastAPI backend pod on OKE | Recommended | LangGraph is request-time orchestration code. It needs Python dependencies, internal state dictionaries, tool calls, logging, and predictable API latency. |
| Run as separate microservice | Possible later | Useful only if multiple backend services need to call the same agent runtime. Adds network and versioning complexity. |
| Run in OCI Functions | Usually not preferred | Better for isolated event handlers than a full always-available API orchestration service. |
| Replace with OCI Generative AI Agents | Optional future redesign | Would change the architecture. Current project already owns orchestration with LangGraph and MCP. |

### Component Choice For MCP Engine And Tools

| Choice | Fit | Why |
| --- | --- | --- |
| Run inside FastAPI backend pod on OKE | Recommended | MCP engine is an in-process control boundary. Keeping it with LangGraph avoids extra network hops and keeps tool execution auditable in one request trace. |
| Split each tool into a separate OCI Function | Possible for specific tools | Useful for long-running or independently scaled jobs, but adds invocation latency and distributed error handling. |
| Put MCP behind a separate internal API service | Possible later | Useful if many applications share the same governed tool layer. Adds operational complexity. |
| Replace MCP with direct integration calls | Not recommended | Removes the governance boundary that keeps the agent from directly calling Salesforce, CPQ, RAG, or database code. |

## Runtime Request Flow On OCI

```mermaid
sequenceDiagram
    participant U as Sales Rep Browser
    participant F as Next.js on OKE
    participant G as OCI API Gateway
    participant B as FastAPI on OKE
    participant L as LangGraph
    participant M as MCP Engine
    participant T as Tool Handlers
    participant A as Autonomous DB
    participant V as DB 23ai Vector Search
    participant AI as OCI Generative AI
    participant S as Salesforce
    participant C as Oracle CPQ

    U->>F: Select opportunity / request recommendation
    F->>G: POST /quote/recommendations
    G->>B: Route API request
    B->>L: Invoke recommendation graph
    L->>M: execute search_knowledge
    M->>T: RAG tool handler
    T->>AI: Create query embedding
    T->>V: Retrieve relevant knowledge
    L->>M: execute get_opportunity
    M->>T: Salesforce tool handler
    T->>S: Fetch opportunity
    L->>M: execute recommend_products
    M->>T: CPQ recommendation handler
    T->>C: Get recommended products
    L->>M: execute get_pricing
    M->>T: CPQ pricing handler
    T->>C: Price selected products
    B->>A: Record agent run and activity
    B->>F: Return products, pricing, trace
    F->>U: Display recommendation and explainability
```

## OCI Network Layout

```mermaid
flowchart TB
    INTERNET[Internet]

    subgraph VCN["OCI VCN"]
        subgraph PUBLIC["Public Subnet"]
            WAF2[WAF / Public Edge]
            LB2[Load Balancer]
            GW2[API Gateway]
        end

        subgraph PRIVATE_APP["Private App Subnet"]
            OKE2[OKE Worker Nodes / Virtual Nodes]
            FRONT2[Frontend Pods]
            BACK2[Backend Pods]
        end

        subgraph PRIVATE_DATA["Private Data Access"]
            ADB2[(Autonomous DB Private Endpoint)]
            VDB2[(Oracle DB 23ai / Vector Search)]
        end

        NAT[NAT Gateway]
        SG[Service Gateway]
    end

    OCI_SERVICES[OCI Services<br/>Generative AI, Vault, Logging, Monitoring, OCIR]
    EXT[External SaaS APIs<br/>Salesforce, Oracle CPQ]

    INTERNET --> WAF2 --> LB2 --> FRONT2
    FRONT2 --> GW2 --> BACK2
    BACK2 --> ADB2
    BACK2 --> VDB2
    BACK2 --> SG --> OCI_SERVICES
    BACK2 --> NAT --> EXT
```

## Migration Notes

### Keep In Code

These remain application code running inside the backend container:

- LangGraph orchestration
- MCP execution engine
- Tool registry
- Tool handlers
- Prompt construction
- API response shaping

### Replace With Managed OCI Services

These local/demo dependencies should move to OCI services:

- SQLite -> Autonomous Database
- ChromaDB -> Oracle Database 23ai AI Vector Search
- Ollama chat -> OCI Generative AI chat
- Ollama embeddings -> OCI Generative AI embeddings
- Local env secrets -> OCI Vault
- Local logs -> OCI Logging
- Local operational checks -> OCI Monitoring alarms

### Replace With Enterprise APIs

These demo mocks should become real integrations:

- `integrations/salesforce/mock.py` -> Salesforce REST API client
- `integrations/cpq/*` -> Oracle CPQ API client or Fusion CPQ integration

## Implementation Phases

1. Containerize and publish frontend/backend images to OCI Container Registry.
2. Deploy frontend and backend to OKE.
3. Put Load Balancer and API Gateway in front of the services.
4. Move secrets into OCI Vault.
5. Replace SQLite with Autonomous Database.
6. Replace Ollama chat and embeddings with OCI Generative AI.
7. Replace ChromaDB with Oracle Database 23ai AI Vector Search.
8. Replace Salesforce and CPQ mocks with real API clients.
9. Add OCI Logging, Monitoring, alarms, and dashboards.
10. Automate build and deployment with OCI DevOps.
