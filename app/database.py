# app/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson import ObjectId
import os

# Load the MongoDB URL from environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client["OPA_Data"] 

# Helper to convert ObjectId to string in JSON responses
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)