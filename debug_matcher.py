
import os
import certifi
from pymongo import MongoClient
from ai_matcher import final_match
import sys

# Connect to DB
MONGO_URI = "mongodb+srv://devsquaddatabase:DEVSQUAD@devsquad239.jdlqcko.mongodb.net/?appName=devsquad239"
DB_NAME = "lost_found_ai"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ DB Connection Failed: {e}")
    sys.exit(1)

# Fetch Items
lost_items = list(db.lost_items.find({"status": "lost"}))
found_items = list(db.found_items.find({"status": "found"}))

print(f"📉 Lost Items: {len(lost_items)}")
print(f"📈 Found Items: {len(found_items)}")

if not lost_items or not found_items:
    print("⚠️ Need at least one lost and one found item to compare.")
    sys.exit(0)

print("\n🔍 STARTING COMPARISONS...")
print("-" * 50)

for lost in lost_items:
    print(f"\n[LOST] {lost.get('item_name')} | Img: {lost.get('image_path')}")
    
    # Check if file exists
    if os.path.exists(lost.get('image_path', '')):
        print(f"  ✅ File exists: {lost.get('image_path')}")
    else:
        print(f"  ❌ File NOT FOUND: {lost.get('image_path')}")

    for found in found_items:
        print(f"  vs [FOUND] {found.get('item_name')} | Img: {found.get('image_path')}")
        
        if os.path.exists(found.get('image_path', '')):
            print(f"    ✅ File exists: {found.get('image_path')}")
        else:
            print(f"    ❌ File NOT FOUND: {found.get('image_path')}")

        if lost.get("image_path") and found.get("image_path"):
            try:
                score = final_match(lost, found)
                print(f"    🎯 SCORE: {score}")
            except Exception as e:
                print(f"    💥 Match Error: {e}")
