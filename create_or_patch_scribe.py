
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the tool
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

# Update Scribe (insert your real ID)
assistant = openai.beta.assistants.update(
    assistant_id="asst_A01vTwkSzqBM5GyJT5r6haBF",
    tools=[mcp_tool]
)

print("✅ Scribe patched with tool:", assistant.id)
