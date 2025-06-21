
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from pymongo import MongoClient
import httpx
import os
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
MCP_URL = os.getenv("MCP_URL")

if mongo_uri:
    mongo_client = MongoClient(mongo_uri)
    log_collection = mongo_client["BridgeLogs"]["conversation_logs"]
    
openai_client = OpenAI(api_key=openai_key)
mongo_client = MongoClient(mongo_uri)
log_db = mongo_client["BridgeLogs"]
log_collection = log_db["conversation_logs"]

@app.post("/bridge")
async def unified_dispatcher(request: Request):
    try:
        payload = await request.json()
        user_input = payload.get("input", "")
        session_id = payload.get("session_id", "default")

        if not user_input:
            return JSONResponse(status_code=400, content={"error": "Missing 'input' field"})

        classification_prompt = [
            {"role": "system", "content": "You are a command router for a hybrid memory and chat system.\nClassify the user's input strictly as one of:\n- schema\n- chat\n- unknown\n\nOnly return one of those words. Do not explain. Do not use quotes."},
            {"role": "user", "content": f"Input: {user_input}"}
        ]

        gpt_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=classification_prompt,
            temperature=0
        )

        route = gpt_response.choices[0].message.content.strip().lower()
        print(f"🧠 GPT classified route as: {route}")

        if "schema" in route:
            route = "schema"
        elif "chat" in route:
            route = "chat"
        elif "unknown" in route:
            route = "unknown"

        full_response = {}

        if route == "schema":
            schema_prompt = [
                {
                    "role": "system",
                    "content": "You are a memory schema formatter. Always return a valid JSON object with:\n- \"command\": one of \"create\", \"read\", \"update\", or \"delete\"\n- \"collection\": the target memory group (like \"dogs\", \"people\")\n- one of: \"data\", \"filter\", or \"update\"\nOnly return valid JSON using double quotes."
                },
                {"role": "user", "content": f"Input: {user_input}"}
            ]

            schema_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=schema_prompt,
                temperature=0
            )

            try:
                schema_payload = json.loads(schema_response.choices[0].message.content)
                print("📤 Forwarding to MCP:", json.dumps(schema_payload, indent=2))

                synonyms = {
                    "add": "create", "insert": "create",
                    "remove": "delete", "erase": "delete",
                    "change": "update", "modify": "update",
                    "get": "read", "find": "read"
                }
                if "command" in schema_payload:
                    cmd = schema_payload["command"].lower()
                    schema_payload["command"] = synonyms.get(cmd, cmd)

                if "command" not in schema_payload:
                    raise ValueError("Missing 'command' in schema payload")

                async with httpx.AsyncClient() as client:
                    mcp_response = await client.post(MCP_URL, json=schema_payload)
                full_response = mcp_response.json()
                return JSONResponse(status_code=mcp_response.status_code, content=full_response)

            except Exception as e:
                full_response = {"error": f"Schema generation failed: {str(e)}"}
                return JSONResponse(status_code=500, content=full_response)

        elif route == "chat":
            reply_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )
            reply = reply_response.choices[0].message.content
            full_response = {"reply": reply}
            return JSONResponse(content=full_response)

        else:
            full_response = {"error": "Unable to classify request intent."}
            return JSONResponse(status_code=400, content=full_response)

    finally:
        # Log the exchange
        log_collection.insert_one({
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "input": payload.get("input", ""),
            "route": route,
            "response": full_response
        })
