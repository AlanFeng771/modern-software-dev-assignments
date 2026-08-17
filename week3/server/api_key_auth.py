"""API key authentication for the HTTP (streamable-http) transport.

STDIO transport ignores these settings entirely (verified against the SDK source: STDIO's
run path never reads `auth`/`token_verifier`), so this only takes effect when the server is
deployed over HTTP.

Auth is opt-in: it's only enabled when the `MCP_API_KEY` environment variable is set. This
keeps local/STDIO usage (and test scripts) working unauthenticated by default, while a
deployment (e.g. Vercel) can enable it by setting that environment variable.
"""

import os

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings


class ApiKeyVerifier(TokenVerifier):
    """Validates the bearer token against a single pre-shared API key.

    Not OAuth2 — there's no issuer, no audience claim, no token expiry. Just a fixed secret
    string, matching the assignment's simpler "API key" bonus option rather than the more
    involved "OAuth2 with audience validation" option.
    """

    def __init__(self, expected_key: str):
        self._expected_key = expected_key

    async def verify_token(self, token: str) -> AccessToken | None:
        if token != self._expected_key:
            return None
        return AccessToken(token=token, client_id="mcp-client", scopes=[])


def build_auth_kwargs(resource_url: str) -> dict:
    """Returns kwargs to pass into MCPServer(...) to enable API-key auth, or an empty dict
    if MCP_API_KEY isn't set (auth disabled)."""
    api_key = os.environ.get("MCP_API_KEY")
    if not api_key:
        return {}

    return {
        "auth": AuthSettings(issuer_url=resource_url, resource_server_url=resource_url),
        "token_verifier": ApiKeyVerifier(api_key),
    }
