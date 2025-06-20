from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # 🔹 Add this import
from handler import handle_schema_memory
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

app = FastAPI()

# 🔐 CORS setup — paste this right after app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 Change to your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["MSE1"]

@app.post("/schema_memory")
async def schema_memory_endpoint(request: Request):
    payload = await request.json()
    result = handle_schema_memory(payload, db)
    return result
