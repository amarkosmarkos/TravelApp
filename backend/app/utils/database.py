from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB URI for local connection (you can change it for Docker if necessary)
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "travel_app"  # The name of the database

# Establish connection to MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database(DB_NAME)  # Get the database

# Users collection
users_collection = db["users"]
