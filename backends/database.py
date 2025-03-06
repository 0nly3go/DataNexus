import pymongo
from datetime import datetime

def write_to_db(texts=[], interaction_id=None, chatbot_name=None,interaction_date=None):
    try:
        # connect to db
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["chatbot"]
        collection = db["chatbot"]
        
        # write data to db
        data = {
            "text": texts,
            "interaction_id": interaction_id,
            "chatbot_name": chatbot_name,
            "interaction_date": interaction_date
            }
        collection.insert_one(data)
        
        print(f"Data written to db for interaction_id: {interaction_id}")
    
    except Exception as e:
        print(f"Error writing to db: {e}")
    finally:
        client.close()
        
