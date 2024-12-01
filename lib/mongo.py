from typing import List
import pymongo
from pymongo.collection import Collection
from bson.objectid import ObjectId

from lib.config import MONGODB_URL


def get_db():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client["staging"]
    return db


def vector_search(vector: List[float], mongo_coll: Collection, limit: int = 1, projects: dict = {"_id": 1, "vector" : 0}):

	projects["score"] = {"$meta": "vectorSearchScore"}

	results = list(mongo_coll.aggregate([
		{
            "$vectorSearch": {
                "index": "vector_index",
                "path": "vector",
                "queryVector": vector,
                "numCandidates": 250,
                "limit": limit
		    }
        },
        {
            "$project": projects
        }
	]))

	return results


def retrieve_product_by_id(product_id: str):

    product = mongo["products"].find_one({"_id": ObjectId(product_id)})
    return product

def get_user_chat(user_id: str):
    user = mongo["users"].find_one({"userId": user_id})
    return user

def upsert_user_chat(chat: list, user_id: str):
    mongo["users"].update_one({"userId": user_id}, {"$set": {"chat": chat}}, upsert=True)

mongo = get_db()
