from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from handler import handle_schema_memory
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

# Create FastAPI app
app = FastAPI()

# Enable CORS (Vercel-friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["MSE1"]

# ✅ Structured memory schema endpoint
@app.post("/schema_memory")
async def schema_memory_endpoint(request: Request):
    try:
        raw_body = await request.body()
        if not raw_body:
            return JSONResponse(status_code=400, content={"error": "Empty request body"})

        payload = await request.json()
        result = handle_schema_memory(payload, db)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 💬 Simple chat-style endpoint
@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        # Temporary: mimic a GPT-like response
        reply = f"You said: {message}"
        return JSONResponse(content={"reply": reply})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
