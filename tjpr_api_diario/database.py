from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = "diarios_db"

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
collection = db["downloads"]  # Define 'collection' corretamente
