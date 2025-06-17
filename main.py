from fastapi import FastAPI, Request
from handler import handle_schema_memory
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

app = FastAPI()

# Load MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["MSE1"]  # <-- replace with your actual DB name

@app.post("/schema_memory")
async def schema_memory_endpoint(request: Request):
    payload = await request.json()
    result = handle_schema_memory(payload, db)
    return result
