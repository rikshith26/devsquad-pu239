
import certifi
from pymongo import MongoClient
import sys

MONGO_URI = "mongodb+srv://devsquaddatabase:DEVSQUAD@devsquad239.jdlqcko.mongodb.net/?appName=devsquad239"
DB_NAME = "lost_found_ai"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    sys.exit(1)

print("\n--- LOST ITEMS ---")
for item in db.lost_items.find().limit(5).sort("created_at", -1):
    print(f"Name: {item.get('item_name')} | Path: {item.get('image_path')}")

print("\n--- FOUND ITEMS ---")
for item in db.found_items.find().limit(5).sort("created_at", -1):
    print(f"Name: {item.get('item_name')} | Path: {item.get('image_path')}")
