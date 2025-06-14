def get_mcp_tool():
    return {
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