from pymongo import MongoClient

mongo_uri = MongoClient(
    "mongodb://sniplyuser:NXy7R7wRskSrk3F2@ac-whear6l-shard-00-00.iwac6oj.mongodb.net:27017,ac-whear6l-shard-00-01.iwac6oj.mongodb.net:27017,ac-whear6l-shard-00-02.iwac6oj.mongodb.net:27017/?replicaSet=atlas-110fhx-shard-0&ssl=true&authSource=admin",
    connectTimeoutMS=30000,  # Increase connection timeout to 30 seconds
    socketTimeoutMS=30000,  # Increase socket timeout to 30 seconds
    serverSelectionTimeoutMS=30000,
)
db_catax = mongo_uri.Catax_Dev_DB
