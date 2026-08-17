"""ASGI entrypoint for deploying this MCP server to a serverless platform (e.g. Vercel).

Unlike `mcp_server.py`'s `if __name__ == "__main__"` block (which calls `mcp.run(...)` and
manages its own uvicorn process), this module just exposes the underlying Starlette ASGI app
object. The hosting platform's own runtime is responsible for starting it and routing requests.

`stateless_http=True` because serverless functions don't guarantee the same process handles
consecutive requests from the same client — the server can't rely on in-memory session state
persisting between calls.

The `sys.path` insert is needed because the hosting platform imports this file directly by path
without adding its parent directory to the module search path, so a plain `from mcp_server
import mcp` (and `mcp_server.py`'s own `from github_errors import ...`) would otherwise fail with
`ModuleNotFoundError`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import mcp  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402

# The deployed domain must be explicitly allow-listed, or the SDK's DNS-rebinding protection
# rejects every request with "Invalid Host header" (the allow-list is empty by default).
transport_security = TransportSecuritySettings(
    allowed_hosts=["modern-software-dev-assignments-pi.vercel.app"],
)

app = mcp.streamable_http_app(stateless_http=True, transport_security=transport_security)
