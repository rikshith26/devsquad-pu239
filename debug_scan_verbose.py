
import os
import certifi
from pymongo import MongoClient
from ai_matcher import final_match
import sys
from flask import Flask

# Mock Flask app for context
app = Flask(__name__)

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
lost_items = list(db.lost_items.find({"status": "lost"}).limit(5))
found_items = list(db.found_items.find({"status": "found"}).limit(5))

print(f"📉 Analyzing top {len(lost_items)} Lost vs {len(found_items)} Found items...")
print("-" * 60)

with app.app_context():
    for lost in lost_items:
        for found in found_items:
            print(f"\n[L] {lost.get('item_name')} vs [F] {found.get('item_name')}")
            
            # Check paths
            l_path = lost.get('image_path')
            f_path = found.get('image_path')
            
            if not l_path or not f_path:
                print("  ⚠️ Missing images, skipping.")
                continue

            try:
                # Force absolute paths for test if they are relative
                if not os.path.isabs(l_path): l_path = os.path.abspath(l_path)
                if not os.path.isabs(f_path): f_path = os.path.abspath(f_path)
                
                # Update dicts temp for matching
                lost_copy = lost.copy()
                found_copy = found.copy()
                lost_copy['image_path'] = l_path
                found_copy['image_path'] = f_path

                score = final_match(lost_copy, found_copy)
                
                print(f"  📝 Text: {score['text_score']}% | 🖼️ Image: {score['image_score']}% | 🎨 Color: {score['color_score']}%")
                print(f"  🏆 FINAL: {score['final_score']}")
                
                if score['final_score'] >= 0.4:
                    print("  ✅ WOULD MATCH (> 0.4)")
                else:
                    print("  ❌ LOW SCORE (< 0.4)")
                    
            except Exception as e:
                print(f"  💥 Error: {e}")
