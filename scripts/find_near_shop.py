from lib import mongo



if __name__ == "__main__":

    shops = list(mongo.mongo["stores"].find({}, {"_id": 1, "name": 1, "lat": 1, "long": 1}))

    # using latitude and longitude, compute distance between the all shops
    for shop in shops:

        shop["near_shops"] = []

        for other_shop in shops:

            if shop["_id"] != other_shop["_id"]:
                distance = ((shop["lat"] - other_shop["lat"]) ** 2 + (shop["long"] - other_shop["long"]) ** 2) ** 0.5
                shop["near_shops"].append({"_id": other_shop["_id"], "distance": distance})
        
        shop["near_shops"].sort(key=lambda x: x["distance"])

    
    ## find the shop that has lower avg distance of the top 3 nearest shops
    for shop in shops:
        shop["avg_distance"] = sum([x["distance"] for x in shop["near_shops"][:3]]) / 3
    
    shops.sort(key=lambda x: x["avg_distance"])

    print(shops[0])
    print(shops[0]["near_shops"][:3])
    print(shops[0]["avg_distance"])

    next_shops_ids = list(set([shops[0]["_id"]] + [x["_id"] for x in shops[0]["near_shops"][:3]]))
    print(next_shops_ids)

    ## for each ids, compute how many products have
    products_by_shop = list(mongo.mongo["products"].aggregate([
        {
            "$group": {
                "_id": "$store_id",
                "ids": {"$sum": 1}
            }
        }
    ]))
    print("\n\n\n")
    print(len(products_by_shop), products_by_shop[:3])

    c = 0
    for prod in products_by_shop:
        if prod["_id"] in next_shops_ids:
            c += 1
            print(prod["_id"], prod["ids"])

    print(c)

    # ## set 10 random prods as "is_selected" = True, for each shop in next_shops_ids
    for shop_id in next_shops_ids:
        products = list(mongo.mongo["products"].find({"store_id": shop_id}).limit(10))

        print(shop_id, len(products))

        for prod in products:
            mongo.mongo["products"].update_one({"_id": prod["_id"]}, {"$set": {"is_selected": True}})
    

    ## use aggregater with "$merge" to create a new collection with the selected products
    mongo.mongo["products"].aggregate([
        {
            "$match": {"is_selected": True}
        },
        {
            "$merge": {"into": "selected_products"}
        }
    ])


    # ## compute how many products have 
    # mongo.mongo["stores"].update_many({"_id": {"$in": next_shops_ids}}, {"$set": {"is_selected": True}})
