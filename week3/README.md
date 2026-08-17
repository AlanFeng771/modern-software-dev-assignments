# Week 3 — GitHub Repository Explorer (MCP Server)

An MCP server that wraps the GitHub REST API, exposing two tools that let an LLM discover GitHub
repositories by keyword and then look up detailed information about a specific one. See
[`spec.md`](./spec.md) for the full design spec and rationale behind each decision.

Deployment mode: **Local (STDIO)** by default, discoverable by Claude Desktop or the MCP
Inspector — with an optional **HTTP (streamable-http)** mode for remote/agent-runtime access.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) (this repo's dependency manager)
- Node.js (only needed to run the MCP Inspector for local debugging)

## Setup

From the repo root:

```powershell
poetry install
```

This installs `mcp` and `httpx`, which this server depends on, along with the rest of the repo's
shared dependencies.

## Running the server

```powershell
cd week3\server
poetry run python mcp_server.py
```

The server communicates over STDIO — it won't print anything to stdout on its own (that channel
is reserved for the MCP protocol messages); status/error logs go to stderr via the standard
`logging` module.

### HTTP mode

```powershell
cd week3\server
poetry run python mcp_server.py --transport streamable-http
```

Starts an HTTP server on `http://127.0.0.1:8000` (via Uvicorn), exposing the MCP endpoint at
`http://127.0.0.1:8000/mcp`. Useful for remote/agent-runtime access, or for testing with the MCP
Inspector's "Streamable HTTP" connection mode instead of spawning a subprocess.

## Testing locally

### Option A — MCP Inspector (recommended)

```powershell
cd week3\server
npx @modelcontextprotocol/inspector poetry run python mcp_server.py
```

This opens a browser UI that connects to the server, lists its tools, and lets you call them
interactively with arbitrary input.

> Run this from inside `week3\server`, and pass just the filename (`mcp_server.py`), not a
> relative path with backslashes — some Inspector versions mishandle `\` in path arguments.

### Option B — Direct function calls (business-logic only, bypasses the MCP protocol layer)

```powershell
cd week3\server
poetry run python test_manual.py
poetry run python test_errors.py
```

### Option C — Interactive ReAct agent (local LLM via Ollama)

`react_agent_demo.py` connects to the server over STDIO, gives its tools to a local Ollama model,
and runs an interactive chat loop — each turn can involve one or more tool calls (reason -> call
tool -> observe) before the model answers. This is the most realistic end-to-end test: an actual
LLM deciding when and how to call each tool from natural-language conversation.

Prerequisites: [Ollama](https://ollama.com/) running locally with a tool-calling-capable model
pulled (e.g. `ollama pull llama3.1:8b`).

```powershell
poetry run python week3\react_agent_demo.py
```

```
You: Are there any good agent skills frameworks on GitHub?
[agent] Calling tool: get_useful_repositories({'keyword': 'agent skills'})
[agent] Tool result: {"items": [...]}
[agent] Calling tool: get_repository_info({'owner': 'obra', 'repo': 'superpowers'})
[agent] Tool result: {"description": "...", ...}

Agent: Yes — "superpowers" by obra looks like a strong pick...
```

A system prompt (`SYSTEM_PROMPT` in the script) tells the model to only call these tools when the
user is actually asking about GitHub repositories — without it, small local models tend to call a
tool for every message (e.g. searching GitHub for "hello" after a plain greeting).

## Configuring Claude Desktop

Add this server to your Claude Desktop config
(`%AppData%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "github-repos": {
      "command": "C://Users//user//Desktop//Projects//modern-software-dev-assignments//.venv//Scripts//python.exe",
      "args": [
        "C://Users//user//Desktop//Projects//modern-software-dev-assignments//week3//server//mcp_server.py"
      ]
    }
  }
}
```

Restart Claude Desktop afterward. You should see a 🔨 tools icon indicating the server connected
and its two tools are available.

## Environment variables

None required — both tools work fully unauthenticated against the public GitHub API. Without a
token, GitHub's unauthenticated rate limits apply (10 req/min for Search API, 60 req/hour for the
Core API); this is handled gracefully (see Reliability below), not required to be avoided.

## Tool reference

### `get_useful_repositories`

Searches GitHub repositories matching a keyword, ranked by star count. Returns a short candidate
list — pass an item's `owner`/`repo` to `get_repository_info` for full details.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keyword` | string | yes | Keyword to search for repositories |
| `max_repositories` | integer | no (default 10) | Maximum number of repositories to return |

**Example call:**
```json
{"keyword": "agent skills", "max_repositories": 5}
```

**Example output:**
```json
{
  "items": [
    {"owner": "obra", "repo": "superpowers", "description": "An agentic skills framework & software development methodology that works.", "stars": 272695}
  ]
}
```

### `get_repository_info`

Retrieves detailed information about a specific GitHub repository.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `owner` | string | yes | The GitHub username or organization that owns the repository |
| `repo` | string | yes | The repository name |

**Example call:**
```json
{"owner": "obra", "repo": "superpowers"}
```

**Example output:**
```json
{
  "description": "An agentic skills framework & software development methodology that works.",
  "stargazers_count": 272695,
  "open_issues_count": 340,
  "language": "Shell",
  "forks_count": 24378,
  "topics": ["ai", "brainstorming", "coding", "obra", "sdlc", "skills", "subagent-driven-development", "superpowers"],
  "html_url": "https://github.com/obra/superpowers"
}
```

## Example invocation flow

1. User: *"Are there any good agent skills frameworks on GitHub?"*
2. Model calls `get_useful_repositories(keyword="agent skills")`
3. Model picks a candidate from the returned list and calls
   `get_repository_info(owner="obra", repo="superpowers")` for more detail
4. Model summarizes the result back to the user

## Reliability

- Both tools handle HTTP failures, timeouts, and empty results gracefully — see the
  "Error Handling" tables in [`spec.md`](./spec.md) for the exact condition → response mapping.
- Rate-limit handling is passive: each response's `X-RateLimit-Remaining` / `X-RateLimit-Reset`
  headers are read after the fact rather than pre-checked, and a warning with an estimated wait
  time is returned only once the quota is actually exhausted — the server never blocks/sleeps
  waiting for a reset.
- Shared error-handling logic (`github_errors.py`) automatically distinguishes the Search API's
  stricter rate-limit bucket from the Core API's, based on the request path.

## Known limitations

- `get_useful_repositories` ranks purely by star count. Star counts can be inflated by
  bot/fake-star campaigns, so a high rank isn't a guarantee of genuine project quality.
- No authentication is implemented, so both tools are subject to GitHub's unauthenticated rate
  limits (see above) — under heavy use this will surface more often than with a token.
