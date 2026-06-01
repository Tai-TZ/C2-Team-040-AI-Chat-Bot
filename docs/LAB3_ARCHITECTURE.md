# Lab 3 Architecture — VinWonders Tour Guide

```mermaid
flowchart TB
  subgraph UI["Frontend"]
    Chat[ChatPanel]
    AgentTab[AgentActivityPanel]
    Canvas[Canvas / Dashboard]
  end

  subgraph API["FastAPI server.py"]
    Stream["POST /api/chat/stream"]
    Tel["GET /api/telemetry/session"]
  end

  subgraph Agent["ReActAgent v2"]
    Boot[bootstrap pipeline]
    Guard[guardrails]
    Loop[Thought → Action → Observation]
    Struct[structured + map]
  end

  subgraph Tools["5 VinWonders tools"]
    R[resolve_site]
    D[parse_visit_date]
    W[get_weather_forecast]
    P[get_ticket_prices]
    L[list_destinations]
  end

  Chat --> Stream
  Stream --> Agent
  Boot --> R --> D --> W --> P
  Loop --> Tools
  Guard --> Loop
  Agent --> Struct --> Chat
  Agent --> Canvas
  Agent --> Tel
```

## Chatbot vs Agent

| | Chatbot | Agent v1 | Agent v2 |
| :--- | :--- | :--- | :--- |
| Tools | No | Yes | Yes + bootstrap |
| Live prices | No | Sometimes hallucinates | API + guardrails |
| Trace UI | No | Basic | Full SSE trace |
