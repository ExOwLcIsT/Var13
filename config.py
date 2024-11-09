from pymongo import MongoClient

# Параметри підключення до MongoDB
MONGO_URI = "mongodb://localhost:27017"  # Замість localhost:27017 вкажіть ваші дані
DB_NAME = "Taxi"

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]
