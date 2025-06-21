from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from handler import handle_schema_memory
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your Vercel app URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["MSE1"]

@app.post("/schema_memory")
async def schema_memory_endpoint(request: Request):
    try:
        # Read raw body and parse JSON
        raw_body = await request.body()
        if not raw_body:
            return JSONResponse(status_code=400, content={"error": "Empty request body"})

        payload = await request.json()
        result = handle_schema_memory(payload, db)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
