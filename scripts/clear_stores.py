from lib import mongo

mongo.mongo["users"].delete_many({})


if __name__ == "__main__":
    
    shops = list(mongo.mongo["stores"].find({}, {"_id": 1}))

    for shop in shops:
        count_prods = mongo.mongo["products"].count_documents({"store_id": shop["_id"]})

        if count_prods == 0:
            mongo.mongo["stores"].delete_one({"_id": shop["_id"]})
            print(f"Deleted shop {shop['_id']}")
