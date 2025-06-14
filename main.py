from fastapi import FastAPI, Request
from bridge import run_mcp_conversation

app = FastAPI()

@app.post("/bridge")
async def bridge(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")
    response = run_mcp_conversation(user_input)
    return { "response": response }