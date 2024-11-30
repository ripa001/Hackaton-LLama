from typing import List
import pymongo
from pymongo.collection import Collection
from bson import ObjectId

from lib.config import MONGODB_URL


def get_db():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client["staging"]
    return db


def vector_search(vector: List[float], mongo_coll: Collection, limit: int = 1, projects: dict = {"_id": 1, "vector" : 0}, limit_winning: bool = False):

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


async def retrieve_product_by_id(product_id: str):

    product = await mongo["products"].find_one({"_id": ObjectId(product_id)})
    return product


mongo = get_db()
