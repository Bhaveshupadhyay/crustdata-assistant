"""Tool declarations and executor for the Documentation agent.

Defines Gemini function-calling tools that allow the LLM to search the
Crustdata API knowledge base dynamically during conversation.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import httpx
from google.genai import types

from src.shared.constants import MessageRole


async def search_docs(query: str) -> dict:
    """Queries the Mintlify assistant API and consumes the SSE stream."""
    url = "https://docs.crustdata.com/_mintlify/api-public/assistant/crustdata/message"

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://docs.crustdata.com/for-agents/llms",
        "Accept": "*/*",
        "Origin": "https://docs.crustdata.com",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/18.6 Safari/605.1.15"
        ),
    }

    # We construct the payload format expected by the Mintlify assistant
    payload = {
        "id": "crustdata",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "role": MessageRole.USER,
                "content": query,
                "parts": [{"type": "text", "text": query}],
            }
        ],
        "fp": "crustdata",
        "filter": {"groups": ["*"]},
        "currentPath": "/for-agents/llms",
        "_": (
            "eyJhbGciOiJFZERTQSJ9.eyJwIjpudWxsLCJzayI6bnVsbCwic3ViIjoiY3J1c3RkYXRhIiwiZXhwI"
            "joxNzg1NDAzOTc2fQ.Ev_L57tQk4Wb3YlAdIdPLRRAahUB73UBMAkQz9dnSBlN4RnnPXWbvjwi_8Nd"
            "jjGzmN1HC5W5alrlnvHcdyRBD%"
        ),
    }

    full_answer = ""

    # Using httpx to consume the stream asynchronously
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", url, headers=headers, json=payload, timeout=30.0
        ) as response:
            response.raise_for_status()

            # The API streams lines formatted like: 0:"Hello!"
            async for line in response.aiter_lines():
                if not line:
                    continue

                # '0:' is the Vercel AI SDK prefix for a text chunk
                if line.startswith("0:"):
                    try:
                        # Extract the JSON-encoded string part after the '0:'
                        chunk_str = line[2:]
                        chunk = json.loads(chunk_str)
                        full_answer += chunk
                    except json.JSONDecodeError:
                        continue

    print("tool", full_answer)
    return {"result": full_answer}


async def search_crustdata() -> dict:
    """Search Crustdata for specific data or information."""
    return {}


def get_doc_tool_declarations() -> list:
    """Return Gemini function-calling tool declarations for the doc agent."""

    # We return the schemas manually since the google-genai SDK
    # explicitly blocks parsing python coroutine (async def) functions.
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_docs",
                    description="Queries the Mintlify assistant API and consumes the SSE stream.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "query": {"type": "STRING", "description": "The search query."}
                        },
                        "required": ["query"],
                    },
                ),
                types.FunctionDeclaration(
                    name="search_crustdata",
                    description="Search Crustdata for specific data or information.",
                    parameters={"type": "OBJECT", "properties": {}},
                ),
            ]
        )
    ]
