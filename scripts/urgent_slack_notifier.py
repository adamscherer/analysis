#!/usr/bin/env python
import argparse
import asyncio
from contextlib import AsyncExitStack
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, stdio_client

# Add the parent directory to system path to import from src
sys.path.append(str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("urgent_slack_notifier")

# Load environment variables
load_dotenv()

# MCP Slack configuration
SLACK_CHANNEL = os.getenv("SLACK_NOTIFICATION_CHANNEL", "#alerts")


class UrgencyEvaluator:
    """Evaluates the urgency of a message based on content analysis."""

    # Keywords that indicate urgency (expand as needed)
    URGENT_KEYWORDS = [
        "urgent",
        "emergency",
        "critical",
        "alert",
        "immediately",
        "asap",
        "failure",
        "error",
        "failed",
        "down",
        "outage",
        "broken",
        "crashed",
        "breach",
        "security",
        "incident",
    ]

    def __init__(self, threshold: float = 0.7):
        """
        Initialize with a threshold for determining urgency.

        Args:
            threshold: Urgency score threshold (0.0-1.0) above which a message is considered urgent
        """
        self.threshold = threshold

    def evaluate(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Evaluate the urgency of a message.

        Args:
            text: The message text to evaluate

        Returns:
            Tuple containing:
                - Boolean indicating if message is urgent
                - Urgency score (0.0-1.0)
                - List of matched urgent keywords
        """
        if not text:
            return False, 0.0, []

        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()

        # Find matches
        matched_keywords = [kw for kw in self.URGENT_KEYWORDS if kw in text_lower]

        # Calculate urgency score based on keyword matches
        # This is a simple implementation, consider ML-based approaches for production
        if not matched_keywords:
            return False, 0.0, []

        # Basic scoring: number of matches / possible matches, capped at 1.0
        urgency_score = min(1.0, len(matched_keywords) / len(self.URGENT_KEYWORDS) * 3)

        return urgency_score >= self.threshold, urgency_score, matched_keywords


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_server(self, name="slack", config_path="~/.cursor/mcp.json"):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        # Expand ~ to the full home directory path
        full_path = os.path.expanduser(config_path)

        with open(full_path, "r") as f:
            config = json.load(f)

        print(config)
        server = config["mcpServers"].get(name)
        if not server:
            raise ValueError(f"Server config for '{name}' not found.")

        server_params = StdioServerParameters(
            command=server["command"],
            args=server.get("args", []),
            env=server.get("env", {}),
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools, with tool chaining (max 6 calls)."""

        def format_tool_call_message(index, name):
            return f"[Tool call {index}/{max_tool_calls}: {name}]"

        def add_assistant_message(messages, contents):
            messages.append({"role": "assistant", "content": contents})

        def add_tool_result_message(messages, tool_use_id, result_content):
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result_content,
                        }
                    ],
                },
            )

        # System message as a top-level parameter instead of in the messages array
        system_message = (
            "You have access to external tools for tasks like Slack. "
            "But if a question can be answered from your general knowledge (e.g., trivia, definitions, geography), "
            "please answer directly without using tools."
        )

        messages = [
            {"role": "user", "content": query},
        ]
        tool_call_count = 0
        max_tool_calls = 6
        final_text = []

        # Fetch available tools from the MCP server
        tool_response = await self.session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tool_response.tools
        ]

        # Initial message to Claude
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_message,  # System message as a top-level parameter
            messages=messages,
            tools=available_tools,
        )

        # Main processing loop for tool calls
        while tool_call_count < max_tool_calls:
            has_tool_call = False
            assistant_contents = []

            for content in response.content:
                if content.type == "text":
                    final_text.append(content.text)
                    assistant_contents.append(content)

                elif content.type == "tool_use":
                    has_tool_call = True
                    tool_call_count += 1
                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    print(format_tool_call_message(tool_call_count, tool_name))
                    final_text.append(
                        format_tool_call_message(tool_call_count, tool_name)
                    )

                    try:
                        result = await self.session.call_tool(tool_name, tool_args)
                    except Exception as e:
                        result = type(
                            "ToolResult",
                            (),
                            {"content": f"Error calling tool {tool_name}: {e}"},
                        )

                    assistant_contents.append(content)
                    add_assistant_message(messages, assistant_contents)
                    add_tool_result_message(messages, tool_id, result.content)
                    break  # Restart loop after handling one tool call

            if not has_tool_call:
                add_assistant_message(messages, assistant_contents)
                break  # No tools to call; we're done

            # Get next Claude response after tool usage
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_message,  # Include system message in subsequent calls too
                messages=messages,
                tools=available_tools,
            )

        # If limit reached but no conclusive text, ask Claude for summary
        if tool_call_count >= max_tool_calls:
            messages.append(
                {
                    "role": "user",
                    "content": "Please summarize the results of all the tool calls in a concise response.",
                }
            )

            final_response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_message,  # Include system message in the final call too
                messages=messages,
            )

            for content in final_response.content:
                if content.type == "text":
                    final_text.append(content.text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 1:
        print("Usage: python urgent_slack_notifier.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
