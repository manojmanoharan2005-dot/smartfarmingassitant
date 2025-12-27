from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')

if not MONGODB_URI:
    print('❌ MONGODB_URI not set. Copy .env.example to .env and set MONGODB_URI')
    raise SystemExit(1)

print('🔄 Attempting to connect to MongoDB...')
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print('✅ Successfully connected to MongoDB')
    # show available databases
    print('Databases:', client.list_database_names())
    client.close()
except Exception as e:
    print('❌ Connection failed:', e)
    raise
