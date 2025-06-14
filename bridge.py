from fastapi import FastAPI, Request
import openai
import requests
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
MCP_URL = os.getenv("MCP_URL")

app = FastAPI()

@app.post("/bridge")
async def bridge(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")

    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=os.getenv("ASSISTANT_ID")
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            args = eval(tool_call.function.arguments)
            mcp_response = requests.post(MCP_URL, json=args).json()

            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": str(mcp_response)
                }]
            )

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return { "response": messages.data[0].content[0].text.value }