from typing import Any
import os
import httpx
import argparse
from typing import Annotated
from pydantic import Field
from mcp.server import MCPServer
from github_errors import handle_github_errors
from api_key_auth import build_auth_kwargs
import logging
logger = logging.getLogger(__name__)


# Only takes effect over HTTP transport, and only if MCP_API_KEY is set — see api_key_auth.py.
_resource_url = os.environ.get("MCP_RESOURCE_URL", "http://127.0.0.1:8000/mcp")
mcp = MCPServer(name="github_repos", **build_auth_kwargs(_resource_url))


@mcp.tool()
@handle_github_errors({422: "Your search keyword could not be processed. Please try a simpler or different keyword."})
async def get_useful_repositories(keyword: Annotated[str, Field(min_length=2, description="The search keyword for finding repositories.")], max_repositories: Annotated[int, Field(ge=1, le=100, description="The maximum number of repositories to return.")] = 10) -> dict[str, Any]:
    """Lists GitHub repositories matching a given `keyword`, including a short description, plus the repository's `owner` and `repo`, which can be passed to `get_repository_info` for detailed information."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": keyword, "sort": "stars", "order": "desc", "per_page": max_repositories},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        result = {
            "items": [
                {
                    "repo": item["name"],
                    "owner": item["owner"]["login"],
                    "description": item.get("description", ""),
                    "stars": item.get("stargazers_count", 0),
                }
                for item in data.get("items", [])
            ]
        }

        if len(result["items"]) == 0:
            return {"error_message": "No matching repositories found. Please try a different keyword."}

        return result

@mcp.tool()
@handle_github_errors({404: "Could not find repository {owner}/{repo}."})
async def get_repository_info(owner: Annotated[str, Field(min_length=1, description="The owner of the repository.")], repo: Annotated[str, Field(min_length=1, description="The name of the repository.")]) -> dict[str, Any]:
    """Fetches detailed information about a specific GitHub repository, including its `description`, `stars`, `forks`, and `open_issues` count."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        descriptions = data.get("description", "No description available")
        language = data.get("language", "Unknown")

        if descriptions is None:
            descriptions = "No description available"

        if language is None:
            language = "Unknown"

        result = {
            "description": descriptions,
            "stargazers_count": data.get("stargazers_count", 0),
            "open_issues_count": data.get("open_issues_count", 0),
            "language": language,
            "forks_count": data.get("forks_count", 0),
            "topics": data.get("topics", []),
            "html_url": data.get("html_url", ""),

        }
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GitHub MCP server.")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "sse", "streamable-http"], help="Transport method for MCP server (default: stdio)")
    args = parser.parse_args()
    mcp.run(transport=args.transport)
     
    
