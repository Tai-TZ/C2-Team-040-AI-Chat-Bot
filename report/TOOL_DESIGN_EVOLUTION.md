# Tool Design Evolution — VinWonders Lab 3

## v0 — Chatbot baseline (no tools)

| Capability | Implementation |
| :--- | :--- |
| Destination list | Static text from `vinwonders_destinations_data.json` |
| Prices / weather | **Not available** — model may hallucinate |

## v1 — Initial ReAct tools (5 tools)

| Tool | Input | Issue observed |
| :--- | :--- | :--- |
| `resolve_site` | `query` | Model passed `location`, `region` → tool errors |
| `parse_visit_date` | `expression` | Model passed `date`, `using_date` → TypeError |
| `get_weather_forecast` | `location`, `using_date` | Called before `resolve_site` |
| `get_ticket_prices` | `supplier_code`, `using_date` | Wrong param names `supplierCode` |
| `list_destinations` | `region_query` optional | Rarely needed |

**Trace failure (v1):** `Final Answer` before weather/prices → hallucinated VND.

## v2 — Improved tools + agent layer

| Improvement | File | Effect |
| :--- | :--- | :--- |
| `_sanitize_tool_args()` | `src/tools/registry.py` | Maps `location`→`query`, `supplierCode`→`supplier_code` |
| Required-field validation | `registry.execute_tool` | JSON error instead of crash |
| Bootstrap pipeline | `src/agent/bootstrap.py` | Auto `resolve_site`→`date`→`weather`→`prices` |
| Premature Final guard | `src/agent/guardrails.py` | Rejects answer until pipeline complete |
| Karphany prompt v2 | `src/prompts/vinwonders.py` | Off-topic refusal, mandatory order |
| Structured UI | `src/agent/structured.py` | Cards, map embed, actions |

## v2.1 — Production extras (bonus)

- OpenWeatherMap + VinWonders booking API (live data)
- Internal map coordinates per sub-location
- SSE: `agent_step`, `trace`, `structured`, `dashboard`
- Telemetry: `LLM_METRIC` with `cost_estimate_usd`, token ratio
