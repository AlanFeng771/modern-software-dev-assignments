"""Quick manual smoke test — calls the tool function directly (bypassing the MCP protocol layer)
to check the underlying GitHub API logic before wiring up a full MCP client."""

import asyncio

from mcp_server import get_useful_repositories
from mcp_server import get_repository_info


async def main():
    result = await get_useful_repositories(keyword="", max_repositories=0)
    # result = await get_repository_info(owner="obra", repo="superpowers")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
