import os
from toolhouse import Toolhouse
from groq import Groq
from lib  import mongo, vectors


th = Toolhouse()
client = Groq(api_key=os.getenv("API_KEY_GROQ"))
MODEL = "llama-3.1-8b-instant"
# MODEL = "llama-3.1-70b-versatile"
# MODEL = "llama3-70b-8192"


my_local_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_minor_price_shop",
            "description": "Retrieves the document with the lowest price of a product, from already near-by shops. DO NOT WORRY ABOUT THE LOCALIZATION, WE'LL CHECK THIS ON OUR END WITHIN THE TOOL! When you specify the product_name, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the product_name of the product you know. If you are sending any other information, think again and remove any information that is not product_name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name_in_italian": {
                        "type": "string",
                        "description": "The name of the product the user is looking for, BUT MUST BE TRANSLATED IN ITALIAN.",
                    }
                },
                "required": [
                    "product_name_in_italian",
                ],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearest_supermarket",
            "description": "When asked to find the nearest supermarket or shop this tool will return the nearest supermarkets to the user. DO NOT WORRY ABOUT THE LOCALIZATION, WE'LL CHECK THIS ON OUR END WITHIN THE TOOL!",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cheapest_list_of_products",
            "description": "Given a list of products, returns the cheapest list of products IN ITALIAN from the shops near the user. When you specify the list of products, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the list of products the user is looking for. If you are sending any other information, think again and remove any information that is not the list of products.",
            "parameters": {
                "type": "object",
                "properties": {
                    "products": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "The name of the product the user is looking for, BUT MUST BE TRANSLATED IN ITALIAN.",
                        },
                    }
                },
                "required": [
                    "products",
                ],
                "additionalProperties": False
                
            }
        }
    }
]

@th.register_local_tool("get_cheapest_list_of_products")
def get_cheapest_list_of_products(products: list, lat: float, long: float):
    print("products", products)
    list_shops = [get_minor_price_shop(p, lat, long) for p in products]
    print("list_shops", list_shops)
    return str(list_shops)

@th.register_local_tool("get_minor_price_shop")
def get_minor_price_shop(
   # Must match the name of the parameters in your tool definition
    product_name_in_italian: str, lat: float, long: float) -> str:
    print("eureka, received the tool call, lat, long", lat, long)

    

    # find top 10 shops close to the user
    shop_ids = list(mongo.mongo["stores"].aggregate([
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [float(lat), float(long)]
                },
                "distanceField": "distance",
                "maxDistance": 10000000,
                "spherical": True
            }
        },
        {
            "$limit": 10
        },
        {
            "$project": {"distance": 1, "working_hours": 1, "city": 1, "zip_code": 1, "street": 1}
        }
    ]))

    shop_infos = {s["_id"]: s for s in shop_ids}
    shop_ids = list(shop_infos.keys())

    
    print("shop_infos", len(shop_infos), shop_infos[shop_ids[0]])
    print("shop_ids", shop_ids)
    print("product_name_in_italian", f'"{product_name_in_italian}"')


    aggregate = lambda name: [
        {
            "$match": {
                "store_id": {"$in": shop_ids},
            }
        },
        {
            "$match": {
                "full_name": {"$regex": name.lower().strip(), "$options": "imxs"}
            }
        },
        {
            "$sort": {"price": 1}
        },
        {
            "$limit": 5
        },
        {
            "$project": {"_id": 0, "store_id": 1, "price": 1, "full_name": 1, "description": 1}
        }
    ]


    print("aggregate", aggregate)

    prods = list(mongo.mongo["products"].aggregate(aggregate(product_name_in_italian)))

    if not len(prods):
        name = product_name_in_italian.lower().strip().split(" ")
        if len(name) > 1:
            prods = list(mongo.mongo["products"].aggregate(aggregate(name[0])))
            if not len(prods):
                prods = list(mongo.mongo["products"].aggregate(aggregate(name[-1])))
                return str(prods)

    #     prods = get_minor_price_shop_vector(product_name_in_italian)

    for p in prods:
        print("shop_infos[p[store_id]]", shop_infos[p["store_id"]])
        p["distance"] = shop_infos[p["store_id"]]["distance"]    
        # p["zip_code"] = shop_infos[p["store_id"]]["zip_code"]
        p["city"] = shop_infos[p["store_id"]]["city"]
        p["street"] = shop_infos[p["store_id"]]["street"]
        p["working_hours"] = shop_infos[p["store_id"]]["working_hours"]

        # p["_id"] = str(p["_id"])
        p["store_id"] = str(p["store_id"])

    return str(prods)

@th.register_local_tool("get_nearest_supermarket")
def get_nearest_supermarket(
    # Must match the name of the parameters in your tool definition
    lat: float, long: float) -> str:
    shop_ids = list(mongo.mongo["stores"].aggregate([
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [float(lat), float(long)]
                },
                "distanceField": "distance",
                "maxDistance": 10000000,
                "spherical": True
            }
        },
        {
            "$sort": {"distance": 1}
        },
        {
            "$limit":5
        },
        {
            "$project": {"_id": 1, "distance": 1, "working_hours": 1, "city": 1, "zip_code": 1, "street": 1}
        }

    ]))
    print("shop_ids", shop_ids)
    return str(list(shop_ids))

