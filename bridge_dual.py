# bridge_dual.py – Unified Chat + Tool Routing with OpenAI v1+ and Proper Tool Injection

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import requests
import os
from env import OPENAI_API_KEY, ASSISTANT_ID, MCP_URL

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# Serve static files (HTML UI)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("index.html")


@app.post("/chat")
async def chat_with_gpt(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}]
    )

    return {"response": response.choices[0].message.content}


@app.post("/bridge")
async def bridge_to_scribe(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            break

        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            args = eval(tool_call.function.arguments)
            mcp_response = requests.post(MCP_URL, json=args).json()

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": str(mcp_response)
                }]
            )

messages = client.beta.threads.messages.list(thread_id=thread.id)

if messages.data and messages.data[0].content:
    return {"response": messages.data[0].content[0].text.value}
else:
    return {"response": f"✅ Tool executed. MCP response: {mcp_response}"}


@app.post("/unified")
async def moderator_router(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")

    with open("moderator_prompt.txt") as f:
        system_prompt = f.read()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    reply = response.choices[0].message.content.strip()

    if reply.startswith("{"):
        try:
            import json
            payload = json.loads(reply)
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content="Moderator forwarded structured memory command."
            )
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID,
                tool_choice={"type": "function", "function": {"name": "handle_mcp_operation"}}
            )
            # Wait for Scribe to ask for tool output
            while True:
                run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run_status.status == "requires_action":
                    tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
                    mcp_response = requests.post(MCP_URL, json=payload).json()
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": str(mcp_response)
                        }]
                    )
                if run_status.status == "completed":
                    break
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return {"response": messages.data[0].content[0].text.value}
        except Exception as e:
            return {"error": "Moderator generated invalid JSON.", "details": str(e), "raw_reply": reply}
    else:
        return {"response": reply}
