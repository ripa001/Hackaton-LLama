from lib import mongo

if __name__ == "__main__":

    shops = list(mongo.mongo["stores"].find({}, {"_id": 1, "name": 1, "lat": 1, "long": 1}))

    # create a new field for each shop for geospatial location using lat and long
    for shop in shops:
        geopos = {
            "type": "Point",
            "coordinates": [shop["lat"], shop["long"]]
        }
        mongo.mongo["stores"].update_one({"_id": shop["_id"]}, {"$set": {"geopos": geopos}})

    ## create index for geopos field
    mongo.mongo["stores"].create_index([("geopos", "2dsphere")])
