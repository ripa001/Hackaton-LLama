import requests, json
from typing import List

from lib.config import INDEXER_URL, INDEXER_HEADER
from lib import mongo, vectors



if __name__ == "__main__":

    for product in mongo.mongo["products"].find({"is_selected": True}, {"_id": 1, "full_name": 1}):

        vector = vectors.get_text_embedding(product["full_name"])

        if vector:
            product["vector"] = vector
            mongo.mongo["products"].update_one({"_id": product["_id"]}, {"$set": {"vector": vector}})
        else:
            print(f"failed to get vector for {product['full_name']}")

