from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
import httpx
import os
import json

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys and MCP endpoint
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY is not set in environment.")

openai_client = OpenAI(api_key=openai_key)
MCP_URL = os.getenv("MCP_URL")  # e.g. https://mcp-server.onrender.com/schema_memory

@app.post("/bridge")
async def unified_dispatcher(request: Request):
    try:
        payload = await request.json()
        user_input = payload.get("input", "")

        if not user_input:
            return JSONResponse(status_code=400, content={"error": "Missing 'input' field"})

        # Step 1: Classify intent
        classification_prompt = [
            {
                "role": "system",
                "content": '''You are a command router for a hybrid memory and chat system.
Classify the user's input as one of the following:
- 'schema' for memory operations (create/read/update/delete)
- 'chat' for general assistant replies
- 'unknown' if unclear.'''
            },
            {"role": "user", "content": f"Input: {user_input}"}
        ]

        gpt_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=classification_prompt,
            temperature=0
        )

        route = gpt_response.choices[0].message.content.strip().lower()

        if route == "schema":
            # Step 2: Ask GPT to generate a schema payload
            generate_prompt = [
                {
                    "role": "system",
                    "content": '''You are a memory schema formatter. Given a user request, generate a valid JSON object
containing: 'command', 'collection', and either 'data', 'filter', or 'update', depending on the intent.
Only return valid JSON.'''
                },
                {"role": "user", "content": f"Input: {user_input}"}
            ]

            schema_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=generate_prompt,
                temperature=0
            )

            try:
                schema_payload = json.loads(schema_response.choices[0].message.content)
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
