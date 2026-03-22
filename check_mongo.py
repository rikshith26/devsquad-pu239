from pymongo import MongoClient
import certifi

MONGO_URI = "mongodb+srv://devsquaddatabase:DEVSQUAD@devsquad239.jdlqcko.mongodb.net/?appName=devsquad239"

try:
    print("Testing MongoDB Connection...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
    info = client.server_info()
    print("SUCCESS: Connected to MongoDB Atlas")
    print(f"Info: {info.get('version')}")
except Exception as e:
    print(f"FAILURE: {e}")
