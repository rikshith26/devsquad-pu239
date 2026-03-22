
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

print("\n📊 --- DATA DIAGNOSTICS ---")
lost_count = db.lost_items.count_documents({"status": "lost"})
found_count = db.found_items.count_documents({"status": "found"})
matched_lost = db.lost_items.count_documents({"status": "matched"})
matched_found = db.found_items.count_documents({"status": "matched"})

print(f"Active Lost Items: {lost_count}")
print(f"Active Found Items: {found_count}")
print(f"Already Matched (Hidden): {matched_lost} Lost | {matched_found} Found")

# RESET OPTION
if len(sys.argv) > 1 and sys.argv[1] == "--reset":
    print("\n🔄 RESETTING ALL ITEMS TO 'lost'/'found'...")
    db.lost_items.update_many({}, {"$set": {"status": "lost"}})
    db.found_items.update_many({}, {"$set": {"status": "found"}})
    print("✅ Reset Complete. All items should be eligible for matching now.")
