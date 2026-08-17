"""A minimal ReAct-style agent, interactive mode: connects to the local MCP server over
STDIO once, then runs a continuous chat loop with a local Ollama model. Each turn may
involve one or more tool calls (reason -> call tool -> observe) before the model gives
a final answer. Conversation history persists across turns until you type "exit"/"quit".

Usage:
    poetry run python week3/react_agent_demo.py
"""

import asyncio
import json
import sys
from pathlib import Path

import mcp
import ollama

SERVER_DIR = Path(__file__).parent / "server"
SERVER_SCRIPT = SERVER_DIR / "mcp_server.py"
OLLAMA_MODEL = "llama3.1:8b"
EXIT_COMMANDS = {"exit", "quit"}
SYSTEM_PROMPT = (
    "You are a helpful assistant with access to two GitHub tools: "
    "get_useful_repositories (search repos by keyword) and get_repository_info "
    "(get details about a specific repo). "
    "Only call a tool when the user is actually asking about GitHub repositories or projects "
    "(e.g. asking for recommendations, or details about a specific repo). "
    "For greetings, small talk, or anything unrelated to GitHub, respond normally without "
    "calling any tool."
)


def mcp_tools_to_ollama_format(tools: list[mcp.types.Tool]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def extract_tool_result_text(result: mcp.types.CallToolResult) -> str:
    texts = [block.text for block in result.content if hasattr(block, "text")]
    return "\n".join(texts) if texts else json.dumps(result.structured_content)


async def run_turn(messages: list[dict], ollama_tools: list[dict], session: mcp.ClientSession) -> None:
    """Runs one user turn to completion: keeps calling tools until the model gives a final answer."""
    while True:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=ollama_tools)
        messages.append(response.message.model_dump())

        if not response.message.tool_calls:
            print(f"\nAgent: {response.message.content}\n")
            return

        for call in response.message.tool_calls:
            name = call.function.name
            arguments = call.function.arguments
            print(f"[agent] Calling tool: {name}({arguments})")

            result = await session.call_tool(name, arguments)
            result_text = extract_tool_result_text(result)
            print(f"[agent] Tool result: {result_text}")

            messages.append({"role": "tool", "tool_name": name, "content": result_text})


async def chat_loop() -> None:
    server_params = mcp.StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
        cwd=str(SERVER_DIR),
    )

    async with mcp.stdio_client(server_params) as (read_stream, write_stream):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            ollama_tools = mcp_tools_to_ollama_format(tools_result.tools)
            print(f"[agent] Connected. Available tools: {[t.name for t in tools_result.tools]}")
            print("Type 'exit' or 'quit' to end.\n")

            messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
            loop = asyncio.get_event_loop()

            while True:
                user_input = await loop.run_in_executor(None, input, "You: ")
                if user_input.strip().lower() in EXIT_COMMANDS:
                    print("[agent] Goodbye.")
                    return

                messages.append({"role": "user", "content": user_input})
                await run_turn(messages, ollama_tools, session)


if __name__ == "__main__":
    asyncio.run(chat_loop())
