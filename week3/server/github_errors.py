"""Shared GitHub API error handling for MCP tools.

Wraps a tool function so both `get_useful_repositories` and `get_repository_info`
can reuse the same exception-handling logic, while still allowing each tool to
supply its own status-code-specific message (see spec.md).
"""

import functools
import logging
from collections.abc import Callable
import time

import httpx

logger = logging.getLogger(__name__)


def handle_github_errors(status_messages: dict[int, str]):
    """
    status_messages: maps a tool-specific HTTP status code (e.g. 422 for Tool 1,
    404 for Tool 2) to a message template. The template can reference the wrapped
    function's own kwargs, e.g. "Could not find repository {owner}/{repo}."

    Status codes NOT in status_messages, plus timeout/network/503/rate-limit,
    are handled generically inside the wrapper (shared by every tool).
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except httpx.HTTPStatusError as e:
                status = e.response.status_code

                if status == 403 and e.response.headers.get("X-RateLimit-Remaining") == "0":
                    reset_time = int(e.response.headers.get("X-RateLimit-Reset", 0))
                    wait_seconds = reset_time - int(time.time())
                    if e.request.url.path.startswith("/search"):
                        # GitHub Search API has a separate rate limit (30 requests/minute)
                        return {"error_message": f"GitHub Search API rate limit exceeded. Please try again in approximately {int(wait_seconds) // 60} minute(s)."}
                    else:
                        return {"error_message": f"GitHub API rate limit exceeded. Please try again in approximately {int(wait_seconds) // 60} minute(s)."}

                elif status in status_messages:
                    # 例如 status_messages[404] = "Could not find repository {owner}/{repo}."
                    message_template = status_messages[status]
                    return {"error_message": message_template.format(**kwargs)} 

                elif status == 503:
                    return {"error_message": "GitHub API is temporarily unavailable. Please try again later."}

                else:
                    logger.error(f"Unexpected status code: {status}")
                    return {"error_message": "An unexpected error occurred while processing your request."}

            except httpx.TimeoutException:
                logger.error("Request timed out")
                return {"error_message": "The request timed out. Please try again later."}

            except httpx.RequestError as e:
                # 注意:HTTPStatusError 不是 RequestError 的子類別,兩者是分開的例外家族
                # (HTTPStatusError = 收到回應但狀態碼錯誤;RequestError = 根本沒收到回應)
                logger.error("Network error occurred")
                return {"error_message": "A network error occurred. Please try again later."}
        return wrapper
    return decorator
