"""ASGI entrypoint for deploying this MCP server to a serverless platform (e.g. Vercel).

Unlike `mcp_server.py`'s `if __name__ == "__main__"` block (which calls `mcp.run(...)` and
manages its own uvicorn process), this module just exposes the underlying Starlette ASGI app
object. The hosting platform's own runtime is responsible for starting it and routing requests.

`stateless_http=True` because serverless functions don't guarantee the same process handles
consecutive requests from the same client — the server can't rely on in-memory session state
persisting between calls.
"""

from mcp_server import mcp

app = mcp.streamable_http_app(stateless_http=True)
