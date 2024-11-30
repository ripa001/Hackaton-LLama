from typing import List
import pymongo
from pymongo.collection import Collection

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


async def retrieve_product_by_id(product_id: int):
	# Placeholder function to simulate database retrieval
	# Replace with actual database query logic
	products = {
		1: {"id": 1, "name": "Product 1", "price": 10.0},
		2: {"id": 2, "name": "Product 2", "price": 20.0},
	}
	return products.get(product_id)


mongo = get_db()
