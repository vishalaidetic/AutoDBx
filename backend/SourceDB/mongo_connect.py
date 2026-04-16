from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def connect_mongodb(uri: str, database_name: str | None = None):
    """
    Establishes a connection to the MongoDB database using a MongoDB Atlas URI.
    Optionally returns a specific database.
    """
    try:
        client = MongoClient(uri, server_api=ServerApi("1"))
        # Send a ping to confirm a successful connection
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        if database_name:
            return client[database_name]
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def fetch_data_mongodb( 
    db_or_client, collection_name: str, query_filter: dict | None = None
):
    """
    Fetches data from a MongoDB collection.
    Expects a database object (not a client) as db_or_client.
    """
    if not db_get_project_working_diror_client:
        print("No MongoDB connection or database/client object provided.")
        return None

    try:
        # If a client is provided, ask for a database
        if isinstance(db_or_client, MongoClient):
            print(
                "Please provide a specific database when fetching data from a MongoClient."
            )
            return None

        collection = db_or_client[collection_name]
        data = list(collection.find(query_filter or {}))
        return data
    except Exception as err:
        print(f"Error fetching data from MongoDB collection '{collection_name}': {err}")
        return None


def close_mongodb_connection(client):
    """
    Closes the MongoDB client connection.
    """
    if client and isinstance(client, MongoClient):
        client.close()
        print("MongoDB connection closed.")


# Example Usage (you can remove this from the final file if you prefer)
if __name__ == "__main__":
    # Replace <db_password> with your actual password
    uri = "mongodb+srv://vishalgaurav293:spartan4666@pro-village.ghcrck5.mongodb.net/?retryWrites=true&w=majority&appName=Pro-village"
    database_name = "pro_village"

    # Connect to a specific database
    mongo_db = connect_mongodb(uri, database_name=database_name)
    if mongo_db:
        # Example: Fetch all documents from a collection named 'users'
        data = fetch_data_mongodb(mongo_db, "users")
        if data:
            print("Fetched MongoDB Data:")
            for doc in data:
                print(doc)
        else:
            print("No data fetched from MongoDB or an error occurred.")

        # Close the client connection (access through the database object)
        close_mongodb_connection(mongo_db.client)

    print("-" * 30)

    # Example: Connect to client without specifying database, then select it
    mongo_client = connect_mongodb(uri)
    if mongo_client:
        my_db = mongo_client["another_mongo_database"]
        data = fetch_data_mongodb(my_db, "another_collection", {"status": "active"})
        if data:
            print("Fetched MongoDB Data from another database/collection:")
            for doc in data:
                print(doc)
        close_mongodb_connection(mongo_client)
