from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
import httpx
import os
import json
from pathlib import Path

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY is not set in environment.")
openai_client = OpenAI(api_key=openai_key)

MCP_URL = os.getenv("MCP_URL")
MODERATOR_PROMPT_PATH = Path(__file__).parent / "moderator_prompt.txt"

@app.post("/bridge")
async def unified_dispatcher(request: Request):
    try:
        payload = await request.json()
        user_input = payload.get("input", "")

        if not user_input:
            return JSONResponse(status_code=400, content={"error": "Missing 'input' field"})

        # Load moderator prompt
        with open(MODERATOR_PROMPT_PATH, "r") as f:
            moderator_prompt = f.read()

        # Step 1: Classify intent
        classification_prompt = [
            {"role": "system", "content": moderator_prompt},
            {"role": "user", "content": f"Input: {user_input}"}
        ]

        gpt_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=classification_prompt,
            temperature=0
        )

        route = gpt_response.choices[0].message.content.strip().lower()

        if route == "schema":
            # Step 2: Generate schema payload
            generation_prompt = [
                {
                    "role": "system",
                    "content": '''You are a memory schema formatter. Always return a valid JSON object with:
- "command": one of "create", "read", "update", or "delete"
- "collection": the target memory group (like "dogs", "people")
- one of: "data", "filter", or "update"
NEVER omit the "command" field — it is required.
Only return valid JSON using double quotes.'''
                },
                {"role": "user", "content": f"Input: {user_input}"}
            ]

            schema_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=generation_prompt,
                temperature=0
            )

            try:
                schema_payload = json.loads(schema_response.choices[0].message.content)

                print("📤 Forwarding to MCP:", json.dumps(schema_payload, indent=2))

                if "command" not in schema_payload:
                    return JSONResponse(status_code=400, content={"error": "Generated schema payload is missing 'command'"})

                if schema_payload["command"] not in {"create", "read", "update", "delete"}:
                    return JSONResponse(status_code=400, content={"error": "Unsupported command: " + schema_payload["command"]})

                async with httpx.AsyncClient() as client:
                    mcp_response = await client.post(MCP_URL, json=schema_payload)
                return JSONResponse(status_code=mcp_response.status_code, content=mcp_response.json())

            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Schema generation failed: {str(e)}"})

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
            return JSONResponse(content={"reply": reply})

        else:
            return JSONResponse(status_code=400, content={"error": "Unable to classify request intent."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
