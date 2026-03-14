# Manual Build Plan (Learning-First Order)

Build bottom-up so you understand each layer before stacking the next.

---

## Phase 1 — Understand the Foundation (Local, No AWS)

| # | Task | Why |
|---|------|-----|
| 1 | Build a FastAPI orders service with SQLite | Understand the REST API you're wrapping. 4 endpoints, simple models, run locally |
| 2 | Write the OpenAPI spec by hand (or export from FastAPI) | Understand what OpenAPI actually describes — paths, params, schemas |
| 3 | Build the OpenAPI parser | Read a YAML spec, extract endpoints + params into a clean data structure |
| 4 | Build the tool name generator | Map `GET /orders/{id}` → `get_order(orderId)` — understand the translation logic |
| 5 | Test parser + generator together | Feed your orders spec in, see tool definitions come out |

---

## Phase 2 — MCP Layer (Still Local)

| # | Task | Why |
|---|------|-----|
| 6 | Build a handwritten MCP server (no generation) | Understand what an MCP server actually does — register tools, handle calls, return results |
| 7 | Test MCP server with a local MCP client | Verify tools work end-to-end: client → MCP → REST API → DB |
| 8 | Build the Jinja2 server template | Now that you know what a server looks like, templatize it |
| 9 | Build the server generator | Auto-generate what you built by hand in step 6 |
| 10 | Generate + run + test | Confirm generated server behaves identically to handwritten one |

---

## Phase 3 — Multi-API & Gateway (Still Local)

| # | Task | Why |
|---|------|-----|
| 11 | Add a second OpenAPI spec (e.g., payments) | Test that your pipeline handles multiple APIs |
| 12 | Build the gateway | Aggregate tools from multiple MCP servers into one endpoint |
| 13 | Build the CLI (register, generate, serve) | Tie the workflow together into a usable command |

---

## Phase 4 — AWS + AgentCore

| # | Task | Why |
|---|------|-----|
| 14 | Deploy FastAPI to Lambda + API Gateway | Get your REST API running on AWS with IAM auth |
| 15 | Deploy MCP server (Lambda or ECS) | Get your MCP server reachable from AWS |
| 16 | Create a Bedrock AgentCore agent | Configure agent with your MCP server as a tool source |
| 17 | Test end-to-end | Prompt → AgentCore → MCP → API Gateway → Lambda → DB |
| 18 | Add auth config per API | API keys, IAM roles — each registered API gets its own auth |

