import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

mcp_tool = {
    "type": "function",
    "function": {
        "name": "handle_mcp_operation",
        "description": "Send a command to the MCP server to perform a schema-aware or CRUD operation.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": { "type": "string", "enum": ["crud", "schema_memory"] },
                "command": { "type": "string" },
                "collection": { "type": "string" },
                "schema_id": { "type": "string" },
                "data": { "type": "object" },
                "filter": { "type": "object" },
                "update": { "type": "object" },
                "created_by": { "type": "string" },
                "instance_id": { "type": "string" },
                "updates": { "type": "object" },
                "tags": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            },
            "required": ["operation", "command"]
        }
    }
}

if not openai.api_key or not assistant_id:
    print("❌ Missing OPENAI_API_KEY or ASSISTANT_ID in environment.")
else:
    updated = openai.beta.assistants.update(
        assistant_id=assistant_id,
        tools=[mcp_tool]
    )
    print("✅ Assistant patched with MCP tool:", updated.id)